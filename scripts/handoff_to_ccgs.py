#!/usr/bin/env python3
"""
handoff_to_ccgs.py — Map book2game workshop output into CCGS-ready
game concept files.

FAIL-LOUD policy: every required source file must exist, otherwise the
script reports the missing file(s) to stderr and exits non-zero. It never
silently skips missing inputs.

entities.json is converted to readable Markdown (entity-registry.md) — it
is never copied as raw JSON text into a .md file.
"""
import os
import sys
import json
import shutil

# src (relative to workshop output dir) -> dst (relative to repo root)
MAPPING = {
    "full_text.md": "design/lore/source_text.md",
    "chapters": "design/lore/chapters",
    "index.json": "design/rag/index.json",
    "entities.json": "design/entities/entity-registry.md",   # JSON -> Markdown
    "design/gdd/game-concept.md": "design/gdd/game-concept.md",
}


def fail(msg, code=1):
    """Print error to stderr and exit."""
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def _cell(v):
    """Render a JSON value as a markdown table cell."""
    if isinstance(v, list):
        return ", ".join(str(x) for x in v)
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)


def entities_to_markdown(data: dict) -> str:
    """Convert the entities.json structure into a human-readable registry."""
    out = []
    out.append("# Entity Registry")
    out.append("")
    out.append("> Converted from `entities.json` by `handoff_to_ccgs.py`.")
    out.append("")

    def table(title, items, cols):
        out.append(f"## {title}")
        out.append("")
        if not items:
            out.append("- _none_")
            out.append("")
            return
        out.append("| " + " | ".join(cols) + " |")
        out.append("| " + " | ".join(["---"] * len(cols)) + " |")
        for it in items:
            out.append("| " + " | ".join(_cell(it.get(c, "")) for c in cols) + " |")
        out.append("")

    table("Characters", data.get("characters", []), ["name", "role", "traits"])
    table("Locations", data.get("locations", []), ["name", "type", "description"])
    table("Objects", data.get("objects", []), ["name", "type", "description"])
    table("Concepts", data.get("concepts", []), ["name", "category"])
    table("Relationships", data.get("relationships", []), ["source", "relation", "target"])
    table("Factions", data.get("factions", []), ["name", "description"])
    table("Timeline", data.get("timeline", []), ["event", "chapter", "description"])

    # Raw JSON as a collapsible block for traceability (NOT the primary content).
    out.append("## Source JSON")
    out.append("")
    out.append("<details>")
    out.append("")
    out.append("```json")
    out.append(json.dumps(data, indent=2, ensure_ascii=False))
    out.append("```")
    out.append("")
    out.append("</details>")
    out.append("")
    return "\n".join(out)


def copy_mapping(src_dir, dst_root):
    missing = []

    for src_key, dst_rel in MAPPING.items():
        src_full = os.path.join(src_dir, src_key)

        # FAIL-LOUD: required source must exist.
        if not os.path.exists(src_full):
            missing.append(src_key)
            continue

        dst_full = os.path.join(dst_root, dst_rel)
        os.makedirs(os.path.dirname(dst_full), exist_ok=True)

        # entities.json -> readable markdown (not raw JSON)
        if src_key == "entities.json":
            try:
                with open(src_full, "r", encoding="utf-8") as f:
                    data = json.loads(f.read())
            except json.JSONDecodeError as e:
                fail(f"entities.json is not valid JSON: {e}")
            if not isinstance(data, dict):
                fail("entities.json root is not a JSON object")
            with open(dst_full, "w", encoding="utf-8") as f:
                f.write(entities_to_markdown(data))
            print(f"  wrote markdown: {dst_rel}")
            continue

        # directories
        if os.path.isdir(src_full):
            shutil.copytree(src_full, dst_full, dirs_exist_ok=True)
            print(f"  copied dir:  {dst_rel}")
        else:
            shutil.copy2(src_full, dst_full)
            print(f"  copied file: {dst_rel}")

    if missing:
        fail("missing required source file(s): " + ", ".join(missing))

    # Post-condition: game-concept.md must exist and be non-empty.
    gc_src = "design/gdd/game-concept.md"
    gc = os.path.join(dst_root, MAPPING[gc_src])
    if not os.path.exists(gc):
        fail(f"post-check: {gc} not produced by handoff")
    size = os.path.getsize(gc)
    if size == 0:
        fail(f"post-check: {gc} is empty (source was empty)")
    print(f"  game-concept.md OK ({size} bytes)")


def main():
    if len(sys.argv) < 2:
        print("Usage: handoff_to_ccgs.py <workshop-output-dir> [repo-root]")
        sys.exit(2)
    src = sys.argv[1]
    dst_root = sys.argv[2] if len(sys.argv) > 2 else "."

    if not os.path.isdir(src):
        fail(f"workshop output dir does not exist: {src}")

    print(f"Handoff: {src} -> {dst_root}")
    copy_mapping(src, dst_root)
    print("Handoff complete")
    sys.exit(0)


if __name__ == "__main__":
    main()
