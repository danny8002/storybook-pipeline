---
name: story-illustrator
description: Generates a consistent illustrated PNG for every scene of a story using GitHub Copilot's built-in image_generation tool. Reads {slug}_scenes.json from scene-splitter, proposes a visual style, asks for one supported output size, extracts a visual bible, creates character and location reference images, drafts a continuity-classified shot list, then generates one scene image per entry with cascading local reference images. Saves {slug}_bible.md, {slug}_shotlist.md, and {slug}_images.json in the story working directory. Use whenever the user wants to illustrate a story, generate scene images, draw storybook pictures, or produce a consistent visual sequence.
---

# Story Illustrator

Turns a split story into a sequence of illustrations with consistent characters, locations, props, and style. The workflow is **bible -> reference plates -> cascading scene images**.

## When this skill applies

Use this skill when `{slug}_scenes.json` exists and the user wants actual story images. If the user supplies an unsplit story, invoke `scene-splitter` first.

This skill does not apply to:
- A single standalone image with no narrative.
- Video or animation.
- Requests for only the visual bible or shot list.

## Required image backend

Use GitHub Copilot's native **`image_generation`** tool. Do not use Fal, an MCP image server, a direct model API, or an API key.

Call `image_generation` once per PNG:

```json
{
  "prompt": "<complete generation prompt>",
  "input_images": [
    { "path": "stories/<slug>/<slug>_images/ref_character.png" },
    { "path": "stories/<slug>/<slug>_images/previous.png" }
  ],
  "size": "1536x1024",
  "quality": "high"
}
```

Omit `input_images` for a text-only reference plate.

The skill offers:
- `1536x1024` — landscape, the storybook default
- `1024x1536` — portrait

The tool owns model selection. Do not ask the user to choose an image model.

`image_generation` returns a PNG artifact. Capture its local path immediately and copy or move it to the locked target under:

```text
stories/{slug}/{slug}_images/
```

Reference images are local files named `ref_<safe-name>.png`; scene images are always `part_NN.png`. Verify that the file exists and is a PNG before recording it in `{slug}_images.json`.

## Reference contract

For a scene call, pass reference images in priority order:
1. Character reference images.
2. Location reference image.
3. Previous scene image, when continuity calls for it.

For a MICRO cut or a correction, the previous/current-attempt image goes first.

The prompt must name each input reference by order, for example:

```text
Reference images, in order:
1. Pip character reference (preserve identity exactly).
2. Meadow location reference (preserve setting).
3. Previous scene image (preserve pose, clothing, lighting, and state while changing only the action described below).
```

Keep the set focused. Copilot's tool accepts at most 16 input images, but fewer, clearly identified references work better than a noisy collection.

## Workflow — six stages plus optional QA

### Stage 0: Load scenes

Read `stories/{slug}/{slug}_scenes.json`. Create exactly one scene image per scene, indexed by `scenes[i].index`.

Use:
- `panel_type` for framing.
- `dominant_action` for the action.
- `characters` and the bible's in-frame roster for visible characters.
- `scene` for the location.
- `mood` for lighting and tone.

If the file is missing, stop and invoke `scene-splitter`.

### Stage 1: Lock the visual setup

1. Propose ONE style based on the story. For a beginner children's story, use a strong default such as:
   > warm, soft watercolor children's-book illustration, gentle rounded shapes, cozy lighting
2. Determine the output size. Ask one of:
   > `1536x1024` landscape (default) or `1024x1536` portrait
   If the orchestrator pre-supplied a size, do not ask again.
3. Lock `style`, `size = selected size`, and `quality = high` for the whole run.
4. State the scope: number of reference plates plus scene images. Do not invent a dollar price; say image generation consumes the user's Copilot image allowance.
5. Wait for `go`.

### Stage 2: Build the visual bible

Read [references/bible-extraction.md](references/bible-extraction.md).

Write `{slug}_bible.md` with:
- recurring cast and exact physical design;
- recurring locations;
- recurring props;
- locked style descriptor;
- prop-state tracker when an object changes;
- characters-in-frame map for casts of three or more.

Invent specific physical details where the story is silent, but make those details visible and testable. Re-read the story in a second pass to catch omissions.

Before pausing, verify child-safe character design: modest everyday clothing, covered torso, and no suggestive framing.

Pause:
> Bible drafted — anything to change before I generate references? Reply `go` or provide edits.

### Stage 3: Generate reference images

Create one reference per recurring character and one per recurring location. Use solo character plates; do not combine characters into a group reference.

For every reference:
- use the exact locked style;
- use the locked size;
- use the universal no-text/no-border rules below;
- call `image_generation` without `input_images`;
- save the returned PNG as `ref_<safe-name>.png`;
- record it in `{slug}_images.json` with its local `path`.

Character reference prompt:
- full body;
- neutral pose and expression;
- plain white background extending to all canvas edges;
- exact clothing, accessories, anatomy, and proportions from the bible.

Location reference prompt:
- wide-angle plate;
- no people;
- neutral lighting;
- every defining feature visible;
- full-bleed image.

Do not generate a separate style-anchor image. The style is carried by the descriptor and the character/location plates.

Show the reference files and pause:
> References generated — review them, then reply `go` to draft the shot list.

### Stage 4: Draft the shot list

Read [references/shot-list.md](references/shot-list.md).

Create one shot per scene and classify continuity:
- **HARD CUT** — new setting/time or scene 1; character + location refs, no previous scene.
- **SOFT CUT** — same setting/time, next moment; character + location + previous scene.
- **MICRO CUT** — tiny change in the same moment; previous scene first, then character + style.
- **STATE RESET** — prior visual state is now wrong; character + location refs, no previous scene.

Write `{slug}_shotlist.md`, including the exact reference paths for each scene. Show the scene count and pause:
> Shot list ready for N scene generations — reply `go` or request changes.

### Stage 5: Generate scene images

Generate scenes in index order because SOFT and MICRO cuts depend on the previous output.

For each scene:
1. Build the prompt as:
   - exact style descriptor;
   - reference-image map in `input_images` order;
   - framing from `panel_type`;
   - one exact action;
   - state deltas and visible-character roster when needed;
   - lighting and exclusions;
   - universal no-text/no-border rules.
2. Build `input_images` from the paths selected in the shot list. Do not use remote URLs.
3. Call `image_generation` with `size` locked in Stage 1 and `quality: "high"`.
4. Copy the returned PNG to:
   `stories/{slug}/{slug}_images/part_NN.png`
5. Verify the file exists and is non-empty.
6. Add or update the matching shot in `{slug}_images.json`.
7. Use this local path as the previous-scene input for the next SOFT or MICRO cut.

Do not silently skip a scene. If the tool fails, preserve the error, retry once when the error is transient, then stop and report the exact scene and failure. Never fabricate a registry entry for a missing file.

Do not run QA inline. Finish the sequence first, then run optional Stage 5.5.

### Stage 5.5: Optional vision QA

Trigger only when the user requested `with QA`, `--qa`, or `qa`.

Never auto-regenerate.

1. Open/read every generated PNG with the host's image-capable file view.
2. Compare each against the bible, shot list, and scene metadata.
3. Check identity, prop state, visible-character roster, anatomy, duplicated objects, lighting, framing, and hallucinated text/borders.
4. Produce a table: scene, findings, severity.
5. Wait for explicit choices such as `regen N`, `regen N M`, or `keep`.
6. Follow [references/qa-and-retry.md](references/qa-and-retry.md) for approved corrections.

### Stage 6: Finalize the registry

Write `{slug}_images.json` using durable local paths:

```json
{
  "story_slug": "the-little-cloud",
  "generator": "github-copilot-image_generation",
  "style": "warm soft watercolor children's-book illustration",
  "size": "1536x1024",
  "quality": "high",
  "references": [
    {
      "name": "pip",
      "kind": "character",
      "path": "stories/the-little-cloud/the-little-cloud_images/ref_pip.png"
    },
    {
      "name": "sky",
      "kind": "location",
      "path": "stories/the-little-cloud/the-little-cloud_images/ref_sky.png"
    }
  ],
  "shots": [
    {
      "index": 1,
      "path": "stories/the-little-cloud/the-little-cloud_images/part_01.png",
      "continuity": "HARD CUT"
    },
    {
      "index": 2,
      "path": "stories/the-little-cloud/the-little-cloud_images/part_02.png",
      "continuity": "SOFT CUT"
    }
  ]
}
```

Every `shots[i].index` must equal the corresponding scene index. The publisher uses the local PNG paths.

## Universal prompt rules

Include these rules in every reference, scene, and retry prompt:

> Create a purely pictorial illustration with clean, unmarked surfaces and no readable text, labels, letters, numbers, signs, book titles, or name tags anywhere.
>
> Create a full-bleed illustration that reaches all four canvas edges: no border, frame, vignette, paper margin, decorative edge, or inner mat.

For text-prone scenes, add an explicit short exclusion for the relevant object, such as "the open book contains only blank illustrated shapes, with no letters."

## Triggering retries

When the user flags an image, inspect the current PNG, translate the feedback into concrete physical corrections, and follow [references/qa-and-retry.md](references/qa-and-retry.md). Put the previous attempt first in `input_images`, regenerate with the same size, overwrite `part_NN.png`, and update its registry entry.

## What good looks like

- `{slug}_bible.md` approved before generation.
- `{slug}_shotlist.md` with continuity and exact local reference paths.
- `{slug}_images.json` with every reference and scene PNG indexed.
- Reference plates plus one `part_NN.png` per scene under `{slug}_images/`.
- No Fal key, cloud image endpoint, or external model registry.

## Reference files

- [references/bible-extraction.md](references/bible-extraction.md)
- [references/shot-list.md](references/shot-list.md)
- [references/qa-and-retry.md](references/qa-and-retry.md)
- [references/image-backends.md](references/image-backends.md)
