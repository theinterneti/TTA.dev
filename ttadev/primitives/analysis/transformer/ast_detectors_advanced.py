"""Advanced AST NodeVisitor detectors: Memory, Delegation, Sequential, Adaptive."""

import ast
from typing import Any


class MemoryDetector(ast.NodeVisitor):
    """Detect conversation history/context management patterns.

    Detects:
    - Message list accumulation (messages.append({...}))
    - Dict-based context storage (context[key] = value)
    - Deque-based history (deque(maxlen=...))
    """

    def __init__(self) -> None:
        self.memory_patterns: list[dict[str, Any]] = []
        self._current_function: str | None = None
        self._current_is_async: bool = False
        self._current_lineno: int = 0

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._current_function = node.name
        self._current_is_async = False
        self._current_lineno = node.lineno
        self.generic_visit(node)
        self._current_function = None

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._current_function = node.name
        self._current_is_async = True
        self._current_lineno = node.lineno
        self.generic_visit(node)
        self._current_function = None

    def visit_Call(self, node: ast.Call) -> None:
        """Detect .append() calls for message lists."""
        # Pattern: messages.append({"role": ..., "content": ...})
        if isinstance(node.func, ast.Attribute) and node.func.attr == "append":
            if isinstance(node.func.value, ast.Name):
                var_name = node.func.value.id
                # Check if appending dict with role/content (chat history pattern)
                if node.args and isinstance(node.args[0], ast.Dict):
                    keys = [
                        k.value if isinstance(k, ast.Constant) else None for k in node.args[0].keys
                    ]
                    if "role" in keys or "content" in keys or "message" in keys:
                        self.memory_patterns.append(
                            {
                                "type": "message_append",
                                "variable": var_name,
                                "parent_function": self._current_function,
                                "is_async": self._current_is_async,
                                "lineno": node.lineno,
                            }
                        )
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        """Detect dict-based context storage."""
        # Pattern: context[key] = value (in Assign context)
        if isinstance(node.ctx, ast.Store):
            if isinstance(node.value, ast.Name):
                var_name = node.value.id
                if any(kw in var_name.lower() for kw in ["context", "history", "memory", "store"]):
                    self.memory_patterns.append(
                        {
                            "type": "dict_storage",
                            "variable": var_name,
                            "parent_function": self._current_function,
                            "is_async": self._current_is_async,
                            "lineno": node.lineno,
                        }
                    )
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        """Detect deque initialization for bounded history."""
        # Pattern: history = deque(maxlen=...)
        if isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name) and node.value.func.id == "deque":
                for keyword in node.value.keywords:
                    if keyword.arg == "maxlen":
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                maxlen = None
                                if isinstance(keyword.value, ast.Constant):
                                    maxlen = keyword.value.value
                                self.memory_patterns.append(
                                    {
                                        "type": "deque_history",
                                        "variable": target.id,
                                        "maxlen": maxlen,
                                        "parent_function": self._current_function,
                                        "is_async": self._current_is_async,
                                        "lineno": node.lineno,
                                    }
                                )
        self.generic_visit(node)


class DelegationDetector(ast.NodeVisitor):
    """Detect task delegation/orchestration patterns.

    Detects:
    - Agent routing (agents[role].execute())
    - Model selection routing (if model == "gpt-4": ...)
    - Task dispatching (executor.run(task))
    """

    def __init__(self) -> None:
        self.delegation_patterns: list[dict[str, Any]] = []
        self._current_function: str | None = None
        self._current_is_async: bool = False

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._current_function = node.name
        self._current_is_async = False
        self._check_function_for_delegation(node)
        self.generic_visit(node)
        self._current_function = None

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._current_function = node.name
        self._current_is_async = True
        self._check_function_for_delegation(node)
        self.generic_visit(node)
        self._current_function = None

    def _check_function_for_delegation(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """Check function for delegation patterns."""
        # Look for if/elif chains with model/agent selection
        for stmt in ast.walk(node):
            if isinstance(stmt, ast.If):
                self._check_model_routing(stmt, node)

    def _check_model_routing(
        self,
        if_node: ast.If,
        func_node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> None:
        """Check if/elif chain for model/agent routing."""
        # Pattern: if model == "gpt-4": ... elif model == "claude": ...
        models: list[str] = []
        variable: str | None = None

        def extract_model(test: ast.expr) -> tuple[str | None, str | None]:
            """Extract model name and variable from comparison."""
            if isinstance(test, ast.Compare):
                if len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq):
                    left = test.left
                    right = test.comparators[0]
                    if isinstance(left, ast.Name) and isinstance(right, ast.Constant):
                        return left.id, str(right.value)
                    if isinstance(right, ast.Name) and isinstance(left, ast.Constant):
                        return right.id, str(left.value)
            return None, None

        # Check main if
        var, model = extract_model(if_node.test)
        if model and var:
            variable = var
            if any(kw in var.lower() for kw in ["model", "agent", "executor", "handler"]):
                models.append(model)

        # Check elif branches
        current = if_node
        while current.orelse:
            if len(current.orelse) == 1 and isinstance(current.orelse[0], ast.If):
                current = current.orelse[0]
                var, model = extract_model(current.test)
                if model:
                    models.append(model)
            else:
                break

        if len(models) >= 2 and variable:
            self.delegation_patterns.append(
                {
                    "type": "model_routing",
                    "variable": variable,
                    "models": models,
                    "parent_function": func_node.name,
                    "is_async": self._current_is_async,
                    "lineno": if_node.lineno,
                }
            )

    def visit_Call(self, node: ast.Call) -> None:
        """Detect executor dispatch patterns."""
        # Pattern: agents[role].execute(...) or executor.run(task)
        if isinstance(node.func, ast.Attribute):
            attr = node.func.attr
            if attr in ["execute", "run", "invoke", "dispatch", "delegate"]:
                # Get the variable being called
                if isinstance(node.func.value, ast.Subscript):
                    # agents[role].execute()
                    if isinstance(node.func.value.value, ast.Name):
                        container = node.func.value.value.id
                        self.delegation_patterns.append(
                            {
                                "type": "agent_dispatch",
                                "container": container,
                                "method": attr,
                                "parent_function": self._current_function,
                                "is_async": self._current_is_async,
                                "lineno": node.lineno,
                            }
                        )
                elif isinstance(node.func.value, ast.Name):
                    # executor.run(task)
                    executor = node.func.value.id
                    if any(
                        kw in executor.lower() for kw in ["executor", "agent", "worker", "handler"]
                    ):
                        self.delegation_patterns.append(
                            {
                                "type": "executor_dispatch",
                                "executor": executor,
                                "method": attr,
                                "parent_function": self._current_function,
                                "is_async": self._current_is_async,
                                "lineno": node.lineno,
                            }
                        )
        self.generic_visit(node)


class SequentialDetector(ast.NodeVisitor):
    """Detect sequential pipeline patterns.

    Detects:
    - Chained function calls: result = step3(step2(step1(data)))
    - Sequential assignments: r1 = step1(data); r2 = step2(r1); r3 = step3(r2)
    - Pipeline patterns with await chains
    """

    def __init__(self) -> None:
        self.sequential_patterns: list[dict[str, Any]] = []
        self._current_function: str | None = None
        self._current_is_async: bool = False

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._current_function = node.name
        self._current_is_async = False
        self._check_sequential_chain(node)
        self.generic_visit(node)
        self._current_function = None

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._current_function = node.name
        self._current_is_async = True
        self._check_sequential_chain(node)
        self.generic_visit(node)
        self._current_function = None

    def _check_sequential_chain(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """Check for sequential assignment chains."""
        assigns: list[tuple[str, str, int]] = []  # (target, func_name, lineno)

        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                # r = func(...)
                if len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                    target = stmt.targets[0].id
                    func_name = self._extract_func_name(stmt.value)
                    if func_name:
                        assigns.append((target, func_name, stmt.lineno))

            elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Await):
                # await func(...)
                if isinstance(stmt.value.value, ast.Call):
                    func_name = self._extract_func_name(stmt.value.value)
                    if func_name:
                        assigns.append(("_", func_name, stmt.lineno))

        # Check for chains where output becomes input
        if len(assigns) >= 3:
            steps = [a[1] for a in assigns]
            self.sequential_patterns.append(
                {
                    "type": "assignment_chain",
                    "steps": steps,
                    "parent_function": self._current_function,
                    "is_async": self._current_is_async,
                    "lineno": assigns[0][2],
                    "step_count": len(assigns),
                }
            )

    def visit_Call(self, node: ast.Call) -> None:
        """Detect nested function calls: step3(step2(step1(data)))."""
        chain = self._extract_call_chain(node)
        if len(chain) >= 3:
            self.sequential_patterns.append(
                {
                    "type": "nested_calls",
                    "steps": list(reversed(chain)),  # Innermost first
                    "parent_function": self._current_function,
                    "is_async": self._current_is_async,
                    "lineno": node.lineno,
                    "step_count": len(chain),
                }
            )
        self.generic_visit(node)

    def _extract_call_chain(self, node: ast.expr) -> list[str]:
        """Extract chain of nested calls."""
        chain: list[str] = []

        def walk(n: ast.expr) -> None:
            if isinstance(n, ast.Call):
                func_name = self._extract_func_name(n)
                if func_name:
                    chain.append(func_name)
                # Check first argument for nested call
                if n.args and isinstance(n.args[0], ast.Call):
                    walk(n.args[0])

        walk(node)
        return chain

    def _extract_func_name(self, node: ast.expr) -> str | None:
        """Extract function name from Call or Await."""
        if isinstance(node, ast.Await):
            node = node.value

        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return node.func.id
            elif isinstance(node.func, ast.Attribute):
                return node.func.attr
        return None


class AdaptiveDetector(ast.NodeVisitor):
    """Detect patterns that benefit from adaptive/learning behavior.

    Detects:
    - Success/failure tracking with counters
    - Parameter adjustment based on results
    - Strategy selection with metrics
    """

    def __init__(self) -> None:
        self.adaptive_patterns: list[dict[str, Any]] = []
        self._current_function: str | None = None
        self._current_is_async: bool = False

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._current_function = node.name
        self._current_is_async = False
        self._check_adaptive_patterns(node)
        self.generic_visit(node)
        self._current_function = None

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._current_function = node.name
        self._current_is_async = True
        self._check_adaptive_patterns(node)
        self.generic_visit(node)
        self._current_function = None

    def _check_adaptive_patterns(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """Check for adaptive/learning patterns in function."""
        has_counter = False
        has_conditional_adjust = False
        counter_vars: list[str] = []

        for stmt in ast.walk(node):
            # Look for counter increments: success_count += 1, failures += 1
            if isinstance(stmt, ast.AugAssign):
                if isinstance(stmt.target, ast.Name):
                    var = stmt.target.id.lower()
                    if any(kw in var for kw in ["count", "success", "fail", "error", "metric"]):
                        has_counter = True
                        counter_vars.append(stmt.target.id)

            # Look for conditional parameter adjustment
            if isinstance(stmt, ast.If):
                # Check if condition references counters/rates
                cond_str = ast.dump(stmt.test)
                if any(kw in cond_str.lower() for kw in ["rate", "count", "threshold", "metric"]):
                    # Check if body adjusts parameters
                    for body_stmt in stmt.body:
                        if isinstance(body_stmt, ast.Assign):
                            has_conditional_adjust = True

        if has_counter and has_conditional_adjust:
            self.adaptive_patterns.append(
                {
                    "type": "metric_based_adjustment",
                    "counter_vars": counter_vars,
                    "parent_function": self._current_function,
                    "is_async": self._current_is_async,
                    "lineno": node.lineno,
                }
            )

    def visit_Assign(self, node: ast.Assign) -> None:
        """Detect strategy dictionaries with performance data."""
        # Pattern: strategies = {"fast": {..., "success_rate": 0.9}, ...}
        if isinstance(node.value, ast.Dict):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    var = target.id.lower()
                    if any(kw in var for kw in ["strateg", "config", "option", "variant"]):
                        # Check if dict values have metrics-like keys
                        has_metrics = False
                        for v in node.value.values:
                            if isinstance(v, ast.Dict):
                                for k in v.keys:
                                    if isinstance(k, ast.Constant):
                                        key_str = str(k.value).lower()
                                        if any(
                                            m in key_str
                                            for m in [
                                                "rate",
                                                "latency",
                                                "score",
                                                "weight",
                                            ]
                                        ):
                                            has_metrics = True
                                            break

                        if has_metrics:
                            self.adaptive_patterns.append(
                                {
                                    "type": "strategy_config",
                                    "variable": target.id,
                                    "parent_function": self._current_function,
                                    "is_async": self._current_is_async,
                                    "lineno": node.lineno,
                                }
                            )
        self.generic_visit(node)
