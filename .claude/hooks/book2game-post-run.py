#!/usr/bin/env python3
"""
book2game-post-run.py — PostToolUse hook for book2game-prep.
Reads JSON from stdin, detects parse_book.py execution, extracts output directory,
and runs book2game-gate.sh validation.
"""
import json
import os
import re
import subprocess
import sys


def to_wsl(path):
    """Convert a Windows path to a WSL /mnt/<drive>/... path."""
    path = os.path.abspath(path)
    drive, rest = os.path.splitdrive(path)
    return f"/mnt/{drive[0].lower()}{rest.replace(chr(92), '/')}"


def main():
    try:
        # Read hook input from stdin
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)  # Not our concern

    tool_name = data.get("tool_name")
    if tool_name != "Bash":
        sys.exit(0)

    tool_input = data.get("tool_input", {})
    command = tool_input.get("command", "")
    tool_output = data.get("tool_output", "")

    # Check if this is a parse_book.py or book2game-prep command
    if "parse_book.py" not in command and "book2game-prep" not in command:
        sys.exit(0)

    # Extract output directory: prefer absolute path from DONE output, fallback to --out arg
    out_dir = None
    # First try DONE: <absolute path> from tool_output
    match = re.search(r'DONE:\s+(.+)', tool_output)
    if match:
        out_dir = match.group(1).strip()
    else:
        # Fallback: parse --out argument (may be relative)
        match = re.search(r'--out\s+["\']?([^"\'\s]+)', command)
        if match:
            out_dir = match.group(1)

    if not out_dir:
        # Last resort: find most recent book2game output
        fallback = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "skills", "book2game-prep", "scripts", "test_output"
        )
        if os.path.exists(fallback):
            out_dir = fallback

    # Resolve relative paths to absolute
    if out_dir and not os.path.isabs(out_dir):
        # We don't know the working directory, so try common locations
        candidates = [
            out_dir,
            os.path.join(os.getcwd(), out_dir),
            os.path.join(os.path.dirname(__file__), "..", "..", "skills", "book2game-prep", "scripts", out_dir),
        ]
        for c in candidates:
            if os.path.exists(c):
                out_dir = os.path.abspath(c)
                break

    if not out_dir:
        print(f"book2game Concept Gate: could not determine output directory", file=sys.stderr)
        sys.exit(0)  # Don't block, just warn

    # Run the gate hook
    gate_script = os.path.join(os.path.dirname(__file__), "book2game-gate.sh")
    if not os.path.exists(gate_script):
        sys.exit(0)

    try:
        # Convert paths to WSL format for bash
        gate_script_wsl = to_wsl(gate_script)
        out_dir_wsl = to_wsl(out_dir)
        result = subprocess.run(
            ["bash", gate_script_wsl, out_dir_wsl],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            # Gate failed - print warning to stderr (shown to Claude)
            print(f"book2game Concept Gate: validation failed for {out_dir}", file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
        # Exit 0 always for PostToolUse (can't block)
    except subprocess.TimeoutExpired:
        print("book2game Concept Gate: timeout", file=sys.stderr)
    except Exception as e:
        print(f"book2game Concept Gate: error: {e}", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()