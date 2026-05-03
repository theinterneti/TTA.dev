---
name: config
description: "Skill for the Config area of TTA.dev. 21 symbols across 4 files."
---

# Config

21 symbols | 4 files | Cohesion: 90%

## When to Use

- Working with code in `scripts/`
- Understanding how execute, execute, execute work
- Modifying config-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `scripts/config/generate_assistant_configs.py` | execute, execute, execute, execute, execute (+5) |
| `ttadev/primitives/config/analysis_config.py` | _load_yaml, _load_json, load_config, save_config, find_config_file (+3) |
| `ttadev/primitives/config/orchestration_config.py` | from_yaml, load_orchestration_config |
| `tests/unit/test_analysis_config.py` | test_save_yaml_roundtrip |

## Entry Points

Start here when exploring this area:

- **`execute`** (Function) — `scripts/config/generate_assistant_configs.py:69`
- **`execute`** (Function) — `scripts/config/generate_assistant_configs.py:87`
- **`execute`** (Function) — `scripts/config/generate_assistant_configs.py:236`
- **`execute`** (Function) — `scripts/config/generate_assistant_configs.py:292`
- **`execute`** (Function) — `scripts/config/generate_assistant_configs.py:399`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `execute` | Function | `scripts/config/generate_assistant_configs.py` | 69 |
| `execute` | Function | `scripts/config/generate_assistant_configs.py` | 87 |
| `execute` | Function | `scripts/config/generate_assistant_configs.py` | 236 |
| `execute` | Function | `scripts/config/generate_assistant_configs.py` | 292 |
| `execute` | Function | `scripts/config/generate_assistant_configs.py` | 399 |
| `execute` | Function | `scripts/config/generate_assistant_configs.py` | 527 |
| `execute` | Function | `scripts/config/generate_assistant_configs.py` | 583 |
| `execute` | Function | `scripts/config/generate_assistant_configs.py` | 622 |
| `generate_configs` | Function | `scripts/config/generate_assistant_configs.py` | 664 |
| `main` | Function | `scripts/config/generate_assistant_configs.py` | 747 |
| `test_save_yaml_roundtrip` | Function | `tests/unit/test_analysis_config.py` | 541 |
| `load_config` | Function | `ttadev/primitives/config/analysis_config.py` | 362 |
| `save_config` | Function | `ttadev/primitives/config/analysis_config.py` | 414 |
| `find_config_file` | Function | `ttadev/primitives/config/analysis_config.py` | 276 |
| `get_config` | Function | `ttadev/primitives/config/analysis_config.py` | 531 |
| `get_config_path` | Function | `ttadev/primitives/config/analysis_config.py` | 549 |
| `from_yaml` | Function | `ttadev/primitives/config/orchestration_config.py` | 113 |
| `load_orchestration_config` | Function | `ttadev/primitives/config/orchestration_config.py` | 205 |
| `_load_yaml` | Function | `ttadev/primitives/config/analysis_config.py` | 332 |
| `_load_json` | Function | `ttadev/primitives/config/analysis_config.py` | 354 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Generate_configs → Execute` | intra_community | 5 |
| `Generate_configs → Execute` | intra_community | 5 |
| `Generate_configs → Execute` | intra_community | 5 |
| `Generate_configs → Execute` | intra_community | 4 |

## How to Explore

1. `gitnexus_context({name: "execute"})` — see callers and callees
2. `gitnexus_query({query: "config"})` — find related execution flows
3. Read key files listed above for implementation details
