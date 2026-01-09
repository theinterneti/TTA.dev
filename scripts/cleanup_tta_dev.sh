#!/bin/bash
set -euo pipefail

# TTA.dev Knowledge Base Cleanup Script
# Auto-generated: 2026-01-08

REPO_ROOT="/home/thein/repos/TTA.dev"
BACKUP_FILE="$HOME/TTA.dev-backup-$(date +%Y%m%d-%H%M%S).tar.gz"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

cd "$REPO_ROOT" || exit 1

echo "╔════════════════════════════════════════════════════╗"
echo "║                                                    ║"
echo "║   TTA.dev Knowledge Base Cleanup                  ║"
echo "║   Target: Remove 295MB of redundant archives      ║"
echo "║                                                    ║"
echo "╚════════════════════════════════════════════════════╝"
echo

# Phase 0: Safety backup
log_info "Phase 0: Creating safety backup..."
if tar -czf "$BACKUP_FILE" . 2>/dev/null; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log_info "✓ Backup created: $BACKUP_FILE"
    log_info "  Backup size: $BACKUP_SIZE"
else
    log_error "Failed to create backup. Aborting."
    exit 1
fi
echo

# Phase 1: Check current state
log_info "Phase 1: Analyzing current state..."
INITIAL_SIZE=$(du -sh . | cut -f1)
ARCHIVE_SIZE=$(du -sh _archive 2>/dev/null | cut -f1)
log_info "  Repository size: $INITIAL_SIZE"
log_info "  Archive size: $ARCHIVE_SIZE"
echo

# Phase 2: Remove archive bloat
log_info "Phase 2: Purging archive directories (295MB target)..."

REMOVED=0

# Package archives (284MB)
if [ -d "_archive/packages" ]; then
    SIZE=$(du -sh _archive/packages | cut -f1)
    log_info "  Removing _archive/packages ($SIZE)..."
    rm -rf _archive/packages
    ((REMOVED++))
fi

if [ -d "_archive/packages-under-review" ]; then
    SIZE=$(du -sh _archive/packages-under-review | cut -f1)
    log_info "  Removing _archive/packages-under-review ($SIZE)..."
    rm -rf _archive/packages-under-review
    ((REMOVED++))
fi

if [ -d "_archive/packages_backup" ]; then
    SIZE=$(du -sh _archive/packages_backup | cut -f1)
    log_info "  Removing _archive/packages_backup ($SIZE)..."
    rm -rf _archive/packages_backup
    ((REMOVED++))
fi

# Duplicate artifacts (8MB)
if [ -d "_archive/nested_copies" ]; then
    SIZE=$(du -sh _archive/nested_copies | cut -f1)
    log_info "  Removing _archive/nested_copies ($SIZE)..."
    rm -rf _archive/nested_copies
    ((REMOVED++))
fi

if [ -d "_archive/logseq_backup" ]; then
    log_info "  Removing _archive/logseq_backup..."
    rm -rf _archive/logseq_backup
    ((REMOVED++))
fi

if [ -d "_archive/logseq_backup_20251220" ]; then
    log_info "  Removing _archive/logseq_backup_20251220..."
    rm -rf _archive/logseq_backup_20251220
    ((REMOVED++))
fi

# Obsolete projects
if [ -d "_archive/legacy-tta-game" ]; then
    log_info "  Removing _archive/legacy-tta-game..."
    rm -rf _archive/legacy-tta-game
    ((REMOVED++))
fi

# Duplicate status reports (1.6MB)
for dir in status-reports status-reports-2025 status-reports-docs reports; do
    if [ -d "_archive/$dir" ]; then
        log_info "  Removing _archive/$dir..."
        rm -rf "_archive/$dir"
        ((REMOVED++))
    fi
done

# Duplicate planning
for dir in planning speckit-planning; do
    if [ -d "_archive/$dir" ]; then
        log_info "  Removing _archive/$dir..."
        rm -rf "_archive/$dir"
        ((REMOVED++))
    fi
done

log_info "  ✓ Removed $REMOVED archive directories"
echo

# Phase 3: Archive old status reports
log_info "Phase 3: Archiving old status reports..."
if [ -d "docs/status-reports" ]; then
    cd docs/status-reports
    mkdir -p ../../_archive/historical

    OLD_REPORTS=$(find . -name "*.md" -not -newermt "2025-01-01" 2>/dev/null | wc -l)
    if [ "$OLD_REPORTS" -gt 0 ]; then
        log_info "  Found $OLD_REPORTS old reports (pre-2025)..."
        tar -czf ../../_archive/historical/status-reports-pre-2025.tar.gz \
            $(find . -name "*.md" -not -newermt "2025-01-01") 2>/dev/null || true
        find . -name "*.md" -not -newermt "2025-01-01" -delete 2>/dev/null || true
        log_info "  ✓ Archived to historical/status-reports-pre-2025.tar.gz"
    else
        log_info "  ✓ No old status reports found (all are recent)"
    fi
    cd ../..
else
    log_warn "  docs/status-reports not found"
fi
echo

# Phase 4: Final state
log_info "Phase 4: Cleanup complete!"
FINAL_SIZE=$(du -sh . | cut -f1)
ARCHIVE_SIZE_AFTER=$(du -sh _archive 2>/dev/null | cut -f1)

echo
echo "╔════════════════════════════════════════════════════╗"
echo "║                                                    ║"
echo "║   Cleanup Results                                  ║"
echo "║                                                    ║"
echo "╚════════════════════════════════════════════════════╝"
echo "  Initial size:     $INITIAL_SIZE"
echo "  Final size:       $FINAL_SIZE"
echo "  Archive before:   $ARCHIVE_SIZE"
echo "  Archive after:    $ARCHIVE_SIZE_AFTER"
echo "  Backup location:  $BACKUP_FILE"
echo "╚════════════════════════════════════════════════════╝"
echo

log_info "Next steps:"
echo "  1. Review changes: git status"
echo "  2. Commit changes: git add -A && git commit"
echo "  3. Run git gc: git gc --aggressive --prune=now"
echo "  4. Remove backup: rm $BACKUP_FILE (after verifying)"
echo

log_info "Cleanup script completed successfully!"
exit 0
