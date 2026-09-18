# `contracts/` — Stage Contracts

Defines ownership, inputs, outputs, and handoff gates per pipeline stage.

- `stage-contracts.json`: 6-stage contract (source → canon → derived → projections → whitebox → distribution)

Each stage declares:
- `owner`: which script/module owns it
- `inputs`: files consumed
- `outputs`: files produced
- `handoff_gate`: verification conditions
- `invariants`: rules that must never break

See `../docs/plans/` for planning documents.
