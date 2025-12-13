# Therapeutic Text Adventure (TTA) User Guide

## 🎮 Introduction

Welcome to the Therapeutic Text Adventure (TTA)! This guide will help you navigate the game, understand its features, and make the most of your therapeutic journey.

## Getting Started

### Installation

1. Ensure you have Python 3.9+ installed
2. Clone the repository:
   ```bash
   git clone https://github.com/your-organization/tta.git
   cd tta
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables in `.env`
5. Start Neo4j database
6. Start LM Studio with required models

### Running the Game

There are three different implementations you can run:

```bash
# Traditional approach
python -m src.main

# LangGraph approach
python -m src.main_langgraph

# Dynamic tools with LangGraph approach (recommended)
python -m src.main_dynamic
```

## Game Commands

### Basic Navigation

- `go [direction]`: Move in a direction (north, south, east, west)
  - Example: `go north`
  - Emoji: 🚶‍♂️

- `look`: Look around the current location
  - Example: `look`
  - Emoji: 👀

### Interaction with Objects

- `take [item]`: Take an item
  - Example: `take journal`
  - Emoji: 🫳

- `examine [item]`: Examine an item
  - Example: `examine journal`
  - Emoji: 🔍

### Character Interaction

- `talk [character]`: Talk to a character
  - Example: `talk wise elder`
  - Emoji: 💬

### Inventory Management

- `inventory` or `inv`: Check your inventory
  - Example: `inventory`
  - Emoji: 🎒

### Game Control

- `quit`: Exit the game
  - Example: `quit`
  - Emoji: 🚪

## Natural Language Commands

The game understands natural language, so you can phrase commands in different ways:

- "I want to go north" → `go north`
- "Let me look around" → `look`
- "Can I pick up the journal?" → `take journal`
- "Tell me more about this crystal" → `examine crystal`
- "I'd like to speak with the elder" → `talk elder`
- "What am I carrying?" → `inventory`

## Emoji Guide

The game uses emojis to enhance the narrative:

### Location Emojis

- 🌲 Forest
- 🏠 House
- 🏞️ River
- 🏔️ Mountain
- 🌅 Beach
- 🌾 Field
- 🌳 Garden

### Item Emojis

- 📜 Scroll
- 📔 Journal
- 🔑 Key
- 🗡️ Sword
- 🧪 Potion
- 💎 Crystal
- 🧭 Compass

### Character Emojis

- 🧙‍♂️ Wizard
- 👵 Elder
- 🦊 Fox
- 🦉 Owl
- 👧 Child
- 👨‍⚕️ Healer
- 🧚 Fairy

### Emotion Emojis

- 😊 Happy
- 😢 Sad
- 😮 Surprised
- 🤔 Thinking
- 😠 Angry
- 😌 Calm
- 😨 Afraid

## Therapeutic Elements

### Mindfulness Exercises

The game includes mindfulness exercises that you can practice:

- Breathing exercises
- Grounding techniques
- Visualization practices
- Body scan meditations

Example: When in the garden, try `practice mindfulness` to engage in a guided exercise.

### Emotional Reflection

The game encourages emotional reflection through:

- Journal writing
- Dialogue with characters
- Interaction with symbolic objects
- Exploration of emotional landscapes

Example: When you find a journal, try `write in journal` to reflect on your feelings.

### Therapeutic Quests

The game includes quests designed to support therapeutic goals:

- Anxiety reduction
- Stress management
- Emotional regulation
- Self-discovery
- Confidence building

Example: Talk to the wise elder to receive quests tailored to your therapeutic needs.

## Tips for a Better Experience

1. **Take your time**: There's no rush. Explore at your own pace.
2. **Read carefully**: The narrative contains therapeutic insights.
3. **Engage with characters**: They offer guidance and support.
4. **Reflect on experiences**: Consider how game situations relate to your life.
5. **Practice regularly**: The therapeutic benefits increase with regular engagement.
6. **Be honest**: The game adapts to your authentic responses.
7. **Try different approaches**: There are multiple ways to navigate challenges.

## Troubleshooting

### Common Issues

1. **Game doesn't start**:
   - Check that Neo4j is running
   - Verify LM Studio is running with the correct models
   - Ensure environment variables are set correctly

2. **Commands not recognized**:
   - Try rephrasing in simpler terms
   - Check for typos
   - Use basic command forms (go, look, take)

3. **Game seems stuck**:
   - Press Enter to continue
   - Type `look` to refresh your surroundings
   - Restart the game if necessary

### Getting Help

If you encounter issues not covered here:

1. Check the project documentation
2. Look for similar issues in the issue tracker
3. Ask for help in the project chat
4. Create a new issue with detailed information

## Conclusion

The Therapeutic Text Adventure is designed to provide an engaging, reflective experience that supports your emotional well-being. By exploring the game world, interacting with characters, and engaging with therapeutic elements, you can discover new insights and develop valuable skills for managing emotions and stress.

Enjoy your journey! 🌟


---
**Logseq:** [[TTA.dev/_archive/Legacy-tta-game/User_guide]]
