#!/usr/bin/env python3
"""
tests/test_english_lexicons.py
Regression test: simulate_player_personas.py and mcts_balance_solver.py must
produce real signal on English-language text, not just Greek.

Bug context: both lexicons were Greek-only, so any English book (e.g.
Neuromancer) silently degenerated to the zero-signal floor score (0.15 for
every persona) and zero detected conflicts — looked like a stub/placeholder
in the audit but was actually a language-coverage gap in the word lists.
"""

import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import simulate_player_personas as spp
import mcts_balance_solver as mbs

ENGLISH_TEXT = (
    "Case walked into the hidden temple, following the old map toward the "
    "ancient ruins. He had a mission to complete, a clear goal, a quest for "
    "the truth. His friend and team leader trusted him like family.\n"
    "\"Watch out,\" Molly said. Armitage attacked Case's rival in a sudden "
    "battle. Molly drew her weapon, ready to strike back and defeat the enemy."
)


class TestEnglishLexiconCoverage(unittest.TestCase):

    def test_personas_do_not_degenerate_to_floor_on_english_text(self):
        result = spp.simulate_personas(ENGLISH_TEXT)
        scores = {p["persona"]: p["compatibility_score"] for p in result["personas"]}
        # not every persona stuck at the zero-signal floor (0.15)
        self.assertTrue(
            any(s > 0.15 for s in scores.values()),
            f"all personas stuck at the zero-signal floor: {scores}",
        )
        # at least one persona has real evidence, not an empty list
        self.assertTrue(any(p["evidence"] for p in result["personas"]))

    def test_conflict_lexicon_detects_english_conflict(self):
        characters = [{"name": "Case"}, {"name": "Armitage"}, {"name": "Molly"}]
        chunks = [(ENGLISH_TEXT, "ch1")]
        result = mbs.solve_mcts_balance(characters, chunks)
        self.assertGreater(
            result["total_conflicts_found"], 0,
            "expected at least one conflict detected in English conflict text",
        )


if __name__ == "__main__":
    unittest.main()
