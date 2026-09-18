# book2game

> Production-grade book-to-context projection engine for Game Studio workflows.
> Converts books (PDF, EPUB, DOCX, TXT) into structured game-development artifacts and 49 specialist-agent projections — one command.

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)](pyproject.toml)
[![Status: Production](https://img.shields.io/badge/Status-Production-green)](roadmap.md)
[![Primary Language: Python](https://img.shields.io/badge/Language-Python-1f425f)](pyproject.toml)

---

## Overview

`book2game` is a deterministic, zero-ML-dependency pipeline that transforms a book (PDF, EPUB, DOCX, or TXT) into a complete Game Studio scaffold. It produces verified canonical artifacts, 49 specialist-agent projections, and a traceable audit trail — every claim backed by source evidence.

**Key characteristics:**

- **Source fidelity** — Every artifact traces to exact book lines via SHA-256 paragraph hashes.
- **Epistemic separation** — Canonical verified facts are strictly separated from derived heuristics (CANON / DERIVED / OPEN_SPACE model).
- **49 specialist projections** — Each agent receives a self-contained view with an immutable kernel header proving source fidelity.
- **Deterministic** — Pure Python stdlib; no nondeterministic ML outputs for canonical artifacts.
- **Hallucination-free** — No entity, relationship, or claim appears without explicit source evidence.

---

## Quick Start

```bash
# Via Claude Code / Opencode skill (recommended)
/book2game "path/to/book.pdf" --out "./my-game"

# Standalone Python (no skill required)
python scripts/parse_book.py "book.pdf" --out "./my-game"
python scripts/validate_output.py "./my-game"
```

### Output Structure

```
my-game/
  source/                    # Full text + paragraph hashes
  canon/                     # Verified canonical artifacts
    entities.json, relationships.json, world-boundaries.json, ...
  derived/                   # Derived heuristics (design, balance, etc.)
  views/projections/         # 49 agent-specific projections
    narrative-director/, systems-designer/, economy-designer/, ...
  benchmarks/                # Executive audit, player personas, Nash
  design/                    # GDD, narrative, mechanics, balance, audio, art, AI
  lore/                      # Bible, connectors, relationship matrix
  technical/                 # Engine selection, MCP servers, mod API
  audit/                     # Provenance, verification report
  standards/                 # Only in skill source (canonical-uuids, etc.)
```

See [`SKILL.md`](SKILL.md) for the full pipeline specification and output schema.

---

## Features

| Cycle | Feature | Output |
|-------|---------|--------|
| 1–4   | Source extraction & RAG index | `full_text.md`, `chapters/`, `index.json` |
| 5     | Entity & psychology extraction | `entities.json`, `voice-fingerprints.json`, `relationship-matrix.json` |
| 6     | Pacing & tension curve | `tension-pacing-curve.json` |
| 7     | Branching graph | `choice-tree.json`, `consequences-matrix.md` |
| 8     | Player persona simulation | `player-personas-simulation.json` |
| 9     | Sensory direction | `leitmotif-matrix.json`, `lighting-color-script.json` |
| 10    | Knowledge & co-occurrence | `information-spread-graph.json` |
| 11    | Conflict & balance | `faction-dynamics.json`, `progression-gini.json` |
| 12    | Expansion grammar & DDA | `expansion-grammar.json`, `mod-api-schema.json` |
| 13    | Runtime validation | `whitebox-validation.json`, `stage-contracts.json` |
| 14b   | Limited exports | `yarn/`, `nodes/` (flag-restricted) |
| 15    | Data backbone | `schemas/*.schema.json`, `knowledge/` |
| 15b   | Theory lenses | South Park causality, Character Arc, Hero's Journey |
| 16a   | State simulation | Choice-tree → card-mode simulator |

---

## Installation

### Prerequisites
- Python 3.10+
- `pandoc` (optional, for format fallback)

### Dependencies
```bash
pip install -r scripts/requirements.txt
```

### Optional MCP Server
```bash
pip install mcp>=1.0.0
python scripts/mcp_server.py
```

See [`pyproject.toml`](pyproject.toml) for the full project definition.

---

## Documentation

| Document | Description |
|----------|-------------|
| [`SKILL.md`](SKILL.md) | Full pipeline specification (12 cycles, 49 projections) |
| [`roadmap.md`](roadmap.md) | Phase-by-phase completion status |
| [`docs/plans/2026-09-10-book2game-final-production.md`](docs/plans/) | Final production architecture plan |
| [`plans/evidence-integration.md`](plans/) | Phases 13–16b integration plan |
| [`references/`](references/README.md) | Engine selection, genre taxonomy, chunking, troubleshooting |
| [`standards/`](standards/README.md) | Canonical UUIDs, epistemic model, verification rules |

---

## Contributing

We welcome contributions! Please see [`CONTRIBUTING.md`](CONTRIBUTING.md) for guidelines and the development workflow.

---

## Acknowledgments

- Built with pure Python 3.10+ stdlib (zero ML dependencies for canonical layer).
- Inspired by production-grade game-adaptation workflows and open-source transparency practices.
- Uses deterministic verification (SHA-256 paragraph hashes) for source fidelity.
