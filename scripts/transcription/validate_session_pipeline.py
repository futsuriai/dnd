#!/usr/bin/env python3
"""Validate durable outputs after a DnD session pipeline run."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


TIMESTAMP_RE = re.compile(r"^\[\d{2}:\d{2}:\d{2}\]\s+", re.MULTILINE)
DIALOGUE_RE = re.compile(r"^[A-Za-z][A-Za-z'\" .-]{1,40}:\s*\"", re.MULTILINE)

BAD_CANONICAL_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bNýtes\b|\bNytes\b"), "Use canonical spelling `Nites`, not `Nýtes` or `Nytes`."),
    (re.compile(r"\bMarie\b"), "Use canonical spelling `Meri`, not `Marie`."),
    (
        re.compile(r"\b(?:Mara|Illaoi|Bigilar)\b"),
        "Unrecognized ASR-like character name; use the canonical entity name or add a real entity before publishing.",
    ),
    (
        re.compile(r"\b(?:Stongalais|Stonegull(?:\s+eyes?)?)\b", re.IGNORECASE),
        "Use canonical phrase `stone goliaths`, not ASR variants like `Stongalais` or `Stonegull eyes`.",
    ),
    (re.compile(r"\bHirotera\b"), "Use canonical spelling `Hieroterra`."),
]
BAD_PUBLIC_PATTERNS: list[tuple[re.Pattern[str], str]] = BAD_CANONICAL_PATTERNS + [
    (re.compile(r"Ardwin,\s+the\s+Black\s+Swan", re.IGNORECASE), "Ardwin is the blacksmith, not the Black Swan."),
    (
        re.compile(r"Is there any books|comically long fuse|tasted the freedom|Mom,\s+not like Jeeves", re.IGNORECASE),
        "Polished public copy preserved a known awkward ASR/direct-transcript phrase; paraphrase or clean it before publishing.",
    ),
    (re.compile(r"Ellara asked if .*Jacinta", re.IGNORECASE), "Verify this likely means Nites, not Jacinta."),
    (
        re.compile(r"\bH[ýy]r\b[^.\n]{0,140}\bJacinta\b|\bJacinta\b[^.\n]{0,140}\bH[ýy]r\b", re.IGNORECASE),
        "In the Session 17 Hýr/static beat, verify this means Nites or the unknown censored birth name, not Jacinta.",
    ),
    (re.compile(r"Session\s+\d+:\s+[a-z]"), "Homepage/session recap appears to lowercase a sentence-leading proper noun."),
    (re.compile(r"By the end,\s+[a-z]"), "Generic recap ending appears to lowercase a sentence-leading proper noun."),
]
SESSION_17_BAD_STATIC_ATTRIBUTION_RE = re.compile(
    r"\bBerridin\s+Arcana\s*=\s*nat(?:ural)?\s*20\b|"
    r"\b(?:static|censorship)\b[^\n]{0,220}\bBerridin\b[^\n]{0,120}\b(?:Arcana\s+natural\s+20|natural\s+20\s+Arcana)\b|"
    r"\bBerridin\b[^\n]{0,120}\b(?:Arcana\s+natural\s+20|natural\s+20\s+Arcana)\b[^\n]{0,220}\b(?:static|censorship|world-scale|world scale|H[ýy]r)\b|"
    r"\bBerridin['’]s\b[^\n]{0,80}\bnatural\s+20\s+Arcana\b[^\n]{0,220}\b(?:static|censorship|world-scale|world scale|H[ýy]r)\b|"
    r"\bBerridin\s+remembered\s+hearing\s+it\b|"
    r"\bvoice\s+was\s+not\s+new\s+to\s+Berridin\b",
    re.IGNORECASE,
)


class Reporter:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)
        print(f"ERROR: {msg}")

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)
        print(f"WARN: {msg}")

    def ok(self, msg: str) -> None:
        print(f"OK: {msg}")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def require_file(path: Path, label: str, reporter: Reporter) -> str:
    if not path.exists():
        reporter.error(f"Missing {label}: {path}")
        return ""
    if path.stat().st_size == 0:
        reporter.error(f"Empty {label}: {path}")
        return ""
    reporter.ok(f"{label} exists: {path}")
    return read_text(path)


def count_matches(pattern: re.Pattern[str], text: str) -> int:
    return sum(1 for _ in pattern.finditer(text))


def check_patterns(
    path: Path,
    text: str,
    reporter: Reporter,
    patterns: list[tuple[re.Pattern[str], str]],
) -> None:
    for pattern, message in patterns:
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            reporter.error(f"{path}:{line}: {message} Found `{match.group(0)}`.")


def check_canonical_text(path: Path, text: str, reporter: Reporter) -> None:
    check_patterns(path, text, reporter, BAD_CANONICAL_PATTERNS)


def check_public_text(path: Path, text: str, reporter: Reporter) -> None:
    check_patterns(path, text, reporter, BAD_PUBLIC_PATTERNS)


def check_session_specific_facts(session: int, path: Path, text: str, reporter: Reporter) -> None:
    if session != 17:
        return

    for match in SESSION_17_BAD_STATIC_ATTRIBUTION_RE.finditer(text):
        line = text.count("\n", 0, match.start()) + 1
        reporter.error(
            f"{path}:{line}: Session 17 Hýr/static-name Arcana natural 20 and familiar-voice realization "
            f"belong to Nyx, not Berridin. Found `{match.group(0)}`."
        )


def object_block(js: str, session: int) -> str:
    marker = f"id: 'session-{session}'"
    start = js.find(marker)
    if start < 0:
        return ""

    brace_start = js.rfind("{", 0, start)
    if brace_start < 0:
        return ""

    depth = 0
    for index in range(brace_start, len(js)):
        char = js[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return js[brace_start : index + 1]
    return ""


def check_sessions_js(path: Path, text: str, session: int, reporter: Reporter) -> None:
    block = object_block(text, session)
    if not block:
        reporter.error(f"{path}: missing session-{session} object")
        return

    checks = [
        ("upcoming: false", f"session-{session} should be marked complete"),
        (f"summaryFile: 'session-{session}.md'", f"session-{session} should reference its summaryFile"),
        ("highlights:", f"session-{session} should have highlights"),
    ]
    for needle, message in checks:
        if needle not in block:
            reporter.error(f"{path}: {message}")

    highlights_match = re.search(r"highlights:\s*\[(.*?)\]", block, re.DOTALL)
    if not highlights_match or "'" not in highlights_match.group(1):
        reporter.error(f"{path}: session-{session} highlights appear empty")

    next_block = object_block(text, session + 1)
    if not next_block:
        reporter.error(f"{path}: missing session-{session + 1} upcoming stub")
    elif "upcoming: true" not in next_block:
        reporter.error(f"{path}: session-{session + 1} stub should be upcoming")


def intermediate_paths(session: int, dnd_dir: Path, ellara_notes_dir: Path) -> list[Path]:
    transcript_dir = ellara_notes_dir / "Transcripts"
    paths: list[Path] = [
        ellara_notes_dir / f"Raw Session {session} Candidate.md",
        ellara_notes_dir / f"Raw Session {session} Reconciled Candidate.md",
        ellara_notes_dir / f"Raw Session {session} Chunks",
        transcript_dir / f"Session {session} OOC Annotation Chunks",
        transcript_dir / f"Session {session} OOC Review Chunks",
        transcript_dir / f"Session {session} OOC Review Chunks From Provider Merge",
        dnd_dir / "src" / "assets" / "sessions" / "transcripts" / f"Session {session}",
        dnd_dir / "src" / "assets" / "sessions" / "transcripts" / f"session_{session}_raw.txt",
    ]
    durable_manifest = transcript_dir / f"Transcript Session {session} - Pipeline Manifest.json"
    paths.extend(
        path
        for path in sorted(transcript_dir.glob(f"Transcript Session {session} - *"))
        if path != durable_manifest
    )
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", required=True, type=int, help="Session number to validate")
    parser.add_argument("--dnd-dir", default="/home/babu/source/dnd", help="DnD repo root")
    parser.add_argument("--ellara-root", default="/home/babu/source/ellara", help="Ellara repo root")
    parser.add_argument("--check-clean", action="store_true", help="Warn if intermediate artifacts remain")
    parser.add_argument("--strict-clean", action="store_true", help="Treat remaining intermediate artifacts as errors")
    parser.add_argument("--skip-home-override", action="store_true", help="Do not require a HomeView recap override")
    parser.add_argument("--skip-story-stage", action="store_true", help="Do not require a StorySoFar staged paragraph")
    args = parser.parse_args()

    session = args.session
    dnd_dir = Path(args.dnd_dir).expanduser().resolve()
    ellara_root = Path(args.ellara_root).expanduser().resolve()
    ellara_notes_dir = ellara_root / "Session Notes"
    reporter = Reporter()

    transcript = require_file(
        ellara_notes_dir / "Transcripts" / f"Transcript Session {session}.txt",
        "canonical transcript",
        reporter,
    )
    raw_notes = require_file(ellara_notes_dir / f"Raw Session {session}.md", "approved raw notes", reporter)
    final_notes = require_file(ellara_notes_dir / f"Session {session}.md", "polished Ellara notes", reporter)
    website_notes = require_file(
        dnd_dir / "src" / "assets" / "sessions" / f"session-{session}.md",
        "website session markdown",
        reporter,
    )

    if transcript and count_matches(TIMESTAMP_RE, transcript) == 0:
        reporter.warn("Canonical transcript has no timestamped lines; verify format if this is intentional.")
    if transcript:
        check_canonical_text(
            ellara_notes_dir / "Transcripts" / f"Transcript Session {session}.txt",
            transcript,
            reporter,
        )

    if raw_notes:
        timestamp_count = count_matches(TIMESTAMP_RE, raw_notes)
        if timestamp_count:
            reporter.error(f"Raw Session {session}.md still contains {timestamp_count} timestamped transcript lines")
        dialogue_count = count_matches(DIALOGUE_RE, raw_notes)
        if dialogue_count < 3:
            reporter.warn(f"Raw Session {session}.md has only {dialogue_count} preserved dialogue lines")

    if final_notes:
        for required in (
            f"# Session {session}",
            "**Locales:**",
            "**Time:**",
            "## 1)",
        ):
            if required not in final_notes:
                reporter.error(f"Session {session}.md missing expected structure marker `{required}`")

    if final_notes and website_notes:
        if final_notes != website_notes:
            reporter.error(f"Website session markdown differs from Ellara Session {session}.md")

    for path, text in (
        (ellara_notes_dir / f"Raw Session {session}.md", raw_notes),
        (ellara_notes_dir / f"Session {session}.md", final_notes),
        (dnd_dir / "src" / "assets" / "sessions" / f"session-{session}.md", website_notes),
    ):
        if text:
            check_session_specific_facts(session, path, text, reporter)

    public_files = [
        dnd_dir / "src" / "assets" / "sessions" / f"session-{session}.md",
        dnd_dir / "src" / "views" / "HomeView.vue",
        dnd_dir / "src" / "views" / "StorySoFarView.vue",
        dnd_dir / "src" / "store" / "sessions.js",
        dnd_dir / "src" / "store" / "locations.js",
        dnd_dir / "src" / "store" / "lore.js",
        dnd_dir / "src" / "store" / "npcs.js",
    ]
    for path in public_files:
        if path.exists():
            public_text = read_text(path)
            check_public_text(path, public_text, reporter)
            check_session_specific_facts(session, path, public_text, reporter)

    sessions_js = dnd_dir / "src" / "store" / "sessions.js"
    if sessions_js.exists():
        check_sessions_js(sessions_js, read_text(sessions_js), session, reporter)
    else:
        reporter.error(f"Missing sessions store: {sessions_js}")

    home_view = dnd_dir / "src" / "views" / "HomeView.vue"
    if not args.skip_home_override and home_view.exists():
        if not re.search(rf"^\s*{session}:\s*['\"]", read_text(home_view), re.MULTILINE):
            reporter.warn(f"HomeView.vue has no explicit recap/next-step override for session {session}")

    story_view = dnd_dir / "src" / "views" / "StorySoFarView.vue"
    if not args.skip_story_stage and story_view.exists():
        if not re.search(rf"minSession:\s*{session}\b", read_text(story_view)):
            reporter.warn(f"StorySoFarView.vue has no staged paragraph for session {session}")

    entity_metadata = dnd_dir / "scripts" / "transcription" / "entity_metadata.json"
    require_file(entity_metadata, "entity metadata", reporter)

    if args.check_clean or args.strict_clean:
        remaining = [path for path in intermediate_paths(session, dnd_dir, ellara_notes_dir) if path.exists()]
        for path in remaining:
            message = f"Intermediate artifact remains: {path}"
            if args.strict_clean:
                reporter.error(message)
            else:
                reporter.warn(message)

    print()
    print(f"Validation complete: {len(reporter.errors)} error(s), {len(reporter.warnings)} warning(s).")
    return 1 if reporter.errors else 0


if __name__ == "__main__":
    sys.exit(main())
