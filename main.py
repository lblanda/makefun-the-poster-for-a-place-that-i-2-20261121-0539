#!/usr/bin/env python3
"""VELMARA - The Poster for a Place That Isn't There.

Draws one vintage travel poster (1024x1024 PNG) for Velmara, an invented
archipelago of floating islands above a sea of glass, lit by twin suns,
and writes it to /output/entry.png.

Self-contained, stdlib only: an embedded 5x7 bitmap font, a hand-rolled
PNG encoder, and procedural drawing. No network, no files read, no time
or randomness: two runs are byte-identical.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import math
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (243, 232, 205)      # vintage poster cream
PAPER_DK = (228, 212, 178)
NAVY = (18, 42, 66)          # deep frame navy
NAVY_LT = (30, 64, 94)
GOLD = (198, 150, 52)
GOLD_LT = (232, 190, 92)
CREAM = (250, 242, 220)
SKY_TOP = (24, 68, 96)       # deep teal sky
SKY_MID = (58, 122, 138)
SKY_LOW = (246, 190, 130)    # warm peach at the horizon
SUN_BIG = (242, 165, 65)     # amber sun
SUN_HALO = (247, 203, 120)
SUN_SMALL = (247, 232, 195)  # pale second sun
SEA_TOP = (46, 110, 124)     # glass sea, mirror of the sky
SEA_BOT = (16, 46, 70)
ISLE_GREEN = (63, 125, 78)
ISLE_GREEN_DK = (44, 96, 58)
ROCK = (107, 74, 58)         # island underside rock
ROCK_DK = (84, 56, 44)
ROOF = (178, 62, 44)         # terracotta roofs
WALL = (250, 244, 228)
FOAM = (214, 236, 238)       # waterfall / glass sheen
WHITE = (250, 248, 240)

OUT = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")


# ------------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)
        for i in range(w * h):
            self.px[3 * i] = bg[0]
            self.px[3 * i + 1] = bg[1]
            self.px[3 * i + 2] = bg[2]

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = 3 * (y * self.w + x)
            self.px[i] = c[0]
            self.px[i + 1] = c[1]
            self.px[i + 2] = c[2]

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = 3 * (y * self.w + x)
            return (self.px[i], self.px[i + 1], self.px[i + 2])
        return (0, 0, 0)

    def blend(self, x, y, c, a):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = 3 * (y * self.w + x)
            self.px[i] = int(c[0] * a + self.px[i] * (1 - a))
            self.px[i + 1] = int(c[1] * a + self.px[i + 1] * (1 - a))
            self.px[i + 2] = int(c[2] * a + self.px[i + 2] * (1 - a))

    def fill_rect(self, x0, y0, x1, y1, c):
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(self.w - 1, x1)
        y1 = min(self.h - 1, y1)
        for y in range(y0, y1 + 1):
            base = 3 * (y * self.w + x0)
            for x in range(x0, x1 + 1):
                self.px[base] = c[0]
                self.px[base + 1] = c[1]
                self.px[base + 2] = c[2]
                base += 3

    def hline(self, x0, x1, y, c):
        if y < 0 or y >= self.h:
            return
        x0 = max(0, x0)
        x1 = min(self.w - 1, x1)
        for x in range(x0, x1 + 1):
            i = 3 * (y * self.w + x)
            self.px[i] = c[0]
            self.px[i + 1] = c[1]
            self.px[i + 2] = c[2]

    def vline(self, x, y0, y1, c):
        if x < 0 or x >= self.w:
            return
        y0 = max(0, y0)
        y1 = min(self.h - 1, y1)
        for y in range(y0, y1 + 1):
            i = 3 * (y * self.w + x)
            self.px[i] = c[0]
            self.px[i + 1] = c[1]
            self.px[i + 2] = c[2]

    def line(self, x0, y0, x1, y1, c):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c):
        x = 0
        y = r
        d = 3 - 2 * r
        while x <= y:
            for px, py in ((cx + x, cy + y), (cx - x, cy + y),
                           (cx + x, cy - y), (cx - x, cy - y),
                           (cx + y, cy + x), (cx - y, cy + x),
                           (cx + y, cy - x), (cx - y, cy - x)):
                self.set(px, py, c)
            if d < 0:
                d += 4 * x + 6
            else:
                d += 4 * (x - y) + 10
                y -= 1
            x += 1

    def fill_circle(self, cx, cy, r, c):
        for y in range(cy - r, cy + r + 1):
            dx = int(math.sqrt(max(0, r * r - (y - cy) ** 2)))
            self.hline(cx - dx, cx + dx, y, c)

    def fill_ellipse(self, cx, cy, rx, ry, c):
        for y in range(cy - ry, cy + ry + 1):
            t = (y - cy) / ry
            dx = int(rx * math.sqrt(max(0.0, 1 - t * t)))
            self.hline(cx - dx, cx + dx, y, c)

    def ellipse(self, cx, cy, rx, ry, c):
        for a in range(360):
            t = math.radians(a)
            self.set(int(cx + rx * math.cos(t)), int(cy + ry * math.sin(t)), c)

    def poly(self, pts, c):
        for i in range(len(pts)):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % len(pts)]
            self.line(x0, y0, x1, y1, c)

    def fill_poly(self, pts, c):
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.hline(int(xs[i]), int(xs[i + 1]), y, c)

    def rect_outline(self, x0, y0, x1, y1, c, w=1):
        for t in range(w):
            self.hline(x0 + t, x1 - t, y0 + t, c)
            self.hline(x0 + t, x1 - t, y1 - t, c)
            self.vline(x0 + t, y0 + t, y1 - t, c)
            self.vline(x1 - t, y0 + t, y1 - t, c)

    def vgrad(self, x0, y0, x1, y1, top, bot):
        for y in range(y0, y1 + 1):
            t = (y - y0) / max(1, y1 - y0)
            c = tuple(int(top[k] + (bot[k] - top[k]) * t) for k in range(3))
            self.hline(x0, x1, y, c)

    def vgrad3(self, x0, y0, x1, y1, c0, c1, c2):
        """Two-stop vertical gradient: c0 at top, c1 at middle, c2 at bottom."""
        mid = (y0 + y1) // 2
        for y in range(y0, y1 + 1):
            if y <= mid:
                t = (y - y0) / max(1, mid - y0)
                c = tuple(int(c0[k] + (c1[k] - c0[k]) * t) for k in range(3))
            else:
                t = (y - mid) / max(1, y1 - mid)
                c = tuple(int(c1[k] + (c2[k] - c1[k]) * t) for k in range(3))
            self.hline(x0, x1, y, c)


# ---------------------------------------------------------------------- PNG
def write_png(cv, path):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.px[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, data):
        out = struct.pack(">I", len(data)) + typ + data
        out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)

# --------------------------------------------------------------------- font
# 5x7 bitmap font. Each glyph is 7 rows; each row is a 5-bit mask, the
# leftmost pixel in the most significant bit.
FONT = {
    "A": (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "B": (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    "C": (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    "D": (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    "E": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    "F": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    "G": (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    "H": (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "I": (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "J": (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
    "K": (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    "L": (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    "M": (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    "N": (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    "O": (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "P": (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    "Q": (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    "R": (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    "S": (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    "T": (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    "U": (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "V": (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    "W": (0x11, 0x11, 0x11, 0x15, 0x15, 0x15, 0x0A),
    "X": (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    "Y": (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    "Z": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    "0": (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    "1": (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "2": (0x0E, 0x11, 0x01, 0x06, 0x08, 0x10, 0x1F),
    "3": (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E),
    "4": (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    "5": (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    "6": (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    "7": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    "8": (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    "9": (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    " ": (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
    ".": (0x00, 0x00, 0x00, 0x00, 0x00, 0x0C, 0x0C),
    ",": (0x00, 0x00, 0x00, 0x00, 0x0C, 0x04, 0x08),
    "-": (0x00, 0x00, 0x00, 0x0E, 0x00, 0x00, 0x00),
    "/": (0x01, 0x02, 0x02, 0x04, 0x08, 0x08, 0x10),
    ":": (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x0C, 0x00),
    ";": (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x04, 0x08),
    "(": (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ")": (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    "'": (0x04, 0x04, 0x08, 0x00, 0x00, 0x00, 0x00),
    '"': (0x0A, 0x0A, 0x00, 0x00, 0x00, 0x00, 0x00),
    "&": (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D),
    "+": (0x00, 0x04, 0x04, 0x1F, 0x04, 0x04, 0x00),
    "=": (0x00, 0x00, 0x1F, 0x00, 0x1F, 0x00, 0x00),
    "*": (0x00, 0x15, 0x0E, 0x1F, 0x0E, 0x15, 0x00),
    "!": (0x04, 0x04, 0x04, 0x04, 0x04, 0x00, 0x04),
    "?": (0x0E, 0x11, 0x01, 0x06, 0x04, 0x00, 0x04),
    "%": (0x19, 0x1A, 0x02, 0x04, 0x08, 0x0B, 0x13),
    "#": (0x0A, 0x0A, 0x1F, 0x0A, 0x1F, 0x0A, 0x0A),
    "\u2022": (0x00, 0x00, 0x0C, 0x1E, 0x1E, 0x0C, 0x00),
    "\u2014": (0x00, 0x00, 0x00, 0x1F, 0x00, 0x00, 0x00),
}

BLANK = (0x00,) * 7


def text_w(s, scale, spacing=None):
    if spacing is None:
        spacing = scale
    return len(s) * (5 * scale + spacing) - spacing


def draw_text(cv, x, y, s, scale, color, spacing=None, bold=False):
    """Draw text at top-left (x, y). Returns width drawn."""
    if spacing is None:
        spacing = scale
    cx = x
    for ch in s:
        g = FONT.get(ch, BLANK)
        for row in range(7):
            bits = g[row]
            for col in range(5):
                if bits & (1 << (4 - col)):
                    cv.fill_rect(cx + col * scale, y + row * scale,
                                 cx + col * scale + scale - 1,
                                 y + row * scale + scale - 1, color)
                    if bold:
                        cv.fill_rect(cx + col * scale + 1, y + row * scale,
                                     cx + col * scale + scale,
                                     y + row * scale + scale - 1, color)
        cx += 5 * scale + spacing
    return cx - x - spacing


def text_center(cv, cx, y, s, scale, color, spacing=None, bold=False):
    w = text_w(s, scale, spacing)
    return draw_text(cv, cx - w // 2, y, s, scale, color, spacing, bold)


def draw_shadow_text(cv, cx, y, s, scale, color, shadow, spacing=None,
                     bold=False):
    """Centred text with a 1-step drop shadow for legibility over the sky."""
    w = text_w(s, scale, spacing)
    x = cx - w // 2
    draw_text(cv, x + scale, y + scale, s, scale, shadow, spacing, bold)
    return draw_text(cv, x, y, s, scale, color, spacing, bold)

# --------------------------------------------------------------- landscape
HORIZON = 640          # where the sky meets the glass sea
ART_X0, ART_X1 = 40, 984
ART_Y0, ART_Y1 = 40, 984


def draw_sky(cv):
    cv.vgrad3(ART_X0, ART_Y0, ART_X1, HORIZON, SKY_TOP, SKY_MID, SKY_LOW)
    # thin warm band hugging the horizon
    for y in range(HORIZON - 26, HORIZON):
        t = (y - (HORIZON - 26)) / 26.0
        c = tuple(int(SKY_LOW[k] + (SUN_HALO[k] - SKY_LOW[k]) * t)
                  for k in range(3))
        cv.hline(ART_X0, ART_X1, y, c)


def draw_sun(cv, cx, cy, r, color, halo, halo_r):
    cv.fill_circle(cx, cy, halo_r, halo)
    cv.fill_circle(cx, cy, r, color)
    # faint outer ring
    cv.circle(cx, cy, halo_r + 6, halo)


def draw_cloud(cv, cx, cy, w, color):
    """A flat vintage-poster cloud: overlapping discs, one baseline."""
    h = w // 4
    cv.fill_ellipse(cx, cy, w // 2, h, color)
    cv.fill_circle(cx - w // 4, cy - h // 2, h, color)
    cv.fill_circle(cx + w // 5, cy - h // 2 - 2, int(h * 0.9), color)
    cv.fill_circle(cx + w // 3, cy - h // 4, int(h * 0.7), color)


def draw_bird(cv, x, y, s, color):
    cv.line(x - s, y, x, y + s // 2, color)
    cv.line(x, y + s // 2, x + s, y, color)


def draw_house(cv, x, y, w, h, roof_h=8):
    """A small white house with a terracotta roof, base at (x, y)."""
    cv.fill_rect(x, y - h, x + w, y, WALL)
    cv.fill_poly([(x - 3, y - h), (x + w // 2, y - h - roof_h),
                  (x + w + 3, y - h)], ROOF)
    cv.fill_rect(x + w // 2 - 3, y - h + 6, x + w // 2 + 3, y, NAVY_LT)


def draw_pine(cv, x, y, h, color=ISLE_GREEN_DK):
    """A pine tree, base at (x, y)."""
    cv.fill_rect(x - 1, y - h // 4, x + 1, y, (90, 60, 40))
    cv.fill_poly([(x - h // 3, y - h // 4), (x, y - h),
                  (x + h // 3, y - h // 4)], color)
    cv.fill_poly([(x - h // 4, y - h // 2), (x, y - h * 3 // 4),
                  (x + h // 4, y - h // 2)], color)


def draw_lighthouse(cv, x, y, h):
    """A white lighthouse with a red cap, base at (x, y); returns lamp pos."""
    w = 16
    cv.fill_rect(x - w // 2, y - h, x + w // 2, y, WHITE)
    cv.fill_rect(x - w // 2, y - h + 14, x + w // 2, y - h + 20, ROOF)
    cv.fill_rect(x - w // 2, y - h + 34, x + w // 2, y - h + 40, ROOF)
    cv.fill_rect(x - w // 2 - 2, y - h - 10, x + w // 2 + 2, y - h, NAVY)
    cv.fill_circle(x, y - h - 5, 5, SUN_BIG)
    cv.fill_rect(x - 3, y - 6, x + 3, y, NAVY)
    return (x, y - h - 5)


def draw_beam(cv, x, y, dx, dy, length, color):
    """A soft light beam from the lamp, drawn as fading parallel lines."""
    for k in range(5):
        off = (k - 2) * 3
        px = x + dx * 0 + off
        py = y + dy * 0
        qx = x + dx * length + off
        qy = y + dy * length
        a = 0.5 - abs(k - 2) * 0.1
        # draw the beam as a series of blended dots along its length
        steps = length // 3
        for i in range(steps):
            t = i / max(1, steps - 1)
            bx = int(px + (qx - px) * t)
            by = int(py + (qy - py) * t)
            cv.blend(bx, by, color, a * (1 - t * 0.6))


def draw_island(cv, cx, cy, rx, ry, tip_y, houses=True):
    """A floating island: green cap, rocky cone underside to tip_y."""
    # rocky underside: a cone with slightly wavy sides
    pts = []
    steps = 14
    for i in range(steps + 1):
        t = i / steps
        y = cy + int((tip_y - cy) * t)
        half = int(rx * (1 - t) * (1 - 0.12 * math.sin(t * 9.0)))
        pts.append((cx - half, y))
    for i in range(steps, -1, -1):
        t = i / steps
        y = cy + int((tip_y - cy) * t)
        half = int(rx * (1 - t) * (1 - 0.12 * math.sin(t * 9.0)))
        pts.append((cx + half, y))
    cv.fill_poly(pts, ROCK)
    # rock shading: darker wedge on the right side
    shade = [(cx, cy), (cx + rx, cy),
             (cx + int(rx * 0.12), tip_y), (cx, tip_y)]
    cv.fill_poly(shade, ROCK_DK)
    # green cap
    cv.fill_ellipse(cx, cy, rx, ry, ISLE_GREEN)
    cv.fill_ellipse(cx, cy - ry // 3, rx - 8, ry * 2 // 3, ISLE_GREEN)
    # cap rim shadow
    cv.ellipse(cx, cy, rx, ry, ISLE_GREEN_DK)
    if houses:
        # a tiny white village along the cap
        draw_house(cv, cx - rx + 26, cy - 2, 34, 22)
        draw_house(cv, cx - rx + 72, cy - 4, 28, 18)
        draw_house(cv, cx + rx - 66, cy - 2, 30, 20)
        draw_pine(cv, cx - rx + 118, cy - 2, 30)
        draw_pine(cv, cx + rx - 96, cy - 4, 26)
    return (cx, cy)


def draw_waterfall(cv, x, y0, y1):
    """A thin fall of water from an island edge to the sea."""
    wob = 0
    for y in range(y0, y1, 2):
        wob = int(2 * math.sin((y - y0) / 14.0))
        cv.set(x + wob, y, FOAM)
        cv.set(x + wob + 1, y, FOAM)
        if y % 6 == 0:
            cv.set(x + wob + 3, y, FOAM)
    # foam burst where it meets the sea
    for dx in range(-7, 8):
        cv.set(x + dx, y1 - 1, FOAM)
        if abs(dx) < 4:
            cv.set(x + dx, y1 - 3, FOAM)


def draw_sea(cv):
    cv.vgrad(ART_X0, HORIZON, ART_X1, ART_Y1, SEA_TOP, SEA_BOT)
    # mirror of the big sun: a shimmering column under it
    for y in range(HORIZON + 6, ART_Y1 - 60, 4):
        t = (y - HORIZON) / (ART_Y1 - HORIZON)
        half = int(26 + 90 * t)
        for x in range(700 - half, 700 + half, 7):
            if (x * 7 + y * 3) % 11 < 6:
                cv.blend(x, y, SUN_HALO, 0.55 * (1 - t * 0.5))
    # mirror of the small sun: a fainter column
    for y in range(HORIZON + 6, ART_Y1 - 140, 5):
        t = (y - HORIZON) / (ART_Y1 - HORIZON)
        half = int(14 + 44 * t)
        for x in range(290 - half, 290 + half, 9):
            if (x * 5 + y * 7) % 13 < 3:
                cv.blend(x, y, SUN_SMALL, 0.4 * (1 - t * 0.5))
    # mirrored island silhouettes, dim and flipped
    for (cx, top, rx, depth, col) in ((512, HORIZON, 240, 72, (20, 60, 76)),
                                       (215, HORIZON, 120, 52, (22, 64, 80)),
                                       (830, HORIZON, 100, 44, (22, 64, 80))):
        for i in range(depth):
            t = i / depth
            half = int(rx * (1 - t * 0.85))
            y = top + 4 + i
            a = 0.5 * (1 - t)
            for x in range(cx - half, cx + half, 3):
                cv.blend(x, y, col, a)
    # glass sheen: long thin highlights
    for (y, x0, x1, a) in ((700, 120, 900, 0.35), (760, 180, 700, 0.3),
                           (830, 620, 940, 0.3), (880, 90, 420, 0.25),
                           (720, 700, 960, 0.22)):
        for x in range(x0, x1):
            cv.blend(x, y, FOAM, a * (0.5 + 0.5 * math.sin(x / 23.0)))


def draw_boat(cv, x, y):
    """A small sailboat on the glass sea, with its reflection."""
    # hull
    cv.fill_poly([(x - 26, y), (x + 26, y), (x + 16, y + 10),
                  (x - 16, y + 10)], NAVY)
    # mast + sails
    cv.vline(x, y - 44, y, NAVY_LT)
    cv.fill_poly([(x + 2, y - 42), (x + 2, y - 4), (x + 26, y - 4)], WHITE)
    cv.fill_poly([(x - 2, y - 36), (x - 2, y - 4), (x - 20, y - 4)], CREAM)
    cv.fill_circle(x, y - 46, 3, GOLD)
    # reflection, dimmed and flipped
    for dy in range(1, 16):
        half = int(24 * (1 - dy / 18.0))
        for xx in range(x - half, x + half):
            cv.blend(xx, y + 11 + dy, NAVY, 0.35 * (1 - dy / 18.0))

# --------------------------------------------------------------------- poster
def draw_frame(cv):
    cv.fill_rect(0, 0, W - 1, H - 1, PAPER)
    cv.rect_outline(10, 10, W - 11, H - 11, NAVY, 5)
    cv.rect_outline(24, 24, W - 25, H - 25, GOLD, 2)
    # corner diamonds on the outer frame
    for (cx, cy) in ((512, 12), (512, 1012), (12, 512), (1012, 512)):
        cv.fill_poly([(cx, cy - 7), (cx + 7, cy), (cx, cy + 7),
                      (cx - 7, cy)], GOLD)


def draw_title(cv):
    # the place name, big and legible, set over the deep sky
    draw_shadow_text(cv, 512, 66, "VELMARA", 11, CREAM, NAVY, bold=True)
    # gold rule with a diamond, under the name
    cv.hline(300, 470, 168, GOLD)
    cv.hline(554, 724, 168, GOLD)
    cv.fill_poly([(512, 160), (520, 168), (512, 176), (504, 168)], GOLD)
    draw_shadow_text(cv, 512, 188, "WHERE THE ISLANDS FLOAT", 3,
                     GOLD_LT, NAVY, bold=True)


def draw_footer(cv):
    # a navy band at the foot of the poster carrying the invitation
    cv.fill_rect(ART_X0, 916, ART_X1, ART_Y1, NAVY)
    cv.hline(ART_X0, ART_X1, 916, GOLD)
    cv.hline(ART_X0, ART_X1, 917, GOLD)
    text_center(cv, 512, 934,
                "TWO SUNS \u2022 ONE SEA OF GLASS \u2022 SAIL BEYOND THE MAP",
                2, CREAM, bold=True)
    text_center(cv, 512, 958, "VISIT VELMARA", 2, GOLD_LT, bold=True)


def build():
    cv = Canvas(W, H, PAPER)
    draw_frame(cv)
    draw_sky(cv)
    # twin suns: one amber, one pale, clear of the title and tagline
    draw_sun(cv, 700, 300, 62, SUN_BIG, SUN_HALO, 78)
    draw_sun(cv, 290, 310, 34, SUN_SMALL, (247, 232, 195), 46)
    # a few flat clouds drifting between the suns
    draw_cloud(cv, 470, 288, 150, (250, 238, 210))
    draw_cloud(cv, 880, 190, 110, (247, 232, 200))
    draw_cloud(cv, 150, 320, 120, (250, 240, 214))
    # birds
    for (x, y, s) in ((420, 330, 12), (455, 315, 9), (620, 240, 10),
                      (790, 350, 9), (250, 380, 10)):
        draw_bird(cv, x, y, s, NAVY_LT)
    # the floating isles: one great island, two small ones
    draw_island(cv, 215, 420, 130, 30, 522, houses=False)
    draw_pine(cv, 175, 414, 34)
    draw_pine(cv, 215, 410, 40)
    draw_pine(cv, 255, 414, 30)
    draw_island(cv, 830, 452, 112, 27, 540, houses=False)
    draw_house(cv, 800, 446, 30, 18)
    draw_pine(cv, 868, 448, 32)
    draw_island(cv, 512, 470, 258, 54, 612)
    lamp = draw_lighthouse(cv, 612, 452, 74)
    draw_beam(cv, lamp[0], lamp[1], -1, -0.35, 150, SUN_HALO)
    # waterfalls spilling from the isles into the glass sea
    draw_waterfall(cv, 330, 500, HORIZON)
    draw_waterfall(cv, 694, 506, HORIZON)
    draw_waterfall(cv, 150, 448, HORIZON)
    draw_waterfall(cv, 886, 478, HORIZON)
    draw_sea(cv)
    draw_boat(cv, 400, 782)
    draw_boat(cv, 640, 838)
    draw_title(cv)
    draw_footer(cv)
    return cv


# ---------------------------------------------------------------------- main
def main():
    out_dir = OUT
    os.makedirs(out_dir, exist_ok=True)
    # Clear only the contents of the output directory (it may be a mount).
    for name in os.listdir(out_dir):
        p = os.path.join(out_dir, name)
        if os.path.isfile(p):
            os.remove(p)
    cv = build()
    path = os.path.join(out_dir, "entry.png")
    size = write_png(cv, path)
    print(f"wrote {path} ({size} bytes)")


if __name__ == "__main__":
    main()
