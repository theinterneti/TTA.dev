---
applyTo:
  - "src/agent_orchestration/**"
  - "src/components/gameplay_loop/**"
  - "src/living_worlds/**"
  - "tests/integration/**"
tags: ['general']
description: "Guidance for TTA's agent orchestration layer using LangGraph and Neo4j. Applies to neo4j, graph database, cypher, langgraph, agent orchestration, and narrative graph code."
priority: 8
category: "architecture"
---

# Agent Orchestration and Graph Database Instructions

This file contains guidance specific to TTA's agent orchestration layer, advising on query optimization and state management patterns.

## LangGraph Agent Orchestration

### Agent State Management
```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated

class AgentState(TypedDict):
    """State shared across agent nodes"""
    user_input: str
    narrative_context: dict
    world_state: dict
    agent_responses: list[str]
    current_agent: str

# Define agent graph
workflow = StateGraph(AgentState)

# Add agent nodes
workflow.add_node("input_processor", process_input_agent)
workflow.add_node("world_builder", world_building_agent)
workflow.add_node("narrative_generator", narrative_generation_agent)

# Define edges
workflow.add_edge("input_processor", "world_builder")
workflow.add_edge("world_builder", "narrative_generator")
workflow.add_edge("narrative_generator", END)

# Set entry point
workflow.set_entry_point("input_processor")
```

### Circuit Breaker Integration
```python
from src.agent_orchestration.circuit_breaker import CircuitBreaker

# Wrap agent calls with circuit breaker
async def call_agent_with_protection(agent_func, *args, **kwargs):
    circuit_breaker = CircuitBreaker(
        name=f"agent_{agent_func.__name__}",
        failure_threshold=5,
        recovery_timeout=60
    )

    try:
        return await circuit_breaker.call(agent_func, *args, **kwargs)
    except CircuitBreakerOpenError:
        # Use fallback agent or cached response
        return await fallback_agent(*args, **kwargs)
```

### Message Coordination
```python
from src.agent_orchestration.messaging import RedisMessageCoordinator

# Initialize message coordinator
coordinator = RedisMessageCoordinator(redis_client)

# Send message to agent
await coordinator.send_message(
    queue="narrative_generation",
    message={
        "user_input": user_input,
        "context": narrative_context
    },
    ttl=300  # 5 minutes
)

# Receive message from agent
message = await coordinator.receive_message(
    queue="narrative_generation",
    timeout=30
)
```

## Neo4j Graph Database Patterns

### Query Optimization

#### Use Parameterized Queries
```python
# GOOD: Parameterized query
query = """
MATCH (p:Player {id: $player_id})-[:IN_WORLD]->(w:World)
RETURN w
"""
result = await session.run(query, player_id=player_id)

# BAD: String interpolation (SQL injection risk)
query = f"MATCH (p:Player {{id: '{player_id}'}})-[:IN_WORLD]->(w:World) RETURN w"
```

#### Use Indexes for Performance
```python
# Create indexes for frequently queried properties
CREATE INDEX player_id_index FOR (p:Player) ON (p.id)
CREATE INDEX world_name_index FOR (w:World) ON (w.name)
CREATE INDEX narrative_timestamp_index FOR (n:Narrative) ON (n.timestamp)
```

#### Limit Result Sets
```python
# Always use LIMIT for potentially large result sets
query = """
MATCH (p:Player {id: $player_id})-[:EXPERIENCED]->(n:Narrative)
RETURN n
ORDER BY n.timestamp DESC
LIMIT 100
"""
```

### State Management Patterns

#### Player State
```python
# Store player state in Neo4j
async def update_player_state(player_id: str, state: dict):
    query = """
    MATCH (p:Player {id: $player_id})
    SET p.state = $state,
        p.updated_at = datetime()
    RETURN p
    """
    await session.run(query, player_id=player_id, state=state)
```

#### World State
```python
# Store world state with relationships
async def update_world_state(world_id: str, state: dict):
    query = """
    MATCH (w:World {id: $world_id})
    SET w.state = $state,
        w.updated_at = datetime()
    WITH w
    MATCH (w)-[:CONTAINS]->(l:Location)
    SET l.state = $state.locations[l.id]
    RETURN w, collect(l) as locations
    """
    await session.run(query, world_id=world_id, state=state)
```

#### Narrative History
```python
# Store narrative history as graph
async def add_narrative_event(player_id: str, event: dict):
    query = """
    MATCH (p:Player {id: $player_id})
    CREATE (n:Narrative {
        id: randomUUID(),
        content: $event.content,
        timestamp: datetime(),
        type: $event.type
    })
    CREATE (p)-[:EXPERIENCED]->(n)
    RETURN n
    """
    await session.run(query, player_id=player_id, event=event)
```

### Transaction Management

#### Use Transactions for Consistency
```python
async def create_player_with_world(player_data: dict, world_data: dict):
    async with driver.session() as session:
        async with session.begin_transaction() as tx:
            # Create player
            player_query = """
            CREATE (p:Player {
                id: $id,
                name: $name,
                created_at: datetime()
            })
            RETURN p
            """
            await tx.run(player_query, **player_data)

            # Create world
            world_query = """
            CREATE (w:World {
                id: $id,
                name: $name,
                created_at: datetime()
            })
            RETURN w
            """
            await tx.run(world_query, **world_data)

            # Create relationship
            rel_query = """
            MATCH (p:Player {id: $player_id})
            MATCH (w:World {id: $world_id})
            CREATE (p)-[:IN_WORLD]->(w)
            """
            await tx.run(rel_query,
                        player_id=player_data['id'],
                        world_id=world_data['id'])

            await tx.commit()
```

### Connection Pooling

#### Configure Connection Pool
```python
from neo4j import AsyncGraphDatabase

# Configure connection pool
driver = AsyncGraphDatabase.driver(
    uri=NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD),
    max_connection_pool_size=50,
    connection_acquisition_timeout=60,
    max_transaction_retry_time=30
)
```

#### Handle Connection Failures
```python
from src.common.error_recovery import retry_with_backoff, RetryConfig

@retry_with_backoff(RetryConfig(max_retries=3, base_delay=1.0))
async def execute_query_with_retry(query: str, **params):
    async with driver.session() as session:
        return await session.run(query, **params)
```

## Performance Monitoring

### Query Performance
```python
# Use EXPLAIN to analyze query performance
query = """
EXPLAIN
MATCH (p:Player {id: $player_id})-[:EXPERIENCED]->(n:Narrative)
RETURN n
ORDER BY n.timestamp DESC
LIMIT 100
"""

# Use PROFILE for detailed execution plan
query = """
PROFILE
MATCH (p:Player {id: $player_id})-[:EXPERIENCED]->(n:Narrative)
RETURN n
ORDER BY n.timestamp DESC
LIMIT 100
"""
```

### Monitoring Metrics
```python
from src.monitoring.metrics import record_metric

# Record query execution time
async def execute_monitored_query(query: str, **params):
    start_time = time.time()
    try:
        result = await session.run(query, **params)
        execution_time = time.time() - start_time

        record_metric(
            "neo4j_query_duration",
            execution_time,
            labels={"query_type": "player_state"}
        )

        return result
    except Exception as e:
        record_metric(
            "neo4j_query_errors",
            1,
            labels={"error_type": type(e).__name__}
        )
        raise
```

## Best Practices

### Schema Design
- **Use Labels**: Organize nodes with meaningful labels
- **Index Properties**: Index frequently queried properties
- **Relationship Types**: Use descriptive relationship types
- **Property Types**: Use appropriate property types (string, int, datetime)

### Query Patterns
- **Parameterize Queries**: Always use parameterized queries
- **Limit Results**: Always use LIMIT for potentially large result sets
- **Use Indexes**: Ensure queries use indexes (check with EXPLAIN)
- **Batch Operations**: Use batch operations for bulk updates

### Error Handling
- **Retry Transient Errors**: Retry transient connection errors
- **Handle Constraint Violations**: Handle unique constraint violations gracefully
- **Log Query Failures**: Log failed queries for debugging
- **Monitor Performance**: Track query performance metrics

### Testing
- **Unit Tests**: Test query logic in isolation
- **Integration Tests**: Test with real Neo4j instance
- **Performance Tests**: Test query performance under load
- **Data Integrity Tests**: Verify data consistency

## Common Pitfalls

### Avoid Cartesian Products
```python
# BAD: Cartesian product
query = """
MATCH (p:Player), (w:World)
RETURN p, w
"""

# GOOD: Use relationships
query = """
MATCH (p:Player)-[:IN_WORLD]->(w:World)
RETURN p, w
"""
```

### Avoid Unbounded Queries
```python
# BAD: No limit
query = """
MATCH (p:Player)-[:EXPERIENCED]->(n:Narrative)
RETURN n
"""

# GOOD: With limit
query = """
MATCH (p:Player)-[:EXPERIENCED]->(n:Narrative)
RETURN n
LIMIT 100
```
```

### Avoid String Concatenation
```python
# BAD: String concatenation
query = f"MATCH (p:Player {{id: '{player_id}'}}) RETURN p"

# GOOD: Parameterized
query = "MATCH (p:Player {id: $player_id}) RETURN p"
result = await session.run(query, player_id=player_id)
```

## References

- **LangGraph Documentation**: https://langchain-ai.github.io/langgraph/
- **Neo4j Cypher Manual**: https://neo4j.com/docs/cypher-manual/current/
- **Neo4j Performance Tuning**: https://neo4j.com/docs/operations-manual/current/performance/
- **Circuit Breaker Pattern**: `src/agent_orchestration/circuit_breaker.py`

---

**Last Updated**: 2025-10-26
**Status**: Active - Agent orchestration and graph database guidance
