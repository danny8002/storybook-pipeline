---
name: story-narrator
description: Generates per-scene MP3 narration and a full-story MP3 through local VoiceStudio OmniVoice. Lists saved voices through VoiceStudio MCP and asks the user to select one before synthesis. Reads {slug}_scenes.json, drafts narration for review, and saves scene clips, {slug}_full.mp3, and a manifest under the story audio directory. Use whenever the user wants to narrate a story, generate per-scene TTS, voice a storybook, or make read-along narration. Requires local VoiceStudio, its MCP connection, and FFmpeg.
---

# Story Narrator

Turns a split story into one MP3 narration clip per scene plus a full-story MP3 using the local VoiceStudio deployment:

```text
stories/{slug}/{slug}_audio/{slug}_part_NN.mp3
stories/{slug}/{slug}_audio/{slug}_full.mp3
```

## When this skill applies

Use this skill when `stories/{slug}/{slug}_scenes.json` exists and the user wants per-scene narration. If the source story is not split, invoke `scene-splitter` first.

Do not use this skill for:
- A single standalone utterance.
- Music or sound effects.
- Cloud TTS or an ElevenLabs workflow.
- Inventing or rewriting the story.

## Required backend

Use **VoiceStudio**, not ElevenLabs, at:

```text
http://127.0.0.1:3900/v1/audio/speech
```

Use VoiceStudio MCP at `http://127.0.0.1:3900/mcp/` to list saved voices and collect the user's selection. Use the OpenAI-compatible endpoint above for MP3 synthesis; MCP `generate_speech` does not currently offer MP3.

Every synthesis request uses:

```json
{
  "model": "omnivoice",
  "voice": "<selected profile ID, or explicitly selected default>",
  "input": "<scene narration>",
  "response_format": "mp3"
}
```

OmniVoice (`k2-fsa/OmniVoice`) supports 600+ languages; its VoiceStudio API model ID is `omnivoice`. Do not substitute `tts-1`, add an ElevenLabs `voice_id`, or request WAV.

Use the bundled stdlib helper:

```bash
python .github/skills/story-narrator/assets/voicestudio_tts.py \
  --check
```

The check must succeed before generation. It verifies that the configured VoiceStudio deployment actually advertises `omnivoice`; it does not generate or consume a clip. If the engine is unavailable, enable the `k2-fsa/OmniVoice` engine and restart VoiceStudio.

Also verify that VoiceStudio MCP exposes `list_voices` and that `ffmpeg` is available. If either is unavailable, stop and ask the user to repair the connection or install FFmpeg; do not silently skip voice selection or the full-story MP3.

Set `VOICESTUDIO_BASE_URL` only when the local deployment is intentionally exposed at another base URL. The model and MP3 format remain fixed.

## Workflow — voice-selection and script-review gates

### Stage 0: Load scenes

Read `{slug}_scenes.json`. Treat each scene's `text` as the source narration. The scene at index N maps to `{slug}_part_NN.mp3`.

### Stage 1: Intake and analysis

1. Read all scene texts.
2. Count scenes, total characters, and dialogue percentage.
3. Report:
   > N scenes, ~C total characters, ~D% dialogue. Recommendation: single narrator.

### Stage 2: Lock voice settings

1. Discover the VoiceStudio MCP `list_voices` tool, then call it.
2. Show a compact list of profile names, IDs, and available language/type information. Do not copy reference transcripts, consent records, or other unnecessary profile fields into the script or manifest.
3. Use `ask_user` to let the user choose a saved voice. Use profile IDs as option values and names as display labels. Include `default` as an explicit option, never a silent fallback. If no profiles are saved, explain this and ask whether to use `default` or wait for a profile to be created.
4. Resolve the selection against the returned profiles and lock its exact ID and display name. If the user already supplied an unambiguous valid profile, validate and reuse it without asking again. Unknown IDs, ambiguous names, listing failures, and unavailable profiles must be surfaced, not replaced with `default`.

Use one narrator and one consistent selected voice for the full run:
- Endpoint: `http://127.0.0.1:3900`
- Model: OmniVoice (`k2-fsa/OmniVoice`, `omnivoice`, 600+ languages)
- Voice: selected saved profile ID (or explicitly selected `default`)
- Format: MP3

Pass the selected ID through the helper's `--voice` option on every scene and title request. The speech endpoint accepts saved profile IDs; do not send an MCP-only `profile_id` field to this endpoint. Never use a display name when an ID is available.

Voice selection is its own gate; the later script approval does not replace it.

### Stage 3: Draft the narration script

Prepare one section per scene containing:
- `original` — the exact scene text;
- `delivery` — a short performance direction, derived from the scene mood;
- optional punctuation changes only when the story text is unchanged semantically.

Do not insert ElevenLabs-style tags such as `[warmly]` or `[whispering]`; VoiceStudio's `input` field receives plain narration text.

Use the story title for a short optional `title.mp3`.

Show the selected voice name and ID in the script. Delivery notes are review guidance, not spoken text or an assurance that arbitrary style instructions are supported.

Write:

```text
stories/{slug}/{slug}_audio/narration_script.md
```

### Stage 4: HARD GATE — review the script

Show the script and pause:

> Narration script ready — review before I generate audio. Reply `go`, `edit`, or paste corrections.

Do not generate audio before explicit approval. This is a quality gate: VoiceStudio synthesis is local, but every correction still costs time and can produce a different take.

### Stage 5: Generate MP3 clips

Run the helper once per scene:

```bash
python .github/skills/story-narrator/assets/voicestudio_tts.py \
  --voice "<selected profile ID or default>" \
  --text "<approved plain narration>" \
  --out "stories/<slug>/<slug>_audio/<slug>_part_<NN>.mp3"
```

For narration containing shell-sensitive quotes, use `--text-file <path>` or `--stdin` instead of interpolating it into a command string.

The helper sends:

```json
{
  "model": "omnivoice",
  "voice": "<selected profile ID or default>",
  "input": "<approved narration>",
  "response_format": "mp3"
}
```

It writes the response directly to the final MP3 path and exits non-zero on connectivity, HTTP, empty-response, or invalid-MP3 errors. Do not rename a WAV or convert an incorrect response silently.

If a clip fails:
1. Preserve the exact scene index and helper error.
2. Continue with other independent scenes if practical.
3. Retry the failed scene after VoiceStudio is healthy.
4. Never claim the narration stage is complete until every scene file exists and is non-empty.

Generate the optional title clip the same way and save it as `title.mp3`.

After generation, write `{slug}_audio/manifest.json`:

```json
{
  "story_slug": "the-little-cloud",
  "endpoint": "http://127.0.0.1:3900/v1/audio/speech",
  "model": "omnivoice",
  "model_name": "OmniVoice (k2-fsa/OmniVoice, 600+ languages)",
  "voice": "<selected profile ID or default>",
  "voice_name": "<selected display name>",
  "response_format": "mp3",
  "title_audio": {
    "filename": "title.mp3",
    "original": "The Little Cloud"
  },
  "parts": [
    {
      "index": 1,
      "filename": "the-little-cloud_part_01.mp3",
      "original": "High in the sky...",
      "delivery": "gentle and bright",
      "mood": "gentle, bright",
      "scene": "wide blue sky"
    }
  ]
}
```

### Stage 6: Assemble the full-story MP3

After every scene clip and the optional title clip are complete, run:

```bash
python .github/skills/story-narrator/assets/assemble_audio.py \
  "stories/<slug>/<slug>_audio/manifest.json"
```

The helper uses FFmpeg to concatenate the optional title first, then all scene clips in ascending index order, without re-synthesis or re-encoding. This preserves the approved voice and takes and avoids the speech endpoint's 4,096-character request limit. Never concatenate MP3 files by raw byte appending.

It validates contiguous scene indices and MP3 inputs, writes `{slug}_full.mp3`, and records `full_audio` in the manifest:

```json
{
  "full_audio": {
    "filename": "the-little-cloud_full.mp3",
    "includes_title": true,
    "scene_indices": [1]
  }
}
```

The example contains one scene; real `scene_indices` must include every scene. Missing/invalid clips or FFmpeg failures are errors; do not claim completion or build a partial full-story track. Verify the output is non-empty and playable and that its duration matches the sum of input durations within MP3 frame-padding tolerance.

Confirm the selected voice, scene clip count, optional title clip, full-story MP3 path, any failures, and audio directory. The HTML publisher still embeds the scene clips; the full MP3 is a separate downloadable deliverable.

## Regeneration

To redo scenes, rerun only those clip commands. The helper atomically overwrites the target MP3, so filenames remain stable and index pairing is preserved.

After changing any scene/title clip, rerun assembly so the full MP3 is not stale. If the voice changes, obtain approval and regenerate every scene and title clip with the newly selected voice before reassembling; never mix voices silently. When resuming, reuse the manifest's saved selection unless the user requests a change.

## What this skill does not do

- Does not edit or rewrite the story.
- Does not generate music or effects.
- Does not use ElevenLabs, cloud credentials, or an ElevenLabs `voice_id`. VoiceStudio MCP is used for voice discovery, not MP3 synthesis.
- Does not automatically listen to or QA the output; final audio approval belongs to the user.
- Does not generate WAV files.
