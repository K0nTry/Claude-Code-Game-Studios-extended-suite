# Active — sample_real_book

> Ζωντανό track. Ενημερώνεται σε κάθε session. Μην ξαναγράφεις ιστορία — κάνε append.

## Gates

- [x] G1: PDF/EPUB/DOCX → full_text.md — CHECK: python parse_book.py — EXPECT: FULL_TEXT_OK — EVIDENCE: 577 chars, 104 words
- [x] G2: Chunking + index — CHECK: count chapters/ — EXPECT: INDEX_OK — EVIDENCE: 3 chunks, index.json OK
- [x] G3: Scaffold entities.json — CHECK: entities.json exists — EXPECT: ENTITIES_OK scaffold — EVIDENCE: pending Claude ανάλυση
- [ ] G4: Genre ranking 13 κατηγοριών — CHECK: grep Genre game-concept.md — EXPECT: GENRE_RANKED — EVIDENCE: pending
- [ ] G5: Studio scaffold gate-check — CHECK: validate_output.py — EXPECT: GATE_PASS — EVIDENCE: pending
- [ ] G6: Resume — CHECK: active.md exists — EXPECT: RESUME_OK — EVIDENCE: 2026-09-14T21:56:49.139582

## Session Log

- 2026-09-14 21:56 — parse_book.py OK — sample_real_book.txt → 3 chunks
- Επόμενο: Claude ανάλυση (Βήμα 2) → entities.json + game-concept.md final

## Handoff

_Κανένα._
