# Systems Index

> Πίνακας όλων των συστημάτων — priority + dependencies

| System | Κατηγορία | Priority | Dependencies | Status |
|--------|-----------|----------|--------------|--------|
| Narrative / Dialogue | Narrative | MVP | — | Draft |
| World / Exploration | Core | MVP | Narrative | Draft |
| Choice & Consequence | Core | MVP | Narrative | Draft |
| Character Progression | Progression | Vertical Slice | Narrative | Draft |
| Puzzle / Challenge | Gameplay | Vertical Slice | World | Draft |
| Audio / Atmosphere | Audio | Vertical Slice | — | Draft |
| Save / Persistence | Persistence | MVP | — | Draft |
| UI / UX | UI | MVP | — | Draft |

## Dependency Map

```
Foundation: Save, UI
    ↓
Core: Narrative, World, Choice
    ↓
Feature: Progression, Puzzle
    ↓
Presentation: Audio
```

## Recommended Design Order

1. Narrative → 2. World → 3. Choice → 4. Save/UI → 5. Progression → 6. Puzzle → 7. Audio

## Circular Dependencies

_Καμία προς το παρόν._

## High-Risk Systems

- Narrative branching (scope explosion) → guardrails: max 3 branches ανά κεφάλαιο στο MVP
