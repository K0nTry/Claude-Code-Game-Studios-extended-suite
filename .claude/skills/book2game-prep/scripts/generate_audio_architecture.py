#!/usr/bin/env python3
"""
generate_audio_architecture.py — Cycle 9: Πολυτροπική Αισθητηριακή Σκηνοθεσία.
Κατασκευάζει βαθιές οδηγίες για Audio Leitmotifs, Cinematic Lighting Color Script,
και Animation Rig Manifests. Προσφέρει Micro-expression directives (FACS).
"""

import json

def cabin_pressure(level: int) -> str:
    return "Low light / High saturation (Desaturated drama)" if level < 3 else "Balanced cinematic (Warm shadows)"

def generate_audio_architecture(chunks: list) -> dict:
    n_chapters = len(chunks) if chunks else 3
    leitmotif_matrix = []

    preset_leitmotifs = [
        {"theme": "Το Μέλλον / Μυστήριο", "scale": "D-Minor", "tempo": 72, "instrument": "Cello Solo & Sub-oscillator"},
        {"theme": "Σύγκρουση / Προδοσία", "scale": "Phrygian", "tempo": 118, "instrument": "Brass Swell & Timpani"},
        {"theme": "Ανακάλυψη / Ελπίδα", "scale": "F-Major", "tempo": 96, "instrument": "Piano + Strings Layer"}
    ]
    
    for idx, (content, title) in enumerate(chunks, 1):
        preset = preset_leitmotifs[idx % len(preset_leitmotifs)]
        leitmotif_matrix.append({
            "chapter_index": idx,
            "chapter_title": title or f"Chapter {idx}",
            "theme": preset["theme"],
            "leitmotif": preset,
            "dynamic_stem": {
                "exploration": "Ambient Pad (Dynamic Low)",
                "tension": "String Ostinato (Rising)",
                "climax": "Full Orchestral Hits"
            }
        })

    return {
        "leitmotif_matrix": leitmotif_matrix,
        "lighting_color_script": [
            {
                "chapter_index": idx,
                "lux_profile": cabin_pressure(idx),
                "color_grading_lut": f"Cinematic Noir LUT v0{idx}",
                "fog_density": round(0.12 + (idx * 0.04), 2)
            } for idx, _ in enumerate(chunks, 1)
        ],
        "facial_rig_directives": {
            "system": "FACS (Facial Action Coding System)",
            "directive_per_chapter": "Κάθε διάλογος παράγει FACS Action Units (π.χ. AU12 Lip Corner Puller για χαρά).",
            "fallback_note": "Οι specialists agents θα χρησιμοποιήσουν το voice-fingerprints.json για τελική anim sync."
        },
        "mixing_instructions": {
            "reverb_type": "Large Hall (Echo of the ancient space)",
            "room_tone_db": -42
        }
    }

if __name__ == "__main__":
    demo = [("c1", "Πρόλογος"), ("c2", "Φως στα Σκοτάδι"), ("c3", "Το Χάσμα")]
    print(json.dumps(generate_audio_architecture(demo), ensure_ascii=False, indent=2))
