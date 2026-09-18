---
name: book2game-prep
description: Use when the user wants to convert a book (PDF, EPUB, DOCX) into a Game Studio-ready folder, rag a pdf book, or prepare a book for game development with one command
allowed-tools: Read, Grep, Glob, Write, Bash
user-invocable: true
argument-hint: "<book-path> [--out ./]"
---

# book2game-prep

Μετατρέπει ένα βιβλίο σε έτοιμο Game Studio scaffold με μία εντολή — production-grade book-to-context preparation layer για 49 specialist agents.

## Τι κάνει

Παίρνει `βιβλίο.pdf` (ή `.epub`, `.docx`, `.txt`, `.md`) και παραδίδει φάκελο με πραγματικά αποδεικτικά στοιχεία από το κείμενο:

- **Πλήρες κείμενο & RAG:** Εξαγωγή χωρίς περικοπές (`full_text.md`), τεμαχισμός σε κεφάλαια (`chapters/`) και ευρετηρίαση (`index.json`) για αναζήτηση με `grep -n`.
- **Αυτόνομη εξαγωγή οντοτήτων & ψυχολογικών προφίλ (Cycle 5):** Ανίχνευση ονομάτων/τοποθεσιών/αντικειμένων με citations (+γραμμή). Voice fingerprints & Big-5 proxies από πραγματικούς διαλόγους.
- **Καμπύλη pacing & έντασης (Cycle 6):** Υπολογισμός έντασης ανά κεφάλαιο από λεξιλόγιο (ένταση, κίνδυνος, αποφασιστικότητα). Σημειώσεις economy από pacing, όχι hardcoded.
- **Branching Graph (Cycle 7):** Εντοπισμός σημείων απόφασης από έλλειψη διαλόγων/σχήματα «εάν…». Κάθε επιλογή φέρει citation και γραμμή.
- **Player Persona (Cycle 8):** Χαρτογράφηση κατανεμημένου ενδιαφέροντος (χαρακτήρες/θέματα/αποφάσεις) με evidence. Χωρίς προβλέψεις D30/Metacritic· αυτά απαιτούν playtest.
- **Αισθητηριακή σκηνοθεσία (Cycle 9):** Leitmotif matrix από λέξεις-θέματα του βιβλίου, lighting/color script από pacing, audio direction με textual context.
- **Γνώση & Co-occurrence (Cycle 10):** Presence matrix χαρακτήρων ανά κεφάλαιο, συν-εμφάνιση και σειρά πρώτης εμφάνισης — όχι σταθερά schedules.
- **Conflict/Balance (Cycle 11):** Χαρτογράφηση συγκρούσεων/πόρων/ανισορροπιών από λεξιλόγιο (μάχη, σπαθί…) — χωρίς αξιώσεις Nash/Gini που απαιτούν playable build.
- **Expansion Grammar & DDA (Cycle 12):** Γραμματική επέκτασης με terminals από πραγματικές οντότητες, όχι placeholders.
- **Επιλογή Game Engine & MCP:** (Godot/Unity/Unreal/Phaser/Custom) + mcp-plugins.yml + .mcp.json.
- **A/B Έλεγχος (Fable):** Κανένα παραποιημένο claim — audit με πραγματικά αρχείο-evidence, coverage report, όχι ψεύτικα AAA benchmarks.
- **MCP Bridge:** Αυτόματη πρόταση Godot / Unity / Unreal / Phaser / Custom με αιτιολόγηση και MCP servers (`technical/engine.md`).
- **Executable Executive Audit:** `benchmarks/executive_audit_report.json` με τεκμηριωμένο audit traceability/coverage (χωρίς ισχυρισμούς ανωτερότητας έναντι AAA).

## Χρήση

```bash
/book2game-prep "C:/path/to/book.pdf" --out "./my-game"
/book2game-prep "./book.epub"
/book2game-prep "./book.docx" --out "C:/Users/Kon_Try/Desktop/my-game"
```

Αν δεν δοθεί `--out`, δημιουργείται φάκελος δίπλα στο βιβλίο: `<όνομα_βιβλίου>_game/`.

---

## Ροή Εκτέλεσης (ο agent την εκτελεί, όχι ο χρήστης)

### Βήμα 1 — Εξαγωγή & Τεμαχισμός (parse_book.py)

```bash
python "${CLAUDE_SKILL_DIR}/scripts/parse_book.py" "$BOOK_PATH" --out "$OUT_DIR"
```

Γράφει:
- `full_text.md` (πλήρες κείμενο, χωρίς κοψίματα),
- `chapters/chNN-*.md` (chunks ~1000 tokens, κεφάλαιο ανά αρχείο),
- `index.json` (RAG index: offsets, line counts, titles),
- `entities.json` (αυτόνομη εξαγωγή μέσω `extract_entities.py`),
- `archetype.json` (ταξινόμηση LINEAR_NARRATIVE / ANTHOLOGY_EPISODIC / THEMATIC_EDUCATIONAL).

### Βήμα 2 — 12-Cycle Advanced Artifact Engine

Μέσα στο `parse_book.py` → `write_advanced_artifacts()` καλούνται αυτόματα τα 8 νέα modules:

- `character_psychology.py` → `design/narrative/character-psychology.json` + `voice-fingerprints.json` + `lore/relationship-matrix.json`
- `simulate_pacing_tension.py` → `design/balance/tension-pacing-curve.json`
- `validate_branching_graph.py` → `design/narrative/choice-tree.json` + `consequences-matrix.md`
- `simulate_player_personas.py` → `benchmarks/player-personas-simulation.json`
- `generate_audio_architecture.py` → `design/audio/leitmotif-matrix.json`
- `simulate_knowledge_graph.py` → `lore/information-spread-graph.json`
- `mcts_balance_solver.py` → `benchmarks/nash-equilibrium-report.json`
- `generate_expansion_grammar.py` → `design/narrative/expansion-grammar.json` + DDA + mod schema
- `generate_executive_audit.py` → `benchmarks/executive_audit_report.json`

### Βήμα 3 — Έλεγχος GATE PASS

```bash
python "${CLAUDE_SKILL_DIR}/scripts/validate_output.py" "$OUT_DIR"
```

Ελέγχει: core GDD, Engine & MCP, 12-cycle artifacts, EXECUTIVE_AUDIT_PASS.

---

## Δομή Output Φακέλου

```
<game-project>/
  source/
    full_text.md                   # Πλήρες κείμενο (RAG source)
    paragraph-hashes.json          # SHA-256 ανά παράγραφο + file_hash
  canon/
    entities.json                  # Entities με _uuid + source_offsets
    relationships.json             # Relationships με _source_uuid, _target_uuid
    entity-aliases.json            # Canonical UUID → [aliases]
    world-boundaries.json          # Locations + factions
    world-glossary.json            # Terms + definitions
    unresolved-ambiguities.json    # Quarantine bucket
  derived/
    (design/*, benchmarks/*, lore/* — same as before)
  views/projections/
    narrative-director/            # Reference projection (self-contained)
      IMMUTABLE_KERNEL.md          # Tamper-evident header
      canon.projection.json        # Canon data for this agent
      derived.projection.json      # Derived data for this agent
    [49 agent folders]
  benchmarks/
    player-personas-simulation.json
    nash-equilibrium-report.json
    executive_audit_report.json
  design/
    gdd/
      game-concept.md
      systems-index.md
      game-pillars.md
    narrative/
      character-psychology.json
      voice-fingerprints.json
      choice-tree.json
      framing-hub.md
      expansion-grammar.json
    mechanics/
      concept-matrix.md
      emotion-triggers.md
      dda-rules.json
      faction-dynamics.json
    balance/
      tension-pacing-curve.json
      economy-formulas.md
      progression-gini.json
    audio/
      leitmotif-matrix.json
    art/
      art-bible.md
      lighting-color-script.json
    ai/
      npc-utility-schedules.json
  lore/
    bible.md
    connectors.md
    relationship-matrix.json
    information-spread-graph.json
  technical/
    engine.md
    mcp-servers.md
    mod-api-schema.json
  production/
    stage.txt
    execution-dag.json
    briefs/
    epics/
  audit/
    provenance.json                # Source hash, tool version, UUID map
    verification-report.json
  standards/                       # Only in skill source, not in output
    canonical-uuids.json
    epistemic-model.md
    verification-rules.md
    projection-template.md
    immutable-kernel-spec.md
```

## Αναφορές (References)

- `references/engine-selection.md` — Κριτήρια επιλογής μηχανής & MCP servers.
- `references/genre-taxonomy.md` — 13 είδη, κριτήρια & MDA mapping.
- `references/game-studio-mapping.md` — Αντιστοίχιση βιβλίου στους 49 agents.
- `references/chunking.md` — Τεμαχισμός & RAG index.
- `references/troubleshooting.md` — Edge cases & νοήμονες επιλογές engine.
