<p align="center">
  <h1 align="center">Claude Code Game Studios</h1>
  <p align="center"><em>Software Factory for Indie Game Development</em></p>
  <p align="center">
    49 specialized AI agents operating as a coordinated studio from concept to shipped game.
  </p>
</p>

---

## What This Is

**Claude Code Game Studios** turns a single AI chat session into a full game development studio. Instead of one generalist AI trying to do everything, you get **49 specialized agents** organized exactly like a real indie studio — Directors who guard the vision, Department Leads who own their domains, and Specialists who execute with precision.

### The Core Idea

> You design the game. The Studio builds it.

You make every creative and strategic decision. The agents provide structure, expertise, and quality gates — they ask sharper questions, catch mistakes earlier, and keep the project oriented as it grows.

---

## Software Factory Pipeline

Every feature flows through a **four-phase factory** that guarantees quality:

`
ISOLATE  ->  BUILD  ->  PROVE  ->  SHIP
`

| Phase | What Happens | Gate |
|-------|--------------|------|
| **ISOLATE** | Fresh worktree/branch created. Spec locked. | Spec approved |
| **BUILD** | Implementation against the spec. | Code complete |
| **PROVE** | Evidence required: screenshots, metrics, test results. **No evidence = back to BUILD.** | Evidence reviewed |
| **SHIP** | PR with proof. Scored 5/5 by adversarial review. Loops until perfect. | 5/5 score |

**No exceptions.** A feature without PROVE evidence never reaches SHIP. Maximum 3 SHIP loops before escalation to you.

---

## Multi-Engine Support (Unreal / Unity / Godot)

This studio speaks **all three major engines** fluently. Each engine has its own complete agent set:

| Engine | Lead Specialist | Sub-Specialists (15 total per engine) |
|--------|----------------|----------------------------------------|
| **Godot 4.6** | godot-specialist | GDScript, Shaders, GDExtension, Animation, Audio, Input, Navigation, Networking, Physics, Rendering, UI |
| **Unity 6** | unity-specialist | DOTS/ECS, Shaders/VFX, Addressables, UI Toolkit, Animation, Audio, Input, Navigation, Networking, Physics, Rendering |
| **Unreal Engine 5** | unreal-specialist | GAS (Gameplay Ability System), Blueprints, Replication, UMG/CommonUI, PCG, Animation, Audio, Camera Systems |

You pick **one engine** during setup. The studio configures itself entirely around that choice — pinned version, verified API references, engine-specific best practices, and the right specialist agents activated.

---

## The 49 Agents — Studio Hierarchy

Agents are organized in three tiers, matching how real studios operate:

### Tier 1 — Directors (Strategic Reasoning)
*Set vision and direction from a blank page*
- **Creative Director** — Owns the creative vision, pillars, player fantasy
- **Technical Director** — Owns architecture, engine decisions, technical strategy
- **Producer** — Owns scope, schedule, cross-department coordination

### Tier 2 — Department Leads (Applied Reasoning)
*Build against decisions already made*
- Game Designer / Lead Programmer / Art Director
- Audio Director / Narrative Director / QA Lead
- Release Manager / Localization Lead

### Tier 3 — Specialists (Applied / Focused Execution)
*Execute against data the tiers above already produced*
- **Programming:** Gameplay / Engine / AI / Network / Tools / UI / Performance / DevOps / Security
- **Design:** Systems / Level / Economy / Live Ops / Prototyper
- **Art & Audio:** Technical Artist / Sound Designer / Writer / World Builder / UX Designer
- **QA & Ops:** QA Tester / Analytics Engineer / Accessibility Specialist / Community Manager

### Engine Specialists (15 per engine)
Dedicated agents that only activate when you choose their engine. They know the pinned version's APIs, breaking changes, and best practices — not generic knowledge.

---

## How 49 Agents Collaborate Without Conflicts

**Vertical Delegation** — Directors delegate to Leads, Leads delegate to Specialists. Clear ownership chains.

**Horizontal Consultation** — Same-tier agents consult each other but cannot make binding cross-domain decisions.

**Conflict Resolution** — Disagreements escalate up to the shared parent (Creative Director for design, Technical Director for technical).

**Change Propagation** — Cross-department changes coordinated by Producer.

**Domain Boundaries** — Agents never modify files outside their domain without explicit delegation.

**Fable/Astra Lens** — 34 agents carry a standards layer that enforces: effort control -> explicit "done" definition -> adversarial verification -> never stop at a plan.

---

## Key Capabilities

### Book-to-Game Pipeline
Feed it a book (PDF, EPUB, DOCX) -> **12 analytical cycles** -> complete game concept + lore + art direction + audio architecture + balance specs. Skips brainstorming entirely.

### 75 Slash Commands
Every workflow phase has a command: /brainstorm, /map-systems, /design-system, /create-epics, /create-stories, /dev-story, /story-done, /gate-check, /vertical-slice, /release-checklist, and 65 more.

### 14 Automated Hooks
Session lifecycle, commit validation, asset validation, agent audit trails, gap detection, compaction safety — all automatic.

### 11 Path-Scoped Rules
Coding standards enforced by file location: src/gameplay/** gets gameplay rules, src/ai/** gets AI rules, design/gdd/** gets design doc standards.

### Verification-Driven Development
Tests first, then implementation. Every story embeds its GDD requirement, ADR guidance, acceptance criteria, and test evidence path.

---

## Getting Started

### Prerequisites
- Git
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (npm install -g @anthropic-ai/claude-code)
- Recommended: jq and Python 3 (hooks fall back gracefully)

### First Session

`ash
git clone <this-repo> my-game
cd my-game
claude
/start
`

/start asks where you are — **no idea, vague concept, clear design, existing project, or a book to adapt** — and routes you to the exact right workflow.

### If You Have a Book

`ash
/book2game-prep "C:/path/to/book.pdf" --out "./my-game"
`

Produces a complete design/gdd/game-concept.md plus lore, art, audio, and balance specs in one command. Then continue with /setup-engine -> /art-bible -> /map-systems.

---

## Project Structure

`
CLAUDE.md                           # Master guide for agents
.claude/
  agents/                           # 49 agent definitions
  skills/                           # 75 slash commands
  hooks/                            # 14 automated hooks
  rules/                            # 11 path-scoped coding standards
  settings.json                     # Permissions, hook config
docs/
  agents/                           # Fable/Astra Lens (fable.xml + astra.xml per agent)
  engine-reference/                 # Version-pinned API docs (Godot/Unity/Unreal)
  architecture/                     # ADRs, TR Registry, Control Manifest
  standards/                        # Lens invocation standards
design/
  gdd/                              # Game Design Documents
  narrative/                        # Story, lore, dialogue
  levels/                           # Level designs
  ux/                               # UX specifications
src/                                # Game source code (engine-specific)
assets/                             # Art, audio, VFX, shaders, data
tests/                              # Unit, integration, performance, playtest
prototypes/                         # Throwaway prototypes (isolated)
production/                         # Sprints, milestones, releases, epics
`

---

## Philosophy

- **Collaborative, not autonomous** — Every agent asks before acting. You decide.
- **Verification over trust** — PROVE phase requires observed evidence, not claims.
- **Structure over chaos** — Factory pipeline, phase gates, traceability from concept to code.
- **Engine-native** — Not engine-agnostic. Deep integration with your chosen engine.
- **Customizable** — Add/remove agents, edit prompts, modify skills, tune hooks. It's a template, not a framework.

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

*Evolved from the original [Claude Code Game Studios](https://github.com/Donchitos/Claude-Code-Game-Studios) with Software Factory protocol, multi-engine specialists, Fable/Astra Lens, model-agnostic difficulty tiers, and book-to-game pipeline.*
