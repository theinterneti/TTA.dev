"""
Langfuse Playground and Dataset Management

This module provides utilities for creating and managing datasets in Langfuse
for testing prompts and evaluating LLM performance.
"""

from typing import Any

from langfuse import Langfuse

from .initialization import get_langfuse_client, is_langfuse_enabled


class DatasetManager:
    """Manage datasets for Langfuse Playground."""

    def __init__(self, client: Langfuse | None = None):
        """
        Initialize dataset manager.

        Args:
            client: Langfuse client instance
        """
        self.client = client or get_langfuse_client()

    def create_dataset(
        self,
        name: str,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Create a new dataset.

        Args:
            name: Unique name for the dataset
            description: Optional description
            metadata: Optional metadata

        Returns:
            Dict with dataset details

        Example:
            >>> manager = DatasetManager()
            >>> dataset = manager.create_dataset(
            ...     name="code-generation-tests",
            ...     description="Test cases for code generation",
            ...     metadata={"category": "code-quality"}
            ... )
        """
        if not is_langfuse_enabled():
            return {
                "name": name,
                "description": description,
                "disabled": True,
            }

        try:
            created = self.client.create_dataset(
                name=name,
                description=description,
                metadata=metadata or {},
            )

            return {
                "id": created.id if hasattr(created, "id") else None,
                "name": name,
                "description": description,
                "metadata": metadata or {},
            }
        except Exception as e:
            raise RuntimeError(f"Failed to create dataset '{name}': {e}") from e

    def create_dataset_item(
        self,
        dataset_name: str,
        input_data: dict[str, Any] | str,
        expected_output: dict[str, Any] | str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Add an item to a dataset.

        Args:
            dataset_name: Name of the dataset
            input_data: Input for the test case
            expected_output: Expected output (optional)
            metadata: Optional metadata

        Returns:
            Dict with item details

        Example:
            >>> manager = DatasetManager()
            >>> item = manager.create_dataset_item(
            ...     dataset_name="code-generation-tests",
            ...     input_data={"prompt": "Write a function to sort a list"},
            ...     expected_output={"code": "def sort_list(lst): return sorted(lst)"},
            ...     metadata={"difficulty": "easy"}
            ... )
        """
        if not is_langfuse_enabled():
            return {
                "dataset_name": dataset_name,
                "input": input_data,
                "expected_output": expected_output,
                "disabled": True,
            }

        try:
            created = self.client.create_dataset_item(
                dataset_name=dataset_name,
                input=input_data,
                expected_output=expected_output,
                metadata=metadata or {},
            )

            return {
                "id": created.id if hasattr(created, "id") else None,
                "dataset_name": dataset_name,
                "input": input_data,
                "expected_output": expected_output,
                "metadata": metadata or {},
            }
        except Exception as e:
            raise RuntimeError(
                f"Failed to create item in dataset '{dataset_name}': {e}"
            ) from e

    def get_dataset(self, name: str) -> dict[str, Any] | None:
        """
        Fetch a dataset by name.

        Args:
            name: Name of the dataset

        Returns:
            Dict with dataset details or None if not found
        """
        if not is_langfuse_enabled():
            return None

        try:
            dataset = self.client.get_dataset(name)
            if not dataset:
                return None

            return {
                "id": dataset.id if hasattr(dataset, "id") else None,
                "name": dataset.name if hasattr(dataset, "name") else name,
                "description": getattr(dataset, "description", None),
                "metadata": getattr(dataset, "metadata", {}),
            }
        except Exception as e:
            print(f"Warning: Failed to fetch dataset '{name}': {e}")
            return None


def create_code_generation_dataset(manager: DatasetManager | None = None) -> dict[str, Any]:
    """
    Create a dataset for testing code generation.

    Args:
        manager: Optional DatasetManager instance

    Returns:
        Dict with dataset and items created

    Example:
        >>> result = create_code_generation_dataset()
        >>> print(f"Created {result['items_created']} test cases")
    """
    if manager is None:
        manager = DatasetManager()

    dataset_name = "code-generation-tests"

    # Create dataset
    dataset = manager.create_dataset(
        name=dataset_name,
        description="Test cases for code generation and quality evaluation",
        metadata={"category": "code-quality", "auto-generated": True},
    )

    # Create test cases
    test_cases = [
        {
            "input": {"prompt": "Write a function to calculate fibonacci numbers"},
            "expected_output": {
                "code": "def fibonacci(n: int) -> int:\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)"
            },
            "metadata": {"difficulty": "easy", "topic": "recursion"},
        },
        {
            "input": {"prompt": "Create a class for a binary search tree with insert and search methods"},
            "expected_output": {
                "code": "class BSTNode:\n    def __init__(self, value):\n        self.value = value\n        self.left = None\n        self.right = None\n\nclass BST:\n    def __init__(self):\n        self.root = None\n\n    def insert(self, value):\n        if not self.root:\n            self.root = BSTNode(value)\n        else:\n            self._insert_recursive(self.root, value)\n\n    def _insert_recursive(self, node, value):\n        if value < node.value:\n            if node.left is None:\n                node.left = BSTNode(value)\n            else:\n                self._insert_recursive(node.left, value)\n        else:\n            if node.right is None:\n                node.right = BSTNode(value)\n            else:\n                self._insert_recursive(node.right, value)"
            },
            "metadata": {"difficulty": "medium", "topic": "data-structures"},
        },
        {
            "input": {"prompt": "Write a decorator that retries a function up to 3 times"},
            "expected_output": {
                "code": "import functools\nimport time\n\ndef retry(max_attempts=3, delay=1):\n    def decorator(func):\n        @functools.wraps(func)\n        def wrapper(*args, **kwargs):\n            for attempt in range(max_attempts):\n                try:\n                    return func(*args, **kwargs)\n                except Exception as e:\n                    if attempt == max_attempts - 1:\n                        raise\n                    time.sleep(delay)\n            return None\n        return wrapper\n    return decorator"
            },
            "metadata": {"difficulty": "medium", "topic": "decorators"},
        },
    ]

    items_created = 0
    for test_case in test_cases:
        try:
            manager.create_dataset_item(
                dataset_name=dataset_name,
                input_data=test_case["input"],
                expected_output=test_case.get("expected_output"),
                metadata=test_case.get("metadata"),
            )
            items_created += 1
        except Exception as e:
            print(f"Warning: Failed to create test case: {e}")

    return {
        "dataset": dataset,
        "items_created": items_created,
        "total_cases": len(test_cases),
    }


def create_documentation_dataset(manager: DatasetManager | None = None) -> dict[str, Any]:
    """
    Create a dataset for testing documentation generation.

    Args:
        manager: Optional DatasetManager instance

    Returns:
        Dict with dataset and items created
    """
    if manager is None:
        manager = DatasetManager()

    dataset_name = "documentation-generation-tests"

    dataset = manager.create_dataset(
        name=dataset_name,
        description="Test cases for documentation generation and quality",
        metadata={"category": "documentation", "auto-generated": True},
    )

    test_cases = [
        {
            "input": {
                "code": "def add(a: int, b: int) -> int:\n    return a + b",
                "prompt": "Generate comprehensive documentation for this function",
            },
            "expected_output": {
                "docs": "# add\n\nAdds two integers together.\n\n## Parameters\n\n- `a` (int): The first number\n- `b` (int): The second number\n\n## Returns\n\nint: The sum of a and b\n\n## Example\n\n```python\nresult = add(2, 3)\nprint(result)  # 5\n```"
            },
            "metadata": {"difficulty": "easy"},
        },
        {
            "input": {
                "code": "class WorkflowPrimitive:\n    async def execute(self, input_data, context): pass",
                "prompt": "Document this class and its abstract method",
            },
            "expected_output": {
                "docs": "# WorkflowPrimitive\n\nBase class for workflow primitives in TTA.dev.\n\n## Methods\n\n### execute\n\nExecutes the primitive's operation.\n\n**Parameters:**\n- `input_data`: Input data for the operation\n- `context`: Workflow context with metadata\n\n**Returns:** Operation result\n\n**Example:**\n```python\nresult = await primitive.execute(data, context)\n```"
            },
            "metadata": {"difficulty": "medium"},
        },
    ]

    items_created = 0
    for test_case in test_cases:
        try:
            manager.create_dataset_item(
                dataset_name=dataset_name,
                input_data=test_case["input"],
                expected_output=test_case.get("expected_output"),
                metadata=test_case.get("metadata"),
            )
            items_created += 1
        except Exception as e:
            print(f"Warning: Failed to create test case: {e}")

    return {
        "dataset": dataset,
        "items_created": items_created,
        "total_cases": len(test_cases),
    }


def create_test_generation_dataset(manager: DatasetManager | None = None) -> dict[str, Any]:
    """
    Create a dataset for testing test generation.

    Args:
        manager: Optional DatasetManager instance

    Returns:
        Dict with dataset and items created
    """
    if manager is None:
        manager = DatasetManager()

    dataset_name = "test-generation-tests"

    dataset = manager.create_dataset(
        name=dataset_name,
        description="Test cases for test generation and coverage",
        metadata={"category": "testing", "auto-generated": True},
    )

    test_cases = [
        {
            "input": {
                "code": "def is_even(n: int) -> bool:\n    return n % 2 == 0",
                "prompt": "Generate comprehensive pytest tests for this function",
            },
            "expected_output": {
                "tests": "import pytest\n\ndef test_is_even_with_even_number():\n    assert is_even(2) is True\n\ndef test_is_even_with_odd_number():\n    assert is_even(3) is False\n\ndef test_is_even_with_zero():\n    assert is_even(0) is True\n\ndef test_is_even_with_negative_even():\n    assert is_even(-4) is True\n\ndef test_is_even_with_negative_odd():\n    assert is_even(-3) is False"
            },
            "metadata": {"difficulty": "easy", "test_count": 5},
        },
    ]

    items_created = 0
    for test_case in test_cases:
        try:
            manager.create_dataset_item(
                dataset_name=dataset_name,
                input_data=test_case["input"],
                expected_output=test_case.get("expected_output"),
                metadata=test_case.get("metadata"),
            )
            items_created += 1
        except Exception as e:
            print(f"Warning: Failed to create test case: {e}")

    return {
        "dataset": dataset,
        "items_created": items_created,
        "total_cases": len(test_cases),
    }


def setup_all_datasets(manager: DatasetManager | None = None) -> dict[str, Any]:
    """
    Create all default datasets for the playground.

    Args:
        manager: Optional DatasetManager instance

    Returns:
        Dict with summary of all datasets created

    Example:
        >>> result = setup_all_datasets()
        >>> print(f"Created {result['total_datasets']} datasets with {result['total_items']} items")
    """
    if manager is None:
        manager = DatasetManager()

    results = {
        "code_generation": create_code_generation_dataset(manager),
        "documentation": create_documentation_dataset(manager),
        "test_generation": create_test_generation_dataset(manager),
    }

    total_datasets = len(results)
    total_items = sum(r["items_created"] for r in results.values())

    return {
        "results": results,
        "total_datasets": total_datasets,
        "total_items": total_items,
        "summary": f"Created {total_datasets} datasets with {total_items} test cases",
    }
