#!/usr/bin/env python3
"""
validate_book2game.py — Gate-check a book2game workshop output folder.

Exit codes: 0 = OK, non-zero = FAIL (fail-loud).
Checks:
  1. full_text.md exists & non-empty
  2. index.json exists, valid JSON, has 'entries'
  3. chapters/ contains at least one .md
  4. entities.json exists & valid JSON object
  5. CITATION CHECK: every entity (characters/locations/objects/concepts)
     must have both a non-empty 'citation' and an integer 'line'.
"""
import json
import os
import sys


def check_entities_citations(path, errors):
    """Each entity must carry a citation string + a line number.
    Accepts both old flat format (citation + line) and new evidence array format (evidence[].quote + evidence[].line).
    """
    if not os.path.exists(path):
        errors.append(f"entities.json missing: {path}")
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.loads(f.read())
    except json.JSONDecodeError as e:
        errors.append(f"entities.json invalid JSON: {e}")
        return
    if not isinstance(data, dict):
        errors.append("entities.json: root is not a JSON object")
        return

    required_keys = ["characters", "locations", "objects", "concepts"]
    for key in required_keys:
        for i, entity in enumerate(data.get(key, [])):
            if not isinstance(entity, dict):
                errors.append(f"entities.json [{key}][{i}]: not an object")
                continue
            label = entity.get("name", f"#{i}")

            # Old flat format
            has_citation = "citation" in entity and isinstance(entity["citation"], str) and entity["citation"].strip()
            has_line = "line" in entity and isinstance(entity["line"], int)

            # New evidence array format
            if not (has_citation and has_line):
                evidence = entity.get("evidence", [])
                if isinstance(evidence, list) and evidence:
                    first_ev = evidence[0]
                    if isinstance(first_ev, dict):
                        has_citation = has_citation or ("quote" in first_ev and isinstance(first_ev["quote"], str) and first_ev["quote"].strip())
                        has_line = has_line or ("line" in first_ev and isinstance(first_ev["line"], int))

            if not has_citation:
                errors.append(f"entities.json [{key}] '{label}': missing citation (need 'citation' or 'evidence[0].quote')")
            if not has_line:
                errors.append(f"entities.json [{key}] '{label}': missing line number (need 'line' or 'evidence[0].line')")


def validate(out_dir="."):
    errors = []

    # New nested structure: full_text.md in source/
    full_text = os.path.join(out_dir, "source", "full_text.md")
    if not os.path.exists(full_text) or os.path.getsize(full_text) == 0:
        errors.append("source/full_text.md missing or empty")

    # index.json at root (unchanged)
    index_json = os.path.join(out_dir, "index.json")
    if not os.path.exists(index_json):
        errors.append("index.json missing")
    else:
        try:
            with open(index_json, "r", encoding="utf-8") as f:
                idx = json.loads(f.read())
            if not isinstance(idx, dict) or not idx.get("entries"):
                errors.append("index.json: missing 'entries'")
        except json.JSONDecodeError as e:
            errors.append(f"index.json invalid JSON: {e}")

    # chapters/ at root (unchanged)
    chapters_dir = os.path.join(out_dir, "chapters")
    if not os.path.isdir(chapters_dir) or not any(f.endswith(".md") for f in os.listdir(chapters_dir)):
        errors.append("chapters/: missing or no .md files")

    # New nested structure: entities.json in canon/
    entities_json = os.path.join(out_dir, "canon", "entities.json")
    check_entities_citations(entities_json, errors)

    if errors:
        print("GATE FAIL")
        for e in errors:
            print(f"  X {e}")
        sys.exit(1)

    print("GATE PASS")
    print(f"  source/full_text.md OK")
    print(f"  index.json OK")
    print(f"  chapters/ OK")
    print(f"  canon/entities.json citations OK")
    sys.exit(0)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    validate(out)
