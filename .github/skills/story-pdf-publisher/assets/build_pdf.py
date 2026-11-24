#!/usr/bin/env python3
"""Build an A4 PDF with two stacked illustration-and-text groups per page."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from html import escape
from io import BytesIO
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph


BACKGROUNDS = {"eye-friendly": "#F7F3E8", "white": "#FFFFFF"}
INK = HexColor("#292720")
MARGIN = 12 * mm
COVER_TITLE_HEIGHT = 40 * mm
FOOTER_HEIGHT = 8 * mm
GROUP_GAP = 10 * mm
IMAGE_TEXT_GAP = 4 * mm
MIN_IMAGE_HEIGHT = 25 * mm
TEXT_STYLE = ParagraphStyle(
    "story", fontName="Times-Roman", fontSize=13, leading=17, textColor=INK,
)
TITLE_STYLE = ParagraphStyle(
    "title", fontName="Times-Bold", fontSize=26, leading=32, textColor=INK,
    alignment=1,
)


@dataclass
class Group:
    index: int
    image: ImageReader
    image_width: float
    image_height: float
    paragraph: Paragraph
    text_height: float


def read_json(path: Path) -> dict:
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError("%s must contain a JSON object" % path)
    return document


def indices(entries: list, label: str) -> list[int]:
    if not isinstance(entries, list) or not entries:
        raise ValueError("%s must be a non-empty list" % label)
    if any(not isinstance(e, dict) or type(e.get("index")) is not int for e in entries):
        raise ValueError("%s entries must have integer indices" % label)
    result = [e["index"] for e in entries]
    if sorted(result) != list(range(1, len(entries) + 1)):
        raise ValueError("%s indices must be unique and contiguous, starting at 1" % label)
    return result


def paragraph(text: str, style: ParagraphStyle, label: str) -> Paragraph:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("%s must contain non-empty text" % label)
    try:
        text.encode("cp1252")
    except UnicodeEncodeError as exc:
        raise ValueError("%s contains characters unsupported by the PDF font" % label) from exc
    return Paragraph(escape(text).replace("\n", "<br/>"), style)


def load_groups(work: Path, slug: str, width: float, height: float) -> tuple[Paragraph, list[Group]]:
    spine = read_json(work / (slug + "_scenes.json"))
    registry = read_json(work / (slug + "_images.json"))
    scenes = spine.get("scenes")
    shots = registry.get("shots")
    scene_indices = indices(scenes, "Scene")
    if set(indices(shots, "Image")) != set(scene_indices):
        raise ValueError("Scene and image indices must match exactly")
    if spine.get("total_scenes") != len(scenes):
        raise ValueError("total_scenes does not match the scene count")
    title = paragraph(spine.get("story_title"), TITLE_STYLE, "Story title")
    if title.wrap(width, COVER_TITLE_HEIGHT)[1] > COVER_TITLE_HEIGHT:
        raise ValueError("Story title is too long for the PDF cover")
    by_index = {e["index"]: e for e in shots}
    groups = []
    for scene in sorted(scenes, key=lambda e: e["index"]):
        index = scene["index"]
        text = paragraph(scene.get("text"), TEXT_STYLE, "Scene %d" % index)
        text_height = text.wrap(width, height)[1]
        image_height = height - text_height - IMAGE_TEXT_GAP
        if image_height < MIN_IMAGE_HEIGHT:
            raise ValueError("Scene %d text is too long for its A4 slot" % index)
        source = by_index[index].get("path")
        if not isinstance(source, str) or not source or "://" in source:
            raise ValueError("Scene %d requires a local image path" % index)
        image_path = Path(source)
        if not image_path.is_absolute() and not image_path.exists():
            image_path = work / image_path
        raw = image_path.read_bytes()
        if not raw.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError("Scene %d image is not a PNG: %s" % (index, image_path))
        image = ImageReader(BytesIO(raw))
        original_width, original_height = image.getSize()
        image.getRGBData()
        scale = min(width / original_width, image_height / original_height)
        groups.append(Group(index, image, original_width * scale,
                            original_height * scale, text, text_height))
    return title, groups


def build_pdf(slug: str, stories_dir: Path, background: str, output: Path | None = None) -> tuple[Path, int]:
    if not re.fullmatch(r"[a-z0-9-]{1,60}", slug):
        raise ValueError("Slug must be lowercase, hyphenated ASCII, at most 60 characters")
    if background not in BACKGROUNDS:
        raise ValueError("Choose eye-friendly or white background")
    work = stories_dir / slug
    page_width, page_height = A4
    width = page_width - 2 * MARGIN
    top = page_height - MARGIN
    group_height = (top - MARGIN - FOOTER_HEIGHT - GROUP_GAP) / 2
    title, groups = load_groups(work, slug, width, group_height)
    body_page_count = math.ceil(len(groups) / 2)
    page_count = 2 + body_page_count
    output = output or work / (slug + ".pdf")
    if output.suffix.lower() != ".pdf":
        raise ValueError("Output must end in .pdf")
    output.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=".storybook-", suffix=".pdf", dir=output.parent, delete=False,
        ) as temp:
            temp_path = Path(temp.name)
        canvas = Canvas(str(temp_path), pagesize=A4, pageCompression=1)
        canvas.setTitle(title.getPlainText())
        canvas.setFillColor(HexColor(BACKGROUNDS[background]))
        canvas.rect(0, 0, page_width, page_height, stroke=0, fill=1)
        title_height = title.wrap(width, COVER_TITLE_HEIGHT)[1]
        title.drawOn(canvas, MARGIN, top - title_height)
        image_top = top - title_height - GROUP_GAP
        cover_image = groups[0].image
        cover_width, cover_height = cover_image.getSize()
        scale = min(width / cover_width, (image_top - MARGIN) / cover_height)
        cover_width, cover_height = cover_width * scale, cover_height * scale
        canvas.drawImage(
            cover_image, (page_width - cover_width) / 2,
            MARGIN + (image_top - MARGIN - cover_height) / 2,
            width=cover_width, height=cover_height, mask="auto",
        )
        canvas.showPage()
        canvas.setFillColor(HexColor(BACKGROUNDS[background]))
        canvas.rect(0, 0, page_width, page_height, stroke=0, fill=1)
        canvas.showPage()
        for page in range(body_page_count):
            canvas.setFillColor(HexColor(BACKGROUNDS[background]))
            canvas.rect(0, 0, page_width, page_height, stroke=0, fill=1)
            for slot, group in enumerate(groups[page * 2:page * 2 + 2]):
                slot_top = top - slot * (group_height + GROUP_GAP)
                image_bottom = slot_top - group.image_height
                canvas.drawImage(
                    group.image, MARGIN + (width - group.image_width) / 2, image_bottom,
                    width=group.image_width, height=group.image_height, mask="auto",
                )
                group.paragraph.drawOn(
                    canvas, MARGIN, image_bottom - IMAGE_TEXT_GAP - group.text_height,
                )
            canvas.setFillColor(INK)
            canvas.setFont("Times-Roman", 10)
            number = page + 1
            if number % 2:
                canvas.drawRightString(page_width - MARGIN, MARGIN, str(number))
            else:
                canvas.drawString(MARGIN, MARGIN, str(number))
            canvas.showPage()
        canvas.save()
        os.replace(temp_path, output)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()
    return output, page_count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slug")
    parser.add_argument("--stories-dir", type=Path, default=Path("stories"))
    parser.add_argument("--background", required=True, choices=BACKGROUNDS)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        output, pages = build_pdf(args.slug, args.stories_dir, args.background, args.out)
    except (OSError, ValueError) as exc:
        print("PDF build failed: %s" % exc, file=sys.stderr)
        return 1
    print(json.dumps({
        "path": str(output), "pages": pages, "page_size": "A4 portrait",
        "background": args.background, "bytes": output.stat().st_size,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
