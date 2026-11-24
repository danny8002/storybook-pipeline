# Claude × Image Generation

Connect Claude to three forms of image generation, and GitHub Copilot to a complete **AI Storybook pipeline** that turns a plain-English story into an illustrated, narrated, self-contained HTML book.

<p align="center">
  <img src="level-1-2-3-comparison/coffee-logo-prompt-to-design.png" height="250" alt="Level 1 — code-based design engine">
  <img src="level-1-2-3-comparison/coffee-logo-3d-render.png" height="250" alt="Level 2 — Three.js 3D render">
  <img src="level-1-2-3-comparison/coffee-logo.jpg" height="250" alt="Level 3 — diffusion model">
</p>
<p align="center"><em>One prompt — “a minimalist logo for a coffee shop” — rendered three ways:<br><b>Level 1</b> code-based design engine · <b>Level 2</b> Three.js 3D scene · <b>Level 3</b> diffusion model.</em></p>

The through-line of every skill here is the same: **Claude does the prompt engineering and orchestration**, not just a raw API call. You describe what you want in plain language; Claude turns it into a strong prompt / scene / plan, runs the right tool, verifies the result, and hands you the file.

```
your idea  →  Claude plans & prompts  →  the right generator  →  verified output
```

## 📖 Read the guides

This repo is the companion code for a series of written tutorials on [**learnwithhasan.com**](https://learnwithhasan.com/?utm_source=github&utm_medium=readme&utm_campaign=claude-image-generation&utm_content=body) that walk through how each piece was built:

| Guide | Covers |
|-------|--------|
| [Generate images in Claude Code with **no AI model**](https://learnwithhasan.com/guide/claude-code-images-no-ai-model/?utm_source=github&utm_medium=readme&utm_campaign=claude-image-generation&utm_content=body) | **Levels 1 & 2** — the code-based design engine and the Three.js 3D renderer |
| [**Free AI images** with Claude Code + **Cloudflare**](https://learnwithhasan.com/guide/free-ai-images-claude-code-cloudflare/?utm_source=github&utm_medium=readme&utm_campaign=claude-image-generation&utm_content=body) | **Level 3** — the Cloudflare Workers AI (Flux) diffusion model |
| [**Consistent AI characters** for visual stories](https://learnwithhasan.com/guide/consistent-ai-characters-visual-stories/?utm_source=github&utm_medium=readme&utm_campaign=claude-image-generation&utm_content=body) | **The Storybook pipeline** — keeping characters stable across every scene |

## Two things this repo teaches

1. **Image generation, three ways (Levels 1–3)** — the *same* "generate an image" request, solved with three very different engines, from free-and-local to a hosted diffusion model.
2. **Composing skills into an app (the Storybook pipeline)** — five skills chained end-to-end into one product.

---

## Part 1 — Image generation in three levels

The three level skills all answer "make me an image," but trade off cost, realism, and control very differently.

| Level | Skill folder | Engine | Needs an API? | Great for |
|-------|--------------|--------|---------------|-----------|
| **1** | [`level-1-image-generator/`](.claude/skills/level-1-image-generator/) | **Code-based design engine** — Pillow + numpy draw gradients, mesh fields, glow, grain, shapes, and real typography. No image model. | ❌ Free / local | Posters, quote & story/reel covers, carousel slides, wallpapers, Bauhaus/Swiss geometric art, neon/synthwave, soft product visuals — anything **typographic or designed**. Crisp text, no AI artifacts. |
| **2** | [`level-2-image-generator/`](.claude/skills/level-2-image-generator/) | **Real Three.js 3D scene**, rendered to one frame headlessly (headless-gl under Xvfb). No image model. | ❌ Free / local (Node) | 3D product shots, rendered scenes, wallpapers, thumbnail backgrounds in named styles (dark studio, Apple light, nature, sunset, underwater). |
| **3** | [`level-3-image-generator/`](.claude/skills/level-3-image-generator/) | **Diffusion model** — Cloudflare Workers AI (`flux-1-schnell`). A hosted image model. | ✅ Cloudflare keys | Photographic / illustrative looks, freeform subjects, logos & icons, quick thumbnails — anything a diffusion model does well. |

> **Why levels?** Levels 1 and 2 never touch an image model — they *construct* the picture from code, so they're free, deterministic, and perfect at text and geometry. Level 3 is the "classic" approach: hand a prompt to a diffusion model. Different jobs want different levels.
>
> 📖 Guides: [no-AI-model images (Levels 1 & 2)](https://learnwithhasan.com/guide/claude-code-images-no-ai-model/?utm_source=github&utm_medium=readme&utm_campaign=claude-image-generation&utm_content=body) · [free Cloudflare images (Level 3)](https://learnwithhasan.com/guide/free-ai-images-claude-code-cloudflare/?utm_source=github&utm_medium=readme&utm_campaign=claude-image-generation&utm_content=body)

### Level 1 — the code-based design engine

<p align="center">
  <img src="level1-examples/synthwave_poster.png" height="240" alt="Synthwave NEON HORIZON poster">
  <img src="level1-examples/quote_card.png" height="240" alt="Quote card — Build quietly. Let the work make the noise.">
  <img src="level1-examples/geometric_art.png" height="240" alt="Bauhaus geometric composition">
  <img src="level1-examples/carousel_slide.png" height="240" alt="Soft Apple-style carousel slide">
</p>

*Everything above is drawn with math and type — no image model. Crisp text, perfect alignment, no AI artifacts.* → [`level1-examples/`](level1-examples/)

### Level 2 — the Three.js 3D renderer

<p align="center">
  <img src="level2-examples/rocket_launch_station_pixar_16x9.png" height="170" alt="Low-poly rocket launch station at dusk">
  <img src="level2-examples/headphones_apple_light_1x1.png" height="170" alt="Studio-lit 3D headphones, Apple-light style">
  <img src="level2-examples/tree_flowers_16x9.png" height="170" alt="3D tree and flowers scene">
</p>

*A real 3D scene, built in code and captured as one frame — still no image model.* → [`level2-examples/`](level2-examples/)

### Level 3 — the diffusion model (Cloudflare Flux)

<p align="center">
  <img src="level3-examples/bookstore-cafe-rainy-evening.jpg" height="210" alt="Photoreal independent bookstore on a rainy evening">
  <img src="level3-examples/water-bottle-marble.jpg" height="210" alt="Product shot — water bottle on marble">
  <img src="level3-examples/ai-agents-thumbnail-bg.jpg" height="210" alt="Thumbnail background for an AI agents video">
</p>

*A hosted diffusion model doing what it does best — photographic and freeform looks.* → [`level3-examples/`](level3-examples/)

### Same prompt, three engines

[`level-1-2-3-comparison/`](level-1-2-3-comparison/) renders the coffee-shop-logo prompt through all three levels (the trio at the top of this page) — the clearest way to feel the trade-offs.

---

## Part 2 — The AI Storybook pipeline

Building on the image skills, this is a small **application**: give it an English story, get back a single self-contained `.html` storybook — a swipe/tap player with one illustration and one narration clip per scene, all embedded so the file works offline and shares as-is.

<p align="center">
  <img src="stories/the-three-gardeners/the-three-gardeners_images/part_02.png" height="250" alt="Storybook scene — grandmother and children in a flower garden">
  <img src="stories/the-three-gardeners/the-three-gardeners_images/part_05.png" height="250" alt="Storybook scene">
  <img src="stories/the-three-gardeners/the-three-gardeners_images/part_08.png" height="250" alt="Storybook scene">
</p>
<p align="center"><em>Consistent, character-stable illustrations across every scene of <b>“The Three Gardeners.”</b></em></p>

> 📖 Guide: [Consistent AI characters for visual stories](https://learnwithhasan.com/guide/consistent-ai-characters-visual-stories/?utm_source=github&utm_medium=readme&utm_campaign=claude-image-generation&utm_content=body) — how the illustrator keeps characters stable across scenes.

```
stories/{slug}.md
      │
      ▼
1. scene-splitter        → {slug}_scenes.json            estimate scenes from words/story beats; user confirms or sets count
2. story-illustrator     → {slug}_images.json (+ images) one consistent image per scene   (Copilot native image tool)
3. story-narrator        → {slug}_audio/*.mp3            per-scene clips + full-story MP3  (local VoiceStudio OmniVoice)
4a. story-html-publisher → {slug}.html                  self-contained narrated HTML
4b. story-pdf-publisher  → {slug}.pdf                   printable A4, two image + text groups per page
    (4a and 4b build in parallel after PDF background selection)
```

[`storybook-pipeline/`](.github/skills/storybook-pipeline/) is the **GitHub Copilot orchestrator** — one entry point ("make a storybook from this") that prepares scenes, illustrations, and narration, then runs the HTML and PDF publishers in parallel. It locks a shared filename convention so every image and audio clip pairs by scene index and preserves each step's approval gate.

| Skill | Role | Backend |
|-------|------|---------|
| [`story-polish/`](.github/skills/story-polish/) | Optional prose preparation: confirm RAZ-aligned level B-K and 12/24/48 scenes (default 24), then polish only if length, language, or story quality misses the project bar | GitHub Copilot |
| [`scene-splitter/`](.github/skills/scene-splitter/) | Estimate scene count from word count and story beats, ask for confirmation/custom count, then split (1 image + 1 narration each) | GitHub Copilot |
| [`story-illustrator/`](.github/skills/story-illustrator/) | One consistent PNG per scene, using local cascading references | **Copilot native `image_generation` tool** |
| [`story-narrator/`](.github/skills/story-narrator/) | Voice selection, one MP3 per scene, and a full-story MP3 | **Local VoiceStudio** (`k2-fsa/OmniVoice`, 600+ languages), VoiceStudio MCP, FFmpeg |
| [`story-html-publisher/`](.github/skills/story-html-publisher/) | Consolidate scenes + images + audio into one self-contained HTML player | Local Python, stdlib only |
| [`story-pdf-publisher/`](.github/skills/story-pdf-publisher/) | Two stacked image + original-text groups per A4 portrait page, with a chosen full-page background | Local Python, ReportLab |

### Finished examples

Three completed storybooks live in [`stories/`](stories/) — each folder has the deliverable `.html`:

- [`stories/the-three-gardeners/the-three-gardeners.html`](stories/the-three-gardeners/the-three-gardeners.html)
- [`stories/pepper-runs-off/pepper-runs-off.html`](stories/pepper-runs-off/pepper-runs-off.html)
- [`stories/the-little-cloud/the-little-cloud.html`](stories/the-little-cloud/the-little-cloud.html)

Open any of them in a browser to read the finished, narrated storybook.

---

## Project structure

```
claude-image-generation/
├── .github/skills/
│   ├── scene-splitter/             # Storybook step 1 — story → scenes
│   ├── story-illustrator/          # Storybook step 2 — Copilot native image tool
│   ├── story-narrator/             # Storybook step 3 — local VoiceStudio MP3
│   ├── story-html-publisher/       # Parallel publishing — everything → one .html
│   ├── story-pdf-publisher/        # Parallel publishing — images + text → A4 .pdf
│   └── storybook-pipeline/         # GitHub Copilot orchestrator
├── .claude/skills/
│   ├── level-1-image-generator/    # Level 1 — code-based design engine (Pillow + numpy + fonts)
│   ├── level-2-image-generator/    # Level 2 — Three.js 3D scene, rendered headlessly
│   └── level-3-image-generator/    # Level 3 — Cloudflare Workers AI (flux-1-schnell) diffusion
├── level1-examples/                # sample outputs, Level 1
├── level2-examples/                # sample outputs, Level 2
├── level3-examples/                # sample outputs, Level 3
├── level-1-2-3-comparison/         # one prompt rendered by all three levels
├── stories/                        # story .md inputs + finished storybook folders
├── .env.example                    # API key template  → copy to .env
└── .mcp.json.example               # MCP server config  → copy to .mcp.json
```

---

## Setup

Open this folder in [Claude Code](https://docs.claude.com/en/docs/claude-code) for the Level 1–3 skills, or in GitHub Copilot for the storybook pipeline. The project-local skill directories are discovered automatically. What each part needs:

### 1. Python (Levels 1 & 3, storybook helpers)

```bash
pip install pillow numpy requests python-dotenv
```

### 2. API keys — copy the template and fill in what you need

```bash
cp .env.example .env
```

| Key | Needed for | Where to get it |
|-----|-----------|-----------------|
| `CF_ACCOUNT_ID`, `CF_API_TOKEN` | **Level 3** (Cloudflare diffusion) | Cloudflare dashboard → *Workers & Pages → Overview* (Account ID) and *My Profile → API Tokens* with **Workers AI** run permission (Token). Free tier works. |

*Levels 1 & 2 and the migrated storybook skills need no API keys.* `.env` is gitignored, so your keys never get committed.

### 3. VoiceStudio for narration (storybook only)

Start your local VoiceStudio deployment on `127.0.0.1:3900`. The narrator calls its OpenAI-compatible endpoint:

```text
POST http://127.0.0.1:3900/v1/audio/speech
```

The storybook locks these request settings:

```json
{
  "model": "omnivoice",
  "voice": "<user-selected VoiceStudio profile ID or default>",
  "response_format": "mp3"
}
```

No cloud TTS service or API key is required. Verify the deployment with:

```bash
python .github/skills/story-narrator/assets/voicestudio_tts.py --check
```

If the check says `omnivoice` is unavailable, enable the `k2-fsa/OmniVoice` engine in VoiceStudio and restart the service.

For VoiceStudio MCP voice discovery, use the `VoiceStudio` HTTP server entry in
[.mcp.json.example](.mcp.json.example), pointing to `http://127.0.0.1:3900/mcp/`.
Copy it into your local `.mcp.json` (or merge the entry if that file already exists),
then reload your MCP client. The narrator lists saved voice profiles and asks
you to choose one, then uses that profile ID for every title and scene request
through the OpenAI-compatible MP3 endpoint. `default` is an explicit choice,
not a silent fallback.

FFmpeg must be installed and available on `PATH`. After generating the clips,
the narrator assembles the optional title and every scene in order into
`stories/{slug}/{slug}_audio/{slug}_full.mp3` without re-synthesis or
re-encoding. This standalone MP3 complements the HTML book, which continues
to use individual scene clips. To rebuild the full track after changing clips:

```bash
python3 .github/skills/story-narrator/assets/assemble_audio.py \
  stories/<slug>/<slug>_audio/manifest.json
```

### 4. Node (Level 2 only)

Level 2 runs `bash <skill>/scripts/setup.sh` on first use to install its npm deps and drop in the prebuilt WebGL binary — no manual step.

### 5. PDF publishing (storybook only)

Install the PDF helper's dependencies in your Python virtual environment:

```bash
python3 -m pip install -r .github/skills/story-pdf-publisher/assets/requirements.txt
```

The PDF skill asks you to choose a full-page **eye-friendly warm cream**
(`#F7F3E8`, recommended) or **white** background. The A4 portrait PDF opens with
a dedicated cover showing the title above the first illustration, followed by
an unnumbered blank page. Subsequent
pages have two vertically stacked groups, each showing an uncropped illustration
above its original scene text; there is no repeated title header. An odd final
scene occupies the top half. Total pages: `2 + ceil(scene_count / 2)`.
Story numbering starts at 1 after the blank page: odd numbers at bottom-right,
even numbers at bottom-left. The cover and blank page have no numbers.
The HTML also shows title and image on its cover, followed by every original
scene, including scene 1.

```bash
python3 .github/skills/story-pdf-publisher/assets/build_pdf.py \
  <slug> --background eye-friendly
```

Use `--background white` for white pages. Output:
`stories/{slug}/{slug}.pdf`. The PDF requires scenes and local images, not
audio or an HTML build. The pipeline builds PDF and HTML concurrently after
background approval and presents both exports for review.

---

## Using it

Ask Claude Code for the Level 1–3 image skills, or ask GitHub Copilot for the migrated storybook pipeline. Each agent picks the matching skill, does the prompt/plan work, runs the generator, verifies, and gives you the file.

**Level 1 — designed graphics**
- *"Generate a synthwave poster, chrome title NEON HORIZON, 1:2."*
- *"Make a quote card: 'Build quietly. Let the work make the noise.' — 9:16."*
- *"A Bauhaus geometric composition, bold primaries, 1:1."*

**Level 2 — 3D renders**
- *"Render a pair of headphones, Apple-light studio style, 1:1."*
- *"3D scene of a rocket launch station, 16:9."*

**Level 3 — diffusion model**
- *"Generate a thumbnail background for a video about AI agents."*
- *"A cozy bookstore café on a rainy evening."*

**Storybook pipeline (GitHub Copilot)**
- Drop a story in `stories/my-story.md`, then: *"Run the storybook pipeline on stories/my-story.md."*
- Or a single step: *"Illustrate this story"* / *"Narrate this story."*

You can also run the Level 3 script directly:

```bash
python .claude/skills/level-3-image-generator/generate.py "a cyberpunk cat coding at night" -o cat.jpg
```

---

## How a skill works

An Agent Skill is a folder with a `SKILL.md`. The YAML frontmatter's `description` tells the agent **when** to use the skill; the markdown body tells it **how**. Claude Code discovers the Level 1–3 skills under `.claude/skills/`, while GitHub Copilot discovers the storybook skills under `.github/skills/`.

## A note on secrets

Keep real keys in `.env` and `.mcp.json` only (both gitignored) — never in code or committed config. If a token ever lands in a commit, rotate it at the provider — the value stays recoverable from git history otherwise.

## License

Released under the [MIT License](LICENSE) © 2026 Hasan Aboul Hasan — use, adapt, and build on it freely.

The fonts bundled in [`level-1-image-generator/fonts/`](.claude/skills/level-1-image-generator/fonts/) are **not** covered by MIT; each is licensed under the **SIL Open Font License 1.1**, with its own `*-OFL.txt` license file shipped alongside it.

---

Built by [Hasan Aboul Hasan](https://learnwithhasan.com/?utm_source=github&utm_medium=readme&utm_campaign=claude-image-generation&utm_content=body)

<!-- lwh-footer -->

---

## 📘 The free book

This repo is one thing I built with AI. The book is the system underneath it.

**[Vibe Engineering Blocks](https://learnwithhasan.com/blocks/?utm_source=github&utm_medium=readme&utm_campaign=claude-image-generation&utm_content=footer)** is my free 74-page book.
47 building blocks for shipping real apps with AI. One block per page, each with the exact
prompt to hand your AI.

Built by **[Hasan Aboul Hasan](https://learnwithhasan.com/?utm_source=github&utm_medium=readme&utm_campaign=claude-image-generation&utm_content=footer)**. I build real products with AI and
write down exactly how.
[Guides](https://learnwithhasan.com/guides/?utm_source=github&utm_medium=readme&utm_campaign=claude-image-generation&utm_content=footer) &nbsp;·&nbsp;
[YouTube](https://www.youtube.com/@HasanAboulHasan) &nbsp;·&nbsp;
[Community](https://learnwithhasan.com/community/?utm_source=github&utm_medium=readme&utm_campaign=claude-image-generation&utm_content=footer)
