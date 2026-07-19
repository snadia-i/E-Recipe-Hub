# E-Recipe Hub — Vercel Version

A Vercel-ready Flask version of E-Recipe Hub that preserves the original UI.

## Attribution

This project was originally developed by @saraemyg, @NisaaaNabilah, @syahafiza, and i, and imported from https://github.com/saraemyg/E-Recipe-Hub-Web-Application.

This version was adapted by me for Vercel deployment, PostgreSQL, Vercel Blob,
backend restructuring, and security improvements.

## Local run

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python run.py
```

Open `http://127.0.0.1:5000`.

## Online architecture

- **Vercel Python Function:** Flask application
- **PostgreSQL:** users, recipes, likes, comments, collections, reports, and notifications
- **Vercel Blob:** new recipe, profile, and header image uploads
- **Vercel public directory:** original CSS, GIFs, images, and other static assets

Read [VERCEL_DEPLOYMENT_GUIDE.md](VERCEL_DEPLOYMENT_GUIDE.md) for the full step-by-step deployment process.
