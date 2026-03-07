---
type: "agent_requested"
description: "Use Redis for key-value storage, caching, vector search, and pub/sub messaging"
---

# Use Redis for Database Operations and Caching

## Rule Priority
**MEDIUM** - Apply when working with caching, key-value storage, vector search, or pub/sub messaging

## When to Use Redis Tools

Prefer Redis tools for fast data operations:

### 1. Key-Value Storage
- **Use**: `set_Redis`, `get_Redis`, `delete_Redis`
- **When**: Storing and retrieving simple key-value data
- **Example**: Caching API responses, storing user sessions, temporary data

### 2. Hash Operations
- **Use**: `hset_Redis`, `hget_Redis`, `hgetall_Redis`, `hdel_Redis`
- **When**: Managing structured data with multiple fields
- **Example**: User profiles, configuration settings, structured cache entries

### 3. JSON Storage
- **Use**: `json_set_Redis`, `json_get_Redis`, `json_del_Redis`
- **When**: Storing and querying JSON documents
- **Example**: Complex data structures, nested objects, API responses

### 4. List Operations
- **Use**: `lpush_Redis`, `rpush_Redis`, `lpop_Redis`, `rpop_Redis`, `lrange_Redis`
- **When**: Managing ordered collections, queues, stacks
- **Example**: Task queues, message buffers, activity logs

### 5. Vector Search
- **Use**: `create_vector_index_hash_Redis`, `set_vector_in_hash_Redis`, `vector_search_hash_Redis`
- **When**: Performing similarity search on embeddings
- **Example**: Semantic search, recommendation systems, similar content discovery

### 6. Pub/Sub Messaging
- **Use**: `publish_Redis`, `subscribe_Redis`, `unsubscribe_Redis`
- **When**: Real-time messaging between components
- **Example**: Event notifications, real-time updates, message broadcasting

## Benefits

- **High Performance**: In-memory storage provides sub-millisecond latency
- **Rich Data Structures**: Supports strings, hashes, lists, sets, sorted sets, streams, JSON
- **Vector Search**: Built-in vector similarity search with HNSW algorithm
- **Pub/Sub**: Real-time messaging without external message broker
- **Expiration Support**: Automatic key expiration with TTL

## Concrete Examples

### Example 1: Store and Retrieve Hash Data

```python
# Store user profile in hash
hset_Redis(
    name="user:12345",
    key="name",
    value="John Doe",
    expire_seconds=3600  # 1 hour TTL
)

hset_Redis(
    name="user:12345",
    key="email",
    value="john@example.com"
)

# Retrieve single field
hget_Redis(name="user:12345", key="name")

# Retrieve all fields
hgetall_Redis(name="user:12345")

# Delete field
hdel_Redis(name="user:12345", key="email")
```

### Example 2: Store and Query JSON Documents

```python
# Store JSON document
json_set_Redis(
    name="narrative:scene:1",
    path="$",
    value={
        "id": 1,
        "title": "Opening Scene",
        "content": "The story begins...",
        "choices": [
            {"id": 1, "text": "Go left"},
            {"id": 2, "text": "Go right"}
        ]
    },
    expire_seconds=7200  # 2 hours
)

# Get entire document
json_get_Redis(name="narrative:scene:1", path="$")

# Get specific field
json_get_Redis(name="narrative:scene:1", path="$.title")

# Get nested array
json_get_Redis(name="narrative:scene:1", path="$.choices")

# Delete specific field
json_del_Redis(name="narrative:scene:1", path="$.choices[0]")
```

### Example 3: Manage Lists (Queues and Stacks)

```python
# Push to list (queue - FIFO)
rpush_Redis(name="task:queue", value="task1", expire=3600)
rpush_Redis(name="task:queue", value="task2")
rpush_Redis(name="task:queue", value="task3")

# Pop from list (FIFO)
lpop_Redis(name="task:queue")  # Returns "task1"

# Push to list (stack - LIFO)
lpush_Redis(name="task:stack", value="task1")
lpush_Redis(name="task:stack", value="task2")

# Pop from list (LIFO)
lpop_Redis(name="task:stack")  # Returns "task2"

# Get range of items
lrange_Redis(name="task:queue", start=0, stop=-1)  # All items

# Get list length
llen_Redis(name="task:queue")
```

### Example 4: Create Vector Index and Perform Similarity Search

```python
# Create vector index for embeddings (1536 dimensions for OpenAI)
create_vector_index_hash_Redis(
    index_name="narrative_embeddings",
    prefix="narrative:",
    vector_field="embedding",
    dim=1536,
    distance_metric="COSINE"
)

# Store vector in hash
set_vector_in_hash_Redis(
    name="narrative:scene:1",
    vector_field="embedding",
    vector=[0.1, 0.2, 0.3, ...]  # 1536-dimensional vector
)

# Perform similarity search
vector_search_hash_Redis(
    query_vector=[0.1, 0.2, 0.3, ...],  # Query embedding
    index_name="narrative_embeddings",
    vector_field="embedding",
    k=5,  # Top 5 results
    return_fields=["title", "content"]
)
```

### Example 5: Publish and Subscribe to Channels

```python
# Subscribe to channel
subscribe_Redis(channel="narrative:updates")

# Publish message to channel
publish_Redis(
    channel="narrative:updates",
    message="New scene available: scene:42"
)

# Unsubscribe from channel
unsubscribe_Redis(channel="narrative:updates")
```

## When NOT to Use Redis Tools

**Use PostgreSQL or other relational DB instead when:**

1. **Complex queries** - Need JOINs, aggregations, complex filtering
   ```
   ❌ Don't: Redis for complex relational queries
   ✅ Do: Use PostgreSQL for relational data
   ```

2. **ACID transactions** - Need strong consistency guarantees
   ```
   ❌ Don't: Redis for financial transactions
   ✅ Do: Use PostgreSQL for ACID compliance
   ```

3. **Large datasets** - Data exceeds available memory
   ```
   ❌ Don't: Redis for multi-GB datasets
   ✅ Do: Use disk-based database (PostgreSQL, MongoDB)
   ```

4. **Persistent storage** - Data must survive server restarts
   ```
   ❌ Don't: Redis as primary persistent storage
   ✅ Do: Use PostgreSQL with Redis as cache layer
   ```

**Use Neo4j instead when:**

1. **Graph queries** - Need relationship traversal, pattern matching
   ```
   ❌ Don't: Redis for graph queries
   ✅ Do: Use Neo4j for graph data
   ```

## Tool Selection Guide

### Decision Tree: Redis vs PostgreSQL vs Neo4j

```
Need to store data?
├─ Simple key-value or cache? → Use Redis
│   ├─ Session data
│   ├─ API response cache
│   └─ Temporary data
│
├─ Structured data with relationships? → Use PostgreSQL
│   ├─ User accounts
│   ├─ Transactional data
│   └─ Complex queries
│
├─ Graph data with relationships? → Use Neo4j
│   ├─ Social networks
│   ├─ Knowledge graphs
│   └─ Recommendation systems
│
Need vector search?
├─ Yes → Use Redis vector search
│   ├─ Semantic search
│   ├─ Similarity matching
│   └─ Recommendation
│
Need real-time messaging?
├─ Yes → Use Redis pub/sub
│   ├─ Event notifications
│   ├─ Real-time updates
│   └─ Message broadcasting
│
Need high performance?
├─ Yes → Use Redis (in-memory)
└─ No → Use PostgreSQL (disk-based)
```

## Default Workflow

1. **Always set expiration**: Use `expire_seconds` parameter to prevent memory leaks
2. **Use appropriate data structure**: Choose hash, JSON, list, set based on use case
3. **Monitor memory usage**: Check `info_Redis(section="memory")` regularly
4. **Use indexes for vector search**: Create index before performing similarity search
5. **Scan instead of KEYS**: Use `scan_keys_Redis` or `scan_all_keys_Redis` for production

## Performance Considerations

### Memory Management

**Set expiration to prevent memory leaks:**
```python
# ✅ Good: Set expiration
hset_Redis(
    name="cache:api:response",
    key="data",
    value="...",
    expire_seconds=3600  # 1 hour
)

# ❌ Avoid: No expiration
hset_Redis(
    name="cache:api:response",
    key="data",
    value="..."  # No expiration, memory leak risk
)
```

### Key Scanning

**Use SCAN instead of KEYS for production:**
```python
# ✅ Good: Use scan_keys_Redis (non-blocking)
scan_keys_Redis(pattern="user:*", count=100)

# ✅ Good: Use scan_all_keys_Redis for all matching keys
scan_all_keys_Redis(pattern="user:*", batch_size=100)

# ❌ Avoid: KEYS command blocks Redis
# (No direct KEYS command available, but avoid patterns that scan all keys)
```

### Vector Search Optimization

**Create index before searching:**
```python
# ✅ Good: Create index first
create_vector_index_hash_Redis(
    index_name="embeddings",
    prefix="doc:",
    vector_field="embedding",
    dim=1536
)
set_vector_in_hash_Redis(name="doc:1", vector=[...])
vector_search_hash_Redis(query_vector=[...], index_name="embeddings")

# ❌ Avoid: Search without index
# (Will fail - index required for vector search)
```

### Connection Management

**Monitor connections:**
```python
# Check connected clients
client_list_Redis()

# Get server info
info_Redis(section="clients")

# Get database size
dbsize_Redis()
```

## TTA-Specific Use Cases

### Cache Narrative State

```python
# Store narrative state in JSON
json_set_Redis(
    name="narrative:state:user:12345",
    path="$",
    value={
        "current_scene": 42,
        "choices_made": [1, 3, 7],
        "inventory": ["key", "map"],
        "timestamp": "2025-10-22T10:30:00Z"
    },
    expire_seconds=86400  # 24 hours
)

# Retrieve narrative state
json_get_Redis(name="narrative:state:user:12345", path="$")
```

### Store User Preferences

```python
# Store user preferences in hash
hset_Redis(
    name="user:prefs:12345",
    key="theme",
    value="dark",
    expire_seconds=2592000  # 30 days
)

hset_Redis(name="user:prefs:12345", key="language", value="en")
hset_Redis(name="user:prefs:12345", key="notifications", value="true")

# Get all preferences
hgetall_Redis(name="user:prefs:12345")
```

### Vector Search for Similar Narratives

```python
# Create index for narrative embeddings
create_vector_index_hash_Redis(
    index_name="narrative_similarity",
    prefix="narrative:embedding:",
    vector_field="vector",
    dim=1536,
    distance_metric="COSINE"
)

# Store narrative embedding
set_vector_in_hash_Redis(
    name="narrative:embedding:scene:42",
    vector_field="vector",
    vector=[0.1, 0.2, ...]  # Scene embedding
)

# Find similar narratives
vector_search_hash_Redis(
    query_vector=[0.1, 0.2, ...],  # Current scene embedding
    index_name="narrative_similarity",
    k=5,  # Top 5 similar scenes
    return_fields=["scene_id", "title"]
)
```

### Pub/Sub for Real-Time Updates

```python
# Subscribe to narrative updates
subscribe_Redis(channel="narrative:events")

# Publish scene change event
publish_Redis(
    channel="narrative:events",
    message="scene_changed:42"
)

# Publish choice made event
publish_Redis(
    channel="narrative:events",
    message="choice_made:user:12345:choice:7"
)
```

## Troubleshooting

### Connection Errors

**Symptom:** Redis operations fail with connection errors

**Solutions:**
1. Verify Redis server is running
2. Check Redis connection settings (host, port)
3. Verify network connectivity
4. Check Redis authentication (if enabled)
5. Review Redis logs for errors

### Key Not Found

**Symptom:** `get_Redis` or `hget_Redis` returns None

**Solutions:**
1. Verify key exists with `type_Redis(key)`
2. Check if key expired (TTL elapsed)
3. Verify key name is correct (case-sensitive)
4. Use `scan_keys_Redis` to find similar keys
5. Check if key was deleted

### Type Mismatch

**Symptom:** Operations fail with "WRONGTYPE" error

**Solutions:**
1. Check key type with `type_Redis(key)`
2. Use correct operation for key type (hash vs string vs list)
3. Delete key and recreate with correct type
4. Use different key name for different data structure

### Memory Issues

**Symptom:** Redis runs out of memory or evicts keys

**Solutions:**
1. Monitor memory usage with `info_Redis(section="memory")`
2. Set expiration on all keys to prevent memory leaks
3. Use `scan_all_keys_Redis` to find keys without expiration
4. Increase Redis max memory limit
5. Enable eviction policy (e.g., allkeys-lru)

### Index Errors

**Symptom:** Vector search fails with index errors

**Solutions:**
1. Verify index exists with `get_indexes_Redis()`
2. Check index info with `get_index_info_Redis(index_name)`
3. Verify vector dimensions match index configuration
4. Recreate index if corrupted
5. Check indexed keys count with `get_indexed_keys_number_Redis(index_name)`

## Integration with Other Rules

### MCP Tool Selection
- **Primary:** Use Redis for caching and fast data operations (see `Use-your-tools.md`)
- **Complement:** Use PostgreSQL for relational data, Neo4j for graph data
- **Fallback:** Use file system for persistent storage

### Development Workflows
- **Caching:** Use Redis to cache API responses, database queries
- **State Management:** Store application state in Redis
- **Vector Search:** Implement semantic search with Redis vector search

### AI Context Management
- **Session Storage:** Store AI context sessions in Redis (see `ai-context-management.md`)
- **Temporary Data:** Use Redis for temporary data with expiration

### Additional Redis Operations

#### Set Operations

**Managing unique collections:**
```python
# Add members to set
sadd_Redis(name="tags:scene:42", value="action", expire_seconds=3600)
sadd_Redis(name="tags:scene:42", value="adventure")
sadd_Redis(name="tags:scene:42", value="combat")

# Get all members
smembers_Redis(name="tags:scene:42")

# Remove member
srem_Redis(name="tags:scene:42", value="combat")
```

#### Sorted Set Operations

**Managing ranked collections:**
```python
# Add members with scores
zadd_Redis(key="leaderboard", score=100, member="player1", expiration=86400)
zadd_Redis(key="leaderboard", score=95, member="player2")
zadd_Redis(key="leaderboard", score=110, member="player3")

# Get range by rank
zrange_Redis(key="leaderboard", start=0, end=2, with_scores=True)  # Top 3

# Remove member
zrem_Redis(key="leaderboard", member="player2")
```

#### Stream Operations

**Managing event streams:**
```python
# Add entry to stream
xadd_Redis(
    key="events:narrative",
    fields={
        "event_type": "scene_change",
        "scene_id": "42",
        "user_id": "12345",
        "timestamp": "2025-10-22T10:30:00Z"
    },
    expiration=86400
)

# Read entries from stream
xrange_Redis(key="events:narrative", count=10)

# Delete entry
xdel_Redis(key="events:narrative", entry_id="1634567890-0")
```

#### Key Management

**Managing keys and expiration:**
```python
# Set expiration on existing key
expire_Redis(name="cache:data", expire_seconds=3600)

# Rename key
rename_Redis(old_key="old:name", new_key="new:name")

# Delete key
delete_Redis(key="temp:data")

# Check key type
type_Redis(key="user:12345")  # Returns: "hash", "string", "list", etc.
```

## Related Documentation

- **MCP Tool Selection:** `Use-your-tools.md` - When to use Redis vs other MCP tools
- **System Prompt:** Redis tool signatures and parameters (40+ tools)
- **Redis Documentation:** https://redis.io/docs/
- **Redis Commands:** https://redis.io/commands/

## Summary

**Primary use:** Key-value storage, caching, vector search, pub/sub messaging, real-time data

**Key data structures:** Strings, Hashes, JSON, Lists, Sets, Sorted Sets, Streams

**Key tools:**
- **Hash:** `hset_Redis`, `hget_Redis`, `hgetall_Redis`, `hdel_Redis`
- **JSON:** `json_set_Redis`, `json_get_Redis`, `json_del_Redis`
- **List:** `lpush_Redis`, `rpush_Redis`, `lpop_Redis`, `rpop_Redis`, `lrange_Redis`
- **Set:** `sadd_Redis`, `srem_Redis`, `smembers_Redis`
- **Sorted Set:** `zadd_Redis`, `zrange_Redis`, `zrem_Redis`
- **Stream:** `xadd_Redis`, `xrange_Redis`, `xdel_Redis`
- **Vector:** `create_vector_index_hash_Redis`, `set_vector_in_hash_Redis`, `vector_search_hash_Redis`
- **Pub/Sub:** `publish_Redis`, `subscribe_Redis`, `unsubscribe_Redis`
- **Key Management:** `set_Redis`, `get_Redis`, `delete_Redis`, `expire_Redis`, `rename_Redis`, `scan_keys_Redis`

**When to use:** Caching, session storage, temporary data, vector search, real-time messaging, queues, leaderboards, event streams

**When NOT to use:** Complex queries (use PostgreSQL), graph data (use Neo4j), large datasets exceeding memory (use disk-based DB), ACID transactions (use PostgreSQL)

---

**Status:** Active
**Last Updated:** 2025-10-22
**Related Rules:** `Use-your-tools.md`, `ai-context-management.md`


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Rules/Use-redis]]
