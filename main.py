#!/usr/bin/env python3
"""THE WORLD IN ONE DAY -- front page for Saturday 21 November 2026.

A one-page newspaper summing up the day's world news, drawn entirely in
code and written out as a 1024x1024 PNG to /output/entry.png.

Pure standard library, no network, no clock, no randomness, fixed
compression, so two runs produce byte-identical output. The four-frame
hero band is drawn procedurally: a night map of Europe under missile
trails, a cyclone spiral over the sea, a plunging market chart, and a
summit hall of flags.
"""
import binascii
import math
import os
import struct
import zlib

W, H = 1024, 1024
PAPER = (247, 243, 232)
INK = (20, 20, 20)
RED = (163, 18, 18)
NAVY = (26, 42, 74)
MUTED = (96, 92, 82)
WHITE = (255, 255, 255)
FAINT = (226, 220, 204)
NIGHT = (16, 24, 48)
LAND = (38, 58, 96)
AMBER = (232, 170, 60)
SEABLUE = (14, 34, 64)
SKY = (20, 28, 52)
SPIRAL = (205, 214, 228)
CHARTBG = (10, 14, 28)
CHARTRED = (230, 60, 50)
HALLBG = (30, 24, 20)
FLAGCOLORS = [
    (200, 40, 40), (40, 90, 200), (240, 210, 60), (40, 160, 80),
    (240, 240, 240), (220, 120, 30), (120, 60, 160), (30, 140, 140),
]


# 5x7 bitmap font: seven rows of five bits per glyph.
FONT = {
    "A": "01110 10001 10001 11111 10001 10001 10001",
    "B": "11110 10001 10001 11110 10001 10001 11110",
    "C": "01110 10001 10000 10000 10000 10001 01110",
    "D": "11110 10001 10001 10001 10001 10001 11110",
    "E": "11111 10000 10000 11110 10000 10000 11111",
    "F": "11111 10000 10000 11110 10000 10000 10000",
    "G": "01110 10001 10000 10111 10001 10001 01111",
    "H": "10001 10001 10001 11111 10001 10001 10001",
    "I": "01110 00100 00100 00100 00100 00100 01110",
    "J": "00111 00010 00010 00010 00010 10010 01100",
    "K": "10001 10010 10100 11000 10100 10010 10001",
    "L": "10000 10000 10000 10000 10000 10000 11111",
    "M": "10001 11011 10101 10101 10001 10001 10001",
    "N": "10001 11001 10101 10011 10001 10001 10001",
    "O": "01110 10001 10001 10001 10001 10001 01110",
    "P": "11110 10001 10001 11110 10000 10000 10000",
    "Q": "01110 10001 10001 10001 10101 10010 01101",
    "R": "11110 10001 10001 11110 10100 10010 10001",
    "S": "01111 10000 10000 01110 00001 00001 11110",
    "T": "11111 00100 00100 00100 00100 00100 00100",
    "U": "10001 10001 10001 10001 10001 10001 01110",
    "V": "10001 10001 10001 10001 10001 01010 00100",
    "W": "10001 10001 10001 10101 10101 11011 10001",
    "X": "10001 10001 01010 00100 01010 10001 10001",
    "Y": "10001 10001 01010 00100 00100 00100 00100",
    "Z": "11111 00001 00010 00100 01000 10000 11111",
    "0": "01110 10001 10011 10101 11001 10001 01110",
    "1": "00100 01100 00100 00100 00100 00100 01110",
    "2": "01110 10001 00001 00110 01000 10000 11111",
    "3": "11111 00010 00100 00010 00001 10001 01110",
    "4": "00010 00110 01010 10010 11111 00010 00010",
    "5": "11111 10000 11110 00001 00001 10001 01110",
    "6": "00110 01000 10000 11110 10001 10001 01110",
    "7": "11111 00001 00010 00100 01000 01000 01000",
    "8": "01110 10001 10001 01110 10001 10001 01110",
    "9": "01110 10001 10001 01111 00001 00010 01100",
    " ": "00000 00000 00000 00000 00000 00000 00000",
    ".": "00000 00000 00000 00000 00000 01100 01100",
    ",": "00000 00000 00000 00000 01100 00100 01000",
    ":": "00000 01100 01100 00000 01100 01100 00000",
    ";": "00000 01100 01100 00000 01100 00100 01000",
    "!": "00100 00100 00100 00100 00100 00000 00100",
    "?": "01110 10001 00001 00110 00100 00000 00100",
    "'": "00100 00100 01000 00000 00000 00000 00000",
    '"': "01010 01010 01010 00000 00000 00000 00000",
    "-": "00000 00000 00000 01110 00000 00000 00000",
    "/": "00001 00010 00010 00100 01000 01000 10000",
    "(": "00010 00100 01000 01000 01000 00100 00010",
    ")": "01000 00100 00010 00010 00010 00100 01000",
    "$": "00100 01111 10100 01110 00101 11110 00100",
    "%": "11001 11010 00010 00100 01000 01011 10011",
    "&": "01100 10010 10100 01000 10101 10010 01101",
    "+": "00000 00100 00100 11111 00100 00100 00000",
    "=": "00000 00000 11111 00000 11111 00000 00000",
    "*": "00000 10101 01110 10101 00000 00000 00000",
    "#": "01010 01010 11111 01010 11111 01010 01010",
    "@": "01110 10001 10111 10101 10110 10000 01110",
    "_": "00000 00000 00000 00000 00000 00000 11111",
    "|": "00100 00100 00100 00100 00100 00100 00100",
}
BLANK = ["00000"] * 7


def glyph_rows(ch):
    g = FONT.get(ch.upper())
    return g.split(" ") if g else BLANK


def text_w(s, sc):
    return len(s) * 6 * sc


class Page:
    def __init__(self):
        self.px = bytearray(PAPER * (W * H))

    def put(self, x, y, col):
        if 0 <= x < W and 0 <= y < H:
            o = (y * W + x) * 3
            self.px[o:o + 3] = bytes(col)

    def rect(self, x, y, w, h, col):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(W, x + w), min(H, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        band = bytes(col) * (x1 - x0)
        for yy in range(y0, y1):
            o = (yy * W + x0) * 3
            self.px[o:o + len(band)] = band

    def line(self, x0, y0, x1, y1, col):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.put(x0, y0, col)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def thick_line(self, x0, y0, x1, y1, col, t=2):
        for ox in range(t):
            for oy in range(t):
                self.line(x0 + ox, y0 + oy, x1 + ox, y1 + oy, col)

    def disc(self, cx, cy, r, col):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.put(xx, yy, col)

    def ring(self, cx, cy, r, col):
        steps = max(24, r * 6)
        for i in range(steps):
            a = 2 * math.pi * i / steps
            self.put(int(cx + r * math.cos(a)), int(cy + r * math.sin(a)), col)

    def arc(self, cx, cy, r, a0, a1, col):
        steps = max(8, int(r * abs(a1 - a0)))
        for i in range(steps + 1):
            a = a0 + (a1 - a0) * i / steps
            self.put(int(cx + r * math.cos(a)), int(cy + r * math.sin(a)), col)

    def text(self, s, x, y, sc, col):
        for ch in s:
            for r, bits in enumerate(glyph_rows(ch)):
                for c, b in enumerate(bits):
                    if b == "1":
                        self.rect(x + c * sc, y + r * sc, sc, sc, col)
            x += 6 * sc

    def centred(self, s, cx, y, sc, col):
        self.text(s, cx - text_w(s, sc) // 2, y, sc, col)

    def wrap(self, s, maxw, sc):
        out = []
        for chunk in s.split("\n"):
            cur = ""
            for word in chunk.split(" "):
                cand = word if not cur else cur + " " + word
                if text_w(cand, sc) <= maxw or not cur:
                    cur = cand
                else:
                    out.append(cur)
                    cur = word
            if cur:
                out.append(cur)
        return out

    def para(self, s, x, y, maxw, sc, col, gap):
        for ln in self.wrap(s, maxw, sc):
            self.text(ln, x, y, sc, col)
            y += gap
        return y


def quad(p, p0, p1, p2, col, steps=40):
    prev = None
    for i in range(steps + 1):
        t = i / steps
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
        cur = (int(x), int(y))
        if prev is not None:
            p.thick_line(prev[0], prev[1], cur[0], cur[1], col, 2)
        prev = cur


# --- hero band: four procedural panels, x=28..996, y=120..420 ---
def panel_map(p, x, y, w, h):
    p.rect(x, y, w, h, NIGHT)
    # stylised European landmass: a cluster of discs.
    land = [(60, 150, 52), (110, 120, 58), (165, 105, 48), (200, 140, 42),
            (150, 175, 55), (95, 195, 46), (185, 195, 38), (70, 110, 34),
            (130, 85, 30), (210, 95, 26)]
    for cx, cy, r in land:
        p.disc(x + cx, y + cy, r, LAND)
    # city lights.
    for cx, cy in [(70, 140), (105, 115), (140, 100), (175, 125), (150, 170),
                   (100, 190), (195, 165), (120, 150), (85, 165), (205, 115)]:
        p.disc(x + cx, y + cy, 3, AMBER)
        p.put(x + cx, y + cy, (255, 230, 160))
    # missile trails arcing in from the top right, red-orange.
    trails = [((235, 8), (190, 60), (170, 118)),
              ((215, 2), (150, 70), (120, 132)),
              ((240, 40), (205, 95), (185, 160))]
    for a, b, c in trails:
        quad(p, (x + a[0], y + a[1]), (x + b[0], y + b[1]),
             (x + c[0], y + c[1]), (240, 90, 40))
        quad(p, (x + a[0] + 1, y + a[1]), (x + b[0] + 1, y + b[1]),
             (x + c[0] + 1, y + c[1]), (255, 180, 90))
        p.disc(x + c[0], y + c[1], 4, (255, 220, 120))
        for dx, dy in [(8, 0), (-8, 0), (0, 8), (0, -8), (6, 6), (-6, -6)]:
            p.line(x + c[0], y + c[1], x + c[0] + dx, y + c[1] + dy,
                   (255, 200, 110))
    # labels for the two places the story names.
    p.disc(x + 165, y + 118, 3, WHITE)
    p.text("POLAND", x + 148, y + 130, 1, WHITE)
    p.disc(x + 180, y + 160, 3, WHITE)
    p.text("UKRAINE", x + 162, y + 172, 1, WHITE)


def panel_cyclone(p, x, y, w, h):
    p.rect(x, y, w, h, SKY)
    p.rect(x, y + 190, w, h - 190, SEABLUE)
    cx, cy = x + w // 2, y + 118
    # spiral arms: two and a half turns, kept inside the panel.
    for turn in range(3):
        pts = []
        for i in range(90):
            t = 2 * math.pi * (turn + i / 90.0) / 1.2
            r = 5 + 5.5 * t
            pts.append((int(cx + r * math.cos(t)), int(cy + r * math.sin(t))))
        for a, b in zip(pts, pts[1:]):
            p.thick_line(a[0], a[1], b[0], b[1], SPIRAL, 2)
    p.disc(cx, cy, 7, (235, 238, 245))
    # rain streaks under the storm.
    for i in range(26):
        rx = x + 12 + (i * 37) % (w - 24)
        ry = y + 205 + (i * 13) % 70
        p.line(rx, ry, rx - 5, ry + 16, (170, 185, 210))
    # lit coastline at the bottom.
    for i in range(14):
        p.disc(x + 10 + i * 17, y + h - 14 - (i % 3) * 4, 2, AMBER)


def panel_chart(p, x, y, w, h):
    p.rect(x, y, w, h, CHARTBG)
    for gx in range(x + 24, x + w, 30):
        p.line(gx, y + 12, gx, y + h - 12, (28, 34, 58))
    for gy in range(y + 24, y + h, 30):
        p.line(x + 12, gy, x + w - 12, gy, (28, 34, 58))
    pts = [(18, 34), (45, 58), (62, 48), (88, 92), (110, 78), (132, 130),
           (155, 118), (178, 172), (196, 158), (214, 208), (226, 246)]
    for a, b in zip(pts, pts[1:]):
        p.thick_line(x + a[0], y + a[1], x + b[0], y + b[1], CHARTRED, 3)
    ex, ey = x + 226, y + 246
    p.line(ex, ey, ex, ey - 26, CHARTRED)
    p.line(ex, ey - 26, ex - 8, ey - 14, CHARTRED)
    p.line(ex, ey - 26, ex + 8, ey - 14, CHARTRED)
    p.text("-3.7%", x + 16, y + 16, 2, CHARTRED)


def panel_summit(p, x, y, w, h):
    p.rect(x, y, w, h, HALLBG)
    cx = x + w // 2
    for r in (96, 78, 60):
        p.arc(cx, y + 215, r, math.pi, 2 * math.pi, (150, 110, 60))
    # two rows of flags.
    for row, fy in enumerate((y + 150, y + 182)):
        for i in range(13):
            fx = x + 14 + i * 17
            p.rect(fx, fy, 11, 20, FLAGCOLORS[(i + row * 3) % len(FLAGCOLORS)])
            p.line(fx + 5, fy, fx + 5, fy - 8, (180, 170, 150))
    # podium and delegates.
    p.rect(cx - 34, y + 226, 68, 26, (90, 64, 40))
    for i in range(12):
        dx = x + 18 + i * 19
        p.disc(dx, y + 268, 5, (12, 10, 10))
        p.rect(dx - 8, y + 272, 16, 14, (16, 14, 14))


# --- the day's news ---
LEAD_KICKER = "WAR IN EUROPE"
LEAD_HEAD = "RUSSIAN MISSILES LAND IN POLAND AS UKRAINE ENDURES ITS BIGGEST BARRAGE"
LEAD_DECK = ("MORE THAN 400 DRONES AND 110 MISSILES HIT UKRAINE OVERNIGHT; "
             "THREE RUSSIAN WEAPONS CAME DOWN IN POLAND, A NATO MEMBER. "
             "WARSAW CALLS IT A DELIBERATE PROVOCATION.")
STORIES = [
    ("WEATHER",
     "CYCLONE AKVAN SLAMS INDIA'S EAST COAST",
     "300,000+ MOVED TO SAFETY AS THE STORM CROSSED ODISHA; "
     "NO MAJOR DAMAGE REPORTED."),
    ("MARKETS",
     "WALL STREET SLUMPS; S&P 500 ENTERS CORRECTION",
     "STOCKS FELL ABOUT 3.7% AS AI SHARES SOLD OFF."),
    ("CLIMATE",
     "COP31 DRAFT DROPS 'FOSSIL FUELS'",
     "THE WORDS VANISH FROM THE DRAFT CLIMATE DEAL."),
    ("DIPLOMACY",
     "TRUMP, XI AND PUTIN LEAVE SUMMIT WITH LITTLE",
     "A DAY AFTER THE SHENZHEN TABLE, MOSCOW'S BARRAGE FOLLOWED."),
]
NUMBERS = [("400+", "DRONES AT UKRAINE"), ("110+", "MISSILES FIRED"),
           ("8", "KILLED IN UKRAINE"), ("300,000+", "EVACUATED IN INDIA")]
WIRE = ("KRYVYI RIH: 2 DEAD, 42 HURT IN NEW STRIKE + UK AND EU SIGN FOOD, "
        "CARBON AND YOUTH DEALS + EU AGREES 1BN EURO MILITARY AID FOR UKRAINE")


def render():
    p = Page()
    p.centred("THE WORLD IN ONE DAY", W // 2, 16, 7, INK)
    p.rect(28, 72, 968, 2, INK)
    p.rect(28, 76, 968, 3, RED)
    p.centred("SATURDAY 21 NOVEMBER 2026", W // 2, 86, 3, NAVY)
    p.rect(28, 112, 968, 2, INK)
    # hero band, four panels.
    p.rect(28, 120, 968, 300, INK)
    panel_map(p, 30, 122, 240, 296)
    panel_cyclone(p, 272, 122, 240, 296)
    panel_chart(p, 514, 122, 240, 296)
    panel_summit(p, 756, 122, 240, 296)
    for dx in (270, 512, 754):
        p.rect(dx, 122, 2, 296, INK)
    p.centred("FOUR FRAMES FROM SATURDAY 21 NOVEMBER 2026", W // 2, 430, 2, MUTED)
    p.text(LEAD_KICKER, 28, 458, 2, RED)
    y = p.para(LEAD_HEAD, 28, 482, 968, 4, INK, 34)
    y = p.para(LEAD_DECK, 28, y + 8, 968, 2, INK, 20)
    p.rect(28, y + 10, 968, 2, INK)
    gy = y + 24
    for i, (kick, head, deck) in enumerate(STORIES):
        cx = 28 if i % 2 == 0 else 526
        cy = gy + (i // 2) * 118
        p.text(kick, cx, cy, 2, RED)
        hy = p.para(head, cx, cy + 20, 470, 2, INK, 18)
        p.para(deck, cx, hy + 4, 470, 2, MUTED, 18)
        if i % 2 == 0:
            p.rect(502, cy, 2, 106, FAINT)
    by = gy + 236
    p.rect(28, by, 968, 2, NAVY)
    p.rect(28, by + 52, 968, 2, NAVY)
    p.rect(28, by, 2, 54, NAVY)
    p.rect(994, by, 2, 54, NAVY)
    for j, (num, lab) in enumerate(NUMBERS):
        nx = 28 + j * 242
        p.text(num, nx + 12, by + 8, 3, RED)
        p.text(lab, nx + 12, by + 32, 2, INK)
    p.rect(0, 946, W, 52, NAVY)
    p.rect(0, 946, W, 3, RED)
    ty = 956
    for ln in p.wrap(WIRE, 968, 2):
        p.text(ln, 28, ty, 2, WHITE)
        ty += 18
    p.centred("ONE DAY. ONE PAGE. THE WHOLE WORLD.", W // 2, 1004, 2, MUTED)
    return p.px


def chunk(kind, data):
    return (struct.pack(">I", len(data)) + kind + data
            + struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF))


def to_png(px):
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    body = bytearray()
    stride = W * 3
    for yy in range(H):
        body.append(0)
        body += px[yy * stride:(yy + 1) * stride]
    blob = zlib.compress(bytes(body), 9)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", blob) + chunk(b"IEND", b""))


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    data = to_png(render())
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as fh:
        fh.write(data)
    print("wrote %s (%d bytes)" % (path, len(data)))


if __name__ == "__main__":
    raise SystemExit(main())
