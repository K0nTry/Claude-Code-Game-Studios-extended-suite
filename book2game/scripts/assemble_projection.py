#!/usr/bin/env python3
"""
assemble_projection.py — Projection assembler for book2game.

Assembles agent-specific views from canon + derived artifacts.
Each projection is self-contained with an IMMUTABLE_KERNEL.md.

Usage:
  python assemble_projection.py <project_dir> --agent narrative-director
  python assemble_projection.py <project_dir> --all
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    from canon_helpers import file_sha256, sha256_hex
except ImportError:
    try:
        from scripts.canon_helpers import file_sha256, sha256_hex
    except ImportError:
        def sha256_hex(t):
            import hashlib
            return hashlib.sha256(t.encode("utf-8")).hexdigest()
        def file_sha256(p):
            import hashlib
            h = hashlib.sha256()
            with open(p, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
            return h.hexdigest()


TOOL_VERSION = "book2game v2.0.0"

# ---- Agent projection specs ----
# Source of truth: D:\Claude Code\external_repos\Claude-Code-Game-Studios\.claude\agents\ (49 agents)
# All inputs validated against book2game pipeline artifact whitelist.
# Canon: write_canon_layer() output. Derived: write_advanced_artifacts() + exec_audit output.

AGENT_SPECS = {
    # ── Tier 1: Directors ──────────────────────────────────────────
    "creative-director": {
        "description": "Creative Director — High-level vision",
        "canon_inputs": ["canon/entities.json", "canon/relationships.json", "canon/world-boundaries.json", "canon/world-glossary.json", "canon/entity-aliases.json"],
        "derived_inputs": ["benchmarks/executive_audit_report.json", "design/balance/tension-pacing-curve.json", "design/narrative/expansion-grammar.json", "design/mechanics/faction-dynamics.json"],
    },
    "technical-director": {
        "description": "Technical Director — Technical vision",
        "canon_inputs": ["canon/entities.json", "canon/world-boundaries.json"],
        "derived_inputs": ["technical/mod-api-schema.json", "design/mechanics/dda-rules.json", "design/balance/economy-formulas.md"],
    },
    "producer": {
        "description": "Producer — Production management",
        "canon_inputs": ["canon/entities.json"],
        "derived_inputs": ["benchmarks/executive_audit_report.json", "design/balance/tension-pacing-curve.json"],
    },
    # ── Tier 2: Leads ──────────────────────────────────────────────
    "game-designer": {
        "description": "Game Designer — Game design",
        "canon_inputs": ["canon/entities.json", "canon/world-boundaries.json"],
        "derived_inputs": ["design/balance/tension-pacing-curve.json", "design/balance/economy-formulas.md", "design/balance/progression-gini.json", "design/mechanics/dda-rules.json", "design/mechanics/faction-dynamics.json"],
    },
    "lead-programmer": {
        "description": "Lead Programmer — Code architecture",
        "canon_inputs": ["canon/entities.json", "canon/world-boundaries.json"],
        "derived_inputs": ["technical/mod-api-schema.json", "design/mechanics/dda-rules.json", "design/ai/npc-utility-schedules.json"],
    },
    "narrative-director": {
        "description": "Narrative Director — Story and writing",
        "canon_inputs": ["canon/entities.json", "canon/relationships.json", "canon/world-glossary.json", "canon/entity-aliases.json"],
        "derived_inputs": ["design/narrative/character-psychology.json", "design/narrative/voice-fingerprints.json", "design/narrative/choice-tree.json", "design/narrative/expansion-grammar.json"],
    },
    "art-director": {
        "description": "Art Director — Visual direction",
        "canon_inputs": ["canon/entities.json", "canon/world-boundaries.json", "canon/world-glossary.json"],
        "derived_inputs": ["design/art/lighting-color-script.json"],
    },
    "audio-director": {
        "description": "Audio Director — Audio direction",
        "canon_inputs": ["canon/entities.json", "canon/relationships.json", "canon/world-glossary.json"],
        "derived_inputs": ["design/audio/leitmotif-matrix.json", "design/balance/tension-pacing-curve.json"],
    },
    "qa-lead": {
        "description": "QA Lead — Quality assurance",
        "canon_inputs": ["canon/entities.json", "canon/world-boundaries.json"],
        "derived_inputs": ["design/narrative/choice-tree.json", "design/mechanics/dda-rules.json"],
    },
    "release-manager": {
        "description": "Release Manager — Release pipeline",
        "canon_inputs": ["canon/entities.json"],
        "derived_inputs": ["benchmarks/executive_audit_report.json"],
    },
    "localization-lead": {
        "description": "Localization Lead — Internationalization",
        "canon_inputs": ["canon/entities.json", "canon/world-glossary.json", "canon/entity-aliases.json"],
        "derived_inputs": ["design/narrative/voice-fingerprints.json", "design/narrative/expansion-grammar.json"],
    },
    # ── Tier 3: Design Specialists ─────────────────────────────────
    "systems-designer": {
        "description": "Systems Designer — Systems design",
        "canon_inputs": ["canon/entities.json", "canon/world-boundaries.json"],
        "derived_inputs": ["design/balance/tension-pacing-curve.json", "design/balance/economy-formulas.md", "design/mechanics/dda-rules.json"],
    },
    "level-designer": {
        "description": "Level Designer — Level design",
        "canon_inputs": ["canon/entities.json", "canon/world-boundaries.json", "canon/world-glossary.json"],
        "derived_inputs": ["design/balance/tension-pacing-curve.json", "design/mechanics/faction-dynamics.json"],
    },
    "economy-designer": {
        "description": "Economy Designer — Economy/balance",
        "canon_inputs": ["canon/entities.json"],
        "derived_inputs": ["design/balance/tension-pacing-curve.json", "design/balance/economy-formulas.md", "design/balance/progression-gini.json", "design/mechanics/dda-rules.json", "design/mechanics/faction-dynamics.json"],
    },
    "technical-artist": {
        "description": "Technical Artist — Tech art",
        "canon_inputs": ["canon/entities.json", "canon/world-boundaries.json", "canon/world-glossary.json"],
        "derived_inputs": ["design/art/lighting-color-script.json"],
    },
    "sound-designer": {
        "description": "Sound Designer — Sound design",
        "canon_inputs": ["canon/entities.json", "canon/relationships.json"],
        "derived_inputs": ["design/audio/leitmotif-matrix.json", "design/balance/tension-pacing-curve.json"],
    },
    "writer": {
        "description": "Writer — Dialogue/lore",
        "canon_inputs": ["canon/entities.json", "canon/relationships.json", "canon/world-glossary.json", "canon/entity-aliases.json"],
        "derived_inputs": ["design/narrative/voice-fingerprints.json", "design/narrative/character-psychology.json", "design/narrative/choice-tree.json", "design/narrative/expansion-grammar.json"],
    },
    "world-builder": {
        "description": "World Builder — World/lore design",
        "canon_inputs": ["canon/entities.json", "canon/relationships.json", "canon/world-boundaries.json", "canon/world-glossary.json"],
        "derived_inputs": ["lore/relationship-matrix.json", "lore/information-spread-graph.json", "design/mechanics/faction-dynamics.json", "design/narrative/expansion-grammar.json"],
    },
    "ux-designer": {
        "description": "UX Designer — UX flows",
        "canon_inputs": ["canon/entities.json", "canon/world-glossary.json"],
        "derived_inputs": ["design/narrative/choice-tree.json", "design/narrative/character-psychology.json"],
    },
    "prototyper": {
        "description": "Prototyper — Rapid prototyping",
        "canon_inputs": ["canon/entities.json", "canon/world-boundaries.json"],
        "derived_inputs": ["design/balance/tension-pacing-curve.json", "design/narrative/character-psychology.json"],
    },
    "live-ops-designer": {
        "description": "Live-Ops Designer — Live operations",
        "canon_inputs": ["canon/entities.json", "canon/world-boundaries.json"],
        "derived_inputs": ["design/balance/economy-formulas.md", "design/balance/progression-gini.json", "design/mechanics/faction-dynamics.json", "benchmarks/executive_audit_report.json"],
    },
    # ── Tier 3: Programmers ────────────────────────────────────────
    "gameplay-programmer": {
        "description": "Gameplay Programmer — Gameplay code",
        "canon_inputs": ["canon/entities.json", "canon/world-boundaries.json"],
        "derived_inputs": ["technical/mod-api-schema.json", "design/mechanics/dda-rules.json"],
    },
    "engine-programmer": {
        "description": "Engine Programmer — Engine systems",
        "canon_inputs": ["canon/entities.json", "canon/world-boundaries.json"],
        "derived_inputs": ["technical/mod-api-schema.json"],
    },
    "ai-programmer": {
        "description": "AI Programmer — AI systems",
        "canon_inputs": ["canon/entities.json", "canon/relationships.json"],
        "derived_inputs": ["design/ai/npc-utility-schedules.json", "design/mechanics/dda-rules.json", "design/mechanics/faction-dynamics.json"],
    },
    "network-programmer": {
        "description": "Network Programmer — Networking",
        "canon_inputs": ["canon/entities.json"],
        "derived_inputs": ["technical/mod-api-schema.json"],
    },
    "tools-programmer": {
        "description": "Tools Programmer — Dev tools",
        "canon_inputs": ["canon/entities.json"],
        "derived_inputs": ["technical/mod-api-schema.json"],
    },
    "ui-programmer": {
        "description": "UI Programmer — UI implementation",
        "canon_inputs": ["canon/entities.json", "canon/world-glossary.json"],
        "derived_inputs": ["technical/mod-api-schema.json", "design/narrative/choice-tree.json"],
    },
    # ── Tier 3: QA / Test / Security / Accessibility ───────────────
    "qa-tester": {
        "description": "QA Tester — Test execution",
        "canon_inputs": ["canon/entities.json"],
        "derived_inputs": ["design/narrative/choice-tree.json"],
    },
    "performance-analyst": {
        "description": "Performance Analyst — Performance",
        "canon_inputs": ["canon/entities.json"],
        "derived_inputs": ["technical/mod-api-schema.json"],
    },
    "security-engineer": {
        "description": "Security Engineer — Security",
        "canon_inputs": ["canon/entities.json"],
        "derived_inputs": ["technical/mod-api-schema.json"],
    },
    "accessibility-specialist": {
        "description": "Accessibility Specialist — Accessibility",
        "canon_inputs": ["canon/entities.json"],
        "derived_inputs": ["design/narrative/choice-tree.json"],
    },
    # ── Tier 3: Ops / Community / Analytics ─────────────────────────
    "devops-engineer": {
        "description": "DevOps Engineer — Build/deploy",
        "canon_inputs": ["canon/entities.json"],
        "derived_inputs": ["technical/mod-api-schema.json"],
    },
    "analytics-engineer": {
        "description": "Analytics Engineer — Telemetry",
        "canon_inputs": ["canon/entities.json"],
        "derived_inputs": ["design/balance/progression-gini.json", "benchmarks/executive_audit_report.json"],
    },
    "community-manager": {
        "description": "Community Manager — Community",
        "canon_inputs": ["canon/entities.json"],
        "derived_inputs": ["benchmarks/executive_audit_report.json"],
    },
    # ── Engine-Specific: Unreal ─────────────────────────────────────
    "unreal-specialist": {
        "description": "Unreal Specialist — Unreal Engine 5",
        "canon_inputs": ["canon/entities.json", "canon/world-boundaries.json"],
        "derived_inputs": ["technical/mod-api-schema.json"],
    },
    "ue-gas-specialist": {
        "description": "UE GAS Specialist — Gameplay Ability System",
        "canon_inputs": ["canon/entities.json", "canon/world-boundaries.json"],
        "derived_inputs": ["technical/mod-api-schema.json"],
    },
    "ue-blueprint-specialist": {
        "description": "UE Blueprint Specialist — Blueprint Architecture",
        "canon_inputs": ["canon/entities.json"],
        "derived_inputs": ["technical/mod-api-schema.json"],
    },
    "ue-replication-specialist": {
        "description": "UE Replication Specialist — Networking/Replication",
        "canon_inputs": ["canon/entities.json"],
        "derived_inputs": ["technical/mod-api-schema.json"],
    },
    "ue-umg-specialist": {
        "description": "UE UMG Specialist — UMG/CommonUI",
        "canon_inputs": ["canon/entities.json"],
        "derived_inputs": ["technical/mod-api-schema.json"],
    },
    # ── Engine-Specific: Unity ──────────────────────────────────────
    "unity-specialist": {
        "description": "Unity Specialist — Unity",
        "canon_inputs": ["canon/entities.json", "canon/world-boundaries.json"],
        "derived_inputs": ["technical/mod-api-schema.json"],
    },
    "unity-dots-specialist": {
        "description": "Unity DOTS Specialist — DOTS/ECS",
        "canon_inputs": ["canon/entities.json"],
        "derived_inputs": ["technical/mod-api-schema.json"],
    },
    "unity-shader-specialist": {
        "description": "Unity Shader Specialist — Shaders/VFX",
        "canon_inputs": ["canon/entities.json"],
        "derived_inputs": ["technical/mod-api-schema.json"],
    },
    "unity-addressables-specialist": {
        "description": "Unity Addressables Specialist — Asset Management",
        "canon_inputs": ["canon/entities.json"],
        "derived_inputs": ["technical/mod-api-schema.json"],
    },
    "unity-ui-specialist": {
        "description": "Unity UI Specialist — UI Toolkit/UGUI",
        "canon_inputs": ["canon/entities.json"],
        "derived_inputs": ["technical/mod-api-schema.json"],
    },
    # ── Engine-Specific: Godot ──────────────────────────────────────
    "godot-specialist": {
        "description": "Godot Specialist — Godot 4",
        "canon_inputs": ["canon/entities.json", "canon/world-boundaries.json"],
        "derived_inputs": ["technical/mod-api-schema.json"],
    },
    "godot-gdscript-specialist": {
        "description": "Godot GDScript Specialist — GDScript",
        "canon_inputs": ["canon/entities.json"],
        "derived_inputs": ["technical/mod-api-schema.json"],
    },
    "godot-csharp-specialist": {
        "description": "Godot C# Specialist — C# / .NET",
        "canon_inputs": ["canon/entities.json"],
        "derived_inputs": ["technical/mod-api-schema.json"],
    },
    "godot-shader-specialist": {
        "description": "Godot Shader Specialist — Shaders/Rendering",
        "canon_inputs": ["canon/entities.json"],
        "derived_inputs": ["technical/mod-api-schema.json"],
    },
    "godot-gdextension-specialist": {
        "description": "Godot GDExtension Specialist — GDExtension",
        "canon_inputs": ["canon/entities.json"],
        "derived_inputs": ["technical/mod-api-schema.json"],
    },
}


def log(msg):
    print(f"[assemble_projection] {msg}")


def build_kernel(agent_name: str, source_hash: str, canon_version: str,
                 derived_version: str, projection_timestamp: str,
                 canon_count: int, derived_count: int, open_space_count: int) -> dict:
    return {
        "tool_version": TOOL_VERSION,
        "source_hash": source_hash,
        "canon_version": canon_version,
        "derived_version": derived_version,
        "extraction_timestamp": projection_timestamp,
        "canonical_uuids_present": canon_count,
        "open_space_count": open_space_count,
        "epistemic_breakdown": {
            "canon": canon_count,
            "derived": derived_count,
            "open_space": open_space_count,
        },
        "projection_agent": agent_name,
    }


def count_epistemic(data):
    """Count epistemic fields in a JSON structure."""
    if isinstance(data, dict):
        epi = data.get("_epistemic", "")
        if epi == "canon":
            return 1, 0, 0
        elif epi == "derived":
            return 0, 1, 0
        elif epi == "open_space":
            return 0, 0, 1
        # recurse
        c, d, o = 0, 0, 0
        for v in data.values():
            cc, dd, oo = count_epistemic(v)
            c += cc; d += dd; o += oo
        return c, d, o
    elif isinstance(data, list):
        c, d, o = 0, 0, 0
        for item in data:
            cc, dd, oo = count_epistemic(item)
            c += cc; d += dd; o += oo
        return c, d, o
    return 0, 0, 0


def load_artifact(project_dir: Path, rel_path: str):
    """Load a JSON or MD artifact, return (data, mtime_iso)."""
    p = project_dir / rel_path
    if not p.exists():
        return None, ""
    mtime = datetime.fromtimestamp(p.stat().st_mtime).isoformat()
    if p.suffix == ".json":
        try:
            return json.loads(p.read_text(encoding="utf-8")), mtime
        except Exception:
            return None, mtime
    else:
        return p.read_text(encoding="utf-8"), mtime


def assemble_agent(project_dir: Path, agent_name: str, spec: dict) -> bool:
    """Assemble a single agent projection."""
    proj_dir = project_dir / "views" / "projections" / agent_name
    proj_dir.mkdir(parents=True, exist_ok=True)

    # Collect all artifacts
    all_canon = {}
    all_derived = {}
    canon_count = 0
    derived_count = 0
    open_space_count = 0
    latest_canon_time = ""
    latest_derived_time = ""
    has_any = False

    for rel in spec["canon_inputs"]:
        data, mtime = load_artifact(project_dir, rel)
        if data is not None:
            all_canon[Path(rel).name] = data
            c, d, o = count_epistemic(data)
            canon_count += c
            derived_count += d
            open_space_count += o
            if mtime > latest_canon_time:
                latest_canon_time = mtime
            has_any = True

    for rel in spec["derived_inputs"]:
        data, mtime = load_artifact(project_dir, rel)
        if data is not None:
            all_derived[Path(rel).name] = data
            c, d, o = count_epistemic(data)
            canon_count += c
            derived_count += d
            open_space_count += o
            if mtime > latest_derived_time:
                latest_derived_time = mtime
            has_any = True

    if not has_any:
        log(f"  {agent_name}: SKIPPED — no source artifacts found")
        return False

    # Source hash
    ft_path = project_dir / "full_text.md"
    source_hash = "sha256:" + file_sha256(ft_path) if ft_path.exists() else "sha256:none"

    # Build kernel
    kernel = build_kernel(
        agent_name=agent_name,
        source_hash=source_hash,
        canon_version=latest_canon_time,
        derived_version=latest_derived_time,
        projection_timestamp=datetime.now().isoformat(),
        canon_count=canon_count,
        derived_count=derived_count,
        open_space_count=open_space_count,
    )

    # Write IMMUTABLE_KERNEL.md
    kernel_md = f"""# Immutable Kernel — {agent_name}

| Field | Value |
|-------|-------|
| tool_version | {kernel['tool_version']} |
| source_hash | {kernel['source_hash'][:32]}... |
| canon_version | {kernel['canon_version']} |
| derived_version | {kernel['derived_version']} |
| extraction_timestamp | {kernel['extraction_timestamp']} |
| canonical_uuids_present | {kernel['canonical_uuids_present']} |
| open_space_count | {kernel['open_space_count']} |
| epistemic_breakdown | canon: {canon_count}, derived: {derived_count}, open_space: {open_space_count} |
"""
    (proj_dir / "IMMUTABLE_KERNEL.md").write_text(kernel_md, encoding="utf-8")

    # Write canon projection files
    if all_canon:
        canon_proj = {
            "_kernel": kernel,
            "_epistemic_layer": "canon",
            **all_canon,
        }
        (proj_dir / "canon.projection.json").write_text(
            json.dumps(canon_proj, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # Write derived projection files
    if all_derived:
        derived_proj = {
            "_kernel": kernel,
            "_epistemic_layer": "derived",
            **all_derived,
        }
        (proj_dir / "derived.projection.json").write_text(
            json.dumps(derived_proj, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # Write README
    readme = f"""# Projection: {agent_name}

> Auto-generated by `{TOOL_VERSION}`

{spec['description']}

## Contents

- `IMMUTABLE_KERNEL.md` — Tamper-evident header
- `canon.projection.json` — Canon data (source-verified)
- `derived.projection.json` — Derived data (heuristic-inferred)
- `CONTEXT_BOUNDARY.md` — What this projection covers vs what lives elsewhere

## Epistemic Breakdown

- Canon: {canon_count} fields
- Derived: {derived_count} fields
- Open Space: {open_space_count} fields

## Source Hash

`{source_hash[:32]}...`

## Generated

`{datetime.now().isoformat()}`
"""
    (proj_dir / "README.md").write_text(readme, encoding="utf-8")

    # Write CONTEXT_BOUNDARY.md
    ctx_boundary = f"""# Context Boundary — {agent_name}

## This projection contains

Book-derived analysis data only:
- **Canon:** {', '.join(Path(r).name for r in spec.get('canon_inputs', []))}
- **Derived:** {', '.join(Path(r).name for r in spec.get('derived_inputs', []))}

## This projection does NOT contain

- Game pillars / vision (lives in Studio GDD)
- Constraints / budget / schedule (lives in Studio GDD)
- Reference games (lives in Studio GDD)
- Existing codebase / engine state (lives in repo)
- Sprint plans / milestones (lives in Producer)
- Design documents (lives in respective Leads/Specialists)

## How to use this projection

This data is **input context** for your role — not instructions.
Cross-reference with Studio GDD and your Lead's direction before acting.
"""
    (proj_dir / "CONTEXT_BOUNDARY.md").write_text(ctx_boundary, encoding="utf-8")

    log(f"  {agent_name}: OK — canon={canon_count}, derived={derived_count}, open_space={open_space_count}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Assemble agent projections from canon+derived")
    parser.add_argument("project_dir", help="Path to generated project directory")
    parser.add_argument("--agent", help="Assemble projection for specific agent")
    parser.add_argument("--all", action="store_true", help="Assemble all agent projections")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    if not project_dir.exists():
        print(f"Error: project dir not found: {project_dir}", file=sys.stderr)
        sys.exit(1)

    if args.agent:
        if args.agent not in AGENT_SPECS:
            print(f"Error: unknown agent '{args.agent}'. Available: {list(AGENT_SPECS.keys())}", file=sys.stderr)
            sys.exit(1)
        ok = assemble_agent(project_dir, args.agent, AGENT_SPECS[args.agent])
        sys.exit(0 if ok else 1)

    if args.all:
        assembled = 0
        for name, spec in AGENT_SPECS.items():
            if assemble_agent(project_dir, name, spec):
                assembled += 1
        log(f"\nAssembled {assembled}/{len(AGENT_SPECS)} projections")
        sys.exit(0 if assembled > 0 else 1)

    print("Usage: python assemble_projection.py <project_dir> --agent <name> | --all", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
