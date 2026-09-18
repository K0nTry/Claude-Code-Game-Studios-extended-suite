# Verification Rules

> Mandatory checks for production-grade book2game output.

## Rule 1: Source Fidelity

Every canon artifact must trace to exact source lines.

- **Check:** Every entity in `canon/entities.json` has `source_offsets` with `file`, `line_start`, `line_end`, `hash`.
- **Check:** SHA-256 hash matches the paragraph content at the given offset.
- **Violation:** Entity without source_offsets → quarantine to `audit/unresolved-ambiguities.json`.

## Rule 2: Epistemic Separation

Canon and derived facts must not mix in the same field.

- **Check:** Canon fields have `source_offsets`; derived fields have `method` + `confidence`.
- **Violation:** Derived field without method → warning. Canon field without offsets → error.

## Rule 3: Zero Hallucination

No entity, relationship, or claim may appear without explicit source evidence OR open-space label.

- **Check:** Every key in canon/ has either `source_offsets` or `_epistemic: "open_space"`.
- **Violation:** Unattributed claim → quarantine.

## Rule 4: Projection Kernels

Every projection must carry an immutable kernel header.

- **Check:** Every file in `views/projections/<agent>/` starts with `IMMUTABLE_KERNEL.md` or has a `_kernel` JSON field.
- **Violation:** Missing kernel → projection is invalid.

## Rule 5: Canonical UUID Stability

UUIDs are assigned once and never reused.

- **Check:** No UUID appears in two different canon entities.
- **Violation:** UUID collision → error (reassignment required).

## Rule 6: Provenance Chain

Audit trail must link source → canon → derived → projection.

- **Check:** `audit/provenance.json` has entries for every canon entity showing its source span.
- **Check:** `audit/verification-report.json` summarizes pass/fail per rule.

## Rule 7: Ambiguity Quarantine

Uncertain extractions are quarantined, not silently included.

- **Check:** `audit/unresolved-ambiguities.json` exists and contains any quarantined items.
- **Check:** No canon artifact contains quarantined items.
