"""Tests for jj/hooks/guard-git-mutating PreToolUse hook."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parent.parent / "guard-git-mutating"


def run_hook(command: str, cwd: str) -> subprocess.CompletedProcess:
    """Run the hook with a simulated Bash tool call."""
    data = {"tool_input": {"command": command}, "cwd": cwd}
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(data),
        capture_output=True,
        text=True,
        timeout=10,
    )


@pytest.fixture()
def jj_repo(tmp_path: Path) -> Path:
    """Create a directory with .jj/ to simulate a jj repo."""
    (tmp_path / ".jj").mkdir()
    return tmp_path


@pytest.fixture()
def colocated_repo(tmp_path: Path) -> Path:
    """Create a directory with both .jj/ and .git/."""
    (tmp_path / ".jj").mkdir()
    (tmp_path / ".git").mkdir()
    return tmp_path


@pytest.fixture()
def git_repo(tmp_path: Path) -> Path:
    """Create a directory with only .git/ (no .jj/)."""
    (tmp_path / ".git").mkdir()
    return tmp_path


class TestMutatingCommands:
    """Mutating git commands in jj repos should be denied."""

    @pytest.mark.parametrize(
        "command",
        [
            "git commit -m 'test'",
            "git checkout main",
            "git rebase main",
            "git merge feature",
            "git push origin main",
            "git stash",
            "git reset --hard HEAD~1",
            "git switch main",
            "git worktree add /tmp/wt",
        ],
    )
    def test_mutating_command_denied(self, jj_repo: Path, command: str) -> None:
        result = run_hook(command, str(jj_repo))
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "systemMessage" in output

    def test_git_c_path_commit(self, jj_repo: Path) -> None:
        """git -C /path commit must be caught (the regex fix)."""
        result = run_hook("git -C /tmp/repo commit -m test", str(jj_repo))
        output = json.loads(result.stdout)
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "git commit" in output["hookSpecificOutput"]["permissionDecisionReason"]

    def test_chained_command(self, jj_repo: Path) -> None:
        """Only the mutating part of a chain is flagged."""
        result = run_hook("git log && git commit -m fix", str(jj_repo))
        output = json.loads(result.stdout)
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "git commit" in output["hookSpecificOutput"]["permissionDecisionReason"]


class TestAdvisoryCommands:
    """Read-only git commands with better jj equivalents produce advisory tips."""

    @pytest.mark.parametrize(
        "command",
        [
            "git log --oneline",
            "git diff HEAD~1",
            "git status",
            "git show HEAD",
            "git blame file.py",
        ],
    )
    def test_advisory_commands_educate(self, jj_repo: Path, command: str) -> None:
        result = run_hook(command, str(jj_repo))
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "systemMessage" in output
        assert "hookSpecificOutput" not in output  # no permission decision — allowed
        assert "jj" in output["systemMessage"]  # mentions jj alternative


class TestSilentCommands:
    """Git plumbing commands with no jj advantage pass silently."""

    @pytest.mark.parametrize(
        "command",
        [
            "git rev-parse --show-toplevel",
            "git remote -v",
            "git ls-files",
            "git config user.name",
        ],
    )
    def test_plumbing_allowed_silently(self, jj_repo: Path, command: str) -> None:
        result = run_hook(command, str(jj_repo))
        assert result.returncode == 0
        assert result.stdout.strip() == ""  # no output = silent allow


class TestNonJjRepo:
    """In a non-jj repo, all git commands should pass."""

    def test_mutating_allowed_in_git_repo(self, git_repo: Path) -> None:
        result = run_hook("git commit -m test", str(git_repo))
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_mutating_allowed_outside_repo(self, tmp_path: Path) -> None:
        result = run_hook("git commit -m test", str(tmp_path))
        assert result.returncode == 0
        assert result.stdout.strip() == ""


class TestEquivalents:
    """Verify jj equivalents are shown in the reason."""

    def test_commit_shows_jj_commit(self, jj_repo: Path) -> None:
        result = run_hook("git commit -m test", str(jj_repo))
        output = json.loads(result.stdout)
        reason = output["hookSpecificOutput"]["permissionDecisionReason"]
        assert "jj commit" in reason

    def test_rebase_shows_jj_rebase(self, jj_repo: Path) -> None:
        result = run_hook("git rebase main", str(jj_repo))
        output = json.loads(result.stdout)
        reason = output["hookSpecificOutput"]["permissionDecisionReason"]
        assert "jj rebase" in reason


class TestJjExempt:
    """The # jj-exempt escape hatch escalates to ask (human approval)."""

    def test_exempt_escalates_to_ask(self, jj_repo: Path) -> None:
        result = run_hook("git push origin main # jj-exempt", str(jj_repo))
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["hookSpecificOutput"]["permissionDecision"] == "ask"
        assert "jj-exempt" in output["hookSpecificOutput"]["permissionDecisionReason"]

    def test_exempt_not_silent_allow(self, jj_repo: Path) -> None:
        """jj-exempt must NOT silently allow — it requires human approval."""
        result = run_hook("git commit -m fix # jj-exempt", str(jj_repo))
        assert result.stdout.strip() != ""  # must produce output (ask decision)


class TestEdgeCases:
    """Edge cases for input handling."""

    def test_empty_command(self, jj_repo: Path) -> None:
        result = run_hook("", str(jj_repo))
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_non_git_command(self, jj_repo: Path) -> None:
        result = run_hook("ls -la", str(jj_repo))
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_gh_cli_allowed(self, jj_repo: Path) -> None:
        result = run_hook("gh pr merge 31", str(jj_repo))
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_malformed_json(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(HOOK)],
            input="not json",
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert proc.returncode == 0

    def test_empty_stdin(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(HOOK)],
            input="",
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert proc.returncode == 0

    def test_null_tool_input(self) -> None:
        """tool_input as null should not crash with AttributeError."""
        proc = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps({"tool_input": None, "cwd": "/tmp"}),
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert proc.returncode == 0

    def test_string_tool_input(self) -> None:
        """tool_input as string should not crash with AttributeError."""
        proc = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps({"tool_input": "not a dict", "cwd": "/tmp"}),
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert proc.returncode == 0
