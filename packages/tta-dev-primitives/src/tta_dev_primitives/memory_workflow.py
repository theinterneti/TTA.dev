"""Memory Workflow Primitive - 4-Layer Memory System Integration.

This primitive provides a unified interface to the 4-layer memory architecture:
- Layer 1: Session Context (working memory)
- Layer 2: Cache Memory (time-windowed)
- Layer 3: Deep Memory (long-term semantic)
- Layer 4: PAF Store (architectural constraints)

Integrates Redis Agent Memory Server for Layers 1-3 with workflow-aware loading.

Example:
    >>> from tta_dev_primitives import MemoryWorkflowPrimitive, WorkflowContext
    >>>
    >>> memory = MemoryWorkflowPrimitive(
    ...     redis_url="http://localhost:8000",
    ...     user_id="user123"
    ... )
    >>>
    >>> context = WorkflowContext(
    ...     workflow_id="feature-auth",
    ...     session_id="session-456",
    ...     workflow_mode="augster-rigorous"
    ... )
    >>>
    >>> # Load stage-aware context
    >>> context_data = await memory.load_workflow_context(
    ...     context=context,
    ...     stage="understand"
    ... )
"""

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

try:
    from agent_memory_client import MemoryAPIClient, MemoryClientConfig

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    if not TYPE_CHECKING:
        MemoryAPIClient = None  # type: ignore
        MemoryClientConfig = None  # type: ignore
    else:
        from agent_memory_client import MemoryAPIClient, MemoryClientConfig

from .core.base import WorkflowContext
from .paf_memory import PAF, PAFMemoryPrimitive, PAFValidationResult
from .session_group import SessionGroupPrimitive
from .workflow_hub import WorkflowMode


class MemoryWorkflowPrimitive:
    """Unified 4-layer memory system with workflow stage awareness.

    This primitive integrates:
    - Redis Agent Memory Server (Layers 1-3)
    - PAFMemoryPrimitive (Layer 4)
    - SessionGroupPrimitive (session context)
    - WorkflowProfiles (stage-aware loading)

    Attributes:
        redis_client: Redis agent memory client (optional)
        paf_primitive: PAF memory primitive
        session_groups: Session group primitive
        user_id: Default user ID for memory operations
        redis_available: Whether Redis client is available

    Example:
        >>> memory = MemoryWorkflowPrimitive(
        ...     redis_url="http://localhost:8000",
        ...     user_id="user123"
        ... )
        >>>
        >>> # Add to session context (Layer 1)
        >>> await memory.add_session_message(
        ...     session_id="session-123",
        ...     role="user",
        ...     content="Implement authentication"
        ... )
        >>>
        >>> # Create deep memory (Layer 3)
        >>> await memory.create_deep_memory(
        ...     text="JWT authentication pattern",
        ...     memory_type="pattern",
        ...     tags=["auth", "security"]
        ... )
        >>>
        >>> # Validate against PAF (Layer 4)
        >>> validation = memory.validate_paf("QUAL-001", 75.0)
    """

    def __init__(
        self,
        redis_url: str | None = None,
        user_id: str | None = None,
        paf_core_path: str | None = None,
        session_groups_path: str | None = None,
    ) -> None:
        """Initialize memory workflow primitive.

        Args:
            redis_url: Redis agent memory server URL (optional)
            user_id: Default user ID for memory operations
            paf_core_path: Path to .universal-instructions directory or PAFCORE.md (optional)
            session_groups_path: Path to session groups storage (optional)
        """
        self.user_id = user_id
        self.redis_available = REDIS_AVAILABLE and redis_url is not None

        # Initialize Redis client if available
        if self.redis_available:
            config = MemoryClientConfig(base_url=redis_url)
            self.redis_client: MemoryAPIClient | None = MemoryAPIClient(config)
        else:
            self.redis_client = None

        # Initialize PAF primitive (Layer 4)
        # If no path provided, try to find PAFCORE.md in common locations
        paf_full_path = paf_core_path
        if paf_core_path is None:
            from pathlib import Path

            # Try current directory and parent directories
            candidates = [
                Path.cwd() / ".universal-instructions" / "paf" / "PAFCORE.md",
                Path.cwd().parent / ".universal-instructions" / "paf" / "PAFCORE.md",
                Path.cwd().parent.parent
                / ".universal-instructions"
                / "paf"
                / "PAFCORE.md",
            ]
            for candidate in candidates:
                if candidate.exists():
                    paf_full_path = str(candidate)
                    break

        self.paf_primitive = PAFMemoryPrimitive(paf_core_path=paf_full_path)

        # Initialize session groups
        self.session_groups = SessionGroupPrimitive(storage_path=session_groups_path)

    # ==================== Layer 1: Session Context ====================

    async def add_session_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add message to session context (Layer 1: Working Memory).

        Args:
            session_id: Session identifier
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional metadata
        """
        if not self.redis_available or self.redis_client is None:
            return

        await self.redis_client.add_working_memory_messages(
            session_id=session_id,
            messages=[
                {
                    "role": role,
                    "content": content,
                    "metadata": metadata or {},
                }
            ],
        )

    async def get_session_context(
        self,
        session_id: str,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Get session context messages (Layer 1).

        Args:
            session_id: Session identifier
            limit: Maximum messages to retrieve (None = all)

        Returns:
            List of session messages
        """
        if not self.redis_available or self.redis_client is None:
            return []

        result = await self.redis_client.get_working_memory(
            session_id=session_id, limit=limit
        )
        return result.get("messages", [])

    # ==================== Layer 2: Cache Memory ====================

    async def get_cache_memory(
        self,
        session_id: str,
        hours: int = 1,
    ) -> list[dict[str, Any]]:
        """Get time-windowed cache memory (Layer 2).

        Args:
            session_id: Session identifier
            hours: Hours to look back (default: 1)

        Returns:
            List of cached messages
        """
        if not self.redis_available or self.redis_client is None:
            return []

        since = datetime.now() - timedelta(hours=hours)
        result = await self.redis_client.get_working_memory(
            session_id=session_id, since=since.isoformat()
        )
        return result.get("messages", [])

    # ==================== Layer 3: Deep Memory ====================

    async def create_deep_memory(
        self,
        text: str,
        memory_type: str = "observation",
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str | None:
        """Create deep memory (Layer 3: Long-term Memory).

        Args:
            text: Memory content
            memory_type: Type (observation, pattern, preference, etc.)
            tags: Optional tags
            metadata: Optional metadata

        Returns:
            Memory ID or None if Redis unavailable
        """
        if not self.redis_available or self.redis_client is None:
            return None

        memories = await self.redis_client.create_long_term_memories(
            [
                {
                    "text": text,
                    "user_id": self.user_id,
                    "memory_type": memory_type,
                    "metadata": {
                        **(metadata or {}),
                        "tags": tags or [],
                    },
                }
            ]
        )
        return memories[0]["id"] if memories else None

    async def search_deep_memory(
        self,
        query: str,
        memory_type: str | None = None,
        tags: list[str] | None = None,
        k: int = 5,
    ) -> list[dict[str, Any]]:
        """Search deep memory (Layer 3).

        Args:
            query: Search query
            memory_type: Optional memory type filter
            tags: Optional tag filters
            k: Number of results

        Returns:
            List of matching memories
        """
        if not self.redis_available or self.redis_client is None:
            return []

        filter_metadata = {}
        if memory_type:
            filter_metadata["memory_type"] = memory_type
        if tags:
            filter_metadata["tags"] = tags

        return await self.redis_client.search_long_term_memory(
            text=query,
            user_id=self.user_id,
            filter_metadata=filter_metadata if filter_metadata else None,
            k=k,
        )

    # ==================== Layer 4: PAF Store ====================

    def validate_paf(
        self,
        paf_id: str,
        actual_value: str | int | float | bool,
    ) -> PAFValidationResult:
        """Validate against PAF (Layer 4).

        Args:
            paf_id: PAF identifier (e.g., "QUAL-001")
            actual_value: Actual value to validate

        Returns:
            PAFValidationResult
        """
        return self.paf_primitive.validate_against_paf(paf_id, actual_value)

    def get_active_pafs(self) -> list[PAF]:
        """Get all active PAFs (Layer 4).

        Returns:
            List of active PAF objects
        """
        return self.paf_primitive.get_active_pafs()

    # ==================== Workflow Stage-Aware Loading ====================

    async def load_workflow_context(
        self,
        context: WorkflowContext,
        stage: str,
        workflow_mode: WorkflowMode | str = WorkflowMode.STANDARD,
    ) -> dict[str, Any]:
        """Load workflow context based on stage and mode.

        This implements stage-aware memory loading as defined in workflow profiles.

        Args:
            context: Workflow context
            stage: Workflow stage (understand, decompose, plan, implement, validate, reflect)
            workflow_mode: Workflow mode (rapid, standard, augster-rigorous)

        Returns:
            Dictionary with loaded context from all relevant layers
        """
        if isinstance(workflow_mode, str):
            workflow_mode = WorkflowMode(workflow_mode)

        loaded_context: dict[str, Any] = {
            "stage": stage,
            "workflow_mode": workflow_mode.value,
            "session_id": context.session_id,
            "workflow_id": context.workflow_id,
        }

        # Layer-specific loading based on stage and mode
        if stage == "understand":
            loaded_context.update(
                await self._load_understand_context(context, workflow_mode)
            )
        elif stage == "decompose":
            loaded_context.update(
                await self._load_decompose_context(context, workflow_mode)
            )
        elif stage == "plan":
            loaded_context.update(await self._load_plan_context(context, workflow_mode))
        elif stage == "implement":
            loaded_context.update(
                await self._load_implement_context(context, workflow_mode)
            )
        elif stage == "validate":
            loaded_context.update(
                await self._load_validate_context(context, workflow_mode)
            )
        elif stage == "reflect":
            loaded_context.update(
                await self._load_reflect_context(context, workflow_mode)
            )

        return loaded_context

    async def _load_understand_context(
        self, context: WorkflowContext, mode: WorkflowMode
    ) -> dict[str, Any]:
        """Load context for Understand stage."""
        result: dict[str, Any] = {}

        if not context.session_id:
            return result

        if mode == WorkflowMode.RAPID:
            # Minimal: Current session only
            result["session_context"] = await self.get_session_context(
                context.session_id, limit=10
            )
        elif mode == WorkflowMode.STANDARD:
            # Standard: Session + recent cache + some deep memory
            result["session_context"] = await self.get_session_context(
                context.session_id
            )
            result["cache_memory"] = await self.get_cache_memory(
                context.session_id, hours=1
            )
            if context.workflow_id:
                result["deep_memory"] = await self.search_deep_memory(
                    query=context.workflow_id, k=5
                )
            result["active_pafs"] = self.get_active_pafs()
        else:  # AUGSTER_RIGOROUS
            # Comprehensive: Full session + 24h cache + extensive deep + all PAFs
            result["session_context"] = await self.get_session_context(
                context.session_id
            )
            result["cache_memory"] = await self.get_cache_memory(
                context.session_id, hours=24
            )
            if context.workflow_id:
                result["deep_memory"] = await self.search_deep_memory(
                    query=context.workflow_id, k=20
                )
            result["active_pafs"] = self.get_active_pafs()

            # Get session groups
            session_group_ids = self.session_groups.get_session_groups(
                context.session_id
            )
            result["session_groups"] = [
                self.session_groups.get_group(gid) for gid in session_group_ids
            ]

        return result

    async def _load_decompose_context(
        self, context: WorkflowContext, mode: WorkflowMode
    ) -> dict[str, Any]:
        """Load context for Decompose stage."""
        result: dict[str, Any] = {}

        if not context.session_id or mode == WorkflowMode.RAPID:
            # Skip decompose in rapid mode or if no session
            return result

        # Standard and Augster-Rigorous
        result["session_context"] = await self.get_session_context(
            context.session_id, limit=20
        )
        result["active_pafs"] = self.get_active_pafs()

        if mode == WorkflowMode.AUGSTER_RIGOROUS and context.workflow_id:
            result["deep_memory"] = await self.search_deep_memory(
                query=context.workflow_id, memory_type="pattern", k=5
            )

        return result

    async def _load_plan_context(
        self, context: WorkflowContext, mode: WorkflowMode
    ) -> dict[str, Any]:
        """Load context for Plan stage."""
        result: dict[str, Any] = {}

        if not context.session_id:
            return result

        if mode == WorkflowMode.RAPID:
            # Minimal planning in rapid mode
            result["session_context"] = await self.get_session_context(
                context.session_id, limit=5
            )
            return result

        # Standard and Augster-Rigorous
        result["session_context"] = await self.get_session_context(context.session_id)
        result["cache_memory"] = await self.get_cache_memory(
            context.session_id, hours=1
        )
        result["active_pafs"] = self.get_active_pafs()

        if mode == WorkflowMode.AUGSTER_RIGOROUS and context.workflow_id:
            result["deep_memory"] = await self.search_deep_memory(
                query=context.workflow_id, k=10
            )

        return result

    async def _load_implement_context(
        self, context: WorkflowContext, mode: WorkflowMode
    ) -> dict[str, Any]:
        """Load context for Implement stage."""
        result: dict[str, Any] = {}

        if not context.session_id:
            return result

        # All modes: Current session + cache
        result["session_context"] = await self.get_session_context(context.session_id)
        result["cache_memory"] = await self.get_cache_memory(
            context.session_id, hours=1
        )

        # Deep memory not needed during implementation
        # PAFs used for validation only in Augster mode
        if mode == WorkflowMode.AUGSTER_RIGOROUS:
            result["active_pafs"] = self.get_active_pafs()

        return result

    async def _load_validate_context(
        self, context: WorkflowContext, mode: WorkflowMode
    ) -> dict[str, Any]:
        """Load context for Validate stage."""
        result: dict[str, Any] = {}

        if mode == WorkflowMode.RAPID or not context.session_id:
            # No validation context in rapid mode or no session
            return result

        # Session context for validation errors
        result["session_context"] = await self.get_session_context(
            context.session_id, limit=10
        )

        # PAFs for validation
        result["active_pafs"] = self.get_active_pafs()

        return result

    async def _load_reflect_context(
        self, context: WorkflowContext, mode: WorkflowMode
    ) -> dict[str, Any]:
        """Load context for Reflect stage."""
        result: dict[str, Any] = {}

        if mode != WorkflowMode.AUGSTER_RIGOROUS or not context.session_id:
            # Only Augster-Rigorous mode has reflect stage
            return result

        # Full session for reflection
        result["session_context"] = await self.get_session_context(context.session_id)

        # Deep memory for pattern storage
        result["deep_memory_available"] = self.redis_available

        return result

    # ==================== Utility Methods ====================

    def summary(self) -> dict[str, Any]:
        """Get memory system summary.

        Returns:
            Dictionary with system status and statistics
        """
        paf_summary = self.paf_primitive.summary()
        session_summary = self.session_groups.summary()

        return {
            "redis_available": self.redis_available,
            "user_id": self.user_id,
            "paf_store": paf_summary,
            "session_groups": session_summary,
        }
