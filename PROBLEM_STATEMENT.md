# Problem & Solution Statement

## Problem

Codebases drift. A module's docstring and folder name describe what it's
*supposed* to do, but over months of quick fixes and feature creep, the
actual behavior quietly diverges — a "pure math utility" module starts
doing file I/O, a "presentation layer" file starts hitting the database
directly, a "just logging" helper triggers business logic. Nobody
schedules time to notice this; it's discovered the hard way, usually by a
new hire trying to understand the code, or a reviewer surprised by a
side effect in a PR that "only touches formatting."

This falls squarely in the developer workflows IBM Bob 2.0 targets —
**onboarding** and **code review** — where too much time and effort go
into rebuilding a mental model of a codebase that nobody wrote down.

## Solution: Codebase Autopsy

Codebase Autopsy is a CLI tool that audits a Python repository for
**architectural drift**: places where declared intent (docstrings) and
observed behavior (actual code) have pulled apart.

It combines two layers of analysis:

1. **Static structural analysis** (no AI): walks the repo with Python's
   `ast` module, builds a module-level dependency graph, and detects real
   issues like import cycles — fast, deterministic, and free.
2. **IBM Bob 2.0 reasoning**: for every module with a docstring, Bob
   (via Bob Shell, `bob run`) is given the module's declared purpose and
   its actual functions/calls, and asked to judge whether the code still
   matches its stated contract. This is where Bob's repo-aware
   understanding does the work a regex or linter can't — judging *intent*
   vs *behavior*, not just syntax.

The output is a ranked **drift report**: which modules have wandered
furthest from what they claim to be, with evidence, so a team can triage
tech debt or brief a new hire on what to actually watch out for — instead
of trusting stale docstrings.

## Why this matters

- **Onboarding**: new developers get an honest map of the codebase
  instead of an aspirational one.
- **Code review**: reviewers can flag "this file no longer does what its
  docstring says" as a real, scored finding instead of a vague hunch.
- **Tech debt triage**: teams can prioritize refactors by drift score
  instead of gut feeling.

## Business value, quantified

A mid-size engineering team onboarding even 10 new hires a year, where
each loses just 3-4 hours untangling stale or misleading module
documentation before becoming productive, is losing 30-40 engineer-hours
a year to this alone — call it $2,250-$6,000/year at a $75-150/hr loaded
cost, for one team, before counting the harder-to-price cost of a
production incident or compliance finding traced back to an
undocumented side effect (a "pure utility" module quietly writing files
or making network calls is exactly the kind of thing that turns into a
security review finding or a SOC2/GDPR data-handling gap). Codebase
Autopsy turns that into a five-minute automated check instead of a
postmortem.

## Why not an existing tool?

Other repo-intelligence tools built on Bob answer different questions:

- **Change-impact analyzers** (e.g. Ripple, a cross-repo impact tool
  built on Bob Shell) answer "if I change X, what breaks elsewhere?" —
  a pre-change simulation, triggered by a proposed edit.
- **Repo visualizers** (e.g. Atlas, a past IBM Bob hackathon
  finalist that renders a repo as a zoomable city map) answer "what
  does this codebase look like?" — a spatial comprehension aid.

Codebase Autopsy answers a third, different question: **"is this code
still honest about what it claims to do, right now — with no change
proposed at all?"** It's a continuous integrity check, not a
what-if simulator or a map. It's the tool that runs on a schedule or in
CI and flags drift before anyone even proposes the change that would
trigger an impact analysis — catching the silent kind of debt neither
a map nor a diff-based impact tool is designed to surface.

It's also deliberately cheap to run at scale: only the layer that needs
judgment (declared vs. observed behavior) calls Bob at all — structural
analysis (parsing, the dependency graph, cycle detection) is free, fast,
local Python. That's a real efficiency difference for any team watching
their Bobcoin/API budget, not just a hackathon constraint.
