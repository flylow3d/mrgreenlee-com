#!/usr/bin/env python3
"""
gen_figure.py — Generate course figures via Google's Gemini image models.

Usage:
    # Basic generation
    python tools/gen_figure.py "A clean line diagram of ..." \
        --out slides/figures/topic-01.png

    # Iterate on an existing figure (image-to-image edit)
    python tools/gen_figure.py "Same figure but make the arrows red" \
        --ref slides/figures/topic-01.png \
        --out slides/figures/topic-01-v2.png

    # Use Nano Banana Pro for figures with precise text labels (paid model)
    python tools/gen_figure.py "..." --pro --out slides/figures/topic-02.png

Environment:
    GEMINI_API_KEY    Required. Free key at https://aistudio.google.com/apikey
                      Loaded from a .env file in the project root if present.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

# Optional .env loader — silent if not installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from google import genai
except ImportError:
    sys.exit("Missing dependency. Run: pip install -r tools/requirements.txt")

try:
    from PIL import Image
except ImportError:
    sys.exit("Missing dependency. Run: pip install -r tools/requirements.txt")


# Nano Banana 2 — current default (Feb 2026), free tier ~500 images/day
DEFAULT_MODEL = "gemini-3.1-flash-image-preview"

# Nano Banana Pro — paid, better at rendering precise text in figures
PRO_MODEL = "gemini-3-pro-image-preview"

MAX_RETRIES = 2  # transient 5xx retries


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generate a figure with Gemini and save it as PNG.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("prompt", help="The image prompt. Wrap in quotes.")
    p.add_argument("--out", required=True,
                   help="Output PNG path, e.g. slides/figures/topic-01.png")
    p.add_argument("--ref", action="append", default=[],
                   help="Reference image to iterate from. Repeatable for multi-image fusion.")
    p.add_argument("--model", default=None,
                   help=f"Override model id. Default: {DEFAULT_MODEL}")
    p.add_argument("--pro", action="store_true",
                   help=f"Shortcut for --model {PRO_MODEL} (paid, sharper text).")
    p.add_argument("--no-sidecar", action="store_true",
                   help="Don't write the sidecar .prompt.txt next to the PNG.")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    if not os.environ.get("GEMINI_API_KEY"):
        sys.exit(
            "GEMINI_API_KEY not set. Add it to .env in the project root, "
            "or export it. Get a free key at https://aistudio.google.com/apikey"
        )

    model = args.model or (PRO_MODEL if args.pro else DEFAULT_MODEL)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    contents: list = [args.prompt]
    for ref in args.ref:
        ref_path = Path(ref)
        if not ref_path.exists():
            sys.exit(f"Reference image not found: {ref}")
        contents.append(Image.open(ref_path))

    client = genai.Client()

    print(f"[gen_figure] model={model}  refs={len(args.ref)}  out={out_path}")

    last_err: Exception | None = None
    response = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(model=model, contents=contents)
            break
        except Exception as e:  # noqa: BLE001 — surface any client error
            last_err = e
            if attempt < MAX_RETRIES:
                wait = 2 ** attempt
                print(f"[gen_figure] attempt {attempt + 1} failed: {e}. Retrying in {wait}s...")
                time.sleep(wait)
            else:
                sys.exit(f"[gen_figure] giving up after {MAX_RETRIES + 1} attempts: {last_err}")

    assert response is not None

    saved = False
    notes: list[str] = []
    for part in response.parts:
        if getattr(part, "text", None):
            notes.append(part.text)
        elif getattr(part, "inline_data", None):
            img = part.as_image()
            img.save(out_path)
            saved = True

    if not saved:
        msg = "No image returned by the model."
        if notes:
            msg += " Model said: " + " | ".join(notes)
        sys.exit(msg)

    if not args.no_sidecar:
        sidecar = out_path.with_suffix(out_path.suffix + ".prompt.txt")
        sidecar.write_text(
            f"model: {model}\n"
            f"refs: {args.ref}\n"
            f"prompt:\n{args.prompt}\n"
        )

    print(f"[gen_figure] saved {out_path}")
    if notes:
        print(f"[gen_figure] model notes: {' | '.join(notes)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
