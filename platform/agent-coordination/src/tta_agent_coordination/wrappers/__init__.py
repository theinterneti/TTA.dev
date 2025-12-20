"""
L4 Execution Wrappers - Direct tool interaction layer.

This module provides production-ready wrappers around external tools and APIs:
- GitHub API (PyGithub)
- Docker SDK
- PyTest CLI
- Snyk API
- Terraform CLI
- Kubernetes SDK
- Prometheus API

All wrappers inherit from WorkflowPrimitive and include:
- Error handling with detailed exceptions
- Rate limiting and retry logic
- Authentication management
- Observable via OpenTelemetry
- Type-safe interfaces
"""

from tta_agent_coordination.wrappers.docker_wrapper import (
    DockerConfig,
    DockerOperation,
    DockerResult,
    DockerSDKWrapper,
)
from tta_agent_coordination.wrappers.github_wrapper import (
    GitHubAPIWrapper,
    GitHubConfig,
    GitHubOperation,
    GitHubResult,
)
from tta_agent_coordination.wrappers.pytest_wrapper import (
    PyTestCLIWrapper,
    PyTestConfig,
    PyTestOperation,
    PyTestResult,
)

__all__ = [
    # Wrappers
    "GitHubAPIWrapper",
    "DockerSDKWrapper",
    "PyTestCLIWrapper",
    # Configs
    "GitHubConfig",
    "DockerConfig",
    "PyTestConfig",
    # Operations
    "GitHubOperation",
    "DockerOperation",
    "PyTestOperation",
    # Results
    "GitHubResult",
    "DockerResult",
    "PyTestResult",
]
