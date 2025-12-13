# Basic Agent Template

A minimal, production-ready agent setup using TTA.dev primitives.

## Features
- **Caching**: Results cached for 1 hour.
- **Retries**: Automatic retries on failure (3 attempts).
- **Observability**: Built-in tracing context.

## Usage

1. Copy this folder.
2. `uv add tta-dev-primitives`
3. `cp .env.example .env` and add your keys.
4. Edit `main.py` to add your LLM logic.
5. `python main.py`


---
**Logseq:** [[TTA.dev/Templates/Basic-agent/Readme]]
