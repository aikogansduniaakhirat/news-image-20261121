#!/usr/bin/env python3
"""Measure the existing poster; run from the repository root. Never renders it."""
import math
import sys
from itertools import combinations
from pathlib import Path

from PIL import Image

sys.path.insert(0, "art")
import render as R


MAP = (44, 250, 980, 556)  # Half-open page-space box.
TOLERANCE = 18


def near(colour, target, tolerance):
    return all(abs(colour[i] - target[i]) <= tolerance for i in range(3))


def ink_share(image, box, step=1):
    if not isinstance(step, int) or step < 1:
        raise ValueError('Ink sampling step must be a positive integer')
    left, top, right, bottom = box
    dark = total = 0
    pixels = image.load()
    for y in range(top, bottom, step):
        for x in range(left, right, step):
            dark += sum(pixels[x, y]) < 560
            total += 1
    return dark / total if total else 0.0


def surface(colour):
    if near(colour, R.LAND, TOLERANCE) or near(colour, R.COAST, TOLERANCE):
        return "land"
    if near(colour, R.OCEAN, TOLERANCE):
        return "ocean"
    return None


def page_point(lon, lat):
    x, y = R.project(lon, lat)
    return x + MAP[0], y + MAP[1]


def main():
    failures = []

    def check(label, measured, allowed, passed):
        print(f'{label}: {measured}; allowed {allowed} [{"PASS" if passed else "FAIL"}]')
        if not passed:
            failures.append(f'{label}: {measured}; expected {allowed}')

    try:
        with Image.open(Path("art/entry.png")) as source:
            source_format = source.format
            image = source.convert("RGB")
    except (OSError, ValueError) as exc:
        print(f'Image load: {exc}; allowed readable PNG [FAIL]')
        print('FAIL (1)\n- Could not read art/entry.png')
        return 1

    check('Image format', source_format, 'PNG', source_format == 'PNG')
    check('Image size', f'{image.width}x{image.height}', '1024x1024',
          image.size == (1024, 1024))
    density = ink_share(image, (0, 0, image.width, image.height), step=2)
    check('Page ink density (RGB sum < 560)', f'{density:.6f}', '[0.03, 0.55]',
          0.03 <= density <= 0.55)

    # Keep reporting failures for malformed sizes without ever sampling off-image.
    if image.width < MAP[2] or image.height < 992:
        check('Measurement coverage', f'{image.width}x{image.height}',
              'width >= 980 and height >= 992', False)
    else:
        left, top, right, bottom = MAP
        edge = set()
        for inset in (3, 4, 5):
            edge.update((x, y) for x in range(left + inset, right - inset)
                        for y in (top + inset, bottom - 1 - inset))
            edge.update((x, y) for y in range(top + inset, bottom - inset)
                        for x in (left + inset, right - 1 - inset))
        filled = sum(not near(image.getpixel(p), R.PAPER, 12) for p in edge) / len(edge)
        check('Map frame fill (3–5px inside)', f'{filled:.6f}', '[0.985, 1.0]',
              filled >= 0.985)

        counts = {'land': 0, 'ocean': 0, None: 0}
        for y in range(top + 6, bottom - 6, 3):
            for x in range(left + 6, right - 6, 3):
                counts[surface(image.getpixel((x, y))) ] += 1
        classified = counts['land'] + counts['ocean']
        land_share = counts['land'] / classified if classified else 0.0
        check('Map land share', f'{land_share:.6f} ({classified} classified, '
              f'{counts[None]} unclassified)', '[0.15, 0.55]', 0.15 <= land_share <= 0.55)

        centres = []
        for number, coords, _, _ in R.STORIES:
            x, y = page_point(*coords)
            centres.append((number, x, y))
            margin = min(x - left, right - x, y - top, bottom - y)
            check(f'Marker {number} frame margin', f'{margin:.3f}px', '[16, infinity)px',
                  margin >= 16)
            cx, cy = round(x), round(y)
            accent = sum(near(image.getpixel((px, py)), R.ACCENT, TOLERANCE)
                         for py in range(max(0, cy - 18), min(image.height, cy + 19))
                         for px in range(max(0, cx - 18), min(image.width, cx + 19)))
            check(f'Marker {number} accent pixels (18px box radius)', accent,
                  '[80, infinity)', accent >= 80)
        pairs = [(math.hypot(ax - bx, ay - by), a, b)
                 for (a, ax, ay), (b, bx, by) in combinations(centres, 2)]
        if pairs:
            distance, a, b = min(pairs)
            check(f'Closest markers ({a}, {b})', f'{distance:.3f}px', '[34, infinity)px',
                  distance >= 34)
        else:
            check('Marker separation', 'no pairs', '>= 34px for every pair', True)

        for label, box, minimum in (
            ('Date band', (44, 104, 980, 180), 0.12),
            ('Legend band', (44, 570, 980, 900), 0.10),
            ('Footer band', (44, 929, 980, 992), 0.025),
        ):
            share = ink_share(image, box)
            check(label + ' ink share', f'{share:.6f}', f'[{minimum}, 1.0]', share >= minimum)
        # Half-open y interval ends at 910, two pixels before the footer rule.
        gap = ink_share(image, (44, 900, 980, 910))
        check('Legend/footer gap ink share (y=900..909)', f'{gap:.6f}', '[0, 0]', gap == 0)

        locations = (
            ('Berlin', 13.4, 52.5, 'land'),
            ('Kansas', -98.0, 38.5, 'land'),
            ('Sahara', 15.0, 23.0, 'land'),
            ('Siberia', 100.0, 60.0, 'land'),
            ('Alice Springs', 133.88, -23.7, 'land'),
            ('Congo', 23.0, -2.0, 'land'),
            ('Brazil', -52.0, -12.0, 'land'),
            ('Atlantic', -35.0, 30.0, 'ocean'),
            ('Pacific', -140.0, 0.0, 'ocean'),
            ('Indian Ocean', 80.0, -25.0, 'ocean'),
            ('Bay of Bengal', 88.0, 14.0, 'ocean'),
        )
        for name, lon, lat, expected in locations:
            x, y = (round(v) for v in page_point(lon, lat))
            inside = (left <= x - 2 and x + 2 < right
                      and top <= y - 2 and y + 2 < bottom)
            if not inside:
                check(f'Geography {name} ({expected})',
                      f'centre ({x}, {y}), neighbourhood outside map',
                      'entire 5x5 neighbourhood inside map; [13, 25] votes', False)
                continue
            votes = sum(surface(image.getpixel((px, py))) == expected
                        for py in range(y - 2, y + 3) for px in range(x - 2, x + 3))
            check(f'Geography {name} ({expected})', f'{votes}/25 votes', '[13, 25] votes',
                  votes >= 13)

    preview = image.resize((300, 300), Image.Resampling.BOX)
    low, high = preview.convert('L').getextrema()
    contrast = high - low
    reference = max(R.PAPER[i] - R.INK[i] for i in range(3))
    check(f'300px luminance contrast (palette channel span {reference})', contrast,
          '[150, 255]', contrast >= 150)
    share = ink_share(preview, (0, 0, 300, 300))
    check('300px ink share', f'{share:.6f}', '[0.02, 1.0]', share >= 0.02)

    if failures:
        print(f'FAIL ({len(failures)})')
        for failure in failures:
            print('- ' + failure)
        return 1
    print('ALL CHECKS PASSED')
    return 0


if __name__ == '__main__':
    sys.exit(main())
