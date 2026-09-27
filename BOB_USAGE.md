# How IBM Bob 2.0 Was Used

This document is the required written statement on how IBM Bob was used
to build Codebase Autopsy.

## Bob as the reasoning engine inside the product (runtime use)

Codebase Autopsy's core value proposition — judging whether a module's
actual behavior matches its declared purpose — is powered directly by
IBM Bob 2.0 at runtime, via Bob Shell's non-interactive CLI:

```
bob run --format json "<analysis prompt>"
```

For each module, `autopsy/main.py` builds a prompt containing the
module's docstring and a structural summary (functions, classes, calls),
references the real source file with `@path` so Bob reads it directly
from the repo, and asks Bob to return a structured verdict: declared
purpose, observed behavior, a 0–10 drift score, and supporting evidence.
`autopsy/bob_client.py` is the thin wrapper around this call — it
shells out to the real `bob` binary, authenticates with an
Inference-scoped `BOB_API_KEY`, and parses the JSON response.

This is deliberately not a bare snippet-in/snippet-out API call: Bob
Shell is a repo-aware CLI agent, and referencing files with `@path`
lets it reason with real file context rather than a text blob we
constructed ourselves — which is the whole point of using Bob 2.0
specifically, rather than any generic LLM API.

## Bob as a development partner (build-time use)

Bob was also used directly in Bob IDE while building this project itself
— setting up the AST-based ingestion module, the dependency graph and
cycle-detection logic, and the CLI orchestration in `main.py`. Screenshots
of those task sessions are in [`bob_sessions/`](./bob_sessions/), per the
hackathon submission requirements.

## What Bob was NOT used for

Static analysis (parsing files with `ast`, building the dependency
graph, detecting import cycles) is deliberately plain Python with no AI
involved — it's fast, deterministic, and free, and there's no reason to
spend an LLM call on something a parser already does exactly right. Bob
is reserved for the one part of the problem that genuinely needs
judgment: deciding whether behavior matches intent.
