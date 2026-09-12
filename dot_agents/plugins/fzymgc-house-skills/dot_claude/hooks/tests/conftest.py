"""Shared pytest fixtures for worktree_helpers tests."""

from __future__ import annotations

import json
import subprocess
import sys
from io import StringIO
from pathlib import Path

import pytest


@pytest.fixture()
def git_repo(tmp_path: Path) -> Path:
    """Create a minimal git repository with one commit and return its path."""
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.email", "test@example.com"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.name", "Test User"],
        check=True,
        capture_output=True,
    )
    readme = tmp_path / "README.md"
    readme.write_text("# test\n")
    subprocess.run(
        ["git", "-C", str(tmp_path), "add", "README.md"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-m", "initial commit"],
        check=True,
        capture_output=True,
    )
    return tmp_path


@pytest.fixture()
def jj_repo(tmp_path: Path) -> Path:
    """Create a minimal jj repository with one commit and return its path."""
    subprocess.run(
        ["jj", "git", "init", str(tmp_path)],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "jj",
            "--no-pager",
            "config",
            "set",
            "--repo",
            "user.email",
            "test@example.com",
        ],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["jj", "--no-pager", "config", "set", "--repo", "user.name", "Test User"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    readme = tmp_path / "README.md"
    readme.write_text("# test\n")
    subprocess.run(
        ["jj", "--no-pager", "commit", "-m", "initial commit"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    return tmp_path


@pytest.fixture()
def colocated_jj_repo(tmp_path: Path) -> Path:
    """Create a colocated jj+git repo (both .jj/ and .git/) with one commit."""
    subprocess.run(
        ["jj", "git", "init", "--colocate", str(tmp_path)],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "jj",
            "--no-pager",
            "config",
            "set",
            "--repo",
            "user.email",
            "test@example.com",
        ],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["jj", "--no-pager", "config", "set", "--repo", "user.name", "Test User"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    readme = tmp_path / "README.md"
    readme.write_text("# test\n")
    subprocess.run(
        ["jj", "--no-pager", "commit", "-m", "initial commit"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    return tmp_path


@pytest.fixture()
def mock_stdin(monkeypatch: pytest.MonkeyPatch):
    """Return a factory that patches sys.stdin with JSON data.

    Usage::

        def test_foo(mock_stdin):
            mock_stdin({"toolName": "Write", "toolInput": {"file_path": "/tmp/x"}})
            # sys.stdin now yields that JSON when read
    """

    def _patch(data: dict) -> None:
        monkeypatch.setattr(sys, "stdin", StringIO(json.dumps(data)))

    return _patch
