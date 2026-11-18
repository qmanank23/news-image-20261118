#!/usr/bin/env python3
"""One-day world news image: Wednesday 18 November 2026.

Draws a newspaper-style front page (1024x1024 PNG) summing up the day's
world news and writes it to $MAKEFUN_OUTPUT_DIR/entry.png (default /output).

Standard library only. No network, no clock, no randomness: every run writes
identical bytes. All news content is baked into this file.

Layout: navy masthead naming the day, six story tiles (2 x 3) each with a
category tag, a two-line headline, a pictogram and a short factual summary,
plus a footer strip with four more one-line stories.
"""

import os
import struct
import zlib

W = 1024
H = 1024

# Palette.
PAPER = (247, 243, 232)
INK = (20, 20, 20)
NAVY = (19, 35, 63)
GOLD = (201, 162, 39)
WHITE = (255, 255, 255)
TILE_BG = (255, 255, 255)
TILE_LINE = (216, 210, 196)
PIC_BG = (240, 237, 226)
FOOTER_BG = (32, 36, 44)
MUTED = (90, 88, 80)

# Category accent colours, one per tile.
ACCENTS = [
    (30, 122, 70),    # markets: green
    (43, 95, 163),    # ukraine: blue
    (176, 58, 46),    # middle east: red
    (91, 74, 138),    # diplomacy: purple
    (14, 124, 123),   # tech: teal
    (199, 91, 18),    # sport: orange
]

# 5x7 bitmap font, all caps. '#' = set pixel. Only the characters the
# image uses are defined; anything else renders blank.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ';': ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '-': ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '$': ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
}


def _bold_glyph(rows):
    """Horizontally dilate a glyph by one cell: a cheap bold weight."""
    out = []
    for row in rows:
        cells = ['0'] * 6
        for i, ch in enumerate(row):
            if ch == '1':
                cells[i] = '1'
                cells[i + 1] = '1'
        out.append(''.join(cells))
    return out


BOLD_FONT = {ch: _bold_glyph(rows) for ch, rows in FONT.items()}


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            if 0 <= yy < self.h:
                xa = max(x, 0)
                xb = min(x + w, self.w)
                for xx in range(xa, xb):
                    i = (yy * self.w + xx) * 3
                    self.px[i:i + 3] = bytes(color)

    def hline(self, x, y, w, color):
        self.rect(x, y, w, 1, color)

    def vline(self, x, y, h, color):
        self.rect(x, y, 1, h, color)

    def line(self, x0, y0, x1, y1, color, width=1):
        """Bresenham line with square brush of `width` pixels."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        r = width // 2
        while True:
            self.rect(x0 - r, y0 - r, width, width, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.hline(cx - dx, cy + dy, 2 * dx + 1, color)

    def ring(self, cx, cy, r, color, thickness=2):
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                d = (dx * dx + dy * dy) ** 0.5
                if r - thickness < d <= r:
                    self.set(cx + dx, cy + dy, color)

    def text(self, x, y, s, scale, color, bold=False, align="left"):
        font = BOLD_FONT if bold else FONT
        adv = (7 if bold else 6) * scale
        if align == "center":
            width = len(s) * adv - scale
            x = x - width // 2
        for ci, ch in enumerate(s):
            rows = font.get(ch, FONT[' '])
            gx0 = x + ci * adv
            for gy, row in enumerate(rows):
                for gx, cell in enumerate(row):
                    if cell == '1':
                        self.rect(gx0 + gx * scale, y + gy * scale,
                                  scale, scale, color)
        return x


def text_width(s, scale, bold=False):
    adv = (7 if bold else 6) * scale
    return len(s) * adv - scale


# ---------------------------------------------------------------- pictograms
# Each draws inside a 100x99 box whose top-left corner is (bx, by).

def pic_bars(cv, bx, by, color):
    heights = [22, 36, 50, 66]
    for i, ht in enumerate(heights):
        x = bx + 12 + i * 21
        shade = color if i == 3 else tuple(min(255, c + 60) for c in color)
        cv.rect(x, by + 82 - ht, 14, ht, shade)
    cv.hline(bx + 6, by + 82, 88, INK)
    cv.line(bx + 10, by + 26, bx + 88, by + 8, color, 4)
    cv.line(bx + 88, by + 8, bx + 74, by + 8, color, 4)
    cv.line(bx + 88, by + 8, bx + 88, by + 22, color, 4)


def pic_bridge(cv, bx, by, color):
    # Water.
    for wy in (78, 86, 93):
        for wx in range(bx + 6, bx + 94, 16):
            cv.hline(wx, by + wy, 9, (120, 160, 200))
    # Pylons.
    cv.rect(bx + 18, by + 18, 6, 52, INK)
    cv.rect(bx + 70, by + 18, 6, 52, INK)
    # Cables.
    cv.line(bx + 21, by + 18, bx + 8, by + 50, MUTED, 2)
    cv.line(bx + 21, by + 18, bx + 38, by + 50, MUTED, 2)
    cv.line(bx + 73, by + 18, bx + 58, by + 50, MUTED, 2)
    cv.line(bx + 73, by + 18, bx + 88, by + 50, MUTED, 2)
    # Deck: two standing spans with a gap in the middle.
    cv.rect(bx + 6, by + 50, 36, 6, color)
    cv.rect(bx + 58, by + 50, 36, 6, color)
    # Fallen middle span, tilted into the strait.
    cv.line(bx + 44, by + 52, bx + 58, by + 70, color, 6)
    cv.disc(bx + 50, by + 44, 4, (200, 60, 40))


def pic_shield(cv, bx, by, color):
    # Interceptor dome.
    for dy in range(0, 34):
        dx = int((34 * 34 - (34 - dy) * (34 - dy)) ** 0.5) if dy <= 34 else 0
        cv.hline(bx + 50 - dx, by + 44 + dy, 2 * dx + 1, (150, 190, 220))
    cv.hline(bx + 14, by + 78, 72, INK)
    # Incoming drones as small squares.
    for dx, dy in ((18, 12), (48, 6), (78, 14)):
        cv.rect(bx + dx, by + dy, 7, 7, INK)
    # Intercept burst.
    cx, cy = bx + 50, by + 34
    cv.line(cx - 10, cy, cx + 10, cy, color, 3)
    cv.line(cx, cy - 10, cx, cy + 10, color, 3)
    cv.line(cx - 7, cy - 7, cx + 7, cy + 7, color, 3)
    cv.line(cx - 7, cy + 7, cx + 7, cy - 7, color, 3)
    cv.disc(cx, cy, 4, GOLD)


def pic_quad(cv, bx, by, color):
    centers = [(24, 24), (76, 24), (24, 74), (76, 74)]
    dots = [(43, 95, 163), (200, 60, 40), (30, 122, 70), (201, 162, 39)]
    for (cx, cy) in centers:
        cv.line(bx + 50, by + 49, bx + cx, by + cy, MUTED, 2)
    cv.disc(bx + 50, by + 49, 10, WHITE)
    cv.ring(bx + 50, by + 49, 10, color, 3)
    for (cx, cy), dot in zip(centers, dots):
        cv.disc(bx + cx, by + cy, 11, dot)


def pic_ipo(cv, bx, by, color):
    # Axes.
    cv.vline(bx + 12, by + 10, 72, INK)
    cv.hline(bx + 12, by + 82, 82, INK)
    # Rising line with an arrowhead.
    pts = [(16, 70), (34, 58), (50, 62), (68, 40), (86, 18)]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        cv.line(bx + x0, by + y0, bx + x1, by + y1, color, 4)
    cv.line(bx + 86, by + 18, bx + 72, by + 18, color, 4)
    cv.line(bx + 86, by + 18, bx + 86, by + 32, color, 4)
    for (x, y) in pts:
        cv.disc(bx + x, by + y, 3, INK)


def pic_cricket(cv, bx, by, color):
    # Stumps and bails.
    for sx in (28, 40, 52):
        cv.rect(bx + sx, by + 50, 5, 36, (220, 180, 110))
    cv.rect(bx + 28, by + 44, 17, 4, (220, 180, 110))
    cv.rect(bx + 44, by + 44, 13, 4, (220, 180, 110))
    # Crease line.
    cv.hline(bx + 18, by + 88, 64, WHITE)
    cv.hline(bx + 18, by + 88, 64, MUTED)
    # Ball.
    cv.disc(bx + 76, by + 28, 10, (178, 34, 34))
    cv.line(bx + 70, by + 22, bx + 82, by + 34, (255, 255, 255), 2)
    # Bat, angled.
    cv.line(bx + 62, by + 88, bx + 86, by + 52, (222, 184, 135), 9)
    cv.line(bx + 86, by + 52, bx + 92, by + 42, INK, 4)


PICTOGRAMS = [pic_bars, pic_bridge, pic_shield, pic_quad, pic_ipo, pic_cricket]

# (tag, headline lines, summary lines) — all caps, verified 18 Nov 2026 news.
STORIES = [
    ("MARKETS",
     ["NVIDIA BEATS,", "ASIA RALLIES"],
     ["SALES $115.8B +103%",
      "KOSPI +3.3%, NIKKEI",
      "RETAKES 59,000.",
      "HUANG NOT RETURNING"]),
    ("UKRAINE",
     ["KERCH BRIDGE", "HIT AGAIN"],
     ["ROAD SPAN COLLAPSES",
      "INTO KERCH STRAIT.",
      "RUSSIA HITS 2 KYIV",
      "BRIDGES IN REPLY"]),
    ("MIDDLE EAST",
     ["BAHRAIN", "ALL-CLEAR"],
     ["DEFENCES INTERCEPT",
      "IRANIAN ATTACKS.",
      "2 ALERTS, ALL-CLEAR.",
      "KUWAIT HIT TOO"]),
    ("DIPLOMACY",
     ["QUAD MEETS", "IN MANILA"],
     ["US, INDIA, JAPAN,",
      "AUSTRALIA MEET;",
      "APEC AND XI-PUTIN",
      "TALKS NEXT"]),
    ("TECH",
     ["ANTHROPIC IPO", "PRICES TODAY"],
     ["825M SHARES AT",
      "$70-$78; VALUE TO",
      "$1.4T. NASDAQ",
      "DEBUT THURSDAY"]),
    ("SPORT",
     ["DHONI RETIRES", "FROM THE IPL"],
     ["ENDS 18-YEAR IPL",
      "CAREER, 278 GAMES,",
      "5 TITLES; STAYS AS",
      "CSK MENTOR IN 2027"]),
]

FOOTER_ITEMS = [
    "N. IRELAND PROMOTED",
    "AKVAN NEARS INDIA",
    "TRUMP PULLS FDA PICK",
    "US LOSES MEASLES STATUS",
]


def render():
    cv = Canvas(W, H, PAPER)

    # Masthead.
    cv.rect(0, 0, W, 116, NAVY)
    cv.text(W // 2, 14, "THE WORLD IN ONE DAY", 3, GOLD, align="center")
    cv.text(W // 2, 44, "18 NOVEMBER 2026", 8, WHITE, bold=True,
            align="center")
    cv.rect(0, 116, W, 4, GOLD)

    # Story tiles: 2 columns x 3 rows.
    tile_w, tile_h, gap, margin = 494, 259, 12, 12
    top = 133
    for idx, (tag, head, summary) in enumerate(STORIES):
        tx = margin + (idx % 2) * (tile_w + gap)
        ty = top + (idx // 2) * (tile_h + gap)
        accent = ACCENTS[idx]
        cv.rect(tx, ty, tile_w, tile_h, TILE_BG)
        # Border.
        cv.rect(tx, ty, tile_w, 2, TILE_LINE)
        cv.rect(tx, ty + tile_h - 2, tile_w, 2, TILE_LINE)
        cv.rect(tx, ty, 2, tile_h, TILE_LINE)
        cv.rect(tx + tile_w - 2, ty, 2, tile_h, TILE_LINE)
        # Accent bar on the left edge.
        cv.rect(tx, ty, 6, tile_h, accent)
        # Tag.
        tag_w = text_width(tag, 2) + 16
        cv.rect(tx + 18, ty + 13, tag_w, 24, accent)
        cv.text(tx + 26, ty + 18, tag, 2, WHITE)
        # Headline, two lines, bold.
        cv.text(tx + 18, ty + 50, head[0], 5, INK, bold=True)
        cv.text(tx + 18, ty + 90, head[1], 5, INK, bold=True)
        # Divider.
        cv.hline(tx + 18, ty + 138, tile_w - 36, TILE_LINE)
        # Pictogram box.
        px, py = tx + 18, ty + 148
        cv.rect(px, py, 100, 99, PIC_BG)
        cv.rect(px, py, 100, 2, TILE_LINE)
        cv.rect(px, py + 97, 100, 2, TILE_LINE)
        cv.rect(px, py, 2, 99, TILE_LINE)
        cv.rect(px + 98, py, 2, 99, TILE_LINE)
        PICTOGRAMS[idx](cv, px, py, accent)
        # Summary lines.
        for li, line in enumerate(summary):
            cv.text(tx + 132, ty + 150 + li * 25, line, 3, INK)

    # Footer strip.
    fy = 946
    cv.rect(0, 940, W, 4, GOLD)
    cv.rect(0, fy, W, H - fy, FOOTER_BG)
    cv.text(18, fy + 28, "ALSO TODAY", 3, GOLD)
    for i, item in enumerate(FOOTER_ITEMS):
        ix = 222 + (i % 2) * 380
        iy = fy + 8 + (i // 2) * 28
        cv.rect(ix, iy + 6, 8, 8, GOLD)
        cv.text(ix + 18, iy, item, 3, WHITE)

    return cv.px


def png_bytes(rgb, w, h):
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)  # filter: none
        raw += rgb[y * stride:(y + 1) * stride]

    def chunk(typ, data):
        out = struct.pack(">I", len(data)) + typ + data
        return out + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    data = png_bytes(render(), W, H)
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes)" % (path, len(data)))


if __name__ == "__main__":
    main()
