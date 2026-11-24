import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from assemble_audio import assemble, collect_clips
from voicestudio_tts import looks_like_mp3


class AssembleAudioTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.manifest = {
            "story_slug": "test-story",
            "title_audio": {"filename": "title.mp3"},
            "parts": [
                {"index": 2, "filename": "part_02.mp3"},
                {"index": 1, "filename": "part_01.mp3"},
            ],
        }
        for name in ("title.mp3", "part_01.mp3", "part_02.mp3"):
            (self.directory / name).write_bytes(b"ID3-test")

    def test_orders_title_then_scenes_and_supports_no_title(self):
        self.assertEqual(
            [p.name for p in collect_clips(self.manifest, self.directory)],
            ["title.mp3", "part_01.mp3", "part_02.mp3"],
        )
        del self.manifest["title_audio"]
        self.assertEqual(
            [p.name for p in collect_clips(self.manifest, self.directory)],
            ["part_01.mp3", "part_02.mp3"],
        )

    def test_rejects_gaps_duplicates_and_invalid_audio(self):
        for indices in ([1, 3], [1, 1]):
            with self.subTest(indices=indices):
                manifest = {"parts": [
                    {"index": i, "filename": "part_01.mp3"} for i in indices
                ]}
                with self.assertRaisesRegex(ValueError, "unique and contiguous"):
                    collect_clips(manifest, self.directory)
        (self.directory / "part_01.mp3").write_bytes(b"RIFF-not-mp3")
        with self.assertRaisesRegex(ValueError, "invalid MP3"):
            collect_clips(self.manifest, self.directory)
        (self.directory / "part_01.mp3").unlink()
        with self.assertRaises(FileNotFoundError):
            collect_clips(self.manifest, self.directory)

    def test_ffmpeg_failure_preserves_existing_output_and_manifest(self):
        path = self.directory / "manifest.json"
        original = json.dumps(self.manifest)
        path.write_text(original)
        output = self.directory / "test-story_full.mp3"
        output.write_bytes(b"ID3-existing")
        with patch("assemble_audio.shutil.which", return_value="/ffmpeg"), patch(
            "assemble_audio.subprocess.run",
            return_value=subprocess.CompletedProcess([], 1, "", "bad clip"),
        ):
            with self.assertRaisesRegex(RuntimeError, "bad clip"):
                assemble(path)
        self.assertEqual(path.read_text(), original)
        self.assertEqual(output.read_bytes(), b"ID3-existing")
        self.assertFalse(list(self.directory.glob(".narration-*")))

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
    def test_builds_playable_full_mp3_and_updates_manifest(self):
        durations = [0.2, 0.4, 0.6]
        for name, duration in zip(
            ("title.mp3", "part_01.mp3", "part_02.mp3"), durations
        ):
            subprocess.run(
                ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
                 "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=24000",
                 "-t", str(duration), str(self.directory / name)],
                check=True, capture_output=True,
            )
        path = self.directory / "manifest.json"
        path.write_text(json.dumps(self.manifest))
        output = assemble(path)
        self.assertTrue(looks_like_mp3(output.read_bytes()))

        def duration(clip):
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", str(clip)],
                check=True, capture_output=True, text=True,
            )
            return float(result.stdout)

        self.assertAlmostEqual(
            duration(output),
            sum(duration(p) for p in collect_clips(self.manifest, self.directory)),
            delta=len(durations) * 2 * 576 / 24000,
        )
        subprocess.run(
            ["ffmpeg", "-nostdin", "-v", "error", "-i", str(output), "-f", "null", "-"],
            check=True, capture_output=True,
        )
        saved = json.loads(path.read_text())
        self.assertEqual(saved["parts"], self.manifest["parts"])
        self.assertEqual(saved["full_audio"], {
            "filename": "test-story_full.mp3",
            "includes_title": True,
            "scene_indices": [1, 2],
        })


if __name__ == "__main__":
    unittest.main()
