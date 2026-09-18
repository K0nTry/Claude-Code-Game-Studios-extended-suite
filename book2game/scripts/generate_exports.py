#!/usr/bin/env python3
"""
generate_exports.py — Phase 14b: Limited Export Layer.
Produces yarn/ and nodes/ exports from choice-tree + dialogue evidence.
Flag-restricted: --export-yarn and --export-nodes control which layer runs.
"""
import json
from pathlib import Path

def generate_yarn(out_dir: Path, choice_tree: dict):
    """Export branching narrative as Yarn Spinner dialogue files."""
    yarn_dir = out_dir / "exports" / "yarn"
    yarn_dir.mkdir(parents=True, exist_ok=True)
    
    decision_points = choice_tree.get("decision_points", [])
    for dp in decision_points:
        node_id = dp.get("id", "root")
        yarn_file = yarn_dir / f"{node_id}.yaml"
        dialogue = dp.get("sentence", dp.get("dialogue", ""))
        choices = dp.get("choices", [])
        
        yaml_content = f'### {node_id} dialog\n{dialogue}\n'
        for ch in choices[:4]:
            yaml_content += f'\n-> {ch.get("target", "unknown")}: {ch.get("text", "")}\n'
        
        yarn_file.write_text(yaml_content, encoding="utf-8")
    
    # Write manifest
    manifest = {
        "export_type": "yarn-spinner",
        "generated_from": "design/narrative/choice-tree.json",
        "node_count": len(decision_points),
        "files": sorted([f.name for f in yarn_dir.glob("*.yaml")])
    }
    (yarn_dir / "_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return yarn_dir


def generate_nodes(out_dir: Path, choice_tree: dict, pacing: dict):
    """Export narrative + pacing as node graph JSON."""
    nodes_dir = out_dir / "exports" / "nodes"
    nodes_dir.mkdir(parents=True, exist_ok=True)
    
    decision_points = choice_tree.get("decision_points", [])
    nodes = []
    edges = []
    
    for dp in decision_points:
        node_id = dp.get("id", "root")
        nodes.append({
            "id": node_id,
            "type": "decision",
            "label": dp.get("sentence", dp.get("dialogue", ""))[:120],
            "chapter": dp.get("chapter", ""),
            "evidence": dp.get("evidence", []),
            "tension": dp.get("tension_score", 0.5)
        })
        for ch in dp.get("choices", []):
            edges.append({
                "from": node_id,
                "to": ch.get("target", "unknown"),
                "label": ch.get("text", ""),
                "weight": ch.get("weight", 1.0)
            })
    
    # Add pacing-tension nodes
    tension_curve = pacing.get("tension_curve", [])
    for i, tc in enumerate(tension_curve[:20]):
        nodes.append({
            "id": f"tension-{i}",
            "type": "pacing",
            "label": tc.get("flow_label", "unknown"),
            "chapter": tc.get("chapter_title", ""),
            "tension": tc.get("intensity", 0.5),
            "detail": tc.get("detail", {})
        })
    
    graph = {
        "export_type": "node-graph",
        "generated_from": ["design/narrative/choice-tree.json", "design/balance/tension-pacing-curve.json"],
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges
    }
    (nodes_dir / "graph.json").write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
    return nodes_dir


def run(out_dir: Path, flags: dict = None):
    """Execute export generation. Flags: export-yarn, export-nodes."""
    flags = flags or {}
    choice_tree_path = out_dir / "design" / "narrative" / "choice-tree.json"
    pacing_path = out_dir / "design" / "balance" / "tension-pacing-curve.json"
    
    if not choice_tree_path.exists():
        print(f"[exports] choice-tree.json not found — skipping")
        return False
    
    choice_tree = json.loads(choice_tree_path.read_text(encoding="utf-8-sig"))
    pacing = json.loads(pacing_path.read_text(encoding="utf-8-sig")) if pacing_path.exists() else {}
    
    if flags.get("export_yarn") or flags.get("export-yarn") or not flags:
        yarn_dir = generate_yarn(out_dir, choice_tree)
        print(f"[exports] Yarn files written to {yarn_dir}")
    
    if flags.get("export_nodes") or flags.get("export-nodes") or not flags:
        nodes_dir = generate_nodes(out_dir, choice_tree, pacing)
        print(f"[exports] Node graph written to {nodes_dir}")
    
    return True


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Phase 14b: Generate exports")
    parser.add_argument("--out", required=True)
    parser.add_argument("--export-yarn", action="store_true")
    parser.add_argument("--export-nodes", action="store_true")
    args = parser.parse_args()
    run(Path(args.out), flags={"export_yarn": args.export_yarn, "export_nodes": args.export_nodes})
