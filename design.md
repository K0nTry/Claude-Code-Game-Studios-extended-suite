# Design — External Audit Resolution

**Αρχή:** κάθε εύρημα κλείνει με εντολή + απόδειξη. Όχι λόγια.

## Έλεγχοι ανά task

- T4 (F7,F8): `validate-commit.sh` υπάρχει + τρέχει. Docs αναφέρουν hooks.
- T5 (F9,F10): backup φάκελος υπάρχει. Tests φάκελος υπάρχει.
- T6 (F11,F12): αρίθμηση skills + frontmatter `user-invocable`.

## Κριτήρια κλεισίματος

- Εντολή έτρεξε, έξοδος καταγράφηκε.
- 0 ευρήματα χωρίς απόδειξη.
