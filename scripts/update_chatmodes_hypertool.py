#!/usr/bin/env python3
"""
Update all chatmode files with Hypertool persona frontmatter.

This script adds or updates YAML frontmatter in .chatmode.md files to include
Hypertool persona references, token budgets, and MCP server configurations.
"""

import re
from pathlib import Path
from typing import Dict, List

# Persona mapping based on chatmode name patterns
PERSONA_MAPPINGS = {
    # Backend Engineering (2000 tokens)
    "tta-backend-engineer": {
        "token_budget": 2000,
        "patterns": ["backend", "api", "database", "python", "async", "architect"],
        "mcp_servers": ["context7", "github", "sequential-thinking", "gitmcp", "serena", "mcp-logseq"],
        "restricted_paths": ["packages/**/frontend/**", "**/node_modules/**"],
    },
    # Frontend Engineering (1800 tokens)
    "tta-frontend-engineer": {
        "token_budget": 1800,
        "patterns": ["frontend", "ui", "ux", "react", "vue", "typescript", "component"],
        "mcp_servers": ["context7", "playwright", "github", "gitmcp", "serena"],
        "restricted_paths": ["packages/**/backend/**", "**/tests/**"],
    },
    # DevOps Engineering (1800 tokens)
    "tta-devops-engineer": {
        "token_budget": 1800,
        "patterns": ["devops", "deploy", "docker", "kubernetes", "ci-cd", "infrastructure"],
        "mcp_servers": ["github", "gitmcp", "serena", "grafana"],
        "restricted_paths": ["packages/**/src/**/*.py", "packages/**/frontend/**"],
    },
    # Testing Specialist (1500 tokens)
    "tta-testing-specialist": {
        "token_budget": 1500,
        "patterns": ["qa", "test", "quality", "integration", "e2e", "performance-test", "security-test"],
        "mcp_servers": ["context7", "playwright", "github", "gitmcp"],
        "restricted_paths": ["packages/**/frontend/**", "**/node_modules/**"],
    },
    # Observability Expert (2000 tokens)
    "tta-observability-expert": {
        "token_budget": 2000,
        "patterns": ["observability", "monitoring", "metrics", "trace", "prometheus", "grafana"],
        "mcp_servers": ["context7", "grafana", "github", "sequential-thinking", "serena"],
        "restricted_paths": ["packages/**/frontend/**", "**/node_modules/**"],
    },
    # Data Scientist (1700 tokens)
    "tta-data-scientist": {
        "token_budget": 1700,
        "patterns": ["data", "ml", "langgraph", "prompt", "analytics", "jupyter"],
        "mcp_servers": ["context7", "github", "sequential-thinking", "mcp-logseq"],
        "restricted_paths": ["**/.github/workflows/**", "**/infrastructure/**"],
    },
}


def detect_persona(filename: str, content: str) -> str:
    """Detect appropriate persona based on filename and content."""
    filename_lower = filename.lower()
    content_lower = content.lower()
    
    # Score each persona
    scores = {}
    for persona, config in PERSONA_MAPPINGS.items():
        score = 0
        for pattern in config["patterns"]:
            if pattern in filename_lower:
                score += 10  # Filename match is strong signal
            if pattern in content_lower:
                score += 1  # Content match is weaker
        scores[persona] = score
    
    # Return persona with highest score
    if not scores or max(scores.values()) == 0:
        return "tta-backend-engineer"  # Default fallback
    
    return max(scores.items(), key=lambda x: x[1])[0]


def has_hypertool_frontmatter(content: str) -> bool:
    """Check if file already has Hypertool persona configuration."""
    return "hypertool_persona:" in content


def extract_existing_frontmatter(content: str) -> tuple[str | None, str]:
    """Extract existing YAML frontmatter and body content."""
    frontmatter_pattern = r'^---\n(.*?)\n---\n(.*)$'
    match = re.match(frontmatter_pattern, content, re.DOTALL)
    
    if match:
        return match.group(1), match.group(2)
    return None, content


def create_hypertool_frontmatter(persona: str, existing_frontmatter: str | None = None) -> str:
    """Create Hypertool frontmatter YAML."""
    config = PERSONA_MAPPINGS[persona]
    
    # Build frontmatter
    frontmatter = []
    
    # Preserve existing frontmatter fields if any
    if existing_frontmatter:
        # Parse existing fields
        for line in existing_frontmatter.split('\n'):
            if line.strip() and not line.strip().startswith('hypertool_'):
                frontmatter.append(line)
    
    # Add Hypertool configuration
    frontmatter.extend([
        f"hypertool_persona: {persona}",
        f"persona_token_budget: {config['token_budget']}",
        "tools_via_hypertool: true",
        "security:",
        "  restricted_paths:",
    ])
    
    for path in config["restricted_paths"]:
        frontmatter.append(f'    - "{path}"')
    
    frontmatter.append("  allowed_mcp_servers:")
    for server in config["mcp_servers"]:
        frontmatter.append(f"    - {server}")
    
    return '\n'.join(frontmatter)


def add_persona_to_header(content: str, persona: str) -> str:
    """Add persona indicator to the main header."""
    config = PERSONA_MAPPINGS[persona]
    
    # Find the first header with role/description
    pattern = r'(# [^\n]+\n\n\*\*Role[^\n]*\n[^\n]+\n[^\n]+)'
    
    def replace_header(match):
        header = match.group(1)
        # Add persona line if not already present
        if "**Persona:**" not in header:
            persona_icons = {
                "tta-backend-engineer": "🐍",
                "tta-frontend-engineer": "⚛️",
                "tta-devops-engineer": "🚀",
                "tta-testing-specialist": "🧪",
                "tta-observability-expert": "📊",
                "tta-data-scientist": "📈",
            }
            icon = persona_icons.get(persona, "🎭")
            persona_name = persona.replace("tta-", "").replace("-", " ").title()
            header += f'\n**Persona:** {icon} TTA {persona_name} ({config["token_budget"]} tokens via Hypertool)'
        return header
    
    return re.sub(pattern, replace_header, content)


def update_chatmode_file(filepath: Path, dry_run: bool = False) -> bool:
    """Update a single chatmode file with Hypertool frontmatter."""
    try:
        content = filepath.read_text()
        
        # Skip if already has Hypertool config
        if has_hypertool_frontmatter(content):
            print(f"✓ {filepath.name} - Already updated")
            return False
        
        # Detect appropriate persona
        persona = detect_persona(filepath.name, content)
        
        # Extract existing frontmatter
        existing_fm, body = extract_existing_frontmatter(content)
        
        # Create Hypertool frontmatter
        hypertool_fm = create_hypertool_frontmatter(persona, existing_fm)
        
        # Add persona to header
        body = add_persona_to_header(body, persona)
        
        # Combine
        new_content = f"---\n{hypertool_fm}\n---\n{body}"
        
        if dry_run:
            print(f"📝 {filepath.name} → {persona} ({PERSONA_MAPPINGS[persona]['token_budget']} tokens)")
            return True
        else:
            filepath.write_text(new_content)
            print(f"✅ {filepath.name} → {persona}")
            return True
    
    except Exception as e:
        print(f"❌ {filepath.name} - Error: {e}")
        return False


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Update chatmode files with Hypertool frontmatter")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be updated without making changes")
    parser.add_argument("--path", default="packages/universal-agent-context", help="Path to search for chatmodes")
    args = parser.parse_args()
    
    # Find all chatmode files
    root = Path(args.path)
    chatmode_files = list(root.rglob("*.chatmode.md"))
    
    print(f"Found {len(chatmode_files)} chatmode files\n")
    
    if args.dry_run:
        print("DRY RUN - No files will be modified\n")
    
    updated = 0
    skipped = 0
    
    for filepath in sorted(chatmode_files):
        if update_chatmode_file(filepath, dry_run=args.dry_run):
            updated += 1
        else:
            skipped += 1
    
    print(f"\n{'Dry run' if args.dry_run else 'Summary'}: {updated} files would be updated, {skipped} skipped")


if __name__ == "__main__":
    main()
