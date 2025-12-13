---
name: Complete File Watcher Implementation for tta-documentation-primitives
about: Implement and integrate the FileWatcherPrimitive for real-time documentation synchronization
title: 'feat(tta-docs): Complete FileWatcherPrimitive integration and workflow'
labels: enhancement, tta-documentation-primitives, phase-1.2
assignees: ''
---

## 📋 Overview

Complete the implementation of the FileWatcherPrimitive for real-time documentation synchronization between TTA.dev documentation files and Logseq knowledge base.

**Status:** FileWatcherPrimitive structure is complete with watchdog library integration, but actual file watching workflow is on hold pending further implementation phases.

**Related TODOs:**
- ✅ Phase 1.1: Package structure complete (10/10 tests passing)
- ✅ Phase 1.2: FileWatcherPrimitive implemented
- 🔲 Phase 1.3: MarkdownConverterPrimitive (next)
- 🔲 Phase 1.4: CLI integration

---

## 🎯 Objectives

### 1. Complete FileWatcherPrimitive Integration
- [x] Implement watchdog-based file monitoring
- [x] Add debouncing (500ms configurable)
- [x] Support glob patterns (`packages/*/README.md`)
- [x] Filter .md files specifically
- [x] Use asyncio queue for event handling
- [ ] **Create integration test with actual file changes**
- [ ] **Test glob pattern expansion**
- [ ] **Verify debouncing behavior with rapid changes**

### 2. Wire to CLI Commands
- [ ] Connect `tta-docs watch start` to FileWatcherPrimitive
- [ ] Implement background daemon mode
- [ ] Add stop/status commands
- [ ] Store PID file for daemon management
- [ ] Handle graceful shutdown (SIGTERM, SIGINT)

### 3. Integrate with Sync Workflow
- [ ] Create `create_watch_workflow()` in workflows.py
- [ ] Chain: FileWatcher >> MarkdownConverter >> LogseqSync
- [ ] Add batch processing for multiple files
- [ ] Implement error recovery (continue on file errors)

### 4. Production Features
- [ ] Add configuration for watch paths (tta-docs.json)
- [ ] Implement ignore patterns (.gitignore style)
- [ ] Add file change notifications (optional: desktop)
- [ ] Create metrics: files_watched, sync_count, error_rate

---

## 🏗️ Implementation Details

### Current State

**File:** `packages/tta-documentation-primitives/src/tta_documentation_primitives/primitives.py`

```python
class FileWatcherPrimitive(InstrumentedPrimitive[dict[str, Any], list[Path]]):
    """✅ IMPLEMENTED - Monitor filesystem for markdown changes with debouncing."""

    # Features:
    # - Watchdog Observer integration
    # - Debounce queue with configurable delay
    # - Glob pattern support
    # - .md file filtering
    # - Asyncio event loop integration
    # - Full observability (trace IDs, structured logs)
```

### Workflow Integration Example

```python
from tta_documentation_primitives import (
    FileWatcherPrimitive,
    create_production_sync_workflow,
)

# Create watch workflow
watcher = FileWatcherPrimitive(
    paths=["docs/", "packages/*/README.md"],
    debounce_ms=500,
)

sync_workflow = create_production_sync_workflow()

# Chain: watch → sync
watch_sync = watcher >> sync_workflow

# Execute (runs until timeout or stopped)
context = WorkflowContext(trace_id="watch-daemon")
changed_files = await watch_sync.execute(
    {"timeout_seconds": 3600},  # Watch for 1 hour
    context,
)
```

### CLI Integration Target

```bash
# Start watching (daemon mode)
tta-docs watch start

# Check status
tta-docs watch status

# Stop watching
tta-docs watch stop

# Watch with custom config
tta-docs watch start --config custom-tta-docs.json
```

---

## 🧪 Testing Requirements

### Unit Tests (Already Passing)
- ✅ `test_file_watcher_primitive` - Basic initialization
- ✅ All 10 tests passing

### Integration Tests (TODO)
```python
@pytest.mark.asyncio
async def test_file_watcher_detects_changes(tmp_path):
    """Test that FileWatcher detects actual file changes."""
    # Create test file
    test_file = tmp_path / "test.md"
    test_file.write_text("# Original")

    # Start watcher
    watcher = FileWatcherPrimitive(paths=[str(tmp_path)])

    # Modify file in background
    asyncio.create_task(modify_file_after_delay(test_file, 0.2))

    # Execute watcher (with short timeout)
    result = await watcher.execute({"timeout_seconds": 1.0}, context)

    # Verify detection
    assert test_file in result
```

### Manual Testing Checklist
- [ ] Create/modify .md file → triggers sync
- [ ] Rapid changes (5 files in 100ms) → debounced to single sync
- [ ] Glob pattern `packages/*/README.md` → watches all package READMEs
- [ ] Non-.md file change → ignored
- [ ] Stop watcher → cleanup completes, no leaked threads

---

## 📝 Dependencies

### Prerequisites
- ✅ watchdog>=4.0.0 installed
- ✅ asyncio integration working
- ✅ InstrumentedPrimitive base class
- 🔲 Phase 1.3: MarkdownConverterPrimitive (blocks workflow integration)
- 🔲 Phase 1.4: CLI commands (blocks user interface)

### Related Issues
- Link to Phase 1.3 issue (MarkdownConverter)
- Link to Phase 1.4 issue (CLI integration)

---

## 🚀 Next Steps

### Immediate (After Phase 1.3)
1. Create integration test with tmp_path
2. Test glob pattern resolution
3. Verify debouncing with multiple rapid changes

### Short-term (Phase 1.4)
1. Wire to CLI commands
2. Add daemon mode with PID file
3. Implement graceful shutdown

### Long-term (Phase 4)
1. Auto-sync on save (VS Code integration)
2. Bidirectional sync (Logseq → docs)
3. Conflict resolution

---

## 📊 Success Criteria

- [ ] Integration test covers actual file change detection
- [ ] Debouncing verified with rapid changes (< 500ms apart)
- [ ] Glob patterns correctly expand to multiple directories
- [ ] CLI commands work: start, stop, status
- [ ] Daemon mode runs in background
- [ ] Graceful shutdown on SIGTERM
- [ ] Metrics exported (files watched, syncs performed)
- [ ] No memory leaks after 24-hour run
- [ ] Performance: < 100ms latency from file change to sync start

---

## 🔗 Related Files

- `packages/tta-documentation-primitives/src/tta_documentation_primitives/primitives.py` (FileWatcherPrimitive)
- `packages/tta-documentation-primitives/src/tta_documentation_primitives/workflows.py` (workflow integration)
- `packages/tta-documentation-primitives/src/tta_documentation_primitives/cli.py` (CLI commands)
- `packages/tta-documentation-primitives/tests/test_primitives.py` (tests)

---

## 💡 Notes

- FileWatcherPrimitive is fully implemented but not yet integrated into workflows
- Current tests use mocks; real integration tests with tmp_path needed
- Consider rate limiting: max X syncs per minute to prevent system overload
- Watchdog Observer uses platform-specific backends (inotify on Linux)
- Debouncing prevents duplicate syncs from editors that save multiple times

---

**Estimated Time:** 2-3 hours (after Phase 1.3 complete)
**Priority:** Medium (blocked by Phase 1.3)
**Complexity:** Medium


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/.github/Issue_template/File-watcher-implementation]]
