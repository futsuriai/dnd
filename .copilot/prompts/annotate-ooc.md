# Transcript Annotation Instructions (IC vs OOC)

You are an expert roleplay analyst. Your task is to annotate a D&D session transcript to distinguish between In-Character (IC) dialogue and Out-of-Character (OOC) table talk.

## Inputs
1.  **Corrected Transcript**: The output from the correction step (e.g., `src/assets/sessions/transcripts/session_N_corrected.txt`).

## Task
Read the transcript and append a classification tag to the start of the text content for each line.

### Classification Rules

**[IC] (In-Character):**
*   The player is speaking *as* their character.
*   First-person statements about the world: "I draw my sword," "I ask him about the money."
*   Direct dialogue: "Hello, traveler, what brings you here?"
*   Internal monologue described by the player.

**[OOC] (Out-of-Character):**
*   Game mechanics: "Roll for initiative," "What's the DC?", "I got a 15."
*    clarifications: "Wait, did you say he was an elf?", "Is it night time?"
*   Table banter/jokes: "Wow, nice roll," "I need to get a snack."
*   Narrative declarations by the GM are usually [IC] unless clarifying a rule.

### Chunking
*   If the transcript is large, process it in manageable chunks (e.g., 50-100 lines) to maintain high-quality analysis. Append each annotated chunk to the final output.

### Format
**Original:**
`[00:10:45] Nyx: I walk over to the guard and say, "Let us in."`

**Annotated:**
`[00:10:45] Nyx: [IC] I walk over to the guard and say, "Let us in."`

**Original:**
`[00:10:50] Berridin: reckless attack, rolling with advantage.`

**Annotated:**
`[00:10:50] Berridin: [OOC] reckless attack, rolling with advantage.`

## Output Format
Save the result to `src/assets/sessions/transcripts/session_N_annotated.txt`.
