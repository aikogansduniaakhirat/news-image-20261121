#!/usr/bin/env python3
"""Deterministic, offline editorial poster. All geometry uses 1024-space."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

S = 3
PAPER = (246, 242, 234)
INK = (20, 18, 16)
ACCENT = (198, 18, 48)
GREY = (108, 104, 97)
OCEAN = (222, 230, 236)
LAND = (206, 193, 167)
COAST = (120, 110, 95)
WHITE = (255, 255, 255)
HERE = Path(__file__).resolve().parent
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'


def font(size, bold=False):
    return ImageFont.truetype(BOLD if bold else FONT, round(size * S))


def width(text, size, bold=False):
    """Measured advance in design pixels, never supersampled pixels."""
    return font(size, bold).getlength(text) / S


def check_line(text, size, limit, bold=False):
    assert width(text, size, bold) <= limit + 0.01, (text, size, limit)


class Canvas:
    def __init__(self, w=1024, h=1024, background=PAPER):
        self.image = Image.new('RGB', (round(w * S), round(h * S)), background)
        self.draw = ImageDraw.Draw(self.image)

    def rect(self, box, fill=None, outline=None, stroke=1):
        self.draw.rectangle(tuple(round(v * S) for v in box), fill=fill,
                            outline=outline, width=round(stroke * S))

    def line(self, points, color, stroke=1):
        self.draw.line([(round(x*S), round(y*S)) for x, y in points],
                       fill=color, width=round(stroke*S), joint='curve')

    def polygon(self, points, fill):
        self.draw.polygon([(round(x*S), round(y*S)) for x, y in points], fill=fill)

    def circle(self, x, y, r, color):
        self.draw.ellipse(tuple(round(v*S) for v in (x-r, y-r, x+r, y+r)), fill=color)

    def text(self, xy, text, size, color=INK, bold=False):
        self.draw.text(tuple(round(v*S) for v in xy), text, font=font(size, bold),
                       fill=color, anchor='lt')

    def centered(self, x, y, text, size, color=WHITE, halo=False):
        f = font(size, True)
        box = self.draw.textbbox((0, 0), text, font=f)
        # A fine dark keyline keeps the white worldwide W legible on pale ocean
        # at 300px without filling the required hollow square.
        self.draw.text((round(x*S)-(box[0]+box[2])/2,
                        round(y*S)-(box[1]+box[3])/2), text, font=f, fill=color,
                       stroke_width=2 if halo else 0, stroke_fill=INK)


def wrap(text, size, limit, bold=False):
    lines = []
    current = ''
    for word in text.split():
        candidate = (current + ' ' + word).strip()
        if current and width(candidate, size, bold) > limit:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    for line in lines:
        check_line(line, size, limit, bold)
    return lines


def shorten(text, size, limit, bold=False):
    if width(text, size, bold) <= limit:
        return text
    original = text
    while text and width(text.rstrip() + '…', size, bold) > limit:
        text = text[:-1]
    result = text.rstrip() + '…'
    print('WARNING: shortened: ' + original + ' -> ' + result)
    check_line(result, size, limit, bold)
    return result


def headline_fit(text):
    for size in range(25, 18, -1):
        if width(text, size, True) <= 894:
            return [text], size
    for size in range(25, 18, -1):
        lines = wrap(text, size, 894, True)
        if len(lines) <= 2:
            return lines, size
    lines = wrap(text, 19, 894, True)
    return [lines[0], shorten(' '.join(lines[1:]), 19, 894, True)], 19


STORIES = [
    ('1', (46.7, 24.7), 'Saudi air defences down three Houthi missiles over Riyadh',
     'Second attack on the capital in days; Houthis warn airlines off the kingdom'),
    ('2', (127.3, 36.5), 'Freight train derails near Sejong, halting Korean rail services',
     'Five cars off the track; Saemaeul and Mugunghwa lines suspended'),
    ('3', (4.4, 50.8), 'UK and EU seal post-Brexit deal on trade, carbon and youth mobility',
     'Brussels summit pledges to rebuild ties a decade after the Leave vote'),
    ('4', (28.0, -26.2), "ANC fights to hold South Africa's key cities after election setback",
     'Party resists local power-sharing with the DA as councils hang on deals'),
    ('5', (-74.0, 40.7), "Mamdani moves to close New York's Rikers Island jail by 2032",
     'Plan replaces the complex with four borough jails and mental health care'),
    ('W', (-30.0, 8.0), 'GTA VI sets a $3.79bn first-day retail record',
     "Rockstar's first new Grand Theft Auto in 13 years tops every launch"),
]
FOOTER = ('Honda recalls 810,000 US cars over Takata airbags · Waymo recalls robotaxis · '
          'Etsy sellers quit over AI policy · Texas executes Reinaldo Dennes')


def project(lon, lat):
    return (lon + 180) / 360 * 936, (83 - lat) / 141 * 306


def main():
    c = Canvas()
    label = 'WORLD NEWS'
    x = 44
    for ch in label:
        c.text((x, 53), ch, 15, GREY, True)
        x += width(ch, 15, True) + 3
    assert x <= 980

    date = '21 NOVEMBER 2026'
    # Search actual integer font pixels: avoid floating-point steps and use the
    # largest possible date, including its ink bearings, not just its advance.
    for pixel_size in range(100*S, 1, -1):
        size = pixel_size / S
        bounds = font(size, True).getbbox(date, anchor='lt')
        ink_width = (bounds[2] - bounds[0]) / S
        if max(width(date, size, True), ink_width) <= 936:
            break
    check_line(date, size, 936, True)
    # The next 1/3px font step must overflow; the last step can leave a few
    # design pixels because the complete date has many glyphs.
    next_bounds = font(size + 1/S, True).getbbox(date, anchor='lt')
    assert max(width(date, size + 1/S, True),
               (next_bounds[2] - next_bounds[0])/S) > 936
    print(f'Date: {size:.3f}px, width {width(date, size, True):.3f}px')
    c.text((44, 104), date, size, INK, True)
    date_box = font(size, True).getbbox(date, anchor='lt')
    rule_y = 104 + (date_box[3] - date_box[1])/S + 16
    c.rect((44, rule_y, 980, rule_y + 6), ACCENT)
    subtitle = "Saturday's world news in one picture"
    check_line(subtitle, 17, 936)
    c.text((44, rule_y + 20), subtitle, 17, GREY)
    assert rule_y + 42 < 250

    rings = json.loads((HERE / 'land_cache.json').read_text())['rings']
    band = Canvas(936, 306, OCEAN)
    polygons = [[project(lon, lat) for lon, lat in ring] for ring in rings if len(ring) >= 3]
    for points in polygons:
        band.polygon(points, LAND)
    for points in polygons:
        band.line(points + [points[0]], COAST, 2)
    c.image.paste(band.image, (44*S, 250*S))
    c.rect((44, 250, 980, 556), outline=INK, stroke=2)

    for number, coords, _, _ in STORIES:
        px, py = project(*coords)
        x, y = 44 + px, 250 + py
        nx, ny = min(954, max(70, x)), min(530, max(276, y))
        if (nx, ny) != (x, y):
            print('WARNING: nudged map marker ' + number + ' inward')
        x, y = nx, ny
        if number == 'W':
            c.rect((x-11, y-11, x+11, y+11), outline=ACCENT, stroke=3)
            c.centered(x, y, number, 14, halo=True)
        else:
            c.circle(x, y, 13, ACCENT)
            c.centered(x, y, number, 16)

    y = 570
    for number, _, headline, detail in STORIES:
        lines, size = headline_fit(headline)
        line_step = size + 2
        detail_y = y + len(lines)*line_step + 4
        row_height = max(55, len(lines)*line_step + 4 + 15 + 8)
        c.circle(57, y + 13, 13, ACCENT)
        c.centered(57, y + 13, number, 16)
        for i, line in enumerate(lines):
            check_line(line, size, 894, True)
            c.text((86, y+i*line_step), line, size, INK, True)
        c.text((86, detail_y), shorten(detail, 15, 894), 15, GREY)
        print(f'Headline {number}: {size}px, {len(lines)} line(s)')
        y += row_height
    assert y <= 902, f'Legend bottom {y} exceeds 902'

    c.rect((44, 912, 980, 914), INK)
    footer_label = 'ALSO ON 21 NOVEMBER'
    check_line(footer_label, 13, 936, True)
    c.text((44, 929), footer_label, 13, GREY, True)
    footer_lines = wrap(FOOTER, 14, 936)
    if len(footer_lines) > 2:
        footer_lines = [footer_lines[0], shorten(' '.join(footer_lines[1:]), 14, 936)]
    for i, line in enumerate(footer_lines):
        c.text((44, 952+i*20), line, 14, GREY)

    output = c.image.resize((1024, 1024), Image.Resampling.BOX)
    path = HERE / 'entry.png'
    output.save(path, format='PNG', optimize=False, compress_level=9)
    print(f'Output: {path}\nBytes: {path.stat().st_size}\nDimensions: {output.width}x{output.height}\nRings drawn: {len(polygons)}')
    preview = output.resize((300, 300), Image.Resampling.BOX)
    preview = preview.convert('L').resize((80, 40), Image.Resampling.BOX)
    ramp = '@%#*+=-:. '
    print('ASCII preview (300px downscale; dark @ to light space):')
    for row in range(preview.height):
        print(''.join(ramp[min(len(ramp)-1, p * len(ramp) // 256)] for p in
                      [preview.getpixel((col, row)) for col in range(preview.width)]))


if __name__ == '__main__':
    main()
