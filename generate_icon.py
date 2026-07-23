# -*- coding: utf-8 -*-
"""Erzeugt das SoftwareCenter-Icon im Superman-Wappen-Stil.

Motiv: rotes Wappen-Schild mit fettem, leicht schraegem weissem "SC".
Erzeugt reproduzierbar alle App-, Store- und PWA-Assets aus einem Master.

Aufruf:
    PYTHONIOENCODING=utf-8 python generate_icon.py          # schreibt alle Assets
    PYTHONIOENCODING=utf-8 python generate_icon.py --preview out.png   # nur Vorschau

Abhaengigkeit: Pillow. Font: Arial Black (C:\\Windows\\Fonts\\ariblk.ttf).
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))

SS = 4                              # Supersampling
BASE = 1024
N = BASE * SS

RED = (206, 27, 35, 255)           # Superman-Rot
WHITE = (255, 255, 255, 255)
FONT_PATH = r"C:\Windows\Fonts\ariblk.ttf"


def _quad(p0, p1, p2, steps):
    out = []
    for i in range(steps + 1):
        t = i / steps
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
        out.append((x, y))
    return out


def _cubic(p0, p1, p2, p3, steps):
    out = []
    for i in range(steps + 1):
        t = i / steps
        mt = 1 - t
        x = mt ** 3 * p0[0] + 3 * mt ** 2 * t * p1[0] + 3 * mt * t * t * p2[0] + t ** 3 * p3[0]
        y = mt ** 3 * p0[1] + 3 * mt ** 2 * t * p1[1] + 3 * mt * t * t * p2[1] + t ** 3 * p3[1]
        out.append((x, y))
    return out


def _shield_points(n):
    """Wappen-Schild als Polygonpunkte, normiert auf Kantenlaenge n."""
    def S(x, y):
        return (x * n, y * n)

    tl, tr = (0.13, 0.16), (0.87, 0.16)
    top_ctrl = (0.50, 0.085)
    tip = (0.50, 0.95)
    r_c1, r_c2 = (1.00, 0.33), (0.74, 0.74)
    l_c2, l_c1 = (0.26, 0.74), (0.00, 0.33)

    pts = _quad(tl, top_ctrl, tr, 120)
    pts += _cubic(tr, r_c1, r_c2, tip, 200)[1:]
    pts += _cubic(tip, l_c2, l_c1, tl, 200)[1:]
    return [S(x, y) for (x, y) in pts]


def _draw_sc(canvas, n, font_frac=0.30, y_center=0.40):
    """Rendert ein leicht schraeges weisses 'SC' mittig auf canvas (Kantenlaenge n)."""
    font = ImageFont.truetype(FONT_PATH, int(font_frac * n))
    layer = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    bbox = d.textbbox((0, 0), "SC", font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (n - tw) / 2 - bbox[0]
    ty = (y_center * n) - th / 2 - bbox[1]
    d.text((tx, ty), "SC", font=font, fill=WHITE)
    shear = -0.16
    layer = layer.transform(
        (n, n), Image.AFFINE, (1, shear, -shear * n * 0.5, 0, 1, 0),
        resample=Image.BICUBIC,
    )
    return Image.alpha_composite(canvas, layer)


def shield_master():
    """Transparentes Schild-Master (N x N): weisser Rand, rote Flaeche, weisses SC."""
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    poly = _shield_points(N)
    d.polygon(poly, fill=WHITE)                       # weisser Aussenrand
    c = N / 2
    inner = [(c + (x - c) * 0.93, c + (y - c) * 0.93) for (x, y) in poly]
    d.polygon(inner, fill=RED)                         # rote Innenflaeche
    return _draw_sc(img, N)


def filled_master():
    """Rotes Vollbild-Master (N x N) mit weissem SC — fuer maskable/apple-touch."""
    img = Image.new("RGBA", (N, N), RED)
    return _draw_sc(img, N, font_frac=0.42, y_center=0.50)


def _save_png(master, size, path, canvas=None):
    out = master.resize((size, size), Image.LANCZOS)
    if canvas:  # in groesseren/anders geformten Rahmen zentrieren
        bg = Image.new("RGBA", canvas, (0, 0, 0, 0))
        bg.alpha_composite(out, ((canvas[0] - size) // 2, (canvas[1] - size) // 2))
        out = bg
    out.save(path)
    print("PNG :", os.path.relpath(path, HERE))


def _save_ico(master, path):
    sizes = [256, 128, 64, 48, 32, 16]
    imgs = [master.resize((s, s), Image.LANCZOS) for s in sizes]
    imgs[0].save(path, format="ICO", sizes=[(s, s) for s in sizes], append_images=imgs[1:])
    print("ICO :", os.path.relpath(path, HERE))


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--preview":
        shield_master().resize((512, 512), Image.LANCZOS).save(sys.argv[2])
        print("Vorschau:", sys.argv[2])
        return

    shield = shield_master()
    filled = filled_master()

    # App-Icons
    _save_ico(shield, os.path.join(HERE, "icon.ico"))
    _save_ico(shield, os.path.join(HERE, "DesktopIcon.ico"))

    # Windows-Store-Assets (transparent)
    store = os.path.join(HERE, "store_assets")
    _save_png(shield, 44, os.path.join(store, "Square44x44Logo.png"))
    _save_png(shield, 150, os.path.join(store, "Square150x150Logo.png"))
    _save_png(shield, 310, os.path.join(store, "Square310x310Logo.png"))
    _save_png(shield, 150, os.path.join(store, "Wide310x150Logo.png"), canvas=(310, 150))


if __name__ == "__main__":
    main()
