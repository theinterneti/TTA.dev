---
title: TTA Extended Evaluation with Meta Llama 3.3 8B - Setup Guide
tags: #TTA
status: Active
repo: theinterneti/TTA
path: testing/extended_evaluation/LLAMA_3_3_SETUP_GUIDE.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/TTA Extended Evaluation with Meta Llama 3.3 8B - Setup Guide]]

## 🚀 Quick Setup (5 minutes)

### Step 1: Get Your Free OpenRouter API Key
1. Visit **https://openrouter.ai/**
2. Sign up for a free account
3. Go to the **Keys** section
4. Create a new API key
5. Copy the API key (starts with `sk-or-v1-`)

### Step 2: Set Up Your API Key
```bash
# Run the API key setup script
./testing/extended_evaluation/setup_api_key.sh

# Or set it manually:
export OPENROUTER_API_KEY="your-api-key-here"
```

### Step 3: Activate Virtual Environment
```bash
# Activate the virtual environment
source venv/bin/activate
```

### Step 4: Verify Configuration
```bash
# Check that everything is configured correctly
python testing/run_extended_evaluation.py --mode status --config testing/configs/production_extended_evaluation.yaml
```

**Expected Output:**
```
✅ Extended evaluation framework loaded successfully!
  Enabled Models: 1
    ✓ Meta Llama 3.3 8B Instruct (openrouter)
  Enhanced User Profiles: 2
    • Typical User
    • Engaged User
  Extended Scenarios: 2
    • Fantasy Baseline Test (25 turns, 120min)
    • Contemporary Baseline Test (20 turns, 100min)
```

## 🧪 Testing Phases

### Phase 1: Quick Sample Test (30-60 minutes)
**Purpose**: Verify model integration and basic functionality

```bash
python testing/run_extended_evaluation.py --mode quick-sample --config testing/configs/production_extended_evaluation.yaml
```

**What it tests:**
- First enabled model (Llama 3.3 8B)
- First profile (Typical User)
- Shortest scenario (Contemporary Baseline - 20 turns)
- ~30-60 minutes duration

**Success Criteria:**
- ✅ Test completes without critical errors
- ✅ Narrative coherence ≥ 7.0/10
- ✅ World consistency ≥ 7.5/10
- ✅ User engagement ≥ 6.5/10

### Phase 2: Single-Model Baseline (2-4 hours)
**Purpose**: Establish quality baselines with Llama 3.3 8B

```bash
# This runs 2 scenarios × 1 profile × 1 model = 2 tests
python testing/run_extended_evaluation.py --mode comprehensive --config testing/configs/production_extended_evaluation.yaml
```

**What it tests:**
- Both baseline scenarios (Fantasy 25 turns, Contemporary 20 turns)
- Typical User profile only
- ~2-4 hours total duration

**Expected Results:**
- **Fantasy Baseline**: Narrative coherence 7.5+, World consistency 8.0+, User engagement 7.0+
- **Contemporary Baseline**: Therapeutic integration 7.8+, Character development 7.5+, User engagement 7.2+

### Phase 3: Multi-Profile Testing (4-8 hours)
**Purpose**: Test performance across different user types

```bash
# Edit config to include both profiles, then run comprehensive
python testing/run_extended_evaluation.py --mode comprehensive --config testing/configs/production_extended_evaluation.yaml
```

**What it tests:**
- Both scenarios × Both profiles (Typical User + Engaged User)
- 2 scenarios × 2 profiles × 1 model = 4 tests
- ~4-8 hours total duration

## 📊 Model Configuration Details

### Meta Llama 3.3 8B Instruct via OpenRouter
```yaml
llama_3_3_8b_instruct:
  name: "Meta Llama 3.3 8B Instruct"
  provider: "openrouter"
  model_id: "meta-llama/llama-3.3-8b-instruct:free"

  # Optimized settings for extended sessions
  temperature: 0.7              # Balanced creativity/consistency
  max_tokens: 2048             # Sufficient for detailed responses
  top_p: 0.9
  frequency_penalty: 0.1       # Reduce repetition over long sessions
  presence_penalty: 0.1        # Encourage topic diversity

  # Free tier optimized settings
  timeout_seconds: 45          # Generous timeout
  retry_attempts: 3            # More retries for reliability
  max_requests_per_minute: 20  # Conservative rate limiting
```

### Expected Performance Targets
- **Narrative Coherence**: 7.8/10 (excellent story consistency)
- **World Consistency**: 8.0/10 (strong world state tracking)
- **User Engagement**: 7.5/10 (engaging interactions)
- **Technical Performance**: 8.2/10 (fast, reliable responses)

## 🎯 Quality Baselines to Establish

### Fantasy Baseline Test (25 turns, ~2 hours)
**Scenario**: Medieval fantasy adventure with moral choices
**Key Metrics**:
- Narrative coherence: Target 7.5+/10
- World consistency: Target 8.0+/10
- User engagement: Target 7.0+/10

**Decision Points**:
- Turn 8: Moral choice (moderate impact)
- Turn 16: Strategic decision (major impact)
- Turn 24: Character development (personal impact)

### Contemporary Baseline Test (20 turns, ~1.5 hours)
**Scenario**: Small town drama with therapeutic integration
**Key Metrics**:
- Therapeutic integration: Target 7.8+/10
- Character development: Target 7.5+/10
- User engagement: Target 7.2+/10

**Decision Points**:
- Turn 7: Relationship choice (personal impact)
- Turn 14: Life direction choice (major impact)

## 📈 Analyzing Results

### After Each Test Phase
```bash
# Generate comprehensive analysis report
python testing/run_extended_evaluation.py --mode analysis-only
```

**Report Includes**:
- Model performance analysis with trends
- Quality metric breakdowns
- Strengths and weaknesses identification
- Improvement recommendations
- Comparative analysis across scenarios

### Key Metrics to Monitor

| Metric | Minimum | Good | Excellent | Action if Below |
|--------|---------|------|-----------|-----------------|
| **Narrative Coherence** | 6.5 | 7.5 | 8.5 | Review prompts, adjust temperature |
| **World Consistency** | 7.0 | 8.0 | 9.0 | Enhance state management |
| **User Engagement** | 6.0 | 7.0 | 8.0 | Improve choice meaningfulness |
| **Technical Performance** | 6.5 | 7.5 | 8.5 | Optimize API calls |

### Success Indicators
- ✅ **All tests complete** without critical errors
- ✅ **Quality scores** meet or exceed targets
- ✅ **Consistent performance** across scenarios
- ✅ **No significant degradation** over extended turns
- ✅ **Response times** under 5 seconds average

## 🔧 Troubleshooting

### Common Issues

**API Key Problems**:
```bash
# Verify API key is set
echo $OPENROUTER_API_KEY

# Re-run setup if needed
./testing/extended_evaluation/setup_api_key.sh
```

**Rate Limiting**:
- OpenRouter free tier: ~20 requests/minute
- Framework automatically handles rate limiting
- If hitting limits, tests will pause and retry

**Memory Issues**:
- Extended sessions can use significant memory
- Monitor system resources during tests
- Reduce concurrent sessions if needed

**Configuration Errors**:
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('testing/configs/production_extended_evaluation.yaml'))"
```

### Performance Optimization
- **Slow responses**: Check internet connection, OpenRouter status
- **High memory usage**: Enable memory optimization in config
- **Inconsistent quality**: Review temperature and penalty settings

## 🎉 Success Checklist

### Phase 1 Complete ✅
- [ ] Quick sample test runs successfully
- [ ] Basic quality metrics established
- [ ] No critical errors or failures
- [ ] Response times acceptable (<5s average)

### Phase 2 Complete ✅
- [ ] Both baseline scenarios tested
- [ ] Quality baselines established for Llama 3.3 8B
- [ ] Performance consistent across scenarios
- [ ] Comprehensive analysis report generated

### Phase 3 Complete ✅
- [ ] Multi-profile testing completed
- [ ] Profile-specific insights generated
- [ ] Model strengths/weaknesses identified
- [ ] Improvement recommendations documented

## 📋 Next Steps After Baseline

1. **Implement Improvements**: Address top recommendations from analysis
2. **Expand Testing**: Add more scenarios or user profiles
3. **Compare Models**: Test additional models for comparison
4. **Regular Monitoring**: Set up weekly/monthly evaluation schedule
5. **Integration**: Incorporate insights into TTA development workflow

---

**Ready to establish your Llama 3.3 8B quality baselines?** Start with the quick sample test! 🚀


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___testing extended evaluation llama 3 3 setup guide document]]
