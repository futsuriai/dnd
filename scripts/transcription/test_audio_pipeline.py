#!/usr/bin/env python3
"""Unit tests for the upgraded audio, Gemini 4 Neon, fusion, normalization, and raw-notes pipeline."""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import agent_cli
import asr_diagnostics
import asr_gemini_windows
import asr_whisper
import assemble_transcript
import audit_raw_notes
import ddb_rolls
import fuse_transcript
import raw_notes_auto
import run_asr_engines
import session_facts
import transcribe_gladia
import vad_compact
from name_normalizer import NameNormalizer


class TestVadCompactTimelineMapper(unittest.TestCase):
    def setUp(self) -> None:
        # Two VAD islands separated by 250ms synthetic silence gap in compact audio,
        # but separated by 285 seconds (4m45s) in original audio!
        self.segments = [
            {
                "compact_start": 0.0,
                "compact_end": 5.0,
                "original_start": 10.0,
                "original_end": 15.0,
            },
            {
                "compact_start": 5.25,
                "compact_end": 10.25,
                "original_start": 300.0,
                "original_end": 305.0,
            },
        ]
        self.mapper = vad_compact.TimelineMapper(self.segments)

    def test_end_in_synthetic_gap_clamps_to_first_island(self) -> None:
        # Word ends 50ms into the synthetic 250ms gap: MUST clamp to 15.0, NOT jump to 300.0!
        self.assertAlmostEqual(self.mapper.map_time(4.80, is_end=False), 14.80, places=3)
        self.assertAlmostEqual(self.mapper.map_time(5.05, is_end=True), 15.0, places=3)
        self.assertAlmostEqual(self.mapper.map_time(5.20, is_end=True), 15.0, places=3)

    def test_map_span_clamps_cross_gap_word_to_start_island(self) -> None:
        s, e = self.mapper.map_span(4.80, 5.10, clamp_to_start_segment=True)
        self.assertAlmostEqual(s, 14.80, places=3)
        self.assertAlmostEqual(e, 15.0, places=3)
        self.assertLessEqual(e - s, 1.0)

        # Even if a jittered word end crosses into island 1 start, single-word span clamps to island 0 end.
        s2, e2 = self.mapper.map_span(4.90, 5.30, clamp_to_start_segment=True)
        self.assertAlmostEqual(s2, 14.90, places=3)
        self.assertAlmostEqual(e2, 15.0, places=3)

    def test_map_span_normal_second_island(self) -> None:
        s, e = self.mapper.map_span(5.50, 6.00, clamp_to_start_segment=True)
        self.assertAlmostEqual(s, 300.25, places=3)
        self.assertAlmostEqual(e, 300.75, places=3)


class TestAssembleTranscript(unittest.TestCase):
    def test_preserves_affirmative_answer_after_turn_end(self) -> None:
        tracks = {
            "1-gm": {
                "words": [
                    {"s": 10.0, "e": 10.4, "w": "Do", "p": 0.99},
                    {"s": 10.4, "e": 10.7, "w": "you", "p": 0.99},
                    {"s": 10.7, "e": 11.2, "w": "open", "p": 0.99},
                    {"s": 11.2, "e": 11.6, "w": "the", "p": 0.99},
                    {"s": 11.6, "e": 12.0, "w": "door?", "p": 0.99},
                ],
                "segments": [],
            },
            "2-nyx": {
                "words": [
                    # Player answers "Yes." 0.3s after GM finished (within old other["e"]+1.0 bug window!)
                    {"s": 12.3, "e": 12.7, "w": "Yes.", "p": 0.95},
                ],
                "segments": [],
            },
        }
        speaker_map = {"1-gm": "GM", "2-nyx": "Nyx"}
        lines = assemble_transcript.build_lines(
            tracks, speaker_map, split_gap=0.9, merge_gap=2.0,
            max_turn_chars=600, max_duration=25.0, low_conf=0.45, keep_backchannels=False,
        )
        speakers_and_texts = [(l["speaker"], l["text"]) for l in lines]
        self.assertIn(("Nyx", "Yes."), speakers_and_texts)
        # raw_asr_text must be preserved on assembled lines
        for line in lines:
            self.assertIn("raw_asr_text", line)
            self.assertIn("overlap_speakers", line)
            self.assertIn("possible_bleed", line)

    def test_drops_strictly_nested_backchannel_during_active_speech(self) -> None:
        tracks = {
            "1-gm": {
                "words": [
                    {"s": 10.0, "e": 11.5, "w": "You", "p": 0.99},
                    {"s": 11.5, "e": 13.0, "w": "walk", "p": 0.99},
                    {"s": 13.0, "e": 14.5, "w": "down", "p": 0.99},
                    {"s": 14.5, "e": 16.0, "w": "the", "p": 0.99},
                    {"s": 16.0, "e": 18.0, "w": "hallway.", "p": 0.99},
                ],
                "segments": [],
            },
            "2-nyx": {
                "words": [
                    # Strictly nested while GM is mid-sentence (12.0..12.4 inside 10.0..18.0)
                    {"s": 12.0, "e": 12.4, "w": "yeah", "p": 0.9},
                ],
                "segments": [],
            },
        }
        speaker_map = {"1-gm": "GM", "2-nyx": "Nyx"}
        lines = assemble_transcript.build_lines(
            tracks, speaker_map, split_gap=0.9, merge_gap=2.0,
            max_turn_chars=600, max_duration=25.0, low_conf=0.45, keep_backchannels=False,
        )
        self.assertEqual([l["speaker"] for l in lines], ["GM"])

    def test_merges_verified_one_sided_gemini_speech_and_flags_bleed(self) -> None:
        tracks = {
            "1-gm": {
                "words": [
                    {"s": 10.0, "e": 10.5, "w": "Roll", "p": 0.99},
                    {"s": 10.5, "e": 11.0, "w": "stealth.", "p": 0.99},
                ],
                "segments": [],
            },
            "2-nyx": {
                "words": [
                    {"s": 10.1, "e": 10.9, "w": "Roll", "p": 0.35},
                ],
                "segments": [],
            },
        }
        verdicts = [
            {
                "track": "2-nyx",
                "speaker": "Nyx",
                "s": 10.0,
                "e": 11.0,
                "status": "mic_bleed",
                "text": "",
                "origin": "reference",
            },
            {
                "track": "2-nyx",
                "speaker": "Nyx",
                "s": 13.0,
                "e": 14.0,
                "status": "speech",
                "text": "I rolled a natural 20.",
                "origin": "alt_only",
            },
        ]
        speaker_map = {"1-gm": "GM", "2-nyx": "Nyx"}
        lines = assemble_transcript.build_lines(
            tracks, speaker_map, split_gap=0.9, merge_gap=1.0,
            max_turn_chars=600, max_duration=25.0, low_conf=0.45, keep_backchannels=False,
            gemini_verdicts=verdicts,
        )
        bleed_line = next(l for l in lines if l["speaker"] == "Nyx" and l["start"] < 12.0)
        self.assertTrue(bleed_line["possible_bleed"])
        self.assertEqual(bleed_line.get("gemini_verdict"), "mic_bleed")
        self.assertIn("GM", bleed_line["overlap_speakers"])

        recovered = next(l for l in lines if "natural 20" in l["text"])
        self.assertEqual(recovered["recovered_from"], "alt_only")

    def test_multi_roll_dice_formatting_has_no_brackets(self) -> None:
        event = {
            "audio_time": 42.5,
            "character": "Nyx",
            "action": "Longbow",
            "roll_type": "to hit damage",
            "total": [19, 11],
            "detail": "1d20+7; 1d8+4",
        }
        line = assemble_transcript.dice_line(event)
        self.assertNotIn("[", line["text"])
        self.assertNotIn("]", line["text"])
        self.assertIn("19, 11", line["text"])


class TestFuseTranscript(unittest.TestCase):
    def test_acceptable_allows_homophone_and_campaign_fixes(self) -> None:
        canonical = {"hyr", "nyx", "ellara", "berridin", "ysidor", "witty", "nites"}
        extra = fuse_transcript._context_hint_tokens(NameNormalizer())
        # Previously rejected by len(unheard) <= max(1, len(new)//10)!
        self.assertTrue(fuse_transcript.acceptable(["I pull out ascending stone"], "I pull out a sending stone", canonical, extra))
        self.assertTrue(fuse_transcript.acceptable(["ascending stone"], "a sending stone", canonical, extra))
        self.assertTrue(fuse_transcript.acceptable(["that 20"], "nat 20", canonical, extra))
        self.assertTrue(fuse_transcript.acceptable(["the story of here"], "the story of Hýr", canonical, extra))
        self.assertTrue(
            fuse_transcript.acceptable(["a Nick's individual"], "a high net worth individual", canonical, extra)
        )

    def test_acceptable_rejects_hallucinated_inventions(self) -> None:
        canonical = {"hyr", "nyx"}
        self.assertFalse(
            fuse_transcript.acceptable(
                ["I walk over"],
                "Then the ancient crimson dragon unleashed lightning across the crowded cathedral",
                canonical,
            )
        )
        self.assertFalse(fuse_transcript.acceptable(["hello there"], "", canonical))

    def test_parse_reply_supports_structured_actions_and_legacy_jsonl(self) -> None:
        structured = json.dumps({
            "edits": [
                {"id": "L00001", "action": "replace", "text": "a sending stone", "reason": "homophone"},
                {"id": "L00002", "action": "delete", "text": "", "reason": "mic bleed"},
                {"id": "L00003", "action": "needs_audio", "text": "", "reason": "unclear roll"},
            ]
        })
        parsed = fuse_transcript.parse_reply(structured)
        self.assertEqual(parsed["L00001"]["action"], "replace")
        self.assertEqual(parsed["L00001"]["text"], "a sending stone")
        self.assertEqual(parsed["L00002"]["action"], "delete")
        self.assertEqual(parsed["L00003"]["action"], "needs_audio")

        legacy = '{"id": "L00010", "text": "fixed text"}\n'
        parsed_legacy = fuse_transcript.parse_reply(legacy)
        self.assertEqual(parsed_legacy["L00010"]["action"], "replace")
        self.assertEqual(parsed_legacy["L00010"]["text"], "fixed text")

    def test_rerun_idempotency_resets_to_unfused_baseline(self) -> None:
        lines = [
            {
                "id": "L00001",
                "speaker": "GM",
                "asr_text": "original primary text",
                "raw_asr_text": "original primary text",
                "text": "stale run 1 edit",
                "other_readings": {"Whisper": "something"},
            }
        ]
        fuse_transcript.reset_lines_for_fusion(lines)
        self.assertEqual(lines[0]["text"], "original primary text")
        self.assertNotIn("other_readings", lines[0])

    def test_engine_text_midpoint_matching_excludes_adjacent_words(self) -> None:
        tracks = {
            "1-gm": {
                "words": [
                    {"s": 9.4, "e": 9.7, "w": "before", "p": 0.9},   # mid 9.55 < 9.85 -> excluded
                    {"s": 10.0, "e": 10.4, "w": "inside", "p": 0.9},  # mid 10.2 -> included
                    {"s": 11.4, "e": 11.8, "w": "after", "p": 0.9},   # mid 11.6 > 11.15 -> excluded
                ]
            }
        }
        line = {"track": "1-gm", "start": 10.0, "end": 11.0}
        self.assertEqual(fuse_transcript.engine_text(line, tracks), "inside")


class TestNameNormalizer(unittest.TestCase):
    def setUp(self) -> None:
        self.norm = NameNormalizer()

    def test_sentence_start_protection_for_capitalized_only_fixes(self) -> None:
        # Utterance start
        self.assertEqual(self.norm.normalize("Mary had a little lamb."), "Mary had a little lamb.")
        self.assertEqual(self.norm.normalize("Nick is not here."), "Nick is not here.")
        self.assertEqual(self.norm.normalize("Laura opened the gate."), "Laura opened the gate.")
        # After sentence boundary (. ? !)
        self.assertEqual(self.norm.normalize("Wait. Laura left."), "Wait. Laura left.")
        self.assertEqual(self.norm.normalize("Oh! Merry Christmas!"), "Oh! Merry Christmas!")
        self.assertEqual(self.norm.normalize("Really? Nick said that?"), "Really? Nick said that?")
        # Blocking previous words
        self.assertEqual(self.norm.normalize("I saw a Nick in the blade."), "I saw a Nick in the blade.")
        self.assertEqual(self.norm.normalize("Look at the Mary statue."), "Look at the Mary statue.")
        # Mid-sentence capitalized IS rewritten
        self.assertEqual(self.norm.normalize("We met Mary at the inn."), "We met Meri at the inn.")
        self.assertEqual(self.norm.normalize("Tell Nick and Laura to wait."), "Tell Nyx and Ellara to wait.")

    def test_hyr_consistency_and_no_dead_speaker_label_fixes(self) -> None:
        self.assertEqual(self.norm.normalize("Praise Hjir and Hypp."), "Praise Hýr and Hýr.")
        raw_cfg = json.loads((SCRIPT_DIR / "name_corrections.json").read_text(encoding="utf-8"))
        self.assertNotIn("speaker_label_fixes", raw_cfg)
        self.assertEqual(self.norm.normalize("alara prays to nytes", preserve_lowercase=True), "ellara prays to nites")


class TestAsrDiagnostics(unittest.TestCase):
    def test_three_engine_hotspot_table_populates_all_columns(self) -> None:
        engines = {
            "gladia": {
                "1-gm": {
                    "audio_file": "/tmp/1-gm.flac",
                    "speech_seconds": 30.0,
                    "words": [
                        {"s": 1.0, "e": 1.3, "w": "You", "p": 0.9},
                        {"s": 1.3, "e": 1.6, "w": "rolled", "p": 0.9},
                        {"s": 1.6, "e": 2.0, "w": "fourteen", "p": 0.4},
                        {"s": 2.0, "e": 2.4, "w": "near", "p": 0.9},
                        {"s": 2.4, "e": 2.8, "w": "Alara", "p": 0.5},
                        {"s": 2.8, "e": 3.2, "w": "castle", "p": 0.9},
                        {"s": 3.2, "e": 3.6, "w": "gates", "p": 0.9},
                    ],
                    "segments": [{"s": 1.0, "e": 3.6, "text": "You rolled fourteen near Alara castle gates"}],
                    "params": {},
                }
            },
            "whisper-large-v3": {
                "1-gm": {
                    "audio_file": "/tmp/1-gm.flac",
                    "speech_seconds": 30.0,
                    "words": [
                        {"s": 1.0, "e": 1.3, "w": "You", "p": 0.9},
                        {"s": 1.3, "e": 1.6, "w": "rolled", "p": 0.9},
                        {"s": 1.6, "e": 2.0, "w": "forty", "p": 0.8},
                        {"s": 2.0, "e": 2.4, "w": "by", "p": 0.8},
                        {"s": 2.4, "e": 2.8, "w": "Ellara", "p": 0.9},
                        {"s": 2.8, "e": 3.2, "w": "stone", "p": 0.8},
                        {"s": 3.2, "e": 3.6, "w": "doors", "p": 0.8},
                    ],
                    "segments": [{"s": 1.0, "e": 3.6, "text": "You rolled forty by Ellara stone doors"}],
                    "params": {},
                }
            },
            "gemini": {
                "1-gm": {
                    "audio_file": "/tmp/1-gm.flac",
                    "speech_seconds": 30.0,
                    "words": [
                        {"s": 1.0, "e": 1.4, "w": "You", "p": None},
                        {"s": 1.4, "e": 1.8, "w": "rolled", "p": None},
                        {"s": 1.8, "e": 2.2, "w": "14", "p": None},
                        {"s": 2.2, "e": 2.6, "w": "near", "p": None},
                        {"s": 2.6, "e": 3.0, "w": "Ellara", "p": None},
                        {"s": 3.0, "e": 3.6, "w": "gates", "p": None},
                    ],
                    "segments": [{"s": 1.0, "e": 3.6, "text": "You rolled 14 near Ellara gates"}],
                    "params": {"partial": True},
                }
            },
        }
        report = asr_diagnostics.compute_diagnostics(
            engines, "gladia", session="21", names=["Ellara", "Berridin"], common=set(), normalizer=NameNormalizer()
        )
        self.assertTrue(report["hotspots"])
        hs = report["hotspots"][0]
        # ALL 3 engines must be present in every hotspot dict!
        self.assertEqual(set(hs["texts"].keys()), {"gladia", "whisper-large-v3", "gemini"})
        self.assertIn("14", hs["texts"]["gemini"])
        # Separate dice/number and entity metrics populated for whisper
        self.assertIsNotNone(report["engines"]["whisper-large-v3"]["dice_number_disagreement"])
        self.assertIsNotNone(report["engines"]["whisper-large-v3"]["entity_disagreement"])

        md = asr_diagnostics.render_markdown(report, 10)
        self.assertIn("**gemini**: You rolled 14 near Ellara gates", md)
        self.assertIn("dice/num disagree", md)

        with tempfile.TemporaryDirectory() as tmp:
            out_hs = asr_diagnostics.export_hotspot_segments(report, Path(tmp) / "hotspot_segments.json")
            data = json.loads(out_hs.read_text(encoding="utf-8"))
            self.assertEqual(len(data["segments"]), 1)
            self.assertEqual(data["segments"][0]["track"], "1-gm")


class TestAgentCli(unittest.TestCase):
    def test_agy_write_vs_readonly_and_json_schema_flags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp) / "repo"
            extra = Path(tmp) / "ellara"
            att_dir = Path(tmp) / "clips"
            ws.mkdir()
            extra.mkdir()
            att_dir.mkdir()
            clip = att_dir / "block.ogg"
            clip.write_bytes(b"OggSfake")

            captured: list[tuple[list[str], str]] = []

            def fake_run(cmd, **kwargs):
                captured.append((cmd, kwargs.get("cwd", "")))
                return subprocess.CompletedProcess(
                    cmd, 0, stdout=json.dumps({"type": "result", "result": '{"ok": true}'}), stderr=""
                )

            with mock.patch("agent_cli._require", return_value="/usr/local/bin/agy"), mock.patch(
                "subprocess.run", side_effect=fake_run
            ):
                # 1) write=True
                out_write = agent_cli.run_agent(
                    "Edit the store files.",
                    provider="agy",
                    workspace=ws,
                    write=True,
                    extra_dirs=[extra],
                    json_schema={"type": "object"},
                    effort="high",
                    timeout=180,
                )
                self.assertEqual(out_write, '{"ok": true}')
                cmd_w, cwd_w = captured[-1]
                self.assertEqual(Path(cwd_w).resolve(), ws.resolve())
                prompt_arg = cmd_w[cmd_w.index("-p") + 1]
                self.assertNotIn("Use your file viewing tool only", prompt_arg)
                self.assertIn("--mode", cmd_w)
                self.assertEqual(cmd_w[cmd_w.index("--mode") + 1], "accept-edits")
                self.assertIn("--json-schema", cmd_w)
                self.assertIn("--output-format", cmd_w)
                self.assertEqual(cmd_w[cmd_w.index("--output-format") + 1], "json")
                self.assertIn("--effort", cmd_w)
                self.assertEqual(cmd_w[cmd_w.index("--effort") + 1], "high")
                self.assertIn("--disable-slash-commands", cmd_w)
                self.assertIn("--print-timeout", cmd_w)
                self.assertEqual(cmd_w[cmd_w.index("--print-timeout") + 1], "180s")
                self.assertEqual(cmd_w[cmd_w.index("--model") + 1], agent_cli.resolve_model("agy"))
                add_dirs = [cmd_w[i + 1] for i, tok in enumerate(cmd_w) if tok == "--add-dir"]
                self.assertIn(str(ws.resolve()), add_dirs)
                self.assertIn(str(extra.resolve()), add_dirs)

                # 2) write=False with attachment
                out_ro = agent_cli.run_agent(
                    "Listen to the clip.",
                    provider="agy",
                    workspace=ws,
                    write=False,
                    attachments=[clip],
                    json_schema={"type": "object"},
                )
                self.assertEqual(out_ro, '{"ok": true}')
                cmd_r, cwd_r = captured[-1]
                self.assertNotEqual(Path(cwd_r).resolve(), ws.resolve())
                self.assertNotIn("--mode", cmd_r)
                prompt_ro = cmd_r[cmd_r.index("-p") + 1]
                self.assertIn("Use your file viewing tool only", prompt_ro)
                add_dirs_r = [cmd_r[i + 1] for i, tok in enumerate(cmd_r) if tok == "--add-dir"]
                self.assertIn(str(att_dir.resolve()), add_dirs_r)

    def test_claude_write_tools_and_strip_code_fences_and_legacy_call(self) -> None:
        self.assertIn("Bash(python3 -B:*)", agent_cli.CLAUDE_WRITE_TOOLS)
        self.assertEqual(agent_cli.PROVIDERS, ("codex", "claude", "agy", "gemini"))
        self.assertEqual(agent_cli.AGY_TIERS["strong"], "gemini-4-neon-high")

        wrapped = 'Sure, here is the JSON:\n```json\n{"scenes": [1, 2]}\n```\nHope that helps!'
        self.assertEqual(agent_cli.strip_code_fences(wrapped), '{"scenes": [1, 2]}')

        with mock.patch("agent_cli._require", return_value="/usr/local/bin/claude"), mock.patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess([], 0, stdout="done", stderr=""),
        ) as m_run:
            with tempfile.TemporaryDirectory() as tmp:
                res = agent_cli.run_agent(
                    "claude", "Update files", Path(tmp), None, True
                )
                self.assertEqual(res, "done")
                cmd = m_run.call_args.args[0]
                self.assertIn("Bash(python3 -B:*)", cmd)
                self.assertIn("--disable-slash-commands", cmd)


class TestAsrGeminiWindows(unittest.TestCase):
    def test_union_includes_whisper_only_and_structured_parsing(self) -> None:
        ref_tracks = {
            "1-gm": {
                "audio_file": "/tmp/1-gm.flac",
                "words": [
                    {"s": 10.0, "e": 10.5, "w": "Roll", "p": 0.9},
                    {"s": 10.5, "e": 11.0, "w": "fourteen", "p": 0.35},
                ],
                "segments": [{"s": 10.0, "e": 11.0, "text": "Roll fourteen"}],
            },
            "2-nyx": {
                "audio_file": "/tmp/2-nyx.flac",
                "words": [],
                "segments": [],
            },
        }
        alt_tracks = {
            "1-gm": {
                "audio_file": "/tmp/1-gm.flac",
                "words": [
                    {"s": 10.0, "e": 10.5, "w": "Roll", "p": 0.9},
                    {"s": 10.5, "e": 11.0, "w": "14", "p": 0.9},
                ],
                "segments": [{"s": 10.0, "e": 11.0, "text": "Roll 14"}],
            },
            "2-nyx": {
                "audio_file": "/tmp/2-nyx.flac",
                "words": [
                    {"s": 11.2, "e": 11.6, "w": "Nat", "p": 0.8},
                    {"s": 11.6, "e": 12.0, "w": "20!", "p": 0.8},
                ],
                "segments": [{"s": 11.2, "e": 12.0, "text": "Nat 20!"}],
            },
        }
        # Number words normalize before diffing
        self.assertEqual(asr_gemini_windows.tokens("Roll fourteen"), asr_gemini_windows.tokens("Roll 14"))

        pool = asr_gemini_windows.collect_union_segments(
            ref_tracks, alt_tracks, lambda t: "GM" if "gm" in t else "Nyx"
        )
        self.assertEqual(len(pool), 2)
        self.assertEqual(pool[1]["origin"], "alt_only")
        self.assertEqual(pool[1]["alt_text"], "Nat 20!")

        selected = asr_gemini_windows.select_segments(pool, alt_tracks, threshold=0.25, low_conf_threshold=0.50)
        self.assertEqual(len(selected), 2)
        self.assertIn("low_conf", selected[0]["reasons"])
        self.assertIn("dice_number", selected[0]["reasons"])
        self.assertIn("one_sided_alt", selected[1]["reasons"])

        # Prompt includes candidate readings & concurrent overlapping speakers
        prompt = asr_gemini_windows.block_prompt("block.ogg", selected, pool, ["Ellara", "Nyx"], "hints")
        self.assertIn("Primary ASR:", prompt)
        self.assertIn("Alt ASR:", prompt)
        self.assertIn("Concurrent OTHER speakers", prompt)

        # Structured reply parsing handles mic_bleed & speech independently without dropping block
        reply = json.dumps({
            "segments": [
                {"idx": 1, "status": "mic_bleed", "text": "", "source": "none"},
                {"idx": 2, "status": "speech", "text": "Nat 20!", "source": "alt"},
            ]
        })
        verdicts = asr_gemini_windows.parse_structured_reply(selected, reply)
        self.assertEqual(len(verdicts), 2)
        self.assertEqual(verdicts[selected[0]["idx"]]["status"], "mic_bleed")
        self.assertEqual(verdicts[selected[1]["idx"]]["status"], "speech")
        self.assertEqual(verdicts[selected[1]["idx"]]["text"], "Nat 20!")


class TestDdbRollsAndNotesAndFacts(unittest.TestCase):
    def test_ddb_multi_roll_formatting_and_keyword_weighted_alignment(self) -> None:
        raw_rec = {
            "id": "r1",
            "eventType": "dice/roll/fulfilled",
            "dateTime": "2026-10-11T19:00:00Z",
            "data": {
                "context": {"name": "Nyx"},
                "action": "Longbow",
                "rolls": [
                    {"rollType": "to hit", "result": {"total": 18, "values": [12], "text": "12+6"}, "diceNotation": {"set": [{"dieType": "d20"}]}},
                    {"rollType": "damage", "result": {"total": 9, "values": [5], "text": "5+4"}, "diceNotation": {"set": [{"dieType": "d8"}]}},
                ],
            },
        }
        norm = ddb_rolls.normalize_record(raw_rec)
        assert norm is not None
        self.assertEqual(norm["total"], [18, 9])
        self.assertEqual(norm["total_display"], "18, 9")

        # Keyword-weighted offset estimation picks the true offset even with noisy casual numbers
        base_epoch = 1_760_000_000.0
        rolls = []
        lines = []
        for i in range(6):
            wall_t = base_epoch + 100.0 + i * 60.0
            val = 14 + i
            rolls.append({
                "wall_time": ddb_rolls.datetime.fromtimestamp(wall_t, tz=ddb_rolls.timezone.utc).isoformat(),
                "character": "Nyx",
                "action": "Stealth",
                "roll_type": "check",
                "total": val,
                "naturals": [val - 4],
            })
            # True offset is base_epoch (audio time = 100 + i*60) with roll keywords
            lines.append({"start": 100.0 + i * 60.0, "end": 102.0 + i * 60.0, "speaker": "Nyx", "text": f"I rolled {val} for stealth check"})
            # Distractor offset (+500s) with no roll keywords
            lines.append({"start": 600.0 + i * 60.0, "end": 602.0 + i * 60.0, "speaker": "Nyx", "text": f"maybe {val} apples"})
        offset, stats = ddb_rolls.estimate_offset(rolls, lines, bin_seconds=3.0)
        self.assertIsNotNone(offset)
        assert offset is not None
        self.assertAlmostEqual(offset, base_epoch, delta=2.0)
        self.assertTrue(stats["confident"])

    def test_raw_notes_review_queue_split_and_audit_dice_coverage(self) -> None:
        raw = "# Ignored heading\nnyx sneaks in.\nreview-name: meridin | Meri or Berridin?\n"
        clean, reviews = raw_notes_auto.split_review_lines(raw)
        self.assertEqual(clean, "nyx sneaks in.")
        self.assertEqual(reviews, ["meridin | Meri or Berridin?"])

        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            (work / "scene_01.md").write_text("nyx stealth 22, sneaks past guard.\n", encoding="utf-8")
            lines = [
                {"n": 1, "time": "00:01:00", "speaker": "DICE", "text": "Nyx rolled Stealth check: 22"},
                {"n": 2, "time": "00:01:30", "speaker": "DICE", "text": "Berridin rolled Perception check: 17"},
            ]
            scenes = [{"start": 1, "end": 2, "kind": "play", "title": "Gate", "summary": ""}]
            cov = audit_raw_notes.check_dice_coverage(lines, scenes, work)
            self.assertEqual(cov["total_play_rolls"], 2)
            self.assertEqual(cov["covered"], 1)
            self.assertEqual(len(cov["missing"]), 1)
            self.assertIn("17", cov["missing"][0]["dice_text"])

            # Adjacent context markers present
            lines_ext = [
                {"n": 1, "time": "00:00:10", "speaker": "GM", "text": "Before"},
                {"n": 2, "time": "00:01:00", "speaker": "Nyx", "text": "Inside"},
                {"n": 3, "time": "00:02:00", "speaker": "GM", "text": "After"},
            ]
            rendered = audit_raw_notes.scene_transcript(lines_ext, {"start": 2, "end": 2}, context_lines=1)
            self.assertIn("=== EARLIER CONTEXT ===", rendered)
            self.assertIn("=== SCENE START ===", rendered)
            self.assertIn("=== LATER CONTEXT ===", rendered)

    def test_session_facts_mid_session_scheduling_and_macos_env(self) -> None:
        transcript = [f"L{i}: regular gameplay line" for i in range(250)]
        transcript[100] = "GM: Quick break — are we playing next Sunday November 1st?"
        excerpt = session_facts.build_scheduling_excerpt(transcript, head_lines=20, tail_lines=30)
        self.assertTrue(any("November 1st" in line for line in excerpt))

        if platform.system() == "Darwin":
            env = run_asr_engines.runtime_env(Path(sys.executable))
            self.assertEqual(env.get("PYTHONDONTWRITEBYTECODE"), "1")
            device, compute = asr_whisper.resolve_device_and_compute("auto", "auto")
            self.assertEqual((device, compute), ("cpu", "int8"))


if __name__ == "__main__":
    unittest.main()
