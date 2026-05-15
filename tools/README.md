# Figure generation setup

Drop these files into your course-content repo:

```
your-repo/
├── tools/
│   ├── gen_figure.py        # the generator
│   └── requirements.txt
├── .env                     # your API key (gitignore this!)
├── .env.example             # template, safe to commit
└── CLAUDE.md                # append the snippet to your existing one
```

## One-time setup

1. **Get a free Gemini API key:** https://aistudio.google.com/apikey
2. **Copy the env template and fill it in:**
   ```bash
   cp .env.example .env
   # then edit .env and paste your key
   ```
3. **Add `.env` to `.gitignore`** if it isn't already.
4. **Install Python deps** (pick one):
   ```bash
   pip install -r tools/requirements.txt
   # or, if you prefer a venv:
   python -m venv .venv && source .venv/bin/activate && pip install -r tools/requirements.txt
   ```
5. **Append `CLAUDE.md.snippet` to your project's `CLAUDE.md`** so Claude Code
   in VS Code knows the workflow without you re-explaining it each session.

## Smoke test

```bash
python tools/gen_figure.py \
    "A simple line drawing of a vintage Greenlee jointer, three-quarter view, thin black strokes on cream background" \
    --out test-figure.png
```

If you get `test-figure.png` plus `test-figure.png.prompt.txt`, you're done.

## How you'll use it day-to-day

Open a slide HTML file in VS Code with Claude Code. Say something like:

> "On slide 4 (the section about fundamental frequencies), let's add a figure
> below the text showing a vibrating string with the first three harmonics
> stacked vertically. Match the style of the figure on slide 2."

Claude will read slide 2 to absorb the style, write a detailed prompt, run
the script, and insert the `<img>` tag. You critique, Claude iterates with
`--ref` against the previous version.

## Models

| Model | API id | Cost | Use when |
|---|---|---|---|
| Nano Banana 2 (default) | `gemini-3.1-flash-image-preview` | Free tier ~500/day | Most figures |
| Nano Banana Pro | `gemini-3-pro-image-preview` | ~$0.13/image | Diagrams with lots of precise text |

Pass `--pro` to switch to Pro for a single call. Set `--model <id>` for any
other model.
