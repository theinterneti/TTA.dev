# Platform Shared Components

This directory contains shared components and utilities that are used across multiple TTA.dev platform packages.

## Directory Structure

```
platform/
├── shared/
│   ├── utils/           # Shared utility functions
│   ├── README.md        # This file
│   └── ...              # Future shared components
```

## Usage

Import shared utilities with:

```python
from platform.shared.utils import some_utility
```

## Contributing

When adding shared components:
1. Ensure they are truly shared across multiple platform components
2. Follow TTA.dev coding standards (type hints, testing, documentation)
3. Add appropriate unit tests
4. Update this README as needed


---
**Logseq:** [[TTA.dev/Platform/Shared/Readme]]
