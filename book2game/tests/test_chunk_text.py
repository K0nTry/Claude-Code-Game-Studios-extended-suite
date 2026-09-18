#!/usr/bin/env python3
"""
tests/test_chunk_text.py
Regression tests for chunk_text() heading detection and title uniqueness
in scripts/parse_book.py.

Covers the bug found in the Neuromancer_game_baseline/v2 audit: bare
standalone-number chapter markers went undetected, dumping the whole book
into a single "Πρόλογος / Εισαγωγή" bucket repeated across 65.6% of chapters.
"""

import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import parse_book


def make_book(n_chapters=5, filler_len=250):
    """Bare-number-headed chapters, like Neuromancer's real structure."""
    filler = "Lorem ipsum dolor sit amet. " * (filler_len // 29 + 1)
    parts = ["Neuromancer\nby William Gibson\nPART ONE.\n"]
    for i in range(1, n_chapters + 1):
        parts.append(f"{i}\n{filler.strip()} Chapter {i} body text here.")
    return "\n\n".join(parts)


class TestChunkTextHeadingDetection(unittest.TestCase):

    def test_bare_number_headings_detected(self):
        """Every bare standalone chapter number becomes its own chunk, not one giant prologue."""
        text = make_book(n_chapters=6)
        chunks = parse_book.chunk_text(text, chunk_tokens=1000)
        titles = [t for _, t in chunks]
        # each chapter number should show up as (part of) a distinct title
        for i in range(1, 7):
            self.assertTrue(
                any(t == str(i) for t in titles),
                f"expected a chunk titled '{i}', got {titles}",
            )

    def test_no_duplicate_titles_for_oversized_prologue(self):
        """An oversized pre-heading section gets numbered, unique titles — not one repeated string."""
        # front matter big enough to exceed chars_per_chunk and force the
        # prologue-splitting branch (chunk_tokens=1 -> chars_per_chunk=4)
        prologue = ("Front matter paragraph one is here.\n\n"
                    "Front matter paragraph two is here.\n\n"
                    "Front matter paragraph three is here.\n\n")
        text = prologue + "1\nReal chapter one body text.\n\n2\nReal chapter two body text."
        chunks = parse_book.chunk_text(text, chunk_tokens=1)
        titles = [t for _, t in chunks]
        non_empty = [t for t in titles if t]
        self.assertEqual(
            len(non_empty), len(set(non_empty)),
            f"expected all chunk titles to be unique, got duplicates in {titles}",
        )

    def test_prologue_precedes_heading_chunks_in_order(self):
        """Split prologue parts must come before the real chapters, not after (ordering bug)."""
        prologue = ("Front matter paragraph one is here.\n\n"
                    "Front matter paragraph two is here.\n\n"
                    "Front matter paragraph three is here.\n\n")
        text = prologue + "1\nReal chapter one body text."
        chunks = parse_book.chunk_text(text, chunk_tokens=1)
        titles = [t for _, t in chunks]
        prologue_positions = [i for i, t in enumerate(titles) if t and t.startswith("Πρόλογος")]
        chapter_positions = [i for i, t in enumerate(titles) if t == "1"]
        self.assertTrue(prologue_positions and chapter_positions)
        self.assertLess(max(prologue_positions), min(chapter_positions))

    def test_numbered_sentence_false_positive_still_tolerated(self):
        """A stray '1948. But a lot of...' style sentence shouldn't crash chunking (pre-existing,
        lower-severity behavior — not fixed here, just confirmed non-fatal)."""
        text = "1\nReal chapter body.\n\n1948. But a lot of the mainstream traditional writers, kept going."
        chunks = parse_book.chunk_text(text, chunk_tokens=1000)
        self.assertGreater(len(chunks), 0)


if __name__ == "__main__":
    unittest.main()
