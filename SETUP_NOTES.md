# Setup Notes — MrGreenlee Project

**Read this first.** Welcome to a freshly scaffolded project. This file is your orientation guide.

## What this is

A blank-slate scaffold for building **mrgreenlee.com** as a static website hosted on GitHub Pages. The domain is registered through IONOS and owned by Joe.

Scaffolded **2026-05-11** from the `Claude Stuff` project (the 12 Step Design Primer at `C:\Users\smitjj09\Documents\Claude Stuff\`). The Claude Stuff project is untouched — none of its files were modified, only copied or referenced.

## Important first move: get this folder out of `Claude Stuff/`

Right now this folder lives at:
```
C:\Users\smitjj09\Documents\Claude Stuff\MrGreenlee\
```

That was a convenience for scaffolding while we still had the primer project open. **Before you do anything else, move it to its own home.** Recommended:
```
C:\Users\smitjj09\Documents\MrGreenlee\
```

Then open *that* folder as a fresh VS Code workspace (`File → Open Folder…`), open a fresh terminal inside it, and start work from there.

## First-session checklist

After moving the folder and opening it in a new VS Code window:

1. **Create a fresh Python virtual environment** (the primer's `.venv` was not copied — Windows binaries don't transfer cleanly):
   ```powershell
   python -m venv tools\.venv
   .\tools\.venv\Scripts\Activate.ps1
   pip install -r tools\requirements.txt
   ```
2. **Set up your Gemini API key:**
   ```powershell
   copy .env.example .env
   notepad .env
   ```
   Paste your real Gemini API key in place of `your-key-here`. You can reuse the key from the primer project's `.env` (it's a personal Google API key, not project-bound).
3. **Smoke test the figure generator:**
   ```powershell
   python tools\gen_figure.py "A simple line drawing of a vintage Greenlee jointer, three-quarter view, thin black strokes on cream background" --out test-figure.png
   ```
   If `test-figure.png` appears, you're good. Delete it after.
4. **Initialize git:**
   ```powershell
   git init
   git add .
   git commit -m "Initial scaffold for mrgreenlee.com"
   ```
5. **Create the GitHub repo** (suggested name `flylow3d/mrgreenlee-com`, but rename freely):
   ```powershell
   gh repo create flylow3d/mrgreenlee-com --public --source . --remote origin --push
   ```
   (or do it via the GitHub website if you prefer)
6. **Enable GitHub Pages** on the repo: Settings → Pages → Source: `Deploy from a branch` → Branch: `main` / root → Save.
7. **Point IONOS DNS at GitHub Pages.** Log into IONOS, open the DNS settings for `mrgreenlee.com`, and add:
   ```
   A      @     185.199.108.153
   A      @     185.199.109.153
   A      @     185.199.110.153
   A      @     185.199.111.153
   CNAME  www   flylow3d.github.io.
   ```
   (Replace `flylow3d` with your actual GitHub username if you used a different account.)
   
   IONOS may have a "GitHub Pages preset" — even simpler if so. Propagation takes 1–24 hours.
8. **Verify HTTPS issues automatically** after a few minutes. GitHub Pages will provision a Let's Encrypt cert once DNS resolves.

For a fuller reference on the GitHub Pages migration pattern, see `migrate sysdesign to github pathways.md` in the original `Claude Stuff` folder.

## What was copied verbatim from the primer project

| File | Why |
|---|---|
| `tools/gen_figure.py` | Gemini image-generation tool. Already generic — works for any project. |
| `tools/requirements.txt` | Python deps for the figure tool. |
| `tools/README.md` | Setup docs for the figure tool. Conveniently uses "vintage Greenlee jointer" as its smoke-test prompt. |
| `.env.example` | Template for the Gemini API key. |

## What was created fresh for this project

| File | What it is |
|---|---|
| `CLAUDE.md` | Project context for Claude Code. NOT a copy of the primer's CLAUDE.md (which had 15 sessions of slide-specific history). This one is minimal and mrgreenlee-focused. |
| `SETUP_NOTES.md` | This file. Welcome / orientation doc. |
| `README.md` | Skeleton for the GitHub repo's front page. Fill in. |
| `SESSION_LOG.md` | Empty session log, ready for `/log-session` to append entries. |
| `index.html` | Minimal HTML5 starter. Replace with your actual site. |
| `CNAME` | One-liner naming the custom domain for GitHub Pages. |
| `.gitignore` | Whitelist-style ignore tuned for this project (does NOT reference any primer files). |
| `.claude/commands/log-session.md` | Project-scope `/log-session` slash command pointing at THIS project's session log. |
| `Images/.gitkeep` | Zero-byte placeholder so the empty `Images/` folder commits. Delete once you have real images. |

## What was intentionally NOT copied

To avoid contaminating this project with primer-specific cruft:

- The primer's `index.html`, `Images/`, `Tables/`, `hidden-slides.html`, `Joes Build Notes.md`
- The Puppeteer/PDF build chain: `package.json`, `package-lock.json`, `build-pdf.js`, `node_modules/`
- The GitHub Actions PDF auto-build workflow: `.github/workflows/build-pdf.yml`
- All the `_restructure_*.py`, `_hide_*.py`, `_apply_edits.py`, `_md_to_docx.py` etc. one-off scripts from past sessions
- All paper-review artifacts (`ICAD Paper Review/`, response letters, etc.)
- The `sysdesign.html` rebuild (different project entirely)
- The primer's `.env` file (contains the real API key — copy the key value to your new `.env` manually)
- `tools/.venv/` (Windows-binary-heavy; recreate fresh)
- `CLAUDE.md`, `SESSION_LOG.md`, `MEMORY.md` from the primer project

## Things to verify before relying on this

- [ ] Python venv installs cleanly and the figure-generator smoke test succeeds
- [ ] `.env` contains a real Gemini API key
- [ ] `git init` and first commit succeed
- [ ] GitHub repo is created and `git push -u origin main` works
- [ ] CNAME file's domain matches what you set up in IONOS DNS
- [ ] Once DNS propagates, `https://mrgreenlee.com` resolves to the new site

## Open questions / decisions for later

1. **Slide-deck infrastructure** — the primer uses Puppeteer + GitHub Actions to auto-build a selectable-text PDF from `index.html`. Not included here by default (adds ~100 MB of `node_modules`). Add later if you want PDF builds.
2. **GitHub repo ownership** — `flylow3d/mrgreenlee-com` suggested, but if this is a personal site you may want a different account or repo name.
3. **Site content** — `index.html` is a one-line placeholder. The actual site design and content is the next thing to author.
4. **`primer.sysdesign.org` linkage** — unrelated to this project, but flagged in case it's relevant: the primer site can be CNAME'd as a subdomain of sysdesign.org once that's set up.

## Auto-memory note

When you open this folder as a new VS Code workspace, Claude Code will derive a new memory location keyed to this folder's path. The memories from the primer project (PS-ALT pluralization rule, "drive through multi-step batches" preference, etc.) **won't carry over automatically** — they were keyed to the `Claude Stuff` folder path.

That's fine. The general-purpose feedback memories (like "drive through multi-step batches") are worth re-establishing in this project once they come up naturally. The primer-specific ones (PS-ALT, citation labels) don't apply here.
