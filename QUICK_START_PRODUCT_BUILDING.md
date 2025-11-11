# TTA.dev Product Building Environment - Quick Start

**Get productive in the TTA.dev product building environment in under 10 minutes.**

---

## 🚀 One-Click Setup

### Option 1: VS Code Devcontainer (Recommended)

1. **Open in VS Code:**
   ```bash
   code .
   ```

2. **Reopen in Container:**
   - VS Code will detect the devcontainer configuration
   - Click "Reopen in Container" when prompted
   - Or: `Ctrl+Shift+P` → "Dev Containers: Reopen in Container"

3. **Wait for Setup:**
   - Environment setup runs automatically (~5-10 minutes)
   - Coffee break time! ☕

4. **Verify Installation:**
   ```bash
   tta-test    # Run all tests
   ace-session # Initialize ACE learning session
   ```

### Option 2: Manual Setup (Local Development)

```bash
# Install UV package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync --all-extras

# Setup development environment
.devcontainer/setup.sh

# Start observability stack
docker-compose -f docker-compose.dev.yml up -d
```

---

## 🎯 Your First TTA Development Session

### 1. Navigate to TTA Rebuild
```bash
tt  # Alias for: cd packages/tta-rebuild
```

### 2. Start ACE Learning Session
```bash
ace-session
```
This initializes the Autonomous Cognitive Engine to capture development lessons.

### 3. Run Existing Tests
```bash
tta-test
```
Verify that all 14/14 tests pass in the TTA rebuild package.

### 4. Start Development Server (if available)
```bash
tta-dev
```

### 5. Monitor Your Development
- **Prometheus Metrics:** http://localhost:9090
- **Grafana Dashboards:** http://localhost:3000 (admin/admin)
- **Development Database:** postgresql://tta_dev:tta_dev@localhost:5432/tta_dev

---

## 🧠 ACE (Knowledge Capture) Usage

### Automatic Pattern Capture

ACE automatically captures patterns as you develop:

```bash
# View captured patterns
ls .ace/knowledge-base/development-patterns/

# View learning insights
ls .ace/learnings/daily-insights/

# Check session reports
cat .ace/learnings/daily-insights/session_report_$(date +%Y-%m-%d).md
```

### Manual Pattern Capture

```python
# In your development session
from .ace.ace_implementation import ACEKnowledgeCapture, DevelopmentPattern

ace = ACEKnowledgeCapture()

# Capture a successful pattern
pattern = DevelopmentPattern(
    name="narrative_validation_pattern",
    description="Pattern for validating narrative coherence",
    context="TTA rebuild narrative engine",
    code_example="...",
    success_metrics={"coherence_score": 0.95},
    reusability_score=0.9,
    tags=["narrative", "validation"],
    captured_date="2025-11-10"
)

ace.capture_development_pattern(pattern)
```

---

## 🛠️ Development Commands

### Code Quality
```bash
tta-lint        # Fix linting issues
tta-format      # Format code
tta-typecheck   # Run type checking
```

### Testing
```bash
tta-test                    # Run all tests
uv run pytest packages/tta-rebuild/tests/ -v  # Test specific package
uv run pytest --cov=packages --cov-report=html  # With coverage
```

### Navigation
```bash
tt        # Go to tta-rebuild
tp        # Go to tta-dev-primitives
docs      # Go to documentation
ace       # Go to ACE knowledge base
```

### Development Tools
```bash
ace-session   # Start new learning session
ace-capture   # Capture current session insights
```

---

## 📊 Observability Stack

### Access Points

| Service | URL | Credentials | Purpose |
|---------|-----|-------------|---------|
| Prometheus | http://localhost:9090 | None | Metrics collection |
| Grafana | http://localhost:3000 | admin/admin | Dashboards |
| PostgreSQL | localhost:5432 | tta_dev/tta_dev | Database |
| Redis | localhost:6379 | None | Caching |

### Key Metrics to Monitor

1. **Development Velocity**
   - Tests passing rate
   - Code coverage trends
   - Feature completion time

2. **Code Quality**
   - Linting issues over time
   - Type checking errors
   - Technical debt metrics

3. **Performance**
   - Test execution time
   - Build duration
   - Memory usage patterns

---

## 🎓 Learning from ACE

### Daily Pattern Review

```bash
# Check today's captured patterns
python3 -c "
import json
from pathlib import Path
from datetime import date

insights_dir = Path('.ace/learnings/daily-insights')
today_file = insights_dir / f'session_report_{date.today()}.md'

if today_file.exists():
    print(today_file.read_text())
else:
    print('No session report for today yet - run ace-session to start!')
"
```

### Weekly Retrospective

```bash
# Generate weekly learning summary
ls .ace/learnings/daily-insights/ | grep $(date +%Y-%m-) | head -7
```

### Apply Patterns to New Features

1. **Review Similar Patterns:**
   ```bash
   grep -r "narrative" .ace/knowledge-base/development-patterns/
   ```

2. **Check Success Metrics:**
   ```bash
   jq '.success_metrics' .ace/knowledge-base/development-patterns/*.json
   ```

3. **Use Reusability Scores:**
   ```bash
   jq '.reusability_score' .ace/knowledge-base/development-patterns/*.json | sort -n
   ```

---

## 🔍 Troubleshooting

### Environment Issues

**Container won't start:**
```bash
# Check Docker status
docker system info

# Rebuild container
Ctrl+Shift+P → "Dev Containers: Rebuild Container"
```

**Package installation fails:**
```bash
# Clear UV cache
rm -rf ~/.cache/uv
uv sync --all-extras
```

**Tests fail:**
```bash
# Check Python path
echo $PYTHONPATH

# Reinstall in development mode
uv sync --all-extras
```

### ACE Issues

**No patterns captured:**
```bash
# Check ACE directory structure
tree .ace/

# Run manual pattern analysis
python3 .ace/ace_implementation.py
```

**Session reports empty:**
```bash
# Initialize new session
python3 .ace/init-session.py

# Check session file
ls -la .ace/learnings/daily-insights/
```

### Observability Stack Issues

**Services not accessible:**
```bash
# Check container status
docker-compose -f docker-compose.dev.yml ps

# Restart services
docker-compose -f docker-compose.dev.yml restart
```

---

## 🎯 Next Steps

### For TTA Development

1. **Explore Existing Code:**
   ```bash
   tt
   tree src/
   ```

2. **Review Tests:**
   ```bash
   cat tests/test_base_primitive.py
   cat tests/test_metaconcepts.py
   ```

3. **Start Feature Development:**
   - Use existing primitives as foundation
   - Follow TTA.dev patterns for observability
   - Let ACE capture your successful approaches

### For Platform Improvement

1. **Identify Pain Points:**
   - Missing primitives needed for TTA
   - Performance bottlenecks in development
   - Integration friction points

2. **Contribute Back:**
   - Enhance TTA.dev primitives based on real usage
   - Share patterns discovered during TTA development
   - Improve developer experience

### For Future Products

1. **Review Captured Patterns:**
   - Study successful development approaches
   - Understand quality strategies that worked
   - Note performance optimization techniques

2. **Apply Templates:**
   - Use generated project structure templates
   - Apply proven tooling configurations
   - Implement validated quality gates

---

## 📚 Resources

- **Main Documentation:** [`PRODUCT_BUILDING_ENVIRONMENT.md`](PRODUCT_BUILDING_ENVIRONMENT.md)
- **Agent Complexity Management:** [`AI_AGENT_COMPLEXITY_MANAGEMENT.md`](AI_AGENT_COMPLEXITY_MANAGEMENT.md)
- **Package Status Report:** [`PACKAGE_STATUS_INVESTIGATION_REPORT.md`](PACKAGE_STATUS_INVESTIGATION_REPORT.md)
- **TTA Rebuild Status:** [`TTA_REBUILD_STATUS.md`](TTA_REBUILD_STATUS.md)

**Ready to build? Your environment is waiting! 🚀**
