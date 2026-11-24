---
name: story-pdf-publisher
description: Assemble a printable A4 portrait storybook PDF from scenes and local illustrations. Ask the user to choose a full-page eye-friendly warm cream or white background, then place two stacked image-and-original-text groups on each page. Runs alongside story-html-publisher in storybook-pipeline. Use when the user wants a storybook PDF, printable story, A4 export, or two scenes per page. Does not generate or rewrite content.
---

# Story PDF Publisher

Package existing scenes and illustrations into `stories/{slug}/{slug}.pdf`.
A dedicated A4 portrait cover shows the story title above the first illustration.
A blank, unnumbered page follows the cover. Each subsequent story page contains two groups, stacked vertically: an illustration
above its original scene text. Scene order and image/text pairing are preserved,
including scene 1 after the cover.

## Inputs

Read these files directly, not the HTML publisher's generated JSON:
- `stories/{slug}/{slug}_scenes.json`
- `stories/{slug}/{slug}_images.json`
- Local PNG files referenced by `shots[].path`

Audio is not required or embedded. The PDF and HTML publishers have independent
outputs and can build concurrently without modifying their shared inputs.

## Workflow

### 1. Discover and validate

Determine the slug from the user's argument or the single relevant scenes file;
ask if ambiguous. Match scene and image indices exactly. Require a non-empty,
contiguous scene sequence starting at 1 and one valid local image per scene.
Support absolute, repository-relative, and story-directory-relative image paths.
Do not download remote images, invent placeholders, or silently skip scenes.

Check for an existing PDF and ask whether to keep it or replace it, defaulting
to keep. Confirm ReportLab is installed in the Python environment used for the
build. If missing, install the declared dependencies:

```bash
python3 -m pip install -r .github/skills/story-pdf-publisher/assets/requirements.txt
```

Use a virtual environment rather than changing a shared/system Python install.

### 2. HARD GATE: choose the background

Use `ask_user` with these labeled choices:
- `eye-friendly`: warm cream `#F7F3E8`, recommended.
- `white`: white `#FFFFFF`.

The color covers the entire page, including margins and unused space. Do not
silently pick a background. If the orchestrator already collected a choice,
reuse it and skip this prompt. A fully automatic run may use the recommended
background only when the user explicitly authorized defaults.

Explain the fixed layout before building:
- A4 portrait cover: title above the first scene's complete image, no body text or page number.
- After the cover, insert one blank page with the chosen background and no text, images, or number.
- Story pages follow the blank page, with exactly two scene slots per page; image above its text in each slot.
- Preserve each complete image's aspect ratio; fit without cropping/stretching.
- Readable 13-point serif text, dark ink, comfortable line spacing.
- Title appears only on the cover, not as a repeated header on story pages.
- Story-page numbering starts at 1 after the unnumbered cover and blank page.
- Show only the page number, not a total: odd numbers at bottom-right, even numbers at bottom-left, aligned to the outer margin.
- An odd last scene occupies the top slot; the bottom slot stays empty.
- Total pages: `2 + ceil(total_scenes / 2)`, including the cover and blank page.

### 3. Build

From the repository root, run with the approved choice:

```bash
python3 .github/skills/story-pdf-publisher/assets/build_pdf.py \
  <slug> --background <eye-friendly|white>
```

Options mirror the HTML helper where relevant:
- `--stories-dir PATH`: defaults to `stories`.
- `--out PATH`: defaults to `stories/{slug}/{slug}.pdf`.

The helper validates and lays out all groups before replacing the output
atomically. Missing/corrupt images, mismatched indices, unsupported text
characters, or text too long for its slot are explicit errors. Never shrink
text to an unreadable size, truncate prose, overwrite a valid PDF with a failed
build, or claim a partial PDF is complete. This beginner English layout supports
WinAnsi characters; unsupported scripts require an explicit font/layout change.

### 4. HARD GATE: review the PDF

Report the PDF path, size, background, scene count, and A4 page count.
Verify `2 + ceil(N / 2)` A4 portrait pages: an unnumbered title-and-image cover,
an unnumbered blank page, then consecutive scene pairs with complete text and
no repeated title headers. Check that story numbers start at 1 and alternate
bottom-right (odd) and bottom-left (even). Inspect the cover and story pages when possible.

Ask the user to open the PDF in a PDF viewer and review it:
- `done`: finish.
- `rebuild`: rebuild after an approved change.
- `background eye-friendly` / `background white`: change background and rebuild.
- `fix image N` / `fix text N`: return to the relevant upstream skill, then rebuild.

When running inside the pipeline, both publishers build concurrently after
background approval. Present their final review surfaces together, rather than
launching competing interactive prompts. Do not declare the pipeline complete
until both outputs have been validated and reviewed.

## Limits

- No new story text, illustrations, audio, or uploads.
- No dependency on the HTML output or narration.
- No partial PDFs or remote image fallback.
- A full-page background is present in the file; edge-to-edge paper printing
  depends on the printer's borderless-printing support.
