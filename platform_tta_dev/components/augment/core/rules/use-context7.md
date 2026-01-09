---
type: "agent_requested"
description: "Use Context7 for fetching up-to-date library documentation and API references"
---

# Use Context7 for Library Documentation Lookup

## Rule Priority
**MEDIUM** - Apply when needing current library documentation, API references, or usage examples

## When to Use Context7 Tools

Prefer Context7's documentation lookup tools for library information:

### 1. Library Documentation Lookup
- **Use**: `resolve-library-id_Context_7`, `get-library-docs_Context_7`
- **When**: Need current, AI-friendly documentation for a library
- **Example**: Looking up FastAPI documentation, React hooks API, LangGraph features

### 2. API Reference Verification
- **Use**: `get-library-docs_Context_7` with specific topic
- **When**: Verifying library features, methods, or API signatures
- **Example**: Checking if a library supports a specific feature, verifying method signatures

### 3. Usage Examples
- **Use**: `get-library-docs_Context_7`
- **When**: Need concrete usage examples for library features
- **Example**: How to use React hooks, FastAPI dependency injection, LangGraph state management

### 4. Version-Specific Documentation
- **Use**: `resolve-library-id_Context_7` with version, `get-library-docs_Context_7`
- **When**: Need documentation for a specific library version
- **Example**: Migrating from React 17 to 18, checking version-specific features

### 5. Framework Migration
- **Use**: `get-library-docs_Context_7` for multiple libraries
- **When**: Comparing libraries or planning migration
- **Example**: Comparing Express vs FastAPI, Vue 2 vs Vue 3

## Benefits

- **Up-to-Date**: Fetches current documentation, not outdated training data
- **AI-Friendly Format**: Returns documentation optimized for AI consumption
- **Focused Retrieval**: Use `topic` parameter to get specific sections
- **Version Support**: Can fetch documentation for specific library versions
- **Token Control**: Adjust `tokens` parameter to control documentation size

## Concrete Examples

### Example 1: Resolve Library ID from Name

```python
# Resolve library name to Context7-compatible ID
resolve-library-id_Context_7(libraryName="fastapi")

# Returns: Library ID like "/tiangolo/fastapi"
# Use this ID in subsequent get-library-docs calls
```

### Example 2: Fetch Library Documentation

```python
# First, resolve library ID
resolve-library-id_Context_7(libraryName="react")

# Then fetch documentation using the resolved ID
get-library-docs_Context_7(
    context7CompatibleLibraryID="/facebook/react",
    tokens=5000  # Default: 5000 tokens
)

# Returns: AI-friendly documentation for React
```

### Example 3: Search Specific Topics

```python
# Fetch documentation focused on specific topic
get-library-docs_Context_7(
    context7CompatibleLibraryID="/facebook/react",
    topic="hooks",  # Focus on React hooks
    tokens=3000
)

# Returns: Documentation focused on React hooks
# More targeted than fetching all documentation
```

### Example 4: Version-Specific Documentation

```python
# Resolve library with specific version
resolve-library-id_Context_7(libraryName="react 18")

# Fetch documentation for specific version
get-library-docs_Context_7(
    context7CompatibleLibraryID="/facebook/react/v18.2.0",
    tokens=5000
)

# Returns: Documentation for React 18.2.0 specifically
```

### Example 5: Compare Library Versions

```python
# Fetch documentation for old version
get-library-docs_Context_7(
    context7CompatibleLibraryID="/facebook/react/v17.0.2",
    topic="hooks",
    tokens=2000
)

# Fetch documentation for new version
get-library-docs_Context_7(
    context7CompatibleLibraryID="/facebook/react/v18.2.0",
    topic="hooks",
    tokens=2000
)

# Compare differences between versions
```

## When NOT to Use Context7 Tools

**Use `view` or `codebase-retrieval` instead when:**

1. **Project-specific documentation** - Need internal docs or README files
   ```
   ❌ Don't: Context7 for project-specific docs
   ✅ Do: view(path="README.md", type="file")
   ```

2. **Internal APIs** - Need documentation for internal code
   ```
   ❌ Don't: Context7 for internal APIs
   ✅ Do: Use Serena tools to navigate internal code
   ```

3. **Offline work** - No internet connection available
   ```
   ❌ Don't: Context7 requires network access
   ✅ Do: Use cached documentation or local files
   ```

4. **Custom libraries** - Library not in Context7 database
   ```
   ❌ Don't: Context7 for custom/private libraries
   ✅ Do: Read library source code with Serena or view
   ```

**Use `web-fetch` instead when:**

1. **Official docs directly** - Need to read official documentation website
   ```
   ❌ Don't: Context7 if you need exact official docs format
   ✅ Do: web-fetch(url="https://docs.library.com")
   ```

## Tool Selection Guide

### Decision Tree: Context7 vs web-fetch vs codebase-retrieval

```
Need library documentation?
├─ Public library (npm, PyPI, etc.)?
│  ├─ Yes → Use Context7
│  │   ├─ Current, AI-friendly format
│  │   ├─ Focused topic retrieval
│  │   └─ Version-specific docs
│  └─ No → Use codebase-retrieval or view
│      ├─ Internal/custom library
│      ├─ Project-specific docs
│      └─ Local README files
│
Need API reference?
├─ Public library → Use Context7
│   ├─ Verify method signatures
│   ├─ Check feature availability
│   └─ Get usage examples
│
Need usage examples?
├─ Public library → Use Context7
│   ├─ Concrete code examples
│   ├─ Best practices
│   └─ Common patterns
│
Need version-specific info?
├─ Public library → Use Context7
│   ├─ Migration guides
│   ├─ Version differences
│   └─ Deprecated features
│
Need official docs format?
├─ Yes → Use web-fetch
└─ No → Use Context7 (AI-friendly)
```

### When to Combine Tools

**Pattern 1: Resolve then Fetch**
```
1. resolve-library-id_Context_7(libraryName="fastapi")
2. get-library-docs_Context_7(context7CompatibleLibraryID="/tiangolo/fastapi")
```

**Pattern 2: Focused Retrieval**
```
1. resolve-library-id_Context_7(libraryName="react")
2. get-library-docs_Context_7(context7CompatibleLibraryID="/facebook/react", topic="hooks", tokens=3000)
3. get-library-docs_Context_7(context7CompatibleLibraryID="/facebook/react", topic="routing", tokens=3000)
```

**Pattern 3: Version Comparison**
```
1. resolve-library-id_Context_7(libraryName="react 17")
2. get-library-docs_Context_7(context7CompatibleLibraryID="/facebook/react/v17.0.2", topic="hooks")
3. resolve-library-id_Context_7(libraryName="react 18")
4. get-library-docs_Context_7(context7CompatibleLibraryID="/facebook/react/v18.2.0", topic="hooks")
5. Compare differences
```

## Default Workflow

1. **Always resolve library ID first**: Call `resolve-library-id_Context_7` before `get-library-docs_Context_7`
2. **Use topic parameter**: Focus on specific sections to reduce token usage
3. **Adjust tokens**: Start with default 5000, reduce if too much content
4. **Cache results**: Store frequently-used documentation in memories
5. **Verify version**: Check library version matches project requirements

## Performance Considerations

### Token Management

**Control documentation size:**
```python
# ✅ Good: Use topic to focus retrieval
get-library-docs_Context_7(
    context7CompatibleLibraryID="/facebook/react",
    topic="hooks",
    tokens=3000  # Reduced from default 5000
)

# ❌ Avoid: Fetching all docs when only need specific section
get-library-docs_Context_7(
    context7CompatibleLibraryID="/facebook/react",
    tokens=10000  # Too much, slow and expensive
)
```

### Library ID Resolution

**Resolve once, use multiple times:**
```python
# ✅ Good: Resolve once
library_id = resolve-library-id_Context_7(libraryName="fastapi")
# Use library_id multiple times
get-library-docs_Context_7(context7CompatibleLibraryID=library_id, topic="routing")
get-library-docs_Context_7(context7CompatibleLibraryID=library_id, topic="dependencies")

# ❌ Avoid: Resolving repeatedly
resolve-library-id_Context_7(libraryName="fastapi")
get-library-docs_Context_7(...)
resolve-library-id_Context_7(libraryName="fastapi")  # Redundant
get-library-docs_Context_7(...)
```

### Network Efficiency

**Batch related queries:**
```python
# ✅ Good: Fetch related topics in sequence
get-library-docs_Context_7(context7CompatibleLibraryID="/facebook/react", topic="hooks")
get-library-docs_Context_7(context7CompatibleLibraryID="/facebook/react", topic="context")
get-library-docs_Context_7(context7CompatibleLibraryID="/facebook/react", topic="effects")

# ❌ Avoid: Interleaving unrelated queries
get-library-docs_Context_7(context7CompatibleLibraryID="/facebook/react", topic="hooks")
get-library-docs_Context_7(context7CompatibleLibraryID="/tiangolo/fastapi", topic="routing")
get-library-docs_Context_7(context7CompatibleLibraryID="/facebook/react", topic="context")
```

## TTA-Specific Use Cases

### Look Up FastAPI Documentation

```python
# Resolve FastAPI library ID
resolve-library-id_Context_7(libraryName="fastapi")

# Fetch dependency injection documentation
get-library-docs_Context_7(
    context7CompatibleLibraryID="/tiangolo/fastapi",
    topic="dependency injection",
    tokens=3000
)
```

### Verify LangGraph Features

```python
# Resolve LangGraph library ID
resolve-library-id_Context_7(libraryName="langgraph")

# Fetch state management documentation
get-library-docs_Context_7(
    context7CompatibleLibraryID="/langchain-ai/langgraph",
    topic="state management",
    tokens=4000
)
```

### Check Redis/Neo4j API References

```python
# Resolve Redis library ID
resolve-library-id_Context_7(libraryName="redis-py")

# Fetch Redis client documentation
get-library-docs_Context_7(
    context7CompatibleLibraryID="/redis/redis-py",
    topic="client",
    tokens=3000
)
```

## Troubleshooting

### Library Not Found

**Symptom:** `resolve-library-id_Context_7` returns no results

**Solutions:**
1. Try alternative library names (e.g., "react" vs "reactjs")
2. Check spelling and capitalization
3. Try package manager name (e.g., "redis-py" instead of "redis")
4. Search for organization/author name (e.g., "facebook/react")
5. Use web-fetch to get official docs if library not in Context7

### Documentation Incomplete

**Symptom:** Retrieved documentation is missing expected content

**Solutions:**
1. Try different `topic` parameter to focus on specific section
2. Increase `tokens` parameter to get more content
3. Use web-fetch to get official documentation
4. Check if library version is correct
5. Verify library is well-documented (some libraries have sparse docs)

### Version Mismatch

**Symptom:** Documentation doesn't match installed library version

**Solutions:**
1. Specify exact version in `resolve-library-id_Context_7` (e.g., "react 18.2.0")
2. Check project's package.json/requirements.txt for installed version
3. Fetch documentation for multiple versions to compare
4. Use `uvx` to check installed version: `uvx pip show <package>`

### Token Limit Exceeded

**Symptom:** Documentation is truncated or incomplete

**Solutions:**
1. Use `topic` parameter to focus on specific section
2. Reduce `tokens` parameter and make multiple focused queries
3. Split documentation retrieval into multiple calls
4. Cache frequently-used documentation in memories

### Network Errors

**Symptom:** Context7 calls fail with network errors

**Solutions:**
1. Check internet connection
2. Retry with exponential backoff
3. Use cached documentation if available
4. Fall back to web-fetch or local documentation
5. Check if Context7 service is available

## Integration with Other Rules

### MCP Tool Selection
- **Primary:** Use Context7 for public library documentation (see `Use-your-tools.md`)
- **Complement:** Use web-fetch for official docs, codebase-retrieval for internal docs
- **Fallback:** Use view or Serena for local documentation

### Development Workflows
- **Library Research:** Use Context7 before implementing features with new libraries
- **Migration Planning:** Compare library versions with Context7
- **API Verification:** Verify library features before using them

### Tool Execution
- **Package Installation:** Use `prefer-uvx-for-tools.md` to install libraries after researching with Context7
- **Version Pinning:** Use Context7 to verify version compatibility before pinning

## Related Documentation

- **MCP Tool Selection:** `Use-your-tools.md` - When to use Context7 vs other MCP tools
- **Tool Execution:** `prefer-uvx-for-tools.md` - Installing libraries with uvx
- **System Prompt:** Context7 tool signatures and parameters

## Summary

**Primary use:** Fetch current, AI-friendly documentation for public libraries

**Key tools:** `resolve-library-id_Context_7`, `get-library-docs_Context_7`

**When to use:** Public library documentation, API references, usage examples, version-specific docs

**When NOT to use:** Project-specific docs (use view), internal APIs (use Serena), offline work (use cached docs)

---

**Status:** Active
**Last Updated:** 2025-10-22
**Related Rules:** `Use-your-tools.md`, `prefer-uvx-for-tools.md`


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Rules/Use-context7]]
