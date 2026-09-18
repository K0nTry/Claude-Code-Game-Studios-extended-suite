#!/usr/bin/env python3
"""
simulate_knowledge_graph.py — Cycle 10: Πραγματικός γράφος γνώσης από το κείμενο.

Αντί για σταθερά schedules 08:00-22:00, βγάζει:
  - Ποιος εμφανίζεται σε ποιο κεφάλαιο (presence matrix)
  - Co-occurrence σχέσεις (ποιοι εμφανίζονται μαζί, πού)
  - Propagation: σειρά πρώτης εμφάνισης → διάδοση πληροφορίας ανά κεφάλαιο
Κάθε στοιχείο έχει evidence (γραμμές).
"""

import json
import re

def _presence(chunks, characters):
    """{όνομα: [κεφάλαια όπου εμφανίζεται]}"""
    presence = {c.get("name",""): [] for c in characters}
    for idx, (content, title) in enumerate(chunks, 1):
        t = title or f"Κεφάλαιο {idx}"
        for c in characters:
            name = c.get("name","")
            if name and name in content:
                presence[name].append({"chapter_index": idx, "chapter_title": t})
    return presence

def _first_appearance(chunks, name):
    for idx, (content, title) in enumerate(chunks, 1):
        if name in content:
            for ln, line in enumerate(content.splitlines(), 1):
                if name in line and len(line.strip()) > 15:
                    return {"chapter_index": idx, "chapter_title": title or f"Κεφάλαιο {idx}", "line": ln, "quote": line.strip()[:160]}
    return None

def simulate_knowledge_graph(characters, chunks, full_text: str = None) -> dict:
    """
    Συμβατό API:
      simulate_knowledge_graph(characters, chunks)
      simulate_knowledge_graph(characters, chunks, full_text) — full_text αγνοείται, χρησιμοποιούνται chunks
    """
    characters = characters or []
    chunks = chunks or []

    if not characters and not chunks:
        return {"nodes": [], "edges": [], "_note": "κανένα δεδομένο"}

    names = [c.get("name","") for c in characters if c.get("name")]
    presence = _presence(chunks, characters)

    # nodes: κάθε χαρακτήρας με presence
    nodes = []
    for c in characters:
        name = c.get("name","")
        pres = presence.get(name, [])
        first = _first_appearance(chunks, name) if name else None
        nodes.append({
            "name": name,
            "role": c.get("role",""),
            "appears_in_chapters": pres,
            "chapter_count": len(pres),
            "first_appearance": first,
        })

    # edges: co-occurrence — ποιοι εμφανίζονται μαζί σε ίδιο κεφάλαιο
    edges = []
    for i in range(len(names)):
        for j in range(i+1, len(names)):
            a, b = names[i], names[j]
            shared = []
            evidence = []
            for idx, (content, title) in enumerate(chunks, 1):
                if a in content and b in content:
                    shared.append({"chapter_index": idx, "chapter_title": title or f"Κεφάλαιο {idx}"})
                    for line in content.splitlines():
                        if a in line and b in line and len(line.strip()) > 20:
                            evidence.append({"chapter": title or f"Κεφάλαιο {idx}", "quote": line.strip()[:160]})
                            break
                    if len(evidence) >= 2:
                        pass
            if shared:
                edges.append({
                    "source": a, "target": b,
                    "shared_chapters": shared,
                    "shared_count": len(shared),
                    "evidence": evidence[:2]
                })

    # propagation: σειρά πρώτης εμφάνισης (ποιος μαθαίνει τι πότε)
    order = sorted(
        [(n, _first_appearance(chunks, n)) for n in names],
        key=lambda x: (x[1]["chapter_index"] if x[1] else 999, x[1]["line"] if x[1] else 999)
    )
    propagation = []
    for idx in range(1, len(order)):
        prev_name, prev_first = order[idx-1]
        cur_name, cur_first = order[idx]
        if prev_first and cur_first and cur_first["chapter_index"] > prev_first["chapter_index"]:
            propagation.append({
                "from": prev_name, "to": cur_name,
                "first_seen_chapter": cur_first["chapter_title"],
                "chapter_index": cur_first["chapter_index"],
                "trigger": f"εμφάνιση του {cur_name} στο {cur_first['chapter_title']}",
                "evidence": cur_first["quote"]
            })

    isolated = [n["name"] for n in nodes if n["chapter_count"] == 0]

    return {
        "nodes": nodes,
        "co_occurrence_edges": edges,
        "propagation_order": propagation,
        "isolated_characters": isolated,
        "total_chapters": len(chunks),
        "_method": "presence ανά κεφάλαιο + co-occurrence + first-appearance order — όχι σταθερά schedules",
        "_note": "Για Utility-AI schedules χρειάζεται game design· εδώ δίνουμε διάδοση πληροφορίας στο κείμενο"
    }

if __name__ == "__main__":
    chars = [{"name":"Αλέξανδρος"},{"name":"Ελένη"},{"name":"Δημήτρης"}]
    chunks = [("Ο Αλέξανδρος και η Ελένη στο λιμάνι.", "Κεφ 1"), ("Ο Δημήτρης περίμενε.", "Κεφ 2"), ("Και οι τρεις μαζί.", "Κεφ 3")]
    print(json.dumps(simulate_knowledge_graph(chars, chunks), ensure_ascii=False, indent=2))
