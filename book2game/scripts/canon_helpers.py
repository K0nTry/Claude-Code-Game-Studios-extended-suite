#!/usr/bin/env python3
"""
canon_helpers.py — Deterministic canon utilities.

- SHA-256 paragraph hashes
- Deterministic canonical UUID assignment (char_NNN, loc_NNN, ...)
- File hash (for full_text.md source_hash)
"""

import hashlib
import re
import json
from pathlib import Path


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_paragraph_hashes(full_text_path: Path) -> dict:
    """
    Returns: {
      "paragraphs": [
        {"index": 0, "text": "...", "hash": "sha256:abc...", "line_start": 1, "line_end": 4}
      ],
      "file_hash": "sha256:..."
    }
    Each paragraph is a block separated by blank lines.
    line_start/line_end are 1-indexed line numbers in full_text.md.
    """
    text = full_text_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    file_hash = file_sha256(full_text_path)

    paragraphs = []
    current = []
    start_line = 1
    idx = 0

    def flush():
        nonlocal idx, current, start_line
        if not current:
            return
        para_text = "\n".join(current)
        end_line = start_line + len(current) - 1
        paragraphs.append({
            "index": idx,
            "text": para_text[:500] + ("..." if len(para_text) > 500 else ""),
            "hash": "sha256:" + sha256_hex(para_text),
            "line_start": start_line,
            "line_end": end_line,
        })
        idx += 1
        current = []

    for lineno, line in enumerate(lines, 1):
        if line.strip() == "":
            flush()
            start_line = lineno + 1
        else:
            if not current:
                start_line = lineno
            current.append(line)
    flush()

    return {"paragraphs": paragraphs, "file_hash": "sha256:" + file_hash}


def assign_canonical_uuids(entities_raw: dict, text: str) -> dict:
    """
    Assign deterministic UUIDs to every entity in entities_raw.
    Order = first mention in text (case-insensitive substring search).
    Returns a dict: {canonical_entities, aliases_map, uuid_map}
    """
    def first_offset(name: str) -> int:
        if not name or not text:
            return 10_000_000
        # case-insensitive search
        idx = text.lower().find(name.lower())
        return idx if idx != -1 else 10_000_000

    prefixes = {
        "characters": "char",
        "locations": "loc",
        "objects": "obj",
        "factions": "fac",
    }

    canonical = {}
    aliases_map = {}   # canonical_name -> [alias, ...]
    uuid_map = {}      # original_name -> uuid
    used_uuids = set()

    for category, prefix in prefixes.items():
        items = entities_raw.get(category, [])
        # sort by first mention to get deterministic order
        sorted_items = sorted(items, key=lambda e: first_offset(
            e.get("name", "") if isinstance(e, dict) else str(e)
        ))
        canonical[category] = []
        for i, item in enumerate(sorted_items, 1):
            if isinstance(item, dict):
                name = item.get("name", "")
            else:
                name = str(item)
                item = {"name": name}
            uuid = f"{prefix}_{i:03d}"
            # dedup safety
            while uuid in used_uuids:
                i += 1
                uuid = f"{prefix}_{i:03d}"
            used_uuids.add(uuid)
            uuid_map[name] = uuid
            enriched = {
                **item,
                "_epistemic": "canon",
                "_uuid": uuid,
                "_category": category,
            }
            canonical[category].append(enriched)
            # alias tracking: if same uuid appears for different names later, merge
            canonical_name = name.lower().strip()
            if canonical_name not in aliases_map:
                aliases_map[canonical_name] = {"uuid": uuid, "aliases": [name]}

    # Collapse aliases_map to final shape: uuid -> [aliases]
    final_aliases = {}
    for key, val in aliases_map.items():
        final_aliases[val["uuid"]] = val["aliases"]

    return {
        "canonical": canonical,
        "aliases": final_aliases,
        "uuid_map": uuid_map,
    }
