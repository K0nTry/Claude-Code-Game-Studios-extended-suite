#!/usr/bin/env python3
"""
simulate_state.py — Phase 16a: Minimal State Simulation.
Choice-tree → binary card-mode simulator.
Pure Python stdlib. Deterministic seed=42.
"""
import json
import hashlib
from pathlib import Path


def simulate_choice_tree(card_mode: bool = True, seed: int = 42):
    """
    Minimal binary card-mode simulation of narrative choice tree.
    Each node = binary card (chosen/not-chosen). State tracked as bitmask.
    """
    import random
    rng = random.Random(seed)
    
    # Load choice tree if available
    state = {
        "simulation_type": "binary_card_mode",
        "seed": seed,
        "deterministic": True,
        "nodes_visited": [],
        "card_stack": [],
        "branching_factor": 2,
        "max_depth": 5,
        "state_hash": ""
    }
    
    # Simulate binary traversal: each level = 2 cards
    for depth in range(state["max_depth"]):
        for card_idx in range(state["branching_factor"]):
            chosen = rng.choice([True, False])
            state["nodes_visited"].append({
                "depth": depth,
                "card": card_idx,
                "chosen": chosen,
                "node_id": f"depth{depth}_card{card_idx}"
            })
            if chosen:
                state["card_stack"].append(f"depth{depth}_card{card_idx}")
    
    # Deterministic hash of final state
    state_json = json.dumps(state, sort_keys=True, default=str)
    state["state_hash"] = "sha256:" + hashlib.sha256(state_json.encode()).hexdigest()[:16]
    
    return state


def run(out_dir: Path, seed: int = 42):
    """Execute minimal state simulation."""
    result = simulate_choice_tree(seed=seed)
    
    sim_dir = out_dir / "simulation"
    sim_dir.mkdir(parents=True, exist_ok=True)
    
    (sim_dir / "state-simulation.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[simulation] Binary card-mode simulation complete — {len(result['nodes_visited'])} nodes visited")
    print(f"[simulation] State hash: {result['state_hash']}")
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Phase 16a: Minimal State Simulation")
    parser.add_argument("--out", required=True)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    run(Path(args.out), seed=args.seed)
