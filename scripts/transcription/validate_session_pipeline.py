#!/usr/bin/env python3
"""Validate durable outputs across both DnD and Ellara repos after a session pipeline run."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import pipeline_paths  # noqa: E402


TIMESTAMP_RE = re.compile(r"^\[\d{2}:\d{2}:\d{2}\]\s+", re.MULTILINE)
DIALOGUE_RE = re.compile(
    r"^(?!(?:check|rules|continuity|review|review-name)\s*:)[A-Za-z][A-Za-z'\" .-]{1,40}:\s*\S",
    re.IGNORECASE | re.MULTILINE,
)


def _compile_rule(rule: dict) -> tuple[re.Pattern[str], str]:
    flags = 0
    raw_flags = str(rule.get("flags", ""))
    if "i" in raw_flags:
        flags |= re.IGNORECASE
    if "m" in raw_flags:
        flags |= re.MULTILINE
    return re.compile(rule["pattern"], flags), rule["message"]


def load_shared_rules(
    dnd_dir: Path,
) -> tuple[
    list[tuple[re.Pattern[str], str]],
    list[tuple[re.Pattern[str], str]],
    dict[str, list[tuple[re.Pattern[str], str]]],
]:
    """Load canonical/public bad patterns and session-specific rules from shared_sync_rules.json."""
    candidates = [
        dnd_dir / "scripts" / "shared_sync_rules.json",
        pipeline_paths.DND_DIR / "scripts" / "shared_sync_rules.json",
    ]
    rules_path = next((p for p in candidates if p.is_file()), None)
    if rules_path is None:
        raise FileNotFoundError(f"Missing shared sync rules file: {candidates[0]}")

    data = json.loads(rules_path.read_text(encoding="utf-8"))
    raw_public = data.get("badPublicPatterns", [])
    canonical = [_compile_rule(r) for r in raw_public if r.get("canonical", False)]
    public = [_compile_rule(r) for r in raw_public]
    session_specific = {
        str(sess): [_compile_rule(r) for r in rules]
        for sess, rules in data.get("sessionSpecificRules", {}).items()
    }
    return canonical, public, session_specific


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


def check_session_specific_facts(
    session: int,
    path: Path,
    text: str,
    reporter: Reporter,
    session_rules: dict[str, list[tuple[re.Pattern[str], str]]],
) -> None:
    rules = session_rules.get(str(session), [])
    if rules:
        check_patterns(path, text, reporter, rules)


def object_block(js: str, session: int) -> str:
    match = re.search(rf"\bid\s*:\s*(['\"])session-{session}\1", js)
    if not match:
        return ""

    brace_start = js.rfind("{", 0, match.start())
    if brace_start < 0:
        return ""

    depth = 0
    in_quote: str | None = None
    escaped = False
    for index in range(brace_start, len(js)):
        char = js[index]
        if in_quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == in_quote:
                in_quote = None
            continue
        if char in ("'", '"', "`"):
            in_quote = char
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return js[brace_start : index + 1]
    return ""


def check_sessions_js(path: Path, text: str, session: int, reporter: Reporter) -> str:
    block = object_block(text, session)
    if not block:
        reporter.error(f"{path}: missing session-{session} object")
        return ""

    if not re.search(r"\bupcoming\s*:\s*false\b", block):
        reporter.error(f"{path}: session-{session} should be marked complete")
    if not re.search(rf"\bsummaryFile\s*:\s*(['\"])session-{session}\.md\1", block):
        reporter.error(f"{path}: session-{session} should reference its summaryFile")
    if "highlights:" not in block:
        reporter.error(f"{path}: session-{session} should have highlights")

    highlights_match = re.search(r"highlights\s*:\s*\[(.*?)\]", block, re.DOTALL)
    if not highlights_match or not re.search(r"['\"`][^'\"`]+['\"`]", highlights_match.group(1)):
        reporter.error(f"{path}: session-{session} highlights appear empty")

    next_block = object_block(text, session + 1)
    if not next_block:
        reporter.error(f"{path}: missing session-{session + 1} upcoming stub")
    elif not re.search(r"\bupcoming\s*:\s*true\b", next_block):
        reporter.error(f"{path}: session-{session + 1} stub should be upcoming")
    return block


def intermediate_paths(session: int, dnd_dir: Path, ellara_notes_dir: Path) -> list[Path]:
    """Return paths inside repos that belong in `<audio-dir>/pipeline/` or scratch, not in Ellara/DnD."""
    transcript_dir = ellara_notes_dir / "Transcripts"
    paths: list[Path] = [
        ellara_notes_dir / f"Raw Session {session} Candidate.md",
        ellara_notes_dir / f"Raw Session {session} Reconciled Candidate.md",
        ellara_notes_dir / f"Raw Session {session} - Audit.md",
        ellara_notes_dir / f"Raw Session {session} Chunks",
        transcript_dir / f"Session {session} OOC Annotation Chunks",
        transcript_dir / f"Session {session} OOC Review Chunks",
        transcript_dir / f"Session {session} OOC Review Chunks From Provider Merge",
        dnd_dir / "src" / "assets" / "sessions" / "transcripts" / f"Session {session}",
        dnd_dir / "src" / "assets" / "sessions" / "transcripts" / f"session_{session}_raw.txt",
    ]
    durable_manifest = transcript_dir / f"Transcript Session {session} - Pipeline Manifest.json"
    if transcript_dir.is_dir():
        paths.extend(
            path
            for path in sorted(transcript_dir.glob(f"Transcript Session {session} - *"))
            if path != durable_manifest
        )
    return paths


def check_ellara_campaign_state(
    session: int,
    dnd_dir: Path,
    ellara_root: Path,
    reporter: Reporter,
    *,
    allow_provisional: bool = False,
) -> None:
    script = ellara_root / ".agents" / "skills" / "ellara-session-analysis" / "scripts" / "check_session_delta.py"
    if not script.is_file():
        reporter.warn(f"Ellara delta/validation script not found: {script}")
        return

    cmd = [
        sys.executable,
        "-B",
        str(script),
        "--ellara-root",
        str(ellara_root),
        "--dnd-root",
        str(dnd_dir),
        "--validate",
        "--session",
        str(session),
        "--json",
    ]
    if allow_provisional:
        cmd.append("--allow-provisional")

    res = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=pipeline_paths.no_bytecode_env(),
        check=False,
    )
    try:
        payload = json.loads(res.stdout)
    except json.JSONDecodeError:
        if res.returncode != 0:
            reporter.error(f"Ellara Campaign State check failed ({res.returncode}): {res.stderr or res.stdout}")
        return

    for warn in payload.get("warnings", []):
        reporter.warn(f"[ellara-state] {warn}")
    for err in payload.get("errors", []):
        reporter.error(f"[ellara-state] {err}")
    if payload.get("ok") and res.returncode == 0:
        reporter.ok(f"Ellara Campaign State validated for Session {session}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", required=True, type=int, help="Session number to validate")
    parser.add_argument("--dnd-dir", default=str(pipeline_paths.resolve_dnd_dir()), help="DnD repo root")
    parser.add_argument("--ellara-root", default=str(pipeline_paths.resolve_ellara_dir()), help="Ellara repo root")
    parser.add_argument("--check-clean", action="store_true", help="Warn if intermediate artifacts remain")
    parser.add_argument("--strict-clean", action="store_true", help="Treat remaining intermediate artifacts as errors")
    parser.add_argument("--skip-transcript", action="store_true", help="Do not require canonical transcript in Ellara")
    parser.add_argument("--skip-home-override", action="store_true", help="Do not require a HomeView / sessions.js homeRecap entry")
    parser.add_argument("--skip-story-stage", action="store_true", help="Do not require a StorySoFar / sessions.js storyBeat entry")
    parser.add_argument("--skip-ellara-state", action="store_true", help="Skip Ellara Campaign State validation")
    parser.add_argument("--allow-provisional", action="store_true", help="Allow provisional Ellara brief during validation")
    args = parser.parse_args(argv)

    session = args.session
    dnd_dir = pipeline_paths.resolve_dnd_dir(args.dnd_dir)
    ellara_root = pipeline_paths.resolve_ellara_dir(args.ellara_root)
    ellara_notes_dir = ellara_root / "Session Notes"
    reporter = Reporter()

    bad_canonical_patterns, bad_public_patterns, session_rules = load_shared_rules(dnd_dir)

    transcript = ""
    transcript_path = ellara_notes_dir / "Transcripts" / f"Transcript Session {session}.txt"
    if not args.skip_transcript:
        transcript = require_file(transcript_path, "canonical transcript", reporter)
    elif transcript_path.exists():
        transcript = read_text(transcript_path)

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
        check_patterns(transcript_path, transcript, reporter, bad_canonical_patterns)

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
            check_session_specific_facts(session, path, text, reporter, session_rules)

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
            check_patterns(path, public_text, reporter, bad_public_patterns)
            check_session_specific_facts(session, path, public_text, reporter, session_rules)

    sessions_js = dnd_dir / "src" / "store" / "sessions.js"
    session_block = ""
    if sessions_js.exists():
        session_block = check_sessions_js(sessions_js, read_text(sessions_js), session, reporter)
    else:
        reporter.error(f"Missing sessions store: {sessions_js}")

    has_session_home_recap = bool(re.search(r"\bhomeRecap\s*:", session_block))
    has_session_story_beat = bool(re.search(r"\bstoryBeat\s*:", session_block))

    home_view = dnd_dir / "src" / "views" / "HomeView.vue"
    if not args.skip_home_override and not has_session_home_recap:
        has_legacy_home = home_view.exists() and bool(
            re.search(rf"^\s*{session}\s*:\s*(?:\[|['\"`])", read_text(home_view), re.MULTILINE)
        )
        if not has_legacy_home:
            reporter.warn(
                f"Neither sessions.js (session-{session}.homeRecap) nor HomeView.vue has an explicit recap for session {session}"
            )

    story_view = dnd_dir / "src" / "views" / "StorySoFarView.vue"
    if not args.skip_story_stage and not has_session_story_beat:
        has_legacy_story = story_view.exists() and bool(
            re.search(rf"\bminSession\s*:\s*{session}\b", read_text(story_view))
        )
        if not has_legacy_story:
            reporter.warn(
                f"Neither sessions.js (session-{session}.storyBeat) nor StorySoFarView.vue has a story beat for session {session}"
            )

    entity_metadata = dnd_dir / "scripts" / "transcription" / "entity_metadata.json"
    require_file(entity_metadata, "entity metadata", reporter)

    if not args.skip_ellara_state:
        check_ellara_campaign_state(
            session,
            dnd_dir,
            ellara_root,
            reporter,
            allow_provisional=args.allow_provisional,
        )

    if args.check_clean or args.strict_clean:
        remaining = [path for path in intermediate_paths(session, dnd_dir, ellara_notes_dir) if path.exists()]
        for path in remaining:
            message = f"Intermediate artifact remains in repo (belongs in <audio-dir>/pipeline/): {path}"
            if args.strict_clean:
                reporter.error(message)
            else:
                reporter.warn(message)

    print()
    print(f"Validation complete: {len(reporter.errors)} error(s), {len(reporter.warnings)} warning(s).")
    return 1 if reporter.errors else 0


if __name__ == "__main__":
    sys.exit(main())
