# Submission Form Text (ready to paste)

## Submission Title (max 50 chars)

```
Codebase Autopsy
```
(16 characters — well under the 50 limit, room to add a subtitle if you want, e.g. "Codebase Autopsy: Drift Detector")

## Short Description (summary) — 255 char max, 50 char min

```
Codebase Autopsy uses IBM Bob 2.0 to audit repos for architectural drift, flagging modules whose real behavior no longer matches their declared docstring purpose — before it costs a new hire or reviewer hours to find out the hard way.
```
(232 characters)

## Long Description (what is your idea?) — 100 words min, 600 characters min

```
Codebase Autopsy is a CLI and web tool that audits a Python repository for architectural drift: places where a module's declared purpose (its docstring) has quietly diverged from what the code actually does. A "pure math utility" module that starts writing files. A "logging helper" that starts triggering business logic. Nobody schedules time to notice this — it's usually discovered the hard way, during onboarding or a code review surprise, or worse, a security review that finds an undocumented side effect.

The tool combines two layers. First, plain static analysis: it walks the repo with Python's ast module, builds a module-level dependency graph, and detects real structural issues like import cycles — fast, deterministic, no AI needed. Second, IBM Bob 2.0 reasoning: for every module with a docstring, we call Bob Shell (bob run --format json) with the module's declared purpose plus its actual functions and calls, referencing the real file directly with @path so Bob reasons over genuine repo context. Bob returns a structured verdict — declared purpose, observed behavior, a 0-10 drift score, evidence — used to produce a ranked report, shown live in a web dashboard.

This answers a different question than other repo-intelligence tools. Change-impact analyzers answer "if I change X, what breaks?" Repo visualizers answer "what does this codebase look like?" Codebase Autopsy answers "is this code still honest about what it claims to do, right now, with nothing changed?" It's a continuous integrity check, not a what-if tool or a map — designed to catch silent drift before it costs a new hire's ramp-up time, a reviewer's trust, or a compliance finding. And because only the judgment layer calls Bob at all, it stays cheap to run at scale.
```
(1,779 characters / ~270 words)

## GitHub link

Paste your public repo URL once you've pushed and set visibility to public.

## Additional Information (ready to paste)

```
Live demo: https://<your-app-name>.onrender.com

Note: this is hosted on a free tier, which spins down after inactivity.
If the page or the first analysis takes up to ~60 seconds to respond,
it's just waking back up — not broken. Opening the link once before
judging warms it up.

Two ways to try it:
- "mock mode" (checked by default) runs the full pipeline against
  honest heuristics that read real files, with zero Bobcoin cost —
  safe for anyone to try repeatedly.
- Unchecking it runs real IBM Bob 2.0 calls via Bob Shell (bob run
  --format json), which is what actually powers the drift-scoring
  logic in production use.

Proof of IBM Bob 2.0 usage — both at build time (developing this
project inside Bob IDE) and at runtime (the core drift-analysis
feature itself is a live bob run call) — is in the repo's
bob_sessions/ folder and documented in BOB_USAGE.md.

Tech stack: Python (ast-based static analysis, FastAPI backend),
vanilla JS frontend, IBM Bob 2.0 via Bob Shell, deployed via Docker.

Known limitation: Python/AST-only for now — no multi-language support
yet. See README.md for the full list.
```
