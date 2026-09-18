# Software Factory Handoff: Engine Specialist Agents Replacement

## Repo Summary
- **Target**: `C:\Users\Kon_Try\Desktop\Claude-Code-Game-Studios-main\.claude\agents\`
- **Total agents**: 49 (15 engine specialists + 34 others)
- **Operation**: Clean replacement of 15 engine specialists from `CCGS-agents-final` (2026-09-16)
- **Source**: `C:\Users\Kon_Try\Desktop\CCGS-agents-final\` (15 files, newer version)

---

## Agent Table: 15 Output Agents → Αντικαθίστανται

| # | Engine | Agent File | Status |
|---|--------|------------|--------|
| 1 | Godot | `godot-specialist.md` | ✅ REPLACE |
| 2 | Godot | `godot-gdscript-specialist.md` | ✅ REPLACE |
| 3 | Godot | `godot-csharp-specialist.md` | ✅ REPLACE |
| 4 | Godot | `godot-gdextension-specialist.md` | ✅ REPLACE |
| 5 | Godot | `godot-shader-specialist.md` | ✅ REPLACE |
| 6 | Unity | `unity-specialist.md` | ✅ REPLACE |
| 7 | Unity | `unity-dots-specialist.md` | ✅ REPLACE |
| 8 | Unity | `unity-addressables-specialist.md` | ✅ REPLACE |
| 9 | Unity | `unity-shader-specialist.md` | ✅ REPLACE |
| 10 | Unity | `unity-ui-specialist.md` | ✅ REPLACE |
| 11 | Unreal | `unreal-specialist.md` | ✅ REPLACE |
| 12 | Unreal | `ue-gas-specialist.md` | ✅ REPLACE |
| 13 | Unreal | `ue-blueprint-specialist.md` | ✅ REPLACE |
| 14 | Unreal | `ue-replication-specialist.md` | ✅ REPLACE |
| 15 | Unreal | `ue-umg-specialist.md` | ✅ REPLACE |

---

## Agent Table: 34 Input Agents → ΔΕΝ ΑΓΓΙΖΟΝΤΑΙ

| Category | Agents (34) |
|----------|-------------|
| **Core Roles** | creative-director, producer, technical-director, lead-programmer, gameplay-programmer, engine-programmer, tools-programmer, network-programmer, ai-programmer, performance-analyst, devops-engineer, security-engineer |
| **Design** | game-designer, systems-designer, level-designer, economy-designer, live-ops-designer, narrative-director, writer, world-builder |
| **Art/Audio** | art-director, technical-artist, sound-designer, audio-director, ui-programmer, ux-designer, accessibility-specialist |
| **QA/Release** | qa-lead, qa-tester, release-manager |
| **Ops/Community** | community-manager, localization-lead, analytics-engineer |
| **Other** | prototyper |

> **Επιβεβαίωση**: 34 input + 15 output = **49 σύνολο**. Τα 15 output αντικαθίστανται, οι 34 input παραμένουν αμετάβλητα.

---

## Embed Points (Πού γίνεται η αλλαγή)

| Action | Path | Description |
|--------|------|-------------|
| **BACKUP** | `C:\Users\Kon_Try\Desktop\Claude-Code-Game-Studios-main\.claude\agents\_backup_pre_merge\` | Δημιουργία φακέλου backup |
| **BACKUP COPY** | 15 αρχεία → `_backup_pre_merge\` | Αντιγραφή τρέχουσων 15 agents |
| **REPLACE** | 15 αρχεία στο `.claude\agents\` | Αντικατάσταση με αρχεία από `CCGS-agents-final\` |

---

## Proposed Changes (Έτοιμα για Builder)

| # | Action | Path | Source | Precondition |
|---|--------|------|--------|--------------|
| 1 | CREATE_DIR | `.claude\agents\_backup_pre_merge\` | — | Directory exists |
| 2 | COPY | `.claude\agents\_backup_pre_merge\godot-specialist.md` | `.claude\agents\godot-specialist.md` | Source exists |
| 3 | COPY | `.claude\agents\_backup_pre_merge\godot-gdscript-specialist.md` | `.claude\agents\godot-gdscript-specialist.md` | Source exists |
| 4 | COPY | `.claude\agents\_backup_pre_merge\godot-csharp-specialist.md` | `.claude\agents\godot-csharp-specialist.md` | Source exists |
| 5 | COPY | `.claude\agents\_backup_pre_merge\godot-gdextension-specialist.md` | `.claude\agents\godot-gdextension-specialist.md` | Source exists |
| 6 | COPY | `.claude\agents\_backup_pre_merge\godot-shader-specialist.md` | `.claude\agents\godot-shader-specialist.md` | Source exists |
| 7 | COPY | `.claude\agents\_backup_pre_merge\unity-specialist.md` | `.claude\agents\unity-specialist.md` | Source exists |
| 8 | COPY | `.claude\agents\_backup_pre_merge\unity-dots-specialist.md` | `.claude\agents\unity-dots-specialist.md` | Source exists |
| 9 | COPY | `.claude\agents\_backup_pre_merge\unity-addressables-specialist.md` | `.claude\agents\unity-addressables-specialist.md` | Source exists |
| 10 | COPY | `.claude\agents\_backup_pre_merge\unity-shader-specialist.md` | `.claude\agents\unity-shader-specialist.md` | Source exists |
| 11 | COPY | `.claude\agents\_backup_pre_merge\unity-ui-specialist.md` | `.claude\agents\unity-ui-specialist.md` | Source exists |
| 12 | COPY | `.claude\agents\_backup_pre_merge\unreal-specialist.md` | `.claude\agents\unreal-specialist.md` | Source exists |
| 13 | COPY | `.claude\agents\_backup_pre_merge\ue-gas-specialist.md` | `.claude\agents\ue-gas-specialist.md` | Source exists |
| 14 | COPY | `.claude\agents\_backup_pre_merge\ue-blueprint-specialist.md` | `.claude\agents\ue-blueprint-specialist.md` | Source exists |
| 15 | COPY | `.claude\agents\_backup_pre_merge\ue-replication-specialist.md` | `.claude\agents\ue-replication-specialist.md` | Source exists |
| 16 | COPY | `.claude\agents\_backup_pre_merge\ue-umg-specialist.md` | `.claude\agents\ue-umg-specialist.md` | Source exists |
| 17 | OVERWRITE | `.claude\agents\godot-specialist.md` | `CCGS-agents-final\godot\godot-specialist.md` | Backup done |
| 18 | OVERWRITE | `.claude\agents\godot-gdscript-specialist.md` | `CCGS-agents-final\godot\godot-gdscript-specialist.md` | Backup done |
| 19 | OVERWRITE | `.claude\agents\godot-csharp-specialist.md` | `CCGS-agents-final\godot\godot-csharp-specialist.md` | Backup done |
| 20 | OVERWRITE | `.claude\agents\godot-gdextension-specialist.md` | `CCGS-agents-final\godot\godot-gdextension-specialist.md` | Backup done |
| 21 | OVERWRITE | `.claude\agents\godot-shader-specialist.md` | `CCGS-agents-final\godot\godot-shader-specialist.md` | Backup done |
| 22 | OVERWRITE | `.claude\agents\unity-specialist.md` | `CCGS-agents-final\unity\unity-specialist.md` | Backup done |
| 23 | OVERWRITE | `.claude\agents\unity-dots-specialist.md` | `CCGS-agents-final\unity\unity-dots-specialist.md` | Backup done |
| 24 | OVERWRITE | `.claude\agents\unity-addressables-specialist.md` | `CCGS-agents-final\unity\unity-addressables-specialist.md` | Backup done |
| 25 | OVERWRITE | `.claude\agents\unity-shader-specialist.md` | `CCGS-agents-final\unity\unity-shader-specialist.md` | Backup done |
| 26 | OVERWRITE | `.claude\agents\unity-ui-specialist.md` | `CCGS-agents-final\unity\unity-ui-specialist.md` | Backup done |
| 27 | OVERWRITE | `.claude\agents\unreal-specialist.md` | `CCGS-agents-final\unreal\unreal-specialist.md` | Backup done |
| 28 | OVERWRITE | `.claude\agents\ue-gas-specialist.md` | `CCGS-agents-final\unreal\ue-gas-specialist.md` | Backup done |
| 29 | OVERWRITE | `.claude\agents\ue-blueprint-specialist.md` | `CCGS-agents-final\unreal\ue-blueprint-specialist.md` | Backup done |
| 30 | OVERWRITE | `.claude\agents\ue-replication-specialist.md` | `CCGS-agents-final\unreal\ue-replication-specialist.md` | Backup done |
| 31 | OVERWRITE | `.claude\agents\ue-umg-specialist.md` | `CCGS-agents-final\unreal\ue-umg-specialist.md` | Backup done |

---

## Anti-Block Check
- ✅ **Κανένα άλλο αρχείο** δεν αναφορά τα 15 agents με path (μόνο με όνομα agent)
- ✅ **Κανένα skill/workflow** δεν σπάει — τα ονόματα agents παραμένουν ίδια
- ✅ **Agent roster/coordination docs** χρησιμοποιούν ονόματα, όχι paths
- ✅ **0% filler/truncation** στα νέα αρχεία (από PROVENANCE.md)
- ✅ **YAML frontmatter identical**: `name`, `description`, `tools`, `model`, `difficulty`, `maxTurns`

---

## Rollback Plan

| Step | Command | Description |
|------|---------|-------------|
| 1 | `copy .claude\agents\_backup_pre_merge\*.md .claude\agents\` | Επαναφορά από backup (Windows) |
| 2 | `git checkout -- .claude\agents\godot-specialist.md ...` (15 files) | Git restore αν backup αποτύχει |
| 3 | Manual: Copy from `_backup_pre_merge\` to `.claude\agents\` | Χειροκίνητη επαναφορά αν και τα δύο αποτύχουν |

---

## Execution Instructions (για Builder)

| # | Action | Path | Content | Precondition |
|---|--------|------|---------|--------------|
| 1 | CREATE_DIR | `.claude\agents\_backup_pre_merge\` | — | Repo exists |
| 2-16 | COPY (backup) | `.claude\agents\_backup_pre_merge\{15 files}` | From current `.claude\agents\` | Backup dir created |
| 17-31 | OVERWRITE (replace) | `.claude\agents\{15 files}` | From `CCGS-agents-final\{engine}\` | Backup verified |

**Σειρά εκτέλεσης**: 1 → 2-16 (parallel OK) → 17-31 (parallel OK)

---

## Success Criteria (για Builder)

| # | Check | Command | Pass Criteria |
|---|-------|---------|---------------|
| 1 | Backup exists | `dir .claude\agents\_backup_pre_merge\` | 15 files present |
| 2 | Files replaced | `dir .claude\agents\godot-specialist.md` + 14 others | 15 files updated (size/timestamp changed) |
| 3 | Content verify | `grep "Stress Gate" .claude\agents\godot-specialist.md` | Found (new pipeline section) |
| 4 | Content verify | `grep "Closed Loop" .claude\agents\unity-specialist.md` | Found (new pipeline section) |
| 5 | Content verify | `grep "Field of Expertise" .claude\agents\ue-gas-specialist.md` | Found (locked content) |
| 6 | Non-touched verify | `diff .claude\agents\_backup_pre_merge\game-designer.md .claude\agents\game-designer.md` | No differences (or file not in backup) |
| 7 | Count verify | `dir /b .claude\agents\*.md | find /c /v ""` | Returns **49** |

---

## Handoff File Location
**Γράφτηκε στο:** `C:\Users\Kon_Try\Desktop\Claude-Code-Game-Studios-main\plans\software-factory-handoff.md`

---

## Next Steps
1. Builder executes steps 1-31
2. Builder verifies all 7 success criteria
3. You confirm backup OK → builder deletes `_backup_pre_merge\`