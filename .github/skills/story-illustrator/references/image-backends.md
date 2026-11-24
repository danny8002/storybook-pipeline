# GitHub Copilot Native Image Tool

The illustrator's consistency workflow is backend-specific now: image generation comes from GitHub Copilot's built-in `image_generation` tool. The skill must not fall back to Fal or another external image API.

## Required operation

Each tool call creates one PNG from:

```json
{
  "prompt": "<complete prompt>",
  "input_images": [
    { "path": "stories/<slug>/<slug>_images/ref_character.png" }
  ],
  "size": "1536x1024",
  "quality": "high"
}
```

`input_images` is optional for reference plates and required when a scene depends on character, location, or previous-scene references.

## Offered output sizes

| Skill label | Tool `size` |
|---|---|
| Landscape, default | `1536x1024` |
| Portrait | `1024x1536` |

Lock one size for the full run. Do not ask for unsupported custom dimensions or a model name.

## Saving the result

The tool returns an image artifact with a local path. Copy or move that PNG immediately to the locked target:

```text
stories/<slug>/<slug>_images/ref_<name>.png
stories/<slug>/<slug>_images/part_<NN>.png
```

Verify the target exists and is non-empty before updating `{slug}_images.json`.

## Reference ordering

1. Character references.
2. Location reference.
3. Previous scene, for SOFT/MICRO continuity.

For a retry, place the previous attempt first. For a MICRO cut, place the previous scene first.

Keep all input paths local and identify every reference in the prompt by array order. The tool accepts up to 16 input images, though shorter reference sets are normally clearer.

## Retry

A correction is still one `image_generation` call:
- same locked size and `quality: "high"`;
- previous attempt as the first input;
- required character/location references after it;
- explicit `CORRECTIONS` and `KEEP UNCHANGED` sections in the prompt.

Overwrite `part_NN.png` only after a valid PNG is returned.

## What remains backend-independent

- the visual bible;
- continuity classification;
- prompt constraints;
- reference ordering;
- QA and correction workflow;
- the `{slug}_images.json` shape and local-path pairing.
