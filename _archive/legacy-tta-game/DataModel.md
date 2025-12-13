**Therapeutic Text Adventure (TTA) - Knowledge Graph Data Model**

**Version:** 1.0
**Date:** 2024-07-26

**Purpose:** This document provides the detailed technical specification for the Therapeutic Text Adventure (TTA) knowledge graph schema, implemented using Neo4j. It defines all node labels, relationship types, properties, constraints, and indexes. This specification serves as the definitive reference for developers, ensuring consistent data structure, facilitating efficient querying, and enabling seamless integration with the Python application layer, particularly through Pydantic data models.

**1. Design Principles:**

*   **Clarity:** Consistent naming conventions and clear definitions for all schema elements.
*   **Efficiency:** Schema optimized for common query patterns and data retrieval, minimizing redundancy.
*   **Flexibility:** Designed to accommodate new data, concepts, and relationships as the game evolves.
*   **Scalability:** Structure considers the graph's ability to expand while maintaining performance.
*   **Consistency:** Standardized data representation for reliable AI reasoning and game logic.
*   **Extensibility:** Easily allows for the addition of new node types, relationship types, and properties.

**2. Naming Conventions:**

*   **Node Labels:** `CamelCase` (e.g., `Character`, `Location`, `Universe`). The primary label representing the core type.
*   **Relationship Types:** `:UPPER_CASE_WITH_UNDERSCORES` (e.g., `:LOCATED_IN`, `:HAS_ITEM`, `:APPLIES_TO`).
*   **Properties:** `snake_case` (e.g., `character_id`, `creation_date`, `physical_laws`). This convention maps directly to standard Python attribute naming, facilitating Pydantic integration.

**3. Node Label Definitions:**

This section details each node label, its purpose, properties, constraints, and indexes.

---

**3.1 Core Concept Nodes**

These nodes form the fundamental building blocks of the knowledge graph, representing ideas, categories, and guidelines.

**3.1.1. `Concept`**

*   **Label:** `:Concept`
*   **Purpose:** Represents a general concept, idea, or entity. Often used as a base label for more specific entity types (e.g., a `Character` is also a `:Concept`).
*   **Properties:**
    *   `concept_id`: INTEGER (Primary Key, Indexed, Unique, Required) - Internal unique numerical ID.
    *   `name`: STRING (Indexed, Unique, Required) - Globally unique name for the concept.
    *   `definition`: STRING (Required) - Clear textual definition.
    *   `abstraction_level`: STRING (Optional, Controlled Vocabulary: ["Abstract", "Concrete", "Metaphorical"]) - Level of abstraction.
    *   `category`: STRING (Optional, Indexed, Controlled Vocabulary - see `:Category` node) - High-level classification.
*   **Constraints:** `concept_id` UNIQUE, `name` UNIQUE.
*   **Indexes:** `concept_id`, `name`, `category`, `abstraction_level`.

**3.1.2. `Metaconcept`**

*   **Label:** `:Metaconcept` (Implicitly also `:Concept`)
*   **Purpose:** Represents high-level principles governing game design and AI behavior.
*   **Properties:**
    *   `name`: STRING (Primary Key, Indexed, Unique, Required) - Unique name (e.g., "PrioritizePlayerAgency"). Inherits `concept_id`, `definition` etc. from `:Concept`.
    *   `description`: STRING (Required) - Detailed explanation of the principle.
    *   `rules`: LIST of STRING (Optional) - Actionable directives.
    *   `considerations`: LIST of STRING (Optional) - Nuances and points to consider.
    *   `priority`: INTEGER (Optional, Indexed) - Priority level for conflict resolution.
*   **Constraints:** `name` UNIQUE.
*   **Indexes:** `name`, `priority`.

**3.1.3. `Scope`**

*   **Label:** `:Scope` (Implicitly also `:Concept`)
*   **Purpose:** Defines the context or level (Multiverse, Universe, World, Region, Location, Character, Narrative, Systemic, etc.) to which concepts or rules apply.
*   **Properties:**
    *   `name`: STRING (Primary Key, Indexed, Unique, Required) - Unique name representing the scope level. Inherits `concept_id`, `definition` etc. from `:Concept`.
    *   `description`: STRING (Optional) - Explanation of the scope level.
*   **Constraints:** `name` UNIQUE.
*   **Indexes:** `name`.

**3.1.4. `Polarity`**

*   **Label:** `:Polarity` (Implicitly also `:Concept`)
*   **Purpose:** Represents positive, negative, or neutral connotations.
*   **Properties:**
    *   `name`: STRING (Primary Key, Indexed, Unique, Required, Controlled Vocabulary: ["Positive", "Negative", "Neutral"]) - The polarity value itself. Inherits `concept_id`, `definition` etc. from `:Concept`.
    *   `description`: STRING (Optional) - Explanation of the polarity value.
*   **Constraints:** `name` UNIQUE, `name` IN ["Positive", "Negative", "Neutral"].
*   **Indexes:** `name`.

**3.1.5. `Intensity`**

*   **Label:** `:Intensity` (Implicitly also `:Concept`)
*   **Purpose:** Represents the degree or strength (High, Medium, Low).
*   **Properties:**
    *   `name`: STRING (Primary Key, Indexed, Unique, Required, Controlled Vocabulary: ["High", "Medium", "Low"]) - The intensity level itself. Inherits `concept_id`, `definition` etc. from `:Concept`.
    *   `description`: STRING (Optional) - Explanation of the intensity level.
*   **Constraints:** `name` UNIQUE, `name` IN ["High", "Medium", "Low"].
*   **Indexes:** `name`.

**3.1.6. `Abstraction`**

*   **Label:** `:Abstraction` (Implicitly also `:Concept`)
*   **Purpose:** Represents the level of abstraction (Abstract, Concrete, Metaphorical).
*   **Properties:**
    *   `name`: STRING (Primary Key, Indexed, Unique, Required, Controlled Vocabulary: ["Abstract", "Concrete", "Metaphorical"]) - The abstraction level itself. Inherits `concept_id`, `definition` etc. from `:Concept`.
    *   `description`: STRING (Optional) - Explanation of the abstraction level.
*   **Constraints:** `name` UNIQUE, `name` IN ["Abstract", "Concrete", "Metaphorical"].
*   **Indexes:** `name`.

**3.1.7. `NarrativeRole`**

*   **Label:** `:NarrativeRole` (Implicitly also `:Concept`)
*   **Purpose:** Represents the function or archetype a Concept plays in a narrative.
*   **Properties:**
    *   `name`: STRING (Primary Key, Indexed, Unique, Required, Controlled Vocabulary: ["Protagonist", "Antagonist", "Mentor", "SettingElement", "PlotDevice", "Theme", "Symbol", ...]) - The narrative role itself. Inherits `concept_id`, `definition` etc. from `:Concept`.
    *   `description`: STRING (Optional) - Explanation of the narrative role.
*   **Constraints:** `name` UNIQUE, `name` IN [Defined List of Narrative Roles].
*   **Indexes:** `name`.

**3.1.8. `Category`**

*   **Label:** `:Category` (Implicitly also `:Concept`)
*   **Purpose:** Represents broad classifications for Concepts (Emotion, Character Trait, Gameplay Mechanic, etc.).
*   **Properties:**
    *   `name`: STRING (Primary Key, Indexed, Unique, Required, Controlled Vocabulary: ["Emotion", "CharacterTrait", "GameplayMechanic", "Recovery", "Knowledge", ...]) - The category name itself. Inherits `concept_id`, `definition` etc. from `:Concept`.
    *   `description`: STRING (Optional) - Explanation of the category.
*   **Constraints:** `name` UNIQUE, `name` IN [Defined List of Categories].
*   **Indexes:** `name`.

**3.1.9. `Universality`**

*   **Label:** `:Universality` (Implicitly also `:Concept`)
*   **Purpose:** Represents how broadly a Concept applies (Universal, Common, Specific, Unique).
*   **Properties:**
    *   `name`: STRING (Primary Key, Indexed, Unique, Required, Controlled Vocabulary: ["Universal", "Common", "Specific", "Unique"]) - The universality level itself. Inherits `concept_id`, `definition` etc. from `:Concept`.
    *   `description`: STRING (Optional) - Explanation of the universality level.
*   **Constraints:** `name` UNIQUE, `name` IN ["Universal", "Common", "Specific", "Unique"].
*   **Indexes:** `name`.

**3.1.10. `Valence`**

*   **Label:** `:Valence` (Implicitly also `:Concept`)
*   **Purpose:** Represents the emotional tone (Positive, Negative, Neutral), often used for emotions.
*   **Properties:**
    *   `name`: STRING (Primary Key, Indexed, Unique, Required, Controlled Vocabulary: ["Positive", "Negative", "Neutral"]) - The valence value itself. Inherits `concept_id`, `definition` etc. from `:Concept`.
    *   `description`: STRING (Optional) - Explanation of the valence value.
*   **Constraints:** `name` UNIQUE, `name` IN ["Positive", "Negative", "Neutral"].
*   **Indexes:** `name`.

**3.1.11. `Arousal`**

*   **Label:** `:Arousal` (Implicitly also `:Concept`)
*   **Purpose:** Represents the level of physiological/psychological activation (High, Medium, Low).
*   **Properties:**
    *   `name`: STRING (Primary Key, Indexed, Unique, Required, Controlled Vocabulary: ["High", "Medium", "Low"]) - The arousal level itself. Inherits `concept_id`, `definition` etc. from `:Concept`.
    *   `description`: STRING (Optional) - Explanation of the arousal level.
*   **Constraints:** `name` UNIQUE, `name` IN ["High", "Medium", "Low"].
*   **Indexes:** `name`.

**3.1.12. `ConstraintType`**

*   **Label:** `:ConstraintType` (Implicitly also `:Concept`)
*   **Purpose:** Categorizes Narrative Constraint concepts (Genre, World, Character, Plot, Concept).
*   **Properties:**
    *   `name`: STRING (Primary Key, Indexed, Unique, Required, Controlled Vocabulary: ["GenreConstraint", "WorldConstraint", "CharacterConstraint", "PlotConstraint", "ConceptConstraint"]) - The constraint type name. Inherits `concept_id`, `definition` etc. from `:Concept`.
    *   `description`: STRING (Optional) - Explanation of the constraint type.
*   **Constraints:** `name` UNIQUE, `name` IN [Defined List of Constraint Types].
*   **Indexes:** `name`.

**3.1.13. `DriverType`**

*   **Label:** `:DriverType` (Implicitly also `:Concept`)
*   **Purpose:** Categorizes Narrative Driver concepts (Conflict, Discovery, Relationship, Goal, Mystery, Choice).
*   **Properties:**
    *   `name`: STRING (Primary Key, Indexed, Unique, Required, Controlled Vocabulary: ["ConflictDriver", "DiscoveryDriver", "RelationshipDriver", "GoalDriver", "MysteryDriver", "ChoiceDriver"]) - The driver type name. Inherits `concept_id`, `definition` etc. from `:Concept`.
    *   `description`: STRING (Optional) - Explanation of the driver type.
*   **Constraints:** `name` UNIQUE, `name` IN [Defined List of Driver Types].
*   **Indexes:** `name`.

**3.1.14. `InteractionType`**

*   **Label:** `:InteractionType` (Implicitly also `:Concept`)
*   **Purpose:** Categorizes interactions between Beings (Communication, Cooperation, Conflict, Trade, Support, etc.).
*   **Properties:**
    *   `name`: STRING (Primary Key, Indexed, Unique, Required, Controlled Vocabulary: ["Communication", "Cooperation", "Conflict", "Trade", "Support", ...]) - The interaction type name. Inherits `concept_id`, `definition` etc. from `:Concept`.
    *   `description`: STRING (Optional) - Explanation of the interaction type.
*   **Constraints:** `name` UNIQUE, `name` IN [Defined List of Interaction Types].
*   **Indexes:** `name`.

**3.1.15. `SpaceType`**

*   **Label:** `:SpaceType` (Implicitly also `:Concept`)
*   **Purpose:** Categorizes concepts related to space (Cosmic, Galactic, Planetary, Local).
*   **Properties:**
    *   `name`: STRING (Primary Key, Indexed, Unique, Required, Controlled Vocabulary: ["Cosmic", "Galactic", "Planetary", "Local"]) - The space type name. Inherits `concept_id`, `definition` etc. from `:Concept`.
    *   `description`: STRING (Optional) - Explanation of the space type.
*   **Constraints:** `name` UNIQUE, `name` IN ["Cosmic", "Galactic", "Planetary", "Local"].
*   **Indexes:** `name`.

**3.1.16. `LocationType`**

*   **Label:** `:LocationType` (Implicitly also `:Concept`)
*   **Purpose:** Categorizes concepts related to locations (Natural, Urban, Rural, Building, Room, etc.).
*   **Properties:**
    *   `name`: STRING (Primary Key, Indexed, Unique, Required, Controlled Vocabulary: ["Natural", "Urban", "Rural", "Building", "Room", "Dungeon", "Shop", "Inn", "Temple", ...]) - The location type name. Inherits `concept_id`, `definition` etc. from `:Concept`.
    *   `description`: STRING (Optional) - Explanation of the location type.
*   **Constraints:** `name` UNIQUE, `name` IN [Defined List of Location Types].
*   **Indexes:** `name`.

**3.1.17. `ContextType`**

*   **Label:** `:ContextType` (Implicitly also `:Concept`)
*   **Purpose:** Categorizes the context of a situation or concept (Temporal, Social, Political, Economic, Environmental).
*   **Properties:**
    *   `name`: STRING (Primary Key, Indexed, Unique, Required, Controlled Vocabulary: ["Temporal", "Social", "Political", "Economic", "Environmental", ...]) - The context type name. Inherits `concept_id`, `definition` etc. from `:Concept`.
    *   `description`: STRING (Optional) - Explanation of the context type.
*   **Constraints:** `name` UNIQUE, `name` IN [Defined List of Context Types].
*   **Indexes:** `name`.

**3.1.18. `RelationType`**

*   **Label:** `:RelationType` (Implicitly also `:Concept`)
*   **Purpose:** Categorizes the *types* of relationships themselves (e.g., Causal, Sequential, Part-Whole, Influence). Used primarily as values for the `relation_type` property on `:RELATED_TO` relationships.
*   **Properties:**
    *   `name`: STRING (Primary Key, Indexed, Unique, Required, Controlled Vocabulary: ["Causal", "Sequential", "PartWhole", "Influence", "Similarity", "Opposition", "Containment", "Connection", ...]) - The relation type name. Inherits `concept_id`, `definition` etc. from `:Concept`.
    *   `description`: STRING (Optional) - Explanation of the relation type.
*   **Constraints:** `name` UNIQUE, `name` IN [Defined List of Relation Types].
*   **Indexes:** `name`.

---

**3.2 Game World Entity Nodes**

These nodes represent the concrete entities within the game world.

**3.2.1. `Player`**

*   **Label:** `:Player`
*   **Purpose:** Represents a human player of the game.
*   **Properties:**
    *   `player_id`: INTEGER (Primary Key, Indexed, Unique, Required) - Unique system ID.
    *   `username`: STRING (Indexed, Unique, Required) - Player's chosen display name.
    *   `email`: STRING (Optional, Indexed) - For account management (optional feature).
    *   `creation_date`: DATETIME (Required) - Account creation timestamp.
    *   `preferences`: MAP (Optional) - Player game settings (e.g., `{"theme": "Fantasy", "difficulty": "Normal"}`).
    *   `psychological_profile`: STRING (Optional, JSON String) - Sensitive data for potential therapeutic personalization (requires ethical handling & consent). Structure TBD.
    *   `trauma_triggers`: STRING (Optional, JSON String) - Sensitive data for content adaptation (requires ethical handling & consent). Structure TBD.
    *   `addiction_patterns`: STRING (Optional, JSON String) - Sensitive data for responsible design (requires ethical handling & consent). Structure TBD.
    *   `progress_data`: STRING (Optional, JSON String) - Flexible storage for quests, achievements, etc. (e.g., `{"questsCompleted": ["q1"], "achievements": ["Explorer"]}`).
    *   `needs_tutorial`: BOOLEAN (Optional, Default: true) - Does the player need the tutorial?
    *   `tutorial_step`: INTEGER (Optional) - Current tutorial step number.
*   **Constraints:** `player_id` UNIQUE, `username` UNIQUE.
*   **Indexes:** `player_id`, `username`, `email`.

**3.2.2. `Character`**

*   **Label:** `:Character` (Implicitly also `:Being`, `:Concept`)
*   **Purpose:** Represents player characters (PCs) and non-player characters (NPCs).
*   **Properties:**
    *   `character_id`: INTEGER (Primary Key, Indexed, Unique, Required) - Unique character ID.
    *   `name`: STRING (Indexed, Required) - In-game name (may not be unique).
    *   `description`: STRING (Optional) - Textual description.
    *   `species`: STRING (Optional, Controlled Vocabulary) - Character's species.
    *   `appearance`: STRING (Optional, JSON String) - Structured visual description. Schema TBD.
    *   `personality`: STRING (Optional, JSON String) - Structured personality (Big Five, shadow_self, character_type). Schema: `{"openness": FLOAT, "conscientiousness": FLOAT, ...}`.
    *   `skills`: LIST of STRING (Optional) - List of skill names (or skill IDs).
    *   `attributes`: STRING (Optional, JSON String) - Game-mechanic stats (strength, agility, etc.). Schema TBD.
    *   `motivations`: LIST of STRING (Optional) - List of driving motivations.
    *   `goals`: STRING (Optional) - Current primary objective.
    *   `background`: STRING (Optional) - Character's history.
    *   `faction`: STRING (Optional) - Faction name or ID.
    *   `role`: STRING (Optional, Controlled Vocabulary) - Narrative role (hero, mentor, etc.).
    *   `inventory`: LIST of STRING (Optional) - List of item IDs or names.
    *   `health`: INTEGER (Optional) - Current health points.
    *   `status`: STRING (Optional, Controlled Vocabulary) - Current state (alive, injured, etc.).
    *   `age`: INTEGER (Optional) - Character's age.
    *   `occupation`: STRING (Optional, Controlled Vocabulary) - Character's job.
*   **Constraints:** `character_id` UNIQUE.
*   **Indexes:** `character_id`, `name`, `faction`, `species`.

**3.2.3. `Universe`**

*   **Label:** `:Universe` (Implicitly also `:Concept`)
*   **Purpose:** Represents a unique parallel universe.
*   **Properties:**
    *   `universe_id`: INTEGER (Primary Key, Indexed, Unique, Required) - Unique universe ID.
    *   `name`: STRING (Indexed, Unique, Required) - Unique universe name.
    *   `description`: STRING (Optional) - General overview.
    *   `physical_laws`: STRING (Optional, JSON String or "Earth-like") - Governing physics. Schema TBD.
    *   `magic_system`: STRING (Optional, JSON String or "None") - Magic rules. Schema TBD.
    *   `technology_level`: STRING (Optional, Controlled Vocabulary) - General tech level.
    *   `history`: STRING (Optional, JSON String) - Key historical events/eras. Schema TBD.
    *   `creation_parameters`: STRING (Optional, JSON String) - Genesis Sequence inputs. Schema based on Genesis steps.
    *   `seed_concept`: STRING (Optional) - The initial concept provided by the player during Genesis.
*   **Constraints:** `universe_id` UNIQUE, `name` UNIQUE.
*   **Indexes:** `universe_id`, `name`.

**3.2.4. `World`**

*   **Label:** `:World` (Implicitly also `:Concept`)
*   **Purpose:** Represents a specific planet or realm within a Universe.
*   **Properties:**
    *   `world_id`: INTEGER (Primary Key, Indexed, Unique, Required) - Unique world ID.
    *   `name`: STRING (Indexed, Required) - World name (unique within its Universe).
    *   `description`: STRING (Optional) - General overview.
    *   `environment`: STRING (Optional, Controlled Vocabulary) - Dominant environment type.
    *   `geography`: STRING (Optional, JSON String) - Continents, oceans, etc. Schema TBD.
    *   `climate`: STRING (Optional, JSON String) - Climate zones, weather. Schema TBD.
    *   `inhabitants`: STRING (Optional) - General description of populations.
    *   `key_locations`: STRING (Optional, JSON String - LIST of location IDs/names) - Important locations.
    *   `resources`: STRING (Optional, JSON String - LIST of resource names) - Major resources.
    *   `dominant_cultures`: STRING (Optional - LIST of culture IDs/names) - Prevalent cultures.
    *   `dominant_languages`: STRING (Optional - LIST of language IDs/names) - Spoken languages.
    *   `political_system`: STRING (Optional) - Governing system description.
    *   `common_religions`: STRING (Optional - LIST of concept IDs/names) - Prevalent belief systems.
    *   `technology_level_description`: STRING (Optional) - Detailed tech description.
    *   `magic_system_description`: STRING (Optional) - Detailed magic description.
*   **Constraints:** `world_id` UNIQUE. Consider UNIQUE constraint on (`Universe`, `name`).
*   **Indexes:** `world_id`, `name`, `environment`.

**3.2.5. `Location`**

*   **Label:** `:Location` (Implicitly also `:Concept`)
*   **Purpose:** Represents a specific place within a World.
*   **Properties:**
    *   `location_id`: INTEGER (Primary Key, Indexed, Unique, Required) - Unique location ID.
    *   `name`: STRING (Indexed, Required) - Location name (unique within its World).
    *   `description`: STRING (Optional) - Detailed textual description for the player.
    *   `coordinates`: STRING (Optional) - Internal spatial reference (e.g., "x,y,z").
    *   `location_type`: STRING (Optional, Controlled Vocabulary) - City, Town, Forest, Building, Room, etc.
    *   `terrain`: STRING (Optional, Controlled Vocabulary) - Cobblestone, Dirt Path, Forest Floor, etc.
    *   `climate`: STRING (Optional, Controlled Vocabulary) - Sunny, Rainy, Temperate, etc.
    *   `architecture`: STRING (Optional, Controlled Vocabulary) - Medieval, Futuristic, Natural, etc.
    *   `security_level`: STRING (Optional, Controlled Vocabulary) - Safe, Dangerous, Restricted, etc.
    *   `population`: INTEGER (Optional) - Approximate population (for settlements).
    *   `governing_body`: STRING (Optional) - Authority in charge.
    *   `transportation`: LIST of STRING (Optional, Controlled Vocabulary) - Available transport (roads, trails, etc.).
    *   `social_classes`: STRING (Optional) - Description of social hierarchy.
*   **Constraints:** `location_id` UNIQUE. Consider UNIQUE constraint on (`World`, `name`).
*   **Indexes:** `location_id`, `name`, `location_type`.

**3.2.6. `Faction`**

*   **Label:** `:Faction` (Implicitly also `:Concept`)
*   **Purpose:** Represents organized groups (guilds, nations, cults, etc.).
*   **Properties:**
    *   `faction_id`: INTEGER (Primary Key, Indexed, Unique, Required) - Unique faction ID.
    *   `name`: STRING (Indexed, Unique, Required) - Unique faction name.
    *   `description`: STRING (Optional) - General overview.
    *   `goals`: STRING (Optional) - Primary objectives.
    *   `values`: LIST of STRING (Optional, Controlled Vocabulary) - Core principles.
    *   `beliefs`: STRING (Optional) - Core ideology description.
    *   `territory`: STRING (Optional) - Description or list of controlled locations/regions.
    *   `allies`: LIST of STRING (Optional) - List of allied faction IDs/names.
    *   `enemies`: LIST of STRING (Optional) - List of enemy faction IDs/names.
    *   `leader`: STRING (Optional) - Leader name or character ID.
    *   `structure`: STRING (Optional) - Internal organization description.
    *   `ideology`: STRING (Optional) - Detailed ideology description.
    *   `faction_type`: STRING (Optional, Controlled Vocabulary) - Kingdom, Guild, Order, etc.
    *   `size`: STRING (Optional, Controlled Vocabulary) - Small, Medium, Large, Regional, etc.
    *   `hierarchy`: STRING (Optional) - Detailed hierarchy description.
    *   `resources`: STRING (Optional, JSON String - LIST of resource names) - Controlled resources.
*   **Constraints:** `faction_id` UNIQUE, `name` UNIQUE.
*   **Indexes:** `faction_id`, `name`, `faction_type`.

**3.2.7. `Item`**

*   **Label:** `:Item` (Implicitly also `:Concept`)
*   **Purpose:** Represents tangible objects characters can interact with.
*   **Properties:**
    *   `item_id`: INTEGER (Primary Key, Indexed, Unique, Required) - Unique item ID.
    *   `name`: STRING (Indexed, Required) - Item name.
    *   `description`: STRING (Optional) - Textual description.
    *   `type`: STRING (Optional, Controlled Vocabulary) - Weapon, Potion, Key, Document, etc.
    *   `properties`: LIST of STRING (Optional, Controlled Vocabulary) - Enchanted, Sharp, Fragile, etc.
    *   `material`: STRING (Optional, Controlled Vocabulary) - Iron, Wood, Crystal, etc.
    *   `value`: FLOAT (Optional) - Economic value.
    *   `weight`: FLOAT (Optional) - Weight for inventory.
    *   `durability`: STRING (Optional, Controlled Vocabulary) - Fragile, Normal, Durable, etc.
    *   `history`: STRING (Optional) - Lore or background.
    *   `location`: STRING (Optional) - Current location ID/name or "Player Inventory".
    *   `rarity`: STRING (Optional, Controlled Vocabulary) - Common, Rare, Legendary, etc.
*   **Constraints:** `item_id` UNIQUE.
*   **Indexes:** `item_id`, `name`, `type`, `rarity`.

**3.2.8. `Event`**

*   **Label:** `:Event` (Implicitly also `:Concept`)
*   **Purpose:** Represents significant occurrences or actions within the timeline.
*   **Properties:**
    *   `event_id`: INTEGER (Primary Key, Indexed, Unique, Required) - Unique event ID.
    *   `name`: STRING (Indexed, Required) - Concise event name.
    *   `description`: STRING (Optional) - Detailed narrative description.
    *   `type`: STRING (Optional, Controlled Vocabulary) - Story Event, Combat, Discovery, etc.
    *   `location`: STRING (Optional) - Location ID/name where event occurred.
    *   `participants`: LIST of STRING (Optional) - List of character/faction IDs/names involved.
    *   `consequences`: LIST of STRING (Optional) - Textual summaries of outcomes.
    *   `start_time`: DATETIME (Required) - Precise start time.
    *   `end_time`: DATETIME (Optional) - Precise end time (null if ongoing).
    *   `duration`: STRING (Optional) - Textual duration (e.g., "a few hours").
    *   `time`: DATETIME (Optional) - *Deprecated? Use start_time/end_time instead for precision.* Consider removing if redundant.
*   **Constraints:** `event_id` UNIQUE, `start_time` EXISTS.
*   **Indexes:** `event_id`, `name`, `type`, `start_time`.

**3.2.9. `Culture`**

*   **Label:** `:Culture` (Implicitly also `:Concept`)
*   **Purpose:** Represents distinct cultural systems (values, practices).
*   **Properties:**
    *   `culture_id`: INTEGER (Primary Key, Indexed, Unique, Required) - Unique culture ID.
    *   `name`: STRING (Indexed, Unique, Required) - Unique culture name.
    *   `description`: STRING (Optional) - Detailed description.
    *   `values`: LIST of STRING (Optional) - Core cultural values.
    *   `practices`: STRING (Optional) - Common cultural practices.
*   **Constraints:** `culture_id` UNIQUE, `name` UNIQUE.
*   **Indexes:** `culture_id`, `name`.

**3.2.10. `Language`**

*   **Label:** `:Language` (Implicitly also `:Concept`)
*   **Purpose:** Represents languages spoken in the game world.
*   **Properties:**
    *   `language_id`: INTEGER (Primary Key, Indexed, Unique, Required) - Unique language ID.
    *   `name`: STRING (Indexed, Unique, Required) - Unique language name.
    *   `description`: STRING (Optional) - Language characteristics.
    *   `speakers`: STRING (Optional) - Description of typical speakers.
*   **Constraints:** `language_id` UNIQUE, `name` UNIQUE.
*   **Indexes:** `language_id`, `name`.

---

**3.3 Time Model Nodes**

These nodes specifically manage the representation of time.

**3.3.1. `Timeline`**

*   **Label:** `:Timeline`
*   **Purpose:** Represents a chronological record of events for a specific entity (Character, Location, Item, Relationship, etc.).
*   **Properties:**
    *   `timeline_id`: STRING (Primary Key, Indexed, Unique, Required) - Unique identifier (e.g., "character_123_timeline", "location_456_timeline").
    *   `creation_date`: DATETIME (Required) - When the timeline was initiated.
    *   `start_time`: DATETIME (Optional) - The earliest time point tracked on this timeline.
    *   `end_time`: DATETIME (Optional) - The latest time point tracked on this timeline.
    *   `description`: STRING (Optional) - Purpose of the timeline (e.g., "Timeline for Elara Meadowlight").
*   **Constraints:** `timeline_id` UNIQUE.
*   **Indexes:** `timeline_id`.

**3.3.2. `TimeSystem`**

*   **Label:** `:TimeSystem` (Implicitly also `:Concept`)
*   **Purpose:** Defines a specific system for measuring time within a Universe.
*   **Properties:**
    *   `timesystem_id`: STRING (Primary Key, Indexed, Unique, Required) - Unique identifier (e.g., "AethelgardianTime", "Gregorian"). Inherits `concept_id`, `name`, `definition` etc. from `:Concept`.
    *   `description`: STRING (Optional) - Explanation of the time system.
    *   `seconds_per_year`: INTEGER (Optional) - Base unit conversion.
    *   `days_per_month`: INTEGER (Optional) - Common calendar unit.
    *   `epoch`: STRING (Optional) - Reference point (e.g., "Year 0 marker").
*   **Constraints:** `timesystem_id` UNIQUE.
*   **Indexes:** `timesystem_id`.

**3.3.3. `TimePoint`**

*   **Label:** `:TimePoint`
*   **Purpose:** Represents a specific, discrete point in time within a `TimeSystem`.
*   **Properties:**
    *   `timepoint_id`: STRING (Primary Key, Indexed, Unique, Required) - Unique identifier.
    *   `name`: STRING (Optional) - Descriptive label (e.g., "The Great Cataclysm").
    *   `timestamp`: DATETIME (Indexed, Required) - Precise timestamp according to its linked `TimeSystem`. Must include timezone.
    *   `description`: STRING (Optional) - Context for the time point.
    *   `value`: STRING (Optional) - Human-readable representation (e.g., "Year 1050, Month 3, Day 12").
*   **Constraints:** `timepoint_id` UNIQUE, `timestamp` EXISTS.
*   **Indexes:** `timepoint_id`, `timestamp`.

**3.3.4. `TimeUnit`**

*   **Label:** `:TimeUnit` (Implicitly also `:Concept`)
*   **Purpose:** Represents units of time (Second, Hour, Day, Year, etc.).
*   **Properties:**
    *   `timeunit_id`: STRING (Primary Key, Indexed, Unique, Required) - Unique identifier (e.g., "Second", "Year"). Inherits `concept_id`, `name`, `definition` etc. from `:Concept`.
    *   `name`: STRING (Required) - Name of the unit.
    *   `length`: STRING (Required) - Duration definition (e.g., "60 seconds", "365.25 days").
*   **Constraints:** `timeunit_id` UNIQUE.
*   **Indexes:** `timeunit_id`, `name`.

**3.3.5. `TimeBranch`**

*   **Label:** `:TimeBranch`
*   **Purpose:** Represents a point where a timeline diverges into alternate realities (Future Feature).
*   **Properties:**
    *   `timebranch_id`: STRING (Primary Key, Indexed, Unique, Required) - Unique identifier.
    *   `name`: STRING (Optional) - Descriptive label.
    *   `description`: STRING (Required) - Reason for the timeline split.
*   **Constraints:** `timebranch_id` UNIQUE.
*   **Indexes:** `timebranch_id`.

**3.3.6. `TimeZone`**

*   **Label:** `:TimeZone` (Implicitly also `:Concept`)
*   **Purpose:** Represents geographical or world-specific time zones.
*   **Properties:**
    *   `timezone_id`: STRING (Primary Key, Indexed, Unique, Required) - Unique identifier (e.g., "UTC", "AethelgardStandardTime"). Inherits `concept_id`, `name`, `definition` etc. from `:Concept`.
    *   `name`: STRING (Required) - Name of the timezone.
    *   `offset`: STRING (Required) - Offset from a reference (e.g., "+00:00", "-05:00").
    *   `description`: STRING (Optional) - Geographical scope or details.
*   **Constraints:** `timezone_id` UNIQUE.
*   **Indexes:** `timezone_id`, `name`.

---

**3.4 Utility Nodes**

**3.4.1. `Metadata`**

*   **Label:** `:Metadata`
*   **Purpose:** A flexible node for attaching arbitrary key-value properties to relationships, avoiding schema clutter.
*   **Properties:**
    *   `key`: STRING (Required) - The key identifying the metadata property.
    *   `value`: STRING (Required) - The value of the metadata.
    *   `data_type`: STRING (Required, Controlled Vocabulary: ["STRING", "INTEGER", "FLOAT", "BOOLEAN", "DATETIME"]) - The intended data type of the `value`.
*   **Constraints:** None specific beyond property existence.
*   **Indexes:** Consider indexing `key` if specific metadata keys are frequently queried.

---

**4. Relationship Type Definitions:**

This section details the key relationship types connecting the nodes defined above.

*(Note: Due to the extensive list implied in the source documents, this section will focus on the most critical and frequently used relationship types. Others can be added iteratively as needed. The `:RELATED_TO` pattern with a `relation_type` property remains a flexible option for less common or highly specific connections.)*

**4.1 Hierarchical & Containment Relationships**

**4.1.1. `:CONTAINS`**

*   **Purpose:** Represents hierarchical containment (Universe contains World, World contains Location, Timeline contains Event, etc.).
*   **Source Labels:** `:Multiverse`, `:Universe`, `:World`, `:Region`, `:Location`, `:Faction`, `:Timeline`, `:Concept`, `:Item` (for containers)
*   **Target Labels:** `:Universe`, `:World`, `:Region`, `:Location`, `:Character`, `:Item`, `:Event`, `:Concept`, `:GenesisStep`
*   **Properties:**
    *   `strength`: FLOAT (Optional, 0.0-1.0) - Degree of containment.
    *   `order`: INTEGER (Optional) - Sequence order (e.g., for `:GenesisStep` within a `:Universe`).
*   **Direction:** Directed (Source CONTAINS Target).

**4.1.2. `:LOCATED_IN`**

*   **Purpose:** Specifically indicates that an entity resides within a spatial container (World, Region, Location).
*   **Source Labels:** `:World`, `:Region`, `:Location`, `:Character`, `:Item`, `:Event`
*   **Target Labels:** `:Universe`, `:World`, `:Region`, `:Location`
*   **Properties:**
    *   `start_time`: DATETIME (Optional) - When the entity entered the location.
    *   `end_time`: DATETIME (Optional) - When the entity left the location.
*   **Direction:** Directed (Source LOCATED_IN Target).

**4.1.3. `:PART_OF_REGION`**

*   **Purpose:** Connects a `:Location` to the `:Region`(s) it belongs to.
*   **Source Labels:** `:Location`
*   **Target Labels:** `:Region`
*   **Properties:** None typical.
*   **Direction:** Directed (Location PART_OF_REGION Region).

**4.2 Concept & Semantic Relationships**

**4.2.1. `:IS_A`**

*   **Purpose:** Represents subtype or classification relationships (e.g., World IS_A Concept, Courage IS_A Virtue).
*   **Source Labels:** `:Concept` (and its sub-labels like `:World`, `:Character`, etc.)
*   **Target Labels:** `:Concept` (and its sub-labels like `:Scope`, `:Category`, etc.)
*   **Properties:** None typical.
*   **Direction:** Directed (Source IS_A Target).

**4.2.2. `:RELATED_TO`**

*   **Purpose:** General-purpose relationship connecting Concepts, with the nature defined by properties.
*   **Source Labels:** `:Concept` (and its sub-labels)
*   **Target Labels:** `:Concept` (and its sub-labels)
*   **Properties:**
    *   `relation_type`: STRING (Required, Controlled Vocabulary from `:RelationType` nodes) - Specifies the relationship nature (e.g., "Causal", "Enablement", "Similarity", "Opposition", "PartWhole", "HasProperty").
    *   `strength`: FLOAT (Optional, 0.0-1.0) - Strength of the relationship.
    *   `description`: STRING (Optional) - Textual context.
*   **Direction:** Directed (Source RELATED_TO Target - direction has semantic meaning based on `relation_type`).

**4.2.3. `:IN_CATEGORY`**

*   **Purpose:** Links a `:Concept` to its `:Category`.
*   **Source Labels:** `:Concept` (and sub-labels)
*   **Target Labels:** `:Category`
*   **Properties:** None typical.
*   **Direction:** Directed (Concept IN_CATEGORY Category).

**4.2.4. `:APPLIES_TO`**

*   **Purpose:** Connects a `:Metaconcept` or `:Concept` to the `:Scope` where it is relevant.
*   **Source Labels:** `:Metaconcept`, `:Concept`
*   **Target Labels:** `:Scope`
*   **Properties:** None typical.
*   **Direction:** Directed (Source APPLIES_TO Target).

**4.2.5. `:HAS_NARRATIVE_ROLE`, `:HAS_POLARITY`, `:HAS_INTENSITY`, `:HAS_ABSTRACTION_LEVEL`, `:HAS_UNIVERSALITY`, `:HAS_VALENCE`, `:HAS_AROUSAL`, `:HAS_CONSTRAINT_TYPE`, `:HAS_DRIVER_TYPE`, `:HAS_INTERACTION_TYPE`, `:HAS_SPACE_TYPE`, `:HAS_LOCATION_TYPE`, `:HAS_CONTEXT_TYPE`**

*   **Purpose:** These relationships link a `:Concept` to its corresponding classification node (e.g., `:Concept` to `:NarrativeRole`, `:Concept` to `:Polarity`).
*   **Source Labels:** `:Concept` (and sub-labels)
*   **Target Labels:** `:NarrativeRole`, `:Polarity`, `:Intensity`, `:Abstraction`, `:Universality`, `:Valence`, `:Arousal`, `:ConstraintType`, `:DriverType`, `:InteractionType`, `:SpaceType`, `:LocationType`, `:ContextType` respectively.
*   **Properties:** None typical.
*   **Direction:** Directed (e.g., Concept HAS_NARRATIVE_ROLE NarrativeRole).

**4.3 Character & Faction Relationships**

**4.3.1. `:KNOWS`**

*   **Purpose:** Represents acquaintance between characters.
*   **Source Labels:** `:Character`
*   **Target Labels:** `:Character`
*   **Properties:**
    *   `strength`: FLOAT (Optional, 0.0-1.0) - Familiarity level.
    *   `description`: STRING (Optional) - Context of acquaintance.
    *   `relationship_type`: STRING (Optional, Controlled Vocabulary: "Friend", "Enemy", "Family", "Professional", "Rival", etc.) - More specific nature of the relationship. *Can evolve from KNOWS*.
    *   `since_date`: DATETIME (Optional) - When the relationship started.
*   **Direction:** Directed (Source KNOWS Target). Can be reciprocal.

**4.3.2. `:MEMBER_OF`**

*   **Purpose:** Indicates a `:Character` belongs to a `:Faction`.
*   **Source Labels:** `:Character`
*   **Target Labels:** `:Faction`
*   **Properties:**
    *   `role`: STRING (Optional) - Character's role within the faction.
    *   `start_date`: DATETIME (Optional) - When membership began.
*   **Direction:** Directed (Character MEMBER_OF Faction).

**4.3.3. `:HAS_INFLUENCE_IN`**

*   **Purpose:** Connects a `:Faction` to a `:Location` or `:Region`, indicating influence.
*   **Source Labels:** `:Faction`
*   **Target Labels:** `:Location`, `:Region`
*   **Properties:**
    *   `strength`: FLOAT (Required, 0.0-1.0) - Degree of influence.
    *   `influence_type`: STRING (Optional, Controlled Vocabulary: "Political", "Economic", "Military", "Cultural") - Nature of influence.
*   **Direction:** Directed (Faction HAS_INFLUENCE_IN Location/Region).

**4.3.4. `:CONTROLS`**

*   **Purpose:** Indicates direct control of a `:Location` or `:Organization` by a `:Faction` or `:Character`.
*   **Source Labels:** `:Faction`, `:Character`
*   **Target Labels:** `:Location`, `:Organization` (if Organization node exists)
*   **Properties:**
    *   `control_level`: STRING (Optional, Controlled Vocabulary: "Full", "Partial", "Nominal")
*   **Direction:** Directed (Source CONTROLS Target).

**4.4 Item & Inventory Relationships**

**4.4.1. `:HAS_ITEM` (Inventory)**

*   **Purpose:** Represents a character possessing an item in their inventory.
*   **Source Labels:** `:Character`
*   **Target Labels:** `:Item`
*   **Properties:**
    *   `quantity`: INTEGER (Optional, Default: 1) - Number of items held.
    *   `equipped`: BOOLEAN (Optional, Default: false) - Is the item currently equipped/wielded?
*   **Direction:** Directed (Character HAS_ITEM Item).

**4.4.2. `:LOCATED_AT` (Item Location)**

*   **Purpose:** Indicates where an item is located in the world (if not in an inventory).
*   **Source Labels:** `:Item`
*   **Target Labels:** `:Location`
*   **Properties:** None typical.
*   **Direction:** Directed (Item LOCATED_AT Location).

**4.5 Event & Timeline Relationships**

**4.5.1. `:HAS_TIMELINE`**

*   **Purpose:** Connects an entity (Character, Location, Item, Relationship) to its `:Timeline`.
*   **Source Labels:** `:Character`, `:Location`, `:Item`, potentially relationships themselves via intermediary nodes.
*   **Target Labels:** `:Timeline`
*   **Properties:** None typical.
*   **Direction:** Directed (Source HAS_TIMELINE Target).

**4.5.2. `:CONTAINS_EVENT`**

*   **Purpose:** Links a `:Timeline` to an `:Event` that occurred within it.
*   **Source Labels:** `:Timeline`
*   **Target Labels:** `:Event`
*   **Properties:**
    *   `impact_description`: STRING (Optional) - Summary of the event's impact on the timeline owner.
    *   `affected_properties`: LIST of STRING (Optional) - Properties changed by the event.
*   **Direction:** Directed (Timeline CONTAINS_EVENT Event).

**4.5.3. `:PRECEDES`**

*   **Purpose:** Defines chronological order between `:Event` nodes on a `:Timeline`.
*   **Source Labels:** `:Event`
*   **Target Labels:** `:Event`
*   **Properties:** None typical.
*   **Direction:** Directed (Event PRECEDES Event).

**4.5.4. `:INVOLVES`**

*   **Purpose:** Links an `:Event` to the `:Character` or `:Faction` entities that participated.
*   **Source Labels:** `:Event`
*   **Target Labels:** `:Character`, `:Faction`
*   **Properties:**
    *   `role`: STRING (Optional) - Role of the participant in the event (e.g., "instigator", "victim", "witness").
*   **Direction:** Directed (Event INVOLVES Participant).

**4.5.5. `:IMPACTS_BELIEF`**

*   **Purpose:** Links an `:Event` to a `:Character`, describing how the event affected the character's belief about a `:Concept`.
*   **Source Labels:** `:Event`
*   **Target Labels:** `:Character`
*   **Properties:**
    *   `concept_name`: STRING (Required) - Name of the Concept whose belief was impacted.
    *   `impact_description`: STRING (Required) - How the belief changed.
    *   `strength_change`: FLOAT (Optional) - Numerical change in belief strength.
    *   `justification`: STRING (Optional) - Reason for the belief change.
*   **Direction:** Directed (Event IMPACTS_BELIEF Character).

**4.6 Time System Relationships**

**4.6.1. `:USES_TIME_SYSTEM`**

*   **Purpose:** Connects a `:World` or `:Universe` to the `:TimeSystem` it uses.
*   **Source Labels:** `:World`, `:Universe`
*   **Target Labels:** `:TimeSystem`
*   **Properties:** None typical.
*   **Direction:** Directed (Source USES_TIME_SYSTEM Target).

**4.6.2. `:OCCURS_AT`**

*   **Purpose:** Links an `:Event` to a specific `:TimePoint` on a timeline.
*   **Source Labels:** `:Event`
*   **Target Labels:** `:TimePoint`
*   **Properties:** None typical.
*   **Direction:** Directed (Event OCCURS_AT TimePoint).

**4.7 Utility Relationships**

**4.7.1. `:HAS_METADATA`**

*   **Purpose:** Connects a relationship instance (via an intermediary node if needed, or directly if Neo4j version supports relationship properties well) to a `:Metadata` node.
*   **Source Labels:** Any Relationship (or intermediary node)
*   **Target Labels:** `:Metadata`
*   **Properties:** None typical.
*   **Direction:** Directed.

---

**5. Pydantic Integration:**

The Neo4j schema defined above is designed for seamless integration with Pydantic models in the Python application layer.

*   **Mapping:**
    *   **Node Label** (`CamelCase`) -> **Pydantic Class Name** (`CamelCase`, inheriting from `pydantic.BaseModel`).
    *   **Property Name** (`snake_case`) -> **Pydantic Field Name** (`snake_case`).
    *   **Neo4j Data Type** -> **Python/Pydantic Type Hint**:
        *   `INTEGER` -> `int`
        *   `FLOAT` -> `float`
        *   `STRING` -> `str`
        *   `BOOLEAN` -> `bool`
        *   `DATETIME` -> `datetime` (from Python's `datetime` module)
        *   `LIST of STRING` -> `List[str]` (from Python's `typing` module)
        *   `MAP` -> `Dict` (from Python's `typing` module, likely `Dict[str, Any]` or more specific)
        *   `STRING (JSON String)` -> `str` (in Neo4j), parsed into a nested Pydantic model or `Dict` in Python.
    *   **Required/Optional** -> **Pydantic Field Definition**:
        *   Required: `field_name: type` or `field_name: type = Field(...)`
        *   Optional: `field_name: Optional[type] = None` or `field_name: Optional[type] = Field(None, ...)`
    *   **Controlled Vocabulary** -> Use `Literal` from `typing` or `Enum` from `enum` in Pydantic models for validation.

*   **Example Pydantic Model (`Character`):**

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class CharacterPersonality(BaseModel):
    openness: Optional[float] = Field(None, ge=0.0, le=1.0)
    conscientiousness: Optional[float] = Field(None, ge=0.0, le=1.0)
    extraversion: Optional[float] = Field(None, ge=0.0, le=1.0)
    agreeableness: Optional[float] = Field(None, ge=0.0, le=1.0)
    neuroticism: Optional[float] = Field(None, ge=0.0, le=1.0)
    shadow_self: Optional[str] = None
    character_type: Optional[str] = None # Consider Enum later

class Character(BaseModel):
    character_id: int = Field(..., description="Unique character ID.")
    name: str = Field(..., description="In-game name.")
    description: Optional[str] = Field(None, description="Textual description.")
    species: Optional[str] = Field(None, description="Character's species.")
    # appearance: Optional[Dict[str, Any]] = Field(None, description="Structured visual description.") # Parse from JSON string
    appearance_json: Optional[str] = Field(None, alias="appearance", description="Structured visual description (JSON string).") # Store as JSON string
    # personality: Optional[CharacterPersonality] = Field(None, description="Structured personality.") # Parse from JSON string
    personality_json: Optional[str] = Field(None, alias="personality", description="Structured personality (JSON string).") # Store as JSON string
    skills: Optional[List[str]] = Field(None, description="List of skill names.")
    # attributes: Optional[Dict[str, Any]] = Field(None, description="Game-mechanic stats.") # Parse from JSON string
    attributes_json: Optional[str] = Field(None, alias="attributes", description="Game-mechanic stats (JSON string).") # Store as JSON string
    motivations: Optional[List[str]] = Field(None, description="List of driving motivations.")
    goals: Optional[str] = Field(None, description="Current primary objective.")
    background: Optional[str] = Field(None, description="Character's history.")
    faction: Optional[str] = Field(None, description="Faction name or ID.")
    role: Optional[str] = Field(None, description="Narrative role.") # Consider Enum later
    inventory: Optional[List[str]] = Field(None, description="List of item IDs or names.") # Assuming IDs/names stored as strings
    health: Optional[int] = Field(None, description="Current health points.")
    status: Optional[str] = Field(None, description="Current state.") # Consider Enum later
    age: Optional[int] = Field(None, description="Character's age.")
    occupation: Optional[str] = Field(None, description="Character's job.") # Consider Enum later

    class Config:
        populate_by_name = True # Allows using Neo4j property names directly

    # Add validators or parsers for JSON string fields (appearance_json, personality_json, attributes_json) if needed
    # to convert them to/from Python dicts/nested models during application logic.
```

*   **Data Flow:** Data retrieved from Neo4j (often as dictionaries) can be directly validated and parsed into Pydantic models. Data created or modified in the Python application using Pydantic models can be easily serialized into formats suitable for Neo4j storage (e.g., dictionaries for properties).

---

**6. Data Examples & Diagrams:**

*(This section would include illustrative Cypher code snippets for creating nodes/relationships and visual diagrams of the schema, added iteratively during development).*

---

---
**Logseq:** [[TTA.dev/_archive/Legacy-tta-game/Datamodel]]
