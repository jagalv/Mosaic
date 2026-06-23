---
title: Mosaic API
emoji: 📊
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# Mosaic API (Hugging Face Space)

FastAPI backend for [Mosaic](https://github.com/jagalv/mosaic) — grounded, cited
Q&A over SEC filings. This Space runs the API only (Docker SDK); the web app is
hosted separately on Vercel and calls this Space over HTTPS.

This file's YAML frontmatter configures the Space (`sdk: docker`, `app_port:
7860`). The runtime image is built from the `Dockerfile` in this directory.
Configuration (DB URL, secrets, CORS origin, cookie flags) is supplied as Space
**Variables and secrets** — never committed. See the repo's `.env.example` for
the full list of names.
