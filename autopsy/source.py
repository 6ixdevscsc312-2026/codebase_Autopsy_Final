"""
source.py
Resolves a "repo" argument that can be either a local filesystem path or a
git URL (https://github.com/... or a .git URL) into a local directory that
the rest of the pipeline (ingest.py, graph.py) can walk as before.

Used by both the CLI (autopsy/main.py, unchanged behavior for local paths)
and the web layer (autopsy/webapp.py, where a GitHub URL is the common case).
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from contextlib import contextmanager


class SourceError(RuntimeError):
    pass


_GIT_URL_RE = re.compile(r"^(https?://|git@)", re.IGNORECASE)

# Public web deployments should only clone from known-safe git hosts, to
# avoid becoming an open SSRF/clone proxy for arbitrary internal URLs.
ALLOWED_HOSTS = {"github.com", "gitlab.com", "bitbucket.org"}


def is_remote(source: str) -> bool:
    return bool(_GIT_URL_RE.match(source.strip()))


def _validate_host(url: str) -> None:
    m = re.search(r"^https?://([^/]+)/", url.strip() + "/")
    host = m.group(1).lower() if m else ""
    # strip credentials/port if present
    host = host.split("@")[-1].split(":")[0]
    if host not in ALLOWED_HOSTS:
        raise SourceError(
            f"Refusing to clone from host '{host}'. Allowed: {', '.join(sorted(ALLOWED_HOSTS))}"
        )


@contextmanager
def resolve_repo(source: str, shallow: bool = True):
    """Yields a local directory path for `source`.

    If `source` is a local path, yields it directly (no cleanup — the
    caller doesn't own that directory).

    If `source` is a git URL, clones it into a temp dir (shallow by
    default) and yields that path, deleting it on exit regardless of
    success or failure.
    """
    source = source.strip()

    if not is_remote(source):
        if not os.path.isdir(source):
            raise SourceError(f"Local path does not exist or is not a directory: {source}")
        yield source
        return

    _validate_host(source)

    tmpdir = tempfile.mkdtemp(prefix="autopsy-clone-")
    try:
        cmd = ["git", "clone"]
        if shallow:
            cmd += ["--depth", "1"]
        cmd += [source, tmpdir]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if proc.returncode != 0:
            raise SourceError(f"git clone failed: {proc.stderr.strip()[:500]}")
        yield tmpdir
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
