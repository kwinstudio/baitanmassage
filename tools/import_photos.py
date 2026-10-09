#!/usr/bin/env python3
"""Zet gegenereerde foto's (Higgsfield PNG's) om naar de bronbestanden van de site.

Gebruik:  python3 tools/import_photos.py <map-met-bestanden>

Bestanden worden herkend aan het Higgsfield job-id in de naam (png, webp of jpg).
Een bestand "<job-id>-mobiel.*" wordt gebruikt als kant-en-klare mobiele uitsnede.

- Bewaart een visueel verliesvrije kopie van elk origineel in media/originals/
  (wordt niet gepubliceerd; alleen assets/ gaat naar de site).
- Schrijft de master voor de site naar assets/images/<naam>.webp.
- Maakt voor de hero een aparte mobiele uitsnede (4:5) als <naam>-mobiel.webp.
Draai daarna tools/optimize_images.py en tools/og_images.py.
"""
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ORIG = ROOT / "media" / "originals"
IMG = ROOT / "assets" / "images"

# Higgsfield job-id -> (bestandsnaam op de site, maximale breedte van de master)
PHOTOS = {
    "3f3892fe-1f62-418e-8535-2c20549d98d5": ("thaise-massage-capelle-aan-den-ijssel", 2560),
    "913c05d7-9148-4fb2-bdd2-42b950f95893": ("thaise-oliemassage-rug", 2528),
    "0a9fa0b7-3e4e-46a5-adcb-80ddef509fff": ("aromatherapie-oliemassage", 2528),
    "618e82a5-004b-4fb3-b603-8b764c5e7d9e": ("sportmassage-kuiten", 2528),
    "c5771609-ffb8-4c81-9f2b-1a689dfaed26": ("hot-stone-massage-warme-stenen", 2528),
    "b8433295-8607-4600-ade6-d8f93757e027": ("duo-massage-twee-behandeltafels", 2528),
    "00af9f91-17d8-42e1-a6de-e4dd2f4d289c": ("body-scrub-massage-rug", 2528),
    "83371462-9b8c-469b-992f-c94921bdcee0": ("massage-schouders-aandacht", 2528),
    "39863d39-78fe-4c9c-9c9e-2792672ca681": ("thaise-massage-handpalmdruk", 2560),
    "225e2a13-44f1-481f-8285-25cce9b785d3": ("schoudermassage-ontspannen", 2496),
}
# Mobiele uitsnede van de hero: 4:5, horizontaal gecentreerd op de behandelende handen
HERO = "thaise-massage-capelle-aan-den-ijssel"
HERO_MOBILE_CENTER_X = 0.60


def main(src_dir):
    src_dir = Path(src_dir)
    ORIG.mkdir(parents=True, exist_ok=True)
    found = 0
    for job, (name, max_w) in PHOTOS.items():
        files = [f for f in src_dir.rglob(f"*{job}*") if f.suffix.lower() in (".png", ".webp", ".jpg") and "-mobiel" not in f.stem]
        if not files:
            print("ontbreekt:", job, name)
            continue
        found += 1
        im = Image.open(files[0]).convert("RGB")
        im.save(ORIG / f"{name}.webp", "WEBP", quality=96, method=6)
        w = min(max_w, im.width)
        h = round(im.height * w / im.width)
        im.resize((w, h), Image.LANCZOS).save(IMG / f"{name}.webp", "WEBP", quality=92, method=6)
        print("ok", name, im.size, "->", (w, h))
        ready = [f for f in src_dir.rglob(f"*{job}-mobiel*")]
        if name == HERO and ready:
            Image.open(ready[0]).convert("RGB").save(IMG / f"{name}-mobiel.webp", "WEBP", quality=92, method=6)
            print("ok", f"{name}-mobiel (kant-en-klaar)")
        elif name == HERO:
            cw = round(im.height * 4 / 5)
            x0 = max(0, min(im.width - cw, round(im.width * HERO_MOBILE_CENTER_X - cw / 2)))
            crop = im.crop((x0, 0, x0 + cw, im.height))
            mw = 1440
            crop.resize((mw, round(crop.height * mw / crop.width)), Image.LANCZOS).save(
                IMG / f"{name}-mobiel.webp", "WEBP", quality=92, method=6)
            print("ok", f"{name}-mobiel", crop.size)
    print(f"{found}/{len(PHOTOS)} foto's verwerkt")


if __name__ == "__main__":
    main(sys.argv[1])
