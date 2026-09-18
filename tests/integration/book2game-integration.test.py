#!/usr/bin/env python3
"""
book2game-integration.test.py — PHASE 6 integration tests (stdlib only).

Runs 6 checks across the book2game -> CCGS chain and writes machine-readable
results to tests/results/book2game-integration-result.json.

  1. Skill loads (book2game-prep SKILL.md has `user-invocable: true`)
  2. handoff_to_ccgs.py produces non-empty design/gdd/game-concept.md
  3. validate_book2game.py exits 0 on valid input, 1 on invalid
  4. book2game-gate.sh is silent (exit 0) on OK, warns (exit 1) on fail
  5. /start surfaces "I have a book to adapt" and routes to book2game
  6. Real parse_book.py -> validate_book2game.py pipeline passes (citations + line)

Usage (repo root):
  python tests/integration/book2game-integration.test.py
Exit code: 0 = all PASS, 1 = at least one FAIL.
"""
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RESULTS_PATH = os.path.join(
    ROOT, "tests", "results", "book2game-integration-result.json")
PY = sys.executable

SKILL = os.path.join(
    ROOT, ".claude", "skills", "book2game-prep", "SKILL.md")
HANDOFF = os.path.join(ROOT, "scripts", "handoff_to_ccgs.py")
VALIDATOR = os.path.join(ROOT, "scripts", "validate_book2game.py")
HOOK = os.path.join(ROOT, ".claude", "hooks", "book2game-gate.sh")
START_SKILL = os.path.join(ROOT, ".claude", "skills", "start", "SKILL.md")
PARSER = os.path.join(ROOT, ".claude", "skills", "book2game-prep", "scripts", "parse_book.py")

ENTITIES_OK = {
    "characters": [{"name": "Hero", "citation": "ch01", "line": 4}],
    "locations": [],
    "objects": [],
    "concepts": [],
}
INDEX_OK = {"entries": [{"id": "ch01", "title": "Chapter 1"}]}

results = []


def record(name, path, command, expected, passed, detail=""):
    # Store relpath for portability (Finding: absolute paths -> relpath)
    rel = os.path.relpath(path, ROOT) if os.path.isabs(path) and path.startswith(ROOT) else path
    results.append({
        "name": name,
        "path": rel,
        "command": command,
        "expected": expected,
        "result": "PASS" if passed else "FAIL",
        "detail": detail[:600],
    })
    print(f"[{'PASS' if passed else 'FAIL'}] {name}" + (f" — {detail[:160]}" if detail and not passed else ""))


def run(cmd, cwd=None):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def to_wsl(path):
    """Convert a Windows path to a WSL /mnt/<drive>/... path."""
    # NOTE: Retained intentionally — required for Windows -> WSL path conversion
    # when invoking bash gate via WSL; works on Windows via os.path.splitdrive.
    # Rule #12: Do not remove/rename; used in test_4_hook for cross-platform CI.
    path = os.path.abspath(path)
    drive, rest = os.path.splitdrive(path)
    return f"/mnt/{drive[0].lower()}{rest.replace(chr(92), '/')}"


def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def make_workshop(base):
    """Valid book2game workshop output folder (pre-handoff layout)."""
    write_file(os.path.join(base, "full_text.md"), "# Test Book\n\nSome text.\n")
    write_file(os.path.join(base, "index.json"), json.dumps(INDEX_OK))
    write_file(os.path.join(base, "chapters", "ch01.md"), "# Ch1\n\nText.\n")
    write_file(os.path.join(base, "entities.json"), json.dumps(ENTITIES_OK))
    write_file(os.path.join(base, "design", "gdd", "game-concept.md"), "# Design\n\nConcept text.\n")
    return base


def test_1_skill_loads():
    name = "skill-loads"
    cmd = f"read {os.path.relpath(SKILL, ROOT)} frontmatter"
    try:
        with open(SKILL, encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        return record(name, SKILL, cmd, "user-invocable: true", False, "SKILL.md not found")
    head = text.split("---")
    front = head[1] if len(head) > 2 else ""
    ok = any(
        line.strip().lower().replace(" ", "") == "user-invocable:true"
        for line in front.splitlines()
    )
    record(name, SKILL, cmd, "user-invocable: true",
           ok, "" if ok else f"frontmatter lacks flag: {front.strip()[:200]}")


def test_2_handoff(tmp):
    name = "handoff-game-concept"
    src = make_workshop(os.path.join(tmp, "workshop"))
    dst = os.path.join(tmp, "repo")
    cmd = f"python scripts/handoff_to_ccgs.py <workshop> <repo>"
    rc, out, err = run([PY, HANDOFF, src, dst])
    gc = os.path.join(dst, "design", "gdd", "game-concept.md")
    ok = rc == 0 and os.path.exists(gc) and os.path.getsize(gc) > 0
    record(name, HANDOFF, cmd, "exit 0 + game-concept.md non-empty", ok,
           "" if ok else f"rc={rc} size={(os.path.getsize(gc) if os.path.exists(gc) else 'missing')} err={err.strip()[:200]}")


def test_3_validator(tmp):
    name = "validator-gate"
    good = make_workshop(os.path.join(tmp, "valid"))
    bad = os.path.join(tmp, "invalid")
    os.makedirs(bad, exist_ok=True)
    cmd = "python scripts/validate_book2game.py <out_dir>"
    rc_ok, out_ok, _ = run([PY, VALIDATOR, good])
    rc_bad, out_bad, _ = run([PY, VALIDATOR, bad])
    ok = rc_ok == 0 and "GATE PASS" in out_ok and rc_bad == 1 and "GATE FAIL" in out_bad
    record(name, VALIDATOR, cmd, "exit 0 valid / exit 1 invalid", ok,
           "" if ok else f"valid rc={rc_ok} invalid rc={rc_bad}")


def test_4_hook(tmp):
    name = "hook-gate"
    bash = shutil.which("bash")
    cmd = "bash -lc \"cd <out> && book2game-gate.sh\""
    if not bash:
        return record(name, HOOK, cmd, "silent 0 OK / warn 1 fail",
                      False, "bash not on PATH")
    ok_dir = make_workshop(os.path.join(tmp, "hook_ok"))
    write_file(os.path.join(ok_dir, "design", "gdd", "game-concept.md"),
               "# Concept\n\nText.\n")
    fail_dir = os.path.join(tmp, "hook_fail")
    os.makedirs(fail_dir, exist_ok=True)
    rc_ok, out_ok, _ = run(
        [bash, "-lc", f"cd {shlex.quote(to_wsl(ok_dir))} && {shlex.quote(to_wsl(HOOK))}"])
    rc_fail, _, err_fail = run(
        [bash, "-lc", f"cd {shlex.quote(to_wsl(fail_dir))} && {shlex.quote(to_wsl(HOOK))}"])
    silent = rc_ok == 0 and out_ok == ""
    blocks = rc_fail == 1 and "book2game Concept Gate:" in err_fail
    ok = silent and blocks
    record(name, HOOK, cmd, "silent 0 OK / warn 1 fail", ok,
           "" if ok else f"ok(rc={rc_ok} out={out_ok!r}) fail(rc={rc_fail} err={err_fail.strip()[:200]!r})")


def test_5_start_option():
    name = "start-book-option"
    cmd = f"grep 'I have a book' {os.path.relpath(START_SKILL, ROOT)}"
    try:
        with open(START_SKILL, encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        return record(name, START_SKILL, cmd, "option visible + routes to book2game",
                      False, "start SKILL.md not found")
    visible = "I have a book to adapt" in text
    routes = "book2game-prep" in text and "handoff_to_ccgs" in text
    ok = visible and routes
    record(name, START_SKILL, cmd, "option visible + routes to book2game", ok,
           "" if ok else f"visible={visible} routes={routes}")


def test_6_real_parser_pipeline(tmp):
    """Test real parse_book.py -> validate_book2game.py pipeline with citation/line fields."""
    name = "real-parser-pipeline"
    book = os.path.join(tmp, "test_book.txt")
    out_dir = os.path.join(tmp, "parser_out")
    write_file(book, "# Chapter 1\n\nThe Hero walked through the City.\n\n## Chapter 2\n\nThe Hero met the Dragon.\n")
    cmd = "python parse_book.py <book> --out <out> && python validate_book2game.py <out>"
    rc, out, err = run([PY, PARSER, book, "--out", out_dir])
    if rc != 0:
        record(name, PARSER, cmd, "parse_book.py exit 0 then validate GATE PASS", False,
               f"parser failed: rc={rc} err={err[:200]}")
        return
    rc_val, out_val, err_val = run([PY, VALIDATOR, out_dir])
    ok = rc_val == 0 and "GATE PASS" in out_val
    record(name, PARSER, cmd, "parse_book.py exit 0 then validate GATE PASS", ok,
           "" if ok else f"validator rc={rc_val} out={out_val[:200]} err={err_val[:200]}")


def main():
    tmp = tempfile.mkdtemp(prefix="b2g_phase6_")
    try:
        test_1_skill_loads()
        test_2_handoff(tmp)
        test_3_validator(tmp)
        test_4_hook(tmp)
        test_5_start_option()
        test_6_real_parser_pipeline(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    passed = sum(1 for r in results if r["result"] == "PASS")
    payload = {
        "suite": "book2game-integration",
        "phase": "PHASE 6",
        "total": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "tests": results,
    }
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"\n{passed}/{len(results)} PASS -> {os.path.relpath(RESULTS_PATH, ROOT)}")
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
