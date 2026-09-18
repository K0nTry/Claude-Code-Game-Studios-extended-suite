# `standards/` — Project Standards & Specifications

Canonical specifications governing all artifacts in the project.

- `canonical-uuids.json`: Deterministic UUID schema (char_, loc_, obj_, evt_, fac_ prefixes)
- `epistemic-model.md`: Tri-state epistemic model (CANON / DERIVED / OPEN_SPACE)
- `immutable-kernel-spec.md`: Required immutable kernel header specification
- `projection-template.md`: Template for agent-specific projection files
- `verification-rules.md`: 7 mandatory verification rules for production output

These are enforced by `scripts/validate_output.py` and govern all project artifacts.
