# mrgreenlee.com

Source for the [mrgreenlee.com](https://mrgreenlee.com) website. Static HTML, hosted on GitHub Pages.

## Local preview

Open `index.html` directly in a browser. No build step.

## Image generation

Some figures are generated with Google's Gemini image API via `tools/gen_figure.py`. Setup:

```powershell
python -m venv tools\.venv
.\tools\.venv\Scripts\Activate.ps1
pip install -r tools\requirements.txt
copy .env.example .env
# then paste your Gemini API key into .env
```

See `tools/README.md` for usage.

## Deployment

Pushes to `main` are served by GitHub Pages within ~30 seconds. DNS is managed at IONOS.
