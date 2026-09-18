#!/usr/bin/env python3
"""
document_ir.py — Normalized Document IR & Magic Bytes Detection (Phase 17 Phase 1)
- Content-based detection (magic bytes: %PDF, PK\\x03\\x04, D0CF11E0)
- Normalized IR: blocks, tables, assets, notes + SHA-256 hashes
- Deterministic GFM rendering to source/full_text.md
- Conditional assets/tables extraction
"""

import hashlib
import json
import os
from pathlib import Path
from datetime import datetime

def detect_format(file_path: Path) -> str:
    """Detect file format using magic bytes and extension fallback."""
    try:
        with open(file_path, "rb") as f:
            header = f.read(8)
        if header.startswith(b"%PDF"):
            return "pdf"
        elif header.startswith(b"PK\x03\x04"):
            # Could be epub or docx
            suffix = file_path.suffix.lower()
            if suffix == ".epub":
                return "epub"
            elif suffix == ".docx":
                return "docx"
            return "epub" # default zip-based
        elif header.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
            return "doc"
    except Exception:
        pass

    suffix = file_path.suffix.lower().lstrip(".")
    return suffix if suffix else "txt"

def file_sha256_hex(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()

def build_document_ir(book_path: Path, extracted_text: str) -> dict:
    """Build normalized Document IR from raw text and source file."""
    file_hash = file_sha256_hex(book_path)
    fmt = detect_format(book_path)

    # Split text into paragraphs/blocks separated by blank lines
    raw_blocks = [b.strip() for b in extracted_text.split("\n\n") if b.strip()]
    blocks = []
    for idx, b_text in enumerate(raw_blocks):
        b_hash = "sha256:" + hashlib.sha256(b_text.encode("utf-8")).hexdigest()
        b_type = "heading" if b_text.startswith("#") else "paragraph"
        blocks.append({
            "index": idx,
            "type": b_type,
            "text": b_text,
            "page": 1, # estimated/approximate if not paged
            "hash": b_hash
        })

    ir = {
        "source_file": book_path.name,
        "file_hash": file_hash,
        "detected_format": fmt,
        "generated_at": datetime.now().isoformat(),
        "blocks": blocks,
        "tables": [],
        "assets": [],
        "notes": []
    }
    return ir

def render_gfm_from_ir(ir: dict) -> str:
    """Render deterministic GFM full_text.md from Document IR."""
    lines = [
        f"# Πλήρες Κείμενο (IR Normalized) — {ir['source_file']}",
        f"",
        f"> Source Hash: `{ir['file_hash']}`  ",
        f"> Format: `{ir['detected_format']}` | Blocks: {len(ir['blocks'])}  ",
        f"> Generated: {ir['generated_at']}",
        f"",
        "---",
        ""
    ]
    for block in ir["blocks"]:
        lines.append(block["text"])
        lines.append("")
    return "\n".join(lines)

def process_document(book_path: Path, out_dir: Path, extracted_text: str) -> Path:
    """Orchestrates IR generation, GFM rendering, and conditional outputs."""
    source_dir = out_dir / "source"
    source_dir.mkdir(parents=True, exist_ok=True)

    ir = build_document_ir(book_path, extracted_text)
    ir_path = source_dir / "document_ir.json"
    ir_path.write_text(json.dumps(ir, ensure_ascii=False, indent=2), encoding="utf-8")

    # Deterministic GFM full_text.md
    gfm_content = render_gfm_from_ir(ir)
    full_text_path = source_dir / "full_text.md"
    full_text_path.write_text(gfm_content, encoding="utf-8")

    # Conditional tables.json if tables detected
    if ir["tables"]:
        tables_path = source_dir / "tables.json"
        tables_path.write_text(json.dumps(ir["tables"], ensure_ascii=False, indent=2), encoding="utf-8")

    # Conditional assets/ directory if assets detected
    if ir["assets"]:
        assets_dir = source_dir / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)

    return full_text_path
