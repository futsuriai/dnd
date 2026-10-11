#!/usr/bin/env python3
"""Judge between ASR engines line by line and write the best transcript.

Text-only and subscription-backed (codex/claude): no audio is sent anywhere.

Every assembled line shows the primary engine's text plus each other engine's
hearing of the same track and time span (e.g. Whisper, and Gemini where it was
asked). An LLM judge reads them with the surrounding conversation and campaign
names, and returns a corrected line wherever the primary is wrong. It may take
the best reading or combine pieces of several (a name from one engine, a number
from another). Everything else stays verbatim.

Edits are applied deterministically by line id. A guard rejects edits that
introduce words no engine heard (the judge may combine, not invent).

Outputs (in place, with backups of the unfused files):
    Transcript Session N.txt / .lines.jsonl   fused text; `asr_text` keeps the primary text
    Transcript Session N - Fusion Report.md   every accepted and rejected edit

Example:
    python fuse_transcript.py "Transcript Session 21.lines.jsonl" --session 21 \
        --alt-dir session-21/asr/whisper-large-v3 --alt-dir session-21/asr/gemini --provider codex
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import agent_cli  # noqa: E402
import asr_common  # noqa: E402
from name_normalizer import NameNormalizer  # noqa: E402
from note_generation_guidance import CANONICAL_CAST_REFERENCE  # noqa: E402

DND_DIR = SCRIPT_DIR.parent.parent
LABELS = {"gladia": "Gladia", "gemini": "Gemini"}

PROMPT = """You are the judge for a speech-recognition transcript of a Dungeons & Dragons session.
Several engines transcribed each player's isolated microphone. For every line you see the primary
engine's text (`{primary}`) and, where available, other engines' independent hearings of the same
audio ({others}). `(same)` means that engine agrees with the primary. `GM` is the game master and voices
every NPC; players speak both in and out of character. Lines before and after give you the conversation.

Return corrections as JSON lines, one object per changed line: {{"id": "L00012", "text": "corrected line"}}
Only output lines whose text you change. If nothing needs changing, output nothing.

How to judge:
- Decide what was actually said using the conversation around the line, the campaign spellings, and
  agreement between engines. Agreement is strong evidence; context and names decide ties.
- You may take one engine's reading or combine pieces from several (e.g. a name one engine got right,
  the rest from another). Prefer words some engine heard.
- All engines sometimes mishear the same sound the same way; fix those from context when the meaning
  is clear: "ascending stone" -> "a sending stone", "the story of here" -> "the story of Hýr" (the GM
  pronounces Hýr like "here"), "that 20" -> "nat 20".
- Gladia boosts campaign names and sometimes inserts one into an ordinary phrase ("Meri Valerian" for
  "Meri will be around", "Aaron, what he saw" for "what he saw"). If the other engines heard ordinary
  words there, trust them.
- Also fix garbled phrases another engine heard cleanly, and dice numbers confirmed by the next lines.
- Never paraphrase, fix grammar or slang, remove profanity, merge or split lines, or polish
  in-character speech. When you cannot tell which reading is right, keep the primary.

Campaign spellings: {names}
{hints}
{cast}

Lines:
{lines}
"""


def load_lines(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def engine_text(line: dict, tracks: dict[str, dict]) -> str | None:
    track = tracks.get(line.get("track"))
    if not track:
        return None
    words = [w["w"] for w in track["words"] if line["start"] - 0.35 <= w["s"] <= line["end"] + 0.2]
    return " ".join(words)


def fold_tokens(text: str) -> list[str]:
    folded = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower()
    return re.findall(r"[a-z0-9']+", folded)


def acceptable(readings: list[str], new: str, canonical: set[str]) -> bool:
    """Accept edits whose words were (nearly all) heard by some engine."""
    if not new.strip():
        return False
    heard = {t for text in readings for t in fold_tokens(text)}
    new_tokens = fold_tokens(new)
    if not new_tokens:
        return False
    unheard = [t for t in new_tokens if t not in heard and t not in canonical]
    longest = max(len(text) for text in readings)
    return len(unheard) <= max(1, len(new_tokens) // 10) and len(new) <= 1.5 * max(longest, 20)


def parse_reply(text: str) -> dict[str, str]:
    edits = {}
    for raw in agent_cli.strip_code_fences(text).splitlines():
        raw = raw.strip().rstrip(",")
        if not raw.startswith("{"):
            continue
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(obj.get("id"), str) and isinstance(obj.get("text"), str):
            edits[obj["id"]] = obj["text"].strip()
    return edits


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("lines_jsonl", help="Assembled .lines.jsonl (transcript .txt is rewritten next to it)")
    parser.add_argument("--alt-dir", action="append", default=[], help="Other engine dnd-asr-v1 dir; repeat for several")
    parser.add_argument("--primary-label", default="Gladia")
    parser.add_argument("--session")
    parser.add_argument("--provider", choices=agent_cli.PROVIDERS, default="codex")
    parser.add_argument("--model")
    parser.add_argument("--chunk", type=int, default=150)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--report", help="Default: '<transcript> - Fusion Report.md' beside the transcript")
    args = parser.parse_args()

    lines_path = Path(args.lines_jsonl)
    txt_path = lines_path.with_name(lines_path.name.replace(".lines.jsonl", ".txt"))
    lines = load_lines(lines_path)
    normalizer = NameNormalizer()
    engines = []
    for directory in args.alt_dir:
        tracks = asr_common.load_engine_dir(Path(directory))
        if tracks:
            name = Path(directory).name
            label = LABELS.get(name, "Whisper" if name.startswith("whisper") else name)
            engines.append((label, tracks))

    import transcribe_gladia

    module = transcribe_gladia.load_transcribe_module(SCRIPT_DIR)
    vocab = transcribe_gladia.vocabulary_terms_from_metadata(DND_DIR, args.session, module)
    names = ", ".join(vocab[:90])
    canonical = {t for term in vocab for t in fold_tokens(term)}

    for line in lines:
        line.setdefault("asr_text", line["text"])
        line["_readings"] = {}
        if line["speaker"] == "DICE":
            continue
        for label, tracks in engines:
            text = engine_text(line, tracks)
            if text is not None and text.strip():
                line["_readings"][label] = normalizer.normalize(text)

    def block(chunk: list[dict]) -> str:
        rows = []
        for line in chunk:
            head = f"{line['id']} [{asr_common.format_ts(line['start'])}] {line['speaker']}:"
            if line["speaker"] == "DICE":
                rows.append(f"{head} {line['text']}")
                continue
            rows.append(f"{head}\n  {args.primary_label}: {line['asr_text']}")
            for label, text in line["_readings"].items():
                same = fold_tokens(text) == fold_tokens(line["asr_text"])
                rows.append(f"  {label}: {'(same)' if same else text}")
        return "\n".join(rows)

    others = ", ".join(f"`{label}`" for label, _ in engines) or "none for this session"
    chunks = [lines[i:i + args.chunk] for i in range(0, len(lines), args.chunk)]
    print(f"Judging {len(lines)} lines in {len(chunks)} chunks with {args.provider}; readings: {args.primary_label}, {others}", flush=True)

    def run(chunk: list[dict]) -> dict[str, str]:
        prompt = PROMPT.format(
            primary=args.primary_label, others=others, names=names,
            hints=normalizer.llm_hint_block(), cast=CANONICAL_CAST_REFERENCE, lines=block(chunk),
        )
        try:
            return parse_reply(agent_cli.run_agent(args.provider, prompt, DND_DIR, args.model))
        except Exception as exc:  # noqa: BLE001 - a failed chunk keeps the primary text
            print(f"  chunk at {chunk[0]['id']} failed: {str(exc)[:200]}", flush=True)
            return {}

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        replies = list(pool.map(run, chunks))

    by_id = {line["id"]: line for line in lines}
    accepted, rejected = [], []
    for edits in replies:
        for line_id, new in edits.items():
            line = by_id.get(line_id)
            if not line or line["speaker"] == "DICE" or new == line["asr_text"]:
                continue
            new = normalizer.normalize(new)
            readings = [line["asr_text"], *line["_readings"].values()]
            if acceptable(readings, new, canonical):
                line["text"] = new
                accepted.append(line)
            else:
                rejected.append((line, new))

    for path in (txt_path, lines_path):
        name = path.name
        backup = path.with_name(
            name.replace(".lines.jsonl", " - Unfused.lines.jsonl") if name.endswith(".lines.jsonl") else name.replace(".txt", " - Unfused.txt")
        )
        if not backup.exists():
            shutil.copy2(path, backup)
    with txt_path.open("w", encoding="utf-8") as txt, lines_path.open("w", encoding="utf-8") as jl:
        for line in lines:
            readings = line.pop("_readings", {})
            if line["text"] != line["asr_text"]:
                line["other_readings"] = readings
            txt.write(f"[{asr_common.format_ts(line['start'])}] {line['speaker']}: {line['text']}\n")
            jl.write(json.dumps(line, ensure_ascii=False) + "\n")

    report = Path(args.report) if args.report else txt_path.with_name(txt_path.stem + " - Fusion Report.md")
    out = ["# Transcript fusion report", "",
           f"Readings: {args.primary_label} (primary), {others}. Judge: {args.provider}.",
           f"Accepted {len(accepted)} edits, rejected {len(rejected)} (guard: nearly every word must have been heard by some engine).", "",
           "## Accepted", ""]
    for line in accepted:
        alts = "; ".join(f"{k}: {v}" for k, v in line.get("other_readings", {}).items())
        out.append(f"- {line['id']} [{asr_common.format_ts(line['start'])}] {line['speaker']}: ~~{line['asr_text']}~~ → **{line['text']}**" + (f"  \n  _{alts}_" if alts else ""))
    out += ["", "## Rejected", ""]
    out += [f"- {l['id']} {l['speaker']}: {l['asr_text']} ⇏ {new}" for l, new in rejected]
    report.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"Accepted {len(accepted)} edits, rejected {len(rejected)}; report {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
