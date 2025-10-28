"""
AI Conversation Context Manager for TTA Development.

This module provides context management for AI-assisted development sessions,
implementing the agentic primitive of context window management at the meta-level
(development process) before integrating into the product.
"""

import fnmatch
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import tiktoken

    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    logging.warning("tiktoken not available, using approximate token counting")

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    logging.warning("pyyaml not available, instruction loading disabled")

logger = logging.getLogger(__name__)


@dataclass
class ConversationMessage:
    """A message in the AI conversation."""

    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)
    tokens: int = 0
    importance: float = 1.0  # 0.0 to 1.0, higher = more important

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "tokens": self.tokens,
            "importance": self.importance,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConversationMessage":
        """Create from dictionary."""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
            tokens=data.get("tokens", 0),
            importance=data.get("importance", 1.0),
        )


@dataclass
class ConversationContext:
    """Managed conversation context for AI sessions."""

    session_id: str
    messages: list[ConversationMessage]
    max_tokens: int = 8000
    current_tokens: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def utilization(self) -> float:
        """
        Return context window utilization.

        Returns:
            Float between 0.0 and 1.0 representing utilization percentage
        """
        return self.current_tokens / self.max_tokens if self.max_tokens > 0 else 0.0

    @property
    def remaining_tokens(self) -> int:
        """Return remaining token capacity."""
        return max(0, self.max_tokens - self.current_tokens)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "messages": [m.to_dict() for m in self.messages],
            "max_tokens": self.max_tokens,
            "current_tokens": self.current_tokens,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConversationContext":
        """Create from dictionary."""
        return cls(
            session_id=data["session_id"],
            messages=[ConversationMessage.from_dict(m) for m in data["messages"]],
            max_tokens=data.get("max_tokens", 8000),
            current_tokens=data.get("current_tokens", 0),
            metadata=data.get("metadata", {}),
        )


class InstructionLoader:
    """
    Loads and parses .instructions.md files for AI context injection.

    This class discovers instruction files in .augment/instructions/,
    parses their YAML frontmatter, and matches them against file paths
    using glob patterns.
    """

    def __init__(self, instructions_dir: str = ".augment/instructions"):
        """
        Initialize the instruction loader.

        Args:
            instructions_dir: Directory containing .instructions.md files
        """
        self.instructions_dir = Path(instructions_dir)
        self._cache: dict[str, dict[str, Any]] = {}

    def discover_instructions(self) -> list[Path]:
        """
        Discover all .instructions.md files in the instructions directory.

        Returns:
            List of Path objects for instruction files
        """
        if not self.instructions_dir.exists():
            logger.warning(f"Instructions directory not found: {self.instructions_dir}")
            return []

        instruction_files = list(self.instructions_dir.glob("*.instructions.md"))
        logger.debug(f"Discovered {len(instruction_files)} instruction files")
        return instruction_files

    def parse_instruction_file(self, file_path: Path) -> dict[str, Any] | None:  # noqa: PLR0911
        """
        Parse instruction file and extract YAML frontmatter and content.

        Args:
            file_path: Path to instruction file

        Returns:
            Dict with 'frontmatter' and 'content' keys, or None if parsing fails
        """
        # Check cache first
        cache_key = str(file_path)
        if cache_key in self._cache:
            return self._cache[cache_key]

        if not YAML_AVAILABLE:
            logger.warning("pyyaml not available, cannot parse instruction files")
            return None

        try:
            content = file_path.read_text(encoding="utf-8")

            # Extract YAML frontmatter (between --- markers)
            frontmatter_match = re.match(
                r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL
            )
            if not frontmatter_match:
                logger.warning(f"No YAML frontmatter found in {file_path.name}")
                return None

            frontmatter_text = frontmatter_match.group(1)
            markdown_content = frontmatter_match.group(2)

            # Parse YAML frontmatter
            frontmatter = yaml.safe_load(frontmatter_text)
            if not frontmatter:
                logger.warning(f"Empty frontmatter in {file_path.name}")
                return None

            # Validate required fields
            if "applyTo" not in frontmatter:
                logger.warning(f"Missing 'applyTo' field in {file_path.name}")
                return None

            result = {
                "frontmatter": frontmatter,
                "content": markdown_content.strip(),
                "filename": file_path.name,
            }

            # Cache result
            self._cache[cache_key] = result
            return result

        except Exception as e:
            logger.error(f"Failed to parse instruction file {file_path.name}: {e}")
            return None

    def match_file_path(self, file_path: str | None, apply_to: str | list[str]) -> bool:
        """
        Check if file path matches applyTo glob pattern(s).

        Args:
            file_path: File path to match (None matches only global patterns)
            apply_to: Glob pattern or list of patterns from applyTo field

        Returns:
            True if file path matches any pattern, False otherwise
        """
        if file_path is None:
            # No file path provided - only match global patterns
            patterns = [apply_to] if isinstance(apply_to, str) else apply_to
            return any(p in {"**/*.py", "**/*"} for p in patterns)

        # Normalize file path
        file_path_obj = Path(file_path)

        # Convert applyTo to list of patterns
        patterns = [apply_to] if isinstance(apply_to, str) else apply_to

        # Check if file matches any pattern
        # Use PurePath.match() which matches from the right side
        # For patterns like "src/player_experience/**/*.py", we need to check
        # if the file path matches the pattern using glob-style matching
        for pattern in patterns:
            # Path.match() matches from the right, so we need to handle
            # patterns with directory prefixes differently
            if "**" in pattern:
                # For patterns with **, use glob-style matching
                # Convert pattern to parts and check if file path matches
                pattern_parts = Path(pattern).parts
                file_parts = file_path_obj.parts

                # Check if pattern matches
                if self._glob_match(file_parts, pattern_parts):
                    return True
            # For simple patterns, use Path.match()
            elif file_path_obj.match(pattern):
                return True

        return False

    def _glob_match(  # noqa: PLR0911
        self, file_parts: tuple[str, ...], pattern_parts: tuple[str, ...]
    ) -> bool:
        """
        Match file path parts against pattern parts with ** support.

        Args:
            file_parts: File path parts (e.g., ('src', 'player_experience', 'service.py'))
            pattern_parts: Pattern parts (e.g., ('src', 'player_experience', '**', '*.py'))

        Returns:
            True if file matches pattern, False otherwise
        """
        # Handle ** in pattern
        if "**" in pattern_parts:
            # Find position of **
            star_idx = pattern_parts.index("**")

            # Match prefix (before **)
            prefix_parts = pattern_parts[:star_idx]
            if len(file_parts) < len(prefix_parts):
                return False
            for i, part in enumerate(prefix_parts):
                if not fnmatch.fnmatch(file_parts[i], part):
                    return False

            # Match suffix (after **)
            suffix_parts = pattern_parts[star_idx + 1 :]
            if len(suffix_parts) > 0:
                if len(file_parts) < len(suffix_parts):
                    return False
                for i, part in enumerate(suffix_parts):
                    if not fnmatch.fnmatch(file_parts[-(len(suffix_parts) - i)], part):
                        return False

            return True
        # No **, simple match
        if len(file_parts) != len(pattern_parts):
            return False
        for file_part, pattern_part in zip(file_parts, pattern_parts, strict=False):
            if not fnmatch.fnmatch(file_part, pattern_part):
                return False
        return True

    def get_relevant_instructions(
        self, current_file: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Get instructions relevant to the current file context.

        Args:
            current_file: Optional file path for scoped instructions

        Returns:
            List of instruction dicts with 'frontmatter', 'content', 'filename'
        """
        instruction_files = self.discover_instructions()
        relevant = []

        for file_path in instruction_files:
            parsed = self.parse_instruction_file(file_path)
            if not parsed:
                continue

            apply_to = parsed["frontmatter"].get("applyTo")
            if self.match_file_path(current_file, apply_to):
                relevant.append(parsed)

        logger.debug(
            f"Found {len(relevant)} relevant instructions for file: {current_file or 'global'}"
        )
        return relevant


class MemoryLoader:
    """
    Loads and parses .memory.md files for AI context injection.

    This class discovers memory files in .augment/memory/ subdirectories,
    parses their YAML frontmatter, and matches them against current context
    (component, tags, category) to provide relevant historical learnings.
    """

    def __init__(self, memory_dir: str = ".augment/memory"):
        """
        Initialize the memory loader.

        Args:
            memory_dir: Directory containing memory subdirectories
        """
        self.memory_dir = Path(memory_dir)
        self._cache: dict[str, dict[str, Any]] = {}

    def discover_memories(self) -> list[Path]:
        """
        Discover all .memory.md files in memory subdirectories.

        Returns:
            List of Path objects for memory files
        """
        if not self.memory_dir.exists():
            logger.warning(f"Memory directory not found: {self.memory_dir}")
            return []

        memory_files = []
        for subdir in self.memory_dir.iterdir():
            if subdir.is_dir() and not subdir.name.startswith("."):
                memory_files.extend(subdir.glob("*.memory.md"))

        logger.debug(f"Discovered {len(memory_files)} memory files")
        return memory_files

    def parse_memory_file(self, file_path: Path) -> dict[str, Any] | None:  # noqa: PLR0911
        """
        Parse memory file and extract YAML frontmatter and content.

        Args:
            file_path: Path to memory file

        Returns:
            Dict with 'frontmatter', 'content', 'filename', 'category' keys, or None if parsing fails
        """
        # Check cache first
        cache_key = str(file_path)
        if cache_key in self._cache:
            return self._cache[cache_key]

        if not YAML_AVAILABLE:
            logger.warning("pyyaml not available, cannot parse memory files")
            return None

        try:
            content = file_path.read_text(encoding="utf-8")

            # Extract YAML frontmatter (between --- markers)
            frontmatter_match = re.match(
                r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL
            )
            if not frontmatter_match:
                logger.warning(f"No YAML frontmatter found in {file_path.name}")
                return None

            frontmatter_text = frontmatter_match.group(1)
            markdown_content = frontmatter_match.group(2)

            # Parse YAML frontmatter
            frontmatter = yaml.safe_load(frontmatter_text)
            if not frontmatter:
                logger.warning(f"Empty frontmatter in {file_path.name}")
                return None

            # Validate required fields
            required_fields = ["category", "date", "component", "severity", "tags"]
            for field in required_fields:
                if field not in frontmatter:
                    logger.warning(f"Missing '{field}' field in {file_path.name}")
                    return None

            # Determine category from parent directory
            category = file_path.parent.name

            result = {
                "frontmatter": frontmatter,
                "content": markdown_content.strip(),
                "filename": file_path.name,
                "category": category,
            }

            # Cache result
            self._cache[cache_key] = result
            return result

        except Exception as e:
            logger.error(f"Failed to parse memory file {file_path.name}: {e}")
            return None

    def match_memory(
        self,
        memory: dict[str, Any],
        component: str | None = None,
        tags: list[str] | None = None,
        category: str | None = None,
    ) -> float:
        """
        Calculate relevance score for a memory based on matching criteria.

        Args:
            memory: Parsed memory dict
            component: Current component being worked on
            tags: Current task tags
            category: Desired memory category

        Returns:
            Relevance score (0.0 to 1.0), 0.0 if no match
        """
        frontmatter = memory["frontmatter"]
        score = 0.0

        # If no filters provided, give base relevance score
        if not component and not tags and not category:
            score = 0.5  # Base relevance when no filters

        # Component match (highest priority)
        memory_component = frontmatter.get("component", "")
        if component and memory_component == component:
            score += 0.5  # Exact component match
        elif component and memory_component == "global":
            score += 0.3  # Global memories apply to all components

        # Tag match
        memory_tags = frontmatter.get("tags", [])
        if tags and memory_tags:
            matching_tags = set(tags) & set(memory_tags)
            if matching_tags:
                # Score based on proportion of matching tags
                tag_score = len(matching_tags) / max(len(tags), len(memory_tags))
                score += 0.3 * tag_score

        # Category match
        if category and memory["category"] == category:
            score += 0.2

        return min(score, 1.0)  # Cap at 1.0

    def calculate_importance(self, memory: dict[str, Any], relevance: float) -> float:
        """
        Calculate importance score for a memory based on severity, recency, and relevance.

        Args:
            memory: Parsed memory dict
            relevance: Relevance score from match_memory()

        Returns:
            Importance score (0.0 to 1.0)
        """
        frontmatter = memory["frontmatter"]

        # Severity scoring
        severity_scores = {
            "critical": 1.0,
            "high": 0.9,
            "medium": 0.7,
            "low": 0.5,
        }
        severity = frontmatter.get("severity", "medium")
        severity_score = severity_scores.get(severity, 0.5)

        # Recency scoring (newer memories score higher)
        try:
            memory_date = datetime.strptime(frontmatter.get("date", ""), "%Y-%m-%d")
            days_old = (datetime.now() - memory_date).days
            # Decay over 180 days (6 months)
            recency_score = max(0.0, 1.0 - (days_old / 180.0))
        except (ValueError, TypeError):
            recency_score = 0.5  # Default if date parsing fails

        # Combine scores: relevance (50%), severity (30%), recency (20%)
        importance = (relevance * 0.5) + (severity_score * 0.3) + (recency_score * 0.2)

        return min(importance, 1.0)  # Cap at 1.0

    def get_relevant_memories(
        self,
        component: str | None = None,
        tags: list[str] | None = None,
        category: str | None = None,
        min_importance: float = 0.3,
        max_memories: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Get memories relevant to the current context, sorted by importance.

        Args:
            component: Current component being worked on
            tags: Current task tags
            category: Desired memory category (implementation-failures, successful-patterns, architectural-decisions)
            min_importance: Minimum importance score to include (0.0 to 1.0)
            max_memories: Maximum number of memories to return

        Returns:
            List of memory dicts with 'frontmatter', 'content', 'filename', 'category', 'importance'
        """
        memory_files = self.discover_memories()
        scored_memories = []

        for file_path in memory_files:
            parsed = self.parse_memory_file(file_path)
            if not parsed:
                continue

            # Calculate relevance and importance
            relevance = self.match_memory(parsed, component, tags, category)
            if relevance == 0.0:
                continue  # Skip irrelevant memories

            importance = self.calculate_importance(parsed, relevance)
            if importance < min_importance:
                continue  # Skip low-importance memories

            # Add importance to memory dict
            parsed["importance"] = importance
            scored_memories.append(parsed)

        # Sort by importance (descending) and limit to max_memories
        scored_memories.sort(key=lambda m: m["importance"], reverse=True)
        result = scored_memories[:max_memories]

        logger.debug(
            f"Found {len(result)} relevant memories (component={component}, tags={tags}, category={category})"
        )
        return result


class AIConversationContextManager:
    """
    Manages conversation context for AI-assisted development.

    Features:
    - Token counting and tracking
    - Intelligent message pruning
    - Context summarization
    - Important message preservation
    - Session persistence

    This is a meta-level implementation of the context window management
    primitive, applied to our development process before integrating into TTA.
    """

    def __init__(
        self,
        max_tokens: int = 8000,
        sessions_dir: str = ".augment/context/sessions",
        instructions_dir: str = ".augment/instructions",
        memory_dir: str = ".augment/memory",
    ):
        """
        Initialize the conversation context manager.

        Args:
            max_tokens: Maximum tokens per context window
            sessions_dir: Directory to store session files
            instructions_dir: Directory containing .instructions.md files
            memory_dir: Directory containing .memory.md files
        """
        self.max_tokens = max_tokens
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

        # Initialize token counter
        if TIKTOKEN_AVAILABLE:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        else:
            self.encoding = None

        # Initialize instruction loader
        self.instruction_loader = InstructionLoader(instructions_dir)

        # Initialize memory loader
        self.memory_loader = MemoryLoader(memory_dir)

        self.contexts: dict[str, ConversationContext] = {}

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if self.encoding:
            return len(self.encoding.encode(text))
        # Approximate: ~4 characters per token
        return len(text) // 4

    def create_session(self, session_id: str) -> ConversationContext:
        """Create a new conversation session."""
        context = ConversationContext(
            session_id=session_id,
            messages=[],
            max_tokens=self.max_tokens,
            current_tokens=0,
        )
        self.contexts[session_id] = context
        logger.info(f"Created new session: {session_id}")
        return context

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        importance: float = 1.0,
        metadata: dict | None = None,
        auto_prune: bool = True,
    ) -> ConversationContext:
        """
        Add a message to the conversation, pruning if necessary.

        Args:
            session_id: Session identifier
            role: Message role (user, assistant, system)
            content: Message content
            importance: Importance score (0.0 to 1.0)
            metadata: Optional metadata
            auto_prune: Whether to auto-prune when threshold exceeded

        Returns:
            Updated conversation context
        """
        context = self.contexts.get(session_id)
        if not context:
            context = self.create_session(session_id)

        # Count tokens
        tokens = self.count_tokens(content)

        # Create message
        message = ConversationMessage(
            role=role,
            content=content,
            timestamp=datetime.utcnow(),
            metadata=metadata or {},
            tokens=tokens,
            importance=importance,
        )

        # Check if pruning needed (at 80% capacity)
        if auto_prune and (context.current_tokens + tokens) / context.max_tokens > 0.8:
            logger.info(f"Context window at {context.utilization:.1%}, pruning...")
            context = self._prune_context(context, tokens)

        # Add message
        context.messages.append(message)
        context.current_tokens += tokens

        logger.debug(
            f"Added {role} message ({tokens} tokens) to {session_id}. "
            f"Utilization: {context.utilization:.1%}"
        )

        return context

    def load_instructions(
        self, session_id: str, current_file: str | None = None
    ) -> ConversationContext:
        """
        Load relevant .instructions.md files into session context.

        This method discovers instruction files in .augment/instructions/,
        parses their YAML frontmatter, and loads instructions that match
        the current file context (based on applyTo glob patterns).

        Args:
            session_id: Session identifier
            current_file: Optional file path for scoped instructions
                         (e.g., "src/player_experience/service.py")

        Returns:
            Updated conversation context

        Example:
            # Load only global instructions
            manager.load_instructions(session_id)

            # Load global + player experience instructions
            manager.load_instructions(session_id, "src/player_experience/service.py")
        """
        context = self.contexts.get(session_id)
        if not context:
            context = self.create_session(session_id)

        # Get relevant instructions
        instructions = self.instruction_loader.get_relevant_instructions(current_file)

        # Add each instruction as a system message
        for instruction in instructions:
            frontmatter = instruction["frontmatter"]
            content = instruction["content"]
            filename = instruction["filename"]

            # Determine importance based on scope
            apply_to = frontmatter.get("applyTo", "")
            is_global = apply_to in {"**/*.py", "**/*"} or (
                isinstance(apply_to, list) and "**/*.py" in apply_to
            )
            importance = 0.9 if is_global else 0.8

            # Add instruction as system message
            self.add_message(
                session_id=session_id,
                role="system",
                content=content,
                importance=importance,
                metadata={
                    "type": "instruction",
                    "source": filename,
                    "scope": "global" if is_global else "scoped",
                    "description": frontmatter.get("description", ""),
                },
                auto_prune=False,  # Don't prune instructions
            )

        logger.info(
            f"Loaded {len(instructions)} instructions for session {session_id} "
            f"(file: {current_file or 'global'})"
        )

        return context

    def load_memories(
        self,
        session_id: str,
        component: str | None = None,
        tags: list[str] | None = None,
        category: str | None = None,
        min_importance: float = 0.3,
        max_memories: int = 10,
    ) -> ConversationContext:
        """
        Load relevant .memory.md files into session context.

        This method discovers memory files in .augment/memory/ subdirectories,
        parses their YAML frontmatter, and loads memories that match the current
        context (component, tags, category) with importance-based scoring.

        Args:
            session_id: Session identifier
            component: Current component being worked on (e.g., "agent-orchestration")
            tags: Current task tags (e.g., ["testing", "pytest", "fixtures"])
            category: Desired memory category (implementation-failures, successful-patterns, architectural-decisions)
            min_importance: Minimum importance score to include (0.0 to 1.0)
            max_memories: Maximum number of memories to load

        Returns:
            Updated conversation context

        Example:
            # Load all relevant memories
            manager.load_memories(session_id)

            # Load memories for specific component
            manager.load_memories(session_id, component="agent-orchestration")

            # Load only implementation failures
            manager.load_memories(session_id, category="implementation-failures")

            # Load memories with specific tags
            manager.load_memories(session_id, tags=["testing", "pytest"])
        """
        context = self.contexts.get(session_id)
        if not context:
            context = self.create_session(session_id)

        # Get relevant memories
        memories = self.memory_loader.get_relevant_memories(
            component=component,
            tags=tags,
            category=category,
            min_importance=min_importance,
            max_memories=max_memories,
        )

        # Add each memory as a system message
        for memory in memories:
            frontmatter = memory["frontmatter"]
            content = memory["content"]
            filename = memory["filename"]
            importance = memory["importance"]

            # Add memory as system message
            self.add_message(
                session_id=session_id,
                role="system",
                content=content,
                importance=importance,
                metadata={
                    "type": "memory",
                    "source": filename,
                    "category": memory["category"],
                    "component": frontmatter.get("component", ""),
                    "severity": frontmatter.get("severity", ""),
                    "tags": frontmatter.get("tags", []),
                    "date": frontmatter.get("date", ""),
                },
                auto_prune=False,  # Don't prune memories
            )

        logger.info(
            f"Loaded {len(memories)} memories for session {session_id} "
            f"(component={component}, tags={tags}, category={category})"
        )

        return context

    def _prune_context(
        self,
        context: ConversationContext,
        needed_tokens: int,  # noqa: ARG002
    ) -> ConversationContext:
        """
        Prune context to make room for new message.

        Strategy: Keep high-importance messages and recent messages.
        """
        # Always keep system messages
        system_msgs = [m for m in context.messages if m.role == "system"]

        # Keep high-importance messages (importance > 0.8)
        important_msgs = [
            m for m in context.messages if m.importance > 0.8 and m.role != "system"
        ]

        # Keep most recent messages
        recent_msgs = [
            m
            for m in context.messages[-5:]
            if m not in system_msgs and m not in important_msgs
        ]

        # Combine and deduplicate
        preserved = []
        seen_ids = set()
        for msg in system_msgs + important_msgs + recent_msgs:
            msg_id = id(msg)
            if msg_id not in seen_ids:
                preserved.append(msg)
                seen_ids.add(msg_id)

        # Sort by timestamp to maintain order
        preserved.sort(key=lambda m: m.timestamp)

        # Update context
        old_count = len(context.messages)
        old_tokens = context.current_tokens

        context.messages = preserved
        context.current_tokens = sum(m.tokens for m in preserved)

        logger.info(
            f"Pruned context: {old_count} → {len(preserved)} messages, "
            f"{old_tokens} → {context.current_tokens} tokens"
        )

        return context

    def get_context_summary(self, session_id: str) -> str:
        """Get a summary of the conversation context."""
        context = self.contexts.get(session_id)
        if not context:
            return f"No context available for session: {session_id}"

        summary = f"Session: {session_id}\n"
        summary += f"Messages: {len(context.messages)}\n"
        summary += f"Tokens: {context.current_tokens:,}/{context.max_tokens:,}\n"
        summary += f"Utilization: {context.utilization:.1%}\n"
        summary += f"Remaining: {context.remaining_tokens:,} tokens\n"

        # Message breakdown
        role_counts = {}
        for msg in context.messages:
            role_counts[msg.role] = role_counts.get(msg.role, 0) + 1

        summary += "\nMessage Breakdown:\n"
        for role, count in role_counts.items():
            summary += f"  {role}: {count}\n"

        return summary

    def save_session(self, session_id: str, filepath: str | None = None) -> Path:
        """
        Save conversation session to file.

        Args:
            session_id: Session identifier
            filepath: Optional custom filepath (defaults to sessions_dir/<session_id>.json)

        Returns:
            Path to saved file
        """
        context = self.contexts.get(session_id)
        if not context:
            raise ValueError(f"No context found for session: {session_id}")

        if filepath is None:
            filepath = self.sessions_dir / f"{session_id}.json"
        else:
            filepath = Path(filepath)

        filepath.parent.mkdir(parents=True, exist_ok=True)

        with filepath.open("w") as f:
            json.dump(context.to_dict(), f, indent=2)

        logger.info(f"Saved session {session_id} to {filepath}")
        return filepath

    def load_session(self, filepath: str | Path) -> ConversationContext:
        """
        Load conversation session from file.

        Args:
            filepath: Path to session file

        Returns:
            Loaded conversation context
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"Session file not found: {filepath}")

        with filepath.open() as f:
            data = json.load(f)

        context = ConversationContext.from_dict(data)
        self.contexts[context.session_id] = context

        logger.info(f"Loaded session {context.session_id} from {filepath}")
        return context

    def list_sessions(self) -> list[str]:
        """List all saved session files."""
        return [f.stem for f in self.sessions_dir.glob("*.json")]

    def get_architecture_context(self) -> str:
        """
        Get standard TTA architecture context for new sessions.

        This provides consistent architectural context across AI sessions.
        """
        return """
TTA (Therapeutic Text Adventure) Architecture Context:

**Core Components:**
- Multi-agent system: IPA (Input Processor), WBA (World Builder), NGA (Narrative Generator)
- State Management: Redis (session state), Neo4j (knowledge graphs)
- Workflow Orchestration: LangGraph integration for complex workflows
- Component System: Base Component class with lifecycle management

**Key Directories:**
- src/agent_orchestration/ - Multi-agent coordination and workflows
- src/player_experience/ - User-facing APIs and session management
- src/components/ - Reusable components (Neo4j, Redis, LLM, etc.)
- src/ai_components/ - AI-specific components (prompts, RAG, etc.)

**Development Principles:**
- Therapeutic Safety: All content validated for therapeutic appropriateness
- Appropriate Complexity: YAGNI/KISS, avoid gold-plating
- Component Maturity: Development → Staging → Production workflow
- Solo Developer Focus: Optimized for WSL2, single-GPU constraints

**Testing Strategy:**
- Unit tests: Development stage validation
- Integration tests: Staging stage validation
- E2E tests: Production readiness validation
- Component-specific test organization

**Current Focus:**
- Implementing agentic primitives (context management, error recovery, observability)
- Phase 1: Meta-level (development process)
- Phase 2: Product-level (TTA application)
"""


# Convenience function for quick session creation
def create_tta_session(
    session_id: str | None = None, current_file: str | None = None
) -> tuple[AIConversationContextManager, str]:
    """
    Create a new TTA development session with standard architecture context and instructions.

    This function creates a session and automatically loads:
    1. TTA architecture context (always)
    2. Global instructions from .augment/instructions/ (always)
    3. File-scoped instructions (if current_file provided)

    Args:
        session_id: Optional session ID (auto-generated if not provided)
        current_file: Optional file path for scoped instructions
                     (e.g., "src/player_experience/service.py")

    Returns:
        Tuple of (context manager, session ID)

    Example:
        # Create session with only global instructions
        manager, session_id = create_tta_session()

        # Create session with player experience instructions
        manager, session_id = create_tta_session(
            current_file="src/player_experience/service.py"
        )
    """
    if session_id is None:
        session_id = f"tta-dev-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

    manager = AIConversationContextManager()
    manager.create_session(session_id)

    # Add architecture context
    manager.add_message(
        session_id=session_id,
        role="system",
        content=manager.get_architecture_context(),
        importance=1.0,
        metadata={"type": "architecture_context"},
    )

    # Load instructions
    manager.load_instructions(session_id, current_file)

    logger.info(
        f"Created TTA development session: {session_id} "
        f"(file: {current_file or 'global'})"
    )
    return manager, session_id
