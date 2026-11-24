# AI Storybook Pipeline

Turn an English story into a consistently illustrated, narrated storybook with **GitHub Copilot**, its native image-generation tool, and **local VoiceStudio OmniVoice**.

The pipeline produces three shareable outputs:

- **Self-contained HTML** — a responsive swipe/tap reader with embedded illustrations and per-scene MP3 narration; works offline.
- **Printable A4 PDF** — a title-and-image cover, a blank page, and two illustration-and-text groups per story page.
- **Full-story MP3** — the optional spoken title followed by every scene's narration.

## Current status

This checkout focuses on the storybook pipeline. It contains **seven project-local Copilot skills**, Python publishing and narration helpers, and an included **12-scene example, “The Legend of the White Snake.”**

The earlier Claude Code Level 1–3 image generators, their example galleries, and the Cloudflare `.env.example` are **not included in this checkout**. The storybook uses Copilot's native image tool rather than those generators, Fal, or a Cloudflare image API; narration uses local VoiceStudio rather than ElevenLabs.

## Included example

<p align="center">
  <img src="stories/the-legend-of-snake/the-legend-of-snake_images/part_01.png" height="250" alt="The Legend of the White Snake — scene 1">
  <img src="stories/the-legend-of-snake/the-legend-of-snake_images/part_02.png" height="250" alt="The Legend of the White Snake — scene 2">
  <img src="stories/the-legend-of-snake/the-legend-of-snake_images/part_03.png" height="250" alt="The Legend of the White Snake — scene 3">
</p>

The example uses portrait (`1024x1536`) Chinese ink-and-watercolor storybook illustrations. Its folder contains scenes, character/location references, a visual bible, a shot list, image and audio manifests, and these exports:

- [Read the HTML storybook](stories/the-legend-of-snake/the-legend-of-snake.html) — download and open locally in a browser.
- [Open the printable PDF](stories/the-legend-of-snake/the-legend-of-snake.pdf).
- [Listen to the full narration](stories/the-legend-of-snake/the-legend-of-snake_audio/the-legend-of-snake_full.mp3).
- [Read the source story](stories/the-legend-of-snake.md).

Embedded media makes the HTML large; use a browser rather than a text editor or GitHub's source preview.

## How it works

```text
stories/{slug}.md
      |
      +-- optional: story-polish -> assessed or polished prose
      |
      v
1. scene-splitter        -> {slug}_scenes.json
2. story-illustrator     -> {slug}_bible.md, {slug}_shotlist.md,
                           {slug}_images.json + local PNGs
3. story-narrator        -> {slug}_audio/manifest.json,
                           per-scene MP3s + {slug}_full.mp3
4a. story-html-publisher -> {slug}_story.json + {slug}.html
4b. story-pdf-publisher  -> {slug}.pdf
    (4a and 4b build in parallel after PDF background approval)
```

All generated pipeline artifacts live under `stories/{slug}/`. **Scene N pairs with image N, audio N, and text N.** The source story stays outside that folder.

| Skill | Role | Backend |
|-------|------|---------|
| [storybook-pipeline](.github/skills/storybook-pipeline/SKILL.md) | Orchestrate intake, readiness checks, scene/image/audio pairing, and both exports | GitHub Copilot |
| [story-polish](.github/skills/story-polish/SKILL.md) | Optional preparation for a confirmed RAZ-aligned level B–K and 12/24/48 scenes (default 24); rewrite only when needed | GitHub Copilot |
| [scene-splitter](.github/skills/scene-splitter/SKILL.md) | Estimate scene count from body words and story beats, confirm the count, then split without rewriting | GitHub Copilot |
| [story-illustrator](.github/skills/story-illustrator/SKILL.md) | Build visual references and a continuity-aware shot list, then generate one consistent PNG per scene | Copilot native `image_generation` |
| [story-narrator](.github/skills/story-narrator/SKILL.md) | Select a saved voice, review narration, generate scene clips, and assemble the full track | Local VoiceStudio OmniVoice + FFmpeg |
| [story-html-publisher](.github/skills/story-html-publisher/SKILL.md) | Validate and embed scenes, images, and audio into an offline HTML player | Python standard library |
| [story-pdf-publisher](.github/skills/story-pdf-publisher/SKILL.md) | Package local images and original scene text into an A4 portrait PDF | Python + ReportLab |

### Review gates and limits

- Confirm the slug and one illustration size: **1536x1024 landscape** (default) or **1024x1536 portrait**.
- Approve the scene count and scene plan. The beginner splitter preserves exact prose and enforces **240 characters per scene**; its count is not restricted to 12/24/48.
- Review the visual style/bible, references, and shot list before scene generation. Image QA is optional: request **“with QA.”**
- Select a VoiceStudio voice and approve the narration script before synthesis. `default` must be an explicit choice, not a fallback.
- Choose the PDF background and review both exports before finishing.
- Existing artifacts are offered for resume/skip rather than silently replaced. Missing tools or media are reported; a partial HTML requires explicit approval, and the PDF never uses placeholders.

`story-polish` is an optional step **before** the orchestrator, not an automatic pipeline stage. Its B–K assessments are editorial estimates, not official Reading A-Z placements; downstream scene JSON remains beginner-targeted.

## Setup

### 1. GitHub Copilot and Python

Open this repository in a GitHub Copilot environment that supports project-local skills and the native `image_generation` tool. Skills live in [.github/skills/](.github/skills/). Illustration requires access to Copilot image generation and uses your image allowance.

Run helper commands from the repository root. On macOS/Linux, create a Python virtual environment and install the PDF dependency:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r .github/skills/story-pdf-publisher/assets/requirements.txt
```

On Windows, use `python` and activate the virtual environment with the appropriate Windows command. The HTML and narration helpers use only Python's standard library; they do not require Pillow, NumPy, requests, or dotenv.

### 2. Local VoiceStudio

Start a local VoiceStudio deployment at `http://127.0.0.1:3900` with the **OmniVoice** engine (`k2-fsa/OmniVoice`, API model ID `omnivoice`) enabled. VoiceStudio is a separate prerequisite; this repository does not install or start it.

Verify the engine before narration:

```bash
python3 .github/skills/story-narrator/assets/voicestudio_tts.py --check
```

If `omnivoice` is unavailable, enable the engine in VoiceStudio and restart the service.

The narrator uses:

```text
POST http://127.0.0.1:3900/v1/audio/speech
model: omnivoice
voice: <user-selected saved profile ID or explicitly selected default>
response_format: mp3
```

Voice discovery uses the **VoiceStudio MCP** endpoint at `http://127.0.0.1:3900/mcp/`. Add this entry to your MCP client's configuration:

```json
{
  "mcpServers": {
    "VoiceStudio": {
      "type": "http",
      "url": "http://127.0.0.1:3900/mcp/"
    }
  }
}
```

Use [.mcp.json.example](.mcp.json.example) as a reference, merging into existing configuration rather than overwriting it. That template also contains a `vidtsx` entry, which is not required for the storybook pipeline. Reload your MCP client and ensure VoiceStudio's `list_voices` tool is available.

MCP lists saved profiles; MP3 synthesis uses the HTTP speech endpoint because VoiceStudio MCP's `generate_speech` does not currently offer MP3.

### 3. FFmpeg

Install FFmpeg and make sure `ffmpeg` is on `PATH`:

```bash
ffmpeg -version
```

It concatenates the optional title and scene clips into the full-story MP3 without re-synthesis or re-encoding. No cloud TTS or image API keys are needed for this pipeline.

## Using it

Put an English story in `stories/my-story.md`, then ask GitHub Copilot:

> Run the storybook pipeline on stories/my-story.md.

For optional image review:

> Run the storybook pipeline on stories/my-story.md with QA.

For reading-level preparation before the pipeline:

> Polish stories/my-story.md for RAZ-aligned level G and 24 scenes.

The polish skill keeps the original untouched and, when a rewrite is needed, saves a file such as `stories/my-story_G_24.md`. Run the pipeline on the approved prose file afterward.

Individual skills can also be requested: **“Split this story into scenes,” “Illustrate this story,” “Narrate this story,” “Build the storybook HTML,”** or **“Export the storybook PDF.”**

### Rebuild existing exports

After updating approved upstream media, rebuild from the repository root:

```bash
# Embed existing scenes, images, and scene audio into HTML.
python3 .github/skills/story-html-publisher/assets/build_html.py \
  the-legend-of-snake

# Build the PDF using the approved background.
python3 .github/skills/story-pdf-publisher/assets/build_pdf.py \
  the-legend-of-snake --background eye-friendly

# Reassemble the full track after changing title or scene clips.
python3 .github/skills/story-narrator/assets/assemble_audio.py \
  stories/the-legend-of-snake/the-legend-of-snake_audio/manifest.json
```

The PDF supports **warm cream** (`eye-friendly`, `#F7F3E8`, recommended) or **white** (`white`, `#FFFFFF`). It needs scenes and valid local images, not narration or the HTML output.

### Export behavior

**HTML:** a separate title-and-first-image cover, every original scene (including scene 1), and a “The End” screen. Tap the image or play button for narration; navigate with swipes, arrow keys, buttons, or progress dots. An auto-play toggle advances after narration ends. All media is embedded; no assets folder or internet connection is needed for playback.

**PDF:** A4 portrait, an unnumbered cover and blank page, then two stacked uncropped image-and-text groups per page. An odd final scene uses the top slot. Total pages: `2 + ceil(scene_count / 2)`. Story-page numbering starts at 1, alternating bottom-right on odd pages and bottom-left on even pages. Audio is not embedded.

**MP3:** one standalone full-story track in the audio folder; the HTML continues to use individual scene clips.

## Project structure

```text
claude-image-generation/
├── .github/skills/
│   ├── story-polish/             # Optional reading-level prose preparation
│   ├── scene-splitter/           # Story -> approved scenes
│   ├── story-illustrator/        # Visual bible, references, shot list, PNGs
│   ├── story-narrator/           # VoiceStudio MP3 + FFmpeg assembly helpers
│   ├── story-html-publisher/     # HTML builder + player template
│   ├── story-pdf-publisher/      # A4 PDF builder + requirements + tests
│   └── storybook-pipeline/       # Copilot orchestrator
├── stories/
│   ├── the-legend-of-snake.md
│   ├── the-legend-of-snake_polished.md
│   └── the-legend-of-snake/
│       ├── the-legend-of-snake_scenes.json
│       ├── the-legend-of-snake_bible.md
│       ├── the-legend-of-snake_shotlist.md
│       ├── the-legend-of-snake_images.json
│       ├── the-legend-of-snake_images/
│       ├── the-legend-of-snake_audio/
│       ├── the-legend-of-snake_story.json
│       ├── the-legend-of-snake.html
│       └── the-legend-of-snake.pdf
├── .mcp.json.example             # Sanitized MCP configuration template
├── .gitignore
└── README.md
```

## Secrets

Keep live tokens in local configuration only. [.gitignore](.gitignore) excludes `.mcp.json`, `.env`, and local Python environments. Commit only sanitized examples; if a token enters Git history, rotate it at the provider.

## Background and attribution

The original image-generation tutorials and storybook guide were created by [Hasan Aboul Hasan](https://learnwithhasan.com/):

- [Generate images in Claude Code with no AI model](https://learnwithhasan.com/guide/claude-code-images-no-ai-model/) — historical Level 1–2 material.
- [Free AI images with Claude Code + Cloudflare](https://learnwithhasan.com/guide/free-ai-images-claude-code-cloudflare/) — historical Level 3 material.
- [Consistent AI characters for visual stories](https://learnwithhasan.com/guide/consistent-ai-characters-visual-stories/) — background on visual consistency.

These guides provide background, not setup instructions for the current Copilot/VoiceStudio workflow.

The original README described an MIT release. A `LICENSE` file is currently absent from this working tree; consult the project's license history before redistribution.
