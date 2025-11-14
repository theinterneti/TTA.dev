# TTA Agent Coordination

**Redis-based multi-agent coordination primitives for distributed agent systems**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

`tta-agent-coordination` provides production-ready, Redis-backed coordination primitives for building reliable multi-agent systems.

### Key Features

✅ **Message Coordination** - Priority queues, retries, dead-letter queues
✅ **Agent Registry** - Heartbeat/TTL management, liveness tracking
✅ **Circuit Breaker** - Fault tolerance with Redis-backed state
✅ **100% Generic** - No application-specific dependencies
✅ **Production-Ready** - Comprehensive tests, type hints, documentation

## Installation

```bash
uv add tta-agent-coordination
```

## Quick Start

```python
from redis.asyncio import Redis
from tta_agent_coordination import RedisMessageCoordinator, AgentId

redis = Redis.from_url("redis://localhost:6379")
coordinator = RedisMessageCoordinator(redis)

# Generic agent IDs - any string type!
sender = AgentId(type="input_processor", instance="worker-1")
recipient = AgentId(type="world_builder", instance="worker-2")

# Send/receive messages with priority queues and retries
result = await coordinator.send_message(sender, recipient, message)
```

## Documentation

- [API Reference](docs/API.md)
- [Examples](examples/)
- [Architecture](docs/ARCHITECTURE.md)

## License

MIT License - see [LICENSE](LICENSE) for details.
