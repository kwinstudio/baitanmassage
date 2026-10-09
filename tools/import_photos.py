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
    "8fccf07e-f19a-475c-92ec-a8ea8ec914d8": ("thaise-massage-capelle-aan-den-ijssel", 2560),
    "a528365b-114f-4fc0-b079-768f68b6b886": ("thaise-oliemassage-rug", 2528),
    "242215bb-6cde-4f11-8263-6f1142aa6195": ("aromatherapie-oliemassage", 2528),
    "1ec6d5e2-0e0c-4198-804e-6c8310c43b9f": ("sportmassage-kuiten", 2528),
    "73cf05f9-5bda-494d-82d4-f6b55d208220": ("hot-stone-massage-warme-stenen", 2528),
    "5c12f211-8690-443f-b092-d139520c893a": ("duo-massage-twee-behandeltafels", 2528),
    "2c50f980-e28b-43f3-8b73-a970ddcff0ec": ("body-scrub-massage-rug", 2528),
    "d87eb841-c9d3-443a-96f1-70b1c6315bce": ("thaise-begroeting-wai", 2528),
    "851e4e00-dd0d-4837-a614-af354ddce9a5": ("thaise-massage-handpalmdruk", 2528),
    "281f63e1-0d76-48b8-810f-02bd1cc90920": ("massagetafel-thaise-zijde", 2528),
    "eb3a51b2-4c93-4fb7-bc88-2f5c549a534d": ("massagetafel-lotus-handdoek", 2528),
}
# Mobiele uitsnede van de hero: 4:5, horizontaal gecentreerd op de behandelende handen
HERO = "thaise-massage-capelle-aan-den-ijssel"
HERO_MOBILE_CENTER_X = 0.66


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
