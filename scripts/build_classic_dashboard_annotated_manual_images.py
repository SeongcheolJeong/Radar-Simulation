#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SNAP_DIR = ROOT / "docs" / "reports" / "classic_dashboard_snapshots" / "latest"


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


FONT_BOLD = load_font(24, bold=True)
FONT_SMALL = load_font(18)


def draw_label(draw: ImageDraw.ImageDraw, number: int, text: str, rect: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = rect
    draw.rounded_rectangle(rect, radius=16, outline=(86, 244, 255), width=4)
    bubble_r = 24
    bubble_x = x1 + 22
    bubble_y = y1 + 22
    draw.ellipse(
        (bubble_x - bubble_r, bubble_y - bubble_r, bubble_x + bubble_r, bubble_y + bubble_r),
        fill=(14, 32, 40),
        outline=(86, 244, 255),
        width=4,
    )
    num = str(number)
    box = draw.textbbox((0, 0), num, font=FONT_BOLD)
    draw.text(
        (bubble_x - (box[2] - box[0]) / 2, bubble_y - (box[3] - box[1]) / 2 - 2),
        num,
        font=FONT_BOLD,
        fill=(225, 255, 250),
    )
    draw.multiline_text((bubble_x + bubble_r + 14, y1 + 10), text, font=FONT_SMALL, fill=(225, 255, 250), spacing=4)


def add_title(draw: ImageDraw.ImageDraw, title: str, subtitle: str, width: int) -> None:
    title_box = draw.textbbox((0, 0), title, font=FONT_BOLD)
    subtitle_box = draw.textbbox((0, 0), subtitle, font=FONT_SMALL)
    panel_w = max(title_box[2] - title_box[0], subtitle_box[2] - subtitle_box[0]) + 36
    x1 = width - panel_w - 16
    y1 = 14
    x2 = width - 16
    y2 = y1 + 72
    draw.rounded_rectangle((x1, y1, x2, y2), radius=18, fill=(7, 19, 28), outline=(86, 244, 255), width=3)
    draw.text((x1 + 18, y1 + 10), title, font=FONT_BOLD, fill=(225, 255, 250))
    draw.text((x1 + 18, y1 + 40), subtitle, font=FONT_SMALL, fill=(170, 215, 210))


def annotate(src_name: str, dst_name: str, title: str, subtitle: str, labels: list[tuple[int, str, tuple[int, int, int, int]]]) -> None:
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
        "dashboard_full.png",
        "dashboard_full_annotated.png",
        "Classic Dashboard",
        "Main areas to scan first",
        [
            (1, "Inputs and\nAPI actions", (8, 62, 320, 1350)),
            (2, "Scene viewer\nand radar map", (330, 62, 930, 1900)),
            (3, "Metrics and\ndetection table", (940, 62, 1545, 980)),
            (4, "Regression / export\ncontrols", (8, 1160, 320, 2550)),
            (5, "Policy tuning\nand radar parameters", (8, 2570, 320, 3360)),
        ],
    )
    annotate(
        "dashboard_controls.png",
        "dashboard_controls_annotated.png",
        "Controls",
        "Top-to-bottom workflow",
        [
            (1, "Refresh outputs\nand local summary", (8, 14, 312, 340)),
            (2, "Run / compare /\npolicy via API", (8, 350, 312, 1040)),
            (3, "Regression history,\nexport, review bundle", (8, 1060, 312, 2300)),
            (4, "Policy tuning and\nscenario parameters", (8, 2310, 312, 3280)),
        ],
    )
    annotate(
        "dashboard_main.png",
        "dashboard_main_annotated.png",
        "Result Areas",
        "Read these panes in order",
        [
            (1, "Scene viewer", (8, 8, 780, 650)),
            (2, "Metrics", (810, 8, 1230, 520)),
            (3, "Radar map", (8, 680, 660, 3290)),
            (4, "Detection table", (680, 680, 1230, 3290)),
        ],
    )


if __name__ == "__main__":
    main()
