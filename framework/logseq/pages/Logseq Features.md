# Logseq Features

**Advanced Logseq features used in TTA.dev knowledge base.**

## Overview

TTA.dev leverages advanced Logseq features for powerful knowledge management including queries, flashcards, whiteboards, and more.

## Core Features

### Queries
- **Custom Queries**: Filter and display TODO items, pages by tag, etc.
- **Property-Based Queries**: Query by properties like priority, status, type
- **Advanced Queries**: Complex multi-condition queries

**Example:**
```clojure
{{query (and (task TODO) [[#dev-todo]] (property priority high))}}
```

### Flashcards
- **Spaced Repetition**: Built-in SRS for learning
- **Card Creation**: Use `#card` tag for flashcards
- **Review System**: Automated review scheduling

**See:** [[Learning TTA Primitives]] for examples

### Whiteboards
- **Visual Diagrams**: Create visual documentation
- **Architecture Diagrams**: System architecture visualization
- **Flowcharts**: Process and workflow diagrams

**See:** [[Whiteboard - TTA.dev Architecture Overview]]

### Page Properties
- **Metadata**: Add structured metadata to pages
- **Tags**: Organize with hierarchical tags
- **References**: Bidirectional page linking

## Advanced Features

### Namespaces
- **Hierarchical Pages**: `TTA.dev/Guides/Getting Started`
- **Organization**: Group related pages
- **Navigation**: Auto-generated namespace views

### Journals
- **Daily Notes**: Automatic date-based journals
- **Session Logs**: Agent work sessions
- **Progress Tracking**: Daily TODO reviews

### Templates
- **Page Templates**: Reusable page structures
- **TODO Templates**: Standard TODO formats
- **Guide Templates**: Documentation templates

**See:** [[TODO Templates]]

## Configuration

### Enabled Features (config.edn)
```clojure
:feature/enable-journals? true
:feature/enable-flashcards? true
:feature/enable-whiteboards? true
:feature/enable-block-timestamps? true
```

## Related Pages

- [[Logseq Knowledge Base]] - KB system overview
- [[TTA.dev/Guides/Logseq Documentation Standards]] - Standards
- [[TODO Management System]] - TODO system

## Documentation

- `logseq/ADVANCED_FEATURES.md` - Feature guide
- `logseq/QUICK_REFERENCE_FEATURES.md` - Quick reference
- `logseq/FEATURES_SUMMARY.md` - Feature summary

## Tags

features:: logseq
type:: documentation

- [[Project Hub]]