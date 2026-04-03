"""TTA.dev CLI: `tta setup` wizard and `tta validate-keys` health check.

No external dependencies — stdlib only (urllib.request, getpass, json, os,
pathlib, socket).
"""

from __future__ import annotations

import dataclasses
import getpass
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class SetupProvider:
    """Descriptor for a supported LLM provider."""

    name: str
    env_var: str
    signup_url: str
    validate_url: str
    auth_style: str  # "query_param" | "bearer" | "none"
    help_what: str
    help_how: list[str]
    is_local: bool = False


SETUP_PROVIDERS: list[SetupProvider] = [
    SetupProvider(
        name="Google AI Studio",
        env_var="GOOGLE_API_KEY",
        signup_url="https://aistudio.google.com",
        validate_url="https://generativelanguage.googleapis.com/v1beta/openai/models",
        auth_style="query_param",
        help_what="Google AI Studio gives free access to Gemini models.",
        help_how=[
            "Go to https://aistudio.google.com",
            "Sign in with your Google account.",
            "Click 'Get API key' in the left sidebar.",
            "Create a new API key and copy it.",
        ],
    ),
    SetupProvider(
        name="Groq",
        env_var="GROQ_API_KEY",
        signup_url="https://console.groq.com",
        validate_url="https://api.groq.com/openai/v1/models",
        auth_style="bearer",
        help_what="Groq offers extremely fast inference for open-source models.",
        help_how=[
            "Go to https://console.groq.com",
            "Sign up for a free account.",
            "Navigate to API Keys in the left sidebar.",
            "Click 'Create API Key' and copy it.",
        ],
    ),
    SetupProvider(
        name="OpenRouter",
        env_var="OPENROUTER_API_KEY",
        signup_url="https://openrouter.ai",
        validate_url="https://openrouter.ai/api/v1/models",
        auth_style="bearer",
        help_what="OpenRouter provides unified access to 100+ LLM providers.",
        help_how=[
            "Go to https://openrouter.ai",
            "Sign up for a free account.",
            "Go to https://openrouter.ai/keys",
            "Click 'Create Key' and copy it.",
        ],
    ),
    SetupProvider(
        name="Ollama",
        env_var="",
        signup_url="https://ollama.ai",
        validate_url="http://localhost:11434/api/tags",
        auth_style="none",
        help_what="Ollama runs LLMs locally on your machine — completely free.",
        help_how=[
            "Go to https://ollama.ai and download the installer.",
            "Install and start Ollama.",
            "Run: ollama pull gemma3:4b  (or any model you like)",
            "Ollama runs at http://localhost:11434 by default.",
        ],
        is_local=True,
    ),
]

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class ValidationResult:
    """Result of validating a single provider."""

    connected: bool
    models: list[str]
    error: str | None


def validate_provider(provider: SetupProvider, key: str | None) -> ValidationResult:
    """Test provider connectivity.

    Uses urllib.request with a 5-second timeout. Never includes key values
    in error messages.

    Args:
        provider: The provider descriptor to validate.
        key: The API key to use, or None for local providers.

    Returns:
        ValidationResult with connection status and up to 3 model names.
    """
    url = provider.validate_url
    headers: dict[str, str] = {}

    if provider.auth_style == "query_param" and key:
        url = f"{url}?key={key}"
    elif provider.auth_style == "bearer" and key:
        headers["Authorization"] = f"Bearer {key}"

    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(  # nosemgrep: dynamic-urllib-use-detected
            req, timeout=5
        ) as resp:
            raw = resp.read()
            data = json.loads(raw)
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            return ValidationResult(connected=False, models=[], error="Invalid API key")
        return ValidationResult(
            connected=False,
            models=[],
            error=f"HTTP {exc.code}: {exc.reason}",
        )
    except (TimeoutError, urllib.error.URLError, OSError):
        return ValidationResult(connected=False, models=[], error="Connection failed (timeout)")

    # Extract model names
    models: list[str] = []
    if provider.is_local:
        # Ollama: {"models": [{"name": "..."}]}
        for m in data.get("models", []):
            if isinstance(m, dict) and "name" in m:
                models.append(m["name"])
    else:
        # OpenAI-compat: {"data": [{"id": "..."}]}
        for m in data.get("data", []):
            if isinstance(m, dict) and "id" in m:
                models.append(m["id"])

    return ValidationResult(connected=True, models=models[:3], error=None)


# ---------------------------------------------------------------------------
# .env read / write
# ---------------------------------------------------------------------------


def _read_env(path: Path) -> dict[str, str]:
    """Parse a .env file into a dict.

    Skips comment lines (starting with #) and blank lines.
    Values that contain '=' are preserved (split on first '=' only).

    Args:
        path: Path to the .env file.

    Returns:
        Mapping of key→value. Empty dict if file doesn't exist.
    """
    if not path.exists():
        return {}
    result: dict[str, str] = {}
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" in stripped:
            key, _, value = stripped.partition("=")
            result[key.strip()] = value.strip()
    return result


def _write_env(path: Path, updates: dict[str, str]) -> None:
    """Atomically update keys in a .env file, preserving all other content.

    Algorithm:
      1. Read existing lines (or start empty if file doesn't exist).
      2. For each existing KEY=value line: if key in updates, replace value.
      3. Append any keys in updates not already in file.
      4. Write to <path>.tmp with chmod 0o600.
      5. os.replace(<path>.tmp, path) for atomic swap.

    Args:
        path: Path to the .env file.
        updates: Mapping of key→new_value to write.
    """
    # Read existing raw lines
    if path.exists():
        lines = path.read_text().splitlines(keepends=True)
    else:
        lines = []

    written_keys: set[str] = set()
    new_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.partition("=")[0].strip()
            if key in updates:
                new_lines.append(f"{key}={updates[key]}\n")
                written_keys.add(key)
                continue
        new_lines.append(line)

    # Append keys not already in file
    for key, value in updates.items():
        if key not in written_keys:
            new_lines.append(f"{key}={value}\n")

    tmp_path = path.parent / (path.name + ".tmp")
    try:
        tmp_path.write_text("".join(new_lines))
        os.chmod(tmp_path, 0o600)
        os.replace(tmp_path, path)
    except KeyboardInterrupt:
        if tmp_path.exists():
            tmp_path.unlink()
        raise


# ---------------------------------------------------------------------------
# VS Code MCP integration
# ---------------------------------------------------------------------------

_MCP_ENTRY = {
    "command": "uv",
    "args": ["run", "python", "-m", "ttadev.primitives.mcp_server"],
    "cwd": "${workspaceFolder}",
}


def _add_vscode_mcp(project_root: Path) -> None:
    """Add TTA.dev MCP server entry to .vscode/settings.json.

    Deep-merges without overwriting existing keys. Creates .vscode/ if needed.
    Operation is idempotent.

    Args:
        project_root: Root directory of the project.
    """
    vscode_dir = project_root / ".vscode"
    vscode_dir.mkdir(exist_ok=True)

    settings_path = vscode_dir / "settings.json"
    if settings_path.exists():
        try:
            settings: dict = json.loads(settings_path.read_text())
        except (json.JSONDecodeError, OSError):
            settings = {}
    else:
        settings = {}

    # Deep-merge into github.copilot.chat.mcpServers
    mcp_servers: dict = settings.setdefault("github.copilot.chat.mcpServers", {})
    mcp_servers.setdefault("tta-dev", _MCP_ENTRY)

    settings_path.write_text(json.dumps(settings, indent=2) + "\n")


# ---------------------------------------------------------------------------
# tta validate-keys
# ---------------------------------------------------------------------------

_RULE = "━" * 62


def _get_key(provider: SetupProvider, env: dict[str, str]) -> str | None:
    """Look up a provider's key from env dict or os.environ."""
    if provider.is_local:
        return None
    return env.get(provider.env_var) or os.environ.get(provider.env_var) or None


def cmd_validate_keys(args: object, *, project_root: Path) -> int:
    """Implement `tta validate-keys`.

    Args:
        args: Parsed CLI args (expects .json_output attribute).
        project_root: Directory containing .env and project files.

    Returns:
        0 if ≥1 provider connected, 1 if none.
    """
    json_output: bool = getattr(args, "json_output", False)

    env_path = project_root / ".env"
    env = _read_env(env_path)

    results: list[dict] = []
    connected_count = 0

    for provider in SETUP_PROVIDERS:
        key = _get_key(provider, env)
        result = validate_provider(provider, key)

        status = "connected" if result.connected else "not_configured"
        if not result.connected and key:
            status = "error"

        results.append(
            {
                "name": provider.name,
                "env_var": provider.env_var if not provider.is_local else None,
                "status": status,
                "models": result.models,
                "error": result.error,
                "is_local": provider.is_local,
            }
        )
        if result.connected:
            connected_count += 1

    if json_output:
        print(json.dumps({"providers": results}))
        return 0 if connected_count >= 1 else 1

    # Human-readable output
    print()
    print("Provider Status")
    print(_RULE)
    for r in results:
        name = r["env_var"] or r["name"]
        if r["status"] == "connected":
            model_str = ", ".join(r["models"][:2]) if r["models"] else ""
            suffix = f"  ({model_str})" if model_str else ""
            if r["is_local"]:
                print(f"{'Ollama':<22} ✅  Running at localhost:11434{suffix}")
            else:
                print(f"{name:<22} ✅  Connected{suffix}")
        elif r["status"] == "not_configured" and not r.get("error"):
            print(f"{name:<22} ❌  Not configured")
        else:
            err = r.get("error") or "Connection failed"
            print(f"{name:<22} ⚠️   {err}")

    print()
    if connected_count == 0:
        print("No providers connected. Run 'tta setup' to configure providers.")
    else:
        print(
            f"{connected_count} provider{'s' if connected_count != 1 else ''} connected."
            " Run 'tta setup' to configure missing providers."
        )

    return 0 if connected_count >= 1 else 1


# ---------------------------------------------------------------------------
# tta setup — wizard
# ---------------------------------------------------------------------------


def _check_git_tracking(env_path: Path) -> bool:
    """Return True if .env is tracked by git (warn the user)."""
    try:
        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", str(env_path)],
            capture_output=True,
            cwd=env_path.parent,
        )
        return result.returncode == 0
    except (OSError, FileNotFoundError):
        return False


def _print_help(provider: SetupProvider) -> None:
    print(f"\n  {provider.name}: {provider.help_what}")
    print(f"  Sign up: {provider.signup_url}\n")
    for i, step in enumerate(provider.help_how, 1):
        print(f"    {i}. {step}")
    print()


def _prompt_for_key(provider: SetupProvider) -> str | None:
    """Interactive prompt for an API key. Returns None on skip or empty input."""
    while True:
        try:
            val = getpass.getpass(f"  {provider.env_var} — Enter to skip, ? for help: ")
        except (EOFError, KeyboardInterrupt):
            raise

        if val == "?":
            _print_help(provider)
            continue
        return val or None


def _run_wizard(env_path: Path, project_root: Path) -> int:
    """Run the interactive setup wizard.

    Args:
        env_path: Path to the .env file.
        project_root: Root directory of the project.

    Returns:
        Number of providers successfully configured this session (cumulative
        is checked at end).
    """
    env = _read_env(env_path)
    configured_names: list[str] = []

    # ------------------------------------------------------------------ #
    # Step 1 — Environment file                                           #
    # ------------------------------------------------------------------ #
    print("\nStep 1/4 — Environment file")
    print(_RULE)

    env_example = project_root / ".env.example"
    if not env_path.exists():
        if env_example.exists():
            shutil.copy(env_example, env_path)
        else:
            env_path.write_text("")
        os.chmod(env_path, 0o600)
        print(f"  Created {env_path}")
    else:
        print("  Found existing .env — checking your keys...")

    if _check_git_tracking(env_path):
        print(
            "\n  ⚠️  WARNING: .env appears to be tracked by git!\n"
            "     Run: git rm --cached .env && echo '.env' >> .gitignore\n"
        )

    # ------------------------------------------------------------------ #
    # Step 2 — Provider prompts                                           #
    # ------------------------------------------------------------------ #
    print("\nStep 2/4 — LLM providers")
    print(_RULE)
    print("  We'll check each provider. Press Enter to skip any provider.\n")

    for provider in SETUP_PROVIDERS:
        print(f"  [{provider.name}]")

        if provider.is_local:
            # Ollama — no key needed, just test connectivity
            print("  Checking Ollama at localhost:11434...")
            result = validate_provider(provider, None)
            if result.connected:
                model_str = ", ".join(result.models) if result.models else "no models found"
                print(f"  ✅  Running  ({model_str})\n")
                configured_names.append(provider.name)
            else:
                print("  ❌  Not running")
                print("       Install: https://ollama.ai")
                print("       Then:  ollama pull gemma3:4b\n")
            continue

        existing_key = env.get(provider.env_var) or os.environ.get(provider.env_var)

        if existing_key:
            print("  Key found in environment — validating...")
            result = validate_provider(provider, existing_key)
            if result.connected:
                model_str = ", ".join(result.models[:2])
                print(f"  ✅  Connected  ({model_str})")
                configured_names.append(provider.name)
            else:
                print(f"  ⚠️  {result.error or 'Connection failed'}")
            print("  [keeping existing key]\n")
            continue

        # Prompt for new key
        key = _prompt_for_key(provider)
        if key is None:
            print("  ⏭  Skipped\n")
            continue

        result = validate_provider(provider, key)

        if result.connected:
            model_str = ", ".join(result.models[:2])
            print(f"  ✅  Connected  ({model_str})")
            _write_env(env_path, {provider.env_var: key})
            env[provider.env_var] = key
            configured_names.append(provider.name)
            print()
        elif "Connection failed" in (result.error or ""):
            print(f"  ⚠️  {result.error}")
            try:
                save = input("     Save anyway? [y/N]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                raise
            if save == "y":
                _write_env(env_path, {provider.env_var: key})
                env[provider.env_var] = key
                configured_names.append(provider.name)
                print("  Saved.\n")
            else:
                print("  ⏭  Skipped\n")
        else:
            # Invalid key — offer one retry
            print(f"  ❌  {result.error}")
            print("  Let's try again...")
            key2 = _prompt_for_key(provider)
            if key2 is None:
                print("  ⏭  Skipped\n")
                continue
            result2 = validate_provider(provider, key2)
            if result2.connected:
                model_str = ", ".join(result2.models[:2])
                print(f"  ✅  Connected  ({model_str})")
                _write_env(env_path, {provider.env_var: key2})
                env[provider.env_var] = key2
                configured_names.append(provider.name)
            else:
                print(f"  ❌  {result2.error} — skipping.\n")

    # ------------------------------------------------------------------ #
    # Step 3 — VS Code MCP                                                #
    # ------------------------------------------------------------------ #
    print("\nStep 3/4 — VS Code MCP integration")
    print(_RULE)
    try:
        answer = input("  Add TTA.dev MCP server to VS Code Copilot? [Y/n]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        raise

    added_mcp = False
    if answer in ("", "y", "yes"):
        _add_vscode_mcp(project_root)
        print("  ✅  MCP server entry added to VS Code\n")
        added_mcp = True
    else:
        print("  ⏭  Skipped\n")

    # ------------------------------------------------------------------ #
    # Step 4 — Summary                                                    #
    # ------------------------------------------------------------------ #
    print("Step 4/4 — Summary")
    print(_RULE)

    if configured_names:
        names_str = ", ".join(configured_names)
        print(
            f"  ✅ {len(configured_names)} provider{'s' if len(configured_names) != 1 else ''}"
            f" configured ({names_str})"
        )
    else:
        print("  ⚠️  No providers configured")

    if added_mcp:
        print("  ✅  MCP server entry added to VS Code")

    print()
    print('  Try: tta workflow run feature_dev --goal "Add a hello world endpoint"')
    print("  Or:  tta validate-keys   (check provider status any time)")
    print()

    return len(configured_names)


def cmd_setup(args: object, *, project_root: Path) -> int:
    """Implement `tta setup` interactive wizard.

    Args:
        args: Parsed CLI args (expects .non_interactive attribute).
        project_root: Directory containing .env and project files.

    Returns:
        0 if ≥1 provider configured, 1 otherwise.
    """
    non_interactive: bool = getattr(args, "non_interactive", False)

    if not sys.stdin.isatty() or non_interactive:
        print("error: 'tta setup' requires an interactive terminal.", file=sys.stderr)
        print(
            "       Use 'tta validate-keys' to check existing configuration.",
            file=sys.stderr,
        )
        return 1

    env_path = project_root / ".env"
    tmp_path = project_root / ".env.tmp"

    try:
        count = _run_wizard(env_path, project_root)
    except KeyboardInterrupt:
        if tmp_path.exists():
            tmp_path.unlink()
        print("\n\nSetup interrupted. No changes written.")
        return 1

    if count == 0:
        print("No providers configured. Run 'tta setup' again or set API keys manually.")
        return 1

    return 0
