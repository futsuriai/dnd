#!/usr/bin/env python3
"""Validate raw session notes before polished session-note generation."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


TIMESTAMP_RE = re.compile(r"^\[\d{2}:\d{2}:\d{2}\]\s+", re.MULTILINE)
DIALOGUE_RE = re.compile(r"^[A-Za-z][A-Za-z'\" .-]{1,40}:\s*\"", re.MULTILINE)
REVIEW_RE = re.compile(r"^[ \t]*review(?:-name)?:", re.IGNORECASE | re.MULTILINE)
PROCESS_LANGUAGE_RE = re.compile(
    r"\b("
    r"GM\s+(?:says|clarifies|rules|ruling|lore|explains)|"
    r"player\s+(?:asks|says|clarifies)|"
    r"table\s+(?:talk|discussion|chatter)|"
    r"transcript|"
    r"last session|"
    r"current plan still"
    r")\b",
    re.IGNORECASE,
)
BAD_NAME_RE = re.compile(r"\b(Nytes|Nýtes|Netus|Nitesh)\b")
RISKY_NITES_RE = re.compile(r"\b(?:Nites.*censored|censored.*Nites)\b", re.IGNORECASE)
OOC_DENSITY_RE = re.compile(
    r"\b(GM|rules:|player|we as players|mechanically|classic movie scene|recording|discord|microphone)\b",
    re.IGNORECASE,
)


class Reporter:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)
        print(f"ERROR: {message}")

    def warn(self, message: str) -> None:
        self.warnings.append(message)
        print(f"WARN: {message}")

    def ok(self, message: str) -> None:
        print(f"OK: {message}")


def line_number(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def check_matches(pattern: re.Pattern[str], text: str, reporter: Reporter, message: str, error: bool = True) -> int:
    count = 0
    for match in pattern.finditer(text):
        count += 1
        location = line_number(text, match.start())
        if error:
            reporter.error(f"line {location}: {message} Found `{match.group(0)}`.")
        else:
            reporter.warn(f"line {location}: {message} Found `{match.group(0)}`.")
    return count


def count_opening_continuity(lines: list[str]) -> int:
    count = 0
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped == "---":
            continue
        if stripped.lower().startswith("continuity:"):
            count += 1
            continue
        break
    return count


def non_review_text(text: str) -> str:
    return "\n".join(
        line for line in text.splitlines()
        if not line.strip().lower().startswith(("review:", "review-name:"))
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw_notes_file", help="Raw Session N.md path")
    parser.add_argument("--session", type=int, help="Session number, used only in messages")
    parser.add_argument("--allow-review-lines", action="store_true", help="Allow review/review-name lines")
    parser.add_argument("--warn-only", action="store_true", help="Report issues but exit 0")
    parser.add_argument("--min-dialogue-lines", type=int, default=8, help="Warn below this preserved dialogue count")
    parser.add_argument("--min-dialogue-ratio", type=float, default=0.15, help="Warn below this dialogue-line ratio")
    args = parser.parse_args()

    path = Path(args.raw_notes_file).expanduser().resolve()
    reporter = Reporter()
    if not path.exists():
        reporter.error(f"Missing raw notes: {path}")
        print(f"Validation complete: {len(reporter.errors)} error(s), {len(reporter.warnings)} warning(s).")
        return 0 if args.warn_only else 1

    text = path.read_text(encoding="utf-8")
    lines = [line for line in text.splitlines() if line.strip()]
    label = f"Raw Session {args.session}" if args.session else path.name

    if not text.strip():
        reporter.error(f"{label} is empty")
    else:
        reporter.ok(f"{label} is non-empty")

    check_matches(TIMESTAMP_RE, text, reporter, "raw notes still contain timestamped transcript lines")
    check_matches(re.compile(r"^#|\bchunk_\d+\b|```", re.MULTILINE), text, reporter, "raw notes contain headings, chunk IDs, or code fences")
    check_matches(PROCESS_LANGUAGE_RE, text, reporter, "raw notes contain table/process phrasing that should be converted or removed")
    check_matches(BAD_NAME_RE, text, reporter, "raw notes contain a known bad canonical spelling")
    check_matches(RISKY_NITES_RE, text, reporter, "raw notes risk equating Nites with the censored unknown birth name", error=False)

    review_count = check_matches(
        REVIEW_RE,
        text,
        reporter,
        "raw notes still contain unresolved review lines",
        error=not args.allow_review_lines,
    )
    if args.allow_review_lines and review_count:
        reporter.warn(f"{review_count} review line(s) remain by explicit allowance")

    opening_continuity = count_opening_continuity(lines)
    if opening_continuity > 3:
        reporter.error(f"opening recap has {opening_continuity} continuity lines; cap this at 1-3")

    prose = non_review_text(text)
    if re.search(r"\bHyr\b", prose) and re.search(r"\bHýr\b", prose):
        reporter.warn("raw notes mix Hyr and Hýr outside review lines; verify prose/store spelling split")

    dialogue_count = len(DIALOGUE_RE.findall(text))
    non_separator_lines = [line for line in lines if line.strip() != "---"]
    ratio = dialogue_count / max(1, len(non_separator_lines))
    if dialogue_count < args.min_dialogue_lines or ratio < args.min_dialogue_ratio:
        reporter.warn(
            f"low dialogue preservation: {dialogue_count} quote line(s), "
            f"{ratio:.1%} of non-separator lines"
        )

    ooc_density = len(OOC_DENSITY_RE.findall(text)) / max(1, len(non_separator_lines))
    if ooc_density > 0.08:
        reporter.warn(f"high possible OOC/process density: {ooc_density:.1%}")

    print()
    print(f"Validation complete: {len(reporter.errors)} error(s), {len(reporter.warnings)} warning(s).")
    return 0 if args.warn_only or not reporter.errors else 1


if __name__ == "__main__":
    sys.exit(main())
