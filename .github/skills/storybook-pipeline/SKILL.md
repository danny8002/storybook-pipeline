---
name: storybook-pipeline
description: GitHub Copilot orchestrator for the full AI Storybook pipeline. Runs scene-splitter, story-illustrator, and story-narrator, then builds HTML and A4 PDF storybooks in parallel with story-html-publisher and story-pdf-publisher. Locks scene/image/audio pairing, asks for the PDF background, and preserves approval gates. Uses Copilot's native image tool and local VoiceStudio OmniVoice. Use when the user wants to run the pipeline or make an illustrated narrated storybook. Optionally accepts "with QA" for image review.
---

# Storybook Pipeline

Turns one English story into a self-contained narrated HTML storybook, a printable A4 PDF, and a full narration MP3. This orchestrator dispatches the component skills and preserves their review gates.

## Pipeline order

```text
input: stories/{slug}.md
1. scene-splitter         -> {slug}_scenes.json
2. story-illustrator      -> {slug}_bible.md, {slug}_shotlist.md, {slug}_images.json
3. story-narrator         -> {slug}_audio/{slug}_part_NN.mp3 + {slug}_full.mp3 + manifest.json
4a. story-html-publisher  -> {slug}_story.json + {slug}.html
4b. story-pdf-publisher   -> {slug}.pdf (two image + text groups per A4 page)
```

Steps 2 and 3 both consume the scene JSON. In an interactive run, keep their order so each review surface happens once.

Steps 4a and 4b run in parallel after the PDF background gate. They read shared
upstream artifacts but write separate outputs; the PDF never reads the HTML
publisher's `{slug}_story.json`.

## Locked paths and filenames

Derive the slug from the title or source filename: lowercase, hyphenated, ASCII-safe, `^[a-z0-9-]+$`, maximum 60 characters.

All generated artifacts live under `stories/{slug}/`. The source story remains `stories/{slug}.md`.

## Workflow

### Stage 0: Intake and pre-flight

1. Identify the story file: explicit argument, then the single relevant `*.md` in `stories/`, otherwise ask.
2. Derive the slug and pause:
   > Slug: `the-little-cloud`. OK?
3. Create `stories/{slug}/`.
4. Look for completed artifacts. If some exist, list them and ask whether to skip or replace them. Default to skip.
5. Record whether `with QA` or `--qa` was requested. Default is off.
6. Ask for the illustration output size unless the user already supplied it:
   - `1536x1024` landscape, the default;
   - `1024x1536` portrait.
   This is a hard gate because the size applies to every generated PNG. Do not ask for an image model: GitHub Copilot's native `image_generation` tool owns model selection.
7. Verify:
   - `stories/` is writable;
   - GitHub Copilot exposes its native `image_generation` tool;
   - local VoiceStudio is reachable with:
     `python .github/skills/story-narrator/assets/voicestudio_tts.py --check`.
   - VoiceStudio MCP exposes `list_voices`;
   - `ffmpeg` is available for full-story MP3 assembly.
   - ReportLab is available for PDF publishing (dependencies are declared in
     `.github/skills/story-pdf-publisher/assets/requirements.txt`).
8. Lock narration as:
   - endpoint `http://127.0.0.1:3900/v1/audio/speech`;
   - model OmniVoice (`k2-fsa/OmniVoice`, 600+ languages), API ID `omnivoice`;
   - format MP3.
   Defer voice selection to the narrator: it lists saved voices through VoiceStudio MCP and asks the user to select one. Reuse an already validated selection without asking twice; never silently force `default`.

Do not proceed past a readiness failure, including a missing OmniVoice engine. The HTML publisher can build a partial book only after the user explicitly chooses `build partial`; the PDF publisher requires every scene's image and text and never creates placeholder groups.

### Stage 1: scene-splitter

Invoke `scene-splitter` with the story path, slug, output directory, and any
user-supplied scene count. It estimates the count from body words and story
beats, then asks the user to confirm or enter a count before drafting the plan.
Preserve both its scene-count and scene-plan gates; reuse an explicit validated
count without asking twice. It writes:

```text
stories/{slug}/{slug}_scenes.json
```

### Stage 2: story-illustrator

Invoke `story-illustrator` with:
- `stories/{slug}/{slug}_scenes.json`;
- the locked slug;
- the locked Copilot image-tool size: `size = <1536x1024|1024x1536>`;
- `quality = high`;
- a style hint from the story;
- `with QA` only when enabled.

Tell the illustrator to skip its own size prompt because the orchestrator already locked it.

The illustrator:
- writes the visual bible and waits;
- creates local character/location references with Copilot's native image tool;
- writes the shot list and waits;
- generates `part_NN.png` files in index order;
- records durable local paths in `{slug}_images.json`.

No Fal key, remote model registry, or cloud image endpoint is used.

### Stage 3: story-narrator

Invoke `story-narrator` with:
- `stories/{slug}/{slug}_scenes.json`;
- the locked slug;
- the locked VoiceStudio settings: OmniVoice (`omnivoice`), MP3, and any already validated voice selection;
- an instruction to list voices via VoiceStudio MCP and ask the user to select one if not already selected;
- an instruction to save clips and the assembled `{slug}_full.mp3` under `stories/{slug}/{slug}_audio/`.

Preserve both voice-selection and narration-script gates. Audio is generated through the local VoiceStudio MP3 helper, not ElevenLabs MCP. The narrator assembles the title (if present) and every scene clip into a full-story MP3 using FFmpeg; the publisher still uses individual scene clips.

### Stage 4: Parallel HTML and PDF publishing

Invoke `story-pdf-publisher` for its intake and background gate first. Use
`ask_user` to choose `eye-friendly` (warm cream `#F7F3E8`, recommended) or `white`
(`#FFFFFF`) unless the user already supplied a choice. Confirm A4 portrait,
one dedicated title-and-first-image cover, an unnumbered blank page, then two vertically stacked
image-above-text groups per story page. The title is shown only on the cover;
every original scene remains after it. PDF page count is `2 + ceil(N / 2)`.
Story numbering starts at 1 after the blank page, with odd numbers bottom-right
and even numbers bottom-left; neither the cover nor blank page is numbered.
The HTML likewise opens with title above the first illustration before scene 1.
Ask about replacing any existing PDF before building. Reuse a locked background
without another prompt.

Then invoke both publishers' build stages concurrently with the locked slug:
- `story-html-publisher`: validate media, embed images/audio as base64, and write
  `{slug}_story.json` and `{slug}.html`.
- `story-pdf-publisher`: validate scene/image pairing and write `{slug}.pdf`
  using the locked full-page background.

Run the independent build commands in parallel; do not finish HTML before
starting the PDF build. Do not delegate interactive approval prompts to parallel
workers. Wait for both builds and validations before presenting a combined
final review, preserving each publisher's review choices.

```text
stories/{slug}/{slug}_story.json
stories/{slug}/{slug}.html
stories/{slug}/{slug}.pdf
```

Report failures independently. A successful HTML export does not mean a failed
PDF export is complete. The user must review both files before the pipeline is
finished.

### Stage 5: Final summary

Report:
- the scene, image, and audio counts;
- every major artifact path;
- the full-story MP3 at `stories/{slug}/{slug}_audio/{slug}_full.mp3`;
- the headline deliverable `stories/{slug}/{slug}.html`;
- the printable PDF `stories/{slug}/{slug}.pdf`, its background and A4 page count;
- how to open the HTML in a browser and the PDF in a PDF viewer.

Mention that images use the user's Copilot image allowance and narration uses the local VoiceStudio process. Do not invent per-image or per-character prices.

## Preserved gates

| Skill | Gate | Reason |
|---|---|---|
| orchestrator | slug + image size | Locks every artifact and PNG |
| scene-splitter | scene count + scene plan | Confirms scope before drafting boundaries that control image/audio pairing |
| story-illustrator | style/bible, references, shot list, optional QA | Avoids consuming image generations on a wrong design |
| story-narrator | voice selection + narration script | Locks the user's saved voice and approved narration before synthesis |
| story-html-publisher | final review | Confirms the assembled deliverable |
| story-pdf-publisher | background choice + final review | Locks page color and confirms two scene groups per A4 page |

The orchestrator never bypasses these gates unless the user explicitly authorizes a fully automatic run.

## Failure modes

- **Story not found:** list candidate Markdown files and ask.
- **Artifacts already exist:** list them; default to resume/skip completed stages.
- **Native image tool unavailable:** stop before illustration and state that Copilot image generation is required.
- **VoiceStudio or OmniVoice unavailable:** stop before narration; show the helper's error and ask the user to start or repair the local deployment.
- **Voice listing or FFmpeg unavailable:** stop and report the readiness failure; do not skip voice selection or full-story audio assembly.
- **A generated image is missing or invalid:** do not record it as complete; retry once or return the exact scene failure.
- **An audio response is not MP3:** stop the affected clip and surface the helper error; do not silently convert WAV.
- **PDF dependency or layout failure:** report the exact error; do not drop scenes, silently shrink text, or claim both exports succeeded.

## What this skill does not do

- Does not author the story.
- Does not bypass sub-skill review gates.
- Does not use Fal or ElevenLabs.
- Does not support multiple stories in one invocation.

## References

- [scene-splitter/SKILL.md](../scene-splitter/SKILL.md)
- [story-illustrator/SKILL.md](../story-illustrator/SKILL.md)
- [story-narrator/SKILL.md](../story-narrator/SKILL.md)
- [story-html-publisher/SKILL.md](../story-html-publisher/SKILL.md)
- [story-pdf-publisher/SKILL.md](../story-pdf-publisher/SKILL.md)
