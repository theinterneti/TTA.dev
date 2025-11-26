"""Core primitives for documentation workflow operations.

This module provides the foundational primitives for the documentation-to-Logseq
integration system, built on TTA.dev's InstrumentedPrimitive pattern.
"""

import asyncio
from pathlib import Path
from typing import Any

import structlog
from pydantic import BaseModel, Field
from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.observability import InstrumentedPrimitive
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

logger = structlog.get_logger(__name__)


class MarkdownDocument(BaseModel):
    """Represents a markdown document with metadata."""

    file_path: Path = Field(description="Source file path")
    content: str = Field(description="Raw markdown content")
    title: str | None = Field(default=None, description="Document title")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Extracted metadata",
    )


class LogseqPage(BaseModel):
    """Logseq page with properties and content."""

    title: str
    content: str
    page_path: Path
    properties: dict[str, Any]
    frontmatter: dict[str, Any]


class FileWatcherPrimitive(InstrumentedPrimitive[dict[str, Any], list[Path]]):
    """Primitive for watching file system changes.

    Monitors specified paths for markdown file changes and returns list of changed files.

    Example:
        >>> watcher = FileWatcherPrimitive(
        ...     paths=["docs/", "packages/*/README.md"],
        ...     debounce_ms=500
        ... )
        >>> context = WorkflowContext(trace_id="watch-123")
        >>> changed_files = await watcher.execute({}, context)
    """

    def __init__(
        self,
        paths: list[str],
        debounce_ms: int = 500,
        name: str = "file_watcher",
    ) -> None:
        """Initialize file watcher primitive.

        Args:
            paths: List of paths or glob patterns to monitor
            debounce_ms: Debounce delay in milliseconds
            name: Primitive name for observability
        """
        super().__init__(name=name)
        self.paths = paths
        self.debounce_ms = debounce_ms

    async def _execute_impl(
        self,
        input_data: dict[str, Any],
        context: WorkflowContext,
    ) -> list[Path]:
        """Watch file system and return changed files.

        Args:
            input_data: Configuration with optional timeout
            context: Workflow context with trace ID

        Returns:
            List of changed markdown file paths
        """
        timeout_seconds = input_data.get("timeout_seconds", 10.0)
        changed_files: set[Path] = set()
        debounce_queue: dict[Path, float] = {}  # file -> last_change_time

        class MarkdownHandler(FileSystemEventHandler):
            """Handler for markdown file changes."""

            def on_modified(self, event: Any) -> None:
                """Handle file modification events."""
                if event.is_directory:
                    return
                path = Path(str(event.src_path))
                if path.suffix == ".md":
                    debounce_queue[path] = asyncio.get_event_loop().time()

            def on_created(self, event: Any) -> None:
                """Handle file creation events."""
                if event.is_directory:
                    return
                path = Path(str(event.src_path))
                if path.suffix == ".md":
                    debounce_queue[path] = asyncio.get_event_loop().time()

        # Start watchdog observer
        observer = Observer()
        handler = MarkdownHandler()

        # Resolve glob patterns and add watchers
        for pattern in self.paths:
            pattern_path = Path(pattern)
            if "*" in pattern:
                # Handle glob patterns like packages/*/README.md
                base_path = Path(str(pattern).split("*")[0].rstrip("/"))
                if base_path.exists():
                    observer.schedule(handler, str(base_path), recursive=True)
                    logger.info(
                        "watching_glob_pattern",
                        pattern=pattern,
                        base_path=str(base_path),
                        trace_id=context.trace_id,
                    )
            elif pattern_path.exists():
                # Watch specific path
                observer.schedule(handler, str(pattern_path), recursive=True)
                logger.info(
                    "watching_path",
                    path=pattern,
                    trace_id=context.trace_id,
                )

        observer.start()
        logger.info(
            "file_watcher_started",
            paths=self.paths,
            debounce_ms=self.debounce_ms,
            timeout_seconds=timeout_seconds,
            trace_id=context.trace_id,
        )

        try:
            # Monitor for changes with debouncing
            start_time = asyncio.get_event_loop().time()
            debounce_seconds = self.debounce_ms / 1000.0

            while True:
                current_time = asyncio.get_event_loop().time()

                # Check timeout
                if current_time - start_time > timeout_seconds:
                    break

                # Process debounced changes
                files_to_add = []
                for file_path, change_time in list(debounce_queue.items()):
                    if current_time - change_time >= debounce_seconds:
                        files_to_add.append(file_path)
                        del debounce_queue[file_path]

                changed_files.update(files_to_add)

                if files_to_add:
                    logger.info(
                        "files_detected",
                        count=len(files_to_add),
                        files=[str(f) for f in files_to_add],
                        trace_id=context.trace_id,
                    )

                # Short sleep to avoid busy waiting
                await asyncio.sleep(0.1)

        finally:
            observer.stop()
            observer.join()
            logger.info(
                "file_watcher_stopped",
                total_files=len(changed_files),
                trace_id=context.trace_id,
            )

        return list(changed_files)


class MarkdownConverterPrimitive(InstrumentedPrimitive[Path, LogseqPage]):
    """Primitive for converting markdown to Logseq format.

    Reads markdown file, extracts metadata, converts links, and produces Logseq page.

    Example:
        >>> converter = MarkdownConverterPrimitive(logseq_path=Path("logseq/pages"))
        >>> context = WorkflowContext(trace_id="convert-123")
        >>> logseq_page = await converter.execute(Path("docs/guide.md"), context)
    """

    def __init__(
        self,
        logseq_path: Path,
        preserve_code_blocks: bool = True,
        convert_links: bool = True,
        name: str = "markdown_converter",
    ) -> None:
        """Initialize markdown converter primitive.

        Args:
            logseq_path: Base path for Logseq pages
            preserve_code_blocks: Whether to preserve code block formatting
            convert_links: Whether to convert markdown links to [[Logseq]] format
            name: Primitive name for observability
        """
        super().__init__(name=name)
        self.logseq_path = logseq_path
        self.preserve_code_blocks = preserve_code_blocks
        self.convert_links = convert_links

    async def _execute_impl(
        self,
        input_data: Path,
        context: WorkflowContext,
    ) -> LogseqPage:
        """Convert markdown file to Logseq format.

        Args:
            input_data: Path to markdown file
            context: Workflow context with trace ID

        Returns:
            LogseqPage with converted content and properties
        """
        file_path = input_data

        logger.info(
            "markdown_conversion_started",
            file=str(file_path),
            trace_id=context.trace_id,
        )

        # Read markdown file
        if not file_path.exists():
            raise FileNotFoundError(f"Markdown file not found: {file_path}")

        content = file_path.read_text(encoding="utf-8")

        # Extract title (first # heading)
        title = self._extract_title(content)

        # Convert to Logseq format
        logseq_content = self._convert_content(content)

        # Generate page path
        page_name = title.replace(" ", "-") if title else file_path.stem
        page_path = self.logseq_path / f"{page_name}.md"

        # Create Logseq page
        logseq_page = LogseqPage(
            title=title or file_path.stem,
            page_path=page_path,
            content=logseq_content,
            properties={
                "source-file": str(file_path),
                "type": "documentation",
            },
            frontmatter={},
        )

        logger.info(
            "markdown_conversion_completed",
            file=str(file_path),
            output_page=str(page_path),
            trace_id=context.trace_id,
        )

        return logseq_page

    def _extract_title(self, content: str) -> str:
        """Extract title from markdown content."""
        for line in content.split("\n"):
            if line.startswith("# "):
                return line[2:].strip()
        return ""

    def _convert_content(self, content: str) -> str:
        """Convert markdown content to Logseq format."""
        # Phase 1.3 will implement full conversion
        # For now, basic pass-through with property header
        return content


class AIMetadataExtractorPrimitive(InstrumentedPrimitive[LogseqPage, LogseqPage]):
    """Primitive for extracting metadata using AI.

    Uses Google Gemini Flash (or Ollama fallback) to analyze document and extract
    structured metadata for Logseq properties.

    Example:
        >>> extractor = AIMetadataExtractorPrimitive(api_key="...")
        >>> context = WorkflowContext(trace_id="ai-123")
        >>> enhanced_page = await extractor.execute(logseq_page, context)
    """

    def __init__(
        self,
        provider: str = "gemini",
        model: str = "gemini-2.0-flash-exp",
        api_key: str | None = None,
        name: str = "ai_metadata_extractor",
    ) -> None:
        """Initialize AI metadata extractor primitive.

        Args:
            provider: AI provider ("gemini" or "ollama")
            model: Model name
            api_key: API key for provider
            name: Primitive name for observability
        """
        super().__init__(name=name)
        self.provider = provider
        self.model = model
        self.api_key = api_key

    async def _execute_impl(
        self,
        input_data: LogseqPage,
        context: WorkflowContext,
    ) -> LogseqPage:
        """Extract metadata from Logseq page using AI.

        Args:
            input_data: LogseqPage to enhance
            context: Workflow context with trace ID

        Returns:
            Enhanced LogseqPage with AI-extracted metadata
        """
        logseq_page = input_data

        logger.info(
            "ai_metadata_extraction_started",
            provider=self.provider,
            model=self.model,
            page=str(logseq_page.page_path),
            trace_id=context.trace_id,
        )

        # Phase 2 will implement AI integration
        # For now, return page unchanged
        enhanced_page = logseq_page.model_copy(deep=True)

        logger.info(
            "ai_metadata_extraction_completed",
            page=str(logseq_page.page_path),
            properties_added=0,
            trace_id=context.trace_id,
        )

        return enhanced_page


class LogseqSyncPrimitive(InstrumentedPrimitive[LogseqPage, Path]):
    """Primitive for syncing LogseqPage to filesystem.

    Writes Logseq page to disk with proper formatting and properties.

    Example:
        >>> syncer = LogseqSyncPrimitive()
        >>> context = WorkflowContext(trace_id="sync-123")
        >>> written_path = await syncer.execute(logseq_page, context)
    """

    def __init__(
        self,
        create_directories: bool = True,
        name: str = "logseq_sync",
    ) -> None:
        """Initialize Logseq sync primitive.

        Args:
            create_directories: Whether to create parent directories
            name: Primitive name for observability
        """
        super().__init__(name=name)
        self.create_directories = create_directories

    async def _execute_impl(
        self,
        input_data: LogseqPage,
        context: WorkflowContext,
    ) -> Path:
        """Write LogseqPage to filesystem.

        Args:
            input_data: LogseqPage to write
            context: Workflow context with trace ID

        Returns:
            Path where page was written
        """
        logseq_page = input_data

        logger.info(
            "logseq_sync_started",
            page=str(logseq_page.page_path),
            trace_id=context.trace_id,
        )

        # Create parent directories if needed
        if self.create_directories:
            logseq_page.page_path.parent.mkdir(parents=True, exist_ok=True)

        # Format content with properties
        full_content = self._format_with_properties(logseq_page)

        # Write to disk
        logseq_page.page_path.write_text(full_content, encoding="utf-8")

        logger.info(
            "logseq_sync_completed",
            page=str(logseq_page.page_path),
            size_bytes=len(full_content),
            trace_id=context.trace_id,
        )

        return logseq_page.page_path

    def _format_with_properties(self, page: LogseqPage) -> str:
        """Format page content with Logseq properties."""
        lines = []

        # Add properties at top
        for key, value in page.properties.items():
            lines.append(f"{key}:: {value}")

        if page.properties:
            lines.append("")  # Blank line after properties

        # Add content
        lines.append(page.content)

        return "\n".join(lines)
