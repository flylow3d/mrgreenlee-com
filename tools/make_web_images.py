#!/usr/bin/env python3
"""
make_web_images.py — Build web-sized derivatives of the machine photos.

The originals in `Images/Front Page/` are 3–7 MB phone photos. This script
emits optimized JPEGs into `Images/web/`:

    <key>-card.jpg   800 px wide  — home-page grid cards
    <key>-full.jpg   1600 px max  — machine detail page heroes
    og-card.jpg      1200x630     — social share card (composited from logo)
    favicon.png      64x64        — PNG favicon fallback (diamond-G)

Safe to re-run any time; it overwrites the derivatives and never touches
the originals. Run from the project root:

    py tools\\make_web_images.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "Images" / "Front Page"
OUT = ROOT / "Images" / "web"

CREAM = (244, 239, 230)  # #f4efe6
SIENNA = (139, 69, 19)   # #8b4513
INK = (26, 26, 26)       # #1a1a1a

CARD_W = 800
FULL_MAX = 1600
JPEG_OPTS = dict(quality=80, optimize=True, progressive=True)


def load_flat(path: Path) -> Image.Image:
    """Open, apply EXIF rotation, drop alpha onto cream, return RGB."""
    im = Image.open(path)
    im = ImageOps.exif_transpose(im)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        flat = Image.new("RGB", im.size, CREAM)
        flat.paste(im, mask=im.split()[-1])
        return flat
    return im.convert("RGB")


def save_jpeg(im: Image.Image, path: Path) -> None:
    im.save(path, "JPEG", **JPEG_OPTS)  # re-encode drops original EXIF
    print(f"  {path.relative_to(ROOT)}  {im.size[0]}x{im.size[1]}  "
          f"{path.stat().st_size // 1024} KB")


def derive(path: Path) -> None:
    key = path.stem  # "410", "495s", "604", ...
    im = load_flat(path)

    card = im.copy()
    if card.width > CARD_W:
        card = card.resize(
            (CARD_W, round(card.height * CARD_W / card.width)),
            Image.LANCZOS)
    save_jpeg(card, OUT / f"{key}-card.jpg")

    full = im.copy()
    full.thumbnail((FULL_MAX, FULL_MAX), Image.LANCZOS)
    save_jpeg(full, OUT / f"{key}-full.jpg")


def find_font(names: list[str], size: int) -> ImageFont.FreeTypeFont:
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def make_og_card() -> None:
    """1200x630 social card: logo on cream with a tagline and rules."""
    W, H = 1200, 630
    card = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(card)

    logo_path = ROOT / "Images" / "Vintage_Greenlee_Logo_Cream.png"
    if logo_path.exists():
        logo = Image.open(logo_path).convert("RGBA")
        lw = 1000
        lh = round(logo.height * lw / logo.width)
        logo = logo.resize((lw, lh), Image.LANCZOS)
        card.paste(logo, ((W - lw) // 2, 200), logo)

    serif_i = find_font(["georgiai.ttf", "timesi.ttf"], 34)
    serif = find_font(["georgia.ttf", "times.ttf"], 22)

    tag = "A working museum of vintage woodworking machinery"
    tw = draw.textlength(tag, font=serif_i)
    draw.text(((W - tw) / 2, 428), tag, font=serif_i, fill=INK)

    site = "M R G R E E N L E E . C O M"
    sw = draw.textlength(site, font=serif)
    draw.text(((W - sw) / 2, 500), site, font=serif, fill=SIENNA)

    y = 560
    draw.line([(80, y), (W - 80, y)], fill=(184, 173, 149), width=2)

    save_jpeg(card, OUT / "og-card.jpg")


def make_logo_alpha() -> None:
    """Convert the flat-cream logo PNG to black ink on transparency.

    Luminance ramp: fully light pixels (the cream field) go transparent,
    fully dark pixels (the ink) stay opaque, edges fade smoothly.
    """
    src = ROOT / "Images" / "Vintage_Greenlee_Logo_Cream.png"
    if not src.exists():
        print("  SKIP logo (missing source)")
        return
    lum = Image.open(src).convert("L")
    LO, HI = 60, 225  # <=LO fully opaque ink, >=HI fully transparent paper
    alpha = lum.point(
        lambda v: 255 if v <= LO else 0 if v >= HI
        else round(255 * (HI - v) / (HI - LO)))
    out_im = Image.new("RGBA", lum.size, (26, 26, 26, 0))  # ink = near-black
    out_im.putalpha(alpha)
    out = OUT / "greenlee-logo.png"
    out_im.save(out, "PNG", optimize=True)
    print(f"  {out.relative_to(ROOT)}  {out_im.size[0]}x{out_im.size[1]}  "
          f"{out.stat().st_size // 1024} KB")


def make_favicon_png() -> None:
    """64x64 diamond-G on cream, PNG fallback for the SVG favicon."""
    S = 256  # draw large, downscale for smooth edges
    im = Image.new("RGB", (S, S), CREAM)
    d = ImageDraw.Draw(im)
    m = 24
    d.polygon(
        [(S // 2, m), (S - m, S // 2), (S // 2, S - m), (m, S // 2)],
        outline=SIENNA, width=16)
    g_font = find_font(["georgiab.ttf", "timesbd.ttf"], 120)
    bbox = d.textbbox((0, 0), "G", font=g_font)
    gw, gh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(((S - gw) / 2 - bbox[0], (S - gh) / 2 - bbox[1]),
           "G", font=g_font, fill=SIENNA)
    im = im.resize((64, 64), Image.LANCZOS)
    out = ROOT / "favicon.png"
    im.save(out, "PNG", optimize=True)
    print(f"  {out.relative_to(ROOT)}  64x64  {out.stat().st_size} B")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    sources = sorted(
        p for p in SRC.iterdir()
        if p.suffix.lower() in (".jpg", ".jpeg", ".png"))
    print(f"[make_web_images] {len(sources)} source photos -> {OUT.relative_to(ROOT)}")
    for p in sources:
        derive(p)
    make_og_card()
    make_logo_alpha()
    make_favicon_png()
    print("[make_web_images] done")


if __name__ == "__main__":
    main()
