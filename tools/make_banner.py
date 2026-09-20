# -*- coding: utf-8 -*-
"""Composes assets/banner.png from the app's own icon (generate_icon.py).

Reproduces the banner deterministically from the same shield master used
for icon.ico/DesktopIcon.ico/Store assets, so the banner never drifts from
the actual app icon. Style reference: doc-bricks/PDFtoPDFocr assets/banner.png
(commit 3a5aabb) — plain gradient, icon left, wordmark, one tagline, no pills.

Aufruf:
    PYTHONIOENCODING=utf-8 python tools/make_banner.py

Abhaengigkeit: Pillow (bereits Projekt-Dependency ueber generate_icon.py).
"""
import importlib.util
import math
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "assets", "banner.png")

W, H = 2400, 680
RED_LIGHT = (230, 48, 52)    # brighter tint of the icon's shield red
RED_DARK = (96, 12, 17)      # darker tint, same hue

FONT_TITLE = r"C:\Windows\Fonts\ariblk.ttf"   # same face as the icon's own "SC"
FONT_SUB = r"C:\Windows\Fonts\seguisb.ttf"


def _load_icon_generator():
    spec = importlib.util.spec_from_file_location(
        "generate_icon", os.path.join(ROOT, "generate_icon.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def radial_bg(w, h):
    """Radial gradient: brighter red near the icon (left third), darker at edges."""
    img = Image.new("RGB", (w, h))
    cx, cy = w * 0.22, h * 0.42
    maxd = math.hypot(max(cx, w - cx), max(cy, h - cy))
    px = img.load()
    for y in range(h):
        for x in range(0, w, 2):  # 2px stride, halves render cost, invisible at output size
            d = math.hypot(x - cx, y - cy) / maxd
            t = min(1.0, d) ** 1.15
            c = tuple(int(RED_LIGHT[i] + (RED_DARK[i] - RED_LIGHT[i]) * t) for i in range(3))
            px[x, y] = c
            if x + 1 < w:
                px[x + 1, y] = c
    return img


def paste_with_shadow(bg, icon, x, y):
    shadow = Image.new("RGBA", bg.size, (0, 0, 0, 0))
    alpha = icon.split()[3].point(lambda a: int(a * 0.55))
    silhouette = Image.new("RGBA", icon.size, (0, 0, 0, 255))
    silhouette.putalpha(alpha)
    shadow.paste(silhouette, (x + 14, y + 22), silhouette)
    shadow = shadow.filter(ImageFilter.GaussianBlur(22))
    bg.alpha_composite(shadow)
    bg.alpha_composite(icon, (x, y))


def main():
    icon_gen = _load_icon_generator()
    shield_master = icon_gen.shield_master()  # 4096px vector-quality master, no upscale needed

    bg = radial_bg(W, H).convert("RGBA")

    icon_size = 480
    icon = shield_master.resize((icon_size, icon_size), Image.LANCZOS)
    icon_x, icon_y = 130, (H - icon_size) // 2
    paste_with_shadow(bg, icon, icon_x, icon_y)

    d = ImageDraw.Draw(bg)
    text_x = icon_x + icon_size + 90

    title_font = ImageFont.truetype(FONT_TITLE, 128)
    d.text((text_x, 240), "SoftwareCenter", font=title_font, fill=(255, 255, 255, 255))

    sub_font = ImageFont.truetype(FONT_SUB, 40)
    d.text((text_x, 402), "Organize your software shortcuts",
            font=sub_font, fill=(255, 255, 255, 235))

    bg.convert("RGB").save(OUT, quality=95)
    print("saved", os.path.relpath(OUT, ROOT), bg.size)


if __name__ == "__main__":
    main()
