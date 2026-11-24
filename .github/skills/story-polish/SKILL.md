---
name: story-polish
description: Assess and polish an English story for a user-confirmed Reading A-Z (RAZ) level B through K and 12, 24, or 48 scenes (default 24). Check body word count, vocabulary, sentence complexity, and story quality before rewriting; preserve stories that already meet the bar. Use before scene-splitter when a story needs expansion, simplification, shortening, or reading-level adaptation.
---

# Story Polish

Prepare engaging English story prose for a confirmed reading level and scene
budget. This skill edits prose; `scene-splitter` later creates the canonical
scene JSON. Do not generate illustrations, audio, or published books here.

## Reading-level policy

Use the US Reading A-Z / Raz-Plus letter levels **B, C, D, E, F, G, H, I, J,
and K**. Ask for the target level before rewriting; never infer it from age,
grade, the source's length, or a previous story.

Word count alone does not establish a reading level. Assess vocabulary,
sentence structure, repetition, picture support, conceptual difficulty,
inference, and total reading load as well. Call the result a **RAZ-aligned
editorial estimate**, not an official placement or certified RAZ book. Do not
equate these letters with other publishers' leveling systems.

Reference: [Reading A-Z leveling criteria](https://www.readinga-z.com/learninga-z-levels/leveling-criteria/).
The budgets below are **this project's scene-planning guidelines**, not
publisher-prescribed word counts. Multiplying them by 24 or 48 can produce
books much longer than typical leveled readers, especially at B-D. Explicitly
flag that reading-stamina tradeoff at confirmation; do not claim that simple
sentences alone make a long book appropriate for an early reader. Offer 12
scenes or shorter reading sessions without silently changing the count.

## Scene and word budgets

Offer only **12, 24, or 48 story scenes**; **24 is the default**. Separate title,
cover, and blank publisher pages do not count as story scenes.

The average band applies to `body_words / scene_count`, not to every individual
scene. Vary scene lengths naturally; never pad a moment to hit its nominal
budget. Total body-word bounds are the average band's bounds multiplied by the
confirmed count. Aim near the planning average unless the story reads better
elsewhere within the band.

| Target level | Average words/scene band | Planning average | 12 scenes: body words | 24 scenes: body words (default) | 48 scenes: body words |
|---|---:|---:|---:|---:|---:|
| B | 4-6 | 5 | 48-72 | 96-144 | 192-288 |
| C | 6-8 | 7 | 72-96 | 144-192 | 288-384 |
| D | 8-12 | 10 | 96-144 | 192-288 | 384-576 |
| E | 11-15 | 13 | 132-180 | 264-360 | 528-720 |
| F | 15-19 | 17 | 180-228 | 360-456 | 720-912 |
| G | 19-23 | 21 | 228-276 | 456-552 | 912-1104 |
| H | 23-27 | 25 | 276-324 | 552-648 | 1104-1296 |
| I | 28-32 | 30 | 336-384 | 672-768 | 1344-1536 |
| J | 33-37 | 35 | 396-444 | 792-888 | 1584-1776 |
| K | 38-42 | 40 | 456-504 | 912-1008 | 1824-2016 |

Use these qualitative writing guides alongside the budgets:

| Level | Editorial guide |
|---|---|
| B | Very familiar, concrete actions; a short repeated sentence pattern; mostly high-frequency words; each line directly picturable. |
| C | Familiar words and predictable patterns with small variations; simple complete sentences; clear picture support. |
| D | A simple beginning, problem, and ending; repeated key words; basic action and feeling words; very clear sequence. |
| E | A familiar small problem and solution; simple descriptive phrases; limited, clearly attributed dialogue. |
| F | Connected actions with explicit reasons; mostly simple sentences with some natural variation; explain unfamiliar words in context. |
| G | A developing problem, attempts, and outcome; varied sentence openings; clear dialogue and simple cause and effect. |
| H | A sustained story with clear paragraph links; supported new vocabulary; simple motives and feelings conveyed through actions. |
| I | Several connected events; modest inference supported by context; some compound sentences; clear references and dialogue. |
| J | A fuller plot and character motivation; varied sentence structures; contextual support for less familiar words; limited figurative language. |
| K | A developed problem and resolution; richer but accessible vocabulary; varied sentences and paragraphs; supported inference and character growth. |

These are writing guides, not an exhaustive official leveling rubric. Familiar
names or culturally necessary words may remain at any level: introduce them
clearly, repeat them consistently, and simplify surrounding prose. Do not erase
cultural identity merely to reduce word length.

## Workflow

### 1. Read and assess without editing

1. Read the full supplied story. If the source is missing or ambiguous, use
   `ask_user` to identify it.
2. Count body words, excluding the title, headings, scene labels, and editorial
   notes. Count whitespace-separated tokens; contractions and hyphenated words
   are one token each. Use the same convention before and after polishing.
3. Identify the premise, important characters, setting, major events, emotional
   arc, and ending. Note continuity problems and prose that may be too complex.
4. Report the source count and a brief diagnosis. Do not overwrite or rewrite
   anything before the target-confirmation gate.

### 2. HARD GATE: confirm level and scene count

Use `ask_user` with:

- `target_level`: string enum `B`, `C`, `D`, `E`, `F`, `G`, `H`, `I`, `J`, `K`.
  No inferred default.
- `scene_count`: string enum `12`, `24`, `48`, default `24`.

Reuse explicitly supplied, valid choices for this story; ask only for missing
choices. Normalize case and accept an equivalent numeric count, but validate
actual answers: form metadata does not enforce the allowed values. An invalid
choice requires clarification, not a silent fallback.

State the proposed body-word range and planning average once both choices are
known, before rewriting. If the choices came from the user directly, that is
their confirmation; do not require a redundant approval. If they decline
without confirming a level, leave the story unchanged and report that a target
is still needed. If they cancel, stop.

If an explicit user word-count requirement conflicts with the selected budget,
explain the mismatch and ask which requirement to revise before proceeding.
Never silently override the level, count, or word requirement.

### 3. Decide whether polishing is needed

Evaluate all of the following against the confirmed choices:

- **Length:** body words fall within the table's total-word band.
- **Language:** vocabulary, syntax, repetition, and inference fit the level.
- **Story:** coherent events, consistent characters, an understandable problem
  and resolution, and an engaging emotional arc.
- **Scene feasibility:** the story can form the exact selected number of
  distinct, illustratable moments without padding or breaking sentences.

If all four pass, report that the story meets the bar and leave it unchanged.
Do not rewrite merely to reach the exact midpoint. If any check fails, explain
what needs changing and polish only as much as necessary.

### 4. Plan and polish

Privately outline exactly the confirmed number of moments before writing.
Give each a dominant action, reaction, or meaningful dialogue beat that can
fit one illustration. Build a clear opening, escalating attempts or discoveries,
and a satisfying ending. Keep the final prose in story order.

- If too short, add meaningful actions, attempts, sensory details, dialogue,
  or consequences suited to the level. Deepen the existing story rather than
  adding unrelated subplots.
- If too long, remove repetition that does not support learning, redundant
  description, and unnecessary side events. Preserve the causal chain.
- If too difficult, simplify vocabulary and syntax, make references explicit,
  and show one idea at a time. Do not make the plot incoherent to shorten it.
- If dull or confusing, use character choices, concrete details, clear stakes,
  and a payoff tied to the opening. Avoid adjective piles and appended morals.
- Preserve the source's core premise, names, cultural setting, emotional intent,
  and ending unless the user approves a substantive adaptation. Ask before
  changing major events or sensitive material to fit the level.
- Use natural US English. Repetition should support early readers, not feel
  like filler. Do not introduce advanced language simply to meet a word quota.

Write a title followed by exactly one prose paragraph per planned scene, with
blank lines between paragraphs. Do not include scene numbers, editorial
annotations, word counts, or planning notes inside the story body.

### 5. Verify the actual draft

Use a local counting command or script on the actual draft, not an estimate.
Exclude the title and use the counting convention above. Verify:

1. Paragraph/scene count equals the confirmed count.
2. Total body words lie within the selected total-word band and any compatible
   explicit user bounds.
3. Actual average is `body_words / scene_count`; report it to one decimal place.
4. Each paragraph is one illustratable moment; sentences and dialogue remain
   intact across boundaries.
5. Vocabulary, syntax, plot continuity, and emotional payoff pass a manual
   editorial review. A passing count is not a passing reading-level assessment.

Also count characters in each proposed scene paragraph. The current
`scene-splitter` enforces **240 characters per scene**, independent of RAZ level.
Respect that limit for downstream-ready prose. If the selected level, word
budget, story content, and character limit cannot all be met naturally, stop
and explain the concrete conflict through `ask_user`. Offer another permitted
scene count or target level and show the recalculated budget. Do not silently
split into extra scenes, truncate prose, call an over-cap draft ready, or
change the splitter's policy in this skill.

Revise and recount until all checks pass. Never claim compliance from a
rounded average when the total falls outside the bounds.

### 6. Save and hand off

Save polished stories as `{story-name}_{level}_{scene_count}.md`, using the
confirmed uppercase level B-K and scene count 12, 24, or 48. For file input,
use the source filename stem as `story-name` and save beside the source. If the
stem already ends in a level/count suffix matching `_[B-K]_(12|24|48)`, replace
that suffix instead of appending another.
For example, `the-legend-of-snake.md` polished at G with 24 scenes becomes
`the-legend-of-snake_G_24.md`.

For text-only input, derive a lowercase, hyphenated story name from the title
and ask for a destination directory before saving with the same naming rule.
Ask before replacing any existing output not already authorized for replacement.
Keep the original untouched. Validate the saved text's counts.

Report the output path, target level, scene count, body-word count, actual
average, and brief changes. If no polish was necessary, report the assessment
and source path without creating a duplicate file.

Pass the approved prose path, confirmed count, and editorial level to
`scene-splitter` only when the user requests downstream work. Preserve its
scene-plan approval gate and exact-text rule. This skill's paragraph plan is
not a replacement for validated scene JSON. Do not change the downstream
`target_level` schema or claim that B-K support is implemented in publishers.

If generated scenes, illustrations, narration, HTML, or PDF already exist,
warn that they describe the earlier prose. Do not regenerate, overwrite, or
claim they are synchronized with the polished story.

## Examples

**Needs expansion:** A 150-word story is confirmed as G with 24 scenes.
The project band is 456-552 words (planning average 21). Expand meaningful
events into 24 picturable paragraphs, validate each paragraph's character
count, then report actual counts. Do not merely add decorative adjectives.

**Already meets the bar:** A 120-word story confirmed as B with 24 scenes
has a 5-word average. If its patterns, vocabulary, distinct moments, and
reading load also pass review, leave it unchanged. Length alone is not enough.

**Conflicting requirements:** A user requests B, 12 scenes, and 1,400 words.
The project band is 48-72 words. Explain the conflict and ask the user to
revise the constraints; do not label a 1,400-word story level B to satisfy them.