#!/usr/bin/env bash
#
# Setup TTA Audit Sandbox
#
# Purpose: Create isolated environment for auditing TTA repository
# Usage: ./scripts/setup-tta-audit-sandbox.sh [sandbox-path]
#
# Date: November 8, 2025

set -euo pipefail

# Configuration
SANDBOX_BASE="${1:-$HOME/sandbox}"
SANDBOX_NAME="tta-audit"
SANDBOX_PATH="$SANDBOX_BASE/$SANDBOX_NAME"
TTA_REPO_URL="https://github.com/theinterneti/TTA.git"
ANALYSIS_DIR="$SANDBOX_PATH/analysis"
SCRIPTS_DIR="$SANDBOX_PATH/scripts"
WORKSPACE_DIR="$SANDBOX_PATH/workspace"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check for git
    if ! command -v git &> /dev/null; then
        log_error "git is not installed. Please install git first."
        exit 1
    fi

    # Check for uv
    if ! command -v uv &> /dev/null; then
        log_error "uv is not installed. Please install uv first:"
        echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi

    # Check Python version
    if ! python3 --version | grep -qE "3\.(11|12|13)"; then
        log_warn "Python 3.11+ recommended. Current: $(python3 --version)"
    fi

    log_info "Prerequisites check passed ✓"
}

# Create sandbox directory structure
create_sandbox_structure() {
    log_info "Creating sandbox directory structure..."

    # Create base directories
    mkdir -p "$SANDBOX_BASE"
    mkdir -p "$SANDBOX_PATH"
    mkdir -p "$ANALYSIS_DIR"
    mkdir -p "$SCRIPTS_DIR"
    mkdir -p "$WORKSPACE_DIR"

    log_info "Created directories:"
    log_info "  - $SANDBOX_PATH (main sandbox)"
    log_info "  - $ANALYSIS_DIR (analysis reports)"
    log_info "  - $SCRIPTS_DIR (analysis scripts)"
    log_info "  - $WORKSPACE_DIR (scratch area)"
}

# Clone TTA repository
clone_tta_repository() {
    log_info "Cloning TTA repository..."

    if [ -d "$SANDBOX_PATH/TTA" ]; then
        log_warn "TTA repository already exists. Skipping clone."
        log_warn "To re-clone, delete $SANDBOX_PATH/TTA first."
        return 0
    fi

    cd "$SANDBOX_PATH"
    git clone "$TTA_REPO_URL" TTA

    log_info "Cloned TTA repository to $SANDBOX_PATH/TTA ✓"
}

# Setup Python environment
setup_python_environment() {
    log_info "Setting up Python environment..."

    cd "$SANDBOX_PATH/TTA"

    # Sync dependencies
    if [ -f "pyproject.toml" ]; then
        log_info "Found pyproject.toml, syncing dependencies..."
        uv sync --all-extras 2>&1 | tee "$ANALYSIS_DIR/dependency-sync.log"
    else
        log_warn "No pyproject.toml found. Manual dependency setup may be needed."
    fi

    log_info "Python environment setup complete ✓"
}

# Run initial analysis
run_initial_analysis() {
    log_info "Running initial analysis..."

    cd "$SANDBOX_PATH/TTA"

    # Package statistics
    log_info "Analyzing package structure..."
    {
        echo "# TTA Package Statistics"
        echo "Generated: $(date)"
        echo ""
        echo "## Package Line Counts"
        echo ""

        for pkg in packages/*; do
            if [ -d "$pkg" ]; then
                pkg_name=$(basename "$pkg")
                line_count=$(find "$pkg" -name "*.py" -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $1}' || echo "0")
                file_count=$(find "$pkg" -name "*.py" | wc -l)
                echo "- **$pkg_name**: $line_count lines in $file_count files"
            fi
        done

        echo ""
        echo "## Test Structure"
        echo ""

        if [ -d "tests" ]; then
            test_count=$(find tests -name "test_*.py" -o -name "*_test.py" | wc -l)
            echo "- Test files found: $test_count"
        else
            echo "- No tests/ directory found"
        fi

        echo ""
        echo "## Configuration Files"
        echo ""

        for config in pyproject.toml setup.py requirements.txt .env*; do
            if [ -e "$config" ]; then
                echo "- Found: $config"
            fi
        done
    } > "$ANALYSIS_DIR/package-statistics.md"

    log_info "Created: $ANALYSIS_DIR/package-statistics.md"

    # List all Python classes
    log_info "Extracting class definitions..."
    grep -r "^class " packages/ --include="*.py" | \
        sed 's/:/: /' | \
        sort > "$ANALYSIS_DIR/class-list.txt"

    class_count=$(wc -l < "$ANALYSIS_DIR/class-list.txt")
    log_info "Found $class_count class definitions"
    log_info "Created: $ANALYSIS_DIR/class-list.txt"

    # Directory structure
    log_info "Documenting directory structure..."
    tree -d -L 3 packages/ > "$ANALYSIS_DIR/directory-structure.txt" 2>/dev/null || \
        find packages/ -type d | head -50 > "$ANALYSIS_DIR/directory-structure.txt"

    log_info "Created: $ANALYSIS_DIR/directory-structure.txt"
}

# Create analysis scripts
create_analysis_scripts() {
    log_info "Creating analysis scripts..."

    # Package analyzer script
    cat > "$SCRIPTS_DIR/analyze_package.py" <<'EOF'
#!/usr/bin/env python3
"""
Analyze TTA package structure and extract primitives.

Usage:
    python analyze_package.py <package-name>

Example:
    python analyze_package.py tta-narrative-engine
"""

import ast
import json
import sys
from pathlib import Path
from typing import Dict, List, Any


def analyze_file(file_path: Path) -> Dict[str, Any]:
    """Analyze a Python file and extract structure."""
    try:
        with open(file_path) as f:
            tree = ast.parse(f.read())
    except Exception as e:
        return {"error": str(e)}

    classes = []
    functions = []
    imports = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Extract class info
            methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
            bases = [ast.unparse(base) for base in node.bases]

            classes.append({
                "name": node.name,
                "line": node.lineno,
                "methods": methods,
                "bases": bases,
                "docstring": ast.get_docstring(node)
            })

        elif isinstance(node, ast.FunctionDef) and node.col_offset == 0:
            # Top-level functions only
            functions.append({
                "name": node.name,
                "line": node.lineno,
                "args": [arg.arg for arg in node.args.args],
                "docstring": ast.get_docstring(node)
            })

        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.Import):
                imports.extend([alias.name for alias in node.names])
            else:
                module = node.module or ""
                imports.extend([f"{module}.{alias.name}" for alias in node.names])

    return {
        "classes": classes,
        "functions": functions,
        "imports": list(set(imports))
    }


def analyze_package(package_name: str) -> Dict[str, Any]:
    """Analyze entire package."""
    package_path = Path("packages") / package_name

    if not package_path.exists():
        print(f"Error: Package {package_name} not found")
        sys.exit(1)

    results = {
        "package": package_name,
        "files": {}
    }

    # Analyze all Python files
    for py_file in package_path.rglob("*.py"):
        if py_file.stem == "__init__":
            continue

        rel_path = str(py_file.relative_to(package_path))
        results["files"][rel_path] = analyze_file(py_file)

    return results


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python analyze_package.py <package-name>")
        sys.exit(1)

    package_name = sys.argv[1]

    print(f"Analyzing package: {package_name}")
    results = analyze_package(package_name)

    # Save results
    output_file = Path("../analysis") / f"{package_name}-structure.json"
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Results saved to: {output_file}")

    # Print summary
    total_classes = sum(len(f.get("classes", [])) for f in results["files"].values())
    total_functions = sum(len(f.get("functions", [])) for f in results["files"].values())

    print(f"\nSummary:")
    print(f"  - Files analyzed: {len(results['files'])}")
    print(f"  - Classes found: {total_classes}")
    print(f"  - Functions found: {total_functions}")
EOF

    chmod +x "$SCRIPTS_DIR/analyze_package.py"
    log_info "Created: $SCRIPTS_DIR/analyze_package.py"

    # Report generator
    cat > "$SCRIPTS_DIR/generate_report.sh" <<'EOF'
#!/usr/bin/env bash
#
# Generate comprehensive analysis report
#

ANALYSIS_DIR="../analysis"

echo "# TTA Audit Report"
echo "Generated: $(date)"
echo ""

echo "## Package Statistics"
cat "$ANALYSIS_DIR/package-statistics.md"

echo ""
echo "## Class Inventory"
echo ""
echo "Total classes: $(wc -l < "$ANALYSIS_DIR/class-list.txt")"
echo ""
echo "First 20 classes:"
head -20 "$ANALYSIS_DIR/class-list.txt"

echo ""
echo "## Next Steps"
echo ""
echo "1. Review package structures in analysis/*.json"
echo "2. Map classes to TTA.dev primitives"
echo "3. Create primitive-mapping.json"
echo "4. Transfer results to TTA.dev"
EOF

    chmod +x "$SCRIPTS_DIR/generate_report.sh"
    log_info "Created: $SCRIPTS_DIR/generate_report.sh"
}

# Create README
create_readme() {
    log_info "Creating sandbox README..."

    cat > "$SANDBOX_PATH/README.md" <<EOF
# TTA Audit Sandbox

**Purpose:** Isolated environment for auditing TTA repository and extracting primitives

**Created:** $(date)

---

## Directory Structure

\`\`\`
$SANDBOX_NAME/
├── TTA/                    # Cloned TTA repository
├── analysis/               # Analysis reports and outputs
├── scripts/                # Analysis and extraction scripts
└── workspace/              # Scratch area for prototyping
\`\`\`

---

## Quick Start

### Run Package Analysis

\`\`\`bash
cd TTA
python ../scripts/analyze_package.py tta-narrative-engine
\`\`\`

### Generate Report

\`\`\`bash
cd scripts
./generate_report.sh > ../analysis/audit-report.md
\`\`\`

### View Statistics

\`\`\`bash
cat analysis/package-statistics.md
\`\`\`

---

## Analysis Workflow

1. **Analyze packages** - Run \`analyze_package.py\` for each package
2. **Review structure** - Examine \`*-structure.json\` files
3. **Map primitives** - Create \`primitive-mapping.json\`
4. **Transfer results** - Copy to TTA.dev/docs/planning/tta-analysis/

---

## Integration with TTA.dev

**Coordination Hub:** ~/repos/TTA.dev

**Transfer command:**
\`\`\`bash
cp analysis/* ~/repos/TTA.dev/docs/planning/tta-analysis/
\`\`\`

**Update TODO:**
\`\`\`bash
cd ~/repos/TTA.dev
# Update logseq/journals/$(date +%Y_%m_%d).md
\`\`\`

---

## Available Scripts

- \`scripts/analyze_package.py\` - Extract package structure
- \`scripts/generate_report.sh\` - Generate audit report

---

## Reference Documentation

- **Workflow Guide:** TTA.dev/docs/planning/TTA_SANDBOX_WORKFLOW.md
- **Remediation Plan:** TTA.dev/docs/planning/TTA_REMEDIATION_PLAN.md
- **Audit Checklist:** TTA.dev/docs/planning/TTA_AUDIT_CHECKLIST.md

---

**Next Steps:**

1. Review analysis/package-statistics.md
2. Run analysis scripts for each package
3. Begin primitive mapping
4. Transfer results to TTA.dev
EOF

    log_info "Created: $SANDBOX_PATH/README.md"
}

# Main execution
main() {
    log_info "=== TTA Audit Sandbox Setup ==="
    log_info "Sandbox location: $SANDBOX_PATH"
    echo ""

    check_prerequisites
    echo ""

    create_sandbox_structure
    echo ""

    clone_tta_repository
    echo ""

    setup_python_environment
    echo ""

    run_initial_analysis
    echo ""

    create_analysis_scripts
    echo ""

    create_readme
    echo ""

    log_info "=== Setup Complete ==="
    log_info ""
    log_info "Sandbox ready at: $SANDBOX_PATH"
    log_info ""
    log_info "Next steps:"
    log_info "  1. cd $SANDBOX_PATH"
    log_info "  2. cat README.md"
    log_info "  3. Review analysis/package-statistics.md"
    log_info "  4. Run: cd TTA && python ../scripts/analyze_package.py tta-narrative-engine"
    log_info ""
    log_info "Documentation: ~/repos/TTA.dev/docs/planning/TTA_SANDBOX_WORKFLOW.md"
}

# Run main
main
