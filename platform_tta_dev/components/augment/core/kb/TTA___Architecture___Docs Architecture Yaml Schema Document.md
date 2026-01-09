---
title: YAML Schema - Universal Agent Context System
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/architecture/YAML_SCHEMA.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Architecture/YAML Schema - Universal Agent Context System]]

**Complete specification for YAML frontmatter in instruction and chat mode files**

---

## Overview

The Universal Agent Context System uses YAML frontmatter to provide structured metadata for instruction files and chat mode files. This enables selective loading, security boundaries, and cross-agent compatibility.

---

## Instruction File Schema

### Required Fields

```yaml
---
applyTo: "**/*.py"           # Required: Glob pattern(s) for file matching
tags: ["python", "quality"]  # Required: List of tags for categorization
description: "Brief description of the instruction file"  # Required
---
```

### Optional Fields

```yaml
---
applyTo: "**/*.py"
tags: ["python", "quality"]
description: "Python quality standards"
priority: 5                  # Optional: Integer 1-10 (default: 5)
version: "1.0.0"            # Optional: Semantic version
---
```

### Complete Example

```yaml
---
applyTo: "**/*.py"
tags: ["python", "quality", "testing"]
description: "Python quality standards and testing requirements"
priority: 8
version: "1.0.0"
---

# Python Quality Standards

## Overview
...
```

### Field Specifications

#### `applyTo` (Required)

**Type**: String or Array of Strings
**Description**: Glob pattern(s) for file matching
**Examples**:

```yaml
# Single pattern
applyTo: "**/*.py"

# Multiple patterns
applyTo:
  - "**/*.py"
  - "**/*.pyi"
  - "tests/**/*.py"

# Specific directories
applyTo: "src/**/*.ts"

# Multiple file types
applyTo:
  - "**/*.js"
  - "**/*.jsx"
  - "**/*.ts"
  - "**/*.tsx"
```

**Validation Rules**:
- Must be a string or array of strings
- Each pattern must be a valid glob pattern
- Patterns are case-sensitive
- Use `**` for recursive directory matching
- Use `*` for wildcard matching

#### `tags` (Required)

**Type**: Array of Strings
**Description**: Tags for categorization and filtering
**Examples**:

```yaml
tags: ["python", "quality"]
tags: ["react", "frontend", "typescript"]
tags: ["security", "api", "authentication"]
```

**Validation Rules**:
- Must be an array
- Must contain at least one tag
- Tags should be lowercase
- Tags should be descriptive and specific

#### `description` (Required)

**Type**: String
**Description**: Brief description of the instruction file
**Examples**:

```yaml
description: "Python quality standards and best practices"
description: "React component development guidelines"
description: "API security requirements and patterns"
```

**Validation Rules**:
- Must be a non-empty string
- Should be concise (1-2 sentences)
- Should clearly describe the purpose

#### `priority` (Optional)

**Type**: Integer
**Description**: Loading priority (1-10, higher = more important)
**Default**: 5
**Examples**:

```yaml
priority: 1   # Low priority
priority: 5   # Medium priority (default)
priority: 10  # High priority
```

**Validation Rules**:
- Must be an integer between 1 and 10
- Higher numbers = higher priority
- Affects loading order when multiple instructions match

#### `version` (Optional)

**Type**: String
**Description**: Semantic version of the instruction file
**Examples**:

```yaml
version: "1.0.0"
version: "2.1.3"
version: "0.5.0-beta"
```

**Validation Rules**:
- Should follow semantic versioning (MAJOR.MINOR.PATCH)
- Optional pre-release and build metadata allowed

---

## Chat Mode File Schema

### Required Fields

```yaml
---
mode: "backend-developer"                    # Required: Unique mode identifier
description: "Backend development role"      # Required: Brief description
cognitive_focus: "Backend architecture"      # Required: Focus area
security_level: "MEDIUM"                     # Required: LOW, MEDIUM, or HIGH
---
```

### Optional Fields

```yaml
---
mode: "backend-developer"
description: "Backend development role"
cognitive_focus: "Backend architecture and implementation"
security_level: "MEDIUM"
allowed_tools: ["editFiles", "runCommands"]  # Optional: List of allowed tools
denied_tools: ["deleteFiles"]                # Optional: List of denied tools
approval_required: ["deployProduction"]      # Optional: Tools requiring approval
version: "1.0.0"                             # Optional: Semantic version
---
```

### Complete Example

```yaml
---
mode: "backend-developer"
description: "Backend development role with focus on API design and database optimization"
cognitive_focus: "Backend architecture, API design, database optimization, performance"
security_level: "MEDIUM"
allowed_tools:
  - "editFiles"
  - "runCommands"
  - "codebase-retrieval"
  - "testFailure"
denied_tools:
  - "deleteFiles"
  - "deployProduction"
approval_required:
  - "deployStaging"
version: "1.0.0"
---

# Backend Developer Chat Mode

## Role Description
...
```

### Field Specifications

#### `mode` (Required)

**Type**: String
**Description**: Unique identifier for the chat mode
**Examples**:

```yaml
mode: "backend-developer"
mode: "frontend-developer"
mode: "qa-engineer"
mode: "devops-engineer"
```

**Validation Rules**:
- Must be a non-empty string
- Should be lowercase with hyphens
- Should be unique across all chat modes
- Should be descriptive of the role

#### `description` (Required)

**Type**: String
**Description**: Brief description of the chat mode
**Examples**:

```yaml
description: "Backend development role"
description: "Frontend development with React and TypeScript"
description: "Quality assurance and testing"
```

**Validation Rules**:
- Must be a non-empty string
- Should be concise (1-2 sentences)
- Should clearly describe the role

#### `cognitive_focus` (Required)

**Type**: String
**Description**: Primary focus areas for this mode
**Examples**:

```yaml
cognitive_focus: "Backend architecture and implementation"
cognitive_focus: "Frontend UI/UX, React components, TypeScript"
cognitive_focus: "Test coverage, quality assurance, bug detection"
```

**Validation Rules**:
- Must be a non-empty string
- Should describe the main areas of focus
- Can include multiple focus areas separated by commas

#### `security_level` (Required)

**Type**: String (Enum)
**Description**: Security level for this mode
**Allowed Values**: `LOW`, `MEDIUM`, `HIGH`
**Examples**:

```yaml
security_level: "LOW"     # Read-only operations
security_level: "MEDIUM"  # Standard development operations
security_level: "HIGH"    # Deployment and infrastructure operations
```

**Validation Rules**:
- Must be one of: `LOW`, `MEDIUM`, `HIGH`
- Must be uppercase
- Determines default tool access restrictions

#### `allowed_tools` (Optional)

**Type**: Array of Strings
**Description**: List of tools this mode can use
**Examples**:

```yaml
allowed_tools:
  - "editFiles"
  - "runCommands"
  - "codebase-retrieval"
  - "testFailure"
```

**Validation Rules**:
- Must be an array of strings
- Tool names should match available tools
- If omitted, default tools for security level apply

#### `denied_tools` (Optional)

**Type**: Array of Strings
**Description**: List of tools this mode cannot use
**Examples**:

```yaml
denied_tools:
  - "deleteFiles"
  - "deployProduction"
  - "modifyInfrastructure"
```

**Validation Rules**:
- Must be an array of strings
- Takes precedence over `allowed_tools`
- Tool names should match available tools

#### `approval_required` (Optional)

**Type**: Array of Strings
**Description**: List of tools requiring explicit approval
**Examples**:

```yaml
approval_required:
  - "deployStaging"
  - "deployProduction"
  - "modifyDatabase"
```

**Validation Rules**:
- Must be an array of strings
- Tool names should match available tools
- User must approve before tool execution

#### `version` (Optional)

**Type**: String
**Description**: Semantic version of the chat mode
**Examples**:

```yaml
version: "1.0.0"
version: "2.1.0"
```

**Validation Rules**:
- Should follow semantic versioning
- Optional pre-release and build metadata allowed

---

## Validation

### YAML Syntax

All YAML frontmatter must:
- Start with `---` on the first line
- End with `---` on a line by itself
- Use valid YAML syntax
- Be properly indented (2 spaces)

### Example Validation

**Valid**:
```yaml
---
applyTo: "**/*.py"
tags: ["python"]
description: "Python guidelines"
---
```

**Invalid** (missing closing `---`):
```yaml
---
applyTo: "**/*.py"
tags: ["python"]
description: "Python guidelines"
```

**Invalid** (invalid YAML syntax):
```yaml
---
applyTo: **/*.py
tags: [python]
description: Python guidelines
---
```

---

## Selective Loading Mechanism

### How It Works

1. **File Change Detection**: AI agent detects which files are being edited
2. **Pattern Matching**: Matches file paths against `applyTo` patterns
3. **Instruction Loading**: Loads matching instruction files
4. **Priority Sorting**: Sorts by `priority` field (higher first)
5. **Context Application**: Applies instructions to AI agent context

### Example Flow

```
User edits: src/api/users.py

Pattern matching:
  ✅ python-quality-standards.instructions.md (applyTo: "**/*.py")
  ✅ api-security.instructions.md (applyTo: "src/api/**/*.py")
  ❌ frontend-react.instructions.md (applyTo: "**/*.tsx")

Loaded instructions:
  1. api-security.instructions.md (priority: 8)
  2. python-quality-standards.instructions.md (priority: 5)
```

---

## Best Practices

### Instruction Files

1. **Specific Patterns**: Use specific `applyTo` patterns to avoid over-loading
2. **Relevant Tags**: Use descriptive, relevant tags
3. **Clear Descriptions**: Write clear, concise descriptions
4. **Appropriate Priority**: Set priority based on importance

### Chat Modes

1. **Unique Modes**: Ensure each mode has a unique identifier
2. **Clear Focus**: Define clear cognitive focus areas
3. **Appropriate Security**: Set security level based on operations
4. **Minimal Tools**: Only allow necessary tools

---

## Support

For questions about YAML schema:
- See [examples/](../examples/)
- Check [[TTA/Architecture/INTEGRATION_GUIDE|INTEGRATION_GUIDE.md]]
- Open an [issue](https://github.com/theinterneti/TTA.dev/issues)


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___architecture___docs architecture yaml schema document]]
