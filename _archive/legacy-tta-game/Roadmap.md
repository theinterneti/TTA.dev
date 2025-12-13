**Therapeutic Text Adventure (TTA) - Roadmap and Project Plan**

**Purpose:** This document provides a high-level overview of the Therapeutic Text Adventure (TTA) project's goals, phases, features, and timelines. It serves as a guide for prioritizing tasks and understanding the overall development direction.

**1. Project Vision:**

Therapeutic Text Adventure (TTA) aims to be a groundbreaking text-based adventure game that offers:

*   **Immersive Narrative:**  Experiences comparable to high-quality literary fiction, driven by player choice and AI-generated content.
*   **Therapeutic Potential:** Subtly integrated therapeutic concepts and techniques to support self-discovery, emotional growth, and recovery, particularly for individuals resistant to traditional therapy.
*   **Dynamic Multiverse:** A vast, interconnected multiverse that feels alive and responsive, offering endless exploration and personalized journeys.

**2. Target Audience:**

TTA is designed for individuals who:

*   Seek engaging and immersive narrative experiences.
*   Are interested in self-reflection and personal growth.
*   May be exploring themes of trauma, addiction, or self-discovery.
*   May be resistant to or lack access to traditional mental health services.
*   Enjoy text-based games and interactive fiction.

**3. Key Features:**

*   **Core Gameplay Loop:** Text-based input and output, dynamic narrative generation, and player-driven progression.
*   **Infinite Multiverse:** A vast and diverse game world with countless universes to explore.
*   **Personalized Narrative:** AI-driven stories that adapt to player choices, preferences, and therapeutic needs.
*   **Subtle Therapeutic Integration:**  Therapeutic concepts woven into the narrative and gameplay, promoting self-reflection and emotional processing.
*   **AI Agents:** A collaborative network of specialized AI agents for content generation, world management, and dynamic responses.
*   **Neo4j Knowledge Graph:** A robust graph database storing game lore, character information, and dynamic game state.
*   **Genesis Sequence:** A guided onboarding process for players to create their own universes and characters.
*   **Nexus Hub:** A central point connecting all universes, facilitating inter-universe travel and potential future multiplayer interactions.
*   **Model-Powered Interface:** Leveraging Qwen2.5 as the core intelligence, with LangGraph for orchestration.
*   **Tool Use and CoRAG:** AI agents equipped with tools and Chain-of-Retrieval Augmented Generation (CoRAG) for enhanced responses.
*   **Ethical AI and Player Safety:**  Commitment to responsible AI use, player privacy, bias mitigation, and content moderation.

**4. Development Phases/Milestones:**

The TTA project is planned across four key phases, each building upon the last:

*   **Phase 1: Prototype (Proof of Concept)**
    *   **Goals:** Demonstrate core gameplay loop, test technical feasibility, validate AI-KG interaction.
    *   **Key Deliverables:** Basic text UI, simplified world generation (single location), rudimentary AI agents (IPA, UGA, NGA), basic Neo4j integration.
*   **Phase 2: Core Functionality**
    *   **Goals:** Develop core game mechanics, expand world generation, implement character creation, basic AI interactions, hybrid time model.
    *   **Key Deliverables:** Playable game with basic narrative, core AI agents (IPA, NGA, WBA, CCA, LKA, POA, NMA), LangGraph integration, persistent game state.
*   **Phase 3: Enhanced Gameplay and Features**
    *   **Goals:** Enhance gameplay with complex quests, dynamic relationships, implement "Dream Weaving" and "Echoes of the Self," refine AI behavior.
    *   **Key Deliverables:** Polished gameplay, refined AI agents, CoRAG integration, expanded knowledge graph, advanced game mechanics.
*   **Phase 4: Advanced Features and Community**
    *   **Goals:** Introduce advanced features ("Collective Unconscious"), AI-driven therapy exploration (research-focused), content creation tools (optional), community platform (optional), therapeutic impact evaluation.
    *   **Key Deliverables:** Fully realized TTA experience, potential community platform, research findings on therapeutic impact.

**5. Timeline (Estimated):**

*(Note: These are rough estimates and subject to change, especially for a solo developer. Phase durations are cumulative.)*

*   **Phase 1: Prototype:** 1-2 Months
*   **Phase 2: Core Functionality:** 3-4 Months (Total: 4-6 Months)
*   **Phase 3: Enhanced Gameplay and Features:** 4-6 Months (Total: 8-12 Months)
*   **Phase 4: Advanced Features and Community:** 6-12 Months (Total: 14-24 Months)
*   **Beta Testing and Launch (Phase 5):** 3-6 Months (Total: 17-30 Months)

**6. Prioritized Feature List (for Prototype & Phase 1):**

1.  **Core Gameplay Loop:** Text input, IPA parsing, NGA response, basic game state.
2.  **Knowledge Graph Foundation:** Basic Neo4j schema, Concept, Character, Location nodes, key relationships.
3.  **Universe Generator Agent (UGA):** Genesis Sequence framework, seed concept elicitation, universe parameter definition.
4.  **Narrative Generator Agent (NGA):** Basic scene description generation, integration with knowledge graph.
5.  **Input Processor Agent (IPA):** Basic intent parsing (look, move, talk_to, quit).
6.  **Text-Based User Interface:** Simple command-line interface for player interaction.
7.  **Persistence:** Saving and loading basic game state to Neo4j.
8.  **Automated Testing:** Unit tests for core components (IPA, NGA, basic KG queries).

**7. Technology Stack Overview:**

*   **Programming Language:** Python
*   **Graph Database:** Neo4j
*   **AI/NLP Libraries:**
    *   Transformers (Hugging Face)
    *   LangChain
    *   LangGraph
    *   Guidance (Optional)
*   **LLM (Large Language Model):** Qwen2.5 (via LM Studio initially)
*   **Development Environment:** VS Code, Git, (Optional: Project Management Software)

This Roadmap and Project Plan provides a structured overview for the development of TTA. It is designed to be a living document, adaptable and refined as the project progresses.

---
**Logseq:** [[TTA.dev/_archive/Legacy-tta-game/Roadmap]]
