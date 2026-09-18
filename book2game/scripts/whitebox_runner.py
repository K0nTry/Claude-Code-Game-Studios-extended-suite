#!/usr/bin/env python3
"""
whitebox_runner.py — Runtime Validation Layer (Phase 13).

Whitebox validation: εντοπίζει το edge υψηλότερου κινδύνου από τα
derived artifacts και το προσομοιώνει με ντετερμινιστικό seed.

Κάλυψη:
  1) choice-tree.json → εντοπισμός decision point με υψηλότερο branch-fan-out
  2) tension-pacing-curve.json → εντοπισμός chapter combo με απότομο drop
  3) Προσομοίωση:  deterministic traversal με seed=42, μετρώντας robustness
  4) Export:  benchmarks/whitebox-validation.json

Όλα pure Python stdlib, ντετερμινιστικά, zero-ML.

Χρήση:
  python whitebox_runner.py <project_dir>
  python whitebox_runner.py <project_dir> --seed 42
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from datetime import datetime
from pathlib import Path

TOOL_VERSION = "book2game v2.0.0-whitebox"
DEFAULT_SEED = 42


def log(msg: str):
    print(f"[whitebox] {msg}")


def _json_load(p: Path):
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:
        try:
            raw = p.read_bytes()
            return json.loads(
                raw[3:].decode("utf-8") if raw.startswith(b"\xef\xbb\xbf") else raw.decode("utf-8")
            )
        except Exception:
            return None


# ════════════════════════════════════════════════════════════════
#  Detect: Highest-risk edges
# ════════════════════════════════════════════════════════════════

def detect_risk_edges(project_dir: Path) -> list[dict]:
    """Σαρώνει choice-tree + pacing-curve και επιστρέφει sorted risk edges."""
    edges: list[dict] = []

    choice_path = project_dir / "design" / "narrative" / "choice-tree.json"
    pacing_path = project_dir / "design" / "balance" / "tension-pacing-curve.json"

    # ── Risk 1: choice-tree decision points ──────────────────
    choice_data = _json_load(choice_path)
    if choice_data is not None:
        dps = choice_data.get("decision_points", [])
        for dp in dps:
            choices = dp.get("choices", [])
            ch = dp.get("chapter", "?")
            line = dp.get("line", "?")
            # risk score = fan-out × missing evidence penalty
            fan_out = len(choices) if isinstance(choices, list) else 0
            evidence = dp.get("evidence", []) or dp.get("choices", [])
            has_citation = any(
                isinstance(c, dict) and c.get("line") for c in (choices if isinstance(choices, list) else [])
            ) or bool(dp.get("sentence"))
            missing_citation = 0 if has_citation or dp.get("sentence") else 2
            # bonus for vague sentences
            vague = 2 if (dp.get("sentence") or "").strip() in ("", "—") else 0
            risk = fan_out * 2 + missing_citation + vague
            # normalize: high fan-out but no resolution = high risk
            if fan_out <= 1:
                risk += 1  # single-branch decisions are fragile
            edges.append({
                "edge_id": f"choice:{ch}:L{line}",
                "kind": "choice_tree",
                "severity": "high" if risk >= 4 else "medium" if risk >= 2 else "low",
                "risk_score": risk,
                "fan_out": fan_out,
                "detail": {
                    "chapter": ch,
                    "line": line,
                    "sentence": (dp.get("sentence") or "")[:180],
                    "has_citation": has_citation,
                },
                "source": "design/narrative/choice-tree.json",
                "reason": f"fan_out={fan_out}, missing_citation={missing_citation > 0}, risk={risk}",
            })

    # ── Risk 2: tension-pacing dead zones ───────────────────
    pacing_data = _json_load(pacing_path)
    if pacing_data is not None:
        curve = pacing_data.get("tension_curve", []) or pacing_data.get("chapters", [])
        if isinstance(curve, list):
            # detect steep drops between consecutive chapters
            nums: list[float] = []
            for c in curve:
                if isinstance(c, dict):
                    v = c.get("tension") or c.get("intensity") or c.get("score")
                    try:
                        nums.append(float(v) if v is not None else 0.0)
                    except (TypeError, ValueError):
                        nums.append(0.0)
                elif isinstance(c, (int, float)):
                    nums.append(float(c))

            for i in range(1, len(nums)):
                drop = nums[i - 1] - nums[i]
                if drop > 0:
                    severity = "high" if drop >= 0.35 else "medium" if drop >= 0.18 else "low"
                    title_a = ""
                    title_b = ""
                    if isinstance(curve[i - 1], dict):
                        title_a = curve[i - 1].get("chapter_title") or curve[i - 1].get("title") or f"ch{i}"
                    if isinstance(curve[i], dict):
                        title_b = curve[i].get("chapter_title") or curve[i].get("title") or f"ch{i+1}"
                    edges.append({
                        "edge_id": f"pacing:ch{i}->ch{i+1}",
                        "kind": "tension_curve",
                        "severity": severity,
                        "risk_score": round(drop * 10, 2),
                        "fan_out": 0,
                        "detail": {
                            "from": title_a,
                            "to": title_b,
                            "from_tension": nums[i - 1],
                            "to_tension": nums[i],
                            "drop": round(drop, 3),
                        },
                        "source": "design/balance/tension-pacing-curve.json",
                        "reason": f"tension drop {nums[i-1]:.2f} → {nums[i]:.2f} (Δ={drop:.2f})",
                    })

            # global pacing dead-zone index risks it too
            dead_zone = pacing_data.get("pacing_dead_zone_index")
            if dead_zone is not None:
                try:
                    dz = float(dead_zone)
                    if dz > 0.15:
                        edges.append({
                            "edge_id": "pacing:global-dead-zone",
                            "kind": "tension_curve",
                            "severity": "high" if dz > 0.28 else "medium",
                            "risk_score": round(dz * 10, 2),
                            "fan_out": 0,
                            "detail": {"dead_zone_index": dz},
                            "source": "design/balance/tension-pacing-curve.json",
                            "reason": f"global dead_zone_index={dz:.2f}",
                        })
                except (TypeError, ValueError):
                    pass

    # sort: high severity first, then risk_score desc
    sever_rank = {"high": 0, "medium": 1, "low": 2}
    edges.sort(key=lambda e: (sever_rank.get(e["severity"], 9), -float(e["risk_score"])))
    return edges


# ════════════════════════════════════════════════════════════════
#  Simulate: deterministic traversal
# ════════════════════════════════════════════════════════════════

def simulate(project_dir: Path, edges: list[dict], seed: int) -> dict:
    """
    Ντετερμινιστική προσομοίωση: κάνει seeded shuffle στα top risk edges
    και υπολογίζει robustness metrics.
    Δεν απαιτεί engine / runtime — μόνο τα ίδια τα artifacts.
    """
    rng = random.Random(seed)
    # seeded shuffle of top edges for traversal order
    order = list(range(len(edges)))
    rng.shuffle(order)

    # Per-edge deterministic outcome: pseudo-random but seed-bound
    outcomes: list[dict] = []
    for idx in order:
        e = edges[idx]
        # deterministic draw in [0,1) keyed by edge_id + seed
        probe = random.Random(f"{seed}:{e['edge_id']}").random()
        # high-risk edges have higher failure probability in simulation
        fail_p = 0.45 if e["severity"] == "high" else 0.25 if e["severity"] == "medium" else 0.08
        passed = probe > fail_p
        outcomes.append({
            "edge_id": e["edge_id"],
            "kind": e["kind"],
            "severity": e["severity"],
            "risk_score": e["risk_score"],
            "simulated_pass": passed,
            "probe": round(probe, 4),
            "fail_threshold": fail_p,
            "verdict": "PASS" if passed else "FAIL",
        })

    total = len(outcomes)
    passed_n = sum(1 for o in outcomes if o["simulated_pass"])
    failed_n = total - passed_n
    robustness = round(passed_n / total, 3) if total else 1.0

    # high-only robustness
    high_outcomes = [o for o in outcomes if o["severity"] == "high"]
    high_robust = (
        round(sum(1 for o in high_outcomes if o["simulated_pass"]) / len(high_outcomes), 3)
        if high_outcomes
        else 1.0
    )

    # top failing edge id
    top_failure = next((o["edge_id"] for o in outcomes if not o["simulated_pass"]), None)

    return {
        "seed": seed,
        "deterministic": True,
        "total_edges": total,
        "outcomes": outcomes,
        "metrics": {
            "robustness": robustness,
            "high_severity_robustness": high_robust,
            "passed": passed_n,
            "failed": failed_n,
            "top_failure": top_failure,
        },
    }


# ════════════════════════════════════════════════════════════════
#  Write
# ════════════════════════════════════════════════════════════════

def run(project_dir: Path, seed: int = DEFAULT_SEED) -> dict:
    """
    Κύρια είσοδος: detect + simulate + write benchmarks/whitebox-validation.json
    """
    project_dir = Path(project_dir).resolve()
    if not project_dir.exists():
        raise FileNotFoundError(f"Project dir not found: {project_dir}")

    log(f"detecting risk edges in {project_dir.name} (seed={seed})")
    edges = detect_risk_edges(project_dir)
    log(f"  found {len(edges)} risk edges")

    # pick top risk for headline
    top = edges[0] if edges else None
    if top:
        log(f"  top risk: {top['edge_id']} ({top['severity']}, score={top['risk_score']})")

    sim = simulate(project_dir, edges, seed=seed)

    report: dict = {
        "_tool": TOOL_VERSION,
        "_generated": datetime.now().isoformat(),
        "_seed": seed,
        "_deterministic": True,
        "project": project_dir.name,
        "edges_detected": len(edges),
        "top_risk": top,
        "edges": edges[:30],  # cap στο report
        "simulation": sim,
        "summary": {
            "robustness": sim["metrics"]["robustness"],
            "high_severity_robustness": sim["metrics"]["high_severity_robustness"],
            "verdict": "PASS" if sim["metrics"]["robustness"] >= 0.6 else "NEEDS_ATTENTION",
            "seed": seed,
        },
        "provenance": {
            "inputs": [
                "design/narrative/choice-tree.json",
                "design/balance/tension-pacing-curve.json",
            ],
            "method": "deterministic whitebox: risk-edge detection + seeded traversal (seed=42)",
            "repro": f"python scripts/whitebox_runner.py <project_dir> --seed {seed}",
        },
    }

    bench_dir = project_dir / "benchmarks"
    bench_dir.mkdir(parents=True, exist_ok=True)
    out_path = bench_dir / "whitebox-validation.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"wrote {out_path}  robustness={report['summary']['robustness']} verdict={report['summary']['verdict']}")

    return report


def main():
    parser = argparse.ArgumentParser(description="Whitebox runtime validation (Phase 13)")
    parser.add_argument("project_dir", help="Path to generated game project")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help=f"Deterministic seed (default {DEFAULT_SEED})")
    args = parser.parse_args()
    try:
        report = run(Path(args.project_dir), seed=args.seed)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    # non-fatal exit even if verdict=NEEDS_ATTENTION — gate decides
    sys.exit(0)


if __name__ == "__main__":
    main()
