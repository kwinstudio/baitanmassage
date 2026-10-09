"""Maakt per foto een deelafbeelding van 1200x630 (Open Graph) in static/og/."""
from pathlib import Path
from PIL import Image, ImageOps

root = Path(__file__).resolve().parent.parent
src = root / "assets" / "images"
out = root / "static" / "og"
out.mkdir(parents=True, exist_ok=True)
for f in sorted(src.glob("*.webp")):
    im = Image.open(f).convert("RGB")
    if im.width < 1100 or f.stem.endswith("-mobiel"):  # te klein, of alleen een mobiele uitsnede
        continue
    og = ImageOps.fit(im, (1200, 630), Image.LANCZOS, centering=(0.5, 0.45))
    og.save(out / f"{f.stem}.jpg", "JPEG", quality=84, optimize=True, progressive=True)
    print(f.stem)
