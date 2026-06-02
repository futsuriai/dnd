#!/usr/bin/env python3
"""
Annotation-first OOC cleanup for timestamped D&D transcripts.

Workflow:
  1. prepare: split transcript into editable chunks with context overlap
  2. prompt: print the annotation prompt for one chunk or as a template
  3. apply: validate chunk_XX_annotations.jsonl and rebuild outputs

The LLM never rewrites the full transcript. It emits structured actions for
editable lines, then this script deterministically builds an audit-friendly
cleaned transcript plus review reports and diffs. Raw-note extraction is a
separate stage.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
from pathlib import Path


RECOMMENDED_MODEL = "gpt-5.2-codex"

ENTRY_RE = re.compile(r"^\[\d{2}:\d{2}:\d{2}\]\s+[^:]+:\s+")
FULL_ENTRY_RE = re.compile(r"^\[(?P<timestamp>\d{2}:\d{2}:\d{2})\]\s+(?P<speaker>[^:]+):\s*(?P<text>.*)$")

ALLOWED_ACTIONS = {"KEEP", "REMOVE", "TRIM", "REVIEW"}
ALLOWED_CATEGORIES = {
    "IC_DIALOGUE",
    "GM_NARRATION",
    "SCENE_DESCRIPTION",
    "CHARACTER_THOUGHT",
    "PLAYER_INTENT",
    "TACTICS",
    "RULES_OR_ROLL",
    "RESOURCE_STATE",
    "LORE_OR_CONTINUITY",
    "RECAP_CONTINUITY",
    "RECAP_REDUNDANT",
    "OOC_TECH",
    "OOC_LOGISTICS",
    "OOC_SOCIAL",
    "OOC_TANGENT",
    "MIXED",
    "UNCERTAIN",
}
ALLOWED_IMPORTANCE = {"HIGH", "MEDIUM", "LOW", "NONE"}
ANNOTATION_PROMPT_TEMPLATE = """\
You are cleaning a D&D session transcript before raw-note extraction.

Your output is not the final notes. Your job is only to remove or trim true
out-of-game chatter while preserving campaign-relevant transcript evidence for
the next stage.

The input contains transcript lines with stable IDs:
`L000001 | EDITABLE | [HH:MM:SS] Speaker: text`

Use CONTEXT_BEFORE and CONTEXT_AFTER to understand the scene, but emit records
only for EDITABLE lines.

For every EDITABLE line, output exactly one JSON object on its own line.
No markdown, no code fence, no commentary.

Schema:
{
  "line_id": "L000001",
  "action": "KEEP | REMOVE | TRIM | REVIEW",
  "category": "IC_DIALOGUE | GM_NARRATION | SCENE_DESCRIPTION | CHARACTER_THOUGHT | PLAYER_INTENT | TACTICS | RULES_OR_ROLL | RESOURCE_STATE | LORE_OR_CONTINUITY | RECAP_CONTINUITY | RECAP_REDUNDANT | OOC_TECH | OOC_LOGISTICS | OOC_SOCIAL | OOC_TANGENT | MIXED | UNCERTAIN",
  "importance": "HIGH | MEDIUM | LOW | NONE",
  "replacement": null,
  "reason": "short reason"
}

Action policy:
- KEEP: GM narration, NPC speech, IC dialogue, player intent, planning that
  changes action, relevant rules/roll/resource state, discoveries, lore, and
  table clarification that affects continuity.
- REMOVE: recording setup, mic/audio/Discord/Teams/controller chatter,
  camera/screen/pet/food/work/scheduling chatter, post-session wrap, unrelated
  real-world tangents, and redundant recap chatter.
- TRIM: mixed line with useful campaign content plus unrelated OOC. `replacement`
  must be only the post-colon text, without timestamp or speaker.
- REVIEW: keep in output but flag when context is insufficient or removal could
  lose continuity.

Session recap is not automatically gameplay. Remove recap intros, recap jokes,
and prior-session summaries unless they add a concrete continuity fact needed
for this session and not otherwise present in the editable/context window. Mark
those rare kept recap facts as RECAP_CONTINUITY.

TRIM constraints:
- Do not invent content.
- Do not improve style unless needed to remove OOC.
- Do not resolve uncertainty or make implied intent explicit.
- For `replacement`, provide only the transcript text after `Speaker:`.
  The script preserves timestamp and speaker.

When in doubt, use REVIEW.

=== CONTEXT BEFORE ===
{context_before}
=== EDITABLE LINES ===
{editable_lines}
=== CONTEXT AFTER ===
{context_after}
=== END CHUNK ===

Output JSONL records now:"""


def parse_entries(text: str) -> list[str]:
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    if lines and sum(1 for line in lines if ENTRY_RE.match(line)) >= max(1, len(lines) // 2):
        return lines
    return [entry.strip() for entry in re.split(r"\n\n+", text.strip()) if entry.strip()]


def make_line_id(line_number: int) -> str:
    return f"L{line_number:06d}"


def annotation_display(line: dict, role: str) -> str:
    return f"{line['line_id']} | {role} | {line['text']}"


def prepare(args: argparse.Namespace) -> None:
    source = Path(args.input_file)
    output_dir = Path(args.output_dir)
    chunk_size = args.chunk_size
    overlap = args.overlap_lines

    if chunk_size < 1:
        raise ValueError("--chunk-size must be positive")
    if overlap < 0:
        raise ValueError("--overlap-lines cannot be negative")

    entries = parse_entries(source.read_text(encoding="utf-8"))
    output_dir.mkdir(parents=True, exist_ok=True)

    line_records = [
        {"line_id": make_line_id(i), "line_number": i, "text": text}
        for i, text in enumerate(entries, 1)
    ]

    chunks = []
    for chunk_number, start in enumerate(range(0, len(line_records), chunk_size)):
        editable = line_records[start:start + chunk_size]
        before = line_records[max(0, start - overlap):start]
        after = line_records[start + chunk_size:start + chunk_size + overlap]
        chunk_id = f"chunk_{chunk_number:02d}"
        chunk_path = output_dir / f"{chunk_id}.txt"

        chunk_lines = [
            "# OOC_ANNOTATION_CHUNK v1",
            f"# chunk_id: {chunk_id}",
            f"# source: {source}",
            f"# editable_start_line: {editable[0]['line_number'] if editable else ''}",
            f"# editable_end_line: {editable[-1]['line_number'] if editable else ''}",
            "",
            "## CONTEXT_BEFORE",
            *[annotation_display(line, "CONTEXT") for line in before],
            "",
            "## EDITABLE_LINES",
            *[annotation_display(line, "EDITABLE") for line in editable],
            "",
            "## CONTEXT_AFTER",
            *[annotation_display(line, "CONTEXT") for line in after],
            "",
        ]
        chunk_path.write_text("\n".join(chunk_lines), encoding="utf-8")
        chunks.append(
            {
                "chunk_id": chunk_id,
                "chunk_file": chunk_path.name,
                "annotation_file": f"{chunk_id}_annotations.jsonl",
                "editable_line_ids": [line["line_id"] for line in editable],
                "context_before_line_ids": [line["line_id"] for line in before],
                "context_after_line_ids": [line["line_id"] for line in after],
            }
        )

    manifest = {
        "version": 1,
        "source": str(source),
        "chunk_size": chunk_size,
        "overlap_lines": overlap,
        "line_count": len(line_records),
        "lines": line_records,
        "chunks": chunks,
    }
    manifest_path = output_dir / "annotation_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"Split {len(entries)} entries into {len(chunks)} annotation chunks in {output_dir}/")
    print(f"Manifest: {manifest_path}")
    print(f"Recommended model: {RECOMMENDED_MODEL}")
    print("For each chunk_NN.txt, apply `filter_ooc.py prompt --chunk-file chunk_NN.txt`.")
    print("Save LLM JSONL results as chunk_NN_annotations.jsonl in the same directory.")


def parse_chunk_sections(path: Path) -> dict[str, list[str]]:
    sections = {"CONTEXT_BEFORE": [], "EDITABLE_LINES": [], "CONTEXT_AFTER": []}
    current = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        normalized = stripped.strip("#").strip().upper()
        if normalized in sections:
            current = normalized
            continue
        if not current or not stripped or stripped.startswith("#"):
            continue
        sections[current].append(raw_line)
    return sections


def build_prompt(context_before: str, editable_lines: str, context_after: str) -> str:
    return (
        ANNOTATION_PROMPT_TEMPLATE
        .replace("{context_before}", context_before or "<none>")
        .replace("{editable_lines}", editable_lines or "<none>")
        .replace("{context_after}", context_after or "<none>")
    )


def prompt(args: argparse.Namespace) -> None:
    if args.chunk_file:
        sections = parse_chunk_sections(Path(args.chunk_file))
        text = build_prompt(
            "\n".join(sections["CONTEXT_BEFORE"]),
            "\n".join(sections["EDITABLE_LINES"]),
            "\n".join(sections["CONTEXT_AFTER"]),
        )
    else:
        text = build_prompt(
            "<context lines from chunk_NN.txt>",
            "<editable lines from chunk_NN.txt>",
            "<context lines from chunk_NN.txt>",
        )
    print(text)
    print(f"\n# Recommended model: {RECOMMENDED_MODEL}")
    print("# Save output as chunk_NN_annotations.jsonl beside the chunk file.")


def load_manifest(path: Path) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("version") != 1:
        raise ValueError(f"Unsupported annotation manifest version: {manifest.get('version')}")
    return manifest


def normalize_enum(value) -> str:
    return "" if value is None else str(value).strip().upper()


def line_prefix(line: str) -> str | None:
    match = FULL_ENTRY_RE.match(line)
    if not match:
        return None
    return f"[{match.group('timestamp')}] {match.group('speaker')}: "


def normalize_replacement(value, field_name: str, line_id: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{line_id}: {field_name} must be string or null")
    value = value.strip()
    if not value:
        return None
    if FULL_ENTRY_RE.match(value):
        raise ValueError(f"{line_id}: {field_name} must be post-colon text only")
    return value


def load_annotation_records(annotation_dir: Path) -> list[dict]:
    files = sorted(annotation_dir.glob("chunk_*_annotations.jsonl"))
    if not files:
        raise FileNotFoundError(f"No chunk_*_annotations.jsonl files found in {annotation_dir}")

    records = []
    for path in files:
        for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            stripped = raw_line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            record["_annotation_file"] = path.name
            record["_annotation_line"] = line_number
            records.append(record)
    return records


def validate_records(manifest: dict, records: list[dict], require_all: bool = True) -> dict[str, dict]:
    line_by_id = {line["line_id"]: line for line in manifest["lines"]}
    editable_by_id = {}
    chunk_by_line_id = {}
    for chunk in manifest["chunks"]:
        for line_id in chunk["editable_line_ids"]:
            editable_by_id[line_id] = line_by_id[line_id]
            chunk_by_line_id[line_id] = chunk["chunk_id"]

    seen = {}
    validated = {}
    errors = []

    for record in records:
        line_id = record.get("line_id")
        location = f"{record.get('_annotation_file')}:{record.get('_annotation_line')}"
        if not isinstance(line_id, str):
            errors.append(f"{location}: missing string line_id")
            continue
        if line_id in seen:
            errors.append(f"{location}: duplicate annotation for {line_id}; first seen at {seen[line_id]}")
            continue
        seen[line_id] = location
        if line_id not in editable_by_id:
            errors.append(f"{location}: {line_id} is not editable in the manifest")
            continue

        action = normalize_enum(record.get("action"))
        category = normalize_enum(record.get("category"))
        importance = normalize_enum(record.get("importance"))
        reason = str(record.get("reason") or "").strip()

        if action not in ALLOWED_ACTIONS:
            errors.append(f"{location}: invalid action {record.get('action')!r}")
        if category not in ALLOWED_CATEGORIES:
            errors.append(f"{location}: invalid category {record.get('category')!r}")
        if importance not in ALLOWED_IMPORTANCE:
            errors.append(f"{location}: invalid importance {record.get('importance')!r}")
        if not reason:
            errors.append(f"{location}: reason is required")

        try:
            replacement = normalize_replacement(record.get("replacement"), "replacement", line_id)
        except ValueError as exc:
            errors.append(f"{location}: {exc}")
            replacement = None

        if action == "TRIM" and not replacement:
            errors.append(f"{location}: TRIM requires replacement")
        if action != "TRIM" and replacement:
            errors.append(f"{location}: replacement is only allowed for TRIM")

        prefix = line_prefix(editable_by_id[line_id]["text"])
        if action == "TRIM" and replacement and prefix is None:
            errors.append(f"{location}: cannot TRIM malformed transcript line")

        validated[line_id] = {
            **record,
            "action": action,
            "category": category,
            "importance": importance,
            "replacement": replacement,
            "reason": reason,
            "chunk_id": chunk_by_line_id[line_id],
        }

    if require_all:
        missing = sorted(set(editable_by_id) - set(validated))
        if missing:
            preview = ", ".join(missing[:20])
            suffix = "..." if len(missing) > 20 else ""
            errors.append(f"Missing annotations for {len(missing)} editable lines: {preview}{suffix}")

    if errors:
        raise ValueError("Annotation validation failed:\n" + "\n".join(f"- {error}" for error in errors))

    return validated


def rebuild_line(original: str, replacement: str) -> str:
    prefix = line_prefix(original)
    if prefix is None:
        raise ValueError(f"Cannot rebuild malformed transcript line: {original}")
    return prefix + replacement


def clean_line(line: dict, record: dict | None) -> str | None:
    if record is None:
        return line["text"]
    if record["action"] == "REMOVE":
        return None
    if record["action"] == "TRIM":
        return rebuild_line(line["text"], record["replacement"])
    return line["text"]


def write_diff(source_lines: list[str], output_lines: list[str], from_path: Path, to_path: Path, diff_path: Path) -> None:
    diff = difflib.unified_diff(
        [line + "\n" for line in source_lines],
        [line + "\n" for line in output_lines],
        fromfile=str(from_path),
        tofile=str(to_path),
        lineterm="",
    )
    diff_path.write_text("".join(diff), encoding="utf-8")


def apply(args: argparse.Namespace) -> None:
    manifest_path = Path(args.manifest)
    annotation_dir = Path(args.annotation_dir)
    manifest = load_manifest(manifest_path)
    records = load_annotation_records(annotation_dir)
    annotations = validate_records(manifest, records, require_all=not args.allow_missing)

    source_path = Path(manifest["source"])
    cleaned_output = Path(args.cleaned_output)
    report_output = Path(args.report_output)
    ambiguous_output = Path(args.ambiguous_output)
    cleaned_diff_output = Path(args.cleaned_diff_output)

    cleaned_lines = []
    changed = []
    ambiguous = []
    missing_kept = []

    for line in manifest["lines"]:
        record = annotations.get(line["line_id"])
        cleaned = clean_line(line, record)

        if record is None:
            missing_kept.append(line)
        else:
            if record["action"] != "KEEP":
                changed.append((line, record, cleaned))
            if record["action"] == "REVIEW":
                ambiguous.append((line, record, cleaned))

        if cleaned is not None:
            cleaned_lines.append(cleaned)

    cleaned_output.write_text("\n".join(cleaned_lines) + "\n", encoding="utf-8")
    write_diff([line["text"] for line in manifest["lines"]], cleaned_lines, source_path, cleaned_output, cleaned_diff_output)

    action_counts = {action: 0 for action in sorted(ALLOWED_ACTIONS)}
    category_counts = {category: 0 for category in sorted(ALLOWED_CATEGORIES)}
    for record in annotations.values():
        action_counts[record["action"]] += 1
        category_counts[record["category"]] += 1

    with report_output.open("w", encoding="utf-8") as f:
        f.write("# Annotation-First OOC Cleanup Report\n\n")
        f.write(f"- Source: `{source_path}`\n")
        f.write(f"- Manifest: `{manifest_path}`\n")
        f.write(f"- Annotation directory: `{annotation_dir}`\n")
        f.write(f"- Cleaned transcript: `{cleaned_output}`\n")
        f.write(f"- Input lines: {len(manifest['lines'])}\n")
        f.write(f"- Cleaned lines: {len(cleaned_lines)}\n")
        f.write(f"- Missing annotations kept: {len(missing_kept)}\n\n")

        f.write("## Action Counts\n\n")
        for action, count in action_counts.items():
            f.write(f"- {action}: {count}\n")
        f.write("\n## Category Counts\n\n")
        for category, count in category_counts.items():
            if count:
                f.write(f"- {category}: {count}\n")

        f.write("\n## Changed Lines\n\n")
        for line, record, cleaned in changed:
            f.write(
                f"- `{line['line_id']}` `{record['chunk_id']}` "
                f"{record['action']} "
                f"{record['category']} {record['importance']}: {record['reason']}\n"
            )
            f.write(f"  - original: {line['text']}\n")
            f.write(f"  - cleaned: {cleaned if cleaned is not None else '<removed>'}\n")

    with ambiguous_output.open("w", encoding="utf-8") as f:
        f.write("# Annotation-First OOC Ambiguous Review\n\n")
        if not ambiguous:
            f.write("No REVIEW lines.\n")
        for line, record, cleaned in ambiguous:
            f.write(
                f"- `{line['line_id']}` `{record['chunk_id']}` "
                f"{record['action']} "
                f"{record['category']} {record['importance']}: {record['reason']}\n"
            )
            f.write(f"  - original: {line['text']}\n")
            f.write(f"  - cleaned: {cleaned if cleaned is not None else '<removed>'}\n")

    print(f"Wrote cleaned transcript: {cleaned_output}")
    print(f"Wrote report: {report_output}")
    print(f"Wrote ambiguous review: {ambiguous_output}")
    print(f"Wrote cleaned diff: {cleaned_diff_output}")
    print(f"Input={len(manifest['lines'])} cleaned={len(cleaned_lines)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p_prepare = sub.add_parser("prepare", help="Split transcript into annotation chunks")
    p_prepare.add_argument("input_file", help="Timestamped transcript file")
    p_prepare.add_argument("output_dir", help="Directory for chunks and annotation_manifest.json")
    p_prepare.add_argument("--chunk-size", type=int, default=80, help="Editable entries per chunk")
    p_prepare.add_argument("--overlap-lines", type=int, default=8, help="Context lines before/after each chunk")

    p_prompt = sub.add_parser("prompt", help="Print annotation prompt")
    p_prompt.add_argument("--chunk-file", help="Optional chunk file to embed")

    p_apply = sub.add_parser("apply", help="Validate and apply chunk annotations")
    p_apply.add_argument("manifest", help="annotation_manifest.json from prepare")
    p_apply.add_argument("annotation_dir", help="Directory containing chunk_XX_annotations.jsonl")
    p_apply.add_argument("cleaned_output", help="Audit-friendly cleaned transcript")
    p_apply.add_argument("report_output", help="Markdown report")
    p_apply.add_argument("ambiguous_output", help="Markdown ambiguous review")
    p_apply.add_argument("cleaned_diff_output", help="Unified diff for cleaned transcript")
    p_apply.add_argument("--allow-missing", action="store_true", help="Keep missing annotations instead of failing")

    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args)
    elif args.command == "prompt":
        prompt(args)
    elif args.command == "apply":
        apply(args)


if __name__ == "__main__":
    main()
