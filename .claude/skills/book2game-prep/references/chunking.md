# Chunking — πώς κόβεται το βιβλίο

## Στόχος

Να μην χρειάζεται να διαβάζεις όλο το `full_text.md` κάθε φορά. Οι agents κάνουν `grep -n` στα `chapters/`.

## Κανόνες

- Στόχος: ~1000 tokens ανά chunk (~4000 χαρακτήρες)
- Κόβει σε επικεφαλίδες αν υπάρχουν (`#`, `ΚΕΦΑΛΑΙΟ`, `Chapter`)
- Αν κεφάλαιο > 6000 chars, το σπάει σε `μέρος 1, μέρος 2` ανά παραγράφους
- Δεν κόβει στη μέση πρόταση
- Πρόλογος πριν το πρώτο κεφάλαιο → ξεχωριστό chunk
- Ονόματα αρχείων: `ch01-kefalaio-1-eisagogi.md` (slug, max 40 chars)

## Index

`index.json`:

```json
{
  "source": "book.pdf",
  "total_chars": 123456,
  "total_words": 20000,
  "chunks": 8,
  "entries": [
    {"id": "ch01", "title": "Κεφάλαιο 1", "file": "chapters/ch01-....md", "chars": 4000, "offset": 0}
  ],
  "rag_hint": "grep -rn 'όρος' chapters/"
}
```

## RAG χρήση

```bash
# Βρες πού αναφέρεται ένας χαρακτήρας
grep -rn "Αλέξανδρος" chapters/

# Βρες σκηνή
grep -n "μάχη" full_text.md

# Διάβασε μόνο ένα κεφάλαιο
Read chapters/ch03-*.md
```
