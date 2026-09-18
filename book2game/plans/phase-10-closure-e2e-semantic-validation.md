# Phase 10 Closure: E2E Semantic Validation Plan

> **Objective:** Close Phase 10 by validating projections not just structurally, but semantically, ensuring they are production-grade.

## Execution Steps

1.  **E2E Test Run:** 
    - Input: 1 synthetic test book (from `tests/fixtures/`) + 1 real verified book type.
    - Pipeline: `parse_book.py` → `canon/derived` generation → `assemble_projection.py --all` → `validate_output.py`.
    - Verification: Gate Pass, 49/49 projections, hash lineage.

2.  **Role-Quality Semantic Verification (Rubric: Coverage, Precision, Traceability, Self-containedness):**
    - Audit 10 critical agents (Directors + Leads).
    - Produce `ROLE_QUALITY_REPORT.md` (49x4 score table).

3.  **Context Boundary & Gap Assessment:**
    - Decide: Keep generic `CONTEXT_BOUNDARY.md` or Refine Selectively.
    - Assess: Value of `qa-tester`, `art-director`, and 14 thin engine agents.

4.  **Self-containedness Proof:**
    - Thought experiment on 5 agents: Deliverable production using only projection + GDD.

5.  **Final Reporting:**
    - Update `active.md`, `audit/verification-report.json`.
    - Verdict: Phase 10 Closure.

## Decisions (Pre-Filled)
- **Test Books:** 1 synthetic (minimal), 1 real (sample verified).
- **Audit Depth:** 10 deep (Directors/Leads), 39 light (spot check).
- **Context Boundary:** Keep generic by default, refine selectively.
- **Thin Engines:** Keep minimal unless proven insufficient by self-containedness check.
