---
name: scene-splitter
description: Split an English story into scenes with one illustration and narration clip per moment. Estimate scene count from body word count and story beats, then ask the user to confirm or enter a count before drafting the scene plan. Preserve exact prose and the 240-character beginner scene limit. Use for splitting stories into scenes, pages, or illustration panels and preparing the storybook pipeline. Outputs {slug}_scenes.json for aligned illustration and narration.
---

# Scene Splitter

Takes a plain English story and produces a numbered list of **scenes** — each scene being one moment that gets exactly one illustration and one narration clip downstream.

This is the upstream spine of the AI Storybook pipeline. Splitting once here and feeding both the illustrator and the narrator from the same `{slug}_scenes.json` keeps everything in lockstep: **image N pairs with audio N pairs with paragraph N.** No drift, no negotiation between skills.

## When this skill applies

The user has an English story and wants to prepare it for the illustration + narration pipeline. Common phrasings: "split this into scenes", "break this into pages", "prepare this story for the storybook", "make scenes for illustration".

The skill does NOT apply to:
- Stories that need only narration OR only images standalone (the illustrator and narrator can split on their own when used independently)
- Non-narrative content (essays, instructions, lists)

## Architectural rule: one scene = one moment = one image = one narration clip

A scene is a single moment that fits one illustration. Operationally, a new scene starts at any of:

- **Action transition** — a different action happens
- **Scene change** — a different location or a significant time jump
- **Emotional turn** — joy → fear, calm → urgency, doubt → resolve
- **Character entry/exit** — someone new appears or leaves the moment
- **Dialogue beat** — a meaningful line of speech that deserves its own picture

Scenes are deliberately short and many. The storybook player renders **one scene at a time**, and the text MUST fit on a phone screen without scrolling. That drives the hard length cap below.

## Reading level + length cap (beginner default)

This pipeline targets **beginner** readers. The cap is screen-fit-driven, not API-driven:

| Level | Per-scene hard cap | Target scene count |
|---|---|---|
| **beginner** (default) | **240 characters** | Estimated from story length and beats; user-confirmed |

The cap is the number of characters in a single scene's `text`. Keep most scenes well under it (~120–180 chars reads best on a phone). Aim for roughly 25–35 words per scene when estimating, but validate the actual character count. The familiar 8–12 scene range is a guide for typical short stories, not a minimum or maximum: shorter stories can need fewer scenes and longer stories more.

## Workflow — scene-count and scene-plan gates

### Stage 1: Story analysis

1. Read the full story.
2. Count words and characters in the story body, excluding any title heading. Count words as whitespace-separated tokens. Detect named characters, distinct settings, and the major action/emotional beats.
3. **Determine the slug** from the title (line 1) or filename — lowercased, hyphenated, ASCII-safe (`^[a-z0-9-]+$`, max 60 chars). Examples: "The Little Cloud" → `the-little-cloud`; `red_balloon.md` → `red-balloon`.
4. Start with `max(1, ceil(body_word_count / 30))` as a length-based estimate. Review the story's natural boundaries and adjust the recommendation so each scene represents one moment and can fit the 240-character cap without rewriting. Explain adjustments for distinct actions, setting changes, or long sentences. Do not pad a short story to eight scenes or cap a long story at twelve.
5. Output a one-line summary: "Story is [W] words, [C] chars, [X] named characters, [Y] settings. Recommended: [Z] scenes (~[W/Z] words per scene), based on length and story beats. Slug: `{slug}`."

### Stage 1.5 — HARD GATE: confirm scene count

Before drafting the detailed scene plan, use `ask_user` with an integer field
named `scene_count`, titled "Number of scenes", and default it to the recommended
count. Explain the estimate in the message and invite the user to accept it or
enter their own count. This counts story scenes, not the publishers' separate
cover or blank pages.

Validate the response as a positive whole number; field metadata alone does not
enforce this. If the user already explicitly supplied a count, validate and reuse
it without asking them to repeat it. If they decline, use the recommendation and
state that choice; if they cancel, stop.

Treat the chosen count as the target for the plan. Check feasibility against
the unmodified prose, natural boundaries, and 240-character limit. If it cannot
be met (too few scenes for the text or too many meaningful moments requested),
explain the specific conflict and use `ask_user` to propose a feasible count or
request author edits. Never silently change the chosen count, rewrite text,
repeat content, add empty scenes, or break the length cap to meet it.

### Stage 2: Scene identification

Walk the story in order and draft the chosen number of scenes. At each candidate boundary, decide: new scene or extend the current one? Use the boundary rules above, retaining one moment per scene. If boundaries reveal that the chosen count is infeasible, return to the scene-count gate instead of silently adding or removing scenes.

For each scene, capture the **exact text** from the source. The splitter chooses BOUNDARIES, not content — do not reword, summarize, or rewrite the author's prose. (If a sentence must be trimmed to fit the cap, that's an author decision — surface it at the gate, don't silently edit.)

### Stage 3: Per-scene metadata

For each scene, populate:

- `index` — 1-based
- `role` — `cover` for scene 1, `closing` for the last scene, `body` for everything else
- `panel_type` — one of `establishing` | `action` | `reaction` | `detail` (drives framing variety downstream):
  - `establishing` — wide, sets the place. Good for scene 1 and any location change.
  - `action` — something is happening; dynamic composition.
  - `reaction` — close on a character's face/feeling.
  - `detail` — tight on one object or element.
- `text` — the exact story text for this scene (no title prefix on scene 1 — see below)
- `char_count` — character count of `text`
- `scene` — location/setting in 2–4 words (e.g. "sunny meadow", "cozy kitchen")
- `characters` — array of named characters present in this moment
- `mood` — emotional tone in 1–3 words (e.g. "warm, curious")
- `dominant_action` — what happens in this moment, in one sentence (the illustrator turns this into the image prompt)

**Title handling for the cover scene (LOCKED).** The story's title (the `# Heading` on line 1) MUST NOT appear in `scenes[0].text`. The player shows the title in the header and builds a dedicated cover page from the first illustration (with the spoken title clip); scene 1's `text` then renders as its own story page. If the title were left in `scenes[0].text` it would show up twice (header + as scene 1's paragraph). Strip it from scene 1's `text` and store it at the top level instead:

```json
{
  "story_slug": "the-little-cloud",
  "story_title": "The Little Cloud",
  "target_level": "beginner",
  "language": "en",
  "total_scenes": 9,
  "scenes": [
    {
      "index": 1,
      "role": "cover",
      "panel_type": "establishing",
      "text": "High in the sky lived a little cloud named Pip.",
      "char_count": 47,
      "scene": "wide blue sky",
      "characters": ["Pip"],
      "mood": "gentle, bright",
      "dominant_action": "A small white cloud drifts alone in a big blue sky."
    }
  ]
}
```

### Stage 3.5: Validation (reconstruction + length cap)

**Reconstruction check.** Concatenate `story_title + "\n\n" + scenes[*].text` (single spaces between scenes) and verify it reconstructs the original story. The title goes at the front because it was stripped from `scenes[0].text`. If even one word is missing or duplicated, abort and report which boundary is broken — do NOT proceed to the gate with broken reconstruction.

**Length-cap check.** For every scene, verify `char_count` ≤ 240. If any scene is over cap:
1. Do NOT show the gate yet.
2. List the over-cap scenes (index, char_count, first ~80 chars).
3. Re-enter Stage 2 for those scenes: find an internal boundary (action shift, emotional turn, dialogue handoff) and split. If a scene is one indivisible moment but still over cap, flag it `OVERSIZED — needs author trim` rather than force-splitting on a non-boundary.
4. Re-run the reconstruction check. If splitting changes the chosen count, return to the scene-count gate with the reason before proceeding.

**Count check.** Verify `len(scenes)` equals the confirmed count and
`total_scenes` equals `len(scenes)`. Any discrepancy must be resolved with the
user before writing output.

### Stage 4 — HARD GATE: review scenes

State the confirmed scene count, then show the proposed scene list in a compact table (so 10+ scenes fit on screen). Columns: index · role · panel_type · mood · char_count · first ~60 chars + ellipsis · dominant_action.

Below the table, prompt:

> **Scene plan ready — review and approve before I write scenes.json. Reply:**
> - `go` to commit
> - `merge N M` to combine two adjacent scenes
> - `split N` to split a scene further (I'll propose where)
> - `edit N` to fix one scene's metadata
> - `fix N <reason>` for free-form feedback (e.g. `fix 7 too long, split before "but then"`)
> - `redo` to restart with a different approach

If the user issues a change, apply it, re-run Stage 3.5 validation, and re-show the gate. An explicit merge or split request authorizes the resulting count change: state the new target count before review. For other changes, do not silently change the count. Loop until `go`.

This gate is where human taste enters: it costs nothing now, but a wrong boundary means a wrong image AND a wrong audio clip downstream.

### Stage 5: Output

Write `{slug}_scenes.json` to the working directory `stories/{slug}/`. Confirm in one line: "Wrote `{slug}_scenes.json` — N scenes, ready for the illustrator and narrator."

## What this skill does NOT do

- Does not edit or rewrite story text — only chooses boundaries.
- Does not generate audio or images — those are downstream skills.
- Does not classify or tag the story (this beginner pipeline skips classification by design).
- Does not write to any database or upload anything — local file output only.

## Compatibility notes

- Output is consumed by `story-illustrator` and `story-narrator`. Both accept `{slug}_scenes.json` and skip their own splitting, so the image for scene N and the audio for scene N stay aligned by index.
- Image filenames downstream are `{slug}_part_NN.png`; audio filenames are `{slug}_part_NN.mp3`, where `NN` is the zero-padded scene index. The publisher pairs them by that index.
- Keep the user-confirmed count consistent across the plan and output. Explicit merge/split requests can revise it at the scene-plan gate.
