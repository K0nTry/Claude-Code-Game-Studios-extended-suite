<p align="center">
  <h1 align="center">Claude Code Game Studios</h1>
  <p align="center"><em>Software Factory for Indie Game Development</em></p>
  <p align="center">
    <strong>You design the game. The Studio builds it.</strong>
  </p>
</p>

---

## What This Is

A **complete digital factory** for game development. Not just "agents." A system that takes your decisions and turns them into certified, tested, proven code — in sequence, without chaos.

---

## The Process: 4 Phases, Hard Gates

| Phase | What Happens | When You Advance |
|-------|--------------|------------------|
| 🔒 **ISOLATE** | Creates clean worktree. Spec locks. | Spec approved |
| 🔨 **BUILD** | Writes code against the locked spec. | Code complete |
| 📸 **PROVE** | **Evidence required:** screenshots, test results, metrics. No evidence → back to BUILD. | Evidence verified |
| 🚢 **SHIP** | Opens PR with proof. External reviewer (Greptile) scores 1–5. Loop BUILD→PROVE→SHIP until **5/5**. Max 3 loops, then escalate. | 5/5 score |

**No exceptions.** Without evidence, no merge happens.

---

## 3 Engines, 1 Studio

You pick **one** engine at setup. The Studio configures entirely around it.

| Engine | Lead | 15 Specialists (e.g.) |
|--------|------|----------------------|
| **Godot 4.6** | godot-specialist | GDScript, Shaders, GDExtension, Animation, Audio, Physics, UI, Networking… |
| **Unity 6** | unity-specialist | DOTS/ECS, Addressables, UI Toolkit, Shaders/VFX, Physics, Animation… |
| **Unreal Engine 5** | unreal-specialist | GAS, Blueprints, Replication, UMG/CommonUI, PCG, Animation, Camera… |

Total **49 agents** (3 Directors + 9 Leads + 22 Specialists + 15 Engine Specialists).

---

## 🚀 The 15 Engine Specialists — **Evolved**

These aren't just "engine experts." They're **evolved agents** with three differences that matter:

- 🎯 **Pinned Version Knowledge** — They know the exact engine version (Godot 4.6, Unity 6, UE5). They read `VERSION.md`, `breaking-changes.md`, `deprecated-apis.md` **before** writing a single line. No unverified APIs.
- 🔬 **Fable/Astra Lens Integrated** — Built-in Fable/Astra Lens for **adversarial verification**. Every delivery passes Stress Gate (abort on breaking change or deprecated pattern) and Closed Loop 4-pass verification.
- ⚙️ **Zero Generic Code** — They don't write generic code. They follow **strictly** the engine's best practices: GDScript static typing / C# partial classes / GDExtension ABI for Godot, Burst compilation / Addressables / asmdef graph for Unity, GAS / Blueprint→C++ migration / replication budgets for Unreal.

> They activate **only** when you pick their engine. The other 34 studio agents work engine-agnostic.

---

## Your Role

- Design (see the big picture)
- Decide (pick from options the agents give you)
- Verify (accept or reject evidence at PROVE)

Agents **ask before acting**. They don't decide for you.

---

## 📚 Book-to-Game — Integrated Extension

Not a separate tool. It's an **integrated extension** inside the Game Studio.

```bash
/book2game-prep "path/to/book.pdf" --out "./my-game"
```

**12 analytical cycles** run automatically and produce:

| Cycle | Output |
|-------|--------|
| 1–2 | Full text, RAG index, entities, archetype classification |
| 3–4 | Character psychology + voice fingerprints, relationship matrix |
| 5 | Pacing & tension curve from intensity/danger vocabulary |
| 6 | Branching graph: decision points with citations & line numbers |
| 7 | Player personas: distributed interest mapping with evidence |
| 8 | Aesthetic direction: leitmotif matrix, lighting/color script, audio direction |
| 9 | Knowledge graph: presence/co-occurrence matrices per chapter |
| 10 | Conflict & balance mapping from vocabulary (combat, resources, imbalances) |
| 11 | Expansion grammar + DDA with terminals from real entities |
| 12 | Engine selection + MCP bridge + Executive audit report |

**Result:** Complete `game-concept.md` + lore + art direction + audio architecture + balance specs. **Skips brainstorming entirely.**

Then: `/setup-engine` → `/art-bible` → `/map-systems` and continue normally.

---

## Quick Start

```bash
git clone https://github.com/K0nTry/Claude-Code-Game-Studios-extended-suite my-game
cd my-game
claude
/start
```

`/start` asks where you are (idea / concept / design / existing project / book) and gives you the exact next command.

---

## Philosophy

- **Collaborative, not autonomous** — You decide.
- **Evidence over trust** — PROVE phase = observed evidence.
- **Structure over chaos** — Pipeline, gates, traceability from concept to code.
- **Engine-native** — Deep integration, not generic wrappers.
- **Customizable** — Add/remove agents, change prompts, tune hooks. Template, not framework.

---

## Model-Agnostic

Works with **Claude, GPT, Gemini, local models** — whatever runs your runtime. Agents carry `difficulty` tiers (strategic / applied / focused) that are provider-neutral.

---

*Evolved from the original [Claude Code Game Studios](https://github.com/Donchitos/Claude-Code-Game-Studios) with Software Factory protocol, multi-engine specialists, Fable/Astra Lens, model-agnostic difficulty tiers, and book-to-game pipeline.*