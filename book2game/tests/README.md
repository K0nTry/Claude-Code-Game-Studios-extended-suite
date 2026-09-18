# `tests/` — Test Suite

Automated tests for the book2game pipeline using `unittest`.

- `test_bm25_rag.py`: BM25 retrieval scoring and search integration
- `test_mcp_server.py`: MCP server module tests
- `test_ocr_fallback.py`: OCR fallback behavior
- `fixtures/`: Sample book text files for deterministic testing

Run with:
```bash
python -m pytest tests/
# or
python -m unittest discover tests/
```
