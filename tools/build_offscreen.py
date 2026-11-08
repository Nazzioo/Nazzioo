#!/usr/bin/env python3
"""
Pixel-art footer for the Nazzioo GitHub profile, with a contact line.

A Japanese room at night, in blue and yellow. Through a round window: two
moons (for Murakami), big clouds (for Miyazaki), a cow in a meadow and
fireflies, with a cat watching from the sill. Inside: a paper lantern, an
easel with a painting, a record player, books with headphones, a podcast mic,
candles, hydrangeas and a lit shoji. On the wall: "CONTACT ME:" and the email.

Writes an animated SVG (twinkling stars, fireflies, flickering candles, music
notes, a spinning record and a swishing tail). Same approach as the sakura
header: plain rects and paths, crisp at any width.

    python3 tools/build_offscreen.py
"""
import math
import random
from pathlib import Path

W, H = 256, 80
FLOOR = 64  # first floor row
RS = 16  # the cabinet, its things and the shoji sit this far right, to leave room for the text
OUT = Path(__file__).resolve().parent.parent / "assets" / "offscreen.svg"

rng = random.Random(20261108)
px = [[None] * W for _ in range(H)]

# blues, darkest to lightest
B = ["#060a20", "#0c1333", "#131c46", "#1a275c", "#223373", "#2c428d",
     "#3955a8", "#4c6fc6", "#6890df", "#93b5f2", "#c6d9fb", "#eef4ff"]
# yellows, darkest to lightest
Y = ["#3f3112", "#6b5218", "#98741f", "#c49a2a", "#e8bd3a", "#ffd65a",
     "#ffe58f", "#fff3c9"]


SHIFT = 0  # set to RS while drawing the right-hand side


def put(x, y, c):
    x += SHIFT
    if 0 <= x < W and 0 <= y < H:
        px[y][x] = c


def get(x, y):
    x += SHIFT
    return px[y][x] if 0 <= x < W and 0 <= y < H else None


BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def thr(x, y):
    return (BAYER[y % 4][x % 4] + 0.5) / 16


def h01(x, y, s=0):
    n = (x * 374761393 + y * 668265263 + s * 974711) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65536


def ramp(colors, f, x, y, sharp=2.2):
    """Dithered pick along a palette; f in [0, 1]."""
    n = len(colors) - 1
    f = max(0.0, min(1.0, f)) * n
    i = min(int(f), n - 1)
    k = max(0.0, min(1.0, (f - i - 0.5) * sharp + 0.5))
    return colors[i + 1] if k > thr(x, y) else colors[i]


def sprite(rows, x0, y0, cmap):
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch != ".":
                put(x0 + i, y0 + j, cmap[ch])


def stroke(x0, y0, x1, y1, colors):
    """A line; colors lists the pixel colours across its width, left to right."""
    n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
    for k in range(n + 1):
        t = k / n
        x = int(round(x0 + (x1 - x0) * t))
        y = int(round(y0 + (y1 - y0) * t))
        for i, c in enumerate(colors):
            put(x + i, y, c)


def puff(cx, cy, r, pal, seed, light=(-0.6, -0.8), mask=None):
    """A lumpy ball (cloud, flower head), lit from `light`, five-shade palette."""
    rr = random.Random(seed)
    subs = []
    for _ in range(int(r * r / 4.0) + 3):
        a = rr.random() * math.tau
        d = math.sqrt(rr.random()) * r * 0.7
        subs.append((cx + math.cos(a) * d, cy + math.sin(a) * d, 1.6 + rr.random() * 1.4 + r * 0.15))
    drawn = set()
    for y in range(int(cy - r - 4), int(cy + r + 5)):
        for x in range(int(cx - r - 4), int(cx + r + 5)):
            if mask is not None and (x, y) not in mask:
                continue
            best = None
            for (sx, sy, sr) in subs:
                q = math.hypot(x + 0.5 - sx, y + 0.5 - sy) / sr
                if best is None or q < best[0]:
                    best = (q, sx, sy, sr)
            q, sx, sy, sr = best
            if q > 1 + (h01(x, y, seed) - 0.5) * 0.3:
                continue
            s_sub = ((x + 0.5 - sx) * light[0] + (y + 0.5 - sy) * light[1]) / sr
            s_all = ((x - cx) * light[0] + (y - cy) * light[1]) / r
            s = 0.55 * s_sub + 0.55 * s_all + (h01(x, y, seed + 1) - 0.5) * 0.3
            idx = 4 if s > 0.62 else 3 if s > 0.18 else 2 if s > -0.28 else 1 if s > -0.7 else 0
            put(x, y, pal[idx])
            drawn.add((x, y))
    return drawn


# ---------------------------------------------------------------- room
LIGHTS = [(57, 15, 26, 0.5), (189 + RS, 40, 30, 0.55)]  # lantern, candles
WALL = [B[1], B[2], B[3], B[4], B[5]]
wall_px = set()


def wall():
    for y in range(3, FLOOR):
        for x in range(W):
            f = 0.30 + 0.18 * (y - 3) / (FLOOR - 3)
            for (lx, ly, r, k) in LIGHTS:
                d = math.hypot(x - lx, (y - ly) * 1.3)
                if d < r:
                    f += k * (1 - d / r) ** 1.6
            put(x, y, ramp(WALL, f, x, y))
            wall_px.add((x, y))
    for x in range(W):  # ceiling beam and baseboard
        put(x, 0, B[1])
        put(x, 1, B[2])
        put(x, 2, B[0])
        put(x, 62, B[1])
        put(x, 63, B[0])
        wall_px.discard((x, 62))
        wall_px.discard((x, 63))


VP = (W // 2, 28)  # vanishing point for the tatami seams


def floor():
    for y in range(FLOOR, H):
        t = (y - FLOOR) / (H - 1 - FLOOR)
        for x in range(W):
            f = 0.2 + 0.7 * t - (0.12 if y % 2 else 0)
            put(x, y, ramp([Y[1], Y[2], Y[3]], f, x, y))
    for x in range(W):  # border cloth along the wall
        put(x, FLOOR, B[3])
        put(x, FLOOR + 1, B[2])
    for xt in (60, 196):
        for y in range(FLOOR + 2, H):
            sx = VP[0] + (xt - VP[0]) * (y - VP[1]) / (FLOOR - VP[1])
            w = 2 if y < 72 else 3
            for i in range(w):
                put(int(sx) + i, y, B[3] if h01(int(sx) + i, y, 2) > 0.15 else B[5])


# ---------------------------------------------------------------- round window
WX, WY, RI, RO = 97, 32, 23, 26
HY = 41  # horizon inside the window
SKYW = [B[0], B[1], B[2], B[3], B[4], B[5], B[6]]
win = set()
MOON = (88, 19, 5.2)
MOON2 = (108, 16, 3.0)


def window():
    top = WY - RI
    for y in range(WY - RO - 1, WY + RO + 2):
        for x in range(WX - RO - 1, WX + RO + 2):
            dx, dy = x + 0.5 - WX, y + 0.5 - WY
            d = math.hypot(dx, dy)
            if d <= RI:
                win.add((x, y))
                put(x, y, ramp(SKYW, (y - top) / (HY - top), x, y))
            elif d <= RO:
                wall_px.discard((x, y))
                if d <= RI + 1:
                    c = B[0] if dy < 0 else B[4]
                elif d > RO - 1:
                    c = B[3] if dy < 0 else B[0]
                else:
                    c = B[1]
                put(x, y, c)


def sky_details():
    mx, my, mr = MOON
    for _ in range(26):
        x, y = rng.randrange(WX - RI, WX + RI), rng.randrange(WY - RI, 32)
        if (x, y) in win and math.hypot(x - mx, y - my) > mr + 3:
            put(x, y, B[9] if rng.random() < 0.7 else Y[7])
    for y in range(int(my - mr - 4), int(my + mr + 5)):
        for x in range(int(mx - mr - 4), int(mx + mr + 5)):
            if (x, y) not in win:
                continue
            d = math.hypot(x + 0.5 - mx, y + 0.5 - my)
            if d <= mr:
                s = ((x + 0.5 - mx) * -0.7 + (y + 0.5 - my) * -0.7) / mr
                put(x, y, Y[7] if s > 0.3 else Y[6] if s > -0.4 else Y[5])
            elif d <= mr + 1.4 and thr(x, y) < 0.5:
                put(x, y, B[6])
            elif d <= mr + 3 and thr(x, y) < 0.22:
                put(x, y, B[5])
    for (x, y) in [(int(mx) + 1, int(my) + 1), (int(mx) - 2, int(my) + 2), (int(mx) + 2, int(my) - 2)]:
        put(x, y, Y[5])
    m2x, m2y, m2r = MOON2  # a thin crescent
    for y in range(int(m2y - 4), int(m2y + 5)):
        for x in range(int(m2x - 4), int(m2x + 5)):
            inside = math.hypot(x + 0.5 - m2x, y + 0.5 - m2y) <= m2r
            cut = math.hypot(x + 0.5 - (m2x + 1.4), y + 0.5 - (m2y - 0.9)) <= m2r - 0.3
            if inside and not cut:
                put(x, y, B[10] if y + 0.5 < m2y + 1 else B[9])
    cloud = [B[4], B[5], B[7], B[8], B[10]]
    for i, (cx, cy, r) in enumerate([(104, 33, 5.5), (111, 31, 3.8), (97, 35, 3.5), (80, 34, 3.2), (86, 36, 2.6)]):
        puff(cx, cy, r, cloud, 300 + i, mask=win)


def landscape():
    for x in range(WX - RI, WX + RI + 1):
        hill = int(HY - 3 + 2 * math.sin(x / 5.0) + 1.2 * math.sin(x / 2.7 + 1))
        for y in range(hill, HY + 3):
            if (x, y) in win:
                put(x, y, B[4] if y == hill else B[3])
        mtop = int(HY + 1 + math.sin(x / 7.0))
        for y in range(mtop, WY + RI + 1):
            if (x, y) not in win:
                continue
            c = ramp([B[5], B[4], B[3]], (y - mtop) / 10, x, y)
            if h01(x, y, 11) > 0.9:
                c = B[6]
            elif h01(x, y, 12) > 0.93:
                c = B[2]
            put(x, y, c)


COW = [
    "..........y.y",
    "..........WWW",
    ".WWkkWWWWWWkW",
    "kWkkkWWWkkWWn",
    "k.WWWWWkkkWnn",
    "..WWWWWWWW...",
    "..WW...WW....",
    "..kk...kk....",
]
COW_X, COW_Y = 78, 40

CAT = [
    "..k......k..",
    "..ki....ik..",
    "..kkkkkkkk..",
    ".kkkkkkkkkk.",
    ".kkkkkkkkkk.",
    "..kkkkkkkk..",
    "...kkkkkk...",
    "..kkkkkkkk..",
    ".kkkkkkkkkk.",
    "kkkkkkkkkkkk",
    "kkkkkkkkkkkk",
    "kkkkkkkkkkkk",
    ".kkkkkkkkkk.",
]
CAT_X, CAT_Y = 92, 44


def animals():
    sprite(COW, COW_X, COW_Y, {"W": B[10], "k": B[1], "y": Y[5], "n": Y[6]})
    cells = {(i, j) for j, row in enumerate(CAT) for i, ch in enumerate(row) if ch != "."}
    for (i, j) in cells:
        ch = CAT[j][i]
        if ch == "i":
            c = B[3]
        elif (i, j - 1) not in cells:
            c = B[5]  # moonlit rim
        elif (i - 1, j) not in cells:
            c = B[4]
        else:
            c = B[0]
        put(CAT_X + i, CAT_Y + j, c)


# ---------------------------------------------------------------- left: lantern, easel
LCX, LCY = 57, 15


def lantern():
    for y in range(3, 7):
        put(LCX, y, B[0])
    for x in range(LCX - 3, LCX + 4):
        put(x, 7, B[1])
    for x in range(LCX - 4, LCX + 5):
        put(x, 8, B[0])
    body = set()
    for y in range(9, 22):
        for x in range(LCX - 7, LCX + 8):
            if ((x - LCX) / 6.2) ** 2 + ((y - LCY) / 6.6) ** 2 <= 1:
                body.add((x, y))
    for (x, y) in body:
        e = abs(x - LCX) / 6.2
        i = 7 if e < 0.4 else 6 if e < 0.7 else 5
        if (y - 9) % 2 == 1:
            i -= 1
        if any(n not in body for n in [(x - 1, y), (x + 1, y)]):
            i = 3
        put(x, y, Y[i])
    for x in range(LCX - 3, LCX + 4):
        put(x, 22, B[1])
    for x in range(LCX - 2, LCX + 3):
        put(x, 23, B[0])
    for y in range(24, 27):
        put(LCX, y, Y[4])
    for x in range(LCX - 1, LCX + 2):
        put(x, 27, Y[3])


def easel():
    stroke(29, 11, 29, 66, [Y[1]])
    stroke(22, 12, 15, 72, [Y[2], Y[1]])
    stroke(36, 12, 43, 72, [Y[2], Y[1]])
    for x in range(21, 38):
        put(x, 12, Y[2])
    for x in range(13, 46):
        put(x, 42, Y[3])
        put(x, 43, Y[1])
    for x in range(28, 31):
        put(x, 13, Y[3])
        put(x, 14, Y[2])
    # canvas with a wooden edge
    x0, y0, x1, y1 = 15, 15, 43, 41
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if x in (x0, x1) or y in (y0, y1):
                put(x, y, Y[1] if (x == x1 or y == y1) else Y[2])
    # painting: sun, Fuji, a sea of wave scales
    for y in range(y0 + 1, 32):
        for x in range(x0 + 1, x1):
            put(x, y, ramp([Y[7], Y[6]], (y - y0) / 16, x, y))
    for y in range(17, 26):
        for x in range(32, 41):
            d = math.hypot(x + 0.5 - 36.5, y + 0.5 - 21)
            if d <= 3.3:
                put(x, y, Y[5] if (x + 0.5 - 36.5) + (y + 0.5 - 21) < -1.5 else Y[4])
    for y in range(24, 32):
        hw = 0.5 + (y - 24) * 1.35
        for x in range(int(27 - hw), int(27 + hw) + 1):
            if x0 < x < x1:
                snow = y <= 25 or (y == 26 and x % 2 == 0)
                put(x, y, B[10] if snow else (B[3] if x < 27 else B[4]))
    for y in range(32, y1):
        for x in range(x0 + 1, x1):
            r = (y - 32) % 3
            shift = ((y - 32) // 3) * 3
            m = (x + shift) % 6
            c = B[6]
            if r == 0 and m in (1, 2, 3):
                c = B[9]
            elif r == 1 and m in (0, 4):
                c = B[8]
            put(x, y, c)


def painter_bits():
    # palette on the floor
    for y in range(71, 77):
        for x in range(44, 60):
            q = ((x + 0.5 - 52) / 7) ** 2 + ((y + 0.5 - 74) / 2.6) ** 2
            if q <= 1:
                put(x, y, Y[0] if q > 0.75 else Y[7])
    put(56, 74, Y[1])
    for (x, y, c) in [(48, 73, B[7]), (50, 73, Y[4]), (52, 73, B[9]), (49, 75, B[5]), (54, 75, B[10])]:
        put(x, y, c)
    # brush jar
    for y in range(63, 71):
        for x in range(3, 10):
            c = B[6]
            if x == 3:
                c = B[9]
            elif x == 9:
                c = B[4]
            if y == 63:
                c = B[8]
            elif y == 64 and 3 < x < 9:
                c = B[7]
            put(x, y, c)
    stroke(5, 62, 3, 53, [Y[2]])
    put(3, 52, B[8])
    stroke(7, 62, 7, 51, [Y[3]])
    put(7, 50, Y[5])
    stroke(8, 62, 11, 54, [Y[2]])
    put(11, 53, B[10])


def zabuton():
    x0, x1, y0, y1 = 89, 117, 68, 75
    for x in range(x0 + 1, x1 + 1):
        put(x, y1 + 1, Y[0])
    for y in range(y0, y1 + 1):
        ins = 1 if y in (y0, y1) else 0  # rounded corners
        for x in range(x0 + ins, x1 - ins + 1):
            if y == y0:
                c = B[8]
            elif y == y1:
                c = B[4]
            elif y >= y1 - 2:
                c = B[5]
            else:
                c = B[7] if y == y0 + 1 else B[6]
            if x == x0 + ins and y0 < y < y1:
                c = B[7]
            elif x == x1 - ins and y0 < y < y1:
                c = B[4]
            put(x, y, c)
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    put(cx, cy, Y[5])
    put(cx, cy + 1, B[4])
    for (x, y) in [(x0 - 1, y0 + 1), (x1 + 1, y0 + 1), (x0 - 1, y1 - 1), (x1 + 1, y1 - 1)]:
        put(x, y, Y[5])
        put(x, y + 1, Y[3])


# ---------------------------------------------------------------- right: cabinet and its things
CX0, CX1, CT = 127, 210, 50


def cabinet():
    for x in range(CX0, CX1 + 1):
        put(x, CT, B[6])
        put(x, CT + 1, B[4])
        for y in range(CT + 2, 66):
            put(x, y, B[2])
        put(x, 65, B[1])
        put(x, 66, Y[0])
    for y in range(CT + 2, 65):
        put(CX0, y, B[3])
        put(CX1, y, B[1])
    for x in range(CX0 + 1, CX1):
        put(x, 58, B[1])
    for xs in (155, 183):
        for y in range(CT + 2, 65):
            put(xs, y, B[1])
    for cx in ((CX0 + 155) // 2, (155 + 183) // 2, (183 + CX1) // 2):
        for cy in (55, 62):
            put(cx - 1, cy, Y[4])
            put(cx, cy, Y[5])
            put(cx + 1, cy, Y[3])


def record_player():
    for x in range(130, 154):
        put(x, 44, Y[5])
        for y in range(45, 50):
            put(x, y, Y[3] if y < 49 else Y[2])
    for y in range(44, 50):
        put(130, y, Y[4] if y == 44 else Y[2])
        put(153, y, Y[1])
    for y in range(46, 49):
        for x in range(133, 141):
            if (x + y) % 2 == 0:
                put(x, y, Y[2])
    put(148, 47, B[1])
    put(150, 47, B[1])
    cx, cy, rx, ry = 140, 42.5, 8.5, 2.6
    for y in range(39, 46):
        for x in range(130, 151):
            q = ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2
            if q <= 1:
                put(x, y, Y[5] if q < 0.12 else B[2] if 0.45 < q < 0.6 else B[0])
    for (x, y) in [(149, 41), (148, 41), (147, 42), (146, 42), (145, 42)]:
        put(x, y, B[9])
    put(144, 42, B[10])
    put(150, 41, B[9])
    put(150, 42, B[6])
    put(151, 42, B[6])
    put(150, 43, B[6])


BOOKS = [  # x0, x1, y0, y1, cover, label
    (156, 171, 47, 49, 6, Y[5]),
    (157, 169, 44, 46, "y", B[2]),
    (156, 168, 42, 43, 8, B[3]),
    (158, 170, 39, 41, 4, Y[5]),
]


def books():
    for (x0, x1, y0, y1, cov, label) in BOOKS:
        if cov == "y":
            mid, top, bot = Y[4], Y[5], Y[3]
        else:
            mid, top, bot = B[cov], B[cov + 1], B[cov - 1]
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                put(x, y, top if y == y0 else bot if (y == y1 and y1 > y0 + 1) else mid)
            put(x0, y, bot)
        ly = y0 + (y1 - y0 + 1) // 2
        for x in range(x0 + 4, x0 + 8):
            put(x, ly, label)
    # headphones resting on top
    for (x, y) in [(159, 34), (159, 33), (160, 32), (161, 31), (162, 31), (163, 31), (164, 31),
                   (165, 31), (166, 31), (167, 32), (168, 33), (168, 34)]:
        put(x, y, Y[4])
    for cx in (158, 167):
        for y in range(35, 39):
            for x in range(cx, cx + 3):
                c = B[9] if y < 37 else B[8]
                if (cx == 158 and x == 160) or (cx == 167 and x == 167):
                    c = B[6]
                put(x, y, c)


def mic():
    for x in range(173, 180):
        put(x, 49, B[1])
    for x in range(174, 179):
        put(x, 48, B[5])
    for y in range(42, 48):
        put(176, y, B[6])
    put(174, 41, B[5])
    put(178, 41, B[5])
    for x in range(175, 178):
        put(x, 42, B[5])
    for y in range(32, 41):
        for x in range(174, 179):
            if y in (32, 40) and x in (174, 178):
                continue
            c = B[8] if (x + y) % 2 == 0 else B[7]
            if x == 174:
                c = B[9]
            elif x == 178:
                c = B[6]
            if y == 37:
                c = Y[4]
            put(x, y, c)


CANDLES = [(184, 42), (189, 37), (194, 44)]  # centre x, top row


def candles():
    for x in range(181, 198):
        put(x, 49, Y[2] if x in (181, 197) else Y[3])
    for cx, top in CANDLES:
        for y in range(top, 49):
            put(cx - 1, y, Y[7])
            put(cx, y, Y[7])
            put(cx + 1, y, Y[6])
        put(cx - 1, top, Y[6])
        put(cx + 1, top, Y[5])
        put(cx + 1, top + 2, Y[7])
        put(cx, top - 1, B[0])


HYD = [B[4], B[6], B[7], B[8], B[10]]


def hydrangea():
    for x in range(199, 210):
        put(x, 43, Y[5])
    for y in range(44, 50):
        inset = (y - 44) // 3
        for x in range(200 + inset, 209 - inset):
            c = Y[3]
            if x == 200 + inset:
                c = Y[4]
            elif x == 208 - inset:
                c = Y[2]
            if y == 46:
                c = B[5]
            put(x, y, c)
    leaf_dark, leaf = "#173a5e", "#235486"
    for (x, y) in [(198, 42), (199, 41), (200, 41), (199, 42), (200, 42), (201, 42)]:
        put(x, y, leaf if y == 41 else leaf_dark)
    for (x, y) in [(210, 42), (209, 41), (210, 41), (208, 42), (209, 42), (211, 41)]:
        put(x, y, leaf if y == 41 else leaf_dark)
    for i, (cx, cy, r) in enumerate([(202, 37.5, 3.2), (207, 37, 3.3), (204.5, 33.5, 3.2)]):
        for (x, y) in puff(cx, cy, r, HYD, 400 + i):
            idx = HYD.index(get(x, y))
            if h01(x, y, 41) > 0.88:
                put(x, y, B[11])
            elif (x + y) % 2 == 0 and idx > 0:
                put(x, y, HYD[idx - 1])


def shoji():
    for y in range(3, 62):
        put(212, y, B[0])
        put(213, y, B[1])
        put(214, y, B[2])
    paper = set()
    for y in range(3, 62):
        for x in range(215, W - RS):
            if x == 215 or y in (3, 61):
                c = B[1]
            elif y >= 53:
                c = B[1] if y == 53 else B[2]
            elif (x - 215) % 6 == 0 or (y - 3) % 8 == 0:
                c = B[2]
            else:
                c = ramp([Y[5], Y[6], Y[7]], 0.85 - 0.4 * (y - 3) / 50, x, y)
                paper.add((x, y))
            put(x, y, c)
            wall_px.discard((x + RS, y))
    # bamboo shadow on the paper
    shade = []
    for y in range(4, 53):
        shade.append((int(round(236 - (y - 4) * 0.06)), y))
    for ny in (14, 27, 41):
        nx = int(round(236 - (ny - 4) * 0.06))
        shade += [(nx - 1, ny + 1), (nx - 2, ny + 2), (nx - 3, ny + 2), (nx - 4, ny + 3), (nx - 5, ny + 3),
                  (nx + 1, ny + 1), (nx + 2, ny + 1), (nx + 3, ny + 2)]
    for (x, y) in shade:
        if (x, y) in paper:
            put(x, y, Y[3])


# ---------------------------------------------------------------- text
CAPS = {  # 5x7 capitals, like the sakura header
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "C": [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": ["###", ".#.", ".#.", ".#.", ".#.", ".#.", "###"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
    ":": [".", ".", "#", ".", ".", "#", "."],
    " ": ["...", "...", "...", "...", "...", "...", "..."],
}
SMALL = {  # compact lower case: 2 rows of ascender, x-height 4, 2 rows of descender
    "a": ["...", "...", ".##", "#.#", "#.#", ".##", "...", "..."],
    "c": ["...", "...", ".##", "#..", "#..", ".##", "...", "..."],
    "g": ["...", "...", ".##", "#.#", "#.#", ".##", "..#", "##."],
    "h": ["#..", "#..", "##.", "#.#", "#.#", "#.#", "...", "..."],
    "i": ["#", ".", "#", "#", "#", "#", ".", "."],
    "l": ["#", "#", "#", "#", "#", "#", ".", "."],
    "m": [".....", ".....", "####.", "#.#.#", "#.#.#", "#.#.#", ".....", "....."],
    "n": ["...", "...", "##.", "#.#", "#.#", "#.#", "...", "..."],
    "o": ["...", "...", ".#.", "#.#", "#.#", ".#.", "...", "..."],
    "p": ["...", "...", "##.", "#.#", "#.#", "##.", "#..", "#.."],
    "r": ["...", "...", "#.#", "##.", "#..", "#..", "...", "..."],
    "z": ["...", "...", "###", "..#", ".#.", "###", "...", "..."],
    ".": [".", ".", ".", ".", ".", "#", ".", "."],
    "@": [".....", ".###.", "#...#", "#.###", "#.#.#", "#.###", "#....", ".###."],
}


def text_width(s, font, gap=1):
    return sum(len(font[ch][0]) + gap for ch in s) - gap


def text(s, x0, y0, font, color, shadow, gap=1):
    lit = set()
    x = x0
    for ch in s:
        g = font[ch]
        for j, row in enumerate(g):
            for i, b in enumerate(row):
                if b == "#":
                    lit.add((x + i, y0 + j))
        x += len(g[0]) + gap
    for (lx, ly) in lit:
        if (lx + 1, ly + 1) not in lit:
            put(lx + 1, ly + 1, shadow)
    for (lx, ly) in lit:
        put(lx, ly, color)


TEXT_X = 127
EMAIL = "nazaniinparmaah@gmail.com"


def title():
    text("CONTACT ME:", TEXT_X, 6, CAPS, B[9], B[0])
    text(EMAIL, TEXT_X, 16, SMALL, Y[5], B[0])


def corners():
    for (x, y) in [(0, 0), (1, 0), (0, 1)]:
        for (fx, fy) in [(x, y), (W - 1 - x, y), (x, H - 1 - y), (W - 1 - x, H - 1 - y)]:
            px[fy][fx] = None


# ---------------------------------------------------------------- animated layer
def rect(x, y, w, h, c, extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{c}"{extra}/>'


def twinkles():
    out = []
    mx, my, mr = MOON
    spots = []
    while len(spots) < 9:
        x, y = rng.randrange(WX - RI + 3, WX + RI - 3), rng.randrange(WY - RI + 3, 28)
        if (x, y) in win and math.hypot(x - mx, y - my) > mr + 4 and math.hypot(x - 108, y - 16) > 5 \
                and all(abs(x - a) + abs(y - b) > 5 for a, b in spots):
            spots.append((x, y))
    for (x, y) in spots:
        delay, dur = -rng.random() * 4, 2.4 + rng.random() * 2.4
        out.append(f'<g class="tw" style="animation-duration:{dur:.1f}s;animation-delay:{delay:.1f}s">'
                   + rect(x, y, 1, 1, B[11])
                   + rect(x - 1, y, 1, 1, B[8]) + rect(x + 1, y, 1, 1, B[8])
                   + rect(x, y - 1, 1, 1, B[8]) + rect(x, y + 1, 1, 1, B[8]) + "</g>")
    return "".join(out)


def fireflies():
    out = []
    spots = [(84, 50), (90, 46), (110, 45), (114, 40), (106, 52), (87, 53), (75, 44)]
    for (x, y) in spots:
        delay, dur = -rng.random() * 4, 2.6 + rng.random() * 2
        out.append(f'<g class="dr" style="animation-delay:{-rng.random() * 5:.1f}s">'
                   f'<g class="ff" style="animation-duration:{dur:.1f}s;animation-delay:{delay:.1f}s">'
                   + rect(x, y, 1, 1, Y[6])
                   + rect(x - 1, y, 1, 1, Y[4], ' opacity=".5"') + rect(x + 1, y, 1, 1, Y[4], ' opacity=".5"')
                   + "</g></g>")
    return "".join(out)


def glow(cx, cy, r0, r1):
    cells = []
    for y in range(int(cy - r1 - 1), int(cy + r1 + 2)):
        for x in range(int(cx - r1 - 1), int(cx + r1 + 2)):
            d = math.hypot(x - cx, (y - cy) * 1.15)
            if r0 < d <= r1 and (x, y) in wall_px and thr(x, y) < (0.4 if d < (r0 + r1) / 2 else 0.16):
                cells.append(rect(x, y, 1, 1, Y[5], ' opacity=".35"'))
    return '<g class="glow">' + "".join(cells) + "</g>"


def flames():
    out = []
    for k, (cx, top) in enumerate(CANDLES):
        a = [(0, -2, Y[7]), (0, -3, Y[6]), (0, -4, Y[4]), (1, -2, Y[5])]
        b = [(0, -2, Y[7]), (0, -3, Y[7]), (-1, -3, Y[5]), (0, -4, Y[5]), (0, -5, Y[4])]
        dur = 0.7 + k * 0.17
        for cls, frame in (("fa", a), ("fb", b)):
            out.append(f'<g class="{cls}" style="animation-duration:{dur:.2f}s">'
                       + "".join(rect(cx + RS + dx, top + dy, 1, 1, c) for dx, dy, c in frame) + "</g>")
    return "".join(out)


NOTE = [".#.", ".##", ".#.", "##.", "##."]


def notes():
    out = []
    for k, (x, y, c) in enumerate([(136, 35, Y[5]), (141, 34, B[9]), (145, 35, Y[6])]):
        cells = "".join(rect(x + RS + i, y + j, 1, 1, c)
                        for j, row in enumerate(NOTE) for i, ch in enumerate(row) if ch == "#")
        out.append(f'<g class="nt" style="animation-delay:{-k * 2}s">{cells}</g>')
    return "".join(out)


def vinyl():
    a = rect(134 + RS, 42, 1, 1, B[3]) + rect(146 + RS, 43, 1, 1, B[3])
    b = rect(137 + RS, 41, 1, 1, B[3]) + rect(143 + RS, 44, 1, 1, B[3])
    return (f'<g class="fa" style="animation-duration:.6s">{a}</g>'
            f'<g class="fb" style="animation-duration:.6s">{b}</g>')


def tail():
    x, y = CAT_X, CAT_Y
    a = [(12, 10), (13, 11), (13, 12), (13, 13), (13, 14), (12, 15), (12, 16)]
    b = [(12, 10), (13, 11), (14, 12), (14, 13), (15, 14), (15, 15), (16, 15)]
    fa = "".join(rect(x + i, y + j, 1, 1, B[0]) for i, j in a)
    fb = "".join(rect(x + i, y + j, 1, 1, B[0]) for i, j in b)
    return (f'<g class="fa" style="animation-duration:2.4s">{fa}</g>'
            f'<g class="fb" style="animation-duration:2.4s">{fb}</g>')


STYLE = """
.tw{animation:tw 4s ease-in-out infinite}
@keyframes tw{0%,100%{opacity:.15}50%{opacity:1}}
.ff{animation:ff 3s ease-in-out infinite}
@keyframes ff{0%,100%{opacity:0}40%,60%{opacity:1}}
.dr{animation:dr 5s ease-in-out infinite alternate}
@keyframes dr{from{transform:translate(0,0)}to{transform:translate(2px,-2px)}}
.glow{animation:glow 3.2s ease-in-out infinite}
@keyframes glow{0%,100%{opacity:.5}45%{opacity:1}70%{opacity:.7}}
.fa{animation:fa 1s steps(1) infinite}
.fb{animation:fb 1s steps(1) infinite}
@keyframes fa{0%,49%{opacity:1}50%,100%{opacity:0}}
@keyframes fb{0%,49%{opacity:0}50%,100%{opacity:1}}
.nt{opacity:0;animation:nt 6s linear infinite}
@keyframes nt{0%{transform:translate(0,0);opacity:0}12%{opacity:1}50%{transform:translate(-2px,-5px)}
75%{opacity:1}100%{transform:translate(-5px,-9px);opacity:0}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}.nt{opacity:1}.fb{opacity:0}}
"""


def to_svg():
    by_color = {}
    for y in range(H):
        x = 0
        while x < W:
            c = px[y][x]
            if c is None:
                x += 1
                continue
            x0 = x
            while x < W and px[y][x] == c:
                x += 1
            by_color.setdefault(c, []).append(f"M{x0} {y}h{x - x0}v1h-{x - x0}z")
    paths = "".join(f'<path fill="{c}" d="{"".join(d)}"/>' for c, d in by_color.items())
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W * 4}" height="{H * 4}" '
        'shape-rendering="crispEdges" role="img" aria-labelledby="t">'
        '<title id="t">Contact me: nazaniinparmaah@gmail.com. A pixel-art Japanese room at night in blue and yellow, '
        "with a cat at a round window, two moons, a cow, books, headphones, a podcast mic, a record player, "
        "candles, hydrangeas, a paper lantern and an easel</title>"
        f"<style>{STYLE.strip()}</style>"
        f"<g>{paths}</g>"
        f"{glow(LCX, LCY, 7.5, 12)}{glow(189 + RS, 38, 5, 11)}"
        f"{twinkles()}{fireflies()}{vinyl()}{flames()}{notes()}{tail()}</svg>\n"
    )


def main():
    wall()
    floor()
    window()
    sky_details()
    landscape()
    animals()
    lantern()
    easel()
    painter_bits()
    zabuton()
    global SHIFT
    SHIFT = RS
    cabinet()
    record_player()
    books()
    mic()
    candles()
    hydrangea()
    shoji()
    SHIFT = 0
    title()
    corners()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(to_svg())
    print(f"wrote {OUT} ({OUT.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
