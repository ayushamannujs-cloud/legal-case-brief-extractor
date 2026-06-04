#!/usr/bin/env python3
"""
sync_cases.py — parse pending_cases.md and append entries to server/data.json.

Stage 2 of the Markdown-Mediated Synchronization workflow:
    1. Backs up data.json to data.json.bak
    2. Parses ### Title / **Description:** blocks from the pending markdown
    3. Skips entries whose title already exists in data.json (case-insensitive)
    4. Assigns a UUID v4 to each new entry
    5. Appends to data["terminologies"]
    6. Heuristically creates connections between case briefs and parent statutes
    7. Writes data.json back with 2-space indentation

Usage:
    python3 sync_cases.py \
        --pending /path/to/pending_cases.md \
        --data /path/to/server/data.json

Flags:
    --dry-run     Parse and report, but don't write files.
    --no-backup   Skip writing data.json.bak.
    --important "Title 1" --important "Title 2"
                  Force isImportant=true on the given titles (case-insensitive).
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import uuid
from pathlib import Path
from typing import Iterable


ENTRY_SPLIT_RE = re.compile(r"^---\s*$", re.MULTILINE)
HEADER_RE = re.compile(r"^###\s+(.+?)\s*$", re.MULTILINE)
DESC_RE = re.compile(r"\*\*Description:\*\*\s*\n(.+)", re.DOTALL)

# Patterns for auto-connection heuristics.
# Each pattern produces a normalized statute reference string we can match
# against existing terminology titles.
STATUTE_PATTERNS = [
    # "Section 85 BNS", "Section 498-A IPC", "section 63"
    re.compile(r"\b[Ss]ection\s+(\d+[A-Za-z\-]*)\s*(BNS|IPC|CrPC|BNSS|BSA|IEA)?\b"),
    # "Sec. 75", "Sec. 77 BNS"
    re.compile(r"\b[Ss]ec\.\s*(\d+[A-Za-z\-]*)\s*(BNS|IPC|CrPC|BNSS|BSA|IEA)?\b"),
    # bare "S. 482", "S.63"
    re.compile(r"\bS\.\s*(\d+[A-Za-z\-]*)\s*(BNS|IPC|CrPC|BNSS|BSA|IEA)?\b"),
    # "498A IPC" / "498-A IPC" without the word Section
    re.compile(r"\b(\d{2,4}[A-Za-z\-]?)\s*(BNS|IPC|CrPC|BNSS|BSA|IEA)\b"),
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--pending", required=True, help="Path to pending_cases.md")
    p.add_argument("--data", required=True, help="Path to server/data.json")
    p.add_argument("--dry-run", action="store_true", help="Parse and report; do not write")
    p.add_argument("--no-backup", action="store_true", help="Skip the .bak file")
    p.add_argument("--important", action="append", default=[],
                   help="Mark these titles as isImportant=true (repeatable, case-insensitive)")
    return p.parse_args()


def parse_pending(text: str) -> list[dict]:
    """Split the markdown on `---` dividers and pull title + description per block."""
    entries = []
    blocks = ENTRY_SPLIT_RE.split(text)
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        header_match = HEADER_RE.search(block)
        if not header_match:
            # The first block is the file's intro header; skip silently.
            continue
        title = header_match.group(1).strip()
        # Description is everything after **Description:**
        desc_match = DESC_RE.search(block)
        if not desc_match:
            print(f"  ! Skipping '{title}' — no **Description:** found", file=sys.stderr)
            continue
        description = desc_match.group(1).strip()
        entries.append({"title": title, "description": description})
    return entries


def is_case_brief(entry: dict) -> bool:
    """Heuristic: titles that look like 'X v. Y' or contain a citation are cases."""
    t = entry["title"]
    if " v. " in t or " v " in t or " vs. " in t.lower():
        return True
    # Bracketed citations like [AIR 1996 SC 309] are a strong case signal
    if re.search(r"\[(AIR|SCC|SCR)\s+\d", t):
        return True
    return False


def find_statute_refs(text: str) -> set[str]:
    """Pull out normalized statute references from a description.

    Returns a set of canonical strings like 'section 85 bns', 'section 498 ipc',
    '498a ipc'. We'll match these (substring, case-insensitive) against existing
    terminology titles to decide whether to create a connection.
    """
    refs: set[str] = set()
    for pat in STATUTE_PATTERNS:
        for m in pat.finditer(text):
            num = m.group(1).strip().lower()
            code = (m.group(2) or "").strip().lower()
            if code:
                refs.add(f"section {num} {code}")
                refs.add(f"{num} {code}")
            else:
                refs.add(f"section {num}")
    return refs


def find_existing_case_refs(text: str, existing_titles: list[str]) -> set[str]:
    """Find references to existing case-brief titles inside the description."""
    hits: set[str] = set()
    for title in existing_titles:
        # Look for the case name part before the comma/citation
        name = re.split(r"[,\[\(]", title, maxsplit=1)[0].strip()
        if len(name) < 6:  # too short to be reliably unique
            continue
        if name.lower() in text.lower():
            hits.add(title)
    return hits


def title_matches_statute_ref(title: str, ref: str) -> bool:
    """Loose match: does this terminology title look like the statute referenced?"""
    t = title.lower()
    # Ref like "section 85 bns" — require both the number token and the code token (if present)
    parts = ref.split()
    return all(p in t for p in parts)


def main() -> int:
    args = parse_args()

    pending_path = Path(args.pending)
    data_path = Path(args.data)

    if not pending_path.is_file():
        print(f"Pending file not found: {pending_path}", file=sys.stderr)
        return 2
    if not data_path.is_file():
        print(f"Data file not found: {data_path}", file=sys.stderr)
        return 2

    pending_text = pending_path.read_text(encoding="utf-8")
    data = json.loads(data_path.read_text(encoding="utf-8"))
    data.setdefault("terminologies", [])
    data.setdefault("connections", [])

    existing_titles_lower = {t["title"].strip().lower() for t in data["terminologies"]}
    existing_titles = [t["title"] for t in data["terminologies"]]

    parsed = parse_pending(pending_text)
    if not parsed:
        print("No entries found in pending file.")
        return 0

    important_set = {s.strip().lower() for s in args.important}

    added: list[dict] = []
    skipped: list[str] = []

    for entry in parsed:
        if entry["title"].strip().lower() in existing_titles_lower:
            skipped.append(entry["title"])
            continue
        new_row = {
            "id": str(uuid.uuid4()),
            "title": entry["title"],
            "description": entry["description"],
        }
        if entry["title"].strip().lower() in important_set:
            new_row["isImportant"] = True
        added.append(new_row)

    # Connection generation: for each added case brief, look for statute
    # references and other case-name references in its description, match them
    # to existing or freshly-added terminology titles, and create undirected
    # edges (deduped against existing edges).
    all_rows = data["terminologies"] + added
    title_to_id = {row["title"]: row["id"] for row in all_rows}

    existing_edges = {tuple(sorted((c["sourceId"], c["targetId"]))) for c in data["connections"]}
    new_edges: list[dict] = []

    for row in added:
        if not is_case_brief(row):
            continue
        src_id = row["id"]
        refs = find_statute_refs(row["description"])
        for ref in refs:
            for title, tid in title_to_id.items():
                if tid == src_id:
                    continue
                if title_matches_statute_ref(title, ref):
                    edge_key = tuple(sorted((src_id, tid)))
                    if edge_key in existing_edges:
                        continue
                    existing_edges.add(edge_key)
                    new_edges.append({"sourceId": src_id, "targetId": tid})
        # Cross-references to other cases
        case_refs = find_existing_case_refs(row["description"], [t for t in title_to_id if t != row["title"]])
        for ref_title in case_refs:
            tid = title_to_id[ref_title]
            edge_key = tuple(sorted((src_id, tid)))
            if edge_key in existing_edges:
                continue
            existing_edges.add(edge_key)
            new_edges.append({"sourceId": src_id, "targetId": tid})

    # Report
    print(f"Parsed {len(parsed)} entr{'y' if len(parsed) == 1 else 'ies'} from {pending_path.name}")
    print(f"  + Added:   {len(added)}")
    for row in added:
        flag = " [important]" if row.get("isImportant") else ""
        print(f"      - {row['title']}{flag}")
    print(f"  ~ Skipped (already in db): {len(skipped)}")
    for t in skipped:
        print(f"      - {t}")
    print(f"  + New connections: {len(new_edges)}")
    for e in new_edges:
        src_title = next(r["title"] for r in all_rows if r["id"] == e["sourceId"])
        tgt_title = next(r["title"] for r in all_rows if r["id"] == e["targetId"])
        print(f"      - {src_title}  <->  {tgt_title}")

    if args.dry_run:
        print("\n(dry run — no files written)")
        return 0

    if not added and not new_edges:
        print("\nNothing to write.")
        return 0

    # Backup, then write
    if not args.no_backup:
        bak_path = data_path.with_suffix(data_path.suffix + ".bak")
        shutil.copy2(data_path, bak_path)
        print(f"\nBackup written to {bak_path}")

    data["terminologies"].extend(added)
    data["connections"].extend(new_edges)

    data_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {data_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
