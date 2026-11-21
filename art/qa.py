#!/usr/bin/env python3
"""Pixel QA for the 21 Nov 2026 news poster.

Palette and geometry are imported from the renderer so the checker can never
disagree with what it checks. Run from the repo root:
    python3 art/qa.py
"""
import sys

from PIL import Image

sys.path.insert(0, "art")
import render as R  # noqa: E402

MAP_X, MAP_Y = 44, 250
MAP_W, MAP_H = 936, 306
MAP_BOX = (MAP_X, MAP_Y, MAP_X + MAP_W, MAP_Y + MAP_H)
LEGEND_TOP, LEGEND_BOTTOM = 570, 902
FOOTER_TOP = 912

im = Image.open("art/entry.png").convert("RGB")
W, H = im.size
px = im.load()
fails = []


def near(c, t, tol=26):
    return all(abs(a - b) <= tol for a, b in zip(c, t))


def ink_share(box, step=2):
    x0, y0, x1, y1 = box
    n = tot = 0
    for y in range(y0, y1, step):
        for x in range(x0, x1, step):
            tot += 1
            if sum(px[x, y]) < 560:
                n += 1
    return n / max(1, tot)


def page(lon, lat):
    bx, by = R.project(lon, lat)
    return MAP_X + bx, MAP_Y + by


print("image %dx%d" % (W, H))
if (W, H) != (1024, 1024):
    fails.append("dimensions %dx%d" % (W, H))

d = ink_share((0, 0, W, H))
print("page ink density %.4f  [0.03-0.55]" % d)
if not (0.03 <= d <= 0.55):
    fails.append("page ink density %.3f" % d)

# --- map frame fill: sample just inside the ink frame -----------------------
x0, y0, x1, y1 = MAP_BOX
pts = []
for x in range(x0 + 4, x1 - 4, 7):
    pts.append((x, y0 + 4))
    pts.append((x, y1 - 5))
for y in range(y0 + 4, y1 - 4, 7):
    pts.append((x0 + 4, y))
    pts.append((x1 - 5, y))
paperish = sum(1 for p in pts if near(px[p], R.PAPER, 20))
fill = 1 - paperish / len(pts)
print("map frame fill %.3f  [>=0.985]  (%d paper px of %d)" % (fill, paperish, len(pts)))
if fill < 0.985:
    fails.append("map frame fill %.3f" % fill)

# --- land share -------------------------------------------------------------
land = ocean = 0
for y in range(y0 + 8, y1 - 8, 3):
    for x in range(x0 + 8, x1 - 8, 3):
        c = px[x, y]
        if near(c, R.LAND, 26) or near(c, R.COAST, 45):
            land += 1
        elif near(c, R.OCEAN, 22):
            ocean += 1
tot = land + ocean
share = land / max(1, tot)
print("land share of map %.3f  [0.15-0.55]  (%d land / %d classified)" % (share, land, tot))
if not (0.15 <= share <= 0.55):
    fails.append("land share %.3f" % share)

# --- pins -------------------------------------------------------------------
for number, coords, _, _ in R.STORIES:
    cx, cy = page(*coords)
    n = sum(1 for y in range(int(cy) - 18, int(cy) + 18)
            for x in range(int(cx) - 18, int(cx) + 18)
            if 0 <= x < W and 0 <= y < H and near(px[x, y], R.ACCENT, 45))
    inside = x0 + 16 < cx < x1 - 16 and y0 + 16 < cy < y1 - 16
    print("marker %-2s at (%4.0f,%4.0f) accent px %4d  inside=%s" % (number, cx, cy, n, inside))
    if n < 80:
        fails.append("marker %s only %d accent px" % (number, n))
    if not inside:
        fails.append("marker %s outside map frame" % number)

# --- marker spacing ---------------------------------------------------------
coords = [(n, page(*c)) for n, c, _, _ in R.STORIES]
for i in range(len(coords)):
    for j in range(i + 1, len(coords)):
        (na, (ax, ay)), (nb, (bx, by)) = coords[i], coords[j]
        dist = ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5
        if dist < 34:
            fails.append("markers %s/%s only %.1f px apart" % (na, nb, dist))

# --- band ink ---------------------------------------------------------------
for name, box, lo in (("date", (44, 96, 980, 200), 0.06),
                      ("legend", (44, LEGEND_TOP, 980, LEGEND_BOTTOM), 0.05),
                      ("footer", (44, FOOTER_TOP, 980, 1000), 0.02)):
    s = ink_share(box)
    print("band %-6s ink %.4f  [>=%.2f]" % (name, s, lo))
    if s < lo:
        fails.append("band %s ink %.3f" % (name, s))

# --- no band overlap: legend must end above the footer rule -----------------
# Stop two px short of FOOTER_TOP: the rule itself is drawn at y=912..914 and
# would otherwise register as ink and report a phantom overlap.
strip = (44, LEGEND_BOTTOM - 2, 980, FOOTER_TOP - 2)
if ink_share(strip, 1) > 0.02:
    fails.append("ink between legend bottom and footer rule (overlap)")

# --- 300 px legibility: the judge's reading size ----------------------------
small = im.resize((300, 300), Image.LANCZOS).convert("L")
vals = list(small.getdata())
contrast = max(vals) - min(vals)
ink = sum(1 for v in vals if v < 150) / len(vals)
print("300px contrast %d  [>=150], ink %.4f  [>=0.02]" % (contrast, ink))
if contrast < 150:
    fails.append("300px contrast %d" % contrast)
if ink < 0.02:
    fails.append("300px ink %.3f" % ink)

# --- geography spot check: 5x5 majority, answers not in doubt ---------------
GEO = [("Berlin", 13.4, 52.5, "land"), ("Kansas", -98.0, 38.5, "land"),
       ("Sahara", 10.0, 23.0, "land"), ("Siberia", 100.0, 62.0, "land"),
       ("Alice Springs", 133.8, -23.7, "land"), ("Congo", 22.0, -2.0, "land"),
       ("Brazil", -52.0, -10.0, "land"),
       ("Atlantic", -35.0, 25.0, "ocean"), ("Pacific", -140.0, 0.0, "ocean"),
       ("Indian Ocean", 80.0, -30.0, "ocean"), ("Bay of Bengal", 88.0, 15.0, "ocean")]
for name, lon, lat, want in GEO:
    cx, cy = page(lon, lat)
    votes = {"land": 0, "ocean": 0, "other": 0}
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            x, y = int(cx) + dx, int(cy) + dy
            if not (x0 + 6 < x < x1 - 6 and y0 + 6 < y < y1 - 6):
                votes["other"] += 1
                continue
            c = px[x, y]
            if near(c, R.LAND, 26) or near(c, R.COAST, 45):
                votes["land"] += 1
            elif near(c, R.OCEAN, 22):
                votes["ocean"] += 1
            else:
                votes["other"] += 1
    got = max(("land", "ocean"), key=lambda k: votes[k])
    ok = got == want and votes[got] >= 13
    print("geo %-13s want %-5s got %-5s %s %s" % (name, want, got, votes, "" if ok else "  <-- FAIL"))
    if not ok:
        fails.append("geo %s want %s got %s %s" % (name, want, got, votes))

print()
if fails:
    print("FAIL (%d)" % len(fails))
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("ALL CHECKS PASSED")
