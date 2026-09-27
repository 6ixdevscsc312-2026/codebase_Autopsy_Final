# Deploying Codebase Autopsy Online

## Run it locally first (sanity check before deploying)

```bash
pip install -r requirements.txt
export BOB_API_KEY=your_key_here   # optional — only needed for mock=false
uvicorn autopsy.webapp:app --reload --port 8000
```

Open http://localhost:8000 — you should see the form. Try a GitHub URL
with "mock mode" checked first (uses zero Bobcoins) before trying a real
run.

## Deploy (Docker-based host — Render, Railway, Fly.io, etc.)

The Dockerfile in this repo handles everything, including installing the
real Bob Shell CLI at build time. Steps are basically the same on any of
these platforms:

1. Push this repo to GitHub (public, per the hackathon requirement —
   double check `.gitignore`/`.bobignore` are committed so no secrets
   leak).
2. On your chosen platform, create a new **Web Service** from that repo.
   It should auto-detect the `Dockerfile`.
3. Set an environment variable / secret: `BOB_API_KEY` = your Inference
   key. **Never** put this in the repo itself.
4. Deploy. The platform builds the Docker image (installing Bob Shell in
   the process) and starts the container.
5. Visit the URL the platform gives you — that's your live demo link.

## Protecting your Bobcoin budget once it's public

- The `/api/analyze` endpoint defaults to `mock: true`. Real Bob calls
  only happen if a request explicitly sets `mock: false` — the frontend's
  checkbox controls this, and it's checked by default.
- `max_modules` (default 25, capped at 100) limits how many Bob calls a
  single request can trigger, so one big repo can't burn through the
  whole budget in one shot.
- If you're sharing the live link widely (e.g. in a demo video comment
  section), consider leaving `BOB_API_KEY` unset on the deployed server
  until you're ready to demo live — `/api/health` reports whether a key
  is configured, and real-mode requests are rejected with a clear error
  if it's missing.

## What still only works locally

`bob` CLI installation requires network access at build time, which the
Dockerfile has — but if you're testing in an offline/restricted sandbox
(like the one this project was originally built in), stick to
`mock: true` or the CLI's `--mock` flag.

## Cold starts on Render's free tier

Render's free web service tier spins the container down after a period
of inactivity, and spins it back up on the next request. In practice
this means:

- If nobody's hit the live URL in a while, the **first** request after
  that (loading the page, or the first `/api/analyze` call) can take
  up to roughly a minute to respond while the container restarts —
  it isn't broken, it's just cold.
- Once it's warm, everything responds normally until it goes idle
  again.
- The landing page itself now shows a note about this next to the
  "Analyze" button, so visitors aren't left wondering if it's stuck.

**Before a live demo or judging session**: open the URL yourself a
minute or two beforehand so it's already warm when anyone else visits.
If you want to avoid this entirely, upgrading off the free tier (or
using a host without this behavior) removes the cold-start delay —
not necessary for a hackathon demo, just worth knowing about.
