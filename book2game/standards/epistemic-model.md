# Epistemic Model — Tri-State

> Every field in every canon or derived artifact carries an epistemic status.
> This prevents inferential creep and keeps projections honest.

## States

| State | Label | Meaning | Source Required |
|-------|-------|---------|-----------------|
| **CANON** | `canon` | Directly extracted from source text. Verifiable against paragraph hash. | Yes — source_offset + hash |
| **DERIVED** | `derived` | Inferred by heuristic from canon facts. Method + confidence recorded. | Yes — method, confidence, source UUIDs |
| **OPEN_SPACE** | `open_space` | No source evidence. Creative/design space. Must be labeled as such. | No — but must carry `_epistemic: "open_space"` |

## Rules

1. **Canon fields** must carry `source_offsets: [{file, line_start, line_end, hash}]`.
2. **Derived fields** must carry `method: string`, `confidence: float [0..1]`, `source_uuids: [uuid, ...]`.
3. **Open-space fields** must carry `_epistemic: "open_space"` and a reason string.
4. **Projections** inherit the epistemic status of each field they expose.
5. **Kernels** report counts: `canon_count`, `derived_count`, `open_space_count`.

## Enforcement

- `validate_output.py` checks that canon fields have source_offsets.
- Missing offsets on a canon field → error.
- Missing method on a derived field → warning.
- Open-space without label → error.

## Migration

Existing artifacts (pre-production-grade) are marked `DERIVED` by default.
Re-extraction with paragraph hashing upgrades them to `CANON` when source evidence exists.
