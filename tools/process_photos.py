#!/usr/bin/env python3
"""
process_photos.py - Classify and prepare collection photos for the website.

Workflow:
  1. Drop original photos (any size, any format) into Images/<slug>/_incoming/
  2. Run review mode:
         python tools/process_photos.py <slug>
     - Reads EXIF date for each photo
     - Asks Gemini Vision to classify (acq / rep / run) and write a caption
     - Writes Images/<slug>/_classifications.txt  (plain text, editable)
     - Writes Images/<slug>/_review.html          (visual review, open in browser)
  3. If any photo is misclassified, edit _classifications.txt by hand.
     Change the first word on the line to acq, rep, or run.
  4. Run commit mode:
         python tools/process_photos.py <slug> --commit
     - Resizes photos (max 2000 px on the long side)
     - Strips EXIF (privacy — removes GPS, camera serial, etc.)
     - Renames YYYY-MM-DD_HHMM_<stage>.jpg
     - Moves originals into Images/<slug>/_originals/

  Operate on every slug at once with --all instead of <slug>.

Re-running with new photos:
  Drop a fresh full download of the album into _incoming/ (don't worry about
  the previous photos still being in there — Google Photos will hand you the
  full set every time). The script matches by filename against _originals/
  and silently skips anything already processed. On --commit, duplicates are
  deleted from _incoming/ (the originals are safely preserved in _originals/),
  leaving you to classify and commit only the genuinely new photos.

Environment:
    GEMINI_API_KEY    Required. Free key at https://aistudio.google.com/apikey
                      Loaded from .env in project root if present.
"""
from __future__ import annotations

import argparse
import html
import os
import shutil
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

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
    from PIL import Image, ImageOps
    from PIL.ExifTags import TAGS
except ImportError:
    sys.exit("Missing dependency. Run: pip install -r tools/requirements.txt")

# Register HEIC/HEIF support if available (iPhones save HEIC by default)
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass


PROJECT_ROOT  = Path(__file__).resolve().parent.parent
IMAGES_DIR    = PROJECT_ROOT / "Images"
DEFAULT_MODEL = "gemini-2.5-flash"
MAX_DIM       = 2000   # max pixels on the long side of web-sized photos
JPEG_QUALITY  = 85
THUMB_DIM     = 320    # thumbnail size for the review HTML
IMAGE_EXTS    = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp", ".tiff", ".tif"}
STAGES        = {
    "acq": "Acquisition",
    "rep": "Repair / Setup",
    "run": "Ready to Run",
}

CLASSIFY_PROMPT = """You are looking at a photo from a vintage Greenlee woodworking machine collection.
Classify the photo into ONE of three restoration stages and write a short caption.

Stages:
- acq = ACQUISITION. Machine in original found condition. On a trailer, truck, or being unloaded. Dirty, rusted, dusty, in a seller's barn/garage. Pre-restoration condition.
- rep = REPAIR / SETUP. Mid-restoration. Disassembled parts. Workbench shots. Sanding, painting, machining. Cleaning. Bare castings being prepped. Wiring/installation in progress.
- run = READY TO RUN. Final state. Clean, painted, in its final shop location, set up to operate. The "beauty shot" of the restored machine in its home.

Respond in EXACTLY this format, two lines, nothing else:
STAGE: <acq or rep or run>
CAPTION: <short phrase, max 8 words, describing what's happening>
"""


@dataclass
class PhotoRow:
    filename: str
    stage:    str
    when:     datetime | None
    caption:  str


# -------- EXIF + dates --------

def read_exif_datetime(path: Path) -> datetime | None:
    try:
        with Image.open(path) as img:
            exif = img.getexif()
            if not exif:
                return None
            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == "DateTimeOriginal" or tag == "DateTime":
                    try:
                        return datetime.strptime(str(value), "%Y:%m:%d %H:%M:%S")
                    except ValueError:
                        continue
    except Exception:
        pass
    return None


def best_datetime(path: Path) -> datetime | None:
    dt = read_exif_datetime(path)
    if dt:
        return dt
    try:
        return datetime.fromtimestamp(path.stat().st_mtime)
    except Exception:
        return None


# -------- Gemini classification --------

def classify_with_gemini(client, model: str, path: Path) -> tuple[str, str]:
    """Return (stage_code, caption). Defaults to ('acq', '') on parse failure."""
    with Image.open(path) as img:
        img.load()
        rgb = img.convert("RGB")
    response = client.models.generate_content(
        model=model,
        contents=[CLASSIFY_PROMPT, rgb],
    )
    text = (response.text or "").strip()
    stage = "acq"
    caption = ""
    for line in text.splitlines():
        line = line.strip()
        if line.upper().startswith("STAGE:"):
            raw = line.split(":", 1)[1].strip().lower()
            for code in STAGES:
                if raw.startswith(code):
                    stage = code
                    break
        elif line.upper().startswith("CAPTION:"):
            caption = line.split(":", 1)[1].strip()
    return stage, caption


# -------- Classifications file (editable plain text) --------

CLASS_HEADER = """# Photo classifications for {slug}
# Edit the first word on each line to override Gemini's guess.
# Stages: acq (Acquisition) | rep (Repair / Setup) | run (Ready to Run)
#
# stage  filename                            date              caption
"""

def write_classifications(path: Path, slug: str, rows: list[PhotoRow]) -> None:
    rows = sorted(rows, key=lambda r: (r.when or datetime.max, r.filename))
    name_w = max((len(r.filename) for r in rows), default=20)
    name_w = max(name_w, 20) + 2
    lines = [CLASS_HEADER.format(slug=slug)]
    for r in rows:
        when = r.when.strftime("%Y-%m-%d %H:%M") if r.when else "(no date)       "
        lines.append(f"{r.stage:<6} {r.filename:<{name_w}} {when}  {r.caption}\n")
    path.write_text("".join(lines), encoding="utf-8")


def read_classifications(path: Path) -> dict[str, tuple[str, str]]:
    """Return {filename: (stage, caption)} from an existing file."""
    out: dict[str, tuple[str, str]] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        parts = line.split(None, 2)
        if len(parts) < 2:
            continue
        stage, filename = parts[0], parts[1]
        if stage not in STAGES:
            continue
        rest = parts[2] if len(parts) > 2 else ""
        # rest looks like "YYYY-MM-DD HH:MM  caption..."  -- strip date+time, keep caption
        caption = ""
        tokens = rest.split(None, 2)
        if len(tokens) >= 3:
            caption = tokens[2]
        elif rest.strip() and not rest.strip()[0].isdigit():
            caption = rest.strip()
        out[filename] = (stage, caption)
    return out


# -------- Review HTML --------

REVIEW_CSS = """
body { font-family: 'Lora', Georgia, serif; background: #f4efe6; color: #1a1a1a; margin: 0; padding: 40px; }
h1 { font-family: 'Cormorant Garamond', Georgia, serif; font-weight: 500; }
h2 { font-family: 'Cormorant Garamond', Georgia, serif; font-style: italic; font-weight: 500;
     border-bottom: 1px solid #b8ad95; padding-bottom: 6px; margin-top: 40px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 18px; }
.card { background: #ece5d6; border: 1px solid #b8ad95; padding: 10px; font-size: 0.85rem; }
.card img { width: 100%; height: 180px; object-fit: cover; display: block; margin-bottom: 8px; }
.fn { font-family: monospace; font-size: 0.8rem; color: #6b6655; word-break: break-all; }
.cap { font-style: italic; color: #2b2b2b; margin-top: 4px; }
.dt { color: #6b6655; font-size: 0.78rem; }
.note { color: #6b6655; font-size: 0.9rem; max-width: 720px; margin-bottom: 24px; }
.tag { display: inline-block; background: #8b4513; color: #f4efe6; padding: 2px 8px; font-size: 0.7rem;
       letter-spacing: 0.15em; text-transform: uppercase; margin-right: 6px; }
"""

def write_review_html(path: Path, slug: str, rows: list[PhotoRow], incoming: Path) -> None:
    by_stage: dict[str, list[PhotoRow]] = {k: [] for k in STAGES}
    for r in rows:
        by_stage.setdefault(r.stage, []).append(r)
    for stage in by_stage:
        by_stage[stage].sort(key=lambda r: (r.when or datetime.max, r.filename))

    parts = [
        "<!DOCTYPE html><html><head><meta charset='utf-8'>",
        f"<title>Review — {html.escape(slug)}</title>",
        f"<style>{REVIEW_CSS}</style></head><body>",
        f"<h1>Review: {html.escape(slug)}</h1>",
        f"<p class='note'>{len(rows)} photos. Open <code>_classifications.txt</code> "
        "in a text editor and change the stage on any photo you want to override, "
        "then run with <code>--commit</code>.</p>",
    ]
    for stage_code, stage_name in STAGES.items():
        stage_rows = by_stage.get(stage_code, [])
        parts.append(f"<h2>{html.escape(stage_name)} <span class='dt'>({len(stage_rows)})</span></h2>")
        if not stage_rows:
            parts.append("<p class='note' style='font-style:italic'>(none)</p>")
            continue
        parts.append("<div class='grid'>")
        for r in stage_rows:
            rel = (incoming / r.filename).relative_to(path.parent).as_posix()
            when = r.when.strftime("%Y-%m-%d %H:%M") if r.when else "(no date)"
            parts.append(
                f"<div class='card'>"
                f"<img src='{html.escape(rel)}' loading='lazy'>"
                f"<div class='fn'>{html.escape(r.filename)}</div>"
                f"<div class='dt'>{html.escape(when)}</div>"
                f"<div class='cap'>{html.escape(r.caption or '—')}</div>"
                f"</div>"
            )
        parts.append("</div>")
    parts.append("</body></html>")
    path.write_text("".join(parts), encoding="utf-8")


# -------- Commit (resize, strip EXIF, rename, stash original) --------

def safe_filename(when: datetime | None, stage: str, used: set[str]) -> str:
    base = (when.strftime("%Y-%m-%d_%H%M") if when else "undated") + f"_{stage}"
    candidate = f"{base}.jpg"
    n = 2
    while candidate in used:
        candidate = f"{base}-{n}.jpg"
        n += 1
    used.add(candidate)
    return candidate


def commit_one(src: Path, dest_dir: Path, stage: str, when: datetime | None, used: set[str]) -> Path:
    dest_name = safe_filename(when, stage, used)
    dest_path = dest_dir / dest_name

    with Image.open(src) as img:
        img = ImageOps.exif_transpose(img)   # honor rotation, then strip EXIF
        img = img.convert("RGB")
        img.thumbnail((MAX_DIM, MAX_DIM), Image.LANCZOS)
        img.save(dest_path, format="JPEG", quality=JPEG_QUALITY, optimize=True)

    originals_dir = dest_dir / "_originals"
    originals_dir.mkdir(exist_ok=True)
    shutil.move(str(src), str(originals_dir / src.name))
    return dest_path


# -------- Slug discovery --------

def list_image_files(folder: Path) -> list[Path]:
    return sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS)


def already_processed_names(slug_dir: Path) -> set[str]:
    """Lowercased filenames already moved into _originals/ — i.e. previously committed."""
    originals = slug_dir / "_originals"
    if not originals.is_dir():
        return set()
    return {p.name.lower() for p in originals.iterdir() if p.is_file()}


def split_new_vs_dup(photos: list[Path], done: set[str]) -> tuple[list[Path], list[Path]]:
    new, dup = [], []
    for p in photos:
        (dup if p.name.lower() in done else new).append(p)
    return new, dup


def discover_slugs() -> list[str]:
    if not IMAGES_DIR.exists():
        return []
    return sorted(d.name for d in IMAGES_DIR.iterdir()
                  if d.is_dir() and (d / "_incoming").exists())


# -------- The two top-level operations --------

def review_slug(slug: str, model: str, limit: int | None, client) -> None:
    slug_dir = IMAGES_DIR / slug
    incoming = slug_dir / "_incoming"
    if not incoming.is_dir():
        print(f"[{slug}] no _incoming/ folder — skipping")
        return

    all_photos = list_image_files(incoming)
    done = already_processed_names(slug_dir)
    photos, dups = split_new_vs_dup(all_photos, done)
    if dups:
        print(f"[{slug}] {len(dups)} already processed (in _originals/) — will be skipped")
    if limit:
        photos = photos[:limit]
    if not photos:
        if dups:
            print(f"[{slug}] no NEW photos — run --commit to clear duplicates from _incoming/")
        else:
            print(f"[{slug}] no photos in _incoming/ — skipping")
        return

    print(f"[{slug}] reviewing {len(photos)} new photos")

    class_file = slug_dir / "_classifications.txt"
    cached = read_classifications(class_file)

    rows: list[PhotoRow] = []
    for i, photo in enumerate(photos, 1):
        when = best_datetime(photo)
        if photo.name in cached:
            stage, caption = cached[photo.name]
            print(f"  [{i}/{len(photos)}] cached: {photo.name} -> {stage}")
        else:
            try:
                stage, caption = classify_with_gemini(client, model, photo)
                print(f"  [{i}/{len(photos)}] {photo.name} -> {stage}: {caption}")
            except Exception as e:
                print(f"  [{i}/{len(photos)}] {photo.name} -> ERROR: {e}")
                stage, caption = "acq", "(classification failed)"
            time.sleep(0.3)  # gentle pacing for free-tier quotas
        rows.append(PhotoRow(filename=photo.name, stage=stage, when=when, caption=caption))

    write_classifications(class_file, slug, rows)
    review_html = slug_dir / "_review.html"
    write_review_html(review_html, slug, rows, incoming)

    counts = {k: 0 for k in STAGES}
    dates = [r.when for r in rows if r.when]
    for r in rows:
        counts[r.stage] = counts.get(r.stage, 0) + 1
    print(f"[{slug}] summary:")
    if dates:
        print(f"  earliest photo: {min(dates).strftime('%Y-%m-%d')}  (proposed acquisition date)")
        print(f"  latest photo:   {max(dates).strftime('%Y-%m-%d')}")
    for code, name in STAGES.items():
        print(f"  {name}: {counts.get(code, 0)}")
    print(f"  open {review_html} in a browser to review")
    print(f"  edit  {class_file}  to override any classifications")


def commit_slug(slug: str) -> None:
    slug_dir = IMAGES_DIR / slug
    incoming = slug_dir / "_incoming"
    class_file = slug_dir / "_classifications.txt"

    if not incoming.is_dir():
        print(f"[{slug}] no _incoming/ folder — nothing to commit")
        return

    all_photos = list_image_files(incoming)
    if not all_photos:
        print(f"[{slug}] _incoming/ is empty — nothing to commit")
        return

    done_set = already_processed_names(slug_dir)
    photos, dups = split_new_vs_dup(all_photos, done_set)

    # Remove duplicates from _incoming/ — they're safe in _originals/ already
    for d in dups:
        d.unlink()
    if dups:
        print(f"[{slug}] removed {len(dups)} duplicates from _incoming/ (already in _originals/)")

    if not photos:
        print(f"[{slug}] no new photos to commit")
        return

    if not class_file.exists():
        print(f"[{slug}] no _classifications.txt — run review mode first")
        return

    classifications = read_classifications(class_file)
    used = {p.name for p in slug_dir.iterdir() if p.is_file()}
    committed = 0
    unclassified = 0
    for src in photos:
        if src.name not in classifications:
            print(f"  skip (no classification — re-run review): {src.name}")
            unclassified += 1
            continue
        stage, _caption = classifications[src.name]
        when = best_datetime(src)
        dest = commit_one(src, slug_dir, stage, when, used)
        print(f"  committed: {src.name} -> {dest.name}")
        committed += 1

    print(f"[{slug}] committed {committed} new photos. Originals in _originals/.")
    if unclassified:
        print(f"[{slug}] {unclassified} photo(s) were skipped — run review again, then commit.")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Classify and prepare collection photos.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("slug", nargs="?",
                   help="Machine slug (folder name in Images/). Omit if using --all.")
    p.add_argument("--all", action="store_true",
                   help="Operate on every slug that has photos in _incoming/.")
    p.add_argument("--commit", action="store_true",
                   help="Apply the classifications: resize, strip EXIF, rename, move originals.")
    p.add_argument("--model", default=DEFAULT_MODEL,
                   help=f"Gemini model for classification. Default: {DEFAULT_MODEL}")
    p.add_argument("--limit", type=int, default=None,
                   help="Only process the first N photos (handy for testing).")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    if args.all and args.slug:
        sys.exit("Pass either <slug> or --all, not both.")
    if not args.all and not args.slug:
        sys.exit("Pass <slug> (folder name under Images/) or use --all.")

    slugs = discover_slugs() if args.all else [args.slug]
    if not slugs:
        sys.exit("No slugs found. Drop photos into Images/<slug>/_incoming/ first.")

    if not args.commit and not os.environ.get("GEMINI_API_KEY"):
        sys.exit(
            "GEMINI_API_KEY not set. Add it to .env in the project root, "
            "or export it. Get a free key at https://aistudio.google.com/apikey"
        )

    client = None if args.commit else genai.Client()

    for slug in slugs:
        if args.commit:
            commit_slug(slug)
        else:
            review_slug(slug, args.model, args.limit, client)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
