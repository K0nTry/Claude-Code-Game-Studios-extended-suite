#!/usr/bin/env python3
"""
tests/test_ocr_fallback.py
Unit tests for OCR fallback functionality in scripts/parse_book.py
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import parse_book


class TestOCRFallback(unittest.TestCase):

    def test_parse_pdf_ocr_function_exists(self):
        """Verify parse_pdf_ocr function is defined in parse_book."""
        self.assertTrue(hasattr(parse_book, "parse_pdf_ocr"), "parse_pdf_ocr function must exist in parse_book.py")

    def test_parse_pdf_ocr_graceful_missing_deps(self):
        """Verify parse_pdf_ocr returns None safely when OCR libraries are unavailable."""
        with patch.dict("sys.modules", {"pytesseract": None}):
            result = parse_book.parse_pdf_ocr(Path("non_existent.pdf"))
            self.assertIsNone(result)

    def test_parse_pdf_fallback_triggers_ocr_when_short(self):
        """Verify parse_pdf_fallback triggers parse_pdf_ocr when text extraction yields < 100 chars."""
        fake_pdf = Path("scanned.pdf")
        with patch("parse_book.parse_pdf_pymupdf", return_value="Short text"), \
             patch("parse_book.parse_pdf_pdfminer", return_value=""), \
             patch("parse_book.parse_pdf_ocr", return_value="Extracted via OCR text from scanned document") as mock_ocr:

            res = parse_book.parse_pdf_fallback(fake_pdf)
            mock_ocr.assert_called_once_with(fake_pdf)
            self.assertEqual(res, "Extracted via OCR text from scanned document")

    def test_parse_pdf_fallback_does_not_trigger_ocr_when_text_sufficient(self):
        """Verify parse_pdf_fallback does NOT call OCR when text is sufficiently long (> 100 chars)."""
        fake_pdf = Path("digital.pdf")
        long_text = "A " * 60  # 120 chars
        with patch("parse_book.parse_pdf_pymupdf", return_value=long_text), \
             patch("parse_book.parse_pdf_ocr") as mock_ocr:

            res = parse_book.parse_pdf_fallback(fake_pdf)
            mock_ocr.assert_not_called()
            self.assertEqual(res, long_text)


if __name__ == "__main__":
    unittest.main()
