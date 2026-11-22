#!/usr/bin/env python3
"""Unit tests for pipeline_paths, run_session_auto, run_ellara_analysis_agent, validators, and ellara delta checks."""

from __future__ import annotations

import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

TRANSCRIPTION_DIR = Path(__file__).resolve().parent
DND_ROOT = TRANSCRIPTION_DIR.parent.parent
if str(TRANSCRIPTION_DIR) not in sys.path:
    sys.path.insert(0, str(TRANSCRIPTION_DIR))

import cleanup_session_artifacts  # noqa: E402
import pipeline_paths  # noqa: E402
import run_ellara_analysis_agent  # noqa: E402
import run_session_auto  # noqa: E402
import run_session_notes_agent  # noqa: E402
import run_website_sync_agent  # noqa: E402
import validate_raw_notes  # noqa: E402
import validate_session_pipeline  # noqa: E402


def _load_ellara_delta_module():
    candidates = [
        Path("/Users/farahfariz/source/ellara/.agents/skills/ellara-session-analysis/scripts/check_session_delta.py"),
        pipeline_paths.resolve_ellara_dir()
        / ".agents"
        / "skills"
        / "ellara-session-analysis"
        / "scripts"
        / "check_session_delta.py",
    ]
    script_path = next((p for p in candidates if p.is_file()), None)
    if script_path is None:
        return None
    spec = importlib.util.spec_from_file_location("check_session_delta_under_test", script_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _create_fixture_repos(root: Path, session: int = 21) -> tuple[Path, Path]:
    """Build minimal valid sister dnd and ellara repositories in a temp directory."""
    dnd = root / "dnd"
    ellara = root / "ellara"

    (dnd / "src" / "assets" / "sessions").mkdir(parents=True)
    (dnd / "src" / "store").mkdir(parents=True)
    (dnd / "src" / "views").mkdir(parents=True)
    (dnd / "scripts" / "transcription").mkdir(parents=True)

    (ellara / "Session Notes" / "Transcripts").mkdir(parents=True)
    (ellara / "Ellara" / "Campaign State" / "Session Briefs").mkdir(parents=True)
    (ellara / "Ellara" / "Spirit").mkdir(parents=True)
    (ellara / ".agents" / "skills" / "ellara-session-analysis" / "scripts").mkdir(parents=True)

    # Copy shared rules and real check_session_delta.py if available
    rules_src = DND_ROOT / "scripts" / "shared_sync_rules.json"
    (dnd / "scripts" / "shared_sync_rules.json").write_text(
        rules_src.read_text(encoding="utf-8"), encoding="utf-8"
    )
    ellara_delta_src = Path(
        "/Users/farahfariz/source/ellara/.agents/skills/ellara-session-analysis/scripts/check_session_delta.py"
    )
    if ellara_delta_src.is_file():
        (
            ellara / ".agents" / "skills" / "ellara-session-analysis" / "scripts" / "check_session_delta.py"
        ).write_text(ellara_delta_src.read_text(encoding="utf-8"), encoding="utf-8")

    polished = (
        f"# Session {session} — *The Lives Within the Light*\n\n"
        f"**Locales:** Bastion City\n"
        f"**Time:** Day 3\n\n"
        f"---\n\n"
        f"## 1) Opening\n\n"
        f"Ellara and Nyx reviewed the crystal.\n"
    )
    raw = (
        'nyx: "we need to check the crystal"\n'
        'ellara: "the light is for everybody"\n'
        'witty: "it is artificial"\n'
        'ysidor: "we honor the fallen"\n'
        'berridin: "i paid the loan"\n'
        'nyx: "another crystal is coming"\n'
        'ellara: "i am staying for now"\n'
        'witty: "i will apply to the lighthouse"\n'
        "Ellara stayed with the party.\n"
    )
    transcript = "[00:01:02] Ellara: The light is for everybody.\n"

    (ellara / "Session Notes" / f"Session {session}.md").write_text(polished, encoding="utf-8")
    (ellara / "Session Notes" / f"Raw Session {session}.md").write_text(raw, encoding="utf-8")
    (ellara / "Session Notes" / "Transcripts" / f"Transcript Session {session}.txt").write_text(
        transcript, encoding="utf-8"
    )
    (dnd / "src" / "assets" / "sessions" / f"session-{session}.md").write_text(polished, encoding="utf-8")

    (dnd / "src" / "store" / "sessions.js").write_text(
        f"""export const sessions = [
  {{
    id: 'session-{session + 1}',
    title: 'Session {session + 1}',
    subtitle: 'Change It from Within',
    location: 'Bastion City',
    date: 'November 1, 2026',
    upcoming: true,
    description: 'Witty applies to the Duskbreaker Lighthouse.',
    highlights: [],
  }},
  {{
    id: 'session-{session}',
    title: 'Session {session}',
    subtitle: 'The Lives Within the Light',
    location: 'Bastion City',
    date: 'October 11, 2026',
    upcoming: false,
    summaryFile: 'session-{session}.md',
    description: 'The party inspects the crystal and commits to stopping the experiments.',
    highlights: [
      "Witty identifies the titan's crystal as artificial.",
      "Ellara meets Proctor Eduard and returns to the party."
    ],
    homeRecap: 'Witty confirmed the crystal is artificial.',
    nextSteps: ['Prepare Witty for the Lighthouse application.'],
    storyBeat: 'At the estate, Witty uncovered the crystal matrix.',
  }},
];
""",
        encoding="utf-8",
    )
    (dnd / "src" / "store" / "locations.js").write_text(
        f"export const locations = [{{ id: 'bastion-city', name: 'Bastion City', history: [{{ session: {session}, note: 'Party regrouped.' }}] }}];\n",
        encoding="utf-8",
    )
    (dnd / "src" / "store" / "lore.js").write_text("export const lore = [];\n", encoding="utf-8")
    (dnd / "src" / "store" / "npcs.js").write_text("export const npcs = [];\n", encoding="utf-8")
    (dnd / "src" / "views" / "HomeView.vue").write_text("<template><div /></template>\n", encoding="utf-8")
    (dnd / "src" / "views" / "StorySoFarView.vue").write_text("<template><div /></template>\n", encoding="utf-8")
    (dnd / "scripts" / "transcription" / "entity_metadata.json").write_text("[]\n", encoding="utf-8")

    (ellara / "Ellara" / "Ellara.md").write_text("# Ellara\n", encoding="utf-8")
    (ellara / "Ellara" / "Spirit" / "Spirit.md").write_text("# Spirit\n", encoding="utf-8")
    (ellara / "Ellara" / "Campaign State" / "Ellara Current State.md").write_text(
        f"""---
last_analyzed_session: {session}
next_session: {session + 1}
next_session_title: "Change It from Within"
campaign_year: "651 AE"
character_level: 5
current_location: "Bastion City"
---

# Ellara Current State

See [[Ellara]], [[Spirit]], and [[Session {session}]].
""",
        encoding="utf-8",
    )
    (ellara / "Ellara" / "Campaign State" / "Ellara Threads and Callbacks.md").write_text(
        f"# Threads\n\nSee [[Ellara Current State]] and [[Session {session} Analysis]].\n",
        encoding="utf-8",
    )
    (ellara / "Ellara" / "Campaign State" / "Knowledge Boundary and Dramatic Irony.md").write_text(
        "# Knowledge Boundary\n\nSee [[Ellara Current State]].\n",
        encoding="utf-8",
    )
    (ellara / "Ellara" / "Campaign State" / "Session Briefs" / f"Session {session} Analysis.md").write_text(
        f"""---
session: {session}
title: "The Lives Within the Light"
date_analyzed: "2026-11-22"
sources:
  - "Session Notes/Session {session}.md"
---

# Session {session} Analysis

Links to [[Ellara Current State]].
""",
        encoding="utf-8",
    )
    return dnd, ellara


class TestPipelinePaths(unittest.TestCase):
    def test_contract_exports_and_resolution(self):
        self.assertEqual(pipeline_paths.TRANSCRIPTION_DIR, TRANSCRIPTION_DIR)
        self.assertEqual(pipeline_paths.DND_DIR, DND_ROOT)
        self.assertTrue(isinstance(pipeline_paths.ELLARA_DIR, Path))
        self.assertTrue(isinstance(pipeline_paths.VENV_PYTHON, Path))

        with tempfile.TemporaryDirectory() as td:
            custom = Path(td) / "custom-ellara"
            with mock.patch.dict(os.environ, {"ELLARA_ROOT": str(custom)}, clear=False):
                self.assertEqual(pipeline_paths.resolve_ellara_dir(), custom.resolve())
                override = Path(td) / "override-ellara"
                self.assertEqual(pipeline_paths.resolve_ellara_dir(override), override.resolve())

            with mock.patch.dict(os.environ, {}, clear=False):
                os.environ.pop("ELLARA_ROOT", None)
                self.assertEqual(
                    pipeline_paths.resolve_ellara_dir(),
                    (pipeline_paths.DND_DIR.parent / "ellara").resolve(),
                )

    def test_no_bytecode_env(self):
        env = pipeline_paths.no_bytecode_env({"CUSTOM_KEY": "1"})
        self.assertEqual(env["PYTHONDONTWRITEBYTECODE"], "1")
        self.assertEqual(env["CUSTOM_KEY"], "1")

    def test_call_agent_supports_legacy_and_upgraded_signatures(self):
        class LegacyAgent:
            called = None

            @classmethod
            def run_agent(cls, provider, prompt, workspace, model=None, write=False):
                cls.called = (provider, prompt, workspace, model, write)
                return "legacy-ok"

        class UpgradedAgent:
            called = None

            @classmethod
            def run_agent(
                cls,
                prompt,
                *,
                provider="codex",
                model=None,
                workspace=None,
                write=False,
                extra_dirs=None,
                extra_allowed_tools=None,
                timeout=300,
                retries=1,
                disable_slash_commands=True,
            ):
                cls.called = (provider, prompt, workspace, model, write, extra_dirs, extra_allowed_tools, timeout)
                return "upgraded-ok"

        res1 = pipeline_paths.call_agent(
            LegacyAgent,
            prompt="hello",
            provider="agy",
            model="gemini-4-neon-medium",
            workspace=Path("/tmp"),
            write=True,
            extra_dirs=[Path("/var")],
        )
        self.assertEqual(res1, "legacy-ok")
        self.assertEqual(LegacyAgent.called, ("agy", "hello", Path("/tmp"), "gemini-4-neon-medium", True))

        res2 = pipeline_paths.call_agent(
            UpgradedAgent,
            prompt="hello",
            provider="agy",
            model="gemini-4-neon-high",
            workspace=Path("/tmp"),
            write=True,
            extra_dirs=[Path("/var")],
            extra_allowed_tools=["Bash(python3 -B:*)"],
            timeout=600,
        )
        self.assertEqual(res2, "upgraded-ok")
        self.assertEqual(
            UpgradedAgent.called,
            ("agy", "hello", Path("/tmp"), "gemini-4-neon-high", True, [Path("/var")], ["Bash(python3 -B:*)"], 600),
        )


class TestSharedSyncRules(unittest.TestCase):
    def test_shared_rules_json_valid_and_compiles(self):
        rules_path = DND_ROOT / "scripts" / "shared_sync_rules.json"
        self.assertTrue(rules_path.is_file())
        data = json.loads(rules_path.read_text(encoding="utf-8"))
        self.assertIn("badPublicPatterns", data)
        self.assertIn("sessionSpecificRules", data)
        self.assertIn("17", data["sessionSpecificRules"])
        for rule in data["badPublicPatterns"]:
            flags = re.IGNORECASE if "i" in rule.get("flags", "") else 0
            re.compile(rule["pattern"], flags)
            self.assertTrue(rule["message"])
        for rules in data["sessionSpecificRules"].values():
            for rule in rules:
                flags = re.IGNORECASE if "i" in rule.get("flags", "") else 0
                re.compile(rule["pattern"], flags)


class TestRunSessionAuto(unittest.TestCase):
    def test_stage_dag_contains_ellara_state_between_website_and_verify(self):
        self.assertEqual(
            run_session_auto.STAGES,
            [
                "entities",
                "asr",
                "gemini",
                "transcript",
                "dice",
                "fuse",
                "diagnostics",
                "raw-notes",
                "audit",
                "notes",
                "website",
                "ellara-state",
                "verify",
                "publish",
            ],
        )

    def test_no_cross_provider_model_leak(self):
        # Default provider codex + --model gpt-5.4; website overridden to claude -> model must NOT leak!
        prov, mod = run_session_auto.resolve_stage_provider_and_model("claude", None, "codex", "gpt-5.4")
        self.assertEqual((prov, mod), ("claude", None))

        # Explicit stage model always wins
        prov, mod = run_session_auto.resolve_stage_provider_and_model(
            "claude", "claude-opus-5-5", "codex", "gpt-5.4"
        )
        self.assertEqual((prov, mod), ("claude", "claude-opus-5-5"))

        # Same provider inherits default --model
        prov, mod = run_session_auto.resolve_stage_provider_and_model(
            None, None, "agy", "gemini-4-neon-high"
        )
        self.assertEqual((prov, mod), ("agy", "gemini-4-neon-high"))

    def test_dry_run_outputs_json_plan_without_mutating(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            audio = root / "session-22"
            audio.mkdir()
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = run_session_auto.main(
                    [
                        "--session",
                        "22",
                        "--audio-dir",
                        str(audio),
                        "--dnd-dir",
                        str(root / "dnd"),
                        "--ellara-root",
                        str(root / "ellara"),
                        "--provider",
                        "agy",
                        "--website-provider",
                        "claude",
                        "--model",
                        "gemini-4-neon-high",
                        "--dry-run",
                    ]
                )
            self.assertEqual(rc, 0)
            plan = json.loads(buf.getvalue())
            self.assertIn("ellara-state", plan["stages"])
            self.assertEqual(plan["providers"]["notes"]["model"], "gemini-4-neon-high")
            self.assertEqual(plan["providers"]["website"]["provider"], "claude")
            self.assertIsNone(plan["providers"]["website"]["model"])
            self.assertFalse((audio / "pipeline" / "manifest.json").exists())

    def test_pre_fuse_snapshot_and_restore_idempotency(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            txt = root / "Transcript Session 22.txt"
            jsonl = root / "Transcript Session 22.lines.jsonl"
            pre_txt = root / "pre_fuse.txt"
            pre_jsonl = root / "pre_fuse.lines.jsonl"

            txt.write_text("[00:00:01] Ellara: original\n", encoding="utf-8")
            jsonl.write_text('{"id":"L1","text":"original"}\n', encoding="utf-8")

            # First fuse prepares snapshot
            run_session_auto.prepare_fuse_input(txt, jsonl, pre_txt, pre_jsonl)
            self.assertEqual(pre_jsonl.read_text(encoding="utf-8"), '{"id":"L1","text":"original"}\n')

            # Simulate fuse mutating files in place
            txt.write_text("[00:00:01] Ellara: mutated\n", encoding="utf-8")
            jsonl.write_text('{"id":"L1","text":"mutated"}\n', encoding="utf-8")

            # Second `--only fuse` restores unfused snapshot!
            run_session_auto.prepare_fuse_input(txt, jsonl, pre_txt, pre_jsonl)
            self.assertEqual(txt.read_text(encoding="utf-8"), "[00:00:01] Ellara: original\n")
            self.assertEqual(jsonl.read_text(encoding="utf-8"), '{"id":"L1","text":"original"}\n')

    def test_verify_fails_when_any_validator_fails_and_records_failed_status(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            dnd, ellara = _create_fixture_repos(root, session=21)
            audio = root / "audio"
            audio.mkdir()

            def fake_subproc(cmd, cwd=None, env=None, check=False):
                joined = " ".join(str(c) for c in cmd)
                # sync_check passes (0), raw_notes passes (0), pipeline passes (0), ellara_state FAILS (1)!
                if "check_session_delta.py" in joined:
                    return mock.Mock(returncode=1)
                return mock.Mock(returncode=0)

            with mock.patch.object(subprocess, "run", side_effect=fake_subproc):
                with self.assertRaises(SystemExit) as ctx:
                    run_session_auto.main(
                        [
                            "--session",
                            "21",
                            "--audio-dir",
                            str(audio),
                            "--dnd-dir",
                            str(dnd),
                            "--ellara-root",
                            str(ellara),
                            "--only",
                            "verify",
                        ]
                    )
                self.assertIn("ellara_state", str(ctx.exception))

            manifest = json.loads((audio / "pipeline" / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["stages"]["verify"]["status"], "failed")
            self.assertEqual(manifest["stages"]["verify"]["failed"], ["ellara_state"])

    def test_skipped_stage_records_skipped_status_in_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            dnd, ellara = _create_fixture_repos(root, session=21)
            audio = root / "audio"
            audio.mkdir()

            rc = run_session_auto.main(
                [
                    "--session",
                    "21",
                    "--audio-dir",
                    str(audio),
                    "--dnd-dir",
                    str(dnd),
                    "--ellara-root",
                    str(ellara),
                    "--only",
                    "ellara-state",
                    "--no-ellara",
                ]
            )
            self.assertEqual(rc, 0)
            manifest = json.loads((audio / "pipeline" / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["stages"]["ellara-state"]["status"], "skipped")

    def test_publish_stages_explicit_files_only_and_never_unrelated_dirty_files(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            dnd, ellara = _create_fixture_repos(root, session=21)
            # Create unrelated dirty file in dnd/src/
            (dnd / "src" / "unrelated_scratch.js").write_text("// dirty\n", encoding="utf-8")

            ellara_files, dnd_files = run_session_auto.collect_publish_files("21", dnd, ellara)
            ellara_rels = {str(p.relative_to(ellara)) for p in ellara_files}
            dnd_rels = {str(p.relative_to(dnd)) for p in dnd_files}

            self.assertIn("Session Notes/Session 21.md", ellara_rels)
            self.assertIn("Session Notes/Raw Session 21.md", ellara_rels)
            self.assertIn("Session Notes/Transcripts/Transcript Session 21.txt", ellara_rels)
            self.assertIn("Ellara/Campaign State/Ellara Current State.md", ellara_rels)
            self.assertIn("Ellara/Campaign State/Session Briefs/Session 21 Analysis.md", ellara_rels)

            self.assertIn("src/assets/sessions/session-21.md", dnd_rels)
            self.assertIn("src/store/sessions.js", dnd_rels)
            self.assertNotIn("src/unrelated_scratch.js", dnd_rels)

            # Verify git_stage_and_commit skips commit when diff --cached --quiet exits 0
            calls = []

            def fake_run(cmd, cwd=None, check=True):
                calls.append(cmd)
                if "diff" in cmd and "--cached" in cmd:
                    return 0
                return 0

            committed = run_session_auto.git_stage_and_commit(dnd, dnd_files, "Publish Session 21", fake_run)
            self.assertFalse(committed)
            self.assertFalse(any("commit" in c for c in calls))


class TestRunEllaraAnalysisAgent(unittest.TestCase):
    def test_parity_check_modes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            dnd, ellara = _create_fixture_repos(root, session=21)

            # Identical -> ok
            res = run_ellara_analysis_agent.check_session_note_parity(21, dnd, ellara)
            self.assertEqual(res, ellara / "Session Notes" / "Session 21.md")

            # Differing without --prefer -> fails fast
            (dnd / "src" / "assets" / "sessions" / "session-21.md").write_text("edited in dnd\n", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                run_ellara_analysis_agent.check_session_note_parity(21, dnd, ellara)

            # With --prefer dnd --sync-from-dnd -> overwrites ellara
            res = run_ellara_analysis_agent.check_session_note_parity(
                21, dnd, ellara, sync_from_dnd=True, prefer="dnd"
            )
            self.assertEqual(res, dnd / "src" / "assets" / "sessions" / "session-21.md")
            self.assertEqual((ellara / "Session Notes" / "Session 21.md").read_text(encoding="utf-8"), "edited in dnd\n")

            # Missing ellara note + --sync-from-dnd -> copies from dnd
            (ellara / "Session Notes" / "Session 21.md").unlink()
            res = run_ellara_analysis_agent.check_session_note_parity(21, dnd, ellara, sync_from_dnd=True)
            self.assertEqual(res, ellara / "Session Notes" / "Session 21.md")
            self.assertTrue((ellara / "Session Notes" / "Session 21.md").is_file())

    def test_idempotent_skip_when_already_analyzed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            dnd, ellara = _create_fixture_repos(root, session=21)
            with mock.patch.object(run_ellara_analysis_agent.pipeline_paths, "call_agent") as mocked_agent:
                rc = run_ellara_analysis_agent.main(
                    [
                        "--session",
                        "21",
                        "--dnd-dir",
                        str(dnd),
                        "--ellara-root",
                        str(ellara),
                    ]
                )
            self.assertEqual(rc, 0)
            mocked_agent.assert_not_called()

    def test_full_mocked_run_invokes_analysis_audit_and_saves_brief(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            dnd, ellara = _create_fixture_repos(root, session=21)
            brief_out = root / "prep_brief.md"
            with mock.patch.object(
                run_ellara_analysis_agent.pipeline_paths,
                "call_agent",
                side_effect=["## Prep Brief\nStay sharp.", "No IC/OOC or quote defects found."],
            ) as mocked_agent:
                rc = run_ellara_analysis_agent.main(
                    [
                        "--session",
                        "21",
                        "--dnd-dir",
                        str(dnd),
                        "--ellara-root",
                        str(ellara),
                        "--provider",
                        "agy",
                        "--force",
                        "--brief-out",
                        str(brief_out),
                    ]
                )
            self.assertEqual(rc, 0)
            self.assertEqual(mocked_agent.call_count, 2)
            first_kwargs = mocked_agent.call_args_list[0].kwargs
            self.assertTrue(first_kwargs["write"])
            self.assertEqual(first_kwargs["workspace"], ellara.resolve())
            self.assertEqual(first_kwargs["extra_dirs"], [dnd.resolve()])
            self.assertIn("Stay sharp.", brief_out.read_text(encoding="utf-8"))


class TestSessionNotesAndWebsiteAgents(unittest.TestCase):
    def test_session_notes_post_generation_validation(self):
        good = (
            "# Session 22 — *Change It from Within*\n\n"
            "**Locales:** Bastion City\n"
            "**Time:** Day 4\n\n"
            "---\n\n"
            "## 1) Opening\n\n"
            "Ellara spoke with Ysidor about Nites and Hýr.\n"
        )
        self.assertEqual(run_session_notes_agent.validate_generated_notes("22", good), [])

        bad = "# Session 22 — *Oops*\n[00:01:02] Ellara: Nytes and Marie.\n"
        errors = run_session_notes_agent.validate_generated_notes("22", bad)
        joined = "\n".join(errors)
        self.assertIn("**Locales:**", joined)
        self.assertIn("**Time:**", joined)
        self.assertIn("## 1)", joined)
        self.assertIn("timestamp", joined)
        self.assertIn("Nites", joined)
        self.assertIn("Meri", joined)

    def test_website_sync_bidirectional_parity_guard_and_prompt(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "Session 22.md"
            tgt = root / "session-22.md"
            src.write_text("ellara version\n", encoding="utf-8")
            tgt.write_text("dnd version\n", encoding="utf-8")

            with self.assertRaises(RuntimeError):
                run_website_sync_agent.sync_session_markdown(src, tgt)

            self.assertEqual(
                run_website_sync_agent.sync_session_markdown(src, tgt, prefer="dnd"),
                "kept_dnd",
            )
            self.assertEqual(tgt.read_text(encoding="utf-8"), "dnd version\n")

            self.assertEqual(
                run_website_sync_agent.sync_session_markdown(src, tgt, prefer="ellara"),
                "copied",
            )
            self.assertEqual(tgt.read_text(encoding="utf-8"), "ellara version\n")

        prompt = run_website_sync_agent.build_prompt(22, "November 1, 2026", "November 15, 2026")
        self.assertIn("MODE: autofix", prompt)
        self.assertIn("homeRecap", prompt)
        self.assertIn("nextSteps", prompt)
        self.assertIn("storyBeat", prompt)
        self.assertIn("Witty", prompt)
        self.assertIn("Do NOT manually edit `src/views/HomeView.vue`", prompt)


class TestValidatorsAndCleanup(unittest.TestCase):
    def test_validate_session_pipeline_double_quoted_highlights_and_shared_rules(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            dnd, ellara = _create_fixture_repos(root, session=21)
            rc = validate_session_pipeline.main(
                [
                    "--session",
                    "21",
                    "--dnd-dir",
                    str(dnd),
                    "--ellara-root",
                    str(ellara),
                    "--strict-clean",
                ]
            )
            self.assertEqual(rc, 0)

            # Stray Audit.md in ellara/Session Notes/ must fail --strict-clean and be collected by cleanup
            audit_leak = ellara / "Session Notes" / "Raw Session 21 - Audit.md"
            audit_leak.write_text("leak\n", encoding="utf-8")
            rc_dirty = validate_session_pipeline.main(
                [
                    "--session",
                    "21",
                    "--dnd-dir",
                    str(dnd),
                    "--ellara-root",
                    str(ellara),
                    "--strict-clean",
                ]
            )
            self.assertEqual(rc_dirty, 1)

            collected = cleanup_session_artifacts.collect_paths(21, dnd, ellara, None, False, False)
            self.assertIn(audit_leak, collected)
            self.assertNotIn(ellara / "Session Notes" / "Session 21.md", collected)

    def test_validate_raw_notes_uses_shared_rules(self):
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "Raw Session 17.md"
            raw.write_text(
                'nyx: "Nytes is wrong"\n'
                'ellara: "ok"\n'
                'witty: "ok"\n'
                'ysidor: "ok"\n'
                'berridin: "ok"\n'
                'nyx: "ok"\n'
                'ellara: "ok"\n'
                'witty: "ok"\n'
                "Berridin Arcana = nat 20\n",
                encoding="utf-8",
            )
            rc = validate_raw_notes.main([str(raw), "--session", "17"])
            self.assertEqual(rc, 1)


class TestEllaraDeltaValidator(unittest.TestCase):
    def test_find_dnd_store_changes_and_validate_invariants(self):
        delta_mod = _load_ellara_delta_module()
        if delta_mod is None:
            self.skipTest("ellara check_session_delta.py not found on disk")

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            dnd, ellara = _create_fixture_repos(root, session=21)

            # Add string-valued HomeView entry to verify improved detection
            (dnd / "src" / "views" / "HomeView.vue").write_text(
                "const HOME_RECAP_BY_SESSION = {\n  21: 'String recap entry.',\n};\n",
                encoding="utf-8",
            )
            changes = delta_mod.find_dnd_store_changes(dnd, since_session=20)
            self.assertIn("src/store/sessions.js", changes["stores"])
            self.assertIn("homeRecap", changes["stores"]["src/store/sessions.js"][0]["copy_fields"])
            self.assertIn("src/views/HomeView.vue", changes["views"])
            self.assertEqual(changes["views"]["src/views/HomeView.vue"], [21])

            # Baseline valid fixture passes
            res = delta_mod.validate_ellara_state(ellara, dnd, session=21)
            self.assertTrue(res["ok"], res["errors"])

            # Pre-existing Session Notes/Session 3/Session 3.md duplicate stem is ignored
            (ellara / "Session Notes" / "Session 3.md").write_text("# Session 3\n", encoding="utf-8")
            (ellara / "Session Notes" / "Session 3").mkdir()
            (ellara / "Session Notes" / "Session 3" / "Session 3.md").write_text("# Session 3\n", encoding="utf-8")
            self.assertTrue(delta_mod.validate_ellara_state(ellara, dnd, session=21)["ok"])

            # Broken WikiLink fails
            threads = ellara / "Ellara" / "Campaign State" / "Ellara Threads and Callbacks.md"
            orig_threads = threads.read_text(encoding="utf-8")
            threads.write_text(orig_threads + "\nBroken [[Nonexistent Vault Page]].\n", encoding="utf-8")
            res_bad_link = delta_mod.validate_ellara_state(ellara, dnd, session=21)
            self.assertFalse(res_bad_link["ok"])
            self.assertTrue(any("Nonexistent Vault Page" in e for e in res_bad_link["errors"]))
            threads.write_text(orig_threads, encoding="utf-8")

            # [PROVISIONAL] brief fails unless --allow-provisional
            brief = ellara / "Ellara" / "Campaign State" / "Session Briefs" / "Session 21 Analysis.md"
            orig_brief = brief.read_text(encoding="utf-8")
            brief.write_text(orig_brief + "\n[PROVISIONAL]\n", encoding="utf-8")
            self.assertFalse(delta_mod.validate_ellara_state(ellara, dnd, session=21)["ok"])
            self.assertTrue(
                delta_mod.validate_ellara_state(ellara, dnd, session=21, allow_provisional=True)["ok"]
            )
            brief.write_text(orig_brief, encoding="utf-8")

            # Stray __pycache__ fails
            cache_dir = ellara / ".agents" / "__pycache__"
            cache_dir.mkdir()
            res_cache = delta_mod.validate_ellara_state(ellara, dnd, session=21)
            self.assertFalse(res_cache["ok"])
            self.assertTrue(any("__pycache__" in e for e in res_cache["errors"]))


if __name__ == "__main__":
    unittest.main()
