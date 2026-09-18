#!/usr/bin/env python3
"""validate_output.py — ελέγχει ότι ο φάκελος περνάει gate-check concept, Studio MCP integration και archetype artifacts."""

import json
import sys
from pathlib import Path

VALID_ENGINES = ["godot", "unity", "unreal", "phaser", "custom"]
MCP_MAPPINGS = {
    "godot": ["godot mcp", "godot headless", "gut", "godot-specialist"],
    "unity": ["unity mcp", "unity bridge", "unity-specialist", "websocket"],
    "unreal": ["unreal mcp", "unreal remote", "unreal-specialist", "gas"],
    "phaser": ["node", "playwright", "puppeteer", "browser", "vite"],
    "custom": ["cli", "gdb", "lldb", "subprocess", "engine-programmer"]
}

def check(out_dir: Path):
    errors = []
    warns = []

    def need(rel, min_chars=10):
        p = out_dir / rel
        if not p.exists():
            errors.append(f"MISSING: {rel}")
            return None
        t = p.read_text(encoding="utf-8", errors="ignore")
        if len(t.strip()) < min_chars:
            errors.append(f"EMPTY: {rel} ({len(t)} chars)")
        return t

    # 1. Required core files
    need("full_text.md", 100)
    need("index.json", 10)
    need("entities.json", 10)
    need("archetype.json", 10)
    need("production/execution-dag.json", 20)
    need("design/gdd/game-concept.md", 500)
    need("design/gdd/systems-index.md", 100)
    need("design/gdd/game-pillars.md", 50)
    need("design/art/art-bible.md", 50)
    need("active.md", 50)
    need("roadmap.md", 50)
    need("design.md", 20)
    need("README.md", 100)
    need("game_blueprint.md", 300)
    need("docs/studio-workflow.md", 150)
    # Cycles 5-12: advanced artifacts (critical path validation)
    need("design/narrative/character-psychology.json", 20)
    need("design/narrative/voice-fingerprints.json", 20)
    need("lore/relationship-matrix.json", 10)
    need("design/balance/tension-pacing-curve.json", 20)
    need("design/narrative/choice-tree.json", 30)
    need("benchmarks/player-personas-simulation.json", 20)
    need("benchmarks/executive_audit_report.json", 50)
    need("design/audio/leitmotif-matrix.json", 20)
    need("lore/information-spread-graph.json", 20)
    need("benchmarks/nash-equilibrium-report.json", 20)
    need("design/narrative/expansion-grammar.json", 20)
    need("design/mechanics/dda-rules.json", 10)
    need("technical/mod-api-schema.json", 10)

    # 2. Stage verification
    stage = out_dir / "production" / "stage.txt"
    if not stage.exists():
        errors.append("MISSING: production/stage.txt")
    else:
        if stage.read_text(encoding="utf-8").strip() != "concept":
            warns.append("stage.txt != concept")

    # 3. Technical Engine & MCP Server Compatibility
    engine_text = need("technical/engine.md", 150)
    if engine_text:
        engine_lower = engine_text.lower()
        matched_engine = None
        for eng in VALID_ENGINES:
            if eng in engine_lower:
                matched_engine = eng
                break

        if not matched_engine:
            errors.append(f"technical/engine.md does not specify a valid engine ({', '.join(VALID_ENGINES)})")
        else:
            if "justification" not in engine_lower and "αιτιολόγηση" not in engine_lower:
                warns.append("technical/engine.md missing explicit justification section")
            if "mcp" not in engine_lower:
                errors.append("technical/engine.md does not define Game Studio MCP server integration")
            else:
                mcp_reqs = MCP_MAPPINGS[matched_engine]
                if not any(req in engine_lower for req in mcp_reqs):
                    warns.append(f"technical/engine.md for {matched_engine} may be missing specific MCP tooling ({', '.join(mcp_reqs)})")

    # 4. game_blueprint.md checks
    gb_text = need("game_blueprint.md", 300)
    if gb_text:
        if "engine" not in gb_text.lower() and "μηχανή" not in gb_text.lower():
            errors.append("game_blueprint.md missing Engine Selection section")
        if "elevator pitch" not in gb_text.lower():
            warns.append("game_blueprint.md missing Elevator Pitch")

    # 5. index.json valid
    try:
        data = json.loads((out_dir / "index.json").read_text(encoding="utf-8"))
        if not data.get("entries"):
            errors.append("index.json: no entries")
    except Exception as e:
        errors.append(f"index.json invalid: {e}")

    # 6. entities.json valid
    try:
        e = json.loads((out_dir / "entities.json").read_text(encoding="utf-8"))
        if not isinstance(e, dict):
            errors.append("entities.json: not an object")
    except Exception as e:
        errors.append(f"entities.json invalid: {e}")

    # 7. game-concept 9 sections
    gc = need("design/gdd/game-concept.md", 0)
    if gc:
        required = ["Elevator Pitch", "Core Identity", "MDA", "Core Loop", "Game Pillars", "MVP"]
        for r in required:
            if r.lower() not in gc.lower():
                warns.append(f"game-concept.md missing section hint: {r}")

    # 8. chapters
    ch_dir = out_dir / "chapters"
    if not ch_dir.exists() or not list(ch_dir.glob("*.md")):
        errors.append("chapters/: no .md files")

    # Final verdict
    if errors:
        print("GATE FAIL")
        for e in errors:
            print(f"  X {e}")
        for w in warns:
            print(f"  ! {w}")
        return 1
    else:
        print("GATE PASS")
        for w in warns:
            print(f"  ! {w}")
        print(f"  Checked: {out_dir}")
        return 0

if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    sys.exit(check(out.resolve()))
