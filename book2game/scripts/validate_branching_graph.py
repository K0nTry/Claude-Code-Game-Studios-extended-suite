#!/usr/bin/env python3
"""
validate_branching_graph.py — Cycle 7: Πραγματικά σημεία επιλογής + γράφημα με citations.

Δεν φτιάχνει τεχνητά "branch A/B" και 3 σταθερά τέλη (sacrifice/dominion/secrets).
Αντιθέτως:
  1. Σαρώνει το κείμενο για ΣΗΜΕΙΑ ΑΠΟΦΑΣΗΣ (decision points) με λεξιλόγιο:
     αποφάσισε, διάλεξε, επέλεξε, δίλημμα, ή/αν/αλλιώς σε συγκείμενο επιλογής,
     δύο δρόμοι/επιλογές, πρέπει να επιλέξει, ερωτηματικές προτάσεις διλήμματος.
  2. Κάθε σημείο φέρει απόσπασμα (evidence) + κεφάλαιο + γραμμή.
  3. Κατασκευάζει ένα DAG: Intro -> κεφάλαια -> decision forks -> επόμενα κεφάλαια
     (γραμμική ραχοκοκαλιά, με πραγματικές διακλαδώσεις όπου βρέθηκαν).
  4. BFS validation: ορφανά σημεία, προσβασιμότητα.
"""

import json
import re
from collections import deque, defaultdict

_DECISION_PATTERNS = [
    r'αποφάσισ\w*', r'διάλεξ\w*', r'επέλεξ\w*', r'διαλέγ\w*', r'επιλέγ\w*',
    r'δίλημμα', r'επιλογή', r'επιλογές', r'δύο\s+δρόμοι', r'δύο\s+επιλογές',
    r'πρέπει\s+να\s+(?:επιλέξ|διαλέξ|αποφασίσ|διαλέγει)',
    r'μπορούσε\s+να\s+(?:πάει|επιλέξ|διαλέξ)',
    r'θα\s+(?:μπορούσε|έπρεπε)\s+να',
    r'ή\s+να\s+\w+', r'αν\s+.*,\s*ή\s+', r'αλλιώς',
]
_DECISION_RE = re.compile("|".join(_DECISION_PATTERNS), re.IGNORECASE)
_QUESTION_RE = re.compile(r'.+\?\s*$')
_SENT_SPLIT = re.compile(r'(?<=[.!?…])\s+')

def _find_decision_points(full_text: str, chunks):
    """Βρίσκει σημεία απόφασης με evidence."""
    points = []
    # χάρτης γραμμής -> κεφάλαιο
    line_to_chapter = {}
    if chunks:
        line_no = 1
        for idx, (content, title) in enumerate(chunks, 1):
            t = title or f"Κεφάλαιο {idx}"
            for _ in content.splitlines():
                line_to_chapter[line_no] = t
                line_no += 1
            line_no += 1  # κενό

    for ln, line in enumerate(full_text.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        # σπάσε σε προτάσεις
        for sent in _SENT_SPLIT.split(stripped):
            s = sent.strip()
            if len(s) < 15:
                continue
            is_decision = bool(_DECISION_RE.search(s))
            # ερωτηματική πρόταση με «ή» θεωρείται δίλημμα
            if not is_decision and "?" in s and (" ή " in s or " η " in s):
                is_decision = True
            # φράσεις όπως "Μπροστά του απλώνονταν δύο δρόμοι"
            if not is_decision and re.search(r'δύο\s+δρόμοι|δύο\s+επιλογές|μπροστά.*δύο', s, re.IGNORECASE):
                is_decision = True
            if is_decision:
                ch = line_to_chapter.get(ln, "")
                points.append({
                    "sentence": s[:220],
                    "line": ln,
                    "chapter": ch,
                    "type": "decision_point",
                    "evidence": s[:220]
                })
    # αφαίρεση διπλών (ίδια πρόταση)
    seen = set()
    uniq = []
    for p in points:
        key = p["sentence"][:80]
        if key not in seen:
            seen.add(key)
            uniq.append(p)
    return uniq


def build_and_validate_branching_graph(chunks: list, full_text: str = None, relationships: list = None) -> dict:
    """
    Κύρια συνάρτηση. Συμβατή με παλιό API (chunks) αλλά δέχεται και full_text.
    Αν δοθεί full_text, κάνει πραγματική ανίχνευση· αλλιώς πέφτει σε ουδέτερο skeleton.
    """
    # αν το chunks είναι λίστα tuples, βγάλε titles
    titles = []
    if chunks:
        for item in chunks:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                _, t = item
                titles.append(t or "")
            elif isinstance(item, dict):
                titles.append(item.get("title",""))
            else:
                titles.append(str(item)[:30])

    # full_text fallback: αν δεν δόθηκε, κόλλα τα chunks
    if full_text is None and chunks:
        parts = []
        for item in chunks:
            if isinstance(item, (list, tuple)):
                parts.append(item[0])
            elif isinstance(item, dict):
                parts.append(item.get("content",""))
        full_text = "\n\n".join(parts)

    decision_points = _find_decision_points(full_text or "", chunks) if full_text else []

    # --- κατασκευή DAG ---
    nodes = []
    edges = []

    nodes.append({"id": "node_00_intro", "type": "Intro", "label": "Αρχή — setup"})

    for i, title in enumerate(titles, 1):
        nid = f"node_{i:02d}_{re.sub(r'[^\\w\\u0370-\\u03FF]', '_', (title or f'chapter_{i}')[:14]).strip('_').lower() or f'ch_{i}'}"
        nodes.append({"id": nid, "type": "Chapter", "title": title or f"Κεφάλαιο {i}", "index": i})

    # decision forks — μόνο όσα βρέθηκαν
    for idx, dp in enumerate(decision_points, 1):
        did = f"decision_{idx:02d}"
        nodes.append({
            "id": did, "type": "DecisionFork",
            "sentence": dp["sentence"],
            "chapter": dp["chapter"],
            "line": dp["line"],
            "evidence": dp["evidence"]
        })

    # edges: γραμμική ραχοκοκαλιά κεφαλαίων
    ch_nodes = [n for n in nodes if n["type"] == "Chapter"]
    if ch_nodes:
        edges.append(("node_00_intro", ch_nodes[0]["id"]))
        for i in range(len(ch_nodes)-1):
            edges.append((ch_nodes[i]["id"], ch_nodes[i+1]["id"]))

    # σύνδεσε κάθε decision στο κεφάλαιο όπου βρέθηκε
    title_to_id = {n.get("title","").lower(): n["id"] for n in ch_nodes}
    for dp_node in [n for n in nodes if n["type"] == "DecisionFork"]:
        ch_title = (dp_node.get("chapter") or "").lower()
        target = None
        # ακριβές match
        if ch_title in title_to_id:
            target = title_to_id[ch_title]
        else:
            # fuzzy: αν ο τίτλος περιέχεται
            for t, nid in title_to_id.items():
                if t and (t in ch_title or ch_title in t):
                    target = nid
                    break
        if target:
            edges.append((target, dp_node["id"]))
            # από το decision → επόμενο κεφάλαιο (αν υπάρχει)
            idx = next((i for i, n in enumerate(ch_nodes) if n["id"] == target), None)
            if idx is not None and idx + 1 < len(ch_nodes):
                edges.append((dp_node["id"], ch_nodes[idx+1]["id"]))

    # --- BFS validation ---
    node_ids = {n["id"] for n in nodes}
    adj = defaultdict(list)
    for u, v in edges:
        if u in node_ids and v in node_ids:
            adj[u].append(v)

    visited = set()
    q = deque(["node_00_intro"])
    visited.add("node_00_intro")
    while q:
        u = q.popleft()
        for v in adj[u]:
            if v not in visited:
                visited.add(v)
                q.append(v)

    orphans = [nid for nid in node_ids if nid not in visited]
    # decisions χωρίς σύνδεση θεωρούνται απομονωμένες αλλά όχι fatal — απλώς αναφορά
    isolated_decisions = [n["id"] for n in nodes if n["type"]=="DecisionFork" and n["id"] not in visited]

    return {
        "branching_graph": {
            "nodes": nodes,
            "edges": [{"from": u, "to": v} for u, v in edges if u in node_ids and v in node_ids],
            "algorithm": "decision points extracted from text + linear chapter spine + BFS reachability"
        },
        "decision_points": decision_points,
        "validation": {
            "total_nodes": len(nodes),
            "chapter_nodes": len(ch_nodes),
            "decision_nodes": len(decision_points),
            "visited_nodes": len(visited),
            "orphan_nodes": orphans,
            "isolated_decisions": isolated_decisions,
            "orphan_rate": round(len(orphans)/len(node_ids)*100, 2) if node_ids else 0,
            "verdict": "PASS" if not orphans else f"ATTENTION: {len(orphans)} ορφανά σημεία — δες decision_points evidence"
        },
        "_method": "regex decision lexicon + sentence scan + chapter-mapped DAG — όχι σταθερά 3 τέλη",
        "_note": "Για πλήρες branching με πολλαπλά τέλη απαιτείται LLM enrichment πάνω στα evidence"
    }


if __name__ == "__main__":
    demo_chunks = [("Μπροστά του δύο δρόμοι. Αποφάσισε να πάει αριστερά.", "Κεφάλαιο 1"),
                   ("Η μάχη ήταν σκληρή.", "Κεφάλαιο 2"),
                   ("Τελικά επέλεξε την αλήθεια.", "Κεφάλαιο 3")]
    full = "\n\n".join(c for c,_ in demo_chunks)
    print(json.dumps(build_and_validate_branching_graph(demo_chunks, full), ensure_ascii=False, indent=2))
