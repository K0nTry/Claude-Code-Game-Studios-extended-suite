# Contributing to book2game

Thank you for your interest in contributing! This project is a deterministic,
production-grade book-to-game pipeline. We value clarity, traceability, and
source fidelity.

## Development Workflow

1. **Fork** the repository.
2. **Create a branch** with a descriptive name (e.g., `feature/entity-extraction`).
3. **Make changes** — follow the existing code style and architecture.
4. **Add tests** where applicable (`tests/`).
5. **Run the full validation**:
   ```bash
   python scripts/validate_output.py ./test-output
   ```
6. **Commit** with a clear, imperative message.
7. **Open a Pull Request** — link any relevant issues.

## Architecture Guidelines

- **Canonical layer must be deterministic.** No ML dependencies in `canon/`.
- **Every artifact needs source evidence.** Claims without citations go to `unresolved-ambiguities.json`.
- **Separate CANON from DERIVED.** Use the tri-state epistemic model.
- **Immutable kernels** on all projections — include `IMMUTABLE_KERNEL.md`.

## Code Style

- Python 3.10+ stdlib (no external ML deps for canonical logic).
- Type hints where applicable.
- Docstrings in Greek or English (consistent per module).
- Follow existing naming conventions in `scripts/`.

## Reporting Issues

When opening an issue:
- Use the appropriate template.
- Include reproduction steps and expected vs. actual output.
- Attach relevant evidence files if it's a data/extraction problem.

## Questions?

See the project documentation:
- [`SKILL.md`](SKILL.md) — Full pipeline spec
- [`roadmap.md`](roadmap.md) — Phase status
- [`standards/`](standards/README.md) — Canonical specifications

## Code of Conduct

This project adheres to a Code of Conduct. By participating, you are expected
to uphold this standard. See [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).
