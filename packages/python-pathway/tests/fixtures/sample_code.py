"""Sample Python file with various patterns and anti-patterns for testing."""

# Anti-pattern: star import
from os.path import *  # noqa: F401, F403


# Pattern: singleton
class SingletonService:
    """A singleton service class."""

    _instance = None

    def __new__(cls) -> "SingletonService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def do_work(self) -> str:
        return "working"


# Pattern: context manager
class ManagedResource:
    """A context manager class."""

    def __enter__(self) -> "ManagedResource":
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        pass

    def read(self) -> str:
        return "data"


# Pattern: factory
def create_service(service_type: str) -> object:
    """Factory function to create a service."""
    if service_type == "singleton":
        return SingletonService()
    return ManagedResource()


def widget_factory(name: str) -> object:
    """Another factory pattern function."""
    return {"name": name}


# Pattern: decorator
def my_decorator(func: object) -> object:
    """A function that implements the decorator pattern."""

    def wrapper(*args: object, **kwargs: object) -> object:
        return func(*args, **kwargs)  # type: ignore[operator]

    return wrapper


# Pattern: async
async def fetch_data(url: str) -> str:
    """An async function."""
    return f"data from {url}"


# Anti-pattern: mutable default argument
def append_item(item: str, items: list = []) -> list:  # noqa: B006
    """Function with mutable default argument."""
    items.append(item)
    return items


# Anti-pattern: bare except
def risky_operation() -> str:
    """Function with bare except."""
    try:
        return str(int("not_a_number"))
    except:  # noqa: E722
        return "failed"


# Anti-pattern: missing type hints
def no_hints(x, y):  # noqa: ANN001, ANN201
    """Function missing type hints."""
    return x + y


# Regular typed function (no anti-patterns)
def typed_function(x: int, y: int) -> int:
    """A properly typed function.

    Args:
        x: First integer.
        y: Second integer.

    Returns:
        The sum of x and y.
    """
    return x + y
