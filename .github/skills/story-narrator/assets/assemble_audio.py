#!/usr/bin/env python3
"""Assemble approved narration clips into one full-story MP3 using FFmpeg."""

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

from voicestudio_tts import looks_like_mp3, write_atomic


def collect_clips(manifest: dict, directory: Path) -> list[Path]:
    parts = manifest.get("parts")
    if not isinstance(parts, list) or not parts:
        raise ValueError("Manifest must contain at least one scene in parts")
    if any(not isinstance(p, dict) or type(p.get("index")) is not int for p in parts):
        raise ValueError("Each scene must have an integer index")
    parts = sorted(parts, key=lambda p: p["index"])
    if [p["index"] for p in parts] != list(range(1, len(parts) + 1)):
        raise ValueError("Scene indices must be unique and contiguous, starting at 1")
    entries = ([manifest["title_audio"]] if manifest.get("title_audio") else []) + parts
    clips = []
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("filename"), str):
            raise ValueError("Each audio entry must have a filename")
        filename = entry["filename"]
        if not filename or Path(filename).name != filename:
            raise ValueError("Audio filenames must be local basenames")
        clip = directory / filename
        if clip.suffix.lower() != ".mp3" or not looks_like_mp3(clip.read_bytes()):
            raise ValueError("Missing or invalid MP3: %s" % clip)
        clips.append(clip)
    if len(set(clips)) != len(clips):
        raise ValueError("Each title and scene must reference a distinct clip")
    return clips


def assemble(manifest_path: Path) -> Path:
    manifest_path = manifest_path.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("Manifest must be a JSON object")
    slug = manifest.get("story_slug")
    if not isinstance(slug, str) or not re.fullmatch(r"[a-z0-9-]{1,60}", slug):
        raise ValueError("Manifest story_slug must be a lowercase ASCII slug")
    clips = collect_clips(manifest, manifest_path.parent)
    output = manifest_path.parent / (slug + "_full.mp3")
    if output in clips:
        raise ValueError("Full-story output cannot also be an input clip")
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("FFmpeg is required to assemble the full-story MP3")
    with tempfile.TemporaryDirectory(prefix=".narration-", dir=manifest_path.parent) as tmp:
        work = Path(tmp)
        for i, clip in enumerate(clips):
            (work / ("%04d.mp3" % i)).symlink_to(clip)
        listing = work / "clips.txt"
        listing.write_text(
            "".join("file '%04d.mp3'\n" % i for i in range(len(clips))),
            encoding="utf-8",
        )
        result = subprocess.run(
            [ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error",
             "-f", "concat", "-safe", "1", "-i", str(listing),
             "-map", "0:a:0", "-c:a", "copy", str(work / "full.mp3")],
            capture_output=True, text=True,
        )
        if result.returncode:
            raise RuntimeError("FFmpeg assembly failed: %s" % result.stderr.strip())
        if not looks_like_mp3((work / "full.mp3").read_bytes()):
            raise RuntimeError("FFmpeg did not produce a valid MP3")
        os.replace(work / "full.mp3", output)
    manifest["full_audio"] = {
        "filename": output.name,
        "includes_title": bool(manifest.get("title_audio")),
        "scene_indices": list(range(1, len(manifest["parts"]) + 1)),
    }
    write_atomic(str(manifest_path), (json.dumps(manifest, indent=2) + "\n").encode("utf-8"))
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="Narration manifest.json")
    args = parser.parse_args()
    try:
        output = assemble(args.manifest)
    except (OSError, ValueError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps({"path": str(output), "bytes": output.stat().st_size}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
