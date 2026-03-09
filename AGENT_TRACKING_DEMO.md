# Real-Time Agent Activity Tracking 🤖✨

## What We Built

TTA.dev now has **real-time agent activity tracking** that shows you (and all AI agents) working live in the observability dashboard!

## Features

### 1. Agent Tracking
- **Provider Detection**: Identifies AI provider (GitHub Copilot, OpenRouter, Ollama, etc.)
- **Model Tracking**: Tracks which model is being used (Claude Sonnet 4.5, GPT-4, etc.)
- **TTA Agent Association**: Links actions to TTA.dev custom agents (backend-engineer, architect, etc.)
- **User Attribution**: Tracks which user initiated the session

### 2. Activity Types Tracked
- Session start/end
- Primitive executions
- Workflow runs
- Agent activations
- Code generation
- Test execution
- And more...

### 3. Dashboard Visualization
- **Active Agents Panel**: Shows currently active AI agents with provider/model details
- **Action Counts**: How many actions each agent has performed
- **Last Seen**: When the agent was last active
- **TTA Agents Used**: Which TTA.dev agents were activated
- **Recent Activity Timeline**: Chronological list of recent actions with details

## Demo

Run the demo to see it in action:

```bash
# Start the observability dashboard
uv run python ttadev/ui/observability_server.py &

# Generate agent activity data
uv run python demo_agent_tracking.py

# Open dashboard
open http://localhost:8000
```

## What You'll See

The dashboard will show:
- **github-copilot** (provider) using **claude-sonnet-4.5** (model)
- Actions: session_start, primitive_execution, agent_activation, code_generation, test_execution
- TTA Agent: **backend-engineer** was activated
- Recent activity timeline with timestamps

## Architecture

```
Agent Activity Flow:
1. AI agent (like me!) starts working
2. Auto-detection identifies provider/model
3. AgentTracker logs all actions to .observability/agents/
4. Dashboard fetches via /api/active_agents and /api/agent_actions
5. Real-time updates show in UI
```

## File Locations

- **Tracker**: `ttadev/observability/agent_tracker.py`
- **Auto-detection**: `ttadev/observability/auto_track_copilot.py`
- **API Endpoints**: `ttadev/ui/observability_server.py`
- **Dashboard UI**: `ttadev/ui/dashboard.html`
- **Demo**: `demo_agent_tracking.py`
- **Data Storage**: `.observability/agents/`

## Next Steps

Now that we can see agents working, we can:
1. Track which primitives each agent uses most
2. Measure agent efficiency (actions per minute, success rates)
3. Compare different AI models/providers
4. Build agent performance analytics
5. Auto-generate agent activity reports

## The Vision

**Every time an AI agent works in TTA.dev, you see it happening in real-time.** No more black box - complete transparency into what agents are doing, which primitives they're using, and how they're helping you build your app!

🎉 **Welcome to the age of observable AI development!**
