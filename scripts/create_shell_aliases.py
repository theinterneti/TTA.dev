#!/usr/bin/env python3
"""
Shell Alias Generator for TTA.dev

Generates shell-specific aliases for common uv and TTA.dev commands.
Automatically detects shell type and creates appropriate aliases.

Usage:
    # Generate aliases for current shell
    python scripts/create_shell_aliases.py

    # Add to shell config permanently
    python scripts/create_shell_aliases.py --install

    # Show available aliases
    python scripts/create_shell_aliases.py --list
"""

import argparse
import os
import platform
import subprocess
from pathlib import Path
from typing import Dict, List


class ShellAliasGenerator:
    """Generates shell-specific aliases for TTA.dev development"""

    # Common aliases for all shells
    COMMON_ALIASES = {
        # UV shortcuts
        "uvsync": "uv sync --all-extras",
        "uvsync-dev": "uv sync --dev",
        "uvr": "uv run",
        "uvtest": "uv run pytest",
        "uvtest-v": "uv run pytest -v",
        "uvtest-cov": "uv run pytest --cov",
        "uvlint": "uv run ruff check . --fix",
        "uvfmt": "uv run ruff format .",

        # Worktree management
        "wtlist": "uv run python scripts/worktree_init.py list",
        "wtinit": "python scripts/worktree_init.py init",

        # TTA.dev specific workflows
        "build-all": "uv run python -m build .",
        "type-check": "uv run pyright packages/",
        "quality-check": "uvfmt && uvlint && type-check && uvtest",

        # Development shortcuts
        "dev-up": "uvsync && uvlint",
        "test-watch": "uv run pytest-watch",
        "serve-docs": "uv run mkdocs serve",
    }

    # Environment-based aliases (when .env exists)
    ENV_ALIASES = {
        "uvrun": "uv run --env-file .env",
        "uvtest-env": "uv run --env-file .env pytest -v",
        "uvserve": "uv run --env-file .env python run_server.py",
        "uvmigrate": "uv run --env-file .env alembic upgrade head",
    }

    # Shell-specific syntax
    SHELL_SYNTAX = {
        "bash": {
            "comment": "#",
            "export": "export",
            "alias": "alias",
            "function": "function",
            "end_function": "}",
            "declaration": "=",
            "single_quote": "'",
            "double_quote": '"',
        },
        "zsh": {
            "comment": "#",
            "export": "export",
            "alias": "alias",
            "function": "function",
            "end_function": "}",
            "declaration": "=",
            "single_quote": "'",
            "double_quote": '"',
        },
        "fish": {
            "comment": "#",
            "export": "set -x",
            "alias": "alias",
            "function": "function",
            "end_function": "end",
            "declaration": " ",
            "single_quote": "'",
            "double_quote": '"',
        },
        "powershell": {
            "comment": "#",
            "export": "$env:",
            "alias": "Set-Alias",
            "function": "function",
            "end_function": "}",
            "declaration": " = ",
            "single_quote": "'",
            "double_quote": '"',
        },
    }

    def __init__(self, shell_type: str = None):
        self.shell_type = shell_type or self._detect_shell()
        self.shell_config = self.SHELL_SYNTAX.get(self.shell_type, self.SHELL_SYNTAX["bash"])
        self.env_file = Path(".env")
        self.has_env = self.env_file.exists()

    def _detect_shell(self) -> str:
        """Detect current shell"""
        # Try environment variables first
        shell_env = os.environ.get("SHELL", "").lower()

        if shell_env:
            if "zsh" in shell_env:
                return "zsh"
            elif "fish" in shell_env:
                return "fish"
            elif "bash" in shell_env:
                return "bash"
            elif "pwsh" in shell_env or "powershell" in shell_env:
                return "powershell"

        # Try detecting from parent process
        try:
            if platform.system() == "Windows":
                # On Windows, check if we're in PowerShell
                result = subprocess.run(
                    ["powershell", "-Command", "$PSVersionTable"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    return "powershell"
            else:
                # On Unix-like systems, check ps
                result = subprocess.run(
                    ["ps", "-p", str(os.getppid()), "-o", "comm="],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    parent = result.stdout.strip().lower()
                    if "zsh" in parent:
                        return "zsh"
                    elif "fish" in parent:
                        return "fish"
                    elif "bash" in parent:
                        return "bash"
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass

        # Default fallback
        return "bash"

    def generate_aliases(self) -> List[str]:
        """Generate shell alias commands"""
        aliases = []

        # Add header
        aliases.append(f"{self.shell_config['comment']} TTA.dev Shell Aliases - Generated by create_shell_aliases.py")
        aliases.append(f"{self.shell_config['comment']} Shell: {self.shell_type}")
        aliases.append(f"{self.shell_config['comment']} Environment file: {'.env' if self.has_env else 'not found'}")
        aliases.append("")

        # Add common aliases
        aliases.append(f"{self.shell_config['comment']} Common UV and TTA.dev shortcuts")
        for alias_name, command in self.COMMON_ALIASES.items():
            aliases.append(self._create_alias(alias_name, command))

        aliases.append("")

        # Add environment-aware aliases if .env exists
        if self.has_env:
            aliases.append(f"{self.shell_config['comment']} Environment-aware shortcuts (.env file detected)")
            for alias_name, command in self.ENV_ALIASES.items():
                aliases.append(self._create_alias(alias_name, command))
        else:
            aliases.append(f"{self.shell_config['comment']} Environment file not found - skipping env-aware aliases")
            aliases.append(f"{self.shell_config['comment']} Create a .env file to enable uvrun, uvtest-env, uvserve aliases")

        return aliases

    def _create_alias(self, name: str, command: str) -> str:
        """Create a shell-specific alias line"""
        if self.shell_type in ["bash", "zsh"]:
            return f"alias {name}='{command}'"
        elif self.shell_type == "fish":
            # Fish uses: alias name 'command'
            return f"alias {name} '{command}'"
        elif self.shell_type == "powershell":
            # PowerShell uses: Set-Alias -Name name -Value { command }
            return f"Set-Alias -Name {name} -Value {{ {command} }}"
        else:
            return f"alias {name}='{command}'"

    def get_shell_config_path(self) -> Path:
        """Get the shell configuration file path"""
        home = Path.home()

        if self.shell_type == "zsh":
            return home / ".zshrc"
        elif self.shell_type == "bash":
            return home / ".bashrc"
        elif self.shell_type == "fish":
            return home / ".config" / "fish" / "config.fish"
        elif self.shell_type == "powershell":
            # PowerShell profile is more complex, return user profile
            try:
                result = subprocess.run(
                    ["powershell", "-Command", "$PROFILE"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return Path(result.stdout.strip())
            except subprocess.SubprocessError:
                pass
            return home / "Documents" / "PowerShell" / "Microsoft.PowerShell_profile.ps1"
        else:
            return home / ".bashrc"

    def install_aliases(self, backup: bool = True) -> None:
        """Install aliases to shell configuration"""
        config_path = self.get_shell_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)

        aliases = self.generate_aliases()
        alias_block = "\n".join(aliases)

        # Read existing config
        existing_content = ""
        if config_path.exists():
            existing_content = config_path.read_text()

        # Create backup
        if backup and config_path.exists():
            backup_path = config_path.with_suffix(config_path.suffix + ".backup")
            config_path.rename(backup_path)
            print(f"✅ Backup created: {backup_path}")

        # Remove existing TTA.dev aliases (between marker comments)
        marker_start = f"{self.shell_config['comment']} TTA.dev Shell Aliases - Generated by create_shell_aliases.py"
        marker_end = f"{self.shell_config['comment']} End TTA.dev aliases"

        lines = existing_content.split("\n")
        filtered_lines = []
        skip_mode = False

        for line in lines:
            if line.strip() == marker_start:
                skip_mode = True
            elif line.strip() == marker_end:
                skip_mode = False
                continue  # Remove the end marker too

            if not skip_mode:
                filtered_lines.append(line)

        # Add new aliases
        new_content = "\n".join(filtered_lines).strip()
        if new_content:
            new_content += "\n\n"

        new_content += alias_block
        new_content += f"\n{marker_end}\n"

        # Write to config file
        config_path.write_text(new_content)
        print(f"✅ Aliases installed to: {config_path}")
        print("🔄 Restart your shell or run: source ~/.bashrc (or equivalent)")

    def show_aliases(self) -> None:
        """Display available aliases"""
        print(f"🎯 TTA.dev Shell Aliases for {self.shell_type.title()}")
        print(f"📁 Environment file: {'.env' if self.has_env else 'not found (limited aliases)'}")
        print("=" * 60)

        print("\n🚀 Common Shortcuts:")
        for alias_name, command in self.COMMON_ALIASES.items():
            print(f"  {alias_name:<12} → {command}")

        if self.has_env:
            print("\n🌍 Environment-Aware (.env detected):")
            for alias_name, command in self.ENV_ALIASES.items():
                print(f"  {alias_name:<12} → {command}")
        else:
            print("\n⚠️  Create a .env file to enable env-aware aliases")

        print("\n📝 Installation:")
        print(f"  python scripts/create_shell_aliases.py --install")
        print(f"  # Or add to your shell config: {self.get_shell_config_path()}")


def main():
    parser = argparse.ArgumentParser(description="Generate shell aliases for TTA.dev development")
    parser.add_argument(
        "--shell",
        choices=["bash", "zsh", "fish", "powershell", "auto"],
        default="auto",
        help="Target shell type (auto-detects by default)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Show available aliases"
    )
    parser.add_argument(
        "--install",
        action="store_true",
        help="Install aliases to shell configuration"
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Don't create backup when installing"
    )

    args = parser.parse_args()

    shell_type = None if args.shell == "auto" else args.shell
    generator = ShellAliasGenerator(shell_type)

    if args.list:
        generator.show_aliases()
    elif args.install:
        generator.install_aliases(backup=not args.no_backup)
    else:
        # Default: print aliases to stdout for manual sourcing
        aliases = generator.generate_aliases()
        print("# Copy and paste these into your shell, or run:")
        print(f"# python scripts/create_shell_aliases.py --install")
        print("#")
        print("\n".join(aliases))


if __name__ == "__main__":
    main()
