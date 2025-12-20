# Knowledge Base Safety Architecture

**Document Created:** 2025-12-20
**Status:** Active
**Related Issues:** #175 (inject_citation Postmortem)

---

## Background

On 2025-12-12, the `inject_citation()` function in `logseq_graph_sync.py` caused catastrophic damage to the TTA.dev codebase, deleting 227,297 lines across 1,155 files. This document establishes architectural safeguards to prevent similar incidents.

## Root Cause Analysis

The `inject_citation()` function violated a fundamental principle: **Knowledge base systems should NEVER modify source code files.**

**What Happened:**
1. The function attempted to add Logseq citations to source files
2. A bug caused it to overwrite files with minimal content instead
3. The damage was committed (4fba161a) before detection
4. Recovery required restoring 650+ files from an earlier commit

## Architectural Principles

### 1. One-Way Data Flow (Code → KB)

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Codebase   │ ──► │  Sync Process    │ ──► │  Knowledge Base │
│  (Source)   │     │  (Read-Only)     │     │  (Logseq)       │
└─────────────┘     └──────────────────┘     └─────────────────┘
       ▲                                              │
       │                     NEVER                    │
       └──────────────────────────────────────────────┘
```

**The sync process MUST:**
- Only READ from the codebase
- Only WRITE to the knowledge base (Logseq pages)
- Never modify source files

### 2. Directory Separation

```
TTA.dev/                      # Source of truth (code)
├── platform/                 # Package source code
├── docs/                     # Documentation (can be read)
├── tests/                    # Test code
└── scripts/                  # Utility scripts

~/repos/TTA-notes/           # Knowledge base (separate repo)
├── pages/                   # Logseq pages (writable)
└── journals/                # Logseq journals (writable)
```

**Rule:** The sync tool should never have write access to `TTA.dev/`.

### 3. Safe File Patterns

**Files the sync tool can READ from TTA.dev:**
- `*.py` - Python source (extract metadata)
- `*.md` - Documentation (copy to KB)
- `*.json` - Config files (read settings)
- `*.toml` - Package configs (version info)

**Files the sync tool can WRITE to TTA-notes:**
- `pages/*.md` - Logseq page files
- `journals/*.md` - Logseq journal entries

## Implementation Safeguards

### Safeguard 1: Remove File Writing from Codebase Operations

The `inject_citation()` function has been disabled and replaced with a warning:

```python
def inject_citation(file_path: Path, page_name: str):
    """DISABLED - See KB_SAFETY_ARCHITECTURE.md"""
    print(f"⚠️ inject_citation is DISABLED - would have modified {file_path.name}")
    return
```

### Safeguard 2: Path Validation

Add validation to ensure we never write to source directories:

```python
PROTECTED_PATHS = [
    "platform/",
    "apps/",
    "tests/",
    "scripts/",
    "docs/",
    ".github/",
]

def is_safe_write_path(path: Path) -> bool:
    """Validate that a path is safe to write to."""
    resolved = path.resolve()
    repo_root = Path(__file__).parents[5].resolve()

    # Never write inside the repository
    if resolved.is_relative_to(repo_root):
        return False

    # Only allow writing to Logseq directories
    logseq_root = Path(os.path.expanduser("~/repos/TTA-notes"))
    return resolved.is_relative_to(logseq_root)
```

### Safeguard 3: Pre-Commit Hook Validation

Add a pre-commit check to detect accidental codebase modifications:

```yaml
# .pre-commit-config.yaml addition
- repo: local
  hooks:
    - id: check-kb-sync-safety
      name: KB Sync Safety Check
      entry: python scripts/check_kb_sync_safety.py
      language: python
      files: "logseq_graph_sync\\.py$"
```

### Safeguard 4: Git Ignore for KB State Files

Ensure KB sync state files don't accidentally overwrite code:

```gitignore
# KB sync state (should never be in codebase)
.logseq_sync_state/
*.logseq_sync
```

## Migration Path

### Phase 1: Disable Dangerous Functions ✅ (Completed)
- [x] Disable `inject_citation()` with explicit warning
- [x] Document the incident (GitHub issue #175)

### Phase 2: Add Safeguards (In Progress)
- [ ] Implement `is_safe_write_path()` validation
- [ ] Add pre-commit hook for KB sync safety
- [ ] Create separate execution context for KB sync

### Phase 3: Architectural Separation
- [ ] Move KB sync to separate repository/module
- [ ] Implement read-only mount for codebase access
- [ ] Add comprehensive logging and audit trail

## Testing the Safeguards

### Unit Test: Path Validation

```python
def test_protected_paths_cannot_be_written():
    """Ensure source code paths are protected."""
    dangerous_paths = [
        Path("platform/primitives/src/file.py"),
        Path("tests/test_file.py"),
        Path("docs/README.md"),
    ]

    for path in dangerous_paths:
        assert not is_safe_write_path(path), f"Path should be protected: {path}"

def test_logseq_paths_can_be_written():
    """Ensure Logseq paths are allowed."""
    safe_paths = [
        Path("~/repos/TTA-notes/pages/Test.md"),
        Path("~/repos/TTA-notes/journals/2025_01_01.md"),
    ]

    for path in safe_paths:
        assert is_safe_write_path(path.expanduser()), f"Path should be allowed: {path}"
```

## Monitoring and Alerts

### Git Diff Monitoring

Before any commit from KB sync operations, validate:

```bash
# Check for unexpected file modifications
git diff --name-only | while read file; do
  if [[ "$file" == platform/* ]] || [[ "$file" == tests/* ]]; then
    echo "❌ DANGER: KB sync modified source file: $file"
    exit 1
  fi
done
```

### Audit Log

All KB sync operations should be logged:

```python
def log_sync_operation(operation: str, source: Path, target: Path):
    """Log sync operation for audit trail."""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "operation": operation,
        "source": str(source),
        "target": str(target),
        "user": os.getenv("USER"),
    }
    audit_file = Path("~/.logseq_sync_audit.jsonl").expanduser()
    with audit_file.open("a") as f:
        f.write(json.dumps(log_entry) + "\n")
```

## Summary

The key architectural change is enforcing **one-way data flow**:

| Direction | Status | Action |
|-----------|--------|--------|
| Code → KB | ✅ Allowed | Read from codebase, write to Logseq |
| KB → Code | ❌ Forbidden | Never modify source files |

This prevents any future incident where knowledge base synchronization could damage source code.

---

**Logseq:** [[TTA.dev/Architecture/KB Safety Architecture]]
