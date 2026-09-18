# Studio Master Roadmap — minimal

> Studio-aligned 7-Phase Roadmap. Κάθε φάση ξεκλειδώνει μόνο όταν περάσει το αντίστοιχο Gate.

## Phase 1: Concept & RAG — 🟡 IN PROGRESS
- [x] Βιβλίο parsed (`full_text.md` + 1 chapters + `index.json`)
- [x] Engine selected & MCP defined (`technical/engine.md`)
- [ ] Claude ανάλυση: `entities.json`, `lore/bible.md`, `design/gdd/game-concept.md`
- [ ] Gate Check: `/gate-check concept` (PASS)
- [ ] Μετάβαση: `echo 'systems' > production/stage.txt`

## Phase 2: Systems Design — ⏳ LOCKED
- [ ] GDDs ανά σύστημα στο `design/gdd/<system>.md` (8 υποχρεωτικές ενότητες + Game Feel)
- [ ] Economy balance, formulas, progression curves
- [ ] Cross-review GDDs
- [ ] Gate Check: `/gate-check systems` (PASS)

## Phase 3: Technical Setup — ⏳ LOCKED
- [ ] `docs/architecture/architecture.md` + ADRs (≥3 `adr-*.md`)
- [ ] `control-manifest.md` + Input mapping
- [ ] Studio MCP server active (Godot/Unity/Unreal bridge)
- [ ] Gate Check: `/gate-check tech` (PASS)

## Phase 4: Pre-Production — ⏳ LOCKED
- [ ] `design/assets/entity-inventory.md` + `design/ux/*.md`
- [ ] Epics & User Stories στο `production/epics/`
- [ ] Prototype στο `prototypes/`
- [ ] Gate Check: `/gate-check pre-prod` (PASS)

## Phase 5: Production — ⏳ LOCKED
- [ ] Sprint loop: `/story-readiness` → `/dev-story` → `/story-done`
- [ ] Implementation υπό 3-tier coordination (Director -> Lead -> Specialist)
- [ ] Gate Check: `/gate-check production` (PASS)

## Phase 6: Polish & QA — ⏳ LOCKED
- [ ] Playtest reports (≥3 στο `production/playtests/`)
- [ ] Performance profiling & accessibility check
- [ ] Gate Check: `/gate-check polish` (PASS)

## Phase 7: Release — ⏳ LOCKED
- [ ] Release checklist & build deployment
- [ ] Final gate: `/gate-check release` (PASS)
