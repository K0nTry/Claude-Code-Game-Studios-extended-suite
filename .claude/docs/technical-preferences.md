# Technical Preferences

<!-- Populated by /setup-engine. Updated as the user makes decisions throughout development. -->
<!-- All agents reference this file for project-specific standards and conventions. -->

## Engine & Language

- **Engine**: Godot 4.6 (pinned per upstream README)
- **Language**: GDScript / C#
- **Rendering**: Godot 4.6 Renderer
- **Physics**: Godot 4.6 PhysicsServer3D

## Input & Platform

<!-- Written by /setup-engine. Read by /ux-design, /ux-review, /test-setup, /team-ui, and /dev-story -->
<!-- to scope interaction specs, test helpers, and implementation to the correct input methods. -->

- **Target Platforms**: [TO BE CONFIGURED — e.g., PC, Console, Mobile, Web]
- **Input Methods**: [TO BE CONFIGURED — e.g., Keyboard/Mouse, Gamepad, Touch, Mixed]
- **Primary Input**: [TO BE CONFIGURED — the dominant input for this game]
- **Gamepad Support**: [TO BE CONFIGURED — Full / Partial / None]
- **Touch Support**: [TO BE CONFIGURED — Full / Partial / None]
- **Platform Notes**: [TO BE CONFIGURED — any platform-specific UX constraints]

## Naming Conventions

- **Classes**: [TO BE CONFIGURED]
- **Variables**: [TO BE CONFIGURED]
- **Signals/Events**: [TO BE CONFIGURED]
- **Files**: [TO BE CONFIGURED]
- **Scenes/Prefabs**: [TO BE CONFIGURED]
- **Constants**: [TO BE CONFIGURED]

## Performance Budgets

- **Target Framerate**: [TO BE CONFIGURED]
- **Frame Budget**: [TO BE CONFIGURED]
- **Draw Calls**: [TO BE CONFIGURED]
- **Memory Ceiling**: [TO BE CONFIGURED]

## Testing

- **Framework**: [TO BE CONFIGURED]
- **Minimum Coverage**: [TO BE CONFIGURED]
- **Required Tests**: Balance formulas, gameplay systems, networking (if applicable)

## Forbidden Patterns

<!-- Add patterns that should never appear in this project's codebase -->
- [None configured yet — add as architectural decisions are made]

## Allowed Libraries / Addons

<!-- Add approved third-party dependencies here -->
- [None configured yet — add as dependencies are approved]

## Architecture Decisions Log

<!-- Quick reference linking to full ADRs in docs/architecture/ -->
- [No ADRs yet — use /architecture-decision to create one]

## Engine Specialists

<!-- Written by /setup-engine when engine is configured. -->
<!-- Read by /code-review, /architecture-decision, /architecture-review, and team skills -->
<!-- to know which specialist to spawn for engine-specific validation. -->

- **Primary**: Godot 4.6
- **Language/Code Specialist**: godot-gdscript-specialist / godot-csharp-specialist
- **Shader Specialist**: godot-shader-specialist
- **UI Specialist**: godot-gdscript-specialist
- **Additional Specialists**: See `.claude/agents/` directory for full roster
- **Routing Notes**: Engine specialists are Godot 4.6 native; see `docs/engine-reference/godot/VERSION.md`

### File Extension Routing

<!-- Skills use this table to select the right specialist per file type. -->
<!-- If a row says [TO BE CONFIGURED], fall back to Primary for that file type. -->

| File Extension / Type | Specialist to Spawn |
|-----------------------|---------------------|
| Game code (GDScript) | godot-gdscript-specialist |
| Game code (C#) | godot-csharp-specialist |
| Shader / material files | godot-shader-specialist |
| UI / screen files | godot-gdscript-specialist |
| Scene / prefab / level files | godot-specialist |
| Native extension / plugin files | godot-gdextension-specialist |
| General architecture review | Primary |

---

## Runtime Model Mapping

> **Rule: `model:` is the Anthropic label (Claude Code only). `difficulty:` is the provider-neutral capability hint (all runtimes).**
> The repo never hard-codes a concrete provider model ID.

| `model:` (Anthropic label) | `difficulty:` (provider-neutral) | Maps to any runtime as |
|---|---|---|
| `opus` | `strategic-reasoning` | Top-tier reasoning model (vision gates, direction) |
| `sonnet` | `applied-reasoning` | Mid-tier professional model (execution with judgment) |
| `haiku` | `focused-execution` | Fast/cheap model (narrow, high-volume tasks) |
| `sonnet` / `haiku` | `flexible` | Runtime picks either applied or focused tier |

- `model:` stays as-is for Claude Code sessions (`opus`, `sonnet`, `haiku`).
- `difficulty:` is added to every agent definition as a second frontmatter field.
- Any non-Anthropic runtime (GPT, Astra, Hermes, …) reads `difficulty:` to resolve its own model.
- No runtime is blocked by the absence of a specific Anthropic model name.
- **Godot version**: pinned to **4.6** per upstream README.
