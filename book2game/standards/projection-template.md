# Projection Template

> Template for creating agent-specific views from canon + derived artifacts.
> Each projection is self-contained: it embeds all data its agent needs, plus a kernel.

## Structure

```
views/projections/<agent-name>/
  IMMUTABLE_KERNEL.md          # Always present. Never modified after creation.
  <artifact>.canon.json        # Canon data for this agent
  <artifact>.derived.json      # Derived data for this agent
  README.md                    # How to use this projection
```

## IMMUTABLE_KERNEL.md Content

```markdown
# Immutable Kernel — <agent-name>

| Field | Value |
|-------|-------|
| tool_version | book2game v2.0.0 |
| source_hash | <SHA-256 of full_text.md> |
| canon_version | <ISO timestamp of canon creation> |
| derived_version | <ISO timestamp of last derivation> |
| extraction_timestamp | <ISO timestamp of this projection> |
| canonical_uuids_present | <count> |
| open_space_count | <count> |
| epistemic_breakdown | canon: N, derived: N, open_space: N |
```

## Canon Fields Format

```json
{
  "_epistemic": "canon",
  "_uuid": "char_001",
  "_name": "Entity Name",
  "source_offsets": [
    {
      "file": "source/chapters/ch01-introduction.md",
      "line_start": 12,
      "line_end": 15,
      "hash": "sha256:abc123..."
    }
  ],
  "data": { ... }
}
```

## Derived Fields Format

```json
{
  "_epistemic": "derived",
  "_uuid": "char_001",
  "_name": "Entity Name",
  "method": "big5_proxy_from_dialogue",
  "confidence": 0.75,
  "source_uuids": ["char_001", "char_002"],
  "data": { ... }
}
```

## Open-Space Fields Format

```json
{
  "_epistemic": "open_space",
  "_reason": "No source evidence for faction dynamics; creative space",
  "data": { ... }
}
```

## Per-Agent Mapping

| Agent | Canon Inputs | Derived Inputs |
|-------|-------------|----------------|
| narrative-director | entities, relationships, world-glossary, character-arc-seeds, choice-consequence-matrix | concept-mechanic-map |
| systems-designer | entities, world-boundaries | design-constraints, concept-mechanic-map, economy-formulas |
| economy-designer | entities | economy-formulas, tension-pacing-curve, dda-rules |
| audio-director | entities, relationships | leitmotif-matrix |
| art-director | entities, world-boundaries, world-glossary | design-constraints |
| qa-lead | entities | branching-graph, choice-consequence-matrix |
| ... | ... | ... |

Full mapping: 49 agents × their required projections. Implemented incrementally.
