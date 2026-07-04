#!/usr/bin/env python3
"""
crop_engravings.py — Trim Gemini engraving plates for the web.

The raw generations in `Images/engraving-*.png` include paper-edge
artifacts (drop shadows, letterbox tone bands). This crops each to its
clean interior and writes optimized JPEGs into `Images/web/`.

Crop boxes are hand-tuned per generation — re-tune if an engraving is
regenerated. Run from the project root:

    py tools\\crop_engravings.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "Images"
OUT = IMG / "web"

# (source, output, crop box L/T/R/B or None, max width)
JOBS = [
    # factory works: trim shadowed paper edge, keep full plate
    ("engraving-works.png", "engraving-works.jpg", (34, 34, 990, 990), 1400),
    # factory works: wide band for the home-page hero plate
    ("engraving-works.png", "engraving-works-wide.jpg", (34, 258, 990, 756), 1400),
    # workshop barn: drop the letterbox tone bands top & bottom
    ("engraving-workshop.png", "engraving-workshop.jpg", (0, 228, 1024, 804), 1400),
    # planing mill: symmetric band around the building
    ("engraving-planing-mill.png", "engraving-planing-mill.jpg", (0, 224, 1024, 800), 1400),
    # band saw vignette: already clean and wide
    ("engraving-bandsaw.png", "engraving-bandsaw.jpg", None, 1400),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for src_name, out_name, box, max_w in JOBS:
        src = IMG / src_name
        if not src.exists():
            print(f"  SKIP (missing): {src_name}")
            continue
        im = Image.open(src).convert("RGB")
        if box:
            im = im.crop(box)
        if im.width > max_w:
            im = im.resize((max_w, round(im.height * max_w / im.width)),
                           Image.LANCZOS)
        out = OUT / out_name
        im.save(out, "JPEG", quality=86, optimize=True, progressive=True)
        print(f"  {out.relative_to(ROOT)}  {im.size[0]}x{im.size[1]}  "
              f"{out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
