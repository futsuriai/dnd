#!/usr/bin/env python3
"""Audit scene-based raw notes against the transcript and patch them in place.

Runs after raw_notes_auto.py, using its work dir (scene_plan.json, scene_XX.md):

1. Every `ooc` scene the planner skipped is checked for real game content
   (in-character dialogue, GM narration, rolls, decisions). Scenes that have
   some are reclassified as `play`; with --fix they get notes written AND are
   immediately audited too.
2. Every play/recap scene is audited by an LLM (with CANONICAL_CAST_REFERENCE,
   NameNormalizer hints, adjacent scene boundary context, and `--json-schema`)
   for OOC leaks, missing in-game beats, and wrong attributions.
3. Deterministic `DICE`-roll coverage check verifies that logged D&D Beyond
   rolls in play scenes appear in the scene notes.
4. Optional `--audio-verify` uses Gemini 4 Neon (`gemini-4-neon-high`) to
   listen directly to speaker audio for flagged misattributions / uncertain
   names in `review_queue.json`.
5. Writes `<work-dir>/audit.json` and `<work-dir>/Raw Session N - Audit.md`
   (or `--report`), never polluting `ellara/Session Notes/`. Fails loudly
   (exit code 2) if any scene audit fails after retries unless `--allow-partial`.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import agent_cli  # noqa: E402
import asr_common  # noqa: E402
import raw_notes_auto  # noqa: E402
from name_normalizer import NameNormalizer  # noqa: E402
from note_generation_guidance import CANONICAL_CAST_REFERENCE  # noqa: E402

try:
    import pipeline_paths as _pipeline_paths
except ImportError:
    _pipeline_paths = None

WORKSPACE = _pipeline_paths.DND_DIR if _pipeline_paths is not None else SCRIPT_DIR.parent.parent

OOC_CHECK_SCHEMA = {
    "type": "object",
    "properties": {
        "has_game_content": {"type": "boolean"},
        "evidence": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["has_game_content", "evidence"],
}

AUDIT_SCHEMA = {
    "type": "object",
    "properties": {
        "ooc_in_notes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "note": {"type": "string"},
                    "why": {"type": "string"},
                },
                "required": ["note", "why"],
            },
        },
        "missing_ic": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "lines": {"type": "string"},
                    "beat": {"type": "string"},
                    "importance": {"type": "string", "enum": ["high", "medium"]},
                    "after_note": {"type": "string"},
                    "add": {"type": "string"},
                },
                "required": ["lines", "beat", "importance", "after_note", "add"],
            },
        },
        "misattributions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "note": {"type": "string"},
                    "fix": {"type": "string"},
                    "replacement": {"type": "string"},
                },
                "required": ["note", "fix", "replacement"],
            },
        },
    },
    "required": ["ooc_in_notes", "missing_ic", "misattributions"],
}

AUDIO_VERIFY_SCHEMA = {
    "type": "object",
    "properties": {
        "verified_text": {"type": "string"},
        "confirmed_speaker": {"type": "string"},
        "assessment": {"type": "string"},
    },
    "required": ["verified_text", "confirmed_speaker", "assessment"],
}

OOC_CHECK_PROMPT = """This stretch of a Dungeons & Dragons session transcript was classified as out-of-character
(setup, tech, breaks, real-world chatter) and will be left out of the session notes. Check whether that is right.
`GM` is the game master and voices NPCs; `DICE` lines are rolls.

Return JSON matching the schema: {{"has_game_content": true|false, "evidence": ["<line number>: <why it is game content>", ...]}}
Answer true only if it contains a substantive game beat: in-character dialogue that matters, GM narration or NPC
speech, a roll with an outcome, a ruling that changes what happens, or a party decision. A single throwaway
in-character quip, recaps of the previous session, rules chatter, dice-app trouble, scheduling and real-world talk
do not count.

{cast}

Transcript:
{scene}
"""

AUDIT_PROMPT = """You are auditing raw session notes for one scene of a Dungeons & Dragons session against the
transcript of that scene. The notes are terse, lowercase, and hand-written in style on purpose; do not comment on
style, brevity or wording, and do not rewrite lines that are fine. `GM` is the game master and voices NPCs; `DICE`
lines are authoritative rolls.

Lines before `=== SCENE START ===` and after `=== SCENE END ===` are adjacent boundary context ONLY (for pronouns,
ongoing conversations, and NPC names) — only audit beats belonging to the scene between `=== SCENE START ===`
and `=== SCENE END ===`.

Report only clear problems, each with an exact edit:
1. ooc_in_notes: note lines that record out-of-character content: real-world talk, tech or dice-app trouble,
   scheduling, players talking about themselves rather than their characters, rules lookups with no effect, or a
   player's quip about the game recorded as a character's dialogue. In-character dialogue, jokes and banter are
   NOT out-of-character, even if the player comments on them afterwards; an in-character question about the plot is
   NOT out-of-character. If you are not sure, do not flag it.
2. missing_ic: in-game beats the notes leave out that matter for the story: things learned, decisions, rolls and
   their outcomes, NPC statements, changes in someone's situation or role, memorable in-character lines or emotional
   beats. Ignore filler. For each, give 1-3 note lines to add in the same style and the existing note line they
   should follow (or "START").
3. misattributions: a line, action, pronoun/gender, or roll credited to the wrong character, or an NPC line
   credited to a player, with the corrected line.

{kind_rule}

{cast}

{hints}

Return JSON matching the schema:
{{"ooc_in_notes": [{{"note": "<exact note line>", "why": "..."}}],
  "missing_ic": [{{"lines": "<transcript line numbers>", "beat": "<what is missing>", "importance": "high"|"medium",
                   "after_note": "<exact existing note line, or START>", "add": "<note line(s) to insert, newline-separated>"}}],
  "misattributions": [{{"note": "<exact note line>", "fix": "<why>", "replacement": "<corrected note line>"}}]}}

Transcript of the scene (with adjacent boundary context):
{scene}

Notes for the scene:
{notes}
"""

KIND_RULES = {
    "play": "This is a gameplay scene: the notes should cover it fully.",
    "recap": (
        "This scene is the GM's recap of earlier sessions. The notes keep at most 3 short continuity lines in total, "
        "so only add a beat if it is essential continuity and the total stays at 3 lines or fewer."
    ),
}

DICE_TOTAL_RE = re.compile(r":\s*([0-9,\s]+)(?:\s*\(([^)]*)\))?")


def scene_transcript(lines: list[dict], scene: dict, context_lines: int = 10) -> str:
    start_idx = max(0, scene["start"] - 1)
    end_idx = min(len(lines), scene["end"])
    before = lines[max(0, start_idx - context_lines) : start_idx]
    body = lines[start_idx:end_idx]
    after = lines[end_idx : min(len(lines), end_idx + context_lines)]

    parts: list[str] = []
    if before:
        parts.append("=== EARLIER CONTEXT ===")
        parts.append(raw_notes_auto.render(before))
    parts.append("=== SCENE START ===")
    parts.append(raw_notes_auto.render(body))
    parts.append("=== SCENE END ===")
    if after:
        parts.append("=== LATER CONTEXT ===")
        parts.append(raw_notes_auto.render(after))
    return "\n".join(parts)


def find_line(note_lines: list[str], target: str, cutoff: float = 0.88) -> int | None:
    """Index of the note line matching `target` exactly, or very closely."""
    target = (target or "").strip()
    if not target:
        return None
    for i, line in enumerate(note_lines):
        if line.strip() == target:
            return i
    best, best_ratio = None, cutoff
    for i, line in enumerate(note_lines):
        ratio = difflib.SequenceMatcher(None, line.strip().lower(), target.lower()).ratio()
        if ratio > best_ratio:
            best, best_ratio = i, ratio
    return best


def apply_edits(text: str, audit: dict, kind: str) -> tuple[str, list[str]]:
    lines = text.rstrip("\n").splitlines()
    log: list[str] = []
    for item in audit.get("misattributions", []):
        index = find_line(lines, item.get("note", ""))
        if index is not None and item.get("replacement"):
            log.append(f"replaced: {lines[index]} -> {item['replacement']}")
            lines[index] = item["replacement"].strip()
    for item in audit.get("ooc_in_notes", []):
        index = find_line(lines, item.get("note", ""))
        if index is not None:
            log.append(f"removed: {lines[index]}")
            del lines[index]
    for item in audit.get("missing_ic", []):
        if kind == "recap" and sum(1 for l in lines if l.strip()) >= 3:
            continue
        additions = [a.strip() for a in str(item.get("add", "")).splitlines() if a.strip()]
        if not additions:
            continue
        anchor = item.get("after_note", "")
        index = -1 if str(anchor).strip().upper() == "START" else find_line(lines, anchor)
        position = len(lines) if index is None else index + 1
        lines[position:position] = additions
        log.append(
            f"added after {'START' if index == -1 else (anchor[:60] if index is not None else 'END')}: "
            f"{' / '.join(additions)}"
        )
    return "\n".join(lines).strip() + "\n", log


def check_dice_coverage(lines: list[dict], scenes: list[dict], work: Path) -> dict:
    """Deterministically verify that DICE-log roll totals in play scenes appear in scene notes."""
    total_rolls = 0
    covered_rolls = 0
    missing: list[dict] = []

    for index, scene in enumerate(scenes):
        if scene["kind"] != "play":
            continue
        scene_lines = lines[scene["start"] - 1 : scene["end"]]
        dice_lines = [l for l in scene_lines if l["speaker"] == "DICE"]
        if not dice_lines:
            continue
        note_path = work / f"scene_{index + 1:02d}.md"
        note_text = note_path.read_text(encoding="utf-8").lower() if note_path.exists() else ""
        note_nums = set(re.findall(r"\b\d+\b", note_text))
        has_nat20 = bool(re.search(r"\bnat(?:ural)?\s*20\b|\bcrit\b", note_text))
        has_nat1 = bool(re.search(r"\bnat(?:ural)?\s*1\b", note_text))

        for dl in dice_lines:
            total_rolls += 1
            match = DICE_TOTAL_RE.search(dl["text"])
            nums = re.findall(r"\b\d+\b", match.group(1)) if match else re.findall(r"\b\d+\b", dl["text"])
            detail = (match.group(2) if match and match.group(2) else "").lower()
            is_covered = any(num in note_nums for num in nums)
            if not is_covered and ("20" in nums or "nat 20" in detail) and has_nat20:
                is_covered = True
            if not is_covered and ("1" in nums or "nat 1" in detail) and has_nat1:
                is_covered = True
            if is_covered:
                covered_rolls += 1
            else:
                missing.append({
                    "scene": index + 1,
                    "title": scene["title"],
                    "line": dl["n"],
                    "time": dl["time"],
                    "dice_text": dl["text"],
                })

    return {
        "total_play_rolls": total_rolls,
        "covered": covered_rolls,
        "missing": missing,
    }


def _run_audio_verification(
    audits: dict[int, dict],
    scenes: list[dict],
    lines: list[dict],
    work: Path,
    *,
    lines_jsonl: Path | None,
    audio_dir: Path | None,
    audio_model: str,
    names_hint: str,
) -> list[dict]:
    """Optional Gemini 4 Neon high audio check on flagged misattributions & review_queue items."""
    if not shutil.which("agy") or not audio_dir or not audio_dir.exists():
        return []

    jsonl_records: list[dict] = []
    if lines_jsonl and lines_jsonl.exists():
        jsonl_records = [
            json.loads(raw) for raw in lines_jsonl.read_text(encoding="utf-8").splitlines() if raw.strip()
        ]
    audio_by_track: dict[str, Path] = {}
    for p in sorted(audio_dir.iterdir()):
        if p.is_file() and p.suffix.lower() in {".flac", ".wav", ".ogg", ".mp3", ".m4a", ".aac"}:
            audio_by_track[p.name.split(".", 1)[0]] = p

    if not audio_by_track:
        return []

    targets: list[dict] = []
    for idx, audit in audits.items():
        for item in audit.get("misattributions", [])[:3]:
            targets.append({
                "kind": "misattribution",
                "scene": idx + 1,
                "scene_obj": scenes[idx],
                "query": f"Verify attribution for note line: `{item.get('note')}` (audit suggests: `{item.get('replacement')}` — {item.get('fix')})",
                "needle": item.get("note", ""),
            })
    rq_path = work / "review_queue.json"
    if rq_path.exists():
        try:
            rq = json.loads(rq_path.read_text(encoding="utf-8"))
            for item in rq.get("items", [])[:6]:
                sc_idx = max(0, min(len(scenes) - 1, int(item.get("scene", 1)) - 1))
                targets.append({
                    "kind": "review_name",
                    "scene": sc_idx + 1,
                    "scene_obj": scenes[sc_idx],
                    "query": f"Verify uncertain proper noun from raw notes: `{item.get('note')}`",
                    "needle": item.get("note", ""),
                })
        except (OSError, json.JSONDecodeError, ValueError):
            pass

    if not targets:
        return []

    import asr_gemini_windows

    results: list[dict] = []
    for target in targets[:8]:
        sc = target["scene_obj"]
        needle_tokens = set(re.findall(r"[a-z0-9']+", target["needle"].lower()))
        best_rec = None
        best_score = 0
        for rec in jsonl_records[max(0, sc["start"] - 1) : min(len(jsonl_records), sc["end"])]:
            if rec.get("speaker") == "DICE":
                continue
            overlap = len(needle_tokens & set(re.findall(r"[a-z0-9']+", rec.get("text", "").lower())))
            if overlap > best_score and rec.get("track") in audio_by_track:
                best_score = overlap
                best_rec = rec
        if not best_rec:
            continue

        track_file = audio_by_track[best_rec["track"]]
        with tempfile.TemporaryDirectory(prefix="audit-audio-") as tmp:
            clip = asr_gemini_windows.write_block_audio(
                [{"audio": str(track_file), "s": max(0.0, best_rec["start"] - 1.5), "e": best_rec["end"] + 1.5}],
                Path(tmp) / f"verify_{target['scene']}_{best_rec['id']}",
            )
            prompt = (
                f"Audio verification for D&D session notes audit.\n"
                f"Track speaker: {best_rec['speaker']} at [{asr_common.format_ts(best_rec['start'])}].\n"
                f"Transcript line: {best_rec['text']}\n"
                f"Question: {target['query']}\n"
                f"{names_hint}\n"
                "Listen to the attached audio clip and return JSON matching the schema."
            )
            try:
                raw = agent_cli.run_agent(
                    prompt,
                    provider="agy",
                    model=audio_model,
                    workspace=Path(tmp),
                    write=False,
                    attachments=[clip],
                    json_schema=AUDIO_VERIFY_SCHEMA,
                    timeout=300,
                    retries=1,
                )
                verdict = agent_cli.extract_json(raw)
                results.append({
                    "kind": target["kind"],
                    "scene": target["scene"],
                    "line_id": best_rec["id"],
                    "speaker": best_rec["speaker"],
                    "time": asr_common.format_ts(best_rec["start"]),
                    "query": target["query"],
                    **verdict,
                })
            except Exception as exc:  # noqa: BLE001
                results.append({
                    "kind": target["kind"],
                    "scene": target["scene"],
                    "line_id": best_rec["id"],
                    "error": str(exc)[:200],
                })
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--session", required=True)
    parser.add_argument("--transcript", required=True)
    parser.add_argument("--notes", required=True, help="Raw Session N.md written by raw_notes_auto.py")
    parser.add_argument("--work-dir", required=True, help="raw_notes_auto.py work dir")
    parser.add_argument("--report", help="Audit Markdown output (default: <work-dir>/Raw Session N - Audit.md)")
    parser.add_argument("--provider", choices=agent_cli.PROVIDERS, default="codex")
    parser.add_argument("--model")
    parser.add_argument("--ooc-model", help="Optional model override for OOC check (default on agy: gemini-4-neon-low)")
    parser.add_argument("--context-lines", type=int, default=10, help="Boundary context lines before/after each scene")
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--fix", action="store_true", help="Apply the edits and re-assemble the notes")
    parser.add_argument("--allow-partial", action="store_true", help="Exit 0 even if one or more scene audits failed")
    parser.add_argument("--audio-verify", action="store_true", help="Spot-check flagged misattributions / review names against audio with Gemini 4 Neon high")
    parser.add_argument("--lines-jsonl", help="Transcript .lines.jsonl (used by --audio-verify)")
    parser.add_argument("--audio-dir", help="Speaker audio directory (used by --audio-verify)")
    parser.add_argument("--audio-model", default=agent_cli.AGY_TIERS["strong"])
    args = parser.parse_args()

    work = Path(args.work_dir)
    plan_path = work / "scene_plan.json"
    scenes = json.loads(plan_path.read_text(encoding="utf-8"))["scenes"]
    lines = raw_notes_auto.load_lines(Path(args.transcript))
    normalizer = NameNormalizer()
    hints = normalizer.llm_hint_block()

    audit_model = args.model
    if args.provider == "agy" and not audit_model:
        audit_model = agent_cli.AGY_TIERS["strong"]
    ooc_model = args.ooc_model or args.model
    if args.provider == "agy" and not ooc_model:
        ooc_model = agent_cli.AGY_TIERS["fast"]

    def ask(prompt: str, schema: dict, model_choice: str | None) -> dict:
        last_exc: Exception | None = None
        for attempt in range(2):
            try:
                reply = agent_cli.run_agent(
                    prompt,
                    provider=args.provider,
                    model=model_choice,
                    workspace=WORKSPACE,
                    write=False,
                    json_schema=schema,
                    timeout=300,
                    retries=1,
                )
                return raw_notes_auto.parse_json(reply)
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                if attempt == 0:
                    print(f"  audit call retry ({type(exc).__name__}: {str(exc)[:120]})", file=sys.stderr, flush=True)
        return {"error": str(last_exc)[:300]}

    # 1. Skipped scenes: anything in-game hiding in them?
    ooc_ids = [i for i, s in enumerate(scenes) if s["kind"] == "ooc"]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        ooc_checks = dict(
            zip(
                ooc_ids,
                pool.map(
                    lambda i: ask(
                        OOC_CHECK_PROMPT.format(
                            cast=CANONICAL_CAST_REFERENCE,
                            scene=scene_transcript(lines, scenes[i], context_lines=args.context_lines),
                        ),
                        OOC_CHECK_SCHEMA,
                        ooc_model,
                    ),
                    ooc_ids,
                ),
            )
        )
    reclassified = [i for i, result in ooc_checks.items() if result.get("has_game_content")]

    # 2. Audit every scene that has notes.
    def audit_scene(index: int) -> dict:
        notes_path = work / f"scene_{index + 1:02d}.md"
        notes = notes_path.read_text(encoding="utf-8") if notes_path.exists() else "(no notes yet)"
        return ask(
            AUDIT_PROMPT.format(
                scene=scene_transcript(lines, scenes[index], context_lines=args.context_lines),
                notes=notes,
                kind_rule=KIND_RULES.get(scenes[index]["kind"], KIND_RULES["play"]),
                cast=CANONICAL_CAST_REFERENCE,
                hints=hints,
            ),
            AUDIT_SCHEMA,
            audit_model,
        )

    noted = [i for i, s in enumerate(scenes) if s["kind"] != "ooc"]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        audits = dict(zip(noted, pool.map(audit_scene, noted)))

    # 3. Patch existing scenes, generate notes for reclassified ooc->play scenes, and re-audit them!
    applied: dict[int, list[str]] = {}
    if args.fix:
        for i, result in audits.items():
            path = work / f"scene_{i + 1:02d}.md"
            if path.exists() and not result.get("error"):
                patched, log = apply_edits(path.read_text(encoding="utf-8"), result, scenes[i]["kind"])
                if log:
                    path.write_text(patched, encoding="utf-8")
                    applied[i] = log

        if reclassified:
            for i in reclassified:
                scenes[i]["kind"] = "play"
                if "(reclassified from ooc)" not in scenes[i]["title"]:
                    scenes[i]["title"] += " (reclassified from ooc)"
            plan_path.write_text(json.dumps({"scenes": scenes}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        def _reassemble() -> None:
            cmd = [
                sys.executable, "-B", str(SCRIPT_DIR / "raw_notes_auto.py"),
                "--session", str(args.session),
                "--transcript", args.transcript,
                "--out", args.notes,
                "--work-dir", str(work),
                "--provider", args.provider,
            ]
            if args.model:
                cmd += ["--model", args.model]
            subprocess.run(cmd, check=True)

        _reassemble()

        # Re-audit newly generated `ooc -> play` scenes so they meet the same quality bar!
        if reclassified:
            print(f"Re-auditing {len(reclassified)} newly generated reclassified scene(s)...", flush=True)
            with ThreadPoolExecutor(max_workers=args.workers) as pool:
                new_audits = dict(zip(reclassified, pool.map(audit_scene, reclassified)))
            changed_new = False
            for i, result in new_audits.items():
                audits[i] = result
                path = work / f"scene_{i + 1:02d}.md"
                if path.exists() and not result.get("error"):
                    patched, log = apply_edits(path.read_text(encoding="utf-8"), result, scenes[i]["kind"])
                    if log:
                        path.write_text(patched, encoding="utf-8")
                        applied[i] = log
                        changed_new = True
            if changed_new:
                _reassemble()

    # 4. Deterministic DICE-roll coverage check.
    dice_coverage = check_dice_coverage(lines, scenes, work)

    # 5. Optional audio verification on flagged misattributions / review-name items.
    audio_verifications: list[dict] = []
    if args.audio_verify:
        lines_jsonl = Path(args.lines_jsonl) if args.lines_jsonl else Path(args.transcript).with_suffix(".lines.jsonl")
        audio_dir = Path(args.audio_dir).expanduser().resolve() if args.audio_dir else None
        audio_verifications = _run_audio_verification(
            audits,
            scenes,
            lines,
            work,
            lines_jsonl=lines_jsonl,
            audio_dir=audio_dir,
            audio_model=args.audio_model,
            names_hint=hints,
        )

    errors = [
        *(f"ooc_check scene {i + 1}: {v['error']}" for i, v in ooc_checks.items() if v.get("error")),
        *(f"audit scene {i + 1}: {v['error']}" for i, v in audits.items() if v.get("error")),
    ]

    result = {
        "session": args.session,
        "reclassified": reclassified,
        "ooc_checks": {str(k): v for k, v in ooc_checks.items()},
        "audits": {str(k): v for k, v in audits.items()},
        "applied": {str(k): v for k, v in applied.items()},
        "dice_coverage": dice_coverage,
        "audio_verifications": audio_verifications,
        "errors": errors,
    }
    (work / "audit.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    report = Path(args.report) if args.report else work / f"Raw Session {args.session} - Audit.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    edits = sum(len(v) for v in applied.values())
    out = [
        f"# Raw notes audit — Session {args.session}",
        "",
        f"Scenes reclassified from ooc: {[scenes[i]['title'] for i in reclassified] or 'none'}",
        f"Edits applied: {edits}" if args.fix else "Report only (no --fix).",
        f"Audit errors: {len(errors)}",
        f"DICE roll coverage: {dice_coverage['covered']}/{dice_coverage['total_play_rolls']} covered",
        "",
    ]
    if errors:
        out += ["## Errors", ""] + [f"- {err}" for err in errors] + [""]

    for i in sorted(audits):
        a = audits[i]
        out.append(f"## {i + 1}. {scenes[i]['title']}" + (f" — ERROR: {a['error']}" if a.get("error") else ""))
        for item in a.get("ooc_in_notes", []):
            out.append(f"- OOC in notes: {item.get('note')} — {item.get('why')}")
        for item in a.get("misattributions", []):
            out.append(f"- Misattributed: {item.get('note')} — {item.get('fix')}")
        for item in a.get("missing_ic", []):
            out.append(f"- Missing ({item.get('importance')}), lines {item.get('lines')}: {item.get('beat')}")
        for entry in applied.get(i, []):
            out.append(f"  - applied {entry}")
        out.append("")

    if dice_coverage["missing"]:
        out += ["## Missing DICE Roll Coverage", ""]
        for m in dice_coverage["missing"]:
            out.append(f"- Scene {m['scene']} ({m['title']}) line {m['line']} [{m['time']}]: {m['dice_text']}")
        out.append("")

    if audio_verifications:
        out += ["## Audio Verifications (Gemini 4 Neon)", ""]
        for av in audio_verifications:
            if av.get("error"):
                out.append(f"- Scene {av['scene']} {av['line_id']}: ERROR {av['error']}")
            else:
                out.append(
                    f"- Scene {av['scene']} {av['line_id']} [{av['time']}] ({av['kind']}): "
                    f"speaker={av.get('confirmed_speaker')} | heard=`{av.get('verified_text')}` — {av.get('assessment')}"
                )
        out.append("")

    for i, check in ooc_checks.items():
        status = f"ERROR: {check['error']}" if check.get("error") else ("has game content" if check.get("has_game_content") else "ok")
        out.append(f"## (ooc) {scenes[i]['title']} — {status}")
        out += [f"- {e}" for e in check.get("evidence", [])]
        out.append("")

    report.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(
        f"Audit: {len(reclassified)} reclassified, {edits} edits applied, "
        f"{dice_coverage['covered']}/{dice_coverage['total_play_rolls']} dice covered, "
        f"{len(errors)} error(s); report {report}"
    )
    if errors and not args.allow_partial:
        print(f"ERROR: {len(errors)} audit call(s) failed; refusing silent exit 0 (pass --allow-partial to override).", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
