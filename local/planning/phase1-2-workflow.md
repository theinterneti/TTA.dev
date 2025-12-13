# Development Workflow - Phase 1.2: File Watcher

**Next Task:** Implement file watching service
**Estimated Time:** 3-4 hours
**Current Status:** Ready to start

---

## 📋 Task Breakdown

### 1. Create watcher.py Module (1.5 hours)

**File:** `packages/tta-documentation-primitives/src/tta_documentation_primitives/watcher.py`

```python
# Key components:
class DocumentWatcher:
    """Main file watcher for documentation sync."""

    def __init__(self, config: TTADocsConfig):
        """Initialize with configuration."""

    def start(self) -> None:
        """Start watching configured paths."""

    def stop(self) -> None:
        """Stop watching gracefully."""

class MarkdownFileHandler(FileSystemEventHandler):
    """Handle markdown file events."""

    def on_created(self, event):
        """Handle file creation."""

    def on_modified(self, event):
        """Handle file modification."""

class SyncQueue:
    """Debounce and queue sync operations."""

    def enqueue(self, file_path: Path) -> None:
        """Add file to sync queue with debouncing."""

    async def process(self) -> None:
        """Process queued items."""
```

**Dependencies:**
- watchdog.observers.Observer
- watchdog.events.FileSystemEventHandler
- asyncio for debouncing
- structlog for logging

---

### 2. Create Tests (1 hour)

**File:** `packages/tta-documentation-primitives/tests/test_watcher.py`

```python
# Test scenarios:
- test_watcher_starts_successfully
- test_watcher_detects_file_creation
- test_watcher_detects_file_modification
- test_watcher_ignores_non_markdown_files
- test_debouncing_multiple_rapid_changes
- test_graceful_stop
- test_multiple_paths_monitoring
```

**Use pytest-asyncio for async tests.**

---

### 3. Wire Up CLI Commands (0.5 hours)

Update `cli.py` to use the watcher:

```python
@watch.command()
def start() -> None:
    """Start the background file watcher."""
    config = load_config()
    watcher = DocumentWatcher(config)

    console.print("[bold green]Starting file watcher...[/bold green]")
    console.print(f"Monitoring: {', '.join(config.docs_paths)}")

    watcher.start()

    # Keep running until interrupted
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping file watcher...[/yellow]")
        watcher.stop()
```

---

### 4. Create Example Script (0.5 hours)

**File:** `packages/tta-documentation-primitives/examples/basic_watcher.py`

```python
"""Example: Basic file watcher usage."""

import asyncio
from pathlib import Path
from tta_documentation_primitives import DocumentWatcher
from tta_documentation_primitives.config import load_config

async def main():
    # Load configuration
    config = load_config()

    # Create watcher
    watcher = DocumentWatcher(config)

    print(f"Watching: {config.docs_paths}")
    print("Press Ctrl+C to stop...")

    # Start watching
    watcher.start()

    try:
        # Keep running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping watcher...")
        watcher.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

---

### 5. Update Documentation (0.5 hours)

Add to README.md:

```markdown
## File Watcher

The file watcher monitors configured paths for markdown file changes and
automatically queues them for synchronization.

### Configuration

Configure watched paths in `.tta-docs.json`:

\`\`\`json
{
  "docs_paths": [
    "docs/",
    "packages/*/README.md"
  ],
  "sync": {
    "auto": true,
    "debounce_ms": 500
  }
}
\`\`\`

### Usage

\`\`\`python
from tta_documentation_primitives import DocumentWatcher
from tta_documentation_primitives.config import load_config

config = load_config()
watcher = DocumentWatcher(config)
watcher.start()
\`\`\`

### CLI

\`\`\`bash
# Start background watcher
tta-docs watch start

# Check status
tta-docs watch status

# Stop watcher
tta-docs watch stop
\`\`\`
```

---

## 🎯 Acceptance Criteria

- [ ] `DocumentWatcher` class implemented with start/stop
- [ ] `MarkdownFileHandler` detects .md file creation/modification
- [ ] `SyncQueue` implements 500ms debouncing
- [ ] Watcher monitors paths from config
- [ ] Tests pass with >80% coverage
- [ ] CLI commands work: `tta-docs watch start/stop/status`
- [ ] Example script demonstrates usage
- [ ] Documentation updated

---

## 🧪 Testing Strategy

### Manual Testing

```bash
# Terminal 1: Start watcher
uv run tta-docs watch start

# Terminal 2: Create/modify files
echo "# Test" > docs/test.md
echo "Updated" >> docs/test.md

# Verify: Terminal 1 shows detected changes
```

### Automated Testing

```bash
# Run tests
uv run pytest tests/test_watcher.py -v

# With coverage
uv run pytest tests/test_watcher.py --cov=src/tta_documentation_primitives/watcher

# Watch mode (for development)
uv run pytest tests/test_watcher.py -v --ff
```

---

## 📝 Implementation Notes

### Debouncing Strategy

```python
class SyncQueue:
    def __init__(self, debounce_ms: int = 500):
        self.queue: dict[Path, float] = {}  # path -> timestamp
        self.debounce_ms = debounce_ms

    def enqueue(self, file_path: Path) -> None:
        """Add file to queue with timestamp."""
        self.queue[file_path] = time.time()

    async def process(self) -> None:
        """Process items that haven't changed in debounce_ms."""
        while True:
            current_time = time.time()
            to_process = []

            for path, timestamp in list(self.queue.items()):
                if (current_time - timestamp) * 1000 >= self.debounce_ms:
                    to_process.append(path)
                    del self.queue[path]

            for path in to_process:
                # Trigger sync (placeholder for now)
                logger.info("sync_queued", file=str(path))

            await asyncio.sleep(0.1)  # Check every 100ms
```

### Path Globbing

```python
from pathlib import Path

def expand_paths(path_patterns: list[str]) -> list[Path]:
    """Expand glob patterns to concrete paths."""
    paths = []
    for pattern in path_patterns:
        if "*" in pattern:
            # Glob pattern
            paths.extend(Path(".").glob(pattern))
        else:
            # Direct path
            paths.append(Path(pattern))
    return [p.resolve() for p in paths if p.exists()]
```

---

## 🚀 Quick Start Commands

```bash
# Navigate to package
cd packages/tta-documentation-primitives

# Create watcher.py
touch src/tta_documentation_primitives/watcher.py

# Create test file
touch tests/test_watcher.py

# Create example
mkdir -p examples
touch examples/basic_watcher.py

# Start development
# (Edit watcher.py in your editor)

# Run tests as you develop
uv run pytest tests/test_watcher.py -v --ff
```

---

## 📚 Resources

- **watchdog docs:** https://python-watchdog.readthedocs.io/
- **pytest-asyncio:** https://pytest-asyncio.readthedocs.io/
- **structlog:** https://www.structlog.org/

---

## ⏭️ After This Task

**Phase 1.3:** Build markdown to Logseq converter (4-5 hours)

The converter will take file paths from the watcher queue and:
1. Read markdown file
2. Extract metadata (title, frontmatter)
3. Convert links to Logseq format
4. Preserve code blocks
5. Add Logseq properties
6. Write to logseq/pages/

---

**Ready to start?** Let's implement the file watcher! 🎯


---
**Logseq:** [[TTA.dev/Local/Planning/Phase1-2-workflow]]
