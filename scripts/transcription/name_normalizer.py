"""Context-aware canonical-name normalization for ASR text.

`text_fixes` are unambiguous misspellings and are replaced everywhere.
`capitalized_only_fixes` are real words or names (Mary, Nick, Laura...) and
are replaced only when they appear capitalized and are not preceded by an
article, determiner, or honorific, so "a nick in the blade" or "the Baron"
survive untouched.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

DEFAULT_CORRECTIONS = Path(__file__).with_name("name_corrections.json")

BLOCKING_PREVIOUS_WORDS = {
    "a", "an", "the", "this", "that", "these", "those", "my", "your", "his",
    "her", "our", "their", "its", "some", "any", "every", "lord", "lady",
    "sir", "saint", "st", "mr", "mrs", "ms", "miss", "dear", "old", "little",
}


def _match_case(matched: str, replacement: str) -> str:
    if matched.isupper() and len(matched) > 1:
        return replacement.upper()
    if matched[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def _possessive(suffix: str, replacement: str) -> str:
    if not suffix or replacement.endswith("'s") or replacement.endswith("s'"):
        return ""
    return suffix


class NameNormalizer:
    def __init__(self, corrections_path: Path = DEFAULT_CORRECTIONS):
        data = json.loads(Path(corrections_path).read_text(encoding="utf-8"))
        self.text_fixes: dict[str, str] = data.get("text_fixes", {})
        self.capitalized_only: dict[str, str] = data.get("capitalized_only_fixes", {})
        self.context_hints: dict[str, str] = data.get("context_hints", {})
        self.aliases: dict[str, str] = data.get("aliases", {})
        self.speaker_label_fixes: dict[str, str] = data.get("speaker_label_fixes", {})

        self._always = [
            (
                re.compile(rf"(?<!\w)({re.escape(wrong)})((?:'s|s)?)(?!\w)", re.IGNORECASE),
                right,
            )
            for wrong, right in sorted(self.text_fixes.items(), key=lambda kv: len(kv[0]), reverse=True)
        ]
        self._capitalized = [
            (re.compile(rf"(?<!\w)({re.escape(wrong)})((?:'s)?)(?!\w)"), right)
            for wrong, right in sorted(self.capitalized_only.items(), key=lambda kv: len(kv[0]), reverse=True)
        ]

    def apply(self, text: str) -> tuple[str, list[tuple[str, str]]]:
        """Return normalized text and the list of (original, replacement) edits."""
        edits: list[tuple[str, str]] = []

        for pattern, right in self._always:
            def always(match: re.Match[str], right: str = right) -> str:
                new = _match_case(match.group(1), right) + _possessive(match.group(2), right)
                if new != match.group(0):
                    edits.append((match.group(0), new))
                return new

            text = pattern.sub(always, text)

        for pattern, right in self._capitalized:
            def capitalized(match: re.Match[str], right: str = right) -> str:
                before = match.string[: match.start()]
                previous = re.findall(r"[A-Za-z']+", before[-24:])
                if previous and previous[-1].lower() in BLOCKING_PREVIOUS_WORDS:
                    return match.group(0)
                new = right + _possessive(match.group(2), right)
                edits.append((match.group(0), new))
                return new

            text = pattern.sub(capitalized, text)

        return text, edits

    def normalize(self, text: str) -> str:
        return self.apply(text)[0]

    def llm_hint_block(self) -> str:
        """Short reference block for LLM prompts."""
        lines = ["Known ASR confusions and nicknames (do not apply blindly):"]
        for wrong, right in self.capitalized_only.items():
            lines.append(f"- \"{wrong}\" is often a mishearing of {right}")
        for term, hint in self.context_hints.items():
            lines.append(f"- {term}: {hint}")
        for alias, canonical in self.aliases.items():
            lines.append(f"- \"{alias}\" = {canonical}")
        return "\n".join(lines)
