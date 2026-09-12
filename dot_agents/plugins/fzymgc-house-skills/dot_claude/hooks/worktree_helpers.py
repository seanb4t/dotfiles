#!/usr/bin/env python3
"""Shared helpers for worktree-create, worktree-remove, and post-edit-format hooks.

Functions:
    sanitize_for_output(s)          — strip control chars for safe logging
    validate_safe_name(name, label) — reject path traversal/metacharacters
    run_cmd(args, *, cwd)           — thin subprocess wrapper, never raises
    detect_repo_root(*, cwd)        — find repo root via git or jj
    cleanup_empty_parent(parent)    — rmdir if directory exists and is empty
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path


def sanitize_for_output(s: str) -> str:
    """Strip C0 control chars (0x00-0x1F) except tab/newline/CR, DEL (0x7F),
    and C1 control chars (0x80-0x9F).

    Preserving \\t (0x09), \\n (0x0A), \\r (0x0D) allows multi-line messages
    to remain readable. This matches the bash:
        tr -d '\\000-\\010\\013\\014\\016-\\037\\177\\200-\\237'
    """
    # Build a set of code points to remove:
    # 0x00-0x08 (NUL..BS), 0x0B (VT), 0x0C (FF), 0x0E-0x1F (SO..US),
    # 0x7F (DEL), 0x80-0x9F (C1 controls)
    remove_chars = (
        set(range(0x00, 0x09))  # 0x00-0x08
        | {0x0B, 0x0C}  # VT, FF
        | set(range(0x0E, 0x20))  # 0x0E-0x1F
        | {0x7F}  # DEL
        | set(range(0x80, 0xA0))  # 0x80-0x9F
    )
    return "".join(ch for ch in s if ord(ch) not in remove_chars)


def validate_safe_name(name: str, label: str) -> None:
    """Validate that *name* is safe for use as a filesystem component.

    Raises ValueError for:
    - Empty names
    - Characters outside [a-zA-Z0-9_.-]
    - Leading dot, trailing dot, or double-dot anywhere in the name
    """
    if not name:
        raise ValueError(f"{sanitize_for_output(label)} must not be empty")

    invalid = (
        not re.fullmatch(r"[a-zA-Z0-9_.-]+", name)
        or name.startswith(".")
        or name.endswith(".")
        or ".." in name
    )
    if invalid:
        safe_name = sanitize_for_output(name)
        safe_label = sanitize_for_output(label)
        raise ValueError(
            f"invalid {safe_label} '{safe_name}' "
            "(alphanumeric, dots, hyphens, underscores only; "
            "no leading dot, trailing dot, or double-dot)"
        )


def run_cmd(args: list[str], *, cwd: Path | str) -> subprocess.CompletedProcess:
    """Run *args* as a subprocess in *cwd*.

    Returns a CompletedProcess. Never raises: returns a synthetic
    result with returncode=127 and descriptive stderr on OSError
    (executable not found, permission denied, etc.).
    """
    try:
        return subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    except OSError as exc:
        return subprocess.CompletedProcess(
            args=args, returncode=127, stdout="", stderr=f"{type(exc).__name__}: {exc}"
        )


def detect_repo_root(*, cwd: Path | str) -> Path:
    """Return the repository root for the working directory *cwd*.

    Tries ``git rev-parse --show-toplevel`` first, then ``jj root`` if jj
    is in PATH. Raises RuntimeError if neither succeeds.
    """
    result = run_cmd(["git", "rev-parse", "--show-toplevel"], cwd=cwd)
    if result.returncode == 0:
        root = result.stdout.strip()
        if root and Path(root).is_dir():
            return Path(root)
        print(
            f"WARNING: git rev-parse succeeded but returned unusable path "
            f"{repr(root)} — trying jj",
            file=sys.stderr,
        )

    # git failed or returned unusable path — try jj
    if shutil.which("jj") is None:
        raise RuntimeError(
            "not inside a git/jj repository (git rev-parse failed; jj not in PATH)"
        )

    jj_result = run_cmd(["jj", "--no-pager", "root"], cwd=cwd)
    if jj_result.returncode == 0:
        jj_root = jj_result.stdout.strip()
        if jj_root and Path(jj_root).is_dir():
            return Path(jj_root)
        if not jj_root:
            raise RuntimeError(
                "not inside a git/jj repository "
                "(git rev-parse failed; jj root returned empty output)"
            )
        raise RuntimeError(
            f"not inside a git/jj repository "
            f"(git rev-parse failed; jj root returned "
            f"'{sanitize_for_output(jj_root)}' but directory does not exist)"
        )

    jj_err = sanitize_for_output(jj_result.stderr.strip())
    raise RuntimeError(
        f"not inside a git/jj repository "
        f"(git rev-parse and jj root both failed"
        f"{'; jj: ' + jj_err if jj_err else ''})"
    )


def cleanup_empty_parent(parent: Path | str) -> None:
    """Remove *parent* if it exists and is empty. Warns to stderr on failure."""
    parent = Path(parent)
    if not parent.exists():
        return
    try:
        contents = list(parent.iterdir())
    except OSError as exc:
        print(
            f"WARNING: failed to list parent directory "
            f"'{sanitize_for_output(str(parent))}': "
            f"{sanitize_for_output(str(exc))}",
            file=sys.stderr,
        )
        return
    if contents:
        return
    try:
        parent.rmdir()
    except OSError as exc:
        print(
            f"WARNING: failed to remove empty parent "
            f"'{sanitize_for_output(str(parent))}': "
            f"{sanitize_for_output(str(exc)[:500])}",
            file=sys.stderr,
        )
