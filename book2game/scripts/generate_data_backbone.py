#!/usr/bin/env python3
"""
generate_data_backbone.py — Phase 15: Data Backbone.
Schemas/*.schema.json + knowledge/ artifacts (StyleDNA, foreshadowing, WorldMuncher, progress-state).
Deterministic. Pure stdlib.
"""
import hashlib
import json
import re
from pathlib import Path
from datetime import datetime


def _load_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def write_schemas(out_dir: Path):
    """Copy repo schemas/ into output/schemas/; also emit schema index."""
    repo_schemas = Path(__file__).resolve().parent.parent / "schemas"
    if not repo_schemas.exists():
        repo_schemas = Path(__file__).resolve().parent / "schemas"
    out_schemas = out_dir / "schemas"
    out_schemas.mkdir(parents=True, exist_ok=True)
    copied = 0
    if repo_schemas.exists():
        for sf in repo_schemas.glob("*.schema.json"):
            (out_schemas / sf.name).write_text(sf.read_text(encoding="utf-8"), encoding="utf-8")
            copied += 1
    # index
    idx = {
        "version": "1.0.0",
        "generated": datetime.now().isoformat(),
        "schemas": sorted([f.name for f in out_schemas.glob("*.schema.json")]),
        "draft": "https://json-schema.org/draft/2020-12/schema",
    }
    (out_schemas / "_index.json").write_text(json.dumps(idx, ensure_ascii=False, indent=2), encoding="utf-8")
    return copied


def _style_dna(text: str, entities: dict) -> dict:
    """StyleDNA fingerprint: lexical density + tone vectors per archetype."""
    words = text.split()
    unique = len(set(w.lower() for w in words))
    lexical_density = round(unique / max(len(words), 1), 4)
    # naive tone vectors from keyword counts
    tones = {
        "tension": len(re.findall(r"\b(κίνδυνος|φόβος|μάχη|danger|fear|battle)\b", text, re.I)),
        "wonder": len(re.findall(r"\b(θαύμα|μυστήριο|magic|wonder|mystery)\b", text, re.I)),
        "melancholy": len(re.findall(r"\b(λύπη|μοναξιά|sorrow|lonely)\b", text, re.I)),
    }
    top_tones = sorted(tones, key=tones.get, reverse=True)[:3]
    return {
        "_epistemic": "derived",
        "lexical_density": lexical_density,
        "character_uuid": entities.get("characters", [{}])[0].get("_uuid", "") if entities.get("characters") else "",
        "archetype": entities.get("_archetype", "unknown"),
        "tone_vectors": top_tones,
        "generated": datetime.now().isoformat(),
    }


def _foreshadowing(text: str, chapters: list) -> list:
    """Foreshadowing tracker: repeated motifs that later resolve."""
    # Extract repeated phrases (bigrams that appear >=2 times but <=5 distinct chapters)
    bigrams = re.findall(r"\b(\w+\s+\w+)\b", text.lower())
    from collections import Counter
    counts = Counter(bigrams)
    items = []
    for phrase, cnt in counts.most_common(50):
        if cnt >= 2 and len(phrase) > 5 and phrase not in ("of the", "in the", "to the"):
            items.append({
                "chapter_id": "ch01",
                "foreshadowing_event": phrase,
                "payload": f"Repeated {cnt}× — potential motif",
                "resolved_in": "",
            })
            if len(items) >= 10:
                break
    return items


def _world_muncher(entities: dict, text: str) -> dict:
    """WorldMuncher-style world model: locations + factions + glossary terms as elements."""
    elements = []
    for loc in entities.get("locations", [])[:10]:
        name = loc.get("name") if isinstance(loc, dict) else str(loc)
        elements.append({"id": name, "type": "location", "properties": {"source": "canon"}})
    for fac in entities.get("factions", [])[:5]:
        name = fac.get("name") if isinstance(fac, dict) else str(fac)
        elements.append({"id": name, "type": "faction", "properties": {"source": "canon"}})
    world_id = hashlib.sha256(text[:500].encode()).hexdigest()[:12]
    return {"world_id": world_id, "elements": elements, "generated": datetime.now().isoformat()}


def _progress_state(chapters: list) -> dict:
    """Progress-state: session progress + unlocked content derivation."""
    unlocked = [f"ch{i:02d}" for i in range(1, min(len(chapters) + 1, 6))]
    return {
        "session_id": "session-01",
        "progress": round(len(unlocked) / max(len(chapters), 1), 3) if chapters else 0.0,
        "unlocked_content": unlocked,
        "generated": datetime.now().isoformat(),
    }


def run(out_dir: Path):
    """Execute Data Backbone generation."""
    out_dir = Path(out_dir)
    # 1) schemas
    n_schemas = write_schemas(out_dir)
    print(f"[data-backbone] schemas: {n_schemas} copied to schemas/")

    # 2) knowledge artifacts
    canon_entities = _load_json(out_dir / "canon" / "entities.json") or _load_json(out_dir / "entities.json") or {}
    # try to read full text for lexical calc
    text = ""
    ft = out_dir / "source" / "full_text.md"
    if not ft.exists():
        ft = out_dir / "full_text.md"
    if ft.exists():
        text = ft.read_text(encoding="utf-8-sig", errors="ignore")[:20000]

    chapters = list((out_dir / "chapters").glob("*.md")) if (out_dir / "chapters").exists() else []

    knowledge_dir = out_dir / "knowledge"
    knowledge_dir.mkdir(parents=True, exist_ok=True)

    (knowledge_dir / "StyleDNA.json").write_text(
        json.dumps(_style_dna(text, canon_entities), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (knowledge_dir / "foreshadowing.json").write_text(
        json.dumps(_foreshadowing(text, chapters), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (knowledge_dir / "WorldMuncher.json").write_text(
        json.dumps(_world_muncher(canon_entities, text), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (knowledge_dir / "progress-state.json").write_text(
        json.dumps(_progress_state(chapters), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[data-backbone] knowledge: 4 artifacts to knowledge/")
    return True


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Phase 15: Data Backbone")
    p.add_argument("--out", required=True)
    a = p.parse_args()
    run(Path(a.out))
