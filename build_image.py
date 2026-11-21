#!/usr/bin/env python3
"""
build_image.py -- draw the 20 November 2026 front-page poster.

This script is the single source of truth for entry.png.  It uses only
Pillow and the system Noto Sans faces, draws every element at a fixed
position on a 1024x1024 canvas, and saves with fixed PNG settings so
that two consecutive runs produce a byte-identical file.

Layout (top to bottom):
  masthead  -- title and date line
  hero      -- dark panel carrying the GTA VI day-one record
  grid      -- six news panels, two columns by three rows
  ticker    -- black footer bar with three short items

All news wording below comes from reports published on
20 November 2026 (Reuters / CNA / SCMP / OneTurn / Moneycontrol).
No figure is invented in this file; numbers are copied from those
reports exactly as briefed.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------- canvas
WIDTH = 1024
HEIGHT = 1024
MARGIN = 36
CONTENT_W = WIDTH - 2 * MARGIN

PAPER = (247, 243, 232)
INK = (18, 18, 20)
MUTED = (92, 88, 80)
RULE = (18, 18, 20)
HERO_BG = (16, 22, 52)
HERO_ACCENT = (255, 196, 0)
HERO_TEXT = (255, 255, 255)
HERO_SUB = (196, 205, 235)
PANEL_BG = (255, 255, 255)
PANEL_BORDER = (205, 198, 182)
TICKER_BG = (18, 18, 20)
TICKER_TEXT = (245, 242, 235)

FONT_DIR = Path("/usr/share/fonts/truetype/noto")
BLACK = FONT_DIR / "NotoSans-Black.ttf"
BOLD = FONT_DIR / "NotoSans-Bold.ttf"
REGULAR = FONT_DIR / "NotoSans-Regular.ttf"
MEDIUM = FONT_DIR / "NotoSans-Medium.ttf"

OUT_PATH = Path(__file__).resolve().parent / "entry.png"


def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    """Load one Noto face at an exact size (no scaling tricks)."""
    return ImageFont.truetype(str(path), size=size)


def text_width(draw: ImageDraw.ImageDraw, text: str, fnt) -> int:
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0]


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt, max_width: int):
    """Greedy word wrap.  Returns a list of lines that each fit."""
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = word if not current else current + " " + word
        if text_width(draw, trial, fnt) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_wrapped(draw, xy, text, fnt, fill, max_width, line_gap):
    """Draw wrapped text starting at xy; return the y after it."""
    x, y = xy
    lines = wrap(draw, text, fnt, max_width)
    ascent_box = fnt.getbbox("Ag")
    line_h = (ascent_box[3] - ascent_box[1]) + line_gap
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += line_h
    return y


def draw_centered(draw, y, text, fnt, fill):
    w = text_width(draw, text, fnt)
    draw.text(((WIDTH - w) // 2, y), text, font=fnt, fill=fill)
    box = fnt.getbbox("Ag")
    return y + (box[3] - box[1])


# ---------------------------------------------------------------- panels
PANELS = [
    (
        "UKRAINE",
        "400+ drones, 110+ missiles hit Kyiv",
        "Russia's massive barrage killed 8, damaged embassies and a "
        "cathedral, and cut power and rail across the capital.",
    ),
    (
        "MARKETS",
        "AI sell-off shakes global stocks",
        "AI valuation doubts after Anthropic's Nasdaq debut: Nikkei "
        "-4.8%, S&P 500 down about 2% for a fifth straight day.",
    ),
    (
        "WASHINGTON",
        "White House fires its cyber chief",
        "Sean Cairncross was dismissed after a week of tech outages "
        "rattled the United States.",
    ),
    (
        "CLIMATE  COP31",
        "Fossil-fuel phase-out dropped",
        "In Antalya a slimmed-down draft deal dropped any call to "
        "phase out fossil fuels; talks went into overtime.",
    ),
    (
        "HEALTH  KENYA",
        "Last Ebola patient discharged",
        "Kenya discharged its last Ebola patient, 37 days after its "
        "first case was confirmed.",
    ),
    (
        "EUROPE",
        "Merz warns against a 'new Yalta'",
        "After the Shenzhen Trump-Xi-Putin summit, Chancellor Merz "
        "said Europe will not accept a settlement negotiated without it.",
    ),
]

TICKER = (
    "Israeli forces cross the Yellow Line in Gaza, first incursion since "
    "the truce  \u2022  Dozens missing after a migrant boat capsizes off "
    "Senegal  \u2022  AMD shares fall 11% on China-link claims its CEO denied."
)


def build() -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), PAPER)
    draw = ImageDraw.Draw(img)

    # ---------------------------------------------------------- masthead
    y = 26
    draw_centered(draw, y, "THE WORLD IN A DAY", font(BLACK, 62), INK)
    y = 98
    # thin rule, date line, thin rule
    draw.line([(MARGIN, y), (WIDTH - MARGIN, y)], fill=RULE, width=3)
    y += 10
    draw_centered(
        draw, y, "FRIDAY \u00b7 20 NOVEMBER 2026", font(BOLD, 22), MUTED
    )
    y += 36
    draw.line([(MARGIN, y), (WIDTH - MARGIN, y)], fill=RULE, width=1)

    # ---------------------------------------------------------- hero
    hero_top = y + 14
    hero_h = 258
    hero_bottom = hero_top + hero_h
    draw.rounded_rectangle(
        [MARGIN, hero_top, WIDTH - MARGIN, hero_bottom],
        radius=10,
        fill=HERO_BG,
    )
    hx = MARGIN + 28
    hw = CONTENT_W - 56
    hy = hero_top + 20
    draw.text((hx, hy), "HERO  \u00b7  ENTERTAINMENT", font=font(BOLD, 17), fill=HERO_ACCENT)
    hy += 30
    draw.text((hx, hy), "GTA VI SMASHES EVERY RECORD", font=font(BLACK, 37), fill=HERO_TEXT)
    hy += 52
    draw.text((hx, hy), "$3.79 BILLION  \u00b7  DAY ONE", font=font(BLACK, 44), fill=HERO_ACCENT)
    hy += 62
    hy = draw_wrapped(
        draw,
        (hx, hy),
        "Rockstar reported $3.79B in first-day retail sales on "
        "32.5 million units pre-release \u2014 nearly 5x GTA V's "
        "day-one (~$800M in 2013) and the biggest entertainment "
        "launch in history.",
        font(REGULAR, 20),
        HERO_TEXT,
        hw,
        6,
    )
    hy += 6
    draw_wrapped(
        draw,
        (hx, hy),
        "Sensor Tower estimate: $2.36B / ~24.6M copies.",
        font(MEDIUM, 18),
        HERO_SUB,
        hw,
        5,
    )

    # ---------------------------------------------------------- panel grid
    grid_top = hero_bottom + 16
    cols = 2
    rows = 3
    gap_x = 14
    gap_y = 12
    panel_w = (CONTENT_W - gap_x) // cols
    panel_h = 148

    kicker_f = font(BOLD, 14)
    head_f = font(BOLD, 20)
    body_f = font(REGULAR, 17)

    for idx, (kicker, headline, body) in enumerate(PANELS):
        col = idx % cols
        row = idx // cols
        left = MARGIN + col * (panel_w + gap_x)
        top = grid_top + row * (panel_h + gap_y)
        right = left + panel_w
        bottom = top + panel_h
        draw.rounded_rectangle(
            [left, top, right, bottom],
            radius=8,
            fill=PANEL_BG,
            outline=PANEL_BORDER,
            width=1,
        )
        # small accent bar on the left edge of each panel
        draw.rectangle([left, top + 10, left + 5, bottom - 10], fill=HERO_ACCENT)
        px = left + 18
        pw = panel_w - 32
        py = top + 12
        draw.text((px, py), kicker, font=kicker_f, fill=(150, 32, 48))
        py += 24
        py = draw_wrapped(draw, (px, py), headline, head_f, INK, pw, 4)
        py += 4
        draw_wrapped(draw, (px, py), body, body_f, (52, 50, 46), pw, 4)

    # ---------------------------------------------------------- ticker
    ticker_top = grid_top + rows * panel_h + (rows - 1) * gap_y + 16
    ticker_bottom = HEIGHT - 26
    draw.rounded_rectangle(
        [MARGIN, ticker_top, WIDTH - MARGIN, ticker_bottom],
        radius=8,
        fill=TICKER_BG,
    )
    tx = MARGIN + 20
    tw = CONTENT_W - 40
    draw.text((tx, ticker_top + 10), "ALSO TODAY", font=font(BOLD, 13), fill=HERO_ACCENT)
    draw_wrapped(
        draw,
        (tx, ticker_top + 32),
        TICKER,
        font(REGULAR, 16),
        TICKER_TEXT,
        tw,
        5,
    )

    return img


def main() -> None:
    image = build()
    # Fixed save parameters keep the bytes deterministic run to run.
    image.save(OUT_PATH, format="PNG", optimize=False, compress_level=6)
    size = OUT_PATH.stat().st_size
    print(f"wrote {OUT_PATH} ({size} bytes, {image.size[0]}x{image.size[1]})")


if __name__ == "__main__":
    main()
