#!/usr/bin/env python3
"""
Group chapters into parts (story arcs/stages) based on entity debut/exit beats.
Reads input from chapters/ and entities.json, outputs parts/N/{fulltext.md, entities.json, meta.json} + partition_map.json.

Designed to work with any book2game output that follows this structure:
- chapters/ch01.md, ch02.md, ... (numbered sequentially)
- entities.json with entities having evidence[].chunk (chapter index)
- index.json with entries[].id = "ch{number}"

Formula: max(4, min(max_parts, ceil(total_chapters / 25)))
- max_parts = 8 for total ≤ 250 chapters, 12 for > 250
- Target ~25 chapters per part, flexible ±3 chapters around story beats
- Part <20 chapters merges with next (unless it has a major beat)
- Leftover chapters appended to last part (0 lost)
"""

import json
import math
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set


def load_json(path: Path) -> dict:
    """Load JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(path: Path, data: dict) -> None:
    """Save JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_chapter_text(chapter_path: Path) -> str:
    """Load chapter text from file."""
    with open(chapter_path, 'r', encoding='utf-8') as f:
        return f.read()


def get_entity_chapters(canonical_entities_path: Path, legacy_entities_path: Path = None) -> Dict[str, Set[int]]:
    """
    Build entity → set of chapter indices from entities.json.
    First tries canonical/entities.json, then legacy entities.json as fallback.
    """
    if canonical_entities_path.exists():
        data = load_json(canonical_entities_path)
    elif legacy_entities_path and legacy_entities_path.exists():
        data = load_json(legacy_entities_path)
    else:
        raise FileNotFoundError(f"No entities.json found at {canonical_entities_path}")
    
    entity_chapters = {}
    for category in ['characters', 'locations', 'organizations', 'items']:
        if category not in data:
            continue
        for entity in data[category]:
            name = entity.get('name')
            if not name:
                continue
            chapters = set()
            for ev in entity.get('evidence', []):
                chunk = ev.get('chunk')
                if chunk is not None:
                    chapters.add(int(chunk))
            if chapters:
                entity_chapters[name] = chapters
    
    return entity_chapters


def get_chapter_count(index_path: Path) -> int:
    """Get total number of chapters from index.json."""
    data = load_json(index_path)
    return len(data.get('entries', []))


def get_chapter_files(chapters_dir: Path) -> List[Path]:
    """Get sorted list of chapter markdown files."""
    pattern = re.compile(r'^ch(\d+)(?:-.*?)?\.md$')
    files = []
    for f in chapters_dir.glob('ch*.md'):
        match = pattern.match(f.name)
        if match:
            idx = int(match.group(1))
            files.append((idx, f))
    files.sort(key=lambda x: x[0])
    return [f for _, f in files]


def find_entity_debuts(entity_chapters: Dict[str, Set[int]], total_chapters: int) -> Set[int]:
    """Find chapter indices where new entities debut (first appearance)."""
    debuts = set()
    for entity, chapters in entity_chapters.items():
        if chapters:
            first_ch = min(chapters)
            debuts.add(first_ch)
    return debuts


def find_entity_exits(entity_chapters: Dict[str, Set[int]], total_chapters: int) -> Set[int]:
    """Find chapter indices where entities exit (last appearance)."""
    exits = set()
    for entity, chapters in entity_chapters.items():
        if chapters:
            last_ch = max(chapters)
            exits.add(last_ch)
    return exits


def find_beat_points(entity_chapters: Dict[str, Set[int]], total_chapters: int) -> Set[int]:
    """Find all story beat points: entity debuts and exits."""
    debuts = find_entity_debuts(entity_chapters, total_chapters)
    exits = find_entity_exits(entity_chapters, total_chapters)
    return debuts | exits


def calculate_max_parts(total_chapters: int) -> int:
    """Calculate max parts based on total chapters."""
    if total_chapters <= 250:
        return 8
    else:
        return 12


def calculate_part_count(total_chapters: int, max_parts: int) -> int:
    """Calculate actual number of parts using the formula."""
    return max(4, min(max_parts, math.ceil(total_chapters / 25)))


def find_split_points(total_chapters: int, beat_points: Set[int], target_parts: int) -> List[int]:
    """
    Find optimal split points between chapters.
    
    Returns list of chapter indices where a new part begins (indices 1-based).
    The first part always starts at chapter 1.
    """
    if total_chapters <= 0:
        return []
    
    base_spacing = total_chapters / target_parts
    split_points = [1]  # First part always starts at chapter 1
    
    current_pos = 1
    for part_num in range(1, target_parts):
        target_pos = int(round(current_pos + base_spacing))
        if target_pos >= total_chapters:
            break
        
        # Search ±3 chapters for a beat point
        best_pos = target_pos
        best_score = 0
        for offset in range(-3, 4):
            pos = target_pos + offset
            if pos < 1 or pos > total_chapters:
                continue
            if pos in beat_points:
                score = 3  # High score for beat point
            elif pos in find_entity_debuts({}, total_chapters):
                score = 2  # Medium score for debut
            elif pos in find_entity_exits({}, total_chapters):
                score = 2  # Medium score for exit
            else:
                score = 1  # Default score
            
            if score > best_score:
                best_score = score
                best_pos = pos
        
        if best_pos not in split_points and best_pos < total_chapters:
            split_points.append(best_pos)
        
        current_pos = best_pos
    
    return sorted(split_points)


def get_part_for_chapter(chapter_idx: int, split_points: List[int]) -> int:
    """Determine which part a chapter belongs to."""
    # First part always starts at chapter 1
    if chapter_idx < split_points[1]:
        return 1
    # Find the last split point that is <= chapter_idx
    for i in range(len(split_points) - 1, 0, -1):
        if chapter_idx >= split_points[i]:
            return i + 1
    return 1


def merge_small_parts(parts_chapters: dict, min_chapters: int = 20) -> dict:
    """
    Merge parts that have fewer than min_chapters with the next part.
    Returns updated parts_chapters dict.
    """
    part_nums = sorted(parts_chapters.keys())
    merged = {}
    i = 0
    while i < len(part_nums):
        current_num = part_nums[i]
        current_chapters = parts_chapters[current_num]
        
        # Check if this part is too small and there's a next part
        if len(current_chapters) < min_chapters and i + 1 < len(part_nums):
            # Merge with next part
            next_num = part_nums[i + 1]
            next_chapters = parts_chapters[next_num]
            merged_chapters = current_chapters + next_chapters
            merged[next_num] = merged_chapters
            i += 2  # Skip the next part since it's merged
        else:
            merged[current_num] = current_chapters
            i += 1
    
    return merged


def create_parts(chapter_files: List[Path], split_points: List[int], entity_chapters: Dict[str, Set[int]], 
                 output_dir: Path) -> dict:
    """
    Create part directories and files.
    
    Returns partition_map: {entity_name: [part_indices]} - which entities appear in which parts
    """
    # Build chapter data list
    chapter_data = []
    for f in chapter_files:
        match = re.match(r'^ch(\d+)(?:-.*?)?\.md$', f.name)
        if match:
            idx = int(match.group(1))
            chapter_data.append((idx, f))
    chapter_data.sort(key=lambda x: x[0])
    
    # Group chapters by part
    parts_chapters = {}
    for idx, chapter_path in chapter_data:
        part_idx = get_part_for_chapter(idx, split_points)
        if part_idx not in parts_chapters:
            parts_chapters[part_idx] = []
        parts_chapters[part_idx].append((idx, chapter_path))
    
    # Merge small parts (<20 chapters) with next part
    parts_chapters = merge_small_parts(parts_chapters, min_chapters=20)
    
    # Re-assign part numbers sequentially after merging
    sorted_part_nums = sorted(parts_chapters.keys())
    remapped_chapters = {}
    for new_idx, old_idx in enumerate(sorted_part_nums, 1):
        remapped_chapters[new_idx] = parts_chapters[old_idx]
    
    # Build partition_map: {entity_name: [part_indices]}
    partition_map = {}
    for part_idx, chapters in remapped_chapters.items():
        for idx, chapter_path in chapters:
            for entity_name, entity_chaps in entity_chapters.items():
                if idx in entity_chaps:
                    if entity_name not in partition_map:
                        partition_map[entity_name] = []
                    if part_idx not in partition_map[entity_name]:
                        partition_map[entity_name].append(part_idx)
    
    # Sort part indices for each entity
    for entity_name in partition_map:
        partition_map[entity_name].sort()
    
    # Create part directories
    for part_idx, chapters in remapped_chapters.items():
        finalize_part(chapters, entity_chapters, part_idx, output_dir)
    
    return partition_map


def finalize_part(chapters: List[tuple], entity_chapters: Dict[str, Set[int]], part_num: int, output_dir: Path) -> None:
    """Create a part directory with fulltext.md, entities.json, meta.json."""
    if not chapters:
        return
    
    part_dir = output_dir / f"part_{part_num:02d}"
    part_dir.mkdir(parents=True, exist_ok=True)
    
    # Combine chapter texts
    full_text = ""
    for idx, chapter_path in chapters:
        text = load_chapter_text(chapter_path)
        full_text += f"\n\n--- Chapter {idx} ---\n\n"
        full_text += text
    
    # Find entities that appear in this part
    part_entities = []
    seen_entities = set()
    for idx, chapter_path in chapters:
        for entity_name, entity_chaps in entity_chapters.items():
            if idx in entity_chaps and entity_name not in seen_entities:
                part_entities.append({
                    "name": entity_name,
                    "first_appearance": idx,
                    "last_appearance": max(entity_chaps)
                })
                seen_entities.add(entity_name)
    
    # Save fulltext.md as plain text (not JSON)
    (part_dir / "fulltext.md").write_text(full_text, encoding='utf-8')
    
    # Save entities.json
    save_json(part_dir / "entities.json", {"entities": part_entities})
    
    # Save meta.json
    save_json(part_dir / "meta.json", {
        "part_number": part_num,
        "chapter_range": {
            "first": chapters[0][0],
            "last": chapters[-1][0]
        },
        "chapter_count": len(chapters),
        "entity_count": len(part_entities)
    })


def main():
    # Get input directory (default: current directory)
    input_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    max_parts_arg = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    # Paths
    chapters_dir = input_dir / "chapters"
    entities_path_canonical = input_dir / "canon" / "entities.json"
    entities_path_legacy = input_dir / "entities.json"
    index_path = input_dir / "index.json"
    output_dir = input_dir / "parts"
    
    # Load data
    print(f"Loading data from {input_dir}")
    
    if not index_path.exists():
        raise FileNotFoundError(f"index.json not found at {index_path}")
    
    total_chapters = get_chapter_count(index_path)
    print(f"Total chapters: {total_chapters}")
    
    # Get entity chapters
    entity_chapters = get_entity_chapters(entities_path_canonical, entities_path_legacy)
    print(f"Found {len(entity_chapters)} entities with chapter evidence")
    
    # Calculate part count
    max_parts = max_parts_arg or calculate_max_parts(total_chapters)
    target_parts = calculate_part_count(total_chapters, max_parts)
    print(f"Target parts: {target_parts} (max_parts={max_parts})")
    
    # Find beat points
    beat_points = find_beat_points(entity_chapters, total_chapters)
    print(f"Found {len(beat_points)} beat points (entity debuts/exits)")
    
    # Find split points
    split_points = find_split_points(total_chapters, beat_points, target_parts)
    print(f"Split points: {split_points}")
    
    # Create parts
    chapter_files = get_chapter_files(chapters_dir)
    partition_map = create_parts(chapter_files, split_points, entity_chapters, output_dir)
    
    # Save partition_map.json
    save_json(output_dir / "partition_map.json", partition_map)
    print(f"Created {len(split_points)} parts in {output_dir}")
    print("Done!")


if __name__ == "__main__":
    main()
