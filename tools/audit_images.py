#!/usr/bin/env python3
"""
audit_images.py — Check every <img> on every page for aspect-ratio distortion.

Renders each page in headless Chromium (desktop 1440px + Pixel 7 emulation)
and flags any image whose rendered box distorts its natural aspect ratio by
more than 3%. Images cropped intentionally (object-fit: cover) are ignored.

This catches the classic responsive-image bug: an <img> with width/height
attributes plus CSS that overrides only the width — without `height: auto`
the attribute height sticks and the image stretches. (Bit us on launch day:
34 distorted renderings across the site.)

Usage (from the project root):
    py tools\\audit_images.py            # audit the local working tree
    py tools\\audit_images.py live       # audit https://mrgreenlee.com

One-time setup:
    py -m pip install playwright
    py -m playwright install chromium

Exit code 0 = clean, 1 = distorted images found. Run `local` before
pushing a CSS change; run `live` after the Pages build to confirm.
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit("Missing dependency. Run: py -m pip install playwright "
             "&& py -m playwright install chromium")

ROOT = Path(__file__).resolve().parent.parent
LIVE = "https://mrgreenlee.com"
TOLERANCE = 0.03

JS = """
() => [...document.images].map(img => {
  const cs = getComputedStyle(img);
  return {
    src: img.currentSrc.split('/').slice(-2).join('/'),
    nw: img.naturalWidth, nh: img.naturalHeight,
    cw: img.clientWidth, ch: img.clientHeight,
    fit: cs.objectFit,
  };
})
"""


def site_pages() -> list[str]:
    """Every page in the site, as paths relative to the root."""
    pages = [p.name for p in sorted(ROOT.glob("*.html"))]
    pages += [f"machines/{p.name}" for p in sorted((ROOT / "machines").glob("*.html"))]
    return pages


def audit(base: str, label: str) -> int:
    bad = 0
    with sync_playwright() as p:
        browser = p.chromium.launch()
        profiles = {
            "desktop": {"viewport": {"width": 1440, "height": 900}},
            "pixel7": p.devices["Pixel 7"],
        }
        for pname, kwargs in profiles.items():
            ctx = browser.new_context(**kwargs)
            page = ctx.new_page()
            for rel in site_pages():
                page.goto(f"{base}/{rel}", wait_until="networkidle")
                for im in page.evaluate(JS):
                    if not im["nw"] or not im["ch"]:
                        continue  # hidden or failed to load
                    natural = im["nw"] / im["nh"]
                    rendered = im["cw"] / im["ch"]
                    if im["fit"] == "fill" and \
                            abs(rendered - natural) / natural > TOLERANCE:
                        bad += 1
                        print(f"  DISTORTED [{pname}] {rel}: {im['src']}  "
                              f"natural {im['nw']}x{im['nh']} ({natural:.2f})  "
                              f"rendered {im['cw']}x{im['ch']} ({rendered:.2f})")
            ctx.close()
        browser.close()
    verdict = f"FAIL — {bad} distorted images" if bad else "PASS — no distorted images"
    print(f"[{label}] {verdict}")
    return bad


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "local"
    base = LIVE if mode == "live" else ROOT.as_uri()
    return 1 if audit(base, mode) else 0


if __name__ == "__main__":
    raise SystemExit(main())
