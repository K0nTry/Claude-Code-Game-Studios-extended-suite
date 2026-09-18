# Immutable Kernel Specification

> Every projection file MUST contain a kernel. The kernel is never modified after creation.

## Purpose

The kernel is a tamper-evident header that proves:
1. This projection was generated from verified source text.
2. The source text has a known hash.
3. The canon and derived data versions are recorded.
4. The epistemic breakdown is transparent.

## Kernel Fields (Required)

| Field | Type | Description |
|-------|------|-------------|
| `tool_version` | string | Version of book2game that created this projection |
| `source_hash` | string | SHA-256 hash of the full_text.md used as source |
| `canon_version` | string (ISO 8601) | Timestamp when canon layer was last updated |
| `derived_version` | string (ISO 8601) | Timestamp when derived layer was last updated |
| `extraction_timestamp` | string (ISO 8601) | When this specific projection was created |
| `canonical_uuids_present` | integer | Count of canonical UUIDs embedded in this projection |
| `open_space_count` | integer | Count of open-space fields in this projection |
| `epistemic_breakdown` | object | `{canon: N, derived: N, open_space: N}` |
| `projection_agent` | string | Name of the agent this projection is for |

## Kernel Format

For Markdown projections (e.g., IMMUTABLE_KERNEL.md):
- Table format as shown in projection-template.md.

For JSON projections:
- Embedded as `"_kernel": { ... }` at the top level of the JSON object.

## Verification

`validate_output.py` checks:
1. Every file in `views/projections/<agent>/` has a kernel.
2. `source_hash` matches the current `full_text.md`.
3. `canonical_uuids_present > 0` for canon projections.
4. `tool_version` matches current book2game version.

## Immutability

- Kernels are written once at projection creation time.
- They are NEVER updated or overwritten.
- If source changes, a NEW projection is created (not an update).
- Old projections are archived to `views/projections/<agent>/archive/`.
