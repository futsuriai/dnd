#!/usr/bin/env python3
"""Fetch D&D Beyond game-log dice rolls and align them to session audio.

D&D Beyond has no official API; this uses the same unofficial game-log REST
endpoints community tools (Foundry DDB Gamelog, Avrae, EncounterLog) use. It
may break if D&D Beyond changes them.

One-time setup in dnd/.env.local (git-ignored):
    DDB_COBALT_SESSION=<value of the CobaltSession cookie on www.dndbeyond.com>
    DDB_CAMPAIGN_ID=<number from https://www.dndbeyond.com/campaigns/<id>>
    # optional: DDB_USER_ID=<your numeric D&D Beyond user id>

The CobaltSession cookie is a login credential: keep it only in .env.local.

Subcommands:
    fetch   download the campaign log, keep the most recent play session's rolls
    align   estimate the recording-start offset by matching roll totals to
            numbers spoken in the transcript, then write audio-timed events

Craig recordings carry no wall-clock start time, so `align` votes over every
(roll, spoken number) pair and picks the offset most rolls agree on. Pass
--recording-start to skip estimation when the start time is known.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import statistics
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib import error, parse, request

SCRIPT_DIR = Path(__file__).resolve().parent
DND_DIR = SCRIPT_DIR.parent.parent
AUTH_URL = "https://auth-service.dndbeyond.com/v1/cobalt-token"
USER_DATA_URL = "https://www.dndbeyond.com/mobile/api/v6/user-data"
GAME_LOG_BASE = "https://game-log-rest-live.dndbeyond.com/v1"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) dnd-session-pipeline"
PARTY = ["Berridin", "Ellara", "Nyx", "Ysidor", "Witty"]


# ---------------------------------------------------------------- utilities

def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def http(method: str, url: str, headers: dict[str, str], body: bytes | None = None) -> dict:
    req = request.Request(url, data=body, headers={"User-Agent": USER_AGENT, **headers}, method=method)
    try:
        with request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"{method} {url.split('?')[0]} -> HTTP {exc.code}: {detail}") from exc


def parse_time(raw) -> datetime | None:
    if raw in (None, ""):
        return None
    if isinstance(raw, (int, float)) or (isinstance(raw, str) and raw.isdigit()):
        value = float(raw)
        return datetime.fromtimestamp(value / 1000 if value > 1e11 else value, tz=timezone.utc)
    text = str(raw).strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def jwt_claims(token: str) -> dict:
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload))
    except (IndexError, ValueError):
        return {}


# ---------------------------------------------------------------- fetch

def cobalt_token(cobalt: str) -> str:
    data = http("POST", AUTH_URL, {"Cookie": f"CobaltSession={cobalt}", "Content-Type": "application/json"}, b"")
    token = data.get("token")
    if not token:
        raise RuntimeError("auth-service returned no token; is DDB_COBALT_SESSION current?")
    return token


def resolve_user_id(cobalt: str, token: str) -> str:
    if os.environ.get("DDB_USER_ID"):
        return os.environ["DDB_USER_ID"]
    for key, value in jwt_claims(token).items():
        if key.endswith("nameidentifier") or key in {"sub", "userId", "user_id"}:
            if str(value).isdigit():
                return str(value)
    body = f"token={cobalt}".encode("utf-8")
    data = http(
        "POST",
        USER_DATA_URL,
        {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Bearer {token}",
            "Cookie": f"CobaltSession={cobalt}",
        },
        body,
    )
    user_id = data.get("userId") or (data.get("data") or {}).get("userId")
    if not user_id:
        raise RuntimeError("could not resolve D&D Beyond user id; set DDB_USER_ID in .env.local")
    return str(user_id)


def fetch_pages(game_id: str, user_id: str, cobalt: str, max_pages: int) -> list[dict]:
    """Return raw roll/message records, trying the paginated endpoint first."""
    token = cobalt_token(cobalt)
    token_time = time.monotonic()
    headers = lambda: {  # noqa: E731
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Origin": "https://www.dndbeyond.com",
        "Referer": f"https://www.dndbeyond.com/campaigns/{game_id}",
    }
    records: list[dict] = []
    url = f"{GAME_LOG_BASE}/game-log/{game_id}/rolls?userId={user_id}&limit=100"
    try:
        for _ in range(max_pages):
            if time.monotonic() - token_time > 240:
                token, token_time = cobalt_token(cobalt), time.monotonic()
            page = http("GET", url, headers())
            batch = page.get("data") or []
            records.extend(batch)
            nxt = (page.get("pagination") or {}).get("next")
            if not batch or not nxt:
                break
            url = nxt if nxt.startswith("http") else parse.urljoin(GAME_LOG_BASE + "/", nxt.lstrip("/"))
        if records:
            return records
    except RuntimeError as exc:
        print(f"paginated rolls endpoint failed ({exc}); falling back to getmessages", file=sys.stderr)

    url = f"{GAME_LOG_BASE}/getmessages?gameId={game_id}&userId={user_id}"
    last_key = None
    for _ in range(max_pages):
        page = http("GET", url + (f"&lastKey={parse.quote(json.dumps(last_key))}" if last_key else ""), headers())
        batch = page.get("data") or []
        records.extend(batch)
        last_key = page.get("lastKey")
        if not batch or not last_key:
            break
    return records


def normalize_record(record: dict) -> dict | None:
    data = record.get("data") if isinstance(record.get("data"), dict) else record
    event_type = record.get("eventType") or record.get("event_type") or "dice/roll/fulfilled"
    if "roll" not in event_type:
        return None
    when = parse_time(record.get("dateTime") or record.get("timestamp") or data.get("dateTime"))
    if when is None:
        return None
    context = data.get("context") or record.get("context") or {}
    rolls = data.get("rolls") or record.get("rolls") or []
    totals, naturals, details, roll_types, kinds = [], [], [], [], []
    for roll in rolls:
        if not isinstance(roll, dict):
            continue
        result = roll.get("result") or {}
        if result.get("total") is not None:
            totals.append(result.get("total"))
        values = result.get("values") or []
        sets = (roll.get("diceNotation") or {}).get("set") or []
        if any(str(s.get("dieType")) == "d20" for s in sets if isinstance(s, dict)):
            naturals.extend(v for v in values if isinstance(v, int))
        if result.get("text"):
            details.append(str(result["text"]))
        if roll.get("rollType"):
            roll_types.append(roll["rollType"])
        if roll.get("rollKind"):
            kinds.append(roll["rollKind"])
    if not totals:
        return None
    return {
        "id": record.get("id") or record.get("rollId") or data.get("rollId"),
        "wall_time": when.isoformat(),
        "character_raw": context.get("name") or context.get("characterName") or record.get("characterName") or "",
        "entity_type": context.get("entityType"),
        "action": data.get("action") or context.get("action") or "",
        "roll_type": " ".join(dict.fromkeys(roll_types)),
        "roll_kind": " ".join(dict.fromkeys(kinds)),
        "total": totals[0] if len(totals) == 1 else totals,
        "naturals": naturals,
        "detail": "; ".join(details),
    }


def canonical_character(raw: str, entity_type: str | None) -> str:
    lowered = (raw or "").lower()
    for name in PARTY:
        if name.lower() in lowered:
            return name
    if "whitaker" in lowered or "whitman" in lowered:
        return "Witty"
    if not raw or (entity_type and entity_type.lower() in {"user", "dm"}):
        return "GM"
    return raw


def latest_cluster(rolls: list[dict], gap_hours: float) -> list[dict]:
    rolls = sorted(rolls, key=lambda r: r["wall_time"])
    clusters: list[list[dict]] = []
    for roll in rolls:
        when = parse_time(roll["wall_time"])
        if clusters and (when - parse_time(clusters[-1][-1]["wall_time"])).total_seconds() <= gap_hours * 3600:
            clusters[-1].append(roll)
        else:
            clusters.append([roll])
    return clusters[-1] if clusters else []


def cmd_fetch(args: argparse.Namespace) -> int:
    load_env_file(Path(args.env_file))
    cobalt = os.environ.get("DDB_COBALT_SESSION")
    game_id = args.campaign_id or os.environ.get("DDB_CAMPAIGN_ID")
    if not cobalt or not game_id:
        print("DDB_COBALT_SESSION and DDB_CAMPAIGN_ID must be set (see --help); skipping dice fetch.")
        return 2

    token = cobalt_token(cobalt)
    user_id = resolve_user_id(cobalt, token)
    raw = fetch_pages(str(game_id), user_id, cobalt, args.max_pages)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "ddb_raw.json").write_text(json.dumps(raw, indent=1) + "\n", encoding="utf-8")

    rolls = [r for r in (normalize_record(x) for x in raw) if r]
    for roll in rolls:
        roll["character"] = canonical_character(roll["character_raw"], roll.get("entity_type"))
    if args.since:
        since = parse_time(args.since)
        rolls = [r for r in rolls if parse_time(r["wall_time"]) >= since]
    if args.until:
        until = parse_time(args.until)
        rolls = [r for r in rolls if parse_time(r["wall_time"]) <= until]
    if not args.since and not args.until:
        rolls = latest_cluster(rolls, args.session_gap_hours)

    rolls.sort(key=lambda r: r["wall_time"])
    with (out_dir / "rolls.jsonl").open("w", encoding="utf-8") as f:
        for roll in rolls:
            f.write(json.dumps(roll, ensure_ascii=False) + "\n")
    span = f"{rolls[0]['wall_time']} .. {rolls[-1]['wall_time']}" if rolls else "none"
    print(f"Fetched {len(raw)} log records; kept {len(rolls)} rolls ({span}) -> {out_dir / 'rolls.jsonl'}")
    print("Characters:", dict(Counter(r["character"] for r in rolls)))
    return 0


# ---------------------------------------------------------------- align

NUMBER_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
}


def spoken_numbers(text: str) -> set[int]:
    lowered = text.lower().replace("-", " ")
    numbers = {int(n) for n in re.findall(r"(?<![\d.])\d{1,3}(?![\d.])", lowered)}
    tokens = re.findall(r"[a-z]+", lowered)
    for i, token in enumerate(tokens):
        if token in NUMBER_WORDS:
            value = NUMBER_WORDS[token]
            if value in (20, 30, 40, 50) and i + 1 < len(tokens) and tokens[i + 1] in NUMBER_WORDS and NUMBER_WORDS[tokens[i + 1]] < 10:
                value += NUMBER_WORDS[tokens[i + 1]]
            numbers.add(value)
    if re.search(r"\bnat(ural)?\s*(20|twenty)\b|\bcrit\b", lowered):
        numbers.add(20)
    return numbers


def load_lines(path: Path) -> list[dict]:
    lines = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if raw.strip():
            line = json.loads(raw)
            if line.get("speaker") != "DICE":
                line["numbers"] = spoken_numbers(line["text"])
                lines.append(line)
    return lines


def estimate_offset(rolls: list[dict], lines: list[dict], bin_seconds: float) -> tuple[float | None, dict]:
    votes: dict[int, set[int]] = defaultdict(set)
    candidates: list[tuple[float, int]] = []
    for index, roll in enumerate(rolls):
        wall = parse_time(roll["wall_time"]).timestamp()
        totals = roll["total"] if isinstance(roll["total"], list) else [roll["total"]]
        targets = {int(t) for t in totals if isinstance(t, (int, float))} | {int(n) for n in roll.get("naturals", [])}
        targets.discard(0)
        speakers = {roll.get("character"), "GM"}
        for line in lines:
            if line["speaker"] in speakers and targets & line["numbers"]:
                offset = wall - line["start"]
                candidates.append((offset, index))
                votes[int(offset // bin_seconds)].add(index)
    if not votes:
        return None, {"reason": "no spoken numbers matched any roll"}

    def support(bin_id: int) -> int:
        return len(votes.get(bin_id - 1, set()) | votes.get(bin_id, set()) | votes.get(bin_id + 1, set()))

    ranked = sorted(votes, key=support, reverse=True)
    best = ranked[0]
    runner_up = next((b for b in ranked[1:] if abs(b - best) > 5), None)
    near = [off for off, _ in candidates if abs(off - (best + 0.5) * bin_seconds) <= 1.5 * bin_seconds]
    offset = statistics.median(near)
    stats = {
        "rolls": len(rolls),
        "supporting_rolls": support(best),
        "runner_up_support": support(runner_up) if runner_up is not None else 0,
        "offset_epoch": offset,
        "recording_start_utc": datetime.fromtimestamp(offset, tz=timezone.utc).isoformat(),
    }
    confident = stats["supporting_rolls"] >= max(4, 0.15 * len(rolls)) and stats["supporting_rolls"] >= 2 * stats["runner_up_support"]
    stats["confident"] = confident
    return (offset if confident else None), stats


def cmd_align(args: argparse.Namespace) -> int:
    rolls = [json.loads(l) for l in Path(args.rolls).read_text(encoding="utf-8").splitlines() if l.strip()]
    lines = load_lines(Path(args.lines_jsonl))
    out = Path(args.out)
    if not rolls:
        print("no rolls to align")
        out.write_text("", encoding="utf-8")
        return 0

    if args.recording_start:
        offset = parse_time(args.recording_start).timestamp()
        stats = {"method": "given", "recording_start_utc": args.recording_start, "confident": True}
    else:
        offset, stats = estimate_offset(rolls, lines, args.bin_seconds)
        stats["method"] = "spoken-number voting"
    duration = max((l["end"] for l in lines), default=0)

    aligned = 0
    with out.open("w", encoding="utf-8") as f:
        for roll in rolls:
            event = dict(roll)
            if offset is not None:
                audio_time = parse_time(roll["wall_time"]).timestamp() - offset
                event["audio_time"] = round(audio_time, 2) if -60 <= audio_time <= duration + 600 else None
                aligned += event["audio_time"] is not None
            else:
                event["audio_time"] = None
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    stats["aligned_rolls"] = aligned
    Path(args.report).write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8") if args.report else None
    print(json.dumps(stats, indent=2))
    return 0 if offset is not None else 3


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    fetch = sub.add_parser("fetch", help="Download dice rolls from the campaign game log")
    fetch.add_argument("--out-dir", required=True)
    fetch.add_argument("--env-file", default=str(DND_DIR / ".env.local"))
    fetch.add_argument("--campaign-id")
    fetch.add_argument("--since", help="ISO time; keep rolls at/after this")
    fetch.add_argument("--until", help="ISO time; keep rolls at/before this")
    fetch.add_argument("--session-gap-hours", type=float, default=5.0, help="Gap that separates play sessions")
    fetch.add_argument("--max-pages", type=int, default=50)
    fetch.set_defaults(func=cmd_fetch)

    align = sub.add_parser("align", help="Map roll wall-clock times onto the recording timeline")
    align.add_argument("rolls", help="rolls.jsonl from fetch")
    align.add_argument("lines_jsonl", help="Transcript .lines.jsonl from assemble_transcript.py")
    align.add_argument("--out", required=True, help="Aligned dice events JSONL")
    align.add_argument("--report", help="Alignment stats JSON")
    align.add_argument("--recording-start", help="Known recording start (ISO) instead of estimating")
    align.add_argument("--bin-seconds", type=float, default=3.0)
    align.set_defaults(func=cmd_align)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
