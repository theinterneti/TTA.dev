#!/usr/bin/env python3
"""Validate chatmode structure and Hypertool integration."""

import json
import re
from pathlib import Path
from typing import Any

# Persona definitions directory
REPO_ROOT = Path("/home/thein/repos/TTA.dev")
PERSONAS_DIR = REPO_ROOT / ".hypertool" / "personas"
TTA_CHATMODES = REPO_ROOT / ".tta" / "chatmodes"
UAC_CHATMODES = REPO_ROOT / "packages" / "universal-agent-context"

# Expected persona names
VALID_PERSONAS = [
    "tta-backend-engineer",
    "tta-frontend-engineer",
    "tta-devops-engineer",
    "tta-testing-specialist",
    "tta-observability-expert",
    "tta-data-scientist",
]

# Token budget ranges
TOKEN_BUDGET_RANGES = {
    "tta-backend-engineer": (1900, 2100),
    "tta-frontend-engineer": (1700, 1900),
    "tta-devops-engineer": (1700, 1900),
    "tta-testing-specialist": (1400, 1600),
    "tta-observability-expert": (1900, 2100),
    "tta-data-scientist": (1600, 1800),
}


def extract_frontmatter(content: str) -> dict[str, Any]:
    """Extract YAML frontmatter from chatmode file."""
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return {}

    # Simple YAML parsing (just for key: value)
    frontmatter: dict[str, Any] = {}
    for line in match.group(1).split('\n'):
        if ':' in line and not line.strip().startswith('-'):
            key, value = line.split(':', 1)
            frontmatter[key.strip()] = value.strip()

    return frontmatter


def validate_chatmode(file_path: Path) -> tuple[bool, list[str], dict[str, Any]]:
    """Validate single chatmode file."""
    errors: list[str] = []
    info: dict[str, Any] = {}

    # Read file
    try:
        content = file_path.read_text()
    except Exception as e:
        return False, [f"Failed to read file: {e}"], {}

    # Check frontmatter exists
    frontmatter = extract_frontmatter(content)
    if not frontmatter:
        errors.append("No YAML frontmatter found")
        return False, errors, {}

    # Check hypertool_persona field
    if 'hypertool_persona' not in frontmatter:
        errors.append("Missing 'hypertool_persona' field")
    else:
        persona = frontmatter['hypertool_persona']
        info['persona'] = persona

        # Validate persona name
        if persona not in VALID_PERSONAS:
            errors.append(f"Invalid persona: {persona}")
        else:
            # Check persona JSON exists
            persona_file = PERSONAS_DIR / f"{persona}.json"
            if not persona_file.exists():
                errors.append(f"Persona definition not found: {persona_file}")
            else:
                info['persona_file_exists'] = True

    # Check token budget
    if 'persona_token_budget' not in frontmatter:
        errors.append("Missing 'persona_token_budget' field")
    else:
        try:
            budget = int(frontmatter['persona_token_budget'])
            info['token_budget'] = budget

            persona = frontmatter.get('hypertool_persona')
            if persona in TOKEN_BUDGET_RANGES:
                min_budget, max_budget = TOKEN_BUDGET_RANGES[persona]
                if not (min_budget <= budget <= max_budget):
                    errors.append(
                        f"Token budget {budget} outside expected range "
                        f"[{min_budget}, {max_budget}] for {persona}"
                    )
        except ValueError:
            errors.append("Invalid token budget (not a number)")

    # Check tools_via_hypertool
    if 'tools_via_hypertool' not in frontmatter:
        errors.append("Missing 'tools_via_hypertool' field")
    elif frontmatter['tools_via_hypertool'] != 'true':
        errors.append("'tools_via_hypertool' should be 'true'")

    return len(errors) == 0, errors, info


def main():
    """Run validation on all chatmodes."""
    print("🔍 Validating Chatmode Structure\n")
    print("=" * 70)

    # Find all chatmode files
    chatmode_files = []

    # Core chatmodes
    if TTA_CHATMODES.exists():
        chatmode_files.extend(TTA_CHATMODES.glob("*.chatmode.md"))

    # UAC chatmodes
    if UAC_CHATMODES.exists():
        chatmode_files.extend(UAC_CHATMODES.rglob("*.chatmode.md"))

    print(f"Found {len(chatmode_files)} chatmode files\n")

    # Validate each file
    results = {
        "passed": 0,
        "failed": 0,
        "errors": {},
        "persona_distribution": {},
        "token_budgets": []
    }

    for file_path in sorted(chatmode_files):
        relative_path = file_path.relative_to(Path("/home/thein/repos/TTA.dev"))
        valid, errors, info = validate_chatmode(file_path)

        if valid:
            print(f"✅ {relative_path}")
            print(f"   └─ Persona: {info.get('persona', 'N/A')} ({info.get('token_budget', 'N/A')} tokens)")
            results["passed"] += 1

            # Track persona distribution
            persona = info.get('persona')
            if persona:
                results["persona_distribution"][persona] = \
                    results["persona_distribution"].get(persona, 0) + 1

            # Track token budgets
            if 'token_budget' in info:
                results["token_budgets"].append(info['token_budget'])
        else:
            print(f"❌ {relative_path}")
            for error in errors:
                print(f"   └─ {error}")
            results["failed"] += 1
            results["errors"][str(relative_path)] = errors

    # Summary
    print("\n" + "=" * 70)
    print(f"\n📊 Validation Summary:")
    print(f"   ✅ Passed: {results['passed']}")
    print(f"   ❌ Failed: {results['failed']}")
    print(f"   📈 Success Rate: {results['passed'] / len(chatmode_files) * 100:.1f}%")

    # Persona distribution
    if results["persona_distribution"]:
        print(f"\n👥 Persona Distribution:")
        for persona, count in sorted(results["persona_distribution"].items()):
            percentage = count / results["passed"] * 100
            print(f"   • {persona}: {count} ({percentage:.1f}%)")

    # Token budget stats
    if results["token_budgets"]:
        avg_budget = sum(results["token_budgets"]) / len(results["token_budgets"])
        min_budget = min(results["token_budgets"])
        max_budget = max(results["token_budgets"])
        print(f"\n💰 Token Budget Statistics:")
        print(f"   • Average: {avg_budget:.0f} tokens")
        print(f"   • Range: {min_budget} - {max_budget} tokens")

    if results["failed"] > 0:
        print(f"\n⚠️  {results['failed']} chatmode(s) need attention")
        return 1
    else:
        print(f"\n🎉 All chatmodes validated successfully!")
        return 0


if __name__ == "__main__":
    exit(main())
