---
title: AI Dev Toolkit - Packaging Guide
tags: #TTA
status: Active
repo: theinterneti/TTA
path: packages/ai-dev-toolkit/docs/PACKAGING_GUIDE.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/AI Dev Toolkit - Packaging Guide]]

## Purpose

Package the reusable AI development infrastructure for use across multiple projects.

## What Gets Packaged

### Core Packages
1. **tta-workflow-primitives** - AI workflow patterns
   - Router, Cache, Timeout, Retry primitives
   - Composition operators
   - Cost optimization (30-40% reduction)

2. **dev-primitives** - Development utilities
   - Error recovery patterns
   - Development tools

### Scripts & Tools
3. **OpenHands Integration**
   - test_openhands_workflow.py
   - test_single_task.py
   - test_docker_runtime.py
   - verify_docker_runtime_setup.py
   - debug_openhands_output.py
   - diagnose_openhands.py
   - monitor_batch_progress.py
   - phase7_batch_execution_final.py
   - phase7_monitor_optimized.py

4. **Workflow Management**
   - scripts/workflow/ (quality gates, stage handlers)
   - scripts/cleanup_and_organize_repo.sh

5. **Utility Scripts**
   - scripts/utils/ (orchestration, devcontainer, imports)
   - scripts/setup.sh
   - scripts/docker-health-check.sh
   - scripts/manage-containers.sh

### Monitoring Stack
6. **Observability**
   - monitoring/ (Prometheus/Grafana configs)
   - scripts/observability/
   - scripts/maturity/
   - scripts/registry/

### Documentation
7. **Complete Docs**
   - docs/agentic-primitives/
   - docs/development/
   - docs/openhands/
   - docs/guides/

## Installation

### As a Package
```bash
pip install ai-dev-toolkit
```

### For Development
```bash
git clone https://github.com/theinterneti/TTA.git
cd TTA
pip install -e packages/ai-dev-toolkit[dev,monitoring,openhands]
```

### Individual Components
```bash
# Just workflow primitives
pip install tta-workflow-primitives

# Just dev primitives
pip install dev-primitives

# With extras
pip install ai-dev-toolkit[monitoring,openhands]
```

## Usage in New Projects

### 1. Install the Toolkit
```bash
pip install ai-dev-toolkit
```

### 2. Use Workflow Primitives
```python
from tta_workflow_primitives.core import RouterPrimitive, CachePrimitive
from tta_workflow_primitives.recovery import RetryPrimitive, TimeoutPrimitive

# Build your workflow
workflow = (
    RouterPrimitive(routes=my_routes) >>
    CachePrimitive(processor, ttl_seconds=3600) >>
    RetryPrimitive(handler, max_attempts=3)
)

result = await workflow.execute(data, context)
```

### 3. Use OpenHands Tools
```bash
# Copy scripts to your project
cp -r $(python -c "import ai_dev_toolkit; print(ai_dev_toolkit.__path__[0])")/scripts ./

# Use them
python scripts/test_openhands_workflow.py
python scripts/phase7_batch_execution_final.py
```

### 4. Setup Monitoring
```bash
# Copy monitoring configs
cp -r monitoring/ ./monitoring/

# Start stack
docker-compose -f monitoring/docker-compose.monitoring.yml up -d
```

## Benefits

- ✅ **Reusable** - Works across any AI project
- ✅ **Production-Ready** - Battle-tested patterns
- ✅ **Cost-Optimized** - 30-40% reduction potential
- ✅ **Observable** - Full monitoring stack
- ✅ **Well-Documented** - Complete guides
- ✅ **Tested** - Comprehensive test suite

## What's NOT Included

Application-specific code:
- TTA domain models
- TTA business logic
- TTA-specific integrations
- Application databases (Neo4j, etc.)

These stay in the TTA repository.

## Future Enhancements

1. Publish to PyPI
2. Add more primitives (Circuit Breaker, Bulkhead, etc.)
3. Enhanced monitoring dashboards
4. Integration examples
5. Video tutorials

## License

MIT - Free to use in any project


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___ai dev toolkit ai dev toolkit docs packaging guide document]]
