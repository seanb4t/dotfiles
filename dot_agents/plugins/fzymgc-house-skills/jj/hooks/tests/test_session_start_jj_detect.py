"""Tests for jj/hooks/session-start-jj-detect SessionStart hook."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parent.parent / "session-start-jj-detect"


def run_hook(cwd: str) -> subprocess.CompletedProcess:
    """Run the hook with a simulated SessionStart event."""
    data = {"cwd": cwd}
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(data),
        capture_output=True,
        text=True,
        timeout=10,
    )


@pytest.fixture()
def jj_repo(tmp_path: Path) -> Path:
    """Pure jj repo (no .git/)."""
    (tmp_path / ".jj").mkdir()
    return tmp_path


@pytest.fixture()
def colocated_repo(tmp_path: Path) -> Path:
    """Colocated jj+git repo."""
    (tmp_path / ".jj").mkdir()
    (tmp_path / ".git").mkdir()
    return tmp_path


@pytest.fixture()
def git_repo(tmp_path: Path) -> Path:
    """Git-only repo."""
    (tmp_path / ".git").mkdir()
    return tmp_path


class TestJjDetection:
    def test_pure_jj_repo_detected(self, jj_repo: Path) -> None:
        result = run_hook(str(jj_repo))
        assert result.returncode == 0
        assert "pure jj" in result.stdout
        assert "VCS Policy" in result.stdout
        assert "MUST use jj" in result.stdout

    def test_colocated_repo_detected(self, colocated_repo: Path) -> None:
        result = run_hook(str(colocated_repo))
        assert result.returncode == 0
        assert "colocated jj+git" in result.stdout
        assert "Colocated Repo Notes" in result.stdout
        assert "MAY use read-only git plumbing" in result.stdout

    def test_git_only_repo_silent(self, git_repo: Path) -> None:
        result = run_hook(str(git_repo))
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_no_repo_silent(self, tmp_path: Path) -> None:
        result = run_hook(str(tmp_path))
        assert result.returncode == 0
        assert result.stdout.strip() == ""


class TestOutputFormat:
    def test_output_goes_to_stdout_not_stderr(self, colocated_repo: Path) -> None:
        """Context must be on stdout for SessionStart injection."""
        result = run_hook(str(colocated_repo))
        assert "VCS Policy" in result.stdout
        assert result.stderr.strip() == ""

    def test_at_minus_mentioned(self, jj_repo: Path) -> None:
        result = run_hook(str(jj_repo))
        assert "@-" in result.stdout

    def test_skill_loading_directive(self, jj_repo: Path) -> None:
        """Session start must instruct Claude to load the jujutsu skill."""
        result = run_hook(str(jj_repo))
        assert 'skill="jj:jujutsu"' in result.stdout

    def test_quick_reference_included(self, jj_repo: Path) -> None:
        """Session start should include git→jj command reference."""
        result = run_hook(str(jj_repo))
        assert "Quick Reference" in result.stdout
        assert "jj commit" in result.stdout

    def test_rebase_flag_uses_onto(self, jj_repo: Path) -> None:
        """Rebase quick reference must use -o (not deprecated -d)."""
        result = run_hook(str(jj_repo))
        assert "-o D" in result.stdout or "--onto" in result.stdout
        assert "-d D" not in result.stdout

    def test_no_double_dots_when_jj_info_missing(self, jj_repo: Path) -> None:
        """When jj version/workspace fails, no '. . .' artifacts."""
        # The hook will try to run jj commands which may fail in a fake .jj/ dir
        # but should still produce clean output
        result = run_hook(str(jj_repo))
        assert ". ." not in result.stdout


class TestEdgeCases:
    def test_empty_stdin(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(HOOK)],
            input="",
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert proc.returncode == 0

    def test_malformed_json(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(HOOK)],
            input="not json",
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert proc.returncode == 0

    def test_subdirectory_detection(self, jj_repo: Path) -> None:
        """Hook should find .jj/ when CWD is a subdirectory."""
        subdir = jj_repo / "src" / "deep"
        subdir.mkdir(parents=True)
        result = run_hook(str(subdir))
        assert result.returncode == 0
        # Must detect the jj repo from the parent — output must mention jj
        assert "pure jj" in result.stdout or "colocated" in result.stdout
