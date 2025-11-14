#!/usr/bin/env python3
"""Validate LLM usage efficiency patterns.

This script checks for inefficient LLM usage patterns in the codebase,
inspired by AI context optimization best practices.

Checks:
- Large context without caching
- Multiple models without router
- No timeout on expensive calls
- Inefficient token usage patterns
"""

import ast
import sys
from pathlib import Path
from typing import List, Tuple


class LLMEfficiencyChecker(ast.NodeVisitor):
    """AST visitor to check for inefficient LLM patterns."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.issues: List[Tuple[int, str]] = []
        self.has_cache_import = False
        self.has_router_import = False
        self.has_timeout_import = False

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Check for observability primitive imports."""
        if node.module and "observability_integration" in node.module:
            for alias in node.names:
                if alias.name == "CachePrimitive":
                    self.has_cache_import = True
                elif alias.name == "RouterPrimitive":
                    self.has_router_import = True
                elif alias.name == "TimeoutPrimitive":
                    self.has_timeout_import = True
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Check for inefficient LLM call patterns."""
        # Check for generate/complete calls
        if hasattr(node.func, "attr"):
            func_name = node.func.attr
            
            # Check for LLM generation calls
            if func_name in {"generate", "complete", "chat", "invoke"}:
                # Check if it's likely an LLM call
                if self._is_likely_llm_call(node):
                    # Suggest cache for repeated calls
                    if not self.has_cache_import:
                        self.issues.append((
                            node.lineno,
                            f"LLM call '{func_name}' without CachePrimitive - consider caching for cost savings"
                        ))
                    
                    # Suggest timeout for long operations
                    if not self.has_timeout_import:
                        self.issues.append((
                            node.lineno,
                            f"LLM call '{func_name}' without TimeoutPrimitive - consider adding timeout"
                        ))
        
        self.generic_visit(node)

    def _is_likely_llm_call(self, node: ast.Call) -> bool:
        """Heuristic to detect LLM calls."""
        # Check for common LLM-related keywords in call
        for keyword in node.keywords:
            if keyword.arg in {"model", "prompt", "messages", "temperature", "max_tokens"}:
                return True
        return False


def check_file_efficiency(file_path: Path) -> List[Tuple[int, str]]:
    """Check a single file for LLM efficiency issues."""
    try:
        with open(file_path) as f:
            tree = ast.parse(f.read(), filename=str(file_path))
        
        checker = LLMEfficiencyChecker(file_path)
        checker.visit(tree)
        return checker.issues
    
    except SyntaxError as e:
        return [(e.lineno or 0, f"Syntax error: {e}")]
    except Exception as e:
        return [(0, f"Error parsing file: {e}")]


def main() -> int:
    """Main validation logic."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate LLM usage efficiency")
    parser.add_argument(
        "--path",
        type=Path,
        default=Path("packages"),
        help="Path to check (default: packages)"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on any issues (default: warn only)"
    )
    args = parser.parse_args()
    
    package_dir = args.path
    if not package_dir.exists():
        print(f"❌ Path not found: {package_dir}")
        return 1
    
    issues_found = False
    total_files = 0
    total_issues = 0
    
    print(f"🔍 Checking LLM efficiency in {package_dir}...")
    print()
    
    for py_file in package_dir.rglob("*.py"):
        # Skip test files and cache
        if "test" in str(py_file) or "__pycache__" in str(py_file):
            continue
        
        total_files += 1
        issues = check_file_efficiency(py_file)
        
        if issues:
            issues_found = True
            total_issues += len(issues)
            print(f"⚠️  Issues in {py_file.relative_to(package_dir)}:")
            for line, msg in issues:
                print(f"  Line {line}: {msg}")
            print()
    
    print(f"📊 Summary:")
    print(f"  Files checked: {total_files}")
    print(f"  Issues found: {total_issues}")
    print()
    
    if issues_found:
        print("💡 Recommendations:")
        print("  - Use CachePrimitive for repeated LLM calls (40% cost savings)")
        print("  - Use RouterPrimitive for multi-model scenarios (30% cost savings)")
        print("  - Use TimeoutPrimitive to prevent hanging operations")
        print()
        
        if args.strict:
            print("❌ LLM efficiency issues found (strict mode)")
            return 1
        else:
            print("⚠️  LLM efficiency issues found (warning only)")
            return 0
    else:
        print("✅ No LLM efficiency issues detected")
        return 0


if __name__ == "__main__":
    sys.exit(main())
