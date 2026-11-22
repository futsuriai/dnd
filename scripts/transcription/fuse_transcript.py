#!/usr/bin/env python3
"""Judge between ASR engines line by line and write the best transcript.

Two-pass multi-engine fusion:
- Pass 1 (overlapping chunks, structured JSON output): an LLM judge reviews the
  primary engine reading, other engine readings (Whisper, Gemini audio), word
  confidence, overlap/bleed flags, and surrounding conversation. It can:
    * `replace` a line with a better / combined / homophone-corrected reading
    * `delete` confirmed mic bleed or ASR hallucination
    * `needs_audio` to escalate genuinely uncertain lines
- Pass 2 (optional audio escalation via Gemini 4 Neon high): when audio tracks
  are available and `agy` is installed, any `needs_audio` lines are batched into
  audio blocks and arbitrated directly from the isolated speaker audio.

Re-running on an already-fused `.lines.jsonl` is idempotent: each run resets
lines to their unfused baseline (`asr_text` / `raw_asr_text`) before applying
fresh edits.
"""

from __future__ import annotations

import argparse
import difflib
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

try:
    import pipeline_paths as _pipeline_paths
except ImportError:
    _pipeline_paths = None

DND_DIR = _pipeline_paths.DND_DIR if _pipeline_paths is not None else SCRIPT_DIR.parent.parent
LABELS = {"gladia": "Gladia", "gemini": "Gemini"}

COMMON_DND_VOCAB = {
    "nat", "natural", "crit", "critical", "dc", "hp", "ac", "gp", "sp", "cp", "pp",
    "sending", "stone", "spell", "slot", "slots", "cantrip", "advantage", "disadvantage",
    "initiative", "saving", "throw", "check", "damage", "healing", "potion", "dagger",
    "sword", "shield", "armor", "stealth", "perception", "insight", "persuasion",
    "deception", "intimidation", "investigation", "arcana", "history", "religion",
    "nature", "survival", "athletics", "acrobatics", "medicine", "performance",
    "sleight", "warforged", "goliath", "goliaths", "smite", "wild", "shape", "turn",
    "bonus", "action", "reaction", "concentration", "grapple", "prone", "blinded",
    "charmed", "frightened", "poisoned", "restrained", "stunned", "unconscious",
    "d4", "d6", "d8", "d10", "d12", "d20", "d100",
}

FUSION_SCHEMA = {
    "type": "object",
    "properties": {
        "edits": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "action": {"type": "string", "enum": ["replace", "delete", "needs_audio"]},
                    "text": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["id", "action"],
            },
        }
    },
    "required": ["edits"],
}

PROMPT = """You are the judge for a speech-recognition transcript of a Dungeons & Dragons session.
Several engines transcribed each player's isolated microphone. For every line you see the primary
engine's text (`{primary}`) and, where available, other engines' independent hearings of the same
audio ({others}). `(same)` means that engine agrees with the primary.
`Gemini [AUDIO-VERIFIED]` means Gemini already listened directly to that speaker's isolated audio clip.
Confidence badges (`conf=...`, `low=[...]`), `overlap=...`, and `possible_bleed` help flag suspect ASR lines.
`GM` is the game master and voices every NPC; players speak both in and out of character.

Lines above `=== JUDGE LINES START ===` are earlier conversation context ONLY — do NOT emit edits for them.

Return JSON matching the schema:
{{"edits": [{{"id": "L00012", "action": "replace"|"delete"|"needs_audio", "text": "corrected line", "reason": "short reason"}}]}}
Only output lines you change, delete, or escalate. If nothing needs changing, return {{"edits": []}}.

How to judge:
- `replace`: choose one engine's reading, combine pieces from several, or fix clear homophones from context:
  "ascending stone" -> "a sending stone", "the story of here" -> "the story of Hýr" (GM pronounces Hýr like "here"),
  "that 20" -> "nat 20", "a Nick's individual" -> "a high net worth individual".
- Gladia boosts campaign names and sometimes inserts one into an ordinary phrase ("Meri Valerian" for
  "Meri will be around", "nites" for "night"). If another engine heard ordinary words there, trust them.
- `delete`: use ONLY for clear mic bleed from another overlapping speaker (`possible_bleed` / `AUDIO: mic_bleed`)
  or obvious ASR hallucination/silence noise where the track speaker did not actually speak.
- `needs_audio`: use sparingly when engines disagree on a critical dice number, unfamiliar proper noun, or
  garbled key plot line AND no `Gemini [AUDIO-VERIFIED]` reading exists yet.
- Never paraphrase, fix grammar or slang, remove profanity, merge or split lines, or polish in-character speech.
  When you cannot tell which reading is right and it is minor, omit the line (keep primary).

Campaign spellings: {names}
{hints}
{cast}

Lines:
{lines}
"""


def load_lines(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def engine_text(line: dict, tracks: dict[str, dict]) -> str | None:
    """Extract another engine's words whose midpoint falls inside this line's span."""
    track = tracks.get(line.get("track"))
    if not track:
        return None
    s = float(line["start"]) - 0.15
    e = float(line["end"]) + 0.15
    words = []
    for w in track.get("words", []):
        ws = float(w["s"])
        we = min(float(w["e"]), ws + 1.5)
        mid = 0.5 * (ws + we)
        if s <= mid <= e:
            words.append(w["w"])
    return " ".join(words)


def fold_tokens(text: str) -> list[str]:
    folded = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower()
    return re.findall(r"[a-z0-9']+", folded)


def _phonetic_skeleton(tokens: list[str]) -> str:
    joined = "".join(t.replace("'", "") for t in tokens)
    joined = joined.replace("ph", "f").replace("ck", "k").replace("qu", "kw")
    joined = re.sub(r"c(?=[eiy])", "s", joined)
    joined = joined.replace("c", "k")
    joined = re.sub(r"(.)\1+", r"\1", joined)
    return joined


def acceptable(
    readings: list[str],
    new: str,
    canonical: set[str],
    extra_allowed: set[str] | None = None,
) -> bool:
    """Accept edits grounded in engine readings, canonical/D&D vocabulary, or close homophones.

    Fixes the over-strict guard that previously rejected legitimate homophone
    corrections such as `"ascending stone" -> "a sending stone"` while still
    blocking fabricated sentences.
    """
    if not new.strip():
        return False
    heard = {t for text in readings for t in fold_tokens(text)}
    new_tokens = fold_tokens(new)
    if not new_tokens:
        return False

    longest = max((len(text) for text in readings), default=0)
    if len(new) > 1.6 * max(longest, 20):
        return False

    allowed = heard | canonical | COMMON_DND_VOCAB | (extra_allowed or set())
    unheard = [t for t in new_tokens if t not in allowed]
    if len(unheard) <= max(1, len(new_tokens) // 10):
        return True

    # Phonetic / concatenated edit-similarity check for homophone splits & merges
    # (e.g., "ascending stone" -> "a sending stone", "that 20" -> "nat 20").
    new_concat = "".join(new_tokens)
    new_skel = _phonetic_skeleton(new_tokens)
    best_sim = 0.0
    for reading in readings:
        r_tokens = fold_tokens(reading)
        if not r_tokens:
            continue
        raw_sim = difflib.SequenceMatcher(None, "".join(r_tokens), new_concat, autojunk=False).ratio()
        skel_sim = difflib.SequenceMatcher(None, _phonetic_skeleton(r_tokens), new_skel, autojunk=False).ratio()
        best_sim = max(best_sim, raw_sim, skel_sim)

    if best_sim >= 0.72 and len(unheard) <= max(3, (len(new_tokens) + 1) // 2):
        return True

    return False


def parse_reply(text: str) -> dict[str, dict]:
    """Parse structured JSON `{"edits": [...]}` or legacy JSONL into `{line_id: edit_obj}`."""
    edits: dict[str, dict] = {}
    cleaned = agent_cli.strip_code_fences(text)
    if not cleaned:
        return edits

    # Try structured JSON object or array first.
    try:
        parsed = agent_cli.extract_json(cleaned)
        items = parsed.get("edits") if isinstance(parsed, dict) else parsed
        if isinstance(items, list):
            for obj in items:
                if not isinstance(obj, dict) or not isinstance(obj.get("id"), str):
                    continue
                action = str(obj.get("action") or "replace").strip().lower()
                if action not in {"replace", "delete", "needs_audio"}:
                    action = "replace"
                edits[obj["id"]] = {
                    "action": action,
                    "text": str(obj.get("text", "")).strip(),
                    "reason": str(obj.get("reason", "")).strip(),
                }
            return edits
    except ValueError:
        pass

    # Fallback: legacy JSONL one object per line.
    for raw in cleaned.splitlines():
        raw = raw.strip().rstrip(",")
        if not raw.startswith("{"):
            continue
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(obj, dict) or not isinstance(obj.get("id"), str):
            continue
        action = str(obj.get("action") or "replace").strip().lower()
        if action not in {"replace", "delete", "needs_audio"}:
            action = "replace"
        if action == "replace" and not isinstance(obj.get("text"), str):
            continue
        edits[obj["id"]] = {
            "action": action,
            "text": str(obj.get("text", "")).strip(),
            "reason": str(obj.get("reason", "")).strip(),
        }
    return edits


def reset_lines_for_fusion(lines: list[dict]) -> None:
    """Make re-running fusion on an already-fused `.lines.jsonl` strictly idempotent."""
    for line in lines:
        baseline = line.setdefault("asr_text", line["text"])
        line.setdefault("raw_asr_text", baseline)
        line["text"] = baseline
        line.pop("other_readings", None)
        line.pop("fusion_action", None)
        line.pop("audio_escalated", None)


def _delete_allowed(line: dict, reason: str) -> bool:
    if line.get("possible_bleed") or line.get("gemini_verdict") in {"mic_bleed", "no_speech"}:
        return True
    if line.get("mean_conf") is not None and line["mean_conf"] < 0.65:
        return True
    readings = line.get("_readings") or {}
    if readings and any(not str(v).strip() for v in readings.values()):
        return True
    lowered = reason.lower()
    if any(k in lowered for k in ("bleed", "hallucinat", "noise", "silence", "duplicate", "echo")):
        return True
    return False


def _context_hint_tokens(normalizer: NameNormalizer) -> set[str]:
    toks: set[str] = set()
    for term, hint in normalizer.context_hints.items():
        toks.update(fold_tokens(term))
        toks.update(fold_tokens(hint))
    for alias, canon in normalizer.aliases.items():
        toks.update(fold_tokens(alias))
        toks.update(fold_tokens(canon))
    return toks


def _find_audio_file(track: str, engines: list[tuple[str, dict[str, dict]]], audio_dir: Path | None) -> str | None:
    for _, tracks in engines:
        data = tracks.get(track)
        if data and data.get("audio_file") and Path(data["audio_file"]).exists():
            return data["audio_file"]
    if audio_dir and audio_dir.exists():
        for ext in (".flac", ".wav", ".ogg", ".mp3", ".m4a", ".aac"):
            cand = audio_dir / f"{track}{ext}"
            if cand.exists():
                return str(cand)
        for p in sorted(audio_dir.iterdir()):
            if p.is_file() and p.name.split(".", 1)[0] == track:
                return str(p)
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("lines_jsonl", help="Assembled .lines.jsonl (transcript .txt is rewritten next to it)")
    parser.add_argument("--alt-dir", action="append", default=[], help="Other engine dnd-asr-v1 dir; repeat for several")
    parser.add_argument("--audio-dir", help="Optional speaker audio dir for Pass 2 `needs_audio` Gemini Neon escalation")
    parser.add_argument("--audio-model", default=agent_cli.AGY_TIERS["strong"], help="agy model for Pass 2 audio escalation")
    parser.add_argument("--no-audio-escalation", action="store_true", help="Do not run Pass 2 audio checks on needs_audio lines")
    parser.add_argument("--primary-label", default="Gladia")
    parser.add_argument("--session")
    parser.add_argument("--provider", choices=agent_cli.PROVIDERS, default="codex")
    parser.add_argument("--model")
    parser.add_argument("--chunk", type=int, default=150)
    parser.add_argument("--chunk-overlap", type=int, default=15, help="Preceding context lines included before each chunk")
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--report", help="Default: '<transcript> - Fusion Report.md' beside the transcript")
    args = parser.parse_args()

    lines_path = Path(args.lines_jsonl)
    txt_path = lines_path.with_name(lines_path.name.replace(".lines.jsonl", ".txt"))
    lines = load_lines(lines_path)
    reset_lines_for_fusion(lines)

    normalizer = NameNormalizer()
    engines: list[tuple[str, dict[str, dict]]] = []
    gemini_verdicts_by_track: dict[str, list[dict]] = {}
    for directory in args.alt_dir:
        dir_path = Path(directory)
        tracks = asr_common.load_engine_dir(dir_path)
        if tracks:
            name = dir_path.name
            label = LABELS.get(name, "Whisper" if name.startswith("whisper") else name)
            engines.append((label, tracks))
            if label == "Gemini":
                vf = dir_path / "verdicts.json"
                if vf.exists():
                    try:
                        vdata = json.loads(vf.read_text(encoding="utf-8"))
                        for v in (vdata.get("verdicts", vdata) if isinstance(vdata, dict) else vdata):
                            if v.get("track"):
                                gemini_verdicts_by_track.setdefault(v["track"], []).append(v)
                    except (OSError, json.JSONDecodeError):
                        pass

    import transcribe_gladia

    module = transcribe_gladia.load_transcribe_module(SCRIPT_DIR)
    vocab = transcribe_gladia.vocabulary_terms_from_metadata(DND_DIR, args.session, module)
    names = ", ".join(vocab[:100])
    canonical = {t for term in vocab for t in fold_tokens(term)}
    extra_allowed = _context_hint_tokens(normalizer)

    for line in lines:
        line["_readings"] = {}
        line["_gemini_audio"] = False
        if line["speaker"] == "DICE":
            continue
        for label, tracks in engines:
            text = engine_text(line, tracks)
            if text is not None:
                cleaned = normalizer.normalize(text) if text.strip() else ""
                if cleaned:
                    line["_readings"][label] = cleaned
                    if label == "Gemini":
                        line["_gemini_audio"] = True
                elif label != "Gemini":
                    # Record empty reading for full engines (Whisper) so bleed/one-sidedness is visible.
                    line["_readings"][label] = ""

        # Attach Gemini negative verdicts if not already present on line.
        if not line.get("gemini_verdict"):
            for v in gemini_verdicts_by_track.get(line.get("track", ""), []):
                if v.get("status") in {"mic_bleed", "no_speech"} and float(v["s"]) <= line["end"] + 0.25 and float(v["e"]) >= line["start"] - 0.25:
                    line["gemini_verdict"] = v["status"]
                    line["possible_bleed"] = True
                    break

    def format_line(line: dict) -> str:
        badges: list[str] = []
        if line.get("mean_conf") is not None:
            badges.append(f"conf={line['mean_conf']:.2f}")
        if line.get("low_conf_words"):
            badges.append("low=[" + ", ".join(line["low_conf_words"][:6]) + "]")
        if line.get("overlap_speakers"):
            badges.append("overlap=" + ",".join(line["overlap_speakers"]))
        if line.get("possible_bleed"):
            badges.append("possible_bleed")
        if line.get("gemini_verdict"):
            badges.append(f"AUDIO:{line['gemini_verdict']}")
        badge_str = f" [{' '.join(badges)}]" if badges else ""
        head = f"{line['id']} [{asr_common.format_ts(line['start'])}] {line['speaker']}{badge_str}:"
        if line["speaker"] == "DICE":
            return f"{head} {line['text']}"

        rows = [f"{head}"]
        primary_line = f"  {args.primary_label}: {line['asr_text']}"
        if line.get("raw_asr_text") and line["raw_asr_text"] != line["asr_text"]:
            primary_line += f"  (pre-norm raw: {line['raw_asr_text']})"
        rows.append(primary_line)
        for label, text in line["_readings"].items():
            if not text:
                rows.append(f"  {label}: (silence)")
                continue
            same = fold_tokens(text) == fold_tokens(line["asr_text"])
            tag = f"{label} [AUDIO-VERIFIED]" if label == "Gemini" else label
            rows.append(f"  {tag}: {'(same)' if same else text}")
        return "\n".join(rows)

    def block_text(context_chunk: list[dict], target_chunk: list[dict]) -> str:
        parts: list[str] = []
        if context_chunk:
            parts.append("(CONTEXT ONLY — do not emit edits for these lines)")
            parts.extend(format_line(l) for l in context_chunk)
        parts.append("=== JUDGE LINES START ===")
        parts.extend(format_line(l) for l in target_chunk)
        return "\n".join(parts)

    others = ", ".join(f"`{label}`" for label, _ in engines) or "none for this session"
    chunk_specs: list[tuple[list[dict], list[dict]]] = []
    for i in range(0, len(lines), args.chunk):
        ctx = lines[max(0, i - args.chunk_overlap) : i]
        target = lines[i : i + args.chunk]
        chunk_specs.append((ctx, target))

    print(
        f"Judging {len(lines)} lines in {len(chunk_specs)} chunks (overlap={args.chunk_overlap}) "
        f"with {args.provider}; readings: {args.primary_label}, {others}",
        flush=True,
    )

    chunk_failures: list[str] = []

    def run_chunk(spec: tuple[list[dict], list[dict]]) -> dict[str, dict]:
        ctx, target = spec
        target_ids = {l["id"] for l in target}
        prompt = PROMPT.format(
            primary=args.primary_label,
            others=others,
            names=names,
            hints=normalizer.llm_hint_block(),
            cast=CANONICAL_CAST_REFERENCE,
            lines=block_text(ctx, target),
        )
        try:
            reply = agent_cli.run_agent(
                prompt,
                provider=args.provider,
                model=args.model,
                workspace=DND_DIR,
                write=False,
                json_schema=FUSION_SCHEMA,
                timeout=300,
                retries=2,
            )
            parsed = parse_reply(reply)
            return {lid: ed for lid, ed in parsed.items() if lid in target_ids}
        except Exception as exc:  # noqa: BLE001 - a failed chunk keeps the primary text after retries
            msg = f"chunk at {target[0]['id']} failed after retries: {str(exc)[:200]}"
            chunk_failures.append(msg)
            print(f"  {msg}", file=sys.stderr, flush=True)
            return {}

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        replies = list(pool.map(run_chunk, chunk_specs))

    by_id = {line["id"]: line for line in lines}
    accepted: list[dict] = []
    deleted: list[tuple[dict, str]] = []
    rejected: list[tuple[dict, str, str]] = []
    escalated_ids: list[tuple[str, str]] = []
    deleted_ids: set[str] = set()

    for edits in replies:
        for line_id, edit in edits.items():
            line = by_id.get(line_id)
            if not line or line["speaker"] == "DICE":
                continue
            action = edit.get("action", "replace")
            reason = edit.get("reason", "")

            if action == "delete":
                if _delete_allowed(line, reason):
                    deleted_ids.add(line_id)
                    deleted.append((line, reason or "bleed/hallucination"))
                else:
                    rejected.append((line, "[DELETE]", f"unjustified delete: {reason}"))
                continue

            if action == "needs_audio":
                escalated_ids.append((line_id, reason or "judge requested audio check"))
                continue

            new = edit.get("text", "").strip()
            if not new or new == line["asr_text"]:
                continue
            new = normalizer.normalize(new)
            if new == line["asr_text"]:
                continue
            readings = [
                r
                for r in (line["asr_text"], line.get("raw_asr_text", ""), *line["_readings"].values())
                if r
            ]
            if acceptable(readings, new, canonical, extra_allowed=extra_allowed):
                line["text"] = new
                line["fusion_action"] = "replace"
                accepted.append(line)
            else:
                rejected.append((line, new, reason or "failed acceptable() guard"))

    # Pass 2: batched Gemini 4 Neon audio escalation for `needs_audio` lines.
    audio_dir = Path(args.audio_dir).expanduser().resolve() if args.audio_dir else None
    audio_resolved: list[tuple[dict, str, str]] = []
    unresolved_needs_audio: list[tuple[dict, str]] = []

    if escalated_ids and not args.no_audio_escalation and shutil.which("agy"):
        import asr_gemini_windows

        pool_for_audio: list[dict] = []
        id_to_pool_idx: dict[str, int] = {}
        for idx, l in enumerate(lines):
            audio_file = _find_audio_file(l.get("track", ""), engines, audio_dir) if l["speaker"] != "DICE" else None
            pool_for_audio.append({
                "idx": idx,
                "s": l["start"],
                "e": l["end"],
                "text": l["asr_text"],
                "alt_text": next((v for k, v in l["_readings"].items() if k != "Gemini" and v), ""),
                "track": l.get("track", ""),
                "speaker": l["speaker"],
                "audio": audio_file or "",
                "origin": "fusion_escalation",
                "reasons": ["needs_audio"],
            })
            id_to_pool_idx[l["id"]] = idx

        audio_segs = []
        for lid, reason in escalated_ids:
            seg = pool_for_audio[id_to_pool_idx[lid]]
            if seg["audio"] and Path(seg["audio"]).exists():
                seg["reasons"] = [f"needs_audio:{reason[:60]}"]
                audio_segs.append(seg)
            else:
                unresolved_needs_audio.append((by_id[lid], f"{reason} (no audio file found)"))

        if audio_segs:
            print(
                f"Pass 2: escalating {len(audio_segs)} lines to audio arbitration ({args.audio_model})...",
                flush=True,
            )
            audio_blocks = asr_gemini_windows.build_blocks(audio_segs, max_segments=12, max_speech=75.0, max_span=600.0)
            verdicts, _ = asr_gemini_windows.arbitrate_blocks(
                audio_blocks,
                pool_for_audio,
                vocab[:100],
                normalizer.llm_hint_block(),
                model=args.audio_model,
                escalation_model=args.audio_model,
                context_lines=3,
                workers=min(args.workers, 3),
                use_cache=False,
            )
            for lid, reason in escalated_ids:
                pidx = id_to_pool_idx[lid]
                if pidx not in verdicts:
                    if not any(l["id"] == lid for l, _ in unresolved_needs_audio):
                        unresolved_needs_audio.append((by_id[lid], f"{reason} (audio check failed)"))
                    continue
                v = verdicts[pidx]
                line = by_id[lid]
                if v["status"] in {"mic_bleed", "no_speech"}:
                    deleted_ids.add(lid)
                    deleted.append((line, f"audio-verified {v['status']}"))
                    audio_resolved.append((line, v["status"], ""))
                elif v["text"]:
                    fixed = normalizer.normalize(v["text"])
                    if fixed != line["asr_text"]:
                        line["text"] = fixed
                        line["fusion_action"] = "audio_escalated"
                        line["audio_escalated"] = True
                        accepted.append(line)
                    audio_resolved.append((line, "speech", fixed))
    else:
        for lid, reason in escalated_ids:
            unresolved_needs_audio.append((by_id[lid], reason))

    for path in (txt_path, lines_path):
        name = path.name
        backup = path.with_name(
            name.replace(".lines.jsonl", " - Unfused.lines.jsonl")
            if name.endswith(".lines.jsonl")
            else name.replace(".txt", " - Unfused.txt")
        )
        if not backup.exists():
            shutil.copy2(path, backup)

    kept_lines = [l for l in lines if l["id"] not in deleted_ids]
    with txt_path.open("w", encoding="utf-8") as txt, lines_path.open("w", encoding="utf-8") as jl:
        for line in kept_lines:
            readings = line.pop("_readings", {})
            line.pop("_gemini_audio", None)
            if line["text"] != line["asr_text"]:
                line["other_readings"] = readings
            txt.write(f"[{asr_common.format_ts(line['start'])}] {line['speaker']}: {line['text']}\n")
            jl.write(json.dumps(line, ensure_ascii=False) + "\n")

    report = Path(args.report) if args.report else txt_path.with_name(txt_path.stem + " - Fusion Report.md")
    out = [
        "# Transcript fusion report",
        "",
        f"Readings: {args.primary_label} (primary), {others}. Judge: {args.provider} ({agent_cli.resolve_model(args.provider, args.model)}).",
        f"Accepted {len(accepted)} edits, deleted {len(deleted)} lines, audio-escalated {len(audio_resolved)}, rejected {len(rejected)}, chunk failures {len(chunk_failures)}.",
        "",
        "## Accepted",
        "",
    ]
    for line in accepted:
        alts = "; ".join(f"{k}: {v}" for k, v in line.get("other_readings", {}).items() if v)
        tag = " [audio-escalated]" if line.get("audio_escalated") else ""
        out.append(
            f"- {line['id']} [{asr_common.format_ts(line['start'])}] {line['speaker']}{tag}: "
            f"~~{line['asr_text']}~~ → **{line['text']}**" + (f"  \n  _{alts}_" if alts else "")
        )
    out += ["", "## Deleted (mic bleed / hallucination)", ""]
    for line, reason in deleted:
        out.append(f"- {line['id']} [{asr_common.format_ts(line['start'])}] {line['speaker']}: ~~{line['asr_text']}~~ — _{reason}_")
    if unresolved_needs_audio:
        out += ["", "## Needs Audio (unresolved)", ""]
        for line, reason in unresolved_needs_audio:
            out.append(f"- {line['id']} [{asr_common.format_ts(line['start'])}] {line['speaker']}: {line['asr_text']} — _{reason}_")
    if chunk_failures:
        out += ["", "## Chunk Failures", ""]
        out.extend(f"- {msg}" for msg in chunk_failures)
    out += ["", "## Rejected", ""]
    out += [f"- {l['id']} {l['speaker']}: {l['asr_text']} ⇏ {new} ({why})" for l, new, why in rejected]
    report.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(
        f"Accepted {len(accepted)} edits, deleted {len(deleted)}, audio-resolved {len(audio_resolved)}, "
        f"rejected {len(rejected)}; report {report}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
