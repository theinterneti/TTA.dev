#!/usr/bin/env python3
"""Fix import structure across TTA.dev codebase."""

import re
from pathlib import Path

# Define import mapping
IMPORT_MAPPINGS = {
    r"from tta_dev_primitives\.core": "from primitives.core",
    r"from tta_dev_primitives\.recovery": "from primitives.recovery",
    r"from tta_dev_primitives\.observability": "from primitives.observability",
    r"from tta_dev_primitives\.orchestration": "from primitives.orchestration",
    r"from tta_dev_primitives\.integrations": "from primitives.integrations",
    r"from tta_dev_primitives\.adaptive": "from primitives.adaptive",
    r"from tta_dev_primitives\.lifecycle": "from primitives.lifecycle",
    r"from tta_dev_primitives\.config": "from primitives.config",
    r"from tta_dev_primitives\.testing": "from primitives.testing",
    r"from tta_dev_primitives\.analysis": "from primitives.analysis",
    r"from tta_dev_primitives\.speckit": "from primitives.speckit",
    r"from tta_dev_primitives\.knowledge": "from primitives.knowledge",
    r"from tta_dev_primitives\.ace": "from primitives.ace",
    r"from tta_dev_primitives\.cli": "from primitives.cli",
    r"from tta_dev_primitives\.research": "from primitives.research",
    r"from tta_dev_primitives\.extensions": "from primitives.extensions",
    r"from tta_dev_primitives\.mcp_server": "from primitives.mcp_server",
    r"from tta_dev_primitives\.benchmarking": "from primitives.benchmarking",
    r"from tta_dev_primitives\.package_managers": "from primitives.package_managers",
    r"from tta_dev_primitives import": "from primitives import",
    r"import tta_dev_primitives\.": "import primitives.",
    r"import tta_dev_primitives": "import primitives",
}


def fix_imports_in_file(file_path: Path) -> bool:
    """Fix imports in a single file."""
    try:
        content = file_path.read_text()
        original = content

        for old_pattern, new_import in IMPORT_MAPPINGS.items():
            content = re.sub(old_pattern, new_import, content)

        if content != original:
            file_path.write_text(content)
            print(f"✓ Fixed: {file_path}")
            return True
        return False
    except Exception as e:
        print(f"✗ Error fixing {file_path}: {e}")
        return False


def main():
    """Fix all imports in tta-dev directory."""
    tta_dev = Path("/home/thein/repos/TTA.dev/tta-dev")

    if not tta_dev.exists():
        print(f"Error: {tta_dev} does not exist")
        return

    python_files = list(tta_dev.rglob("*.py"))
    fixed_count = 0

    print(f"Processing {len(python_files)} Python files...")

    for py_file in python_files:
        if fix_imports_in_file(py_file):
            fixed_count += 1

    print(f"\n✓ Fixed {fixed_count} files")


if __name__ == "__main__":
    main()
