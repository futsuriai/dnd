#!/usr/bin/env python3
"""Audit scene-based raw notes against the transcript and patch them in place.

Runs after raw_notes_auto.py, using its work dir (scene_plan.json, scene_XX.md).

1. Every `ooc` scene the planner skipped is checked for real game content
   (in-character dialogue, GM narration, rolls, decisions). Scenes that have
   some are reclassified as `play`; with --fix they get notes written.
2. Every play/recap scene is audited by an LLM against its transcript for
   out-of-character content that leaked into the notes, in-game beats that are
   missing, and wrong attributions. The audit returns exact edits.
3. With --fix the edits are applied surgically: leaked lines are deleted,
   misattributed lines replaced, missing beats inserted after the note line the
   audit names. Nothing else in the scene changes (no regeneration churn).

Writes <work-dir>/audit.json and '<Raw Session N> - Audit.md' beside the notes.

Example:
    python audit_raw_notes.py --session 21 --transcript ".../Transcript Session 21.txt" \
        --notes ".../Raw Session 21.md" --work-dir ".../pipeline/raw_notes" --provider codex --fix
"""

from __future__ import annotations

import argparse
import difflib
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import agent_cli  # noqa: E402
import raw_notes_auto  # noqa: E402

WORKSPACE = SCRIPT_DIR.parent.parent

OOC_CHECK_PROMPT = """This stretch of a Dungeons & Dragons session transcript was classified as out-of-character
(setup, tech, breaks, real-world chatter) and will be left out of the session notes. Check whether that is right.
`GM` is the game master and voices NPCs; `DICE` lines are rolls.

Return JSON only: {{"has_game_content": true|false, "evidence": ["<line number>: <why it is game content>", ...]}}
Answer true only if it contains a substantive game beat: in-character dialogue that matters, GM narration or NPC
speech, a roll with an outcome, a ruling that changes what happens, or a party decision. A single throwaway
in-character quip, recaps of the previous session, rules chatter, dice-app trouble, scheduling and real-world talk
do not count.

Transcript:
{scene}
"""

AUDIT_PROMPT = """You are auditing raw session notes for one scene of a Dungeons & Dragons session against the
transcript of that scene. The notes are terse, lowercase, and hand-written in style on purpose; do not comment on
style, brevity or wording, and do not rewrite lines that are fine. `GM` is the game master and voices NPCs; `DICE`
lines are authoritative rolls.

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
3. misattributions: a line, action or roll credited to the wrong character, or an NPC line credited to a player,
   with the corrected line.

{kind_rule}

Return JSON only:
{{"ooc_in_notes": [{{"note": "<exact note line>", "why": "..."}}],
  "missing_ic": [{{"lines": "<transcript line numbers>", "beat": "<what is missing>", "importance": "high"|"medium",
                   "after_note": "<exact existing note line, or START>", "add": "<note line(s) to insert, newline-separated>"}}],
  "misattributions": [{{"note": "<exact note line>", "fix": "<why>", "replacement": "<corrected note line>"}}]}}

Transcript of the scene:
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


def scene_transcript(lines: list[dict], scene: dict) -> str:
    return raw_notes_auto.render(lines[scene["start"] - 1: scene["end"]])


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
        log.append(f"added after {'START' if index == -1 else (anchor[:60] if index is not None else 'END')}: {' / '.join(additions)}")
    return "\n".join(lines).strip() + "\n", log


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--session", required=True)
    parser.add_argument("--transcript", required=True)
    parser.add_argument("--notes", required=True, help="Raw Session N.md written by raw_notes_auto.py")
    parser.add_argument("--work-dir", required=True, help="raw_notes_auto.py work dir")
    parser.add_argument("--provider", choices=agent_cli.PROVIDERS, default="codex")
    parser.add_argument("--model")
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--fix", action="store_true", help="Apply the edits and re-assemble the notes")
    args = parser.parse_args()

    work = Path(args.work_dir)
    plan_path = work / "scene_plan.json"
    scenes = json.loads(plan_path.read_text(encoding="utf-8"))["scenes"]
    lines = raw_notes_auto.load_lines(Path(args.transcript))

    def ask(prompt: str) -> dict:
        try:
            return raw_notes_auto.parse_json(agent_cli.run_agent(args.provider, prompt, WORKSPACE, args.model))
        except Exception as exc:  # noqa: BLE001 - an unreadable audit is treated as "no findings"
            return {"error": str(exc)[:300]}

    # 1. Skipped scenes: anything in-game hiding in them?
    ooc_ids = [i for i, s in enumerate(scenes) if s["kind"] == "ooc"]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        ooc_checks = dict(zip(ooc_ids, pool.map(lambda i: ask(OOC_CHECK_PROMPT.format(scene=scene_transcript(lines, scenes[i]))), ooc_ids)))
    reclassified = [i for i, result in ooc_checks.items() if result.get("has_game_content")]

    # 2. Audit every scene that has notes.
    def audit(index: int) -> dict:
        notes_path = work / f"scene_{index + 1:02d}.md"
        notes = notes_path.read_text(encoding="utf-8") if notes_path.exists() else "(no notes yet)"
        return ask(AUDIT_PROMPT.format(
            scene=scene_transcript(lines, scenes[index]), notes=notes,
            kind_rule=KIND_RULES.get(scenes[index]["kind"], KIND_RULES["play"]),
        ))

    noted = [i for i, s in enumerate(scenes) if s["kind"] != "ooc"]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        audits = dict(zip(noted, pool.map(audit, noted)))

    # 3. Patch.
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
                scenes[i]["title"] += " (reclassified from ooc)"
            plan_path.write_text(json.dumps({"scenes": scenes}, indent=2) + "\n", encoding="utf-8")
        # Re-assemble; raw_notes_auto only writes scenes that have no file yet (the reclassified ones).
        cmd = [sys.executable, str(SCRIPT_DIR / "raw_notes_auto.py"), "--session", args.session,
               "--transcript", args.transcript, "--out", args.notes, "--work-dir", str(work), "--provider", args.provider]
        if args.model:
            cmd += ["--model", args.model]
        subprocess.run(cmd, check=True)

    result = {
        "reclassified": reclassified,
        "ooc_checks": {str(k): v for k, v in ooc_checks.items()},
        "audits": {str(k): v for k, v in audits.items()},
        "applied": {str(k): v for k, v in applied.items()},
    }
    (work / "audit.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    notes_path = Path(args.notes)
    report = notes_path.with_name(notes_path.stem + " - Audit.md")
    edits = sum(len(v) for v in applied.values())
    out = [f"# Raw notes audit — Session {args.session}", "",
           f"Scenes reclassified from ooc: {[scenes[i]['title'] for i in reclassified] or 'none'}",
           f"Edits applied: {edits}" if args.fix else "Report only (no --fix).", ""]
    for i, a in audits.items():
        out.append(f"## {i + 1}. {scenes[i]['title']}" + (f" — error: {a['error']}" if a.get("error") else ""))
        for item in a.get("ooc_in_notes", []):
            out.append(f"- OOC in notes: {item.get('note')} — {item.get('why')}")
        for item in a.get("misattributions", []):
            out.append(f"- Misattributed: {item.get('note')} — {item.get('fix')}")
        for item in a.get("missing_ic", []):
            out.append(f"- Missing ({item.get('importance')}), lines {item.get('lines')}: {item.get('beat')}")
        for entry in applied.get(i, []):
            out.append(f"  - applied {entry}")
        out.append("")
    for i, check in ooc_checks.items():
        out.append(f"## (ooc) {scenes[i]['title']} — {'has game content' if check.get('has_game_content') else 'ok'}")
        out += [f"- {e}" for e in check.get("evidence", [])]
        out.append("")
    report.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"Audit: {len(reclassified)} reclassified, {edits} edits applied; report {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
