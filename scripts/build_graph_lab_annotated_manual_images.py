#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SNAP_DIR = ROOT / "docs" / "reports" / "graph_lab_playwright_snapshots" / "latest"


def load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = []
    if bold:
        candidates.extend(
            [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
            ]
        )
    candidates.extend(
        [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        ]
    )
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


FONT = load_font(22)
FONT_BOLD = load_font(24, bold=True)
FONT_SMALL = load_font(18)


def draw_label(
    draw: ImageDraw.ImageDraw,
    number: int,
    text: str,
    rect: tuple[int, int, int, int],
) -> None:
    x1, y1, x2, y2 = rect
    draw.rounded_rectangle(rect, radius=16, outline=(105, 255, 230), width=4)
    bubble_r = 24
    bubble_x = x1 + 22
    bubble_y = y1 + 22
    draw.ellipse(
        (bubble_x - bubble_r, bubble_y - bubble_r, bubble_x + bubble_r, bubble_y + bubble_r),
        fill=(14, 32, 40),
        outline=(105, 255, 230),
        width=4,
    )
    number_box = draw.textbbox((0, 0), str(number), font=FONT_BOLD)
    number_w = number_box[2] - number_box[0]
    number_h = number_box[3] - number_box[1]
    draw.text(
        (bubble_x - number_w / 2, bubble_y - number_h / 2 - 2),
        str(number),
        font=FONT_BOLD,
        fill=(220, 255, 250),
    )
    text_x = bubble_x + bubble_r + 14
    text_y = y1 + 10
    draw.multiline_text(
        (text_x, text_y),
        text,
        font=FONT_SMALL,
        fill=(220, 255, 250),
        spacing=4,
    )


def add_title(draw: ImageDraw.ImageDraw, title: str, subtitle: str, width: int) -> None:
    title_box = draw.textbbox((0, 0), title, font=FONT_BOLD)
    title_w = title_box[2] - title_box[0]
    subtitle_box = draw.textbbox((0, 0), subtitle, font=FONT_SMALL)
    subtitle_w = subtitle_box[2] - subtitle_box[0]
    panel_w = max(title_w, subtitle_w) + 36
    panel_h = 72
    x1 = width - panel_w - 16
    y1 = 14
    x2 = width - 16
    y2 = y1 + panel_h
    draw.rounded_rectangle((x1, y1, x2, y2), radius=18, fill=(7, 19, 28), outline=(105, 255, 230), width=3)
    draw.text((x1 + 18, y1 + 10), title, font=FONT_BOLD, fill=(220, 255, 250))
    draw.text((x1 + 18, y1 + 40), subtitle, font=FONT_SMALL, fill=(170, 215, 210))


def annotate(src_name: str, dst_name: str, title: str, subtitle: str, labels: Iterable[tuple[int, str, tuple[int, int, int, int]]]) -> None:
    src = SNAP_DIR / src_name
    dst = SNAP_DIR / dst_name
    image = Image.open(src).convert("RGBA")
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    add_title(draw, title, subtitle, image.size[0])
    for number, text, rect in labels:
        draw_label(draw, number, text, rect)
    merged = Image.alpha_composite(image, overlay)
    merged.save(dst)


def main() -> None:
    annotate(
        "page_full.png",
        "page_full_annotated.png",
        "Graph Lab",
        "Main areas to scan first",
        [
            (1, "Graph inputs\nand runtime setup", (10, 68, 295, 310)),
            (2, "Graph canvas\nloaded template\nand run flow", (300, 68, 1095, 330)),
            (3, "Node inspector,\nvalidation, run result", (1110, 68, 1548, 360)),
            (4, "Top status bar:\nrun state, backend,\nlicense chips", (510, 6, 1160, 86)),
        ],
    )
    annotate(
        "decision_pane.png",
        "decision_pane_annotated.png",
        "Decision Pane",
        "Read top-to-bottom by task",
        [
            (1, "Compare actions:\nload, pin, clear", (12, 14, 322, 190)),
            (2, "Preset pair compare:\nbaseline -> target", (12, 228, 322, 535)),
            (3, "Track compare workflow\nand forecast", (12, 605, 322, 980)),
            (4, "Pinned quick actions\nfor saved pairs", (12, 2410, 322, 2760)),
            (5, "Compare history:\nreplay, import,\nretention", (12, 2940, 322, 3860)),
        ],
    )
    annotate(
        "artifact_inspector.png",
        "artifact_inspector_annotated.png",
        "Artifact Inspector",
        "Use this read order",
        [
            (1, "Current / compare\nartifact evidence", (12, 14, 322, 900)),
            (2, "Cursor probe\nand peak lock", (12, 1030, 322, 1760)),
            (3, "Artifacts list:\nfastest file check", (12, 1810, 322, 2140)),
            (4, "Node trace:\nwhat ran", (12, 2160, 322, 2800)),
            (5, "Visuals and panel state:\naudit / maintenance", (12, 2820, 322, 3360)),
        ],
    )


if __name__ == "__main__":
    main()
