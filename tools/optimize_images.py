#!/usr/bin/env python3
"""Maakt responsive AVIF- en WebP-varianten van de foto's in assets/images.

Gebruik (lokaal, vereist Pillow >= 11 met AVIF):  python3 tools/optimize_images.py
Uitvoer: assets/images/r/<naam>-<breedte>.avif en .webp
build.py gebruikt deze varianten automatisch in <picture>/srcset als ze bestaan;
ontbreken ze (bijv. een nieuwe CMS-upload), dan valt de site terug op het origineel.
"""
from pathlib import Path
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "images"
OUT = SRC / "r"
WIDTHS = [320, 480, 720, 1080, 1440, 1920, 2560]


def main():
    OUT.mkdir(exist_ok=True)
    for f in sorted(SRC.glob("*.webp")):
        im = Image.open(f).convert("RGB")
        for w in WIDTHS:
            if w > im.width:
                continue
            h = round(im.height * w / im.width)
            v = im.resize((w, h), Image.LANCZOS)
            # Verkleinen maakt iets zachter: licht naslijpen, sterker bij kleine varianten
            v = v.filter(ImageFilter.UnsharpMask(radius=0.8 if w >= 1440 else 0.6, percent=55, threshold=2))
            v.save(OUT / f"{f.stem}-{w}.webp", "WEBP", quality=86, method=6)
            v.save(OUT / f"{f.stem}-{w}.avif", "AVIF", quality=70, speed=4)
        print("ok", f.name, im.size)


if __name__ == "__main__":
    main()
