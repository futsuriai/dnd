#!/usr/bin/env python3
import argparse
import re
from pathlib import Path

LINE_RE = re.compile(r"^\[(\d{2}:\d{2}:\d{2})\] ([^:]+): (.*)$")

# High-confidence OOC indicators.
OOC_STRONG_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\bcraig\b",
        r"\bnow recording\b",
        r"\brecording\b",
        r"\bcan you hear me\b",
        r"\bmic\b|\bmute\b|\bunmute\b|\blag\b|\bdiscord\b",
        r"\bnext session\b|\bnext sunday\b|\bsession ending\b",
        r"\bit's that time\b|\bit's time for me\b|\bi gotta go\b|\bi have to go\b|\bhe has to go\b|\bshe has to go\b",
        r"\bbobby\b|\bmatt\b|\bandres\b|\barthur\b",
    ]
]

# Weaker OOC indicators; these are only removed if there are no in-game cues.
OOC_WEAK_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\bclimate change\b|\bcovid\b|\bstock crash\b|\bguinness\b|\bhistory books\b",
        r"\bhalo\b|\bspider-?man\b|\bcaptain america\b|\bsolid snake\b|\bbreaking bad\b|\bnighthawks\b",
        r"\bdinner\.?\s+alright\b|\bhot sauce from last, from dinner\b",
    ]
]

# In-game indicators (combat, setting, characters, mechanics relevant to the campaign).
INGAME_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\bnyx\b|\bellara\b|\bberridin\b|\bysidor\b|\bwitty\b|\bmeri\b|\bodwin\b",
        r"\bhyrda\b|\bh\u00fdrda\b|\bducal\b|\bwarforged\b|\bstone goliath\b",
        r"\bcamp\b|\bcave\b|\bmine\b|\bvillage\b|\bsoldier\b|\barcher\b|\bcaptain\b",
        r"\battack\b|\bhit\b|\bdamage\b|\bdead\b|\bsurrender\b|\bcage\b",
        r"\broll\b|\bac\b|\bhp\b|\binitiative\b|\bbonus action\b|\bconcentration\b|\bturn\b",
        r"\bmoonbeam\b|\bacid splash\b|\bmisty step\b|\bmirror image\b|\bminor illusion\b",
        r"\bpoison\b|\bgunpowder\b|\bexplosive\b|\bstealth\b|\bdisguise\b",
    ]
]

FILLER_EXACT = {
    "yeah",
    "yeah.",
    "okay",
    "okay.",
    "ok",
    "ok.",
    "um",
    "um.",
    "um...",
    "uh",
    "uh.",
    "uh...",
    "no",
    "no.",
    "yes",
    "yes.",
    "right",
    "right.",
    "sorry",
    "sorry.",
    "alright",
    "alright.",
}

FILLER_REPEAT_RE = re.compile(r"^(yeah|ok|okay|um|uh|no|yes|right|alright|sorry)(\W+\1){1,}\W*$", re.IGNORECASE)


def count_hits(text: str, patterns):
    return [p.pattern for p in patterns if p.search(text)]


def classify_line(text: str):
    text_l = text.strip().lower()
    words = re.findall(r"[a-zA-Z']+", text_l)

    ooc_strong_hits = count_hits(text, OOC_STRONG_PATTERNS)
    ooc_weak_hits = count_hits(text, OOC_WEAK_PATTERNS)
    ingame_hits = count_hits(text, INGAME_PATTERNS)

    filler = text_l in FILLER_EXACT or bool(FILLER_REPEAT_RE.match(text_l))
    short = len(words) <= 2

    # Remove only high-confidence OOC lines.
    if ooc_strong_hits and not ingame_hits:
        return "remove", "ooc_strong"
    if ooc_weak_hits and not ingame_hits:
        return "remove", "ooc_weak"

    # Mixed cues are ambiguous.
    if (ooc_strong_hits or ooc_weak_hits) and ingame_hits:
        return "ambiguous", "mixed_ooc_ingame"

    # Keep pure filler lines by default; they are often in-game reactions.
    if filler or short:
        return "keep", "short_or_filler"

    # Lines with unclear broken phrasing are ambiguous for manual review.
    if text.count("...") >= 2 and len(words) < 8 and not ingame_hits:
        return "ambiguous", "fragment"

    return "keep", "campaign_relevant"


def run(input_path: Path, filtered_path: Path, ambiguous_path: Path, report_path: Path):
    lines = input_path.read_text(encoding="utf-8").splitlines()

    kept = []
    ambiguous = []
    removed = []

    for idx, line in enumerate(lines, 1):
        m = LINE_RE.match(line)
        if not m:
            # Preserve unknown-format lines in filtered output, but mark ambiguous.
            kept.append(line)
            ambiguous.append((idx, "format", line))
            continue

        text = m.group(3)
        action, reason = classify_line(text)

        if action == "keep":
            kept.append(line)
        elif action == "remove":
            removed.append((idx, reason, line))
        else:
            kept.append(line)
            ambiguous.append((idx, reason, line))

    filtered_path.write_text("\n".join(kept) + "\n", encoding="utf-8")

    with ambiguous_path.open("w", encoding="utf-8") as f:
        for idx, reason, line in ambiguous:
            f.write(f"[line {idx}][{reason}] {line}\n")

    with report_path.open("w", encoding="utf-8") as f:
        f.write("Linewise OOC Filter Report\n")
        f.write(f"Input: {input_path}\n")
        f.write(f"Filtered: {filtered_path}\n")
        f.write(f"Ambiguous: {ambiguous_path}\n")
        f.write(f"Total lines: {len(lines)}\n")
        f.write(f"Kept lines: {len(kept)}\n")
        f.write(f"Removed OOC lines: {len(removed)}\n")
        f.write(f"Ambiguous lines: {len(ambiguous)}\n\n")

        f.write("Removed lines:\n")
        for idx, reason, line in removed:
            f.write(f"[line {idx}][{reason}] {line}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Conservative linewise OOC filter with ambiguous review output")
    parser.add_argument("input_file")
    parser.add_argument("filtered_file")
    parser.add_argument("ambiguous_file")
    parser.add_argument("report_file")
    args = parser.parse_args()

    run(
        Path(args.input_file),
        Path(args.filtered_file),
        Path(args.ambiguous_file),
        Path(args.report_file),
    )
