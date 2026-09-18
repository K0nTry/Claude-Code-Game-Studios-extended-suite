# Plan: Evidence-Driven Integration (Phases 13–16b)

## Objective
Integrate core competitive advantages from 10 high-star game adaptation repositories into `book2game`, upgrading it from a preparation layer to an end-to-end validated studio system.

## Principles
- **Deterministic:** All integration is pure Python, zero-ML-dependency, deterministic seeds.
- **Incremental:** Each phase is independently verifiable via `--flag` and `GATE PASS`.
- **Minimalist:** YAGNI approach — if a feature isn't core, it's flagged as optional or quarantined.

## Execution Order
1. **Phase 13: Runtime Validation Layer**
    - `whitebox/whitebox_runner.py`: Detects highest-risk edge (choice-tree + tension-curve) and simulates with deterministic seed.
    - `contracts/stage-contracts.json`: Root-level definition of ownership/inputs/outputs per stage.
    - Anti-overclaim: Quarantine non-verifiable claims to `canon/unresolved-ambiguities.json`.
2. **Phase 15: Data Backbone**
    - `schemas/*.schema.json`: Strict JSON Schema Draft 2020-12 for all artifacts.
    - `knowledge/`: StyleDNA fingerprint, foreshadowing tracking, WorldMuncher-style world model, progress-state.
3. **Phase 14b: Limited Export Layer**
    - `exports/yarn/` + `exports/nodes/`: Yarn and node-graph exports only (flag-restricted).
4. **Phase 16a: Minimal State Simulation**
    - `simulation/`: Minimalist choice-tree → binary card-mode simulator.
5. **Phase 15b: Theory-Lenses**
    - 3 optional validators: South Park causality, Character Arc, Hero’s Journey.

## Verification
- Every phase requires `GATE PASS` (via `validate_output.py` updated with heavy flags).
- All simulations and whitebox runs use deterministic seeds.

## Handoff
- The next session must begin by reading this plan and `active.md`.
- Implementation starts with Phase 13.
