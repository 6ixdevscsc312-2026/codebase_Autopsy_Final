"""
bob_client.py
Thin wrapper around Bob Shell's non-interactive CLI (`bob run --format json`).

Real usage requires:
  1. Bob Shell installed: curl -fsSL https://bob.ibm.com/download/bobshell.sh | bash
  2. BOB_API_KEY env var set to an Inference-scoped key
  3. `bob` on PATH

Docs: https://bob.ibm.com/docs/shell/getting-started/start-bobshell-non-interactive

For local development without the binary (e.g. this sandbox), set
AUTOPSY_MOCK_BOB=1 and BobClient returns a canned-but-plausible response so
the rest of the pipeline (prompt construction -> JSON parsing -> scoring)
can be built and tested end-to-end before the real CLI is wired in.
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass


class BobError(RuntimeError):
    """Raised when a `bob run` invocation fails or returns malformed output."""


@dataclass
class BobResult:
    status: str  # "success" or "error"
    last_message: str
    total_tokens: int | None = None
    session_cost: float | None = None
    raw: dict | None = None


class BobClient:
    def __init__(self, api_key: str | None = None, mock: bool | None = None,
                 max_cost: float = 0.50, max_turns: int = 10,
                 workspace: str | None = None):
        self.api_key = api_key or os.environ.get("BOB_API_KEY")
        # Auto-detect mock mode: explicit flag, explicit env var, or no key/binary present.
        if mock is None:
            mock = bool(os.environ.get("AUTOPSY_MOCK_BOB"))
        self.mock = mock
        self.max_cost = max_cost
        self.max_turns = max_turns
        # The repo directory bob should treat as its workspace root. Without
        # this, a non-interactive `bob run` either operates on the server's
        # own cwd instead of the target repo, or blocks on a trust-confirmation
        # prompt it has no way to answer (--trust below is the other half of
        # that fix).
        self.workspace = workspace

        if not self.mock and not self.api_key:
            raise BobError(
                "BOB_API_KEY is not set. Export it or pass api_key=, "
                "or set AUTOPSY_MOCK_BOB=1 to develop without the real CLI."
            )

    def run(self, prompt: str, file_refs: list[str] | None = None) -> BobResult:
        """Run a single non-interactive Bob prompt and return the parsed result.

        file_refs: paths to reference inline with `@path` syntax so Bob
        pulls real file content into context.
        """
        full_prompt = prompt
        if file_refs:
            refs = " ".join(f"@{p}" for p in file_refs)
            full_prompt = f"{prompt}\n\nFiles: {refs}"

        if self.mock:
            return self._mock_run(full_prompt, file_refs or [])

        return self._real_run(full_prompt)

    # -- real CLI path -----------------------------------------------------

    def _real_run(self, full_prompt: str) -> BobResult:
        cmd = [
            "bob", "run",
            "--format", "json",
            "--max-cost", str(self.max_cost),
            "--max-turns", str(self.max_turns),
            "--accept-license",
            "--trust",
        ]
        if self.workspace:
            cmd += ["--workspace", self.workspace]
        cmd.append(full_prompt)

        env = dict(os.environ)
        if self.api_key:
            env["BOB_API_KEY"] = self.api_key

        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=180, env=env,
                cwd=self.workspace or None,
            )
        except FileNotFoundError as e:
            raise BobError(
                "The `bob` binary was not found on PATH. Install Bob Shell: "
                "curl -fsSL https://bob.ibm.com/download/bobshell.sh | bash"
            ) from e
        except subprocess.TimeoutExpired as e:
            raise BobError("bob run timed out after 180s") from e

        if proc.returncode != 0:
            raise BobError(f"bob run failed (exit {proc.returncode}): {proc.stderr.strip()}")

        try:
            data = json.loads(proc.stdout.strip().splitlines()[-1])
        except (json.JSONDecodeError, IndexError) as e:
            raise BobError(f"Could not parse bob run JSON output: {proc.stdout[:500]}") from e

        stats = data.get("stats", {})
        return BobResult(
            status=data.get("status", "unknown"),
            last_message=data.get("last_message", ""),
            total_tokens=stats.get("total_tokens"),
            session_cost=stats.get("session_costs"),
            raw=data,
        )

    # -- mock path (no network / no binary needed) --------------------------

    def _mock_run(self, full_prompt: str, file_refs: list[str]) -> BobResult:
        """Deterministic canned response so the pipeline is testable offline.
        Actually reads the referenced files (real Bob would too) and applies
        a crude heuristic so downstream scoring logic has something real to
        chew on, rather than faking intelligence from the prompt text alone."""
        source = ""
        for p in file_refs:
            try:
                with open(p, "r", encoding="utf-8") as f:
                    source += f.read()
            except OSError:
                pass

        io_signals = ("open(", "requests.", "socket.", "subprocess.", "print(")
        claims_pure = "no side effect" in source.lower() or "pure" in source.lower()
        has_io = any(sig in source for sig in io_signals)
        drifted = claims_pure and has_io

        if drifted:
            verdict = (
                '{"declared_purpose": "Pure math utility functions with no side effects", '
                '"observed_behavior": "Performs file I/O (writes JSON report) and logging, '
                'contradicting the stated no-side-effects contract", '
                '"drift_score": 8, '
                '"evidence": ["compute_and_save_report writes to disk via open()", '
                '"calls log_event from app.logger"]}'
            )
        else:
            verdict = (
                '{"declared_purpose": "Utility module", "observed_behavior": '
                '"Matches declared purpose", "drift_score": 1, "evidence": []}'
            )
        return BobResult(
            status="success",
            last_message=verdict,
            total_tokens=len(source) // 3 + len(verdict) // 3,
            session_cost=round((len(source) + len(verdict)) / 50000, 4),
            raw={"mock": True},
        )


if __name__ == "__main__":
    client = BobClient(mock=True)
    result = client.run(
        "Analyze this module: does its behavior match its docstring? "
        "Respond as JSON with declared_purpose, observed_behavior, drift_score (0-10), evidence.",
        file_refs=["sample_repo/app/math_utils.py"],
    )
    print(f"status={result.status}")
    print(result.last_message)
