#!/usr/bin/env python3
"""
query_rag.py — Τοπικό RAG CLI tool για αναζήτηση όρων στα chapters/ και full_text.md
Χρήση: python query_rag.py <game_dir> "όρος αναζήτησης"
"""

import sys
import json
from pathlib import Path

def search_rag(out_dir: Path, query: str):
    query_lower = query.lower()
    results = []

    # 1. Έλεγχος στα chapters/
    ch_dir = out_dir / "chapters"
    if ch_dir.exists():
        for ch_file in sorted(ch_dir.glob("*.md")):
            lines = ch_file.read_text(encoding="utf-8", errors="ignore").splitlines()
            for idx, line in enumerate(lines, 1):
                if query_lower in line.lower():
                    results.append({
                        "file": str(ch_file.relative_to(out_dir)),
                        "line": idx,
                        "content": line.strip()
                    })

    # 2. Αν δεν βρεθεί στα chapters, δοκιμή στο full_text.md
    full_text = out_dir / "full_text.md"
    if not results and full_text.exists():
        lines = full_text.read_text(encoding="utf-8", errors="ignore").splitlines()
        for idx, line in enumerate(lines, 1):
            if query_lower in line.lower():
                results.append({
                    "file": "full_text.md",
                    "line": idx,
                    "content": line.strip()
                })

    return results

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Χρήση: python query_rag.py <game_dir> <query>")
        sys.exit(1)
    
    out_dir = Path(sys.argv[1])
    query = sys.argv[2]
    res = search_rag(out_dir, query)
    print(json.dumps(res, ensure_ascii=False, indent=2))
