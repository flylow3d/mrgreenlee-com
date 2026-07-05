# MrGreenlee.com — Project Context

## What We're Building

A static website for **mrgreenlee.com**, hosted on GitHub Pages. Domain registered through IONOS, owned by Joe.

Currently a **blank-slate scaffold** — there's no site content yet. `index.html` is a placeholder. The first work session will be defining what this site is and authoring it.

## Status

Full site built out (17 pages): `index.html` (engraved hero plate, stats band, clickable 1890s–1967 timeline, sepia-to-color archive grid), all 13 `machines/<slug>.html` detail pages (cast-iron nameplate spec panels fed from the Excel directory, unique prose, prev/next ring), `the-workshop.html` (both buildings), `about.html` (Greenlee history + collection principles; personal bio is an HTML comment awaiting Joe), `404.html`. Plus `site.js` (scroll reveals, header shadow — reduced-motion safe), `favicon.svg`/`.png`, OG cards, `robots.txt`, `sitemap.xml`.

Image pipeline: `tools/make_web_images.py` builds `Images/web/` derivatives (800px cards / 1600px heroes from `Images/Front Page/` originals, OG card, transparent-background logo, favicon). `tools/crop_engravings.py` trims the four Gemini engravings (`Images/engraving-*.png` — works, workshop, planing mill, band saw vignette; crop boxes are hand-tuned per generation). Re-run both after changing source images.

QA: `py tools\audit_images.py` (Playwright; needs `playwright` + chromium installed) renders every page desktop + Pixel 7 and fails if any image's rendered box distorts its natural aspect ratio. Run `local` before pushing CSS/layout changes, `live` after the Pages build.

Photo pipeline (`tools/process_photos.py`) live and tested on No. 410 (12 photos classified, awaiting `--commit`).

**Deployed:** live at https://mrgreenlee.com (repo `flylow3d/mrgreenlee-com`, GitHub Pages from `main` root, HTTPS enforced). Publish workflow is simply commit → push.

**The Paper Archive:** `archive.html` lists all 53 Greenlee publications mirrored from VintageMachinery.org (with prominent credit + donation link). The PDFs live in a separate repo `flylow3d/greenlee-archive` (local clone at `C:\Users\smitjj09\Documents\greenlee-archive`, 582 MB, served by its own GitHub Pages at flylow3d.github.io/greenlee-archive) — do NOT copy them into this repo. Metadata: `greenlee_pubs.json` in that repo. Machine pages' "From the Catalog" sections use crops in `Images/catalog/` from publication 31151.

**Privacy rule:** raw phone photos carry GPS EXIF. `Images/Front Page/`, `Images/*/_incoming/`, `_originals/` are gitignored — the site serves only the EXIF-stripped derivatives in `Images/web/`. Never loosen those ignore rules. (History note: the originals were public on the repo 2026-05-16 → 2026-07-04; branch history was rewritten to remove them, but GitHub may retain orphaned commits until Support purges them.)

**Open items:**
- Optional: ask GitHub Support to purge the orphaned pre-rewrite commits (`a782307`, `095013b`) that contained GPS photos.
- Commit the No. 410 band saw test batch (`--commit`) and pick its `hero.jpg`; wire real galleries into the machine pages' `gallery-empty` placeholders.
- Process Google Photos albums for the other 12 machines + Workshop + Planing Mill.
- Joe: personal bio for `about.html` (see HTML comment), fact-check machine-page prose and building descriptions, decide name/location disclosure.
- Stray file: `Images/Requirements Ledger Tool — Architecture Sketch_v.01.pdf` looks like it belongs to another project (gitignored) — Joe to move/delete.

See `SESSION_LOG.md` for full session history. See `SETUP_NOTES.md` for the original orientation guide.

## File Structure

```
MrGreenlee/
├── index.html              ← the site (currently a placeholder)
├── CNAME                   ← contains "mrgreenlee.com" — tells GitHub Pages the custom domain
├── Images/                 ← image assets
├── tools/                  ← Gemini figure-generation tool (see tools/README.md)
│   ├── gen_figure.py
│   ├── requirements.txt
│   └── README.md
├── .env.example            ← Gemini API key template (copy to .env, fill in)
├── .gitignore              ← whitelist-style; only explicit paths get committed
├── README.md               ← GitHub repo front page
├── SETUP_NOTES.md          ← read this first — explains the scaffold
├── SESSION_LOG.md          ← rolling work log; updated via /log-session
└── .claude/
    └── commands/
        └── log-session.md  ← project-scope slash command
```

## Hosting target

- **Repo:** `flylow3d/mrgreenlee-com` (suggested; not yet created)
- **GitHub Pages:** will serve from `main` branch root
- **DNS:** IONOS A records pointing at `185.199.108.153–111` (the GitHub Pages IP block)
- **Domain:** `mrgreenlee.com` (and `www.mrgreenlee.com` via CNAME to `<account>.github.io`)

See `SETUP_NOTES.md` for the full DNS / repo setup procedure.

## Publish workflow

Once the repo is set up:

1. Edit files locally in VS Code.
2. `git add` specific paths, `git commit` with a 1–2 sentence message.
3. `git push` to `main`.
4. GitHub Pages rebuilds the site automatically. Live within ~30 seconds.

No CI / no PDF build (unlike the primer). Plain static site.

# Figure generation workflow

We can co-create figures using Google's Gemini image API via `tools/gen_figure.py`. You write the prompt, the script generates the PNG, I embed it in the page.

## When to generate a figure

1. **Read the surrounding HTML first** so the figure fits the context.
2. **Write a detailed prompt.** Include style notes, exact text labels verbatim, composition.
3. **Run the script:**
   ```powershell
   python tools\gen_figure.py "<prompt>" --out Images\<name>.png
   ```
   Add `--pro` for figures with lots of precise text labels (charts, diagrams with callouts) — Nano Banana Pro renders text far more reliably than Flash.
4. **Embed in HTML:** `<img src="Images/<name>.png" alt="<description>">`

## Iterating

Pass the existing PNG as a reference:
```powershell
python tools\gen_figure.py "Same figure but change <thing>" --ref Images\<name>.png --out Images\<name>-v2.png
```

## Conventions

- **Filenames:** lowercase, hyphenated, descriptive — `workshop-bench-overview.png`, not `fig1.png`
- **Output dir:** `Images/`
- **Sidecar files:** the script writes `<name>.png.prompt.txt` next to each PNG containing the prompt + model. Commit these alongside the PNG.
- **Free tier:** ~500 images/day on `gemini-3.1-flash-image-preview`
- **Output is 1024×1024.** For non-square aspect ratios, describe the composition in the prompt and crop in CSS.

## Failure modes

- **Empty response with safety notes:** the model refused. Soften the prompt.
- **Text in the figure looks wrong:** switch to `--pro`.
- **Style drift across figures:** include a one-line style preamble in every prompt and keep it identical site-wide.
