"""Code processing utilities for ACE-generated code."""

import ast


def deduplicate_imports(code: str) -> str:
    """
    Removes duplicate imports from a Python code string.

    Args:
        code: The Python code as a string.

    Returns:
        The code with duplicate imports removed.
    """
    try:
        tree = ast.parse(code)
        imports = set()
        new_body = []
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                import_str = ast.unparse(node)
                if import_str not in imports:
                    imports.add(import_str)
                    new_body.append(node)
            else:
                new_body.append(node)
        tree.body = new_body
        return ast.unparse(tree)
    except SyntaxError:
        # Fallback for invalid syntax
        return code


def deduplicate_functions_and_classes(code: str) -> str:
    """
    Removes duplicate function and class definitions from a Python code string.

    Args:
        code: The Python code as a string.

    Returns:
        The code with duplicate functions and classes removed.
    """
    try:
        tree = ast.parse(code)
        definitions = {}
        new_body = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name not in definitions:
                    definitions[node.name] = ast.unparse(node)
                    new_body.append(node)
            else:
                new_body.append(node)
        tree.body = new_body
        return ast.unparse(tree)
    except SyntaxError:
        return code


def process_generated_code(code: str) -> str:
    """
    Applies all deduplication and processing steps to generated code.

    Args:
        code: The generated Python code.

    Returns:
        The processed and cleaned code.
    """
    processed_code = deduplicate_imports(code)
    processed_code = deduplicate_functions_and_classes(processed_code)
    return processed_code
