#!/usr/bin/env python3
"""Generate Raw Session N notes from a transcript, scene by scene, unattended.

Replaces fixed 100-line chunks + a reconcile pass with:
1. one structured planning call (`--json-schema`, defaulting to
   `gemini-4-neon-high` on `agy`) that splits the transcript into scenes
   (`play` / `recap` / `ooc`) with a one-line summary each
2. one extraction call per play/recap scene (run in parallel) that sees the
   whole session outline, the scene's transcript, D&D Beyond dice lines, and
   real examples of the player's hand-written notes; uncertain proper nouns
   emitted as `review-name:` are routed into `<work-dir>/review_queue.json`
3. deterministic `NameNormalizer` cleanup and assembly with `---` between scenes

Work files (plan + per-scene notes + review_queue.json) are kept in --work-dir
so reruns only redo missing scenes (use --force to redo everything).

Example:
    python3 -B scripts/transcription/raw_notes_auto.py --session 21 \
        --transcript "<ellara>/Session Notes/Transcripts/Transcript Session 21.txt" \
        --out "<ellara>/Session Notes/Raw Session 21.md" --provider agy
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import agent_cli  # noqa: E402
from name_normalizer import NameNormalizer  # noqa: E402
from note_generation_guidance import CANONICAL_CAST_REFERENCE, CANONICAL_EVIDENCE_POLICY  # noqa: E402

try:
    import pipeline_paths as _pipeline_paths
except ImportError:
    _pipeline_paths = None

LINE_RE = re.compile(r"^\[(\d{2}:\d{2}:\d{2}(?:\.\d+)?)\] ([^:]+): (.*)$")
REVIEW_LINE_RE = re.compile(r"^\s*review(?:-name)?\s*:(.*)$", re.IGNORECASE)
EXAMPLES_PATH = SCRIPT_DIR / "examples" / "raw_notes_examples.md"
EXAMPLES = EXAMPLES_PATH.read_text(encoding="utf-8") if EXAMPLES_PATH.exists() else ""
WORKSPACE = _pipeline_paths.DND_DIR if _pipeline_paths is not None else SCRIPT_DIR.parent.parent

SCENE_PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "scenes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "start": {"type": "integer"},
                    "end": {"type": "integer"},
                    "kind": {"type": "string", "enum": ["play", "recap", "ooc"]},
                    "title": {"type": "string"},
                    "summary": {"type": "string"},
                },
                "required": ["start", "end", "kind", "title", "summary"],
            },
        }
    },
    "required": ["scenes"],
}

PLAN_PROMPT = """You are planning notes for a Dungeons & Dragons session. Below is the full machine transcript,
one numbered line per speaker turn: `<n> [time] Speaker: text`. `GM` is the game master, who also voices every NPC.
`DICE` lines are rolls from the D&D Beyond game log.

Split the transcript into consecutive scenes and return JSON matching the schema, no prose:
{{"scenes": [{{"start": <first line number>, "end": <last line number>, "kind": "play" | "recap" | "ooc",
  "title": "<short scene title>", "summary": "<1-2 sentences: who does what, what is learned or decided>"}}]}}

Rules:
- Cover every line from 1 to {last} exactly once, in order, with no gaps or overlaps.
- A scene is one continuous situation: a location, encounter, conversation, or travel leg. Usually 40-350 lines.
- kind "ooc": pre-game setup, tech/scheduling, breaks and real-world chatter with no game content.
- kind "recap": the GM's recap of earlier sessions near the start.
- Everything with game content is "play", even if table talk is mixed in.
- Summaries use character names, not player names; Berridin is also called Din.

Transcript:
{transcript}
"""

SCENE_PROMPT = """You are writing the raw session notes for one scene of a Dungeons & Dragons session, the way the
player who used to take these notes by hand wrote them. These raw notes feed a later polishing step and the campaign
website, so they must capture what happened, who said what, rolls and outcomes, and anything learned, in the
player's terse style. They are not a recap and not a cleaned transcript.

How the hand-written notes look (follow this closely):
- all lowercase, terse, chronological; short sentences and fragments are fine; no headings, bullets, or bold
- dialogue as `name: what they said`, shortened but in the speaker's own words and voice; keep jokes and banter
  that are in character; NPCs by name or role (`meri:`, `teller:`, `guard:`); the GM voicing an NPC is that NPC
- GM narration becomes plain description: `ornate building, all made of stone. guards at the door, at least 2.`
- actions and intentions as plain lines: `witty tells din to come with him and asks for a disguise.`
- rolls inline with the roller, value, and what it meant: `stealth roll nyx 27, he goes in quietly.`
  `insight 12: eduard is not hiding anything.` `con save dc 15. nat 20.`
- DICE lines come from the D&D Beyond log and are authoritative for who rolled what and the total; spoken
  numbers that conflict with a DICE line lose. If a roll matters but the roller is unclear, write it without a name.
- rulings, retcons and rules lookups only when they change what happens, as a short parenthetical:
  `(retcon: witty made a bag of holding during the trip)`
- drop out-of-character chatter, tech trouble, scheduling, real-world jokes, and dice-app fumbling
- compress repeated planning to the options considered and the choice made
- canonical spellings for names; the transcript's speaker labels are reliable, but ASR mishears names in the text
- never invent facts, quotes, or outcomes; if something is unclear, leave it out rather than guess; never write
  notes to the reader or meta-commentary about the transcript
- uncertain proper nouns: if a heard/transcribed proper noun is genuinely ambiguous, keep the safest descriptive form
  in the note prose and add a separate trailing `review-name: <heard> | <candidates or context>` line at the very end;
  the pipeline automatically extracts `review-name:` lines into a sidecar `review_queue.json` so they never appear in
  the final raw notes file
- density: dialogue-heavy scenes keep most exchanges; logistics and long rules discussions become one line

{examples}

{cast}

{evidence}

{hints}

Whole-session outline (for context; write notes only for the CURRENT scene):
{outline}

{kind_instruction}

Transcript of the current scene (lines before `=== SCENE START ===` are earlier context only):
{scene}

Write only the raw notes for the current scene (plus any trailing `review-name:` lines if a proper noun is ambiguous)."""

KIND_INSTRUCTIONS = {
    "play": "The current scene is gameplay: write full raw notes for it.",
    "recap": (
        "The current scene is the GM's recap of earlier sessions. Write at most 3 short lines with only the "
        "continuity needed to understand this session (where the party is, what they are about to do). "
        "If nothing is needed, write nothing."
    ),
}


def load_lines(path: Path) -> list[dict]:
    lines = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        match = LINE_RE.match(raw.strip())
        if match:
            lines.append({"n": len(lines) + 1, "time": match.group(1), "speaker": match.group(2), "text": match.group(3)})
    return lines


def render(lines: list[dict]) -> str:
    return "\n".join(f"{l['n']} [{l['time']}] {l['speaker']}: {l['text']}" for l in lines)


def parse_json(text: str) -> dict:
    parsed = agent_cli.extract_json(text)
    if not isinstance(parsed, dict):
        raise ValueError(f"expected JSON object, got {type(parsed).__name__}")
    return parsed


def split_review_lines(text: str) -> tuple[str, list[str]]:
    """Separate clean scene notes from `review:` / `review-name:` sidecar entries."""
    note_lines: list[str] = []
    review_items: list[str] = []
    for raw in text.splitlines():
        stripped = raw.lstrip()
        if stripped.startswith("#"):
            continue
        review_match = REVIEW_LINE_RE.match(raw)
        if review_match:
            item = review_match.group(1).strip()
            if item:
                review_items.append(item)
            continue
        note_lines.append(raw)
    return "\n".join(note_lines).strip(), review_items


def to_seconds(stamp: str) -> float:
    h, m, s = stamp.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def repair_plan(scenes: list[dict], total: int, lines: list[dict], max_lines: int) -> list[dict]:
    """Make scenes contiguous and bounded no matter what the planner returned."""
    cleaned = []
    for scene in sorted(scenes, key=lambda s: int(s.get("start", 0))):
        start, end = int(scene.get("start", 0)), int(scene.get("end", 0))
        if end < start or start < 1:
            continue
        kind = scene.get("kind") if scene.get("kind") in {"play", "recap", "ooc"} else "play"
        cleaned.append({
            "start": start,
            "end": min(end, total),
            "kind": kind,
            "title": str(scene.get("title", "")).strip(),
            "summary": str(scene.get("summary", "")).strip(),
        })
    if not cleaned:
        cleaned = [{"start": 1, "end": total, "kind": "play", "title": "Session", "summary": ""}]
    cleaned[0]["start"] = 1
    for prev, nxt in zip(cleaned, cleaned[1:]):
        nxt["start"] = prev["end"] + 1 if nxt["start"] != prev["end"] + 1 else nxt["start"]
        if nxt["start"] > nxt["end"]:
            nxt["end"] = nxt["start"]
    cleaned[-1]["end"] = total
    cleaned = [s for s in cleaned if s["start"] <= s["end"]]

    bounded = []
    for scene in cleaned:
        pending = [scene]
        while pending:
            current = pending.pop(0)
            size = current["end"] - current["start"] + 1
            if size <= max_lines:
                bounded.append(current)
                continue
            lo, hi = current["start"] + size // 3, current["end"] - size // 3
            cut = max(
                range(lo, max(lo + 1, hi)),
                key=lambda n: to_seconds(lines[min(n, total - 1)]["time"]) - to_seconds(lines[max(0, n - 1)]["time"]),
            )
            pending[:0] = [
                {**current, "end": cut},
                {**current, "start": cut + 1, "title": current["title"] + " (cont.)"},
            ]
    return bounded


def outline_text(scenes: list[dict], current: int | None) -> str:
    rows = []
    for i, scene in enumerate(scenes):
        marker = ">> CURRENT" if i == current else "  "
        rows.append(f"{marker} {i + 1}. [{scene['kind']}] {scene['title']}: {scene['summary']}")
    return "\n".join(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--session", required=True)
    parser.add_argument("--transcript", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--work-dir", help="Default: <out dir>/Raw Session N Work")
    parser.add_argument("--provider", choices=agent_cli.PROVIDERS, default="codex")
    parser.add_argument("--model")
    parser.add_argument("--plan-provider", choices=agent_cli.PROVIDERS, help="Default: --provider")
    parser.add_argument("--plan-model", help="Default: --model (or gemini-4-neon-high when planning with agy)")
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--context-lines", type=int, default=10)
    parser.add_argument("--max-scene-lines", type=int, default=400)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    transcript = Path(args.transcript)
    out = Path(args.out)
    work = Path(args.work_dir) if args.work_dir else out.parent / f"Raw Session {args.session} Work"
    work.mkdir(parents=True, exist_ok=True)
    lines = load_lines(transcript)
    if not lines:
        raise SystemExit(f"no transcript lines in {transcript}")

    plan_provider = args.plan_provider or args.provider
    plan_model = args.plan_model or args.model
    if plan_provider == "agy" and not plan_model:
        plan_model = agent_cli.AGY_TIERS["strong"]

    plan_path = work / "scene_plan.json"
    if plan_path.exists() and not args.force:
        scenes = json.loads(plan_path.read_text(encoding="utf-8"))["scenes"]
    else:
        print(
            f"Planning scenes over {len(lines)} lines with {plan_provider} "
            f"({agent_cli.resolve_model(plan_provider, plan_model)})...",
            flush=True,
        )
        plan_prompt = PLAN_PROMPT.format(last=len(lines), transcript=render(lines))
        planned: list[dict] = []
        fallback_reason: str | None = None
        last_reply = ""

        for attempt in range(2):
            try:
                last_reply = agent_cli.run_agent(
                    plan_prompt,
                    provider=plan_provider,
                    model=plan_model,
                    workspace=WORKSPACE,
                    write=False,
                    json_schema=SCENE_PLAN_SCHEMA,
                    timeout=360,
                    retries=1,
                )
                parsed = parse_json(last_reply)
                candidate = parsed.get("scenes", [])
                if isinstance(candidate, list) and candidate:
                    planned = candidate
                    fallback_reason = None
                    break
                fallback_reason = "planner returned empty scenes list"
            except Exception as exc:  # noqa: BLE001
                fallback_reason = f"{type(exc).__name__}: {exc}"
            if attempt == 0:
                print(
                    f"WARNING: scene planner attempt 1 failed ({fallback_reason}); retrying once...",
                    file=sys.stderr,
                    flush=True,
                )

        if not planned:
            raw_dump = work / "scene_plan_raw.txt"
            raw_dump.write_text(last_reply + "\n", encoding="utf-8")
            print(
                f"WARNING: scene planner fell back to timestamp-gap scenes ({fallback_reason}). "
                f"Raw output saved to {raw_dump}",
                file=sys.stderr,
                flush=True,
            )

        scenes = repair_plan(planned, len(lines), lines, args.max_scene_lines)
        plan_payload: dict = {"scenes": scenes, "fallback": bool(fallback_reason)}
        if fallback_reason:
            plan_payload["fallback_reason"] = fallback_reason
        plan_path.write_text(json.dumps(plan_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"{len(scenes)} scenes: " + ", ".join(f"{s['kind']}:{s['end'] - s['start'] + 1}" for s in scenes), flush=True)

    normalizer = NameNormalizer()
    hints = normalizer.llm_hint_block()
    review_queue_path = work / "review_queue.json"
    existing_queue: dict[int, list[dict]] = {}
    if review_queue_path.exists() and not args.force:
        try:
            prev_q = json.loads(review_queue_path.read_text(encoding="utf-8"))
            for item in prev_q.get("items", []):
                existing_queue.setdefault(int(item.get("scene", 0)), []).append(item)
        except (OSError, json.JSONDecodeError, ValueError):
            pass

    scene_reviews: dict[int, list[dict]] = dict(existing_queue)

    def run_scene(index: int) -> None:
        scene = scenes[index]
        target = work / f"scene_{index + 1:02d}.md"
        if scene["kind"] == "ooc" or (target.exists() and not args.force):
            return
        before = lines[max(0, scene["start"] - 1 - args.context_lines) : scene["start"] - 1]
        body = lines[scene["start"] - 1 : scene["end"]]
        scene_text = (render(before) + "\n" if before else "") + "=== SCENE START ===\n" + render(body)
        prompt = SCENE_PROMPT.format(
            examples=EXAMPLES,
            cast=CANONICAL_CAST_REFERENCE,
            evidence=CANONICAL_EVIDENCE_POLICY,
            hints=hints,
            outline=outline_text(scenes, index),
            kind_instruction=KIND_INSTRUCTIONS[scene["kind"]],
            scene=scene_text,
        )
        raw_reply = agent_cli.strip_code_fences(
            agent_cli.run_agent(
                prompt,
                provider=args.provider,
                model=args.model,
                workspace=WORKSPACE,
                write=False,
                timeout=300,
                retries=2,
            )
        )
        clean_reply, review_items = split_review_lines(raw_reply)
        normalized_reply = normalizer.normalize(clean_reply, preserve_lowercase=True)
        target.write_text((normalized_reply.strip() + "\n") if normalized_reply.strip() else "", encoding="utf-8")

        if review_items:
            scene_reviews[index + 1] = [
                {
                    "scene": index + 1,
                    "title": scene["title"],
                    "start_line": scene["start"],
                    "end_line": scene["end"],
                    "start_time": lines[scene["start"] - 1]["time"],
                    "end_time": lines[scene["end"] - 1]["time"],
                    "note": item,
                }
                for item in review_items
            ]
        else:
            scene_reviews.pop(index + 1, None)

        print(
            f"  scene {index + 1}/{len(scenes)} ({scene['title']}): "
            f"{len(normalized_reply.splitlines())} lines"
            + (f" (+{len(review_items)} review-name queued)" if review_items else ""),
            flush=True,
        )

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(run_scene, range(len(scenes))))

    flat_reviews = [item for idx in sorted(scene_reviews) for item in scene_reviews[idx]]
    review_queue_path.write_text(
        json.dumps({"session": args.session, "items": flat_reviews}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    parts = []
    for index, scene in enumerate(scenes):
        path = work / f"scene_{index + 1:02d}.md"
        if scene["kind"] != "ooc" and path.exists():
            text = path.read_text(encoding="utf-8").strip()
            if text:
                parts.append(text)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n\n---\n\n".join(parts) + "\n", encoding="utf-8")
    print(
        f"Wrote {out} ({sum(len(p.splitlines()) for p in parts)} lines from {len(parts)} scenes; "
        f"{len(flat_reviews)} review-name item(s) -> {review_queue_path})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
