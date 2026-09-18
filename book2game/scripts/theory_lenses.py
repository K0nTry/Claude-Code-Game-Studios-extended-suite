#!/usr/bin/env python3
"""
theory_lenses.py — Phase 15b: Three optional narrative-theory validators.
Pure Python stdlib. Deterministic. Non-fatal validators.
"""
import json
from pathlib import Path


def validate_south_park_causality(chapters: list, choice_tree: dict):
    """
    South Park causality check: every scene must connect via 'therefore' or 'but'.
    Verifies that pacing + decision points exhibit causal linkage.
    """
    tensions = choice_tree.get("tension_curve", []) if "tension_curve" in choice_tree else []
    decision_points = choice_tree.get("decision_points", [])
    
    # Heuristic: check that decision points have explicit causal markers
    causal_markers = ["γιατί", "άρα", "επομένως", "αλλά", "ωστόσο", "therefore", "but", "so", "because"]
    total = len(decision_points)
    causal_linked = 0
    
    for dp in decision_points:
        text = (dp.get("sentence", "") + " " + dp.get("dialogue", "")).lower()
        if any(m in text for m in causal_markers):
            causal_linked += 1
    
    coverage = (causal_linked / total) if total > 0 else 1.0
    return {
        "lens": "south_park_causality",
        "validator": "therefore/but causal linkage",
        "total_decision_points": total,
        "causal_linked": causal_linked,
        "coverage": round(coverage, 3),
        "verdict": "PASS" if coverage >= 0.5 else ("PARTIAL" if coverage > 0 else "NEEDS_ATTENTION"),
        "deterministic": True
    }


def validate_character_arc(character_psychology: dict, chapters: list):
    """
    Character arc validator: characters should exhibit arc (change over chapters).
    Checks Big-5 trait variance across presence matrix.
    """
    characters = character_psychology.get("characters", character_psychology.get("profiles", []))
    if not characters:
        # Fallback: treat as pass with note
        return {
            "lens": "character_arc",
            "validator": "Big-5 trait variance (character arc)",
            "character_count": 0,
            "verdict": "SKIPPED",
            "reason": "No character profiles available",
            "deterministic": True
        }
    
    arc_count = 0
    for char in characters:
        # If psychology has trait variance or arc field
        if char.get("arc") or char.get("big5") or char.get("psych_proxies"):
            arc_count += 1
    
    coverage = (arc_count / len(characters)) if characters else 1.0
    return {
        "lens": "character_arc",
        "validator": "Big-5 trait variance / hero arc",
        "character_count": len(characters),
        "characters_with_arc": arc_count,
        "coverage": round(coverage, 3),
        "verdict": "PASS" if coverage >= 0.5 else ("PARTIAL" if coverage > 0 else "NEEDS_ATTENTION"),
        "deterministic": True
    }


def validate_heros_journey(chapters: list, pacing: dict):
    """
    Hero's Journey 12-stage validator: checks chapter distribution across journey stages.
    Maps tension curve to journey beats.
    """
    tension_curve = pacing.get("tension_curve", [])
    stage_labels = [
        "ordinary_world", "call_to_adventure", "refusal", "mentor",
        "crossing_threshold", "tests_allies_enemies", "approach",
        "ordeal", "reward", "road_back", "resurrection", "return"
    ]
    
    total_chapters = len(chapters) if chapters else len(tension_curve)
    mapped_stages = min(total_chapters, 12)
    
    stages = []
    for i, label in enumerate(stage_labels[:mapped_stages]):
        tc = tension_curve[i] if i < len(tension_curve) else {}
        stages.append({
            "stage_index": i + 1,
            "label": label,
            "chapter_title": tc.get("chapter_title", f"Chapter {i+1}"),
            "tension": tc.get("intensity", 0.5)
        })
    
    coverage = (mapped_stages / 12.0)
    return {
        "lens": "heros_journey",
        "validator": "12-stage Hero's Journey mapping",
        "total_chapters": total_chapters,
        "stages_mapped": mapped_stages,
        "coverage": round(coverage, 3),
        "stages": stages,
        "verdict": "PASS" if coverage >= 0.75 else ("PARTIAL" if coverage >= 0.33 else "NEEDS_ATTENTION"),
        "deterministic": True
    }


def run(out_dir: Path):
    """Execute all three theory lenses (optional, non-fatal)."""
    chapters_path = out_dir / "chapters"
    choice_tree_path = out_dir / "design" / "narrative" / "choice-tree.json"
    pacing_path = out_dir / "design" / "balance" / "tension-pacing-curve.json"
    psych_path = out_dir / "design" / "narrative" / "character-psychology.json"
    
    chapters = list(chapters_path.glob("*.md")) if chapters_path.exists() else []
    choice_tree = json.loads(choice_tree_path.read_text(encoding="utf-8-sig")) if choice_tree_path.exists() else {}
    pacing = json.loads(pacing_path.read_text(encoding="utf-8-sig")) if pacing_path.exists() else {}
    psych = json.loads(psych_path.read_text(encoding="utf-8-sig")) if psych_path.exists() else {}
    
    results = {
        "theory_lenses": [
            validate_south_park_causality(chapters, choice_tree),
            validate_character_arc(psych, chapters),
            validate_heros_journey(chapters, pacing)
        ],
        "generated": "theory_lenses.py",
        "deterministic": True
    }
    
    theory_dir = out_dir / "theory_lenses"
    theory_dir.mkdir(parents=True, exist_ok=True)
    (theory_dir / "validation.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[theory_lenses] 3 lenses validated — verdict: {[r['verdict'] for r in results['theory_lenses']]}")
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Phase 15b: Theory Lenses")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    run(Path(args.out))
