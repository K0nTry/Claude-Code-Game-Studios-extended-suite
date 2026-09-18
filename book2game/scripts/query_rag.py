#!/usr/bin/env python3
"""
query_rag.py — Τοπικό RAG CLI tool για αναζήτηση όρων στα chapters/ και full_text.md
Χρήση: python query_rag.py <game_dir> "όρος αναζήτησης" [--json]
Αρχιτεκτονική: Mandatory zero-dependency lexical retrieval (BM25 / TF-IDF scoring).
Χωρίς Vector DB, χωρίς semantic embeddings (Lexical relevance retrieval).
"""

import sys
import json
import math
import re
from pathlib import Path

def tokenize(text: str) -> list:
    """Απλός tokenizer για BM25/TF-IDF: πεζά, αφαίρεση σημείων στίξης, διαχωρισμός λέξεων."""
    # Υποστήριξη ελληνικών και λατινικών χαρακτήρων
    words = re.findall(r'\b[α-ωάέήίόύώa-z0-9]+\b', text.lower())
    return words

def compute_bm25_scores(corpus: list, query: str, k1: float = 1.5, b: float = 0.75) -> list:
    """
    Υπολογίζει σκορ BM25 για λίστα κειμένων (corpus) ως προς ένα query.
    Το corpus είναι λίστα από dicts ή strings. Εδώ υποθέτουμε λίστα από strings ή dicts με 'content'.
    Επιστρέφει λίστα με τα σκορ ανά έγγραφο, ταξινομημένη κατά φθίνουσα σειρά.
    """
    query_tokens = tokenize(query)
    if not query_tokens or not corpus:
        return []

    # Προετοιμασία εγγράφων
    doc_tokens_list = []
    doc_lengths = []
    total_len = 0

    for doc in corpus:
        text = doc.get("content", "") if isinstance(doc, dict) else str(doc)
        tokens = tokenize(text)
        doc_tokens_list.append(tokens)
        doc_lengths.append(len(tokens))
        total_len += len(tokens)

    N = len(corpus)
    if N == 0:
        return []

    avgdl = total_len / N if N > 0 else 0

    # Υπολογισμός Inverse Document Frequency (IDF) για κάθε όρο του query
    idf = {}
    for qt in set(query_tokens):
        # Αριθμός εγγράφων που περιέχουν τον όρο qt
        n_q = sum(1 for tokens in doc_tokens_list if qt in tokens)
        # BM25 IDF formula με smoothing
        idf[qt] = math.log(1 + (N - n_q + 0.5) / (n_q + 0.5))

    scores = []
    for idx, tokens in enumerate(doc_tokens_list):
        score = 0.0
        doc_len = len(tokens)
        # Συχνότητα όρων στο έγγραφο (TF)
        tf_map = {}
        for t in tokens:
            tf_map[t] = tf_map.get(t, 0) + 1

        for qt in query_tokens:
            if qt not in tf_map:
                continue
            tf = tf_map[qt]
            i = idf.get(qt, 0.0)
            
            # BM25 numerator and denominator
            numerator = tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * (doc_len / avgdl if avgdl > 0 else 1))
            if denominator > 0:
                score += i * (numerator / denominator)

        scores.append((idx, score))

    # Ταξινόμηση κατά φθίνουσα βαθμολογία (score)
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores

def bm25_score_texts(texts: list, query: str) -> list:
    """Wrapper function για testing BM25 scoring σε λίστα κειμένων."""
    scores = compute_bm25_scores(texts, query)
    return [score for _, score in scores]

def search_rag(out_dir: Path, query: str):
    query_lower = query.lower()
    corpus = []
    meta = []

    # 1. Συλλογή από chapters/
    ch_dir = out_dir / "chapters"
    if ch_dir.exists():
        for ch_file in sorted(ch_dir.glob("*.md")):
            lines = ch_file.read_text(encoding="utf-8", errors="ignore").splitlines()
            for idx, line in enumerate(lines, 1):
                clean_line = line.strip()
                if clean_line:
                    corpus.append(clean_line)
                    meta.append({
                        "file": str(ch_file.relative_to(out_dir)),
                        "line": idx,
                        "content": clean_line
                    })

    # 2. Αν δεν υπάρχουν chapters, συλλογή από full_text.md
    full_text = out_dir / "full_text.md"
    if not corpus and full_text.exists():
        lines = full_text.read_text(encoding="utf-8", errors="ignore").splitlines()
        for idx, line in enumerate(lines, 1):
            clean_line = line.strip()
            if clean_line:
                corpus.append(clean_line)
                meta.append({
                    "file": "full_text.md",
                    "line": idx,
                    "content": clean_line
                })

    if not corpus:
        return []

    # 3. Εκτέλεση BM25 lexical relevance ranking
    ranked_indices = compute_bm25_scores(corpus, query)

    results = []
    for idx, score in ranked_indices:
        if score > 0.0:  # Κρατάμε μόνο όσα έχουν σχετικότητα > 0
            item = meta[idx].copy()
            item["bm25_score"] = round(score, 4)
            results.append(item)

    # Αν το BM25 δεν βρει τίποτα (π.χ. πολύ σπάνιος όρος), κάνουμε fallback σε απλό substring match
    if not results:
        for m in meta:
            if query_lower in m["content"].lower():
                item = m.copy()
                item["bm25_score"] = 0.1  # minimal fallback score
                results.append(item)

    return results

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Χρήση: python query_rag.py <game_dir> <query> [--json]")
        sys.exit(1)
    
    out_dir = Path(sys.argv[1])
    query = sys.argv[2]
    res = search_rag(out_dir, query)
    print(json.dumps(res, ensure_ascii=False, indent=2))
