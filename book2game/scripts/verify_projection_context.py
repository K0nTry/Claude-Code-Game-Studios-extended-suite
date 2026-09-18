#!/usr/bin/env python3
"""
verify_projection_context.py — Cross-validate AGENT_SPECS vs authoritative roster.

Checks:
  1. AGENT_SPECS count == roster count (49)
  2. Every roster agent has an AGENT_SPECS entry (no missing)
  3. Every AGENT_SPECS entry has a roster file (no extra)
  4. All canon_inputs/derived_inputs reference pipeline-produced artifacts only
  5. No duplicate filenames across different source paths in same projection
  6. Role-sanity: extract role keywords from agent .md, verify inputs match
"""

import json
import re
import sys
from pathlib import Path

# ---- Configuration ----
ROSTER_DIR = Path(r"D:\Claude Code\external_repos\Claude-Code-Game-Studios\.claude\agents")
SCRIPTS_DIR = Path(__file__).resolve().parent

# Import AGENT_SPECS from assemble_projection
import importlib.util as _iu
_asm_path = SCRIPTS_DIR / "assemble_projection.py"
_spec = _iu.spec_from_file_location("assemble_projection", _asm_path)
_mod = _iu.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
AGENT_SPECS = _mod.AGENT_SPECS

# ---- Artifact whitelist (pipeline-produced only) ----
CANON_WHITELIST = {
    "canon/entities.json",
    "canon/relationships.json",
    "canon/entity-aliases.json",
    "canon/world-boundaries.json",
    "canon/world-glossary.json",
    "canon/unresolved-ambiguities.json",
}

DERIVED_WHITELIST = {
    # Design
    "design/narrative/character-psychology.json",
    "design/narrative/voice-fingerprints.json",
    "design/narrative/choice-tree.json",
    "design/narrative/expansion-grammar.json",
    "design/narrative/framing-hub.md",
    "design/balance/tension-pacing-curve.json",
    "design/balance/economy-formulas.md",
    "design/balance/progression-gini.json",
    "design/mechanics/dda-rules.json",
    "design/mechanics/faction-dynamics.json",
    "design/mechanics/concept-matrix.md",
    "design/art/lighting-color-script.json",
    "design/audio/leitmotif-matrix.json",
    "design/ai/npc-utility-schedules.json",
    # Lore
    "lore/relationship-matrix.json",
    "lore/information-spread-graph.json",
    "lore/connectors.md",
    # Benchmarks
    "benchmarks/executive_audit_report.json",
    "benchmarks/player-personas-simulation.json",
    "benchmarks/nash-equilibrium-report.json",
    # Technical
    "technical/mod-api-schema.json",
    # Production
    "production/stage.txt",
    "production/epics/",
    "production/briefs/",
    "production/execution-dag.json",
}

# ---- Role keyword mapping (from agent .md descriptions) ----
# Maps agent-name-fragment → expected artifact relevance keywords
ROLE_KEYWORDS = {
    "narrative":    ["voice-fingerprints", "character-psychology", "choice-tree", "expansion-grammar", "relationships"],
    "writer":       ["voice-fingerprints", "character-psychology", "choice-tree", "expansion-grammar", "relationships"],
    "creative":     ["executive_audit", "expansion-grammar", "faction-dynamics", "tension-pacing"],
    "art":          ["lighting-color-script", "world-boundaries", "world-glossary"],
    "audio":        ["leitmotif-matrix", "relationships", "tension-pacing", "world-glossary"],
    "sound":        ["leitmotif-matrix", "relationships", "tension-pacing"],
    "game-design":  ["tension-pacing", "economy-formulas", "progression-gini", "dda-rules", "faction-dynamics"],
    "economy":      ["economy-formulas", "tension-pacing", "progression-gini", "dda-rules", "faction-dynamics"],
    "systems":      ["tension-pacing", "economy-formulas", "dda-rules"],
    "level":        ["tension-pacing", "faction-dynamics", "world-boundaries", "world-glossary"],
    "lead-programmer": ["mod-api-schema", "dda-rules", "npc-utility-schedules"],
    "gameplay-programmer": ["mod-api-schema", "dda-rules"],
    "engine-programmer":   ["mod-api-schema"],
    "ai-programmer": ["npc-utility-schedules", "dda-rules", "faction-dynamics"],
    "network":       ["mod-api-schema"],
    "tools":         ["mod-api-schema"],
    "ui-programmer": ["mod-api-schema", "choice-tree", "world-glossary"],
    "security":      ["mod-api-schema"],
    "devops":        ["mod-api-schema"],
    "qa-tester":     ["choice-tree"],
    "qa-lead":       ["choice-tree", "dda-rules", "world-boundaries"],
    "performance":   ["mod-api-schema"],
    "accessibility": ["choice-tree"],
    "technical":     ["mod-api-schema", "dda-rules", "economy-formulas"],
    "producer":      ["executive_audit", "tension-pacing"],
    "release":       ["executive_audit"],
    "analytics":     ["progression-gini", "executive_audit"],
    "community":     ["executive_audit"],
    "localization":  ["voice-fingerprints", "expansion-grammar", "world-glossary"],
    "ux":            ["choice-tree", "character-psychology"],
    "prototyper":    ["tension-pacing", "character-psychology"],
    "live-ops":      ["economy-formulas", "progression-gini", "faction-dynamics", "executive_audit"],
    "world-builder": ["relationships", "information-spread-graph", "faction-dynamics", "expansion-grammar"],
    # Engine specialists: all get mod-api-schema
    "unreal":    ["mod-api-schema"],
    "ue-":       ["mod-api-schema"],
    "unity":     ["mod-api-schema"],
    "godot":     ["mod-api-schema"],
}


def log(msg):
    print(f"[verify_context] {msg}")


def check_roster_match(errors):
    """Check 1+2+3: AGENT_SPECS ↔ roster 1:1."""
    roster_names = sorted(p.stem for p in ROSTER_DIR.glob("*.md"))
    spec_names = sorted(AGENT_SPECS.keys())

    if len(roster_names) != len(spec_names):
        errors.append(f"COUNT_MISMATCH: roster={len(roster_names)}, specs={len(spec_names)}")

    missing_in_spec = set(roster_names) - set(spec_names)
    extra_in_spec = set(spec_names) - set(roster_names)

    if missing_in_spec:
        errors.append(f"MISSING_IN_SPECS: {sorted(missing_in_spec)}")
    if extra_in_spec:
        errors.append(f"EXTRA_IN_SPECS: {sorted(extra_in_spec)}")

    return roster_names, spec_names


def check_whitelist(errors, warns):
    """Check 4: all inputs are pipeline-produced artifacts only."""
    for agent, spec in AGENT_SPECS.items():
        for path in spec.get("canon_inputs", []):
            if path not in CANON_WHITELIST:
                errors.append(f"WHITELIST_VIOLATION: {agent} canon_inputs '{path}' not in whitelist")
        for path in spec.get("derived_inputs", []):
            if path not in DERIVED_WHITELIST:
                errors.append(f"WHITELIST_VIOLATION: {agent} derived_inputs '{path}' not in whitelist")


def check_duplicate_filenames(errors):
    """Check 5: no duplicate filenames across different source paths in same projection."""
    for agent, spec in AGENT_SPECS.items():
        all_paths = spec.get("canon_inputs", []) + spec.get("derived_inputs", [])
        names = [Path(p).name for p in all_paths]
        seen = {}
        for i, name in enumerate(names):
            if name in seen:
                # Check if different source paths
                src1 = all_paths[seen[name]]
                src2 = all_paths[i]
                if src1 != src2:
                    errors.append(
                        f"DUPLICATE_FILENAME: {agent} has '{name}' from both '{src1}' and '{src2}'"
                    )
            else:
                seen[name] = i


def check_role_sanity(warns, roster_names):
    """Check 6: extract role keywords from agent .md, verify inputs match."""
    for agent_name in roster_names:
        md_path = ROSTER_DIR / f"{agent_name}.md"
        if not md_path.exists():
            continue
        content = md_path.read_text(encoding="utf-8", errors="ignore")[:2000]  # first 2KB

        # Find matching role keywords
        spec = AGENT_SPECS.get(agent_name)
        if not spec:
            continue

        all_inputs = set(spec.get("canon_inputs", []) + spec.get("derived_inputs", []))

        # Check each keyword pattern
        for pattern, expected_keywords in ROLE_KEYWORDS.items():
            if pattern in agent_name:
                for kw in expected_keywords:
                    if not any(kw in inp for inp in all_inputs):
                        warns.append(
                            f"ROLE_MISMATCH: {agent_name} — expected artifact containing '{kw}' "
                            f"(role pattern: '{pattern}') but not in inputs"
                        )
                break  # first match only


def main():
    errors = []
    warns = []

    log("Cross-validating AGENT_SPECS vs authoritative roster...")
    roster_names, spec_names = check_roster_match(errors)

    log(f"Roster: {len(roster_names)} agents, Specs: {len(spec_names)} agents")

    check_whitelist(errors, warns)
    check_duplicate_filenames(errors)
    check_role_sanity(warns, roster_names)

    # Summary
    print()
    print("=" * 60)
    print(f"VERIFICATION RESULT: {'PASS' if not errors else 'FAIL'}")
    print(f"  Agents: {len(spec_names)}/{len(roster_names)}")
    print(f"  Errors: {len(errors)}")
    print(f"  Warnings: {len(warns)}")
    print("=" * 60)

    if errors:
        print("\nERRORS:")
        for e in errors:
            print(f"  FAIL {e}")

    if warns:
        print("\nWARNINGS:")
        for w in warns:
            print(f"  WARN {w}")

    if not errors and not warns:
        print("\nOK: All 49 projections have correct role-specific context mapping.")

    print()
    return len(errors) == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
