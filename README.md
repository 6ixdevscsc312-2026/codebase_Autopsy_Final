# Codebase Autopsy

An architectural-drift auditor built on **IBM Bob 2.0**. Points at a
Python repo and flags modules whose actual behavior no longer matches
their declared purpose (docstrings) — catching the kind of silent
tech debt that normally only surfaces the hard way, during onboarding
or code review.

Built for the [IBM Bob 2.0 Hackathon](https://lablab.ai/ai-hackathons/ibm-bob-2-hackathon)
(lablab.ai, Sept 25–27, 2026).

See [`PROBLEM_STATEMENT.md`](./PROBLEM_STATEMENT.md) for the problem
and solution write-up, and [`BOB_USAGE.md`](./BOB_USAGE.md) for exactly
how IBM Bob 2.0 was used to build and power this project.

## How it works

1. **Ingest** (`autopsy/ingest.py`) — walks the repo, parses every
   `.py` file with Python's `ast` module, extracts imports, functions,
   classes, and docstrings.
2. **Graph** (`autopsy/graph.py`) — builds a module dependency graph,
   detects import cycles, ranks modules by in/out-degree.
3. **Bob analysis** (`autopsy/bob_client.py` + `autopsy/main.py`) —
   for every module with a docstring, asks IBM Bob 2.0 (via Bob Shell's
   `bob run` CLI) to judge declared purpose vs. observed behavior,
   returning a 0–10 drift score with evidence.
4. **Report** — prints a ranked drift report: worst offenders first,
   plus any import cycles found.

## Setup

```bash
# 1. Install Bob Shell (the bob CLI)
curl -fsSL https://bob.ibm.com/download/bobshell.sh | bash

# 2. Set up credentials
cp .env.example .env
# edit .env and paste your Inference-scoped BOB_API_KEY
export BOB_API_KEY="your-key-here"
```

## Usage

```bash
# Real run, against an actual repo, using live Bob 2.0
python3 -m autopsy.main /path/to/some/repo

# Offline / no BOB_API_KEY needed (mock mode) — useful for demos
# or dev without a live Bob Shell install
python3 -m autopsy.main sample_repo --mock
```

Run it against the included `sample_repo/` fixture (which has an
intentional import cycle and a docstring/behavior mismatch baked in)
to see it work out of the box:

```bash
python3 -m autopsy.main sample_repo --mock
```

## Running it online

Codebase Autopsy also runs as a small web app — paste a GitHub URL
instead of needing local clone access, and see results in a browser.
See [`DEPLOY.md`](./DEPLOY.md) for full instructions; the short version:

```bash
pip install -r requirements.txt
uvicorn autopsy.webapp:app --reload --port 8000
```

or deploy the included `Dockerfile` to any container host (Render,
Railway, Fly.io, etc.) with `BOB_API_KEY` set as a secret env var.

The public `/api/analyze` endpoint defaults to mock mode and caps how
many modules one request can send to Bob, so a public demo link can't
accidentally burn through your Bobcoin budget.

**Note on free-tier hosting**: if deployed on Render's (or a similar
platform's) free tier, the service spins down after inactivity and can
take up to ~60s to respond on the first request after being idle. Open
the live link yourself a minute before demoing it so it's warm. See
`DEPLOY.md` for details.

## Project layout

```
autopsy/
  ingest.py      AST-based repo walker -> ModuleInfo per file
  graph.py       Dependency graph, cycle detection
  bob_client.py  Wraps `bob run --format json`, with an honest mock mode
  source.py      Resolves a local path OR a GitHub/GitLab/Bitbucket URL
                 into a local dir (shallow-clones + cleans up remotes)
  main.py        Orchestrates ingest -> graph -> Bob analysis -> report
  webapp.py      FastAPI layer: serves the UI + POST /api/analyze
static/
  index.html     Web UI — repo input, mock toggle, live results
sample_repo/     Small fixture repo with a real import cycle + drift
bob_sessions/    Required: screenshots of Bob task session summaries
tests/           (reserved for test coverage)
Dockerfile       Builds the web app + installs Bob Shell for deployment
DEPLOY.md        Step-by-step deployment instructions
```

## Mock mode — how it's honest

Mock mode does **not** fake intelligence. `bob_client.py`'s mock path
actually reads the file(s) referenced via `@path` in the prompt and
applies a simple, transparent heuristic (does the docstring claim "no
side effects" while the code contains `open(`, `requests.`, etc.) so
the rest of the pipeline — prompt construction, JSON parsing, drift
scoring, reporting — can be built and demoed without a live Bob
install or network access. It exists to validate the pipeline, not to
substitute for real Bob reasoning in the final demo/submission.

## Known limitations (honest, for the demo)

- Python/AST-only for now — no multi-language support.
- Drift detection depends on modules having a docstring to compare
  against; undocumented modules are skipped (arguably themselves a
  finding worth surfacing in a future version).
- Cycle detection is a straightforward DFS — fine for hackathon scale,
  not optimized for huge monorepos.

## Hackathon submission checklist

- [x] Code repository (this repo)
- [x] Written problem and solution statement (`PROBLEM_STATEMENT.md`)
- [x] Written statement on how IBM Bob was used (`BOB_USAGE.md`)
- [x] Security files from the official IBM Hackathon template
      (`.gitignore`, `.bobignore`, `.env.example`) — no credentials
      committed
- [ ] `bob_sessions/` populated with real task session screenshots
      (see `bob_sessions/README.md` for how to capture them)
- [ ] Video demonstration of the solution (≤ 5 min)
- [ ] Repository made publicly accessible
- [ ] Submitted via the Project Submission form on your lablab.ai team
      page (Submission Title, Short Description, Long Description,
      GitHub link)
