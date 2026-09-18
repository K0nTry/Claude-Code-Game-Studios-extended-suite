# Project Roadmap: book2game

## Phases 1–12 [COMPLETED]
- [x] G1–G16: Skill install, 12-cycle pipeline, production-grade canon, 49 projections, BM25, OCR, MCP
- See `plans/` for per-phase detail. All gates PASSED via `validate_output.py`.

## Phase 13: Runtime Validation Layer [COMPLETED]
- [x] `scripts/whitebox_runner.py` — detect highest-risk edge (choice-tree + tension-curve), seed=42 deterministic simulate, `benchmarks/whitebox-validation.json`
- [x] `contracts/stage-contracts.json` — 6-stage ownership/inputs/outputs/handoff_gate; copied into output as `contracts/stage-contracts.json`
- [x] Anti-overclaim quarantine — scan derived artifacts for 99.8%/Nash/Metacritic/d30 patterns → `canon/unresolved-ambiguities.json`
- [x] Integrate Phase 13 into `parse_book.py` (calls: `write_contract_snapshot` → `quarantine_overclaims` → `run_whitebox_validation`)
- [x] `scripts/validate_output.py` — Phase 13 gate checks (non-fatal) integrated
- [x] E2E verify: `python scripts/parse_book.py tests/fixtures/synthetic_test_book.txt --out C:\Temp\book2game-phase13-synth` → GATE PASS (3 pre-existing cosmetic NO_EVIDENCE warnings, Phase 13 artifacts OK)

## Phases 14b / 15 / 16a / 15b [COMPLETED — from `plans/evidence-integration.md`]
- [x] Phase 15: Data Backbone — `schemas/*.schema.json`, `knowledge/{StyleDNA, foreshadowing, WorldMuncher, progress-state}`
- [x] Phase 14b: Limited Export Layer — `exports/yarn/` + `exports/nodes/` (flag-restricted)
- [x] Phase 16a: Minimal State Simulation — `simulation/` (choice-tree → binary card-mode)
- [x] Phase 15b: Theory-Lenses — 3 optional validators (South Park causality, Character Arc, Hero's Journey)

## Completed Summary
- [x] Phase 13: Runtime Validation Layer (whitebox, contracts, anti-overclaim)
- [x] Phase 15: Data Backbone — schemas + knowledge/
- [x] Phase 14b: Limited Export Layer — exports/yarn & exports/nodes
- [x] Phase 16a: Minimal State Simulation
- [x] Phase 15b: Theory-Lenses

---

# Phase 17: Preparation Package — Canonical Agent-Ready Handoff

> **STATUS: DESIGN LOCKED (Plan³ loop completed) — Phase 1 & Phase 3 COMPLETED (Tests / Final Verification passed)**
> Source of truth: AnyDoc analysis (firecrawl/anydoc) + Claude Code Game Studios workflow study (Donchitos/Claude-Code-Game-Studios) + Plan³ loop (maximum result / minimum work).
> Phase 1 (Package Foundations) & Phase 3 (Tests / Final Verification) fully implemented and validated (`python -m unittest discover tests` → 9/9 PASS, E2E validation PASS).
> This section is the canonical master plan for Phase 17. `active.md` mirrors its status.

## 17.1 — Τελικός Στόχος

Το `book2game` παράγει ένα **canonical, self-describing, agent-ready preparation package** από το source material όπου:
- όλα τα απαραίτητα στοιχεία υπάρχουν,
- συνδέονται μεταξύ τους μέσω UUIDs/hashes,
- είναι εύκολα discoverable από οποιονδήποτε CCGS agent με μία ανάγνωση,
- κάθε agent ξέρει ποιο αρχείο είναι authoritative χωρίς να ψάχνει,
- κάθε derived element trace-άρεται πίσω στο source paragraph,
- το package περνάει validation πριν το handoff,
- το handoff boundary προς Claude Code Game Studios είναι σαφές και non-invasive (copy + Read, όχι write στο CCGS src).

Αντικαθιστά το `PDF → full_text.md` mental model με:
`raw source → extraction → normalized IR → organized knowledge package → validation → CCGS handoff`

## 17.2 — Υπάρχουσα Κατάσταση

**Ισχυρά (μένουν ως έχουν):**
- 6-stage contracts (`contracts/stage-contracts.json`) με ownership/inputs/outputs/handoff_gate
- Epistemic model `CANON / DERIVED / OPEN_SPACE` (`standards/epistemic-model.md`) + `immutable-kernel-spec.md` + `verification-rules.md`
- 49 projections (`views/projections/<agent>/IMMUTABLE_KERNEL.md`) self-contained
- 12-cycle derived layer (Cycles 5–12) evidence-grounded
- `source/full_text.md` + `chapters/chNN-*.md` + `index.json` + `source/paragraph-hashes.json` + `audit/provenance.json`

**Αδυναμίες που λύνει το Phase 17:**
- 11+ διάσπαρτες τοποθεσίες (`source/`, `canon/`, `design/`, `lore/`, `benchmarks/`, `technical/`, `views/`, `audit/`, `contracts/`) χωρίς single entry — information archaeology για agent με `Read/Glob/Grep` μόνο (no Bash)
- Κανένα manifest που να δηλώνει `authoritative:true/false` — κίνδυνος duplicated/contradictory context (π.χ. `entities.json` vs `canon/entities.json` vs projection copy)
- Assets/tables του βιβλίου πετιούνται (κανένα `source/assets/`, `source/tables.json`)
- `full_text.md` non-deterministic (διαφέρει με/χωρίς pandoc) — χωρίς IR anchor
- Κανένα single handover verdict — ο CCGS agent πρέπει να τρέξει `validate_output.py` μόνος του
- Derived → Canon trace απαιτεί grep, όχι 1-hop reverse index

## 17.3 — Τελικό Architecture (Target)

```
raw source (pdf/epub/docx/txt/md)
  → [Stage 01] Detection (inline helper) + Normalized IR (blocks/tables/assets/notes + hashes)
  → [Stage 02] Canon Layer (entities/relationships/world, UUIDs + source_offsets)
  → [Stage 03] Derived Layer (Cycles 5–12, method+confidence+source_uuids ή open_space)
  → [Stage 04] PACKAGE INDEX  ← ΝΕΟ LAYER (μόνο αυτό προστίθεται)
       _manifest.json   (machine truth — authoritative declaration)
       _catalog.md      (human/agent one-Read — thin view του manifest)
       _handover.json   (gate verdict — thin)
  → [Stage 05] Validation Gate (επέκταση validate_output.py)
  → [Stage 06] HANDOFF: copy my-game/ → <ccgs>/design/source-material/<book>/ → CCGS Read
```

**Φυσική δομή output (additive, χωρίς μετακίνηση υπαρχόντων):**
```
my-game/                          ← handoff package (self-contained)
├── _manifest.json                ← ΝΕΟ (P1)
├── _catalog.md                   ← ΝΕΟ (P1, thin)
├── _handover.json                ← ΝΕΟ (P1, thin)
├── source/
│   ├── document_ir.json          ← ΝΕΟ (P1) — blocks/tables/assets/notes + hashes
│   ├── full_text.md              ← rendered από IR (deterministic, GFM)
│   ├── paragraph-hashes.json     ← existing, μένει
│   ├── chapters/chNN-*.md        ← derived από IR
│   ├── index.json                ← derived από IR
│   ├── assets/                   ← conditional (μόνο αν υπάρχουν)
│   └── tables.json               ← conditional (GridBuilder, μόνο αν υπάρχουν)
├── canon/                        ← AUTHORITATIVE (μένει)
├── design/ lore/ benchmarks/ technical/  ← DERIVED (μένουν, manifest τα χαρακτηρίζει)
├── views/projections/<agent>/    ← VIEW (όχι source, δηλώνεται ρητά)
├── audit/                        ← provenance + verification-report (επέκταση 1 field)
└── contracts/                    ← stage-contracts.json
```

## 17.4 — Νέα Package Artifacts

### `_manifest.json` — Machine truth (AUTHORITATIVE για discovery)
- Single source of truth: τι υπάρχει, πού, τι είναι authoritative, dependencies
- Κάθε entry: `{path, tier: 0|1|2, authoritative: bool, kind, count, canonical_source?}`
- Views δηλώνονται `authoritative:false` + `canonical_source: "canon/entities.json"`
- Minimal links: επαναχρησιμοποίηση υπάρχοντος `source_uuids` — όχι νέο links array
- Schema: `package_version, source:{file, sha256, ir}, artifacts:[], handoff:{status, report}`

### `_catalog.md` — Human/Agent one-Read (thin view του manifest, <800 tokens)
- Rendered από `_manifest.json` — δεν είναι independent source
- Agent κάνει `Read _catalog.md` → ξέρει αμέσως:
  `Χαρακτήρες → canon/entities.json (AUTHORITATIVE, 48) | Κεφάλαια → source/chapters/ | Πίνακες → source/tables.json | Για τον ρόλο σου → views/projections/<agent>/IMMUTABLE_KERNEL.md`
- Αποτρέπει Glob/ψάξιμο όλου του package — σέβεται CCGS `context-management.md` (3–5k tokens/section)

### `_handover.json` — Gate verdict (thin, ~20 γραμμές)
- `{status: PASS|NEEDS_ATTENTION|FAIL, checks:[], quarantined:[], next_action: "cp -r my-game/ <ccgs>/design/source-material/<book>/ && Read _catalog.md"}`
- Rendered από validation — CCGS agent δεν χρειάζεται να τρέξει `validate_output.py`
- `NEEDS_ATTENTION` για NeedsOcr / whitebox robustness <0.6 (non-fatal, με reason)

### `source/document_ir.json` — Normalized IR (νέο authoritative anchor)
- `Document { blocks:[{type, text, style, page, hash}], tables:[{grid}], assets:[{id, type, bytes_ref}], notes:[] }`
- Κάθε block έχει SHA-256 hash — άγκυρα για `paragraph-hashes.json` + `source_offsets`
- `source/full_text.md` παράγεται από IR (deterministic GFM: escapes, anchors, tables) — όχι απευθείας από pandoc
- Detection (magic bytes: %PDF, PK\x03\x04, D0CF11E0) ως inline helper μέσα στο ίδιο module — όχι ξεχωριστό αρχείο
- Assets/tables conditional: δημιουργούνται μόνο αν το IR τα βρει — όχι άδειοι φάκελοι

## 17.5 — Single Authority Model

- Κάθε fact έχει **ένα** authoritative file. Όλα τα άλλα το αναφέρουν με UUID+path, δεν το ξαναγράφουν.
- `canon/entities.json` = AUTHORITATIVE για characters/locations/objects
- `views/projections/<agent>/canon.projection.json` = VIEW (`authoritative:false`) — ίδιο `_uuid`, όχι νέα UUIDs
- `_manifest.json` είναι το μόνο μέρος που δηλώνει `authoritative:true/false` — κανένα άλλο artifact δεν διεκδικεί authority
- Κανόνας: δύο files δεν διεκδικούν ίδιο `kind` ως authoritative → validation FAIL

## 17.6 — Discovery Model (για CCGS agent με Read/Glob/Grep, no Bash)

- **L1 — One Read:** `Read _catalog.md` → πλήρης χάρτης σε <1k tokens
- **L2 — Machine:** `Grep '"authoritative": true' _manifest.json` → όλες οι πηγές
- **L3 — Scoped:** `Glob canon/*` / `Glob source/chapters/*` μόνο αφού το catalog είπε πού
- Οδηγία σε `views/projections/<agent>/README.md`: `Διάβασε πρώτα _catalog.md, μετά IMMUTABLE_KERNEL.md, μετά canon/entities.json — μην κάνεις Glob όλο το package`
- Χωρίς per-folder `_index.json` — το manifest αρκεί

## 17.7 — Provenance / Traceability

- Υπάρχον μοντέλο μένει: `paragraph-hashes.json` + `source_offsets[].hash` + `epistemic-model` + `audit/provenance.json`
- Ενίσχυση — ελάχιστη:
  - IR block → hash (νέο anchor)
  - Derived → Canon: `source_uuids + method + confidence` **επιβάλλεται** (missing → quarantine σε `canon/unresolved-ambiguities.json`)
  - Reverse index: `audit/provenance.json` παίρνει **ένα** νέο field `reverse: { "<uuid>": ["sha256:..."] }` → 1 hop από derived node στο paragraph, χωρίς νέο αρχείο
  - View → Canon: ίδιο `_uuid`, κανένα νέο

## 17.8 — Validation / Handover Gate

Επέκταση `contracts/stage-contracts.json` (Stage 01 gate) + `scripts/validate_output.py` — όχι νέο σύστημα. Νέο **Handover Gate** ως Stage 07:

**PASS αν:**
1. `_manifest.json` valid + version OK
2. `source/document_ir.json` exists + `file_hash == sha256(document_ir.json)`
3. Κάθε `authoritative:true` υπάρχει + valid JSON
4. Κάθε `authoritative:false` έχει έγκυρο `canonical_source`
5. Κανένα canon χωρίς `_uuid`/`source_offsets`+hash
6. Κανένα derived χωρίς `method+confidence+source_uuids` ή `open_space+reason`
7. Κανένα duplicated authoritative kind
8. NeedsOcr (IR blocks < N αλλά source pages > M) → `NEEDS_ATTENTION` (non-fatal, με `pages`+`reason` σε `_handover.json`)
9. Whitebox robustness <0.6 → `NEEDS_ATTENTION` (ήδη)
10. Ό,τι απέτυχε → `canon/unresolved-ambiguities.json` + `_handover.quarantined[]`

Αποτέλεσμα → `_handover.json`. **Handoff boundary:** `cp -r my-game/ <ccgs>/design/source-material/<book>/` → CCGS agents κάνουν `Read _catalog.md` → `/start` ή `/brainstorm` → `game-concept.md` παράγεται από CCGS, όχι από book2game. Καμία εγγραφή σε `src/` ή `design/gdd/` του CCGS (σέβεται `No Unilateral Cross-Domain Changes` + `Ask before Write`).

## 17.9 — Τι Παίρνουμε από AnyDoc

| Ιδέα | Θέση | Προτεραιότητα |
|---|---|---|
| Content-based detection (magic bytes) | inline στο `document_ir.py` (30 γραμμές) | P0 |
| Document IR (`blocks/notes/assets/tables`) | `source/document_ir.json` — θεμέλιο | P0 |
| Conditional assets/tables | `source/assets/`, `source/tables.json` | P0 |
| Typed NeedsOcr (exit 3 → NEEDS_ATTENTION) | `_handover.json` | P0 |
| Deterministic GFM rendering (escapes, anchors, tables) | `source/full_text.md` από IR | P1 |
| Snapshot tests ανά format | `tests/fixtures/` + `tests/snapshots/` | P1 |

Χωρίς IR, το manifest δεν έχει τι να δηλώσει ως authoritative — το AnyDoc layer είναι **προϋπόθεση** για το Knowledge Package.

## 17.10 — Τι Απορρίψαμε (Unnecessary Complexity — Plan³)

| Να ΜΗΝ γίνει | Δικαιολόγηση (CCGS workflow) |
|---|---|
| Rust rewrite / pdf-inspector / WASM | Python stdlib + determinism αρκεί, κόστος >> όφελος |
| Υποστήριξη ppt/xls/odp/csv | Εκτός scope `book → game` |
| Auto-συγγραφή `design/gdd/game-concept.md` / `game-pillars.md` | Δουλειά CCGS agents (`/brainstorm` + `creative-director` Question→Options, User=Creative Director) |
| `design/seeds/concept-seeds.json` | Διαγράφηκε στο Plan³ — παραβιάζει User ως decision maker, δεν αποδεικνύεται αναγκαίο |
| Graph DB / Vector DB / embeddings | CCGS χρησιμοποιεί Grep/Glob + BM25 (ήδη), non-deterministic, εκτός epistemic model |
| Auto-import που γράφει σε CCGS `src/`/`design/gdd/` | Παραβιάζει `No Unilateral Cross-Domain Changes` |
| Mega-JSON ενοποίηση όλων των artifacts | Καταστρέφει incremental file writing (3–5k/section) + file-is-memory |
| Per-folder `_index.json` | Το manifest αρκεί — extra archaeology |
| Ξεχωριστό link graph file | Links ήδη υπάρχουν ως `source_uuids` — duplication |
| 3 ξεχωριστά scripts για manifest/catalog/handover | Συγχωνεύτηκε σε 1 script (ίδια inputs) |

**Από Plan³:** 7 νέα αρχεία + 4 scripts → **4 νέα αρχεία + 2 scripts** (~40% λιγότερη δουλειά, ίδιο όφελος).

## 17.11 — Phased Implementation (χωρίς breaking changes)

Κάθε phase: GATE PASS, additive μόνο, δεν μετακινεί υπάρχοντα paths.

### Phase 1 — Package Foundations (1 απόγευμα, 2 scripts, 4 αρχεία) — CORE
- **Scripts:**
  - `scripts/document_ir.py` (με inline detection + GFM render + conditional assets/tables)
  - `scripts/build_package_index.py` → `_manifest.json` + `_catalog.md` + `_handover.json` (διάβασε IR/canon/derived/provenance, γράψε 3)
- **Artifacts:**
  - `source/document_ir.json` + `source/full_text.md` (από IR) + `source/tables.json`/`assets/` (conditional)
  - `_manifest.json` + `_catalog.md` + `_handover.json`
- **Contracts/Validation:**
  - Επέκταση `contracts/stage-contracts.json` stage-01 gate (`document_ir.json exists && file_hash matches`)
  - `scripts/validate_output.py` → manifest/handover checks + NeedsOcr
  - Αναβάθμιση `views/projections/<agent>/README.md` (πρώτο read = `_catalog.md`)
- **Dependencies:** Καμία — μπορεί να ξεκινήσει αμέσως. Το IR είναι προϋπόθεση για manifest.
- **Από Plan³:** Συγχώνευση 3 scripts→1, διαγραφή per-folder indexes/seeds/link-graph

### Phase 2 — Hardening & Tests (½ απόγευμα) — CORE [COMPLETED]
- **Tests / Snapshots (COMPLETED):** `tests/fixtures/{minimal.pdf, minimal.epub}` + `tests/snapshots/` (`test_snapshots.py` snapshot test harness, 2/2 PASS via `pytest tests/snapshots -q`) — snapshot pattern όπως AnyDoc
- **Provenance & Quarantine (COMPLETED):** `audit/provenance.json` reverse field (`reverse: {uuid: [hash]}`) + enforcement `derived.source_uuids` → quarantine (`canon/unresolved-ambiguities.json`)
- **Dependencies:** Μετά Phase 1 (χωρίς IR δεν υπάρχει τι να testάρεις)
- **Από Plan³:** Ήταν ξεχωριστή Phase C — συγχωνεύτηκε, seeds διαγράφηκαν

### Phase 3 — Optional Polish (μόνο αν φανεί ανάγκη σε CCGS pilot) — NON-CORE
- Εμπλουτισμός manifest με counts/links μόνο αν pilot δείξει ότι `level-designer` ψάχνει tables
- `docs/ccgs-handoff.md` guidance: `cp -r my-game/ <ccgs>/design/source-material/` → `/start`
- Καμία αυτόματη εγγραφή στο CCGS — guidance μόνο
- **Dependencies:** Μετά Phase 1 (μπορεί να παραλειφθεί εντελώς)

**Σειρά εκτέλεσης:** Phase 1 → Phase 2 → (Phase 3 αν χρειαστεί). Η Phase 1 είναι αυτοτελές handoff — το CCGS μπορεί να το καταναλώσει αμέσως.

## 17.12 — Gates & Acceptance Criteria

| Phase | Gate Command | Acceptance |
|---|---|---|
| Phase 1 | `python scripts/parse_book.py <fixture> --out /tmp/pkg && python scripts/validate_output.py /tmp/pkg` | `GATE PASS` + `source/document_ir.json` exists + `_manifest.json` valid + `_catalog.md` <800 tokens + `_handover.json` status PASS/NEEDS_ATTENTION + `full_text.md` rendered από IR |
| Phase 2 | `pytest tests/snapshots -q` + `validate_output.py` | Snapshots pass (pdf+epub) + `grep authoritative.*true _manifest.json` βρίσκει canon + `audit/provenance.json` reverse lookup περνάει + quarantine για missing `source_uuids` |
| Phase 3 | CCGS pilot `Read _catalog.md` | Pilot agent βρίσκει entities/chapters/tables χωρίς extra Glob — αν όχι, skip |

## 17.13 — Dependencies & Σωστή Σειρά

```
Phase 1 (IR + Manifest/Catalog/Handover)  ← ξεκινά πρώτο, προϋπόθεση όλων
  └→ Phase 2 (Snapshots + Reverse Provenance)
       └→ Phase 3 (Pilot polish, optional)
```

Καμία phase δεν σπάει υπάρχοντα consumers — όλα additive. Το CCGS wiring, Unity/Unreal, exports, simulation, theory-lenses **δεν αγγίζονται**.

## 17.14 — Analysis/Design vs Implementation

- **Analysis/Design (COMPLETED):** AnyDoc study + CCGS workflow study + Plan³ loop (7→4 artifacts, 4→2 scripts, seeds/indexes/link-graph διαγραφές) — κλειδωμένο σε αυτό το roadmap + `active.md`
- **Implementation (Phase 1 & 2 COMPLETED, Phase 3 NOT STARTED):** `scripts/document_ir.py` + `scripts/build_package_index.py` + `audit/provenance.json` reverse lookup + `scripts/validate_output.py` enforcement for `derived.source_uuids` & quarantine → **GATE PASS** (`pytest tests/snapshots -q` + `python scripts/validate_output.py`).
- **Phase 17 artifacts (Phase 1):** `source/document_ir.json` + `source/full_text.md` (GFM from IR) + `_manifest.json` + `_catalog.md` + `_handover.json` — all generated per build, conditional `source/tables.json`/`source/assets/` when present.

---

## TOMORROW — FINAL VERIFICATION & COMPARATIVE AUDIT (TODO)

> **STATUS: FIX IMPLEMENTED (2026-09-15), STILL BLOCKED ON FULL RE-RUN — see `docs/plans/2026-09-15-entity-extraction-agent-fix-plan.md`. `SKILL.md` now has Βήμα 1.5 (agent entity refinement) and `parse_book.py` caps `_real_chars` to top-40-by-evidence before the O(N²) consumers (`character_psychology.py`, `simulate_knowledge_graph.py`, and `mcts_balance_solver.py` — same nested-loop pattern found there too during the twin-check, not in the original plan). Verified on `tests/fixtures/minimal.pdf` (GATE PASS, 3 chars, 12K projections) + `python -m unittest discover tests` (9/9). NOT yet re-verified on the real Neuromancer PDF — that 72-minute run, plus the comparative audit below, is still pending.**
> **HARD SCOPE RULE:** Agent-to-agent wiring / orchestration is **OUT OF SCOPE**. No wiring implementation. If audit reveals issues requiring wiring/routing/orchestration changes, mark them **BLOCKED / DEFERRED** and notify immediately.

**2026-09-15 attempt (real PDF: Neuromancer, 489 pages):** Ran full pipeline end-to-end (72 min, GATE PASS / handover NEEDS_ATTENTION). Output discarded (was 2.8GB, broken) — found:
1. `extract_entities.py`'s `_CAPITALIZED` regex over-extracts — produced 1578 "characters" for a book with ~20-30 real ones (e.g. "Neuromancer" and "Neuro" extracted as two separate entities, linked to each other as a relationship). Inflates `entities.json` (1.6MB) and `canon/relationships.json` (1.3MB, 3321 relationships).
2. Downstream, `assemble_projection.py`'s `derived.projection.json` explodes for 5 of 49 agent roles (world-builder 405MB, writer/narrative-director/ux-designer/prototyper ~343MB each) vs ~700KB for the other 44 — almost certainly fed by bug #1's entity bloat. Root cause of the explosion not yet diagnosed (deferred, not investigated this session).

Fix both before re-running the real-book comparison; old baseline output at `book_test_outputs/Neuromancer_game/` is untouched and still usable as the "old version" side of the comparison. Fix plan (both bugs, same root cause): `docs/plans/2026-09-15-entity-extraction-agent-fix-plan.md`. See also `docs/plans/2026-09-15-ccgs-handoff-plan.md` (separate, unrelated planned work).

**2026-09-15 `/fable-judge` comparative audit (`Neuromancer_game_baseline` vs `_v2`, outputs only, PDF not read):** verdict "verified with caveats" — confirmed real canon-extraction improvement (89.7% entity-noise reduction), but flagged 4 open items. All 4 now CLOSED — see `docs/plans/2026-09-15-fable-judge-audit-and-fixes.md`:
1. Chapter-title bug (65.6% of chapters shared a duplicate title) — real bug, root-caused and fixed in `parse_book.py::chunk_text()` (bare-number heading detection was missing entirely).
2. Mojibake in Greek fields — verified false alarm (display artifact, zero corrupted bytes on disk); one dormant `try_pandoc()` encoding bug fixed defensively.
3. 2 benchmark reports looked like stubs (nash-equilibrium, player-personas) — root cause found: their lexicons were Greek-only, so they silently zeroed out on Neuromancer's English text. Fixed by switching `mcts_balance_solver.py` and `simulate_player_personas.py`'s lexicons to English-only (user's call: most book text passed through this pipeline is English, not worth keeping bilingual here — Greek words removed, not kept alongside).
Full test suite 17/17 PASS (13 pre-existing + 4 new chapter tests + 2 new lexicon tests). Not yet re-verified via a full real-book pipeline re-run (verification was done by calling the fixed functions directly against the already-extracted `source/full_text.md` — still compatible with the "TOMORROW" full re-run below, not a substitute for it).

### 1. Final `book2game` Audit
Full audit of current state:
- pipeline
- contracts
- artifacts
- provenance
- validation
- tests
- preparation package
- canonical/derived separation
- agent-readiness
- remaining gaps

### 2. Claude Code Game Studio Verification
Verify that the real preparation package can be consumed correctly by Claude Code Game Studio and that agents receive required context without unnecessary information archaeology.

### 3. Real-World Old-vs-New Comparison
- Source PDF: `Στοιχεία λήψης\Neuromancer - William Gibson`
- Run new `book2game` version with this source PDF.
- Leave existing old-version output (`C:\Users\Kon_Try\Desktop\book_test_outputs`) untouched.
- Create a distinct new output folder inside `C:\Users\Kon_Try\Desktop\book_test_outputs` for direct side-by-side comparison.

### 4. Comparative Measurement
Objective evidence-based comparison between old and new versions on:
- information completeness
- extraction quality
- structure/organization
- provenance/traceability
- correctness
- usefulness to downstream Game Studio agents
- artifact quality
- preparation efficiency
- processing/runtime metrics

---

## References
- AnyDoc: https://github.com/firecrawl/anydoc — detection → IR → deterministic render → typed errors
- Claude Code Game Studios: https://github.com/Donchitos/Claude-Code-Game-Studios — 49 agents, file-is-memory, Question→Options→Decision→Draft→Approval
- Internal: `standards/epistemic-model.md`, `standards/immutable-kernel-spec.md`, `standards/verification-rules.md`, `standards/projection-template.md`, `contracts/stage-contracts.json`
