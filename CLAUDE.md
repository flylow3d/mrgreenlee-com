# MrGreenlee.com — Project Context

## What We're Building

A static website for **mrgreenlee.com**, hosted on GitHub Pages. Domain registered through IONOS, owned by Joe.

Currently a **blank-slate scaffold** — there's no site content yet. `index.html` is a placeholder. The first work session will be defining what this site is and authoring it.

## Status

Home page (`index.html`) and stylesheet (`styles.css`) built in the heritage / industrial museum aesthetic — cream background, serif type, sienna accent. Machine grid populated from the 13-machine `Greenlee Machine Directory.xlsx`. Per-machine and building image folders created under `Images/`. Photo pipeline (`tools/process_photos.py`) live and tested on No. 410 (12 photos classified, awaiting `--commit`).

**Open items:**
- Commit the No. 410 band saw test batch and pick its `hero.jpg`.
- Build `the-workshop.html`, `about.html`, and the first machine detail page (suggested: No. 604 Hauncher & Relisher).
- Process Google Photos albums for the other 12 machines + Workshop + Planing Mill.
- Infra: `git init`, create GitHub repo, point IONOS DNS at GitHub Pages.

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
