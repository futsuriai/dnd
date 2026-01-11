Goal:
Fix the transcript using ONLY the provided Canonical Spelling List as the source of truth for proper nouns / special terms (names, places, organizations, jargon, etc.). The transcript may contain misspellings, spacing differences, casing differences, partial words, and phonetic approximations of these canonical terms.

Rules:
1) Only change text when you are confident it refers to an item in the Canonical Spelling List.
2) Prefer minimal edits: keep punctuation, line breaks, and non-term wording exactly as-is.
3) Do NOT “improve writing style.” Do NOT paraphrase.
4) Do NOT invent new canonical terms. If something seems like it should be a term but is not in the list, leave it unchanged and flag it as "unknown_term_candidate".
5) If multiple canonical terms could match, choose the one that best fits local context; if still ambiguous, do not change it—flag as "ambiguous".
6) Preserve the original language/script (e.g., keep Japanese text Japanese). Only correct the specific matched term (and its immediate spacing/casing) as needed.

How to decide a match (use both):
- Similarity: spelling closeness (typos, missing letters, swapped letters, spacing, hyphens).
- Context: surrounding words should make sense with the chosen canonical term.

Output format (STRICT):
Return JSON with:
- "corrected_transcript": the full corrected transcript as a single string
- "changes": array of objects with:
   - "original": exact substring from the transcript
   - "replacement": canonical form used
   - "reason": one of ["typo","spacing","casing","hyphenation","phonetic","partial_match","context_disambiguation"]
   - "confidence": number 0.00-1.00
- "flags": array of objects with:
   - "text": exact substring
   - "type": one of ["ambiguous","unknown_term_candidate"]
   - "note": short explanation

Canonical Spelling List (one per line):
@ENTITY_LIST.md

Transcript:
**Raw Transcript**: A text file containing the dialogue (e.g., `src/assets/sessions/transcripts/session_N_raw.txt`).
