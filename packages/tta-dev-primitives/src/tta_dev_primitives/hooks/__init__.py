# TTA.dev Primitives for Cline Hook Management

from .create_hook import CreateHookInput, CreateHookPrimitive
from .list_hooks import HookInfo, ListHooksPrimitive
from .refine_hook import (
    RefineHookInput,
    RefineHookPrimitive,
    RefineHookResult,
    RefinementAttempt,
)
from .test_hook import TestHookInput, TestHookPrimitive, TestResult
from .validate_hook import (
    ShellCheckIssue,
    ValidateHookInput,
    ValidateHookPrimitive,
    ValidationResult,
)

__all__ = [
    "ListHooksPrimitive",
    "HookInfo",
    "CreateHookPrimitive",
    "CreateHookInput",
    "ValidateHookPrimitive",
    "ValidateHookInput",
    "ValidationResult",
    "ShellCheckIssue",
    "TestHookPrimitive",
    "TestHookInput",
    "TestResult",
    "RefineHookPrimitive",
    "RefineHookInput",
    "RefineHookResult",
    "RefinementAttempt",
]
