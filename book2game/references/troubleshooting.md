# Troubleshooting

## PDF χωρίς κείμενο (σκαναρισμένο)

```
[Σελίδα 5: εικόνα/σαρωμένο — χωρίς εξαγώγιμο κείμενο]
```

Λύση: Εξαγωγή ως searchable PDF (OCR) ή περίμενε v2 με tesseract. Το skill δεν αποτυγχάνει — γράφει scaffold και σημειώνει στο `active.md`.

## Ελληνικά με λάθος encoding

Το parser δοκιμάζει utf-8 → windows-1253 → iso-8859-7. Αν βλέπεις `Î`/`Ã`, άνοιξε το `full_text.md` και έλεγξε.

## EPUB χωρίς κείμενο

Κάποια EPUB έχουν DRMed ή είναι εικόνες. Δοκίμασε `pandoc book.epub -t gfm -o out.md` χειροκίνητα.

## Μεγάλο βιβλίο (>100k λέξεις)

- Μην κάνεις `Read(full_text.md)` — θα φας όλο το context.
- Κάνε `grep -rn "όρος" chapters/` ή `Read chapters/ch03-*.md`
- Το `index.json` λέει πού είναι τι.

## Pandoc

Αν έχεις pandoc εγκατεστημένο, το skill το προτιμά αυτόματα (πιο σταθερό). Αν όχι, δουλεύει με pure python.

```bash
pandoc --version  # έλεγχος
```

## Deps

```bash
pip install -r scripts/requirements.txt
# ή
pip install pymupdf ebooklib beautifulsoup4 python-docx pdfminer.six mammoth
```

## Validation

```bash
python scripts/validate_output.py "./my-game"
# ✅ GATE PASS ή ❌ GATE FAIL με λεπτομέρειες
```
