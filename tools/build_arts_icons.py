"""Build the Transformation trait icons and the Heavenly Gate phase icon from the mod's own artwork.

Each Transformation icon starts from its Style's approved trait master (Limitbreaker from the
Cultivator master) and wraps it in the IF's description of the form:
- Limitbreaker: three surging auras layered one over another.
- Reaper: ten swords of chi in a circle behind the wielder.
- Godhand: a halo of kinetic chi over the head.
- Soul Domain: an inner world spilling out around the body.
- Malocchio: eyes become black voids with burning purple irises.
- Titan: the body expands a hundred-fold.
- Asura: a second set of arms rips out (a doubled figure).
The Gate icon is a ring of light breaking open. Writes 120 px trait DDS (as tools/build_trait_icons.py)
and a 205 px activity-phase DDS. Requires Pillow. --check compares without writing.

Usage: python tools/build_arts_icons.py [--check]
"""
from __future__ import annotations

import argparse
import math
import struct
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'assets/trait-icons/source'
TRAITS = ROOT / 'AuraClash/gfx/interface/icons/traits'
PHASES = ROOT / 'AuraClash/gfx/interface/icons/activity_phases'
WORK = 512

# form: (base master, aura colour, mark)
FORMS = {
    'limitbreaker': ('ac_cultivator', (255, 196, 64), 'triple'),
    'reaper': ('ac_style_akakiru', (220, 40, 40), 'blades'),
    'godhand': ('ac_style_aoyusumu', (120, 200, 255), 'halo'),
    'soul_domain': ('ac_style_kiihakai', (255, 220, 120), 'domain'),
    'malocchio': ('ac_style_kurokonton', (170, 60, 230), 'eye'),
    'titan': ('ac_style_midorikatai', (80, 230, 120), 'titan'),
    'asura': ('ac_style_midorikatai', (230, 70, 50), 'asura'),
}


def dds(image: Image.Image, size: int) -> bytes:
    rgba = image.convert('RGBA').resize((size, size), Image.Resampling.LANCZOS)
    header = struct.pack('<4s31I', b'DDS ', 124, 0x100F, size, size, size * 4, 0, 0, *([0] * 11),
                         32, 0x41, 0, 32, 0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000, 0x1000, 0, 0, 0, 0)
    return header + rgba.tobytes('raw', 'BGRA')


def glow(alpha: Image.Image, colour, radius, strength=1.0) -> Image.Image:
    blurred = alpha.filter(ImageFilter.GaussianBlur(radius)).point(lambda v: min(255, int(v * 2.2 * strength)))
    layer = Image.new('RGBA', alpha.size, colour + (0,))
    layer.putalpha(blurred)
    return layer


def ring(colour, radius, width, alpha=210) -> Image.Image:
    layer = Image.new('RGBA', (WORK, WORK), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    c = WORK / 2
    d.ellipse((c - radius, c - radius, c + radius, c + radius), outline=colour + (alpha,), width=width)
    return layer.filter(ImageFilter.GaussianBlur(2))


def transform_icon(form: str) -> Image.Image:
    master, colour, mark = FORMS[form]
    base = Image.open(SOURCE / f'{master}.png').convert('RGBA').resize((WORK, WORK), Image.Resampling.LANCZOS)
    # Shrink the master a little so the aura has room.
    scale = 1.0 if mark == 'titan' else 0.78
    inner = base.resize((int(WORK * scale), int(WORK * scale)), Image.Resampling.LANCZOS)
    figure = Image.new('RGBA', (WORK, WORK), (0, 0, 0, 0))
    off = (WORK - inner.width) // 2
    figure.alpha_composite(inner, (off, off))
    canvas = Image.new('RGBA', (WORK, WORK), (0, 0, 0, 0))
    alpha = figure.getchannel('A')
    if mark == 'triple':
        for radius, strength in ((34, 0.7), (22, 0.9), (12, 1.1)):
            canvas.alpha_composite(glow(alpha, colour, radius, strength))
    elif mark == 'blades':
        layer = Image.new('RGBA', (WORK, WORK), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        c = WORK / 2
        for i in range(10):
            a = 2 * math.pi * i / 10
            inner_r, outer_r = WORK * 0.36, WORK * 0.49
            p = [(c + math.cos(a) * inner_r, c + math.sin(a) * inner_r),
                 (c + math.cos(a + 0.06) * outer_r, c + math.sin(a + 0.06) * outer_r),
                 (c + math.cos(a - 0.06) * outer_r, c + math.sin(a - 0.06) * outer_r)]
            d.polygon(p, fill=colour + (230,))
        canvas.alpha_composite(layer.filter(ImageFilter.GaussianBlur(1.5)))
        canvas.alpha_composite(glow(alpha, colour, 16, 0.8))
    elif mark == 'halo':
        layer = Image.new('RGBA', (WORK, WORK), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        d.ellipse((WORK * 0.28, WORK * 0.02, WORK * 0.72, WORK * 0.16), outline=colour + (240,), width=12)
        canvas.alpha_composite(glow(alpha, colour, 18, 0.9))
        figure.alpha_composite(layer.filter(ImageFilter.GaussianBlur(2)))
    elif mark == 'domain':
        canvas.alpha_composite(ring(colour, WORK * 0.47, 14))
        canvas.alpha_composite(ring(colour, WORK * 0.41, 5, 150))
        canvas.alpha_composite(glow(alpha, colour, 20, 0.8))
    elif mark == 'eye':
        layer = Image.new('RGBA', (WORK, WORK), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        c = WORK / 2
        d.ellipse((c - 150, c - 70, c + 150, c + 70), fill=(10, 0, 20, 140), outline=colour + (255,), width=10)
        d.ellipse((c - 52, c - 52, c + 52, c + 52), outline=colour + (255,), width=14)
        d.ellipse((c - 22, c - 22, c + 22, c + 22), fill=(0, 0, 0, 255))
        canvas.alpha_composite(glow(alpha, colour, 18, 0.9))
        figure.alpha_composite(layer.filter(ImageFilter.GaussianBlur(1.5)))
    elif mark == 'titan':
        canvas.alpha_composite(glow(alpha, colour, 26, 1.0))
    elif mark == 'asura':
        ghost = figure.copy()
        ghost = ImageChops.multiply(ghost, Image.new('RGBA', ghost.size, colour + (150,)))
        for dx in (-46, 46):
            shifted = Image.new('RGBA', (WORK, WORK), (0, 0, 0, 0))
            shifted.alpha_composite(ghost, (dx, -10))
            canvas.alpha_composite(shifted)
        canvas.alpha_composite(glow(alpha, colour, 18, 0.9))
    canvas.alpha_composite(figure)
    return canvas


def gate_icon() -> Image.Image:
    size = WORK
    canvas = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    c = size / 2
    for i in range(24):
        a = 2 * math.pi * i / 24
        d.line((c, c, c + math.cos(a) * size * 0.48, c + math.sin(a) * size * 0.48), fill=(255, 230, 150, 120), width=6)
    canvas = canvas.filter(ImageFilter.GaussianBlur(4))
    d = ImageDraw.Draw(canvas)
    for radius, colour, width in ((0.40, (120, 220, 255, 230), 18), (0.30, (255, 240, 190, 240), 12), (0.18, (255, 255, 255, 255), 0)):
        r = size * radius
        if width:
            d.ellipse((c - r, c - r, c + r, c + r), outline=colour, width=width)
        else:
            d.ellipse((c - r, c - r, c + r, c + r), fill=colour)
    return canvas.filter(ImageFilter.GaussianBlur(2))


def render():
    files = {TRAITS / f'ac_tf_{form}.dds': dds(transform_icon(form), 120) for form in FORMS}
    files[PHASES / 'ac_gate_cycling_phase.dds'] = dds(gate_icon(), 205)
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    files = render()
    if args.check:
        stale = [str(p) for p, d in files.items() if not p.exists() or p.read_bytes() != d]
        if stale:
            raise SystemExit('Stale icons: ' + ', '.join(stale))
    else:
        for path, data in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        preview = Image.new('RGBA', (8 * 130, 130), (40, 34, 30, 255))
        for i, form in enumerate(FORMS):
            preview.alpha_composite(transform_icon(form).resize((120, 120), Image.Resampling.LANCZOS), (i * 130 + 5, 5))
        preview.alpha_composite(gate_icon().resize((120, 120), Image.Resampling.LANCZOS), (7 * 130 + 5, 5))
        preview.save(ROOT / 'assets/trait-icons/transformations_preview.png')
    print(f'Icons: {len(files)}.')


if __name__ == '__main__':
    main()
