#!/bin/bash
# Pre-commit hook for KB validation
# Install: ln -s ../../scripts/kb-validation-hook.sh .git/hooks/pre-commit

set -e

echo "🔍 Running KB validation..."

# Check if tta-kb-automation is available
if ! python -c "import tta_kb_automation" 2>/dev/null; then
    echo "⚠️  tta-kb-automation not installed, skipping KB validation"
    exit 0
fi

# Get staged files
STAGED_MD_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E 'logseq/.*\.md$' || true)

if [ -z "$STAGED_MD_FILES" ]; then
    echo "✅ No KB files changed, skipping validation"
    exit 0
fi

echo "Validating changed KB files:"
echo "$STAGED_MD_FILES"

# Run quick link validation on changed files only
TEMP_REPORT=$(mktemp)

python -c "
import asyncio
import sys
from pathlib import Path
from tta_kb_automation import ValidateLinks, WorkflowContext

async def main():
    files = '''$STAGED_MD_FILES'''.strip().split('\n')
    files = [Path(f) for f in files if f]

    if not files:
        print('✅ No files to validate')
        return 0

    validator = ValidateLinks(kb_root=Path('logseq'))
    context = WorkflowContext(workflow_id='pre-commit-check')

    broken_links = []
    for file in files:
        content = file.read_text()
        links = [line for line in content.split('\n') if '[[' in line or '](' in line]

        for link in links:
            # Simple extraction (LinkExtractor would be better)
            if '[[' in link and ']]' in link:
                start = link.find('[[')
                end = link.find(']]', start)
                link_text = link[start+2:end]

                # Quick check if referenced page exists
                potential_paths = [
                    Path('logseq/pages') / f'{link_text}.md',
                    Path('logseq/pages') / f'{link_text.replace(\"/\", \"___\")}.md',
                ]

                exists = any(p.exists() for p in potential_paths)
                if not exists:
                    broken_links.append((file, link_text))

    if broken_links:
        print(f'❌ Found {len(broken_links)} broken links:')
        for file, link in broken_links[:10]:
            print(f'  - {file}: [[{link}]]')
        if len(broken_links) > 10:
            print(f'  ... and {len(broken_links) - 10} more')
        return 1

    print(f'✅ All links validated in {len(files)} files')
    return 0

sys.exit(asyncio.run(main()))
" > "$TEMP_REPORT" 2>&1

EXIT_CODE=$?
cat "$TEMP_REPORT"
rm "$TEMP_REPORT"

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "💡 Fix broken links or run: git commit --no-verify (not recommended)"
    exit 1
fi

echo "✅ KB validation passed"
exit 0
