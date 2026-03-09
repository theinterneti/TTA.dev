# TTA.dev Observability Dashboard Features

## 🎯 Current Status: WORKING

The observability dashboard is now live with comprehensive features for monitoring TTA.dev workflows, primitives, and agents.

## 📊 Dashboard Panels

### 1. **Live Metrics**
- Total workflows executed
- Active workflows (real-time)
- Success rate percentage
- Average workflow duration

### 2. **Active Agents** 🤖
- Auto-discovers agents from `.github/agents/*.agent.md`
- Shows agent name, description, and available tools
- Parses YAML frontmatter from agent files
- Currently showing: backend-engineer, architect

### 3. **Primitives Catalog** ⚙️
- Complete list of available TTA.dev primitives
- Categorized by type (recovery, optimization, composition, control, core)
- Shows:
  - RetryPrimitive - Automatic retry with exponential backoff
  - CircuitBreakerPrimitive - Circuit breaker for fault tolerance
  - FallbackPrimitive - Fallback to alternative on failure
  - TimeoutPrimitive - Enforce execution timeouts
  - CachePrimitive - Result caching with TTL
  - ParallelPrimitive - Execute operations in parallel
  - SequentialPrimitive - Execute sequentially
  - ConditionalPrimitive - Conditional execution
  - RouterPrimitive - Route to different primitives
  - LambdaPrimitive - Wrap any function

### 4. **Workflow Registry** 🔄
- Auto-discovers workflows from `examples/` and `ttadev/workflows/`
- Shows registered workflows with descriptions
- Links to workflow source files

## 🕸️ CodeGraphContext Integration

Interactive code visualization with multiple views:

### Architecture View
- Package structure visualization
- Shows ttadev.primitives, ttadev.observability, ttadev.ui
- Displays inter-package dependencies

### Dependencies View
- External dependencies (fastapi, opentelemetry)
- Internal package relationships
- Dependency graph

### Primitives Map
- Visual map of primitive hierarchy
- Base WorkflowPrimitive and derived classes
- Categorization by type

### Agents Flow
- Agent interaction visualization
- Shows backend-engineer, architect agents
- Future: Agent coordination patterns

## 📜 Recent Traces Panel
- Real-time trace visualization
- Shows trace ID, duration, status (success/error)
- Span count and primitive usage
- Detailed span breakdown with individual durations
- Color-coded status indicators

## 🔌 WebSocket Integration
- Live connection status indicator
- Real-time updates as workflows execute
- Auto-reconnection with exponential backoff
- Ping/pong keep-alive mechanism

## 🚀 API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /` | Dashboard HTML |
| `GET /api/agents` | List all configured agents |
| `GET /api/primitives` | List all available primitives |
| `GET /api/workflows` | List registered workflows |
| `GET /api/codegraph/{view}` | Get code graph data (architecture, dependencies, primitives, agents) |
| `GET /api/metrics` | Current system metrics |
| `GET /health` | Health check |
| `WS /ws` | WebSocket for real-time updates |
| `POST /api/spans` | Submit trace spans |

## 🎨 UI Features

- **Dark theme** with gradient header
- **Responsive grid layout** adapts to screen size
- **Interactive elements** - click traces for details
- **Real-time updates** via WebSocket
- **Smooth animations** for new data
- **Color-coded status** (success=green, error=red)
- **Connection indicator** shows WebSocket status

## 📈 Self-Growing Dashboard (Roadmap)

Future enhancements:
1. **Auto-detection** of new primitive types from user code
2. **Dynamic visualization** generation for custom workflows
3. **User project metrics** alongside TTA.dev internals
4. **Agent activity tracking** - which agent triggered which workflow
5. **Performance profiling** with flamegraphs
6. **Alert system** for failures and anomalies

## 🔧 Technical Stack

- **Backend**: FastAPI with async support
- **Real-time**: WebSocket connections
- **Tracing**: OpenTelemetry integration
- **Database**: SQLite for persistence
- **Frontend**: Vanilla JavaScript (no build step!)
- **Styling**: Modern CSS with gradients and animations

## 🎯 User Journey

1. Clone TTA.dev repository
2. Run `./setup.sh` to install
3. Dashboard auto-starts on `http://localhost:8000`
4. Agent sees `AGENTS.md` and starts using TTA.dev
5. Dashboard automatically shows agent activity
6. User sees workflows, primitives, and agents in real-time
7. Zero configuration required!

## 🌟 Batteries Included

- ✅ No setup required
- ✅ Auto-discovers agents and workflows
- ✅ Real-time visualization
- ✅ Persistent storage
- ✅ Self-instrumenting (uses TTA.dev primitives)
- ✅ Production-ready fault tolerance

## Access

🌐 **Dashboard URL**: http://localhost:8000

The dashboard is now ready to demonstrate TTA.dev's capabilities to users and showcase the platform in action!
