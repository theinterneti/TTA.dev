"""Code analysis primitives for TTA.dev KB automation.

This module provides primitives for scanning, parsing, and analyzing Python code
to extract TODOs, docstrings, and structural information for KB integration.
"""

import ast
import logging
import re
from pathlib import Path

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.observability import InstrumentedPrimitive

logger = logging.getLogger(__name__)


class ScanCodebase(InstrumentedPrimitive[dict, dict]):
    """Recursively scan codebase for Python files.

    Input:
        {
            "root_path": str,              # Root directory to scan
            "exclude_patterns": List[str], # Patterns to exclude (optional)
            "include_tests": bool          # Include test files (default: True)
        }

    Output:
        {
            "files": List[str],           # List of Python file paths
            "total_files": int,           # Total count
            "excluded_files": List[str]   # Files excluded by patterns
        }
    """

    def __init__(self):
        """Initialize ScanCodebase primitive."""
        super().__init__(name="scan_codebase")
        self._default_excludes = [
            "__pycache__",
            ".venv",
            "venv",
            ".git",
            ".pytest_cache",
            ".ruff_cache",
            ".mypy_cache",
            "htmlcov",
            "build",
            "dist",
            "*.egg-info",
        ]

    async def _execute_impl(
        self,
        input_data: dict,
        context: WorkflowContext,
    ) -> dict:
        """Scan codebase for Python files."""
        root_path = Path(input_data["root_path"])
        exclude_patterns = input_data.get("exclude_patterns", self._default_excludes)
        include_tests = input_data.get("include_tests", True)

        if not root_path.exists():
            raise ValueError(f"Root path does not exist: {root_path}")

        python_files = []
        excluded_files = []

        # Recursively find Python files
        for py_file in root_path.rglob("*.py"):
            # Check if file should be excluded
            should_exclude = False
            for pattern in exclude_patterns:
                if pattern in str(py_file):
                    should_exclude = True
                    break

            # Check if test file should be excluded
            if not should_exclude and not include_tests:
                if "test_" in py_file.name or py_file.name.endswith("_test.py"):
                    should_exclude = True

            # Add to appropriate list
            if should_exclude:
                excluded_files.append(str(py_file))
            else:
                python_files.append(str(py_file))

        return {
            "files": sorted(python_files),
            "total_files": len(python_files),
            "excluded_files": sorted(excluded_files),
        }


class ExtractTODOs(InstrumentedPrimitive[dict, dict]):
    """Extract TODO comments from Python files with context.

    Input:
        {
            "files": List[str],           # Python file paths to scan
            "include_context": bool,      # Include surrounding lines (default: True)
            "context_lines": int          # Lines of context (default: 2)
        }

    Output:
        {
            "todos": List[{
                "file": str,              # File path
                "line_number": int,       # Line number
                "todo_text": str,         # TODO content
                "context_before": List[str], # Lines before
                "context_after": List[str],  # Lines after
                "category": str           # Inferred category (implementation/testing/docs)
            }],
            "total_todos": int,
            "files_with_todos": int
        }
    """

    def __init__(self):
        """Initialize ExtractTODOs primitive."""
        super().__init__(name="extract_todos")
        # Regex to match TODO comments
        self._todo_pattern = re.compile(r"#\s*TODO:?\s*(.+)", re.IGNORECASE)

    async def _execute_impl(
        self,
        input_data: dict,
        context: WorkflowContext,
    ) -> dict:
        """Extract TODOs from Python files."""
        files = input_data["files"]
        include_context = input_data.get("include_context", True)
        context_lines = input_data.get("context_lines", 2)

        todos = []
        files_with_todos = set()

        for file_path in files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    lines = f.readlines()

                # Scan for TODO comments
                for i, line in enumerate(lines, start=1):
                    match = self._todo_pattern.search(line)
                    if match:
                        todo_text = match.group(1).strip()

                        # Get context lines
                        context_before = []
                        context_after = []
                        if include_context:
                            start_idx = max(0, i - 1 - context_lines)
                            end_idx = min(len(lines), i + context_lines)
                            context_before = [
                                lines[j].rstrip() for j in range(start_idx, i - 1)
                            ]
                            context_after = [
                                lines[j].rstrip() for j in range(i, end_idx)
                            ]

                        # Infer category from file path and context
                        category = self._infer_category(
                            file_path, todo_text, context_before
                        )

                        todos.append(
                            {
                                "file": file_path,
                                "line_number": i,
                                "todo_text": todo_text,
                                "context_before": context_before,
                                "context_after": context_after,
                                "category": category,
                            }
                        )
                        files_with_todos.add(file_path)

            except Exception as e:
                # Log error but continue processing other files
                logger.warning(f"Error analyzing {file_path}: {e}")
                continue

        return {
            "todos": todos,
            "total_todos": len(todos),
            "files_with_todos": len(files_with_todos),
        }

    def _infer_category(
        self, file_path: str, todo_text: str, context: list[str]
    ) -> str:
        """Infer TODO category from file path and content."""
        file_lower = file_path.lower()
        todo_lower = todo_text.lower()

        # Check file path
        if "test" in file_lower:
            return "testing"
        if "docs" in file_lower or "readme" in file_lower:
            return "documentation"

        # Check TODO text keywords
        if any(kw in todo_lower for kw in ["test", "coverage", "pytest"]):
            return "testing"
        if any(kw in todo_lower for kw in ["doc", "comment", "explain", "readme"]):
            return "documentation"
        if any(kw in todo_lower for kw in ["implement", "add", "create", "build"]):
            return "implementation"
        if any(kw in todo_lower for kw in ["fix", "bug", "issue", "error"]):
            return "bugfix"
        if any(kw in todo_lower for kw in ["refactor", "cleanup", "optimize"]):
            return "refactoring"

        # Default
        return "implementation"


class ParseDocstrings(InstrumentedPrimitive[dict, dict]):
    """Parse Python docstrings for KB integration.

    Input:
        {
            "files": List[str],           # Python file paths to parse
            "extract_examples": bool,     # Extract code examples (default: True)
            "extract_references": bool    # Extract cross-references (default: True)
        }

    Output:
        {
            "docstrings": List[{
                "file": str,              # File path
                "type": str,              # "module" | "class" | "function"
                "name": str,              # Entity name
                "docstring": str,         # Full docstring
                "summary": str,           # First line summary
                "examples": List[str],    # Code examples
                "references": List[str],  # Cross-references
                "line_number": int        # Starting line
            }],
            "total_docstrings": int,
            "missing_docstrings": List[{
                "file": str,
                "type": str,
                "name": str,
                "line_number": int
            }]
        }
    """

    def __init__(self):
        """Initialize ParseDocstrings primitive."""
        super().__init__(name="parse_docstrings")

    async def _execute_impl(
        self,
        input_data: dict,
        context: WorkflowContext,
    ) -> dict:
        """Parse docstrings from Python files."""
        files = input_data["files"]
        extract_examples = input_data.get("extract_examples", True)
        extract_references = input_data.get("extract_references", True)

        docstrings = []
        missing_docstrings = []

        for file_path in files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    source = f.read()

                # Parse AST
                tree = ast.parse(source, filename=file_path)

                # Extract module docstring
                module_doc = ast.get_docstring(tree)
                if module_doc:
                    doc_entry = self._process_docstring(
                        file_path,
                        "module",
                        Path(file_path).stem,
                        module_doc,
                        1,
                        extract_examples,
                        extract_references,
                    )
                    docstrings.append(doc_entry)
                else:
                    missing_docstrings.append(
                        {
                            "file": file_path,
                            "type": "module",
                            "name": Path(file_path).stem,
                            "line_number": 1,
                        }
                    )

                # Walk AST for classes and functions
                for node in ast.walk(tree):
                    if isinstance(
                        node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
                    ):
                        doc = ast.get_docstring(node)
                        node_type = (
                            "class" if isinstance(node, ast.ClassDef) else "function"
                        )

                        if doc:
                            doc_entry = self._process_docstring(
                                file_path,
                                node_type,
                                node.name,
                                doc,
                                node.lineno,
                                extract_examples,
                                extract_references,
                            )
                            docstrings.append(doc_entry)
                        else:
                            # Skip private and dunder methods
                            if not node.name.startswith("_"):
                                missing_docstrings.append(
                                    {
                                        "file": file_path,
                                        "type": node_type,
                                        "name": node.name,
                                        "line_number": node.lineno,
                                    }
                                )

            except Exception as e:
                logger.warning(f"Error parsing {file_path}: {e}")
                continue

        return {
            "docstrings": docstrings,
            "total_docstrings": len(docstrings),
            "missing_docstrings": missing_docstrings,
        }

    def _process_docstring(
        self,
        file_path: str,
        doc_type: str,
        name: str,
        docstring: str,
        line_number: int,
        extract_examples: bool,
        extract_references: bool,
    ) -> dict:
        """Process a docstring and extract components."""
        lines = docstring.split("\n")
        summary = lines[0].strip() if lines else ""

        examples = []
        references = []

        if extract_examples:
            # Extract code blocks (simple heuristic)
            # Look for >>> prompts or ``` code fences or Example: sections
            in_code_block = False
            in_example_section = False
            current_example = []

            for _i, line in enumerate(lines):
                stripped = line.strip()

                # Detect example section
                if "Example:" in line or "Examples:" in line:
                    in_example_section = True
                    continue

                # Detect code fence start
                if stripped.startswith("```"):
                    if in_code_block:
                        # End of code block
                        if current_example:
                            examples.append("\n".join(current_example))
                        current_example = []
                        in_code_block = False
                    else:
                        # Start of code block
                        in_code_block = True
                        current_example = []
                    continue

                # Detect >>> prompt (interactive example)
                if stripped.startswith(">>>"):
                    if not in_code_block:
                        in_code_block = True
                        current_example = []
                    current_example.append(line)
                elif in_code_block:
                    # In a code block
                    if stripped and not stripped.startswith("#"):
                        # Continue collecting code
                        current_example.append(line)
                    elif not stripped and current_example:
                        # Empty line ends >>> style example
                        if any(
                            code_line.strip().startswith(">>>")
                            for code_line in current_example
                        ):
                            examples.append("\n".join(current_example))
                            current_example = []
                            in_code_block = False
                elif in_example_section and stripped:
                    # Indented content in Example section (likely code)
                    if line.startswith("    ") or line.startswith("\t"):
                        if not in_code_block:
                            in_code_block = True
                            current_example = []
                        current_example.append(line)
                    elif current_example:
                        # End of indented section
                        examples.append("\n".join(current_example))
                        current_example = []
                        in_code_block = False
                        in_example_section = False

            # Don't forget last example
            if current_example:
                examples.append("\n".join(current_example))

        if extract_references:
            # Extract references to other entities (simple heuristic)
            # Look for :class:`ClassName`, :func:`function_name`, [[WikiLink]]
            class_refs = re.findall(r":class:`([^`]+)`", docstring)
            func_refs = re.findall(r":func:`([^`]+)`", docstring)
            wiki_refs = re.findall(r"\[\[([^\]]+)\]\]", docstring)
            references = class_refs + func_refs + wiki_refs

        return {
            "file": file_path,
            "type": doc_type,
            "name": name,
            "docstring": docstring,
            "summary": summary,
            "examples": examples,
            "references": references,
            "line_number": line_number,
        }


class AnalyzeCodeStructure(InstrumentedPrimitive[dict, dict]):
    """Analyze Python code structure for KB integration.

    Input:
        {
            "files": List[str],           # Python file paths to analyze
            "include_imports": bool,      # Extract imports (default: True)
            "include_dependencies": bool  # Track dependencies (default: True)
        }

    Output:
        {
            "modules": List[{
                "file": str,              # File path
                "classes": List[str],     # Class names
                "functions": List[str],   # Function names
                "imports": List[str],     # Import statements
                "dependencies": List[str], # Imported modules
                "loc": int                # Lines of code
            }],
            "total_classes": int,
            "total_functions": int,
            "dependency_graph": Dict[str, List[str]]  # File -> dependencies
        }
    """

    def __init__(self):
        """Initialize AnalyzeCodeStructure primitive."""
        super().__init__(name="analyze_code_structure")

    async def _execute_impl(
        self,
        input_data: dict,
        context: WorkflowContext,
    ) -> dict:
        """Analyze code structure."""
        files = input_data["files"]
        include_imports = input_data.get("include_imports", True)
        include_dependencies = input_data.get("include_dependencies", True)

        modules = []
        total_classes = 0
        total_functions = 0
        dependency_graph = {}

        for file_path in files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    source = f.read()

                # Parse AST
                tree = ast.parse(source, filename=file_path)

                # Extract classes
                classes = [
                    node.name
                    for node in ast.walk(tree)
                    if isinstance(node, ast.ClassDef)
                ]

                # Extract functions
                functions = [
                    node.name
                    for node in ast.walk(tree)
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]

                # Extract imports
                imports = []
                dependencies = []
                if include_imports or include_dependencies:
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                imports.append(f"import {alias.name}")
                                if include_dependencies:
                                    dependencies.append(alias.name.split(".")[0])
                        elif isinstance(node, ast.ImportFrom):
                            module = node.module or ""
                            for alias in node.names:
                                imports.append(f"from {module} import {alias.name}")
                                if include_dependencies and module:
                                    dependencies.append(module.split(".")[0])

                # Count lines of code (excluding blank lines and comments)
                loc = sum(
                    1
                    for line in source.split("\n")
                    if line.strip() and not line.strip().startswith("#")
                )

                module_info = {
                    "file": file_path,
                    "classes": classes,
                    "functions": functions,
                    "imports": imports if include_imports else [],
                    "dependencies": list(set(dependencies))
                    if include_dependencies
                    else [],
                    "loc": loc,
                }

                modules.append(module_info)
                total_classes += len(classes)
                total_functions += len(functions)

                if include_dependencies:
                    dependency_graph[file_path] = list(set(dependencies))

            except Exception as e:
                logger.warning(f"Error analyzing {file_path}: {e}")
                continue

        return {
            "modules": modules,
            "total_classes": total_classes,
            "total_functions": total_functions,
            "dependency_graph": dependency_graph,
        }
