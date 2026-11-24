import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image
from pypdf import PdfReader
from pypdf.generic import ContentStream
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth

from build_pdf import BACKGROUNDS, MARGIN, build_pdf


class BuildPdfTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.stories = Path(self.temp.name)
        self.work = self.stories / "test-story"
        self.work.mkdir()
        self.texts = [
            'First scene: <a leaf> & "sunshine".',
            "Second scene: a quiet garden.",
            "Third scene: the friends wave goodbye.",
        ]
        self.spine = {
            "story_title": "Test Story", "total_scenes": 3,
            "scenes": [{"index": i, "text": text} for i, text in enumerate(self.texts, 1)],
        }
        self.registry = {"shots": []}
        for i, (size, color) in enumerate(
            [((300, 200), "green"), ((200, 300), "blue"), ((300, 200), "red")], 1
        ):
            path = self.work / ("part_%02d.png" % i)
            Image.new("RGB", size, color).save(path)
            self.registry["shots"].append({"index": i, "path": path.name})
        self.registry["shots"].reverse()
        self.write_inputs()

    def write_inputs(self):
        (self.work / "test-story_scenes.json").write_text(json.dumps(self.spine))
        (self.work / "test-story_images.json").write_text(json.dumps(self.registry))

    def test_a4_pairs_odd_last_page_and_full_page_backgrounds(self):
        for background, hex_color in BACKGROUNDS.items():
            with self.subTest(background=background):
                output, count = build_pdf("test-story", self.stories, background)
                reader = PdfReader(output)
                self.assertEqual(count, 4)
                self.assertEqual(len(reader.pages), 4)
                for i, page in enumerate(reader.pages):
                    self.assertAlmostEqual(float(page.mediabox.width), A4[0], places=3)
                    self.assertAlmostEqual(float(page.mediabox.height), A4[1], places=3)
                    text = page.extract_text()
                    self.assertEqual("Test Story" in text, i == 0)
                    for j, scene_text in enumerate(self.texts):
                        self.assertEqual(scene_text in text, j // 2 + 2 == i)
                    if i >= 2:
                        self.assertEqual(text.strip().splitlines()[-1], str(i - 1))
                    elif i == 1:
                        self.assertEqual(text.strip(), "")
                    self.assertNotIn(" / ", text)
                    stream = ContentStream(page.get_contents(), reader)
                    colors = [operands for operands, op in stream.operations if op == b"rg"]
                    expected = [int(hex_color[j:j + 2], 16) / 255 for j in (1, 3, 5)]
                    for actual, component in zip(colors[0], expected):
                        self.assertAlmostEqual(float(actual), component, places=5)
                    rectangles = [a for a, op in stream.operations if op == b"re"]
                    self.assertEqual([float(n) for n in rectangles[0][:2]], [0, 0])
                    self.assertAlmostEqual(float(rectangles[0][2]), A4[0], places=3)
                    self.assertAlmostEqual(float(rectangles[0][3]), A4[1], places=3)
                    images = page["/Resources"].get("/XObject", {})
                    self.assertEqual(len(images), 0 if i == 1 else (2 if i == 2 else 1))
                    if i == 0:
                        cover_image = next(iter(images.values())).get_object()
                        self.assertEqual((cover_image["/Width"], cover_image["/Height"]), (300, 200))
                    matrix = None
                    image_boxes = []
                    for operands, op in stream.operations:
                        if op == b"cm":
                            matrix = [float(n) for n in operands]
                        elif op == b"Do":
                            image = images[operands[0]]
                            image_boxes.append(matrix)
                            self.assertAlmostEqual(
                                matrix[0] / matrix[3], image["/Width"] / image["/Height"],
                                places=5,
                            )
                            self.assertGreaterEqual(matrix[4], 0)
                            self.assertGreaterEqual(matrix[5], 0)
                            self.assertLessEqual(matrix[4] + matrix[0], A4[0])
                            self.assertLessEqual(matrix[5] + matrix[3], A4[1])
                    if len(image_boxes) == 2:
                        self.assertGreater(image_boxes[0][5], image_boxes[1][5])

    def test_cover_does_not_consume_first_scene_for_single_and_even_counts(self):
        scenes = self.spine["scenes"]
        shots = self.registry["shots"]
        for count in (1, 2):
            with self.subTest(count=count):
                self.spine["scenes"] = scenes[:count]
                self.spine["total_scenes"] = count
                self.registry["shots"] = [
                    shot for shot in shots if shot["index"] <= count
                ]
                self.write_inputs()
                output, pages = build_pdf("test-story", self.stories, "white")
                reader = PdfReader(output)
                self.assertEqual(pages, 3)
                self.assertIn("Test Story", reader.pages[0].extract_text())
                self.assertNotIn(self.texts[0], reader.pages[0].extract_text())
                for text in self.texts[:count]:
                    self.assertIn(text, reader.pages[2].extract_text())

    def test_story_numbers_alternate_outer_corners_after_blank_page(self):
        self.spine["scenes"] = [
            {"index": i, "text": "Scene %d content." % i} for i in range(1, 9)
        ]
        self.spine["total_scenes"] = 8
        self.registry["shots"] = [
            {"index": i, "path": "part_01.png"} for i in range(1, 9)
        ]
        self.write_inputs()
        output, count = build_pdf("test-story", self.stories, "white")
        reader = PdfReader(output)
        self.assertEqual(count, 6)
        self.assertEqual(reader.pages[0].extract_text().strip(), "Test Story")
        self.assertEqual(reader.pages[1].extract_text().strip(), "")
        for number, page in enumerate(reader.pages[2:], 1):
            stream = ContentStream(page.get_contents(), reader)
            matrices = [a for a, op in stream.operations if op == b"Tm"]
            footer = matrices[-1]
            expected_x = (
                A4[0] - MARGIN - stringWidth(str(number), "Times-Roman", 10)
                if number % 2 else MARGIN
            )
            self.assertAlmostEqual(float(footer[4]), expected_x, places=3)
            self.assertAlmostEqual(float(footer[5]), MARGIN, places=3)
            self.assertEqual(page.extract_text().strip().splitlines()[-1], str(number))

    def test_missing_corrupt_images_and_index_mismatches_preserve_output(self):
        output = self.work / "test-story.pdf"
        output.write_bytes(b"existing-pdf")
        for mode in ("missing", "corrupt", "duplicate", "extra"):
            with self.subTest(mode=mode):
                original = json.loads(json.dumps(self.registry))
                if mode == "missing":
                    self.registry["shots"][0]["path"] = "missing.png"
                elif mode == "corrupt":
                    path = self.work / "bad.png"
                    path.write_bytes(b"not-a-png")
                    self.registry["shots"][0]["path"] = path.name
                elif mode == "duplicate":
                    self.registry["shots"][0]["index"] = 1
                else:
                    self.registry["shots"].append({"index": 4, "path": "part_01.png"})
                self.write_inputs()
                with self.assertRaises((OSError, ValueError)):
                    build_pdf("test-story", self.stories, "white")
                self.assertEqual(output.read_bytes(), b"existing-pdf")
                self.registry = original

    def test_overflow_and_unsupported_text_are_explicit_errors(self):
        for text, error in (
            ("A very long scene. " * 500, "too long"),
            ("An unsupported character: \u4e2d", "unsupported"),
        ):
            with self.subTest(error=error):
                self.spine["scenes"][0]["text"] = text
                self.write_inputs()
                with self.assertRaisesRegex(ValueError, error):
                    build_pdf("test-story", self.stories, "eye-friendly")
                self.assertFalse((self.work / "test-story.pdf").exists())


if __name__ == "__main__":
    unittest.main()
