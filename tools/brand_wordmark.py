#!/usr/bin/env python3
"""Snijdt de woordmerk-tekst ("BAITAN / THAI MASSAGE") uit het officiele logo
voor gebruik naast het embleem in de header.

Het logo is lichtgoud; op de lichte header is dat nauwelijks leesbaar. Daarom
wordt het goud iets dieper gemaakt (zelfde letters en verloop, donkerder toon).

Gebruik:  python3 tools/brand_wordmark.py
Schrijft static/logo/baitan-woordmerk-{40,80,120}.webp
"""
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
LOGO = ROOT / "static" / "logo" / "baitan-logo.png"
OUT = ROOT / "static" / "logo"
TEXT_TOP = 590          # onder het embleem begint de tekst (rij ~604)
DEEPEN, GAMMA = 0.72, 1.25
HEIGHTS = (40, 80, 120)


def main():
    im = Image.open(LOGO).convert("RGBA")
    wm = im.crop((0, TEXT_TOP, im.width, im.height))
    wm = wm.crop(wm.getbbox())
    a = np.array(wm).astype(float)
    rgb = (a[:, :, :3] / 255) ** GAMMA * DEEPEN
    a[:, :, :3] = np.clip(rgb * 255, 0, 255)
    wm = Image.fromarray(a.astype("uint8"), "RGBA")
    for h in HEIGHTS:
        w = round(wm.width * h / wm.height)
        wm.resize((w, h), Image.LANCZOS).save(OUT / f"baitan-woordmerk-{h}.webp", "WEBP", quality=92, method=6)
        print("ok", h, (w, h))


if __name__ == "__main__":
    main()
