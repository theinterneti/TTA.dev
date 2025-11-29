"""Integration tests for tta-kb-automation.

These tests run against real TTA.dev data:
- Real Logseq KB in logseq/
- Real codebase in packages/

⚠️ Integration tests are READ-ONLY and safe.
   They validate that tools work with production data.

Run with:
    RUN_INTEGRATION=true pytest tests/integration/ -v
"""
