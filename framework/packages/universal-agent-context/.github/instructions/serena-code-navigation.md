---
applyTo:
  - "src/**/*.py"
  - "tests/**/*.py"
  - "**/*.ts"
  - "**/*.js"
tags: ['general']
description: "Serena MCP tool usage for semantic code operations - prefer over text-based tools"
priority: 8
auto_trigger: "true"
applies_to: "["code navigation", "refactoring", "symbol search", "code analysis", "serena", "find symbol", "code editing"]"
category: "tooling"
---

# Serena Code Navigation: Semantic Code Operations

**Auto-triggered when**: Working with code navigation, refactoring, symbol search, or code analysis.

## Quick Reference

**Default recommendation:** Use Serena for semantic code operations (finding symbols, refactoring, analysis)
**Alternative:** Use `view` for simple file reading, `codebase-retrieval` for high-level search
**Best practice:** Use `get_symbols_overview_Serena` before reading full files

## When to Use Serena Tools

Prefer Serena's semantic tools over basic text operations for:

### 1. Finding Code Symbols
- **Use**: `find_symbol_Serena` instead of grep/search
- **When**: Looking for classes, functions, methods by name
- **Example**: Finding all classes named "Agent" or methods containing "workflow"

### 2. Understanding File Structure
- **Use**: `get_symbols_overview_Serena` before reading full files
- **When**: Need to understand what's in a file without reading all content
- **Example**: "What classes/functions are in this module?"

### 3. Finding References
- **Use**: `find_referencing_symbols_Serena`
- **When**: Need to see where a symbol is used across the codebase
- **Example**: Before refactoring, find all callers of a function

### 4. Code Pattern Search
- **Use**: `search_for_pattern_Serena` for regex-based searches
- **When**: Looking for specific code patterns across files
- **Example**: Find all pytest decorators, async functions, TODO comments

### 5. Precise Code Editing
- **Use**: `replace_symbol_body_Serena`, `insert_after_symbol_Serena`, `insert_before_symbol_Serena`
- **When**: Making surgical changes to functions/classes
- **Example**: Updating a method implementation while preserving structure

### 6. Project Knowledge
- **Use**: `write_memory_Serena`, `read_memory_Serena`, `list_memories_Serena`
- **When**: Storing/retrieving architecture decisions, patterns, conventions
- **Example**: Document component maturity criteria, testing strategies

## Benefits

- **Semantic Understanding**: Works with code structure, not just text
- **Language-Aware**: Understands Python/TypeScript/JavaScript syntax
- **Precise**: Symbol-level operations prevent breaking changes
- **Persistent**: Memory system maintains context across sessions

## Quick Examples

### Finding Code Symbols
```python
# Find all classes named "Agent"
find_symbol_Serena(
    name_path="Agent",
    substring_matching=True,
    include_kinds=[5]  # 5 = Class
)

# Find specific method in a class
find_symbol_Serena(
    name_path="/AgentOrchestrator/execute_workflow",
    relative_path="src/agent_orchestration"
)
```

### Understanding File Structure
```python
# Get overview before reading full file
get_symbols_overview_Serena(
    relative_path="src/agent_orchestration/service.py"
)
```

### Finding References
```python
# Before refactoring, find all callers
find_referencing_symbols_Serena(
    name_path="execute_workflow",
    relative_path="src/agent_orchestration/service.py"
)
```

### Precise Code Editing
```python
# Replace method implementation
replace_symbol_body_Serena(
    name_path="/AgentOrchestrator/execute_workflow",
    relative_path="src/agent_orchestration/service.py",
    body="""async def execute_workflow(self, workflow_id: str) -> dict:
    \"\"\"Execute workflow with enhanced error handling.\"\"\"
    try:
        result = await self._execute_internal(workflow_id)
        return result
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        raise"""
)
```

## When NOT to Use Serena

**Use `view` or `str-replace-editor` instead when:**
1. **Simple file reading** - Just need to see file contents
2. **Text-based search** - Looking for specific string, not code symbol
3. **Line-based editing** - Simple text replacement
4. **Non-code files** - Configuration, documentation, data files

**Use `codebase-retrieval` instead when:**
1. **High-level search** - Don't know which files contain the code
2. **Conceptual search** - Looking for patterns, not specific symbols
3. **Cross-cutting concerns** - Features spanning multiple files

## Tool Selection Guide

```
Need to work with code?
├─ Know the file location?
│  ├─ Yes → Know the symbol name?
│  │  ├─ Yes → Use Serena (find_symbol, replace_symbol_body)
│  │  └─ No → Use Serena (get_symbols_overview) then drill down
│  └─ No → Use codebase-retrieval to find files, then Serena

Need to read file contents?
├─ Code file with semantic operations?
│  ├─ Yes → Use Serena (get_symbols_overview)
│  └─ No → Use view

Need to search for text?
├─ Code symbol (class, function, method)?
│  ├─ Yes → Use Serena (find_symbol, search_for_pattern)
│  └─ No → Use view with search_query_regex

Need to edit code?
├─ Symbol-level change (method, class)?
│  ├─ Yes → Use Serena (replace_symbol_body, insert_after_symbol)
│  └─ No → Use str-replace-editor
```

## Common Patterns

### Pattern 1: High-level search → Semantic navigation
```
1. codebase-retrieval("Where is workflow execution?")
2. get_symbols_overview_Serena("src/agent_orchestration/service.py")
3. find_symbol_Serena(name_path="execute_workflow", ...)
```

### Pattern 2: Overview → Detailed reading
```
1. get_symbols_overview_Serena("src/components/gameplay_loop/base.py")
2. view("src/components/gameplay_loop/base.py", view_range=[100, 200])
```

### Pattern 3: Find → Refactor → Verify
```
1. find_referencing_symbols_Serena(name_path="old_method", ...)
2. replace_symbol_body_Serena(name_path="old_method", ...)
3. find_referencing_symbols_Serena(name_path="old_method", ...)  # Verify
```

## Default Workflow

1. **Before reading files**: Use `get_symbols_overview_Serena` to understand structure
2. **Before refactoring**: Use `find_referencing_symbols_Serena` to check impact
3. **When searching**: Use `find_symbol_Serena` or `search_for_pattern_Serena` instead of grep
4. **When editing**: Use `replace_symbol_body_Serena` for precise changes
5. **For context**: Check `list_memories_Serena` for existing project knowledge

## Performance Tips

1. **Use `relative_path` parameter** to restrict search scope
2. **Use `include_kinds` parameter** to filter by symbol type
3. **Check memories first** before searching entire codebase
4. **Use `get_symbols_overview_Serena`** before reading full files

## LSP Symbol Kinds Reference

- `5` = Class
- `6` = Method
- `12` = Function
- `13` = Variable
- `14` = Constant

---

**Last Updated**: 2025-10-27
**Status**: Active - Universal AI agent guidance for Serena MCP tools
