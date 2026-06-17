#!/usr/bin/env python3
"""
sort_chest_logs.py

Walks through a directory (and all its subfolders), reads each log file,
counts how many times each player name appears (based on the
"[date time] PlayerName" header lines), and COPIES each file into an
"output" folder named after whichever player appears most often in that
file (i.e. the presumed chest owner).

The output folder is always called "output", is created automatically
inside the directory being scanned if it doesn't already exist, and is
automatically excluded from the scan (so re-running the script won't
re-process files it already copied).

Usage:
    python sort_chest_logs.py [/path/to/input_dir]

If input_dir is omitted, the current directory is used.

Example log format expected in each file:
    [06.06.26  15:58:44] AashesOfTheWake
    Items Added: [10 minecraft:cobblestone]
    Items Removed: []

    [06.06.26  16:03:54] AashesOfTheWake
    Items Added: [125 minecraft:cobblestone]
    Items Removed: []
"""

import argparse
import os
import re
import shutil
import sys
from collections import Counter

# Matches lines like: [06.06.26  15:58:44] AashesOfTheWake
HEADER_RE = re.compile(
    r"^\[\d{2}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2}\]\s+(\S+)\s*$",
    re.MULTILINE,
)


def count_players_in_file(filepath):
    """Return a Counter of player_name -> number of occurrences in the file."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except (OSError, UnicodeDecodeError) as e:
        print(f"  ! Could not read {filepath}: {e}")
        return Counter()

    names = HEADER_RE.findall(content)
    return Counter(names)


def safe_copy(src_path, dest_dir, filename):
    """Copy src_path into dest_dir/filename, avoiding overwriting existing files
    with the same name by appending a numeric suffix if needed."""
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, filename)

    if os.path.exists(dest_path):
        base, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(dest_path):
            dest_path = os.path.join(dest_dir, f"{base}_{counter}{ext}")
            counter += 1

    shutil.copy2(src_path, dest_path)
    return dest_path


def main():
    parser = argparse.ArgumentParser(
        description="Sort chest log files into folders by owner (most frequent player name)."
    )
    parser.add_argument(
        "input_dir",
        nargs="?",
        default=".",
        help="Root directory containing the log files (searched recursively). Defaults to the current directory.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print what would happen, don't actually copy any files.",
    )
    args = parser.parse_args()

    input_dir = os.path.abspath(args.input_dir)
    output_dir = os.path.join(input_dir, "output")

    if not os.path.isdir(input_dir):
        print(f"Error: input directory does not exist: {input_dir}")
        sys.exit(1)

    if not args.dry_run:
        os.makedirs(output_dir, exist_ok=True)
        print(f"Output directory: {output_dir}")

    total_files = 0
    skipped_files = 0
    owner_totals = Counter()

    for root, dirs, files in os.walk(input_dir):
        # Don't descend into (or re-process) the output directory.
        dirs[:] = [
            d for d in dirs
            if os.path.abspath(os.path.join(root, d)) != output_dir
        ]
        if os.path.abspath(root) == output_dir:
            continue

        for filename in files:
            filepath = os.path.join(root, filename)
            total_files += 1

            counts = count_players_in_file(filepath)
            if not counts:
                print(f"  - No player names found in {filepath}, skipping.")
                skipped_files += 1
                continue

            owner, occurrences = counts.most_common(1)[0]
            owner_totals[owner] += 1

            print(f"{filepath}")
            print(f"    Player counts: {dict(counts)}")
            print(f"    -> Owner: {owner} ({occurrences} occurrences)")

            if not args.dry_run:
                dest_dir = os.path.join(output_dir, owner)
                dest_path = safe_copy(filepath, dest_dir, filename)
                print(f"    Copied to: {dest_path}")
            else:
                print(f"    [dry-run] Would copy to: {os.path.join(output_dir, owner, filename)}")

    print("\n--- Summary ---")
    print(f"Total files scanned: {total_files}")
    print(f"Files skipped (no player names found): {skipped_files}")
    print(f"Files sorted by owner: {dict(owner_totals)}")


if __name__ == "__main__":
    main()