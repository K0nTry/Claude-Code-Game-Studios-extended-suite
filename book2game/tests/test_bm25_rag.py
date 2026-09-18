# -*- coding: utf-8 -*-
import unittest
from pathlib import Path
import json
import sys
import tempfile
import shutil

# Ensure scripts/ in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from query_rag import search_rag, bm25_score_texts

class TestBM25Retrieval(unittest.TestCase):
    def test_bm25_scoring_logic(self):
        docs = [
            "The quick brown fox jumps over the lazy dog.",
            "A fast dark animal leaps across the sleepy canine.",
            "Completely unrelated text about cooking recipes and kitchen tools."
        ]
        query = "quick brown fox"
        scores = bm25_score_texts(docs, query)
        self.assertEqual(len(scores), 3)
        # Doc 0 should have the highest score since it contains all query terms
        self.assertGreater(scores[0], scores[2])

    def test_search_rag_bm25_integration(self):
        tmp_dir = Path(tempfile.mkdtemp())
        try:
            out_dir = tmp_dir / "game_proj"
            ch_dir = out_dir / "chapters"
            ch_dir.mkdir(parents=True)
            
            (ch_dir / "ch1.md").write_text("The hero fought the dragon in the dark cave.", encoding="utf-8")
            (ch_dir / "ch2.md").write_text("The merchant sold apples and oranges in the sunny market.", encoding="utf-8")
            
            results = search_rag(out_dir, "hero dragon")
            self.assertIsInstance(results, list)
            self.assertGreater(len(results), 0)
            self.assertIn("hero", results[0]["content"].lower())
            self.assertIn("bm25_score", results[0])
        finally:
            shutil.rmtree(tmp_dir)

if __name__ == "__main__":
    unittest.main()
