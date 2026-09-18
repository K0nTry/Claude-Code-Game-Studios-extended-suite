# book2game — Final Production-Grade Architecture Plan

> **For agentic workers:** This plan is the source of truth for the production-grade redesign. Implementation will proceed in a future session. For any build session, read this plan, confirm it against current artifacts, and implement incrementally following the execution order.

**Goal:** Redesign `book2game` into a 100% traceable, hallucination-free context layer producing self-contained views tailored for 49 specialist agents.

**Architecture:** 5-layer pipeline with immutable verification (source → canon → derived → views/projections → audit). Canonical content is verified against source line hashes. Agent-facing projections embed mandatory kernels and remain self-contained.

**Tech Stack:** Pure Python 3.10+ stdlib (no ML/NLP dependencies for core extraction). PDF: pymupdf; EPUB: ebooklib; DOCX: python-docx. All validation deterministic and reproducible.

---

## Core Principles

1. **Source Fidelity:** Every artifact traces to exact book lines with SHA-256 paragraph hashes.
2. **Epistemic Separation:** Canonical verified facts are separated from derived heuristics.
3. **Projection-as-Consumer:** Each specialist agent receives a self-contained view with an immutable kernel header.
4. **Zero Hallucination:** No entity, relationship, or claim may appear without explicit source evidence.
5. **Auditability:** Every derivation records method, confidence, and the source spans used.

---

## Output Structure (Target)

```
<book-project>/
  source/
    full_text.md
    chapters/
    index.json
  canon/
    entities.json
    relationships.json
    world-boundaries.json
    world-glossary.json
    spatial-geography.json
    entity-aliases.json
    character-arc-seeds.json
    unresolved-ambiguities.json
  derived/
    design-constraints.json
    concept-mechanic-map.json
    economy-formulas.json
    tension-pacing-curve.json
    branching-graph.json
    choice-consequence-matrix.json
    npc-utility-schedules.json
    faction-dynamics.json
    leitmotif-matrix.json
    expansion-grammar.json
    dda-rules.json
    mod-api-schema.json
  views/
    projections/
      narrative-director/
        entities.canon.json
        relationships.canon.json
        world-glossary.canon.json
        concept-mechanic-map.derived.json
        character-arc-seeds.canon.json
        choice-consequence-matrix.derived.json
        IMMUTABLE_KERNEL.md
      systems-designer/
        ...
      economy-designer/
        ...
      audio-director/
        ...
      [49 agent folders]
    design/
      gdd/
      narrative/
      mechanics/
      balance/
      audio/
      art/
      ai/
    lore/
    technical/
    production/
    docs/
  audit/
    provenance.json
    verification-report.json
    resolved-ambiguities.json
  standards/
    canonical-uuids.json
    epistemic-model.md
    verification-rules.md
    projection-template.md
    immutable-kernel-spec.md
```

---

## Design Decisions

### D1: Extraction Engine
- **Chosen:** Pure deterministic Python stdlib (A1)
- **Rationale:** Maximize reproducibility; avoid nondeterministic ML outputs for canonical layer. Hybrid verification (A2) deferred to future phase.

### D2: Canonical Separation
- **Chosen:** Strict Canon/Derived split with Tri-State Epistemic Model (CANON / DERIVED / OPEN_SPACE)
- **Rationale:** Prevents inferential creep. Each projection embeds a header indicating epistemic status per field.

### D3: Projection Kernels
- **Chosen:** Mandatory immutable kernel header on every projection
- **Content:** tool version, source hash, canon version, derived version, extraction timestamp, canonical UUIDs present, open-space count

### D4: Canonical UUIDs
- **Chosen:** char_NNN, loc_NNN, obj_NNN, event_NNN, faction_NNN
- **Rationale:** Deterministic identity for cross-projection linking; avoids collision and ambiguity.

### D5: Paragraph Hash Verification
- **Chosen:** SHA-256 per paragraph recorded in canon with source offsets
- **Rationale:** Tamper-evident lineage for every extracted fact.

### D6: Legacy Cleanup
- **Chosen:** Keep legacy artifacts for backwards compatibility but mark as superseded
- **Rationale:** Avoids breaking existing workflows during transition.

### D7: Enforcement Policy
- **Chosen:** Strict zero-tolerance gate for canon artifacts; unresolved claims quarantined to unresolved-ambiguities.json
- **Rationale:** Prevents partial canon contamination while preserving discovery trail.

---

## Assumptions

- Input books are ≤ 200k words; larger inputs processed in chunks without global canon merges.
- English/Greek extraction supported; additional languages added by extending stopword and NER heuristics.
- 49-agent projections are static templates; per-project projection is assembled at extraction time.
- Future phases may add ML-backed NER/LLM-assisted inference in derived layer only.
- OCR is optional and deferred to Phase 8 polish.

---

## Remaining Decision Points

1. **Hybrid Extraction:** Whether to introduce LLM-assisted extraction in canon (future phase)
2. **Vector RAG:** Optional semantic embeddings for advanced retrieval
3. **OCR Integration:** Handling scanned PDFs
4. **Plugin Publishing:** Whether to publish as standalone plugin or embed in existing skill

---

## Execution Order (Future Build Session)

1. Initialize `docs/plans`, `standards/`, `views/projections/` scaffolding.
2. Implement canonical-UUIDs.json and immutable-kernel-spec.md.
3. Implement paragraph hash verification in parse_book.py.
4. Implement canon/ derived/ split logic for entities/relationships/world-models.
5. Build projection assembler for one agent (narrative-director) as reference implementation.
6. Validate with real book input; generate audit/ verification report.
7. Scale projection assembler to all 49 agents.
8. Update validation gate to enforce canonical constraints and kernel presence.
9. Deprecate legacy artifacts with warnings and compatibility wrappers.
10. Final polish: documentation, troubleshooting, example outputs.

---

## Notes

- All changes must preserve backward compatibility until explicit deprecation phase.
- Plan document was saved 2026-09-10; implementation session must reload this plan before code changes.
- Only the canonical and projection layers are mandatory for release; derived layer may remain experimental in early production.

---

**Saved:** 2026-09-10 — FINAL PRODUCTION-GRADE PLAN