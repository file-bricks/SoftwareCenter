# -*- coding: utf-8 -*-
"""Erzeugt das LaunchBoards-Icon im selben Wappen-Stil wie SoftwareCenter.

Motiv: blaues Wappen-Schild mit fettem, leicht schraegem weissem "LB".
Recycelt die Geometrie/Helfer aus generate_icon.py (gemeinsamer Unterbau),
nur Farbe + Text weichen ab -> konsistente Produktfamilie.

Aufruf:
    PYTHONIOENCODING=utf-8 python generate_icon_launchboards.py
    PYTHONIOENCODING=utf-8 python generate_icon_launchboards.py --preview out.png
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

import generate_icon as gi  # gemeinsame Geometrie/Helfer (Schild, ICO-Export)

HERE = os.path.dirname(os.path.abspath(__file__))
BLUE = (29, 113, 184, 255)   # kraeftiges Blau (Abgrenzung zum SC-Rot)
WHITE = (255, 255, 255, 255)
N = gi.N
TEXT = "LB"


def _draw_lb(canvas, n, font_frac=0.30, y_center=0.40):
    font = ImageFont.truetype(gi.FONT_PATH, int(font_frac * n))
    layer = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    bbox = d.textbbox((0, 0), TEXT, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (n - tw) / 2 - bbox[0]
    ty = (y_center * n) - th / 2 - bbox[1]
    d.text((tx, ty), TEXT, font=font, fill=WHITE)
    shear = -0.16
    layer = layer.transform(
        (n, n), Image.AFFINE, (1, shear, -shear * n * 0.5, 0, 1, 0),
        resample=Image.BICUBIC,
    )
    return Image.alpha_composite(canvas, layer)


def shield_lb():
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    poly = gi._shield_points(N)
    d.polygon(poly, fill=WHITE)
    c = N / 2
    inner = [(c + (x - c) * 0.93, c + (y - c) * 0.93) for (x, y) in poly]
    d.polygon(inner, fill=BLUE)
    return _draw_lb(img, N)


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--preview":
        shield_lb().resize((512, 512), Image.LANCZOS).save(sys.argv[2])
        print("Vorschau:", sys.argv[2])
        return
    master = shield_lb()
    gi._save_ico(master, os.path.join(HERE, "launchboards.ico"))
    gi._save_ico(master, os.path.join(HERE, "LaunchBoardsDesktopIcon.ico"))
    print("LaunchBoards-Icon erzeugt.")


if __name__ == "__main__":
    main()
