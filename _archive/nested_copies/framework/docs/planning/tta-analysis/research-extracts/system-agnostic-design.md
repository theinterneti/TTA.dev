As your software development and design expert for the TTA project, I can provide a detailed exposition of the variable universe parameters system and how its flexible structure is essential for maintaining system-agnostic game rules.

The foundation of TTA's system-agnostic approach lies in representing the core mechanics of a universe through descriptive, structured data, rather than hardcoded numerical rules.

### Export of the Variable Universe Parameters System

The core parameters that define a unique parallel universe are stored as properties on the dedicated `:Universe` node within the Neo4j knowledge graph. This structure is deliberately designed to be extensible and flexible, enabling dynamic simulation without relying on fixed game rule sets.

#### 1. Core Universe Node Properties (`:Universe` Label)

| Property Name | Description | Data Structure & Purpose | Source(s) |
| :--- | :--- | :--- | :--- |
| **`universe_id`** | Unique numerical identifier. | Primary Key (INTEGER). | |
| **`name`** | Human-readable name of the universe. | STRING. | |
| **`description`** | General overview and textual context of the universe. | STRING (Free-form text). | |
| **`physical_laws`** | Defines the underlying physics (gravity, time, fundamental forces). | JSON String. Allows for customization beyond "Earth-like" norms. | |
| **`magic_system`** | Describes the rules, sources, limitations, and types of magic, if present. | JSON String. If magic is absent, the value is "None". | |
| **`technology_level`** | General level of technological advancement (e.g., "Medieval," "Futuristic"). | STRING (Controlled Vocabulary). | |
| **`history`** | Key historical events, timelines, and significant turning points. | JSON String. Allows for structured representation of historical context. | |
| **`creation_parameters`** | Records the input and choices made during the universe creation process. | JSON String. Useful for reproducibility and future modifications. | |

#### 2. Related World Node Parameters

The concepts defined at the Universe level flow down into the World level (a specific planet or realm) which further details the localized environment and systems. World parameters, which must be consistent with the universe parameters, include crucial descriptive information such as:

*   **`environment`** (e.g., "Terrestrial," "Jungle World").
*   **`geography`** and **`climate`** (stored as JSON strings for detailed, structured data).
*   **`resources`**, **`dominant_cultures`**, and **`political_system`**.

These parameters are defined through the structured **Genesis Sequence**, a process guided by the Universe Generator Agent (UGA) that elicits a "Seed Concept" and collaboratively defines the necessary parameters with the player. The Lore Keeper Agent (LKA) is consulted to ensure that the parameters are internally consistent and do not contradict existing lore.

### How the System Enables System-Agnostic Game Rules

The fundamental philosophy of TTA is to remain system agnostic, allowing for the integration of various character or combat systems (like Dungeons and Dragons or GURPS) based on player preference, rather than being restricted to one set of mechanics. This is achieved by relying on AI interpretation of descriptive data rather than numerical presets:

**1. Descriptive Data over Fixed Mechanics:**
Instead of storing numerical values for every physical or magical rule (which would tie the system to a specific game engine), the TTA uses detailed, descriptive strings and JSON objects. For example, the `magic_system` doesn't define a damage formula; it describes the source and limitations: e.g., "Magic is based on musical frequencies. Technology is primitive".

**2. AI-Driven Interpretation:**
The AI agents, particularly the Narrative Generator Agent (NGA) and Character Creator Agent (CCA), are tasked with interpreting these descriptions to generate outcomes dynamically.

*   **CCA Role:** Character attributes and skills are defined in a system-agnostic way, focusing on descriptions, traits, motivations, and relationships rather than specific numerical mechanics. For instance, a character might possess the descriptive trait "Gifted with musical affinity" instead of a numerical "Skill: Music Magic +5".
*   **NGA Role:** When a player attempts an action—such as casting a spell—the NGA receives the descriptive parameters (`magic_system`: JSON rules, `Character`: descriptive traits) and generates a coherent outcome based on LLM reasoning and the narrative context. The NGA translates the textual description of the universe's physics and magic into a narrative response.

**3. Flexibility through JSON and Textual Descriptions:**
Storing complex elements like `physical_laws` and `history` as flexible JSON strings allows the schema to adapt to virtually any universe concept the player devises, from elemental magic systems to advanced AI technology. This prevents the need for major database restructuring when new genres or rules are introduced. The detailed descriptive attributes serve as the context that LLMs use to dynamically adjust complexity and pacing, making the world feel consistent without relying on external rule sets.

In essence, the system ensures system-agnostic rules by storing the *lore* and *logic* of the universe descriptively, leaving the implementation of numerical *mechanics* open for dynamic interpretation by the AI agents or for future integration with specific external systems.


The architecture of the Therapeutic Text Adventure (TTA) leverages a variable system of **Universe Parameters** to define the specific rule sets of each reality, which, in combination with universal **Metaconcepts**, enables system-agnostic game rules across its vast multiverse.

### The Export Variable Universe Parameters System

The "variable universe parameters system" refers to the comprehensive set of foundational characteristics defined for each distinct universe during its creation, primarily during the **Genesis Sequence**. These parameters act as the core, system-defining variables that the game's AI agents rely on to maintain local consistency.

**Key Universe Parameters (Variables):**

These parameters are defined collaboratively by the player and the **Universe Generator Agent (UGA)**, and are stored in the Neo4j knowledge graph as properties of the `Universe` node. They fundamentally define the physical and thematic constraints of that specific reality:

1.  **Physical Laws:** Details how fundamental forces like gravity, time, and space function (e.g., "Time flows backwards on certain days of the year," or "Standard physics apply").
2.  **Magic/Supernatural:** Specifies if magic is present, its rules, system, and limitations.
3.  **Technology Level:** Defines the technological advancement (e.g., "primitive," "medieval," "industrial," or "futuristic").
4.  **Inhabitants:** Describes the types of beings present (e.g., humans, mythical creatures, or new species).
5.  **Scope:** Determines the spatial size of the universe (e.g., a single planet, a solar system, or a pocket dimension).
6.  **Deities/Higher Powers:** Details the role and activity of any existing gods or powerful entities.

### Enabling System-Agnostic Game Rules

The core game engine and AI behavior remain consistent (system-agnostic) because the local, unique constraints (the *rules of physics and magic*) are separated from the overarching design principles (the *rules of narrative and ethics*).

#### 1. Decoupling Rules and Context

The TTA architecture achieves system-agnosticism by defining two distinct layers of rules:

| Rule Layer | Definition & Role | Example |
| :--- | :--- | :--- |
| **Global/System-Agnostic Rules** | **Metaconcepts** are high-level, guiding principles that apply universally to all AI agents and content generation across the entire multiverse. They ensure ethical conduct and narrative quality, regardless of the local reality. | "Prioritize Player Agency", "Maintain Narrative Consistency", "Avoid Harmful Stereotypes". |
| **Local/Variable Rules** | **Universe Parameters** define the specific, unique physical and thematic constraints (the "game system") of a single universe. | "Physical Laws: Gravity is much weaker than on Earth", "Magic System: Elemental magic only". |

#### 2. Dynamic Enforcement by AI Agents

The AI agents, powered by the Qwen2.5 Large Language Model and orchestrated by LangGraph, serve as the system-agnostic interpreter. When an agent needs to generate content or resolve an action, it uses both layers of rules simultaneously.

1.  **Contextual Input:** The agent retrieves the specific Universe Parameters (the local system rules) from the knowledge graph and includes them as **contextual information** in its prompt.
2.  **Global Constraint:** The agent is simultaneously constrained by the non-negotiable **Metaconcepts**. For example, the Narrative Generator Agent (NGA) always adheres to the "Maintain Narrative Consistency" metaconcept.
3.  **Resulting Behavior:** If a player attempts an action, the agent checks the action against the specific variables of the local universe. If the action is inconsistent with the local parameters (e.g., attempting advanced technology in a strictly "Medieval" universe), the agent denies or modifies the action while maintaining narrative coherence (a global metaconcept). This allows the core logic engine (the AI/LangGraph workflow) to operate identically across wildly diverse settings, promoting system **flexibility** and **extensibility**.

The result is that the game's high-level rules, like prioritizing the player's choices ("Prioritize Player Agency"), remain constant, while the local game mechanics (whether a sword swing or a laser blast is possible) are dynamically derived from the currently active Universe Parameters.

***

The way TTA manages its diverse realities is like designing a single computer program capable of running any game in history. The **Metaconcepts** are the core programming language and operating system—they ensure the software runs reliably and ethically everywhere. The **Universe Parameters** are the individual game cartridges (like *Chess* or *Space Invaders*); they provide the specific variable data (the board layout, the rules of movement, the physics engine) that tells the underlying system *what kind* of game to run right now, allowing the core software to stay constant while the experience changes infinitely.


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Docs/Planning/Tta-analysis/Research-extracts/System-agnostic-design]]
