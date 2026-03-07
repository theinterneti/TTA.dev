---
title: TTA Single-Player Testing Quick Start Guide
tags: #TTA
status: Active
repo: theinterneti/TTA
path: testing/QUICK_START_GUIDE.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/TTA Single-Player Testing Quick Start Guide]]

## Prerequisites Checklist
- [ ] Python dependencies installed
- [ ] Redis running on localhost:6379
- [ ] Neo4j running on localhost:7687
- [ ] At least one local model running (Qwen2.5 or Llama-3.1)
- [ ] OpenRouter API key configured (optional)

## Quick Commands

### Check Configuration Status
```bash
python testing/run_single_player_tests.py --mode status
```

### Run Quick Test (Single Model/Profile/Scenario)
```bash
python testing/run_single_player_tests.py --mode quick
```

### Run Comprehensive Test Suite
```bash
python testing/run_single_player_tests.py --mode comprehensive
```

## Model Setup Instructions

### Local Models (Recommended)
1. Install LM Studio or similar local inference server
2. Download and run:
   - Qwen2.5-7B-Instruct on port 1234
   - Llama-3.1-8B-Instruct on port 1235

### OpenRouter Models (Optional)
1. Get free API key from https://openrouter.ai/
2. Set environment variable:
   ```bash
   export OPENROUTER_API_KEY=your_key_here
   ```

## Understanding Results

### Scoring System (1-10 scale)
- **Narrative Quality (40%)**: Creativity, consistency, depth
- **User Engagement (30%)**: Fun factor, immersion, retention
- **Therapeutic Integration (20%)**: Subtlety, effectiveness, safety
- **Technical Performance (10%)**: Speed, reliability, efficiency

### Target Scores
- **Minimum Acceptable**: 6.0/10
- **Target Score**: 7.5/10
- **Excellence Threshold**: 8.5/10

## Troubleshooting

### Common Issues
1. **No models enabled**: Check model server status and configuration
2. **Database connection failed**: Ensure Redis and Neo4j are running
3. **Slow response times**: Check model server resources
4. **High error rates**: Review model configuration and prompts

### Getting Help
- Check logs in `testing/results/logs/`
- Review configuration in `testing/model_testing_config.yaml`
- Run setup script again: `python testing/setup_testing_environment.py`


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___testing quick start guide document]]
