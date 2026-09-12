"""Tests for .claude/hooks/worktree-remove Python uv script."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


HOOK_DIR = Path(__file__).resolve().parent.parent
SCRIPT = HOOK_DIR / "worktree-remove"

JJ_AVAILABLE = shutil.which("jj") is not None


def run_hook(
    data: dict,
    *,
    cwd: Path,
    timeout: int = 30,
    env: dict | None = None,
) -> subprocess.CompletedProcess:
    """Run the worktree-remove hook as a subprocess with JSON on stdin."""
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=json.dumps(data),
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )


# ---------------------------------------------------------------------------
# test_malformed_json — invalid JSON exits 1
# ---------------------------------------------------------------------------


def test_malformed_json_exits_1(git_repo: Path) -> None:
    """Malformed JSON input exits 1 with an error about parse failure."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input="not json",
        cwd=str(git_repo),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 1
    assert "failed to parse JSON input" in proc.stderr


# ---------------------------------------------------------------------------
# test_no_path_exits_1 — empty input
# ---------------------------------------------------------------------------


def test_no_path_exits_1(git_repo: Path) -> None:
    """Empty JSON input exits 1 with an error about missing path field."""
    result = run_hook({}, cwd=git_repo)
    assert result.returncode == 1
    assert "no path field" in result.stderr


# ---------------------------------------------------------------------------
# test_nonexistent_path_exits_0 — path doesn't exist
# ---------------------------------------------------------------------------


def test_nonexistent_path_exits_0(git_repo: Path) -> None:
    """Non-existent path exits 0 with 'already removed' warning."""
    result = run_hook({"path": str(git_repo / "no-such-worktree")}, cwd=git_repo)
    assert result.returncode == 0
    assert "already removed" in result.stderr


# ---------------------------------------------------------------------------
# test_removes_git_worktree — integration: create worktree, remove it
# ---------------------------------------------------------------------------


def test_removes_git_worktree(git_repo: Path) -> None:
    """Create a git worktree in _worktrees sibling, remove it, verify deregistered."""
    repo_name = git_repo.name
    worktrees_dir = git_repo.parent / f"{repo_name}_worktrees"
    worktrees_dir.mkdir(parents=True, exist_ok=True)

    worktree_name = "fix-worker-abc"
    worktree_path = worktrees_dir / worktree_name

    # Create the worktree
    result = subprocess.run(
        ["git", "worktree", "add", str(worktree_path)],
        cwd=str(git_repo),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"git worktree add failed: {result.stderr}"
    assert worktree_path.is_dir()

    # Run the remove hook from within the repo (so detect_repo_root works)
    result = run_hook({"path": str(worktree_path)}, cwd=git_repo)
    assert result.returncode == 0, f"hook failed: {result.stderr}"

    # Worktree directory should be gone
    assert not worktree_path.exists()

    # Git should no longer list this worktree
    list_result = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        cwd=str(git_repo),
        capture_output=True,
        text=True,
    )
    assert worktree_name not in list_result.stdout


# ---------------------------------------------------------------------------
# test_cleans_up_empty_parent — verify parent rmdir after last worktree removed
# ---------------------------------------------------------------------------


def test_cleans_up_empty_parent(git_repo: Path) -> None:
    """After the last worktree is removed, the _worktrees parent dir is removed."""
    repo_name = git_repo.name
    worktrees_dir = git_repo.parent / f"{repo_name}_worktrees"
    worktrees_dir.mkdir(parents=True, exist_ok=True)

    worktree_name = "fix-worker-xyz"
    worktree_path = worktrees_dir / worktree_name

    # Create the worktree
    result = subprocess.run(
        ["git", "worktree", "add", str(worktree_path)],
        cwd=str(git_repo),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"git worktree add failed: {result.stderr}"

    # Run the remove hook
    result = run_hook({"path": str(worktree_path)}, cwd=git_repo)
    assert result.returncode == 0, f"hook failed: {result.stderr}"

    # Both worktree and parent should be gone (parent was the only entry)
    assert not worktree_path.exists()
    assert not worktrees_dir.exists(), (
        f"Expected _worktrees parent to be cleaned up but it still exists: {worktrees_dir}"
    )


# ---------------------------------------------------------------------------
# test_outside_expected_parent_exits_1 — rogue path refused
# ---------------------------------------------------------------------------


def test_outside_expected_parent_exits_1(git_repo: Path, tmp_path: Path) -> None:
    """A path outside the expected _worktrees parent is refused with exit 1."""
    # Create a directory that exists but is NOT inside any _worktrees sibling
    rogue_dir = tmp_path / "rogue-worktree"
    rogue_dir.mkdir()

    # Run hook from within the repo; the rogue_dir is inside tmp_path, not
    # inside <repo>_worktrees/, so it should be refused
    result = run_hook({"path": str(rogue_dir)}, cwd=git_repo)
    assert result.returncode == 1
    assert "refusing removal" in result.stderr or "ERROR" in result.stderr

    # The rogue directory should NOT have been deleted
    assert rogue_dir.exists()


# ---------------------------------------------------------------------------
# test_symlink_traversal_exits_1 — symlink path traversal refused
# ---------------------------------------------------------------------------


def test_symlink_traversal_exits_1(git_repo: Path, tmp_path: Path) -> None:
    """Symlink pointing outside _worktrees is rejected after resolve()."""
    repo_name = git_repo.name
    worktrees_dir = git_repo.parent / f"{repo_name}_worktrees"
    worktrees_dir.mkdir(parents=True, exist_ok=True)

    # Create a target directory outside _worktrees
    outside_dir = tmp_path / "outside-target"
    outside_dir.mkdir()

    # Create a symlink inside _worktrees that points to the outside directory
    symlink_path = worktrees_dir / "evil-link"
    symlink_path.symlink_to(outside_dir)

    try:
        result = run_hook({"path": str(symlink_path)}, cwd=git_repo)

        # After resolve(), the path points outside _worktrees — should be refused
        assert result.returncode == 1
        assert (
            "refusing removal" in result.stderr
            or "outside expected parent" in result.stderr
        )
        # The outside directory must NOT have been deleted
        assert outside_dir.exists()
    finally:
        if symlink_path.is_symlink():
            symlink_path.unlink()
        if worktrees_dir.is_dir() and not any(worktrees_dir.iterdir()):
            worktrees_dir.rmdir()


# ---------------------------------------------------------------------------
# jj integration tests
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not JJ_AVAILABLE, reason="jj is not installed")
class TestJjIntegration:
    def test_removes_jj_worktree(self, jj_repo: Path) -> None:
        """Create a jj workspace in _worktrees sibling, remove it, verify deregistered."""
        repo_name = jj_repo.name
        worktrees_dir = jj_repo.parent / f"{repo_name}_worktrees"
        worktrees_dir.mkdir(parents=True, exist_ok=True)

        worktree_name = "fix-worker-abc"
        worktree_path = worktrees_dir / worktree_name
        workspace_name = f"worktree-{worktree_name}"

        # Create the jj workspace
        result = subprocess.run(
            [
                "jj",
                "--no-pager",
                "workspace",
                "add",
                str(worktree_path),
                "--name",
                workspace_name,
            ],
            cwd=str(jj_repo),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"jj workspace add failed: {result.stderr}"
        assert worktree_path.is_dir()

        try:
            # Run the remove hook from within the repo
            result = run_hook({"path": str(worktree_path)}, cwd=jj_repo)
            assert result.returncode == 0, f"hook failed: {result.stderr}"

            # Worktree directory should be gone
            assert not worktree_path.exists()

            # jj should no longer list this workspace
            list_result = subprocess.run(
                ["jj", "--no-pager", "workspace", "list"],
                cwd=str(jj_repo),
                capture_output=True,
                text=True,
            )
            assert workspace_name not in list_result.stdout
        finally:
            if worktree_path.exists():
                subprocess.run(
                    [
                        "jj",
                        "--no-pager",
                        "workspace",
                        "forget",
                        workspace_name,
                    ],
                    cwd=str(jj_repo),
                    capture_output=True,
                )
                shutil.rmtree(worktree_path, ignore_errors=True)
            if worktrees_dir.is_dir() and not any(worktrees_dir.iterdir()):
                worktrees_dir.rmdir()

    def test_removes_colocated_jj_worktree(self, colocated_jj_repo: Path) -> None:
        """Create a jj workspace in a colocated jj+git repo, remove it, verify jj was used."""
        repo_name = colocated_jj_repo.name
        worktrees_dir = colocated_jj_repo.parent / f"{repo_name}_worktrees"
        worktrees_dir.mkdir(parents=True, exist_ok=True)

        worktree_name = "fix-worker-colocated"
        worktree_path = worktrees_dir / worktree_name
        workspace_name = f"worktree-{worktree_name}"

        # Verify colocated repo has both .jj/ and .git/
        assert (colocated_jj_repo / ".jj").is_dir(), "Expected .jj/ in colocated repo"
        assert (colocated_jj_repo / ".git").is_dir(), "Expected .git/ in colocated repo"

        # Create the jj workspace
        result = subprocess.run(
            [
                "jj",
                "--no-pager",
                "workspace",
                "add",
                str(worktree_path),
                "--name",
                workspace_name,
            ],
            cwd=str(colocated_jj_repo),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"jj workspace add failed: {result.stderr}"
        assert worktree_path.is_dir()

        try:
            # Run the remove hook from within the colocated repo
            result = run_hook({"path": str(worktree_path)}, cwd=colocated_jj_repo)
            assert result.returncode == 0, f"hook failed: {result.stderr}"

            # Worktree directory should be gone
            assert not worktree_path.exists()

            # jj should no longer list this workspace
            list_result = subprocess.run(
                ["jj", "--no-pager", "workspace", "list"],
                cwd=str(colocated_jj_repo),
                capture_output=True,
                text=True,
            )
            assert workspace_name not in list_result.stdout
        finally:
            if worktree_path.exists():
                subprocess.run(
                    [
                        "jj",
                        "--no-pager",
                        "workspace",
                        "forget",
                        workspace_name,
                    ],
                    cwd=str(colocated_jj_repo),
                    capture_output=True,
                )
                shutil.rmtree(worktree_path, ignore_errors=True)
            if worktrees_dir.is_dir() and not any(worktrees_dir.iterdir()):
                worktrees_dir.rmdir()

    def test_jj_not_installed_warning(self, jj_repo: Path, tmp_path: Path) -> None:
        """Exits 0 with 'jj not installed' error when jj binary is absent (advisory, not failure)."""
        repo_name = jj_repo.name
        worktrees_dir = jj_repo.parent / f"{repo_name}_worktrees"
        worktrees_dir.mkdir(parents=True, exist_ok=True)

        worktree_name = "no-jj-test"
        worktree_path = worktrees_dir / worktree_name
        workspace_name = f"worktree-{worktree_name}"

        # Create the workspace with real jj first
        result = subprocess.run(
            [
                "jj",
                "--no-pager",
                "workspace",
                "add",
                str(worktree_path),
                "--name",
                workspace_name,
            ],
            cwd=str(jj_repo),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"jj workspace add failed: {result.stderr}"

        try:
            # Build a fake bin dir containing only git (not jj)
            fake_bin = tmp_path / "fake_bin"
            fake_bin.mkdir()
            git_path = shutil.which("git")
            assert git_path is not None, "git must be available for this test"
            (fake_bin / "git").symlink_to(git_path)

            env = os.environ.copy()
            env["PATH"] = str(fake_bin)

            # Run hook with jj excluded from PATH
            result = run_hook({"path": str(worktree_path)}, cwd=jj_repo, env=env)

            # Hook should exit 0 (directory removed; jj metadata leak is advisory)
            assert result.returncode == 0
            assert "jj not installed" in result.stderr
        finally:
            if worktree_path.exists():
                subprocess.run(
                    [
                        "jj",
                        "--no-pager",
                        "workspace",
                        "forget",
                        workspace_name,
                    ],
                    cwd=str(jj_repo),
                    capture_output=True,
                )
                shutil.rmtree(worktree_path, ignore_errors=True)
            if worktrees_dir.is_dir() and not any(worktrees_dir.iterdir()):
                worktrees_dir.rmdir()

    def test_jj_workspace_not_in_list(self, jj_repo: Path) -> None:
        """Directory in _worktrees but not registered as jj workspace still gets removed."""
        repo_name = jj_repo.name
        worktrees_dir = jj_repo.parent / f"{repo_name}_worktrees"
        worktrees_dir.mkdir(parents=True, exist_ok=True)

        worktree_name = "unregistered-ws"
        worktree_path = worktrees_dir / worktree_name
        # Create directory without registering as jj workspace
        worktree_path.mkdir()

        try:
            result = run_hook({"path": str(worktree_path)}, cwd=jj_repo)

            # Hook should emit INFO about workspace not found and attempt forget
            assert "not found" in result.stderr or "INFO" in result.stderr

            # Directory should be gone (hook still removes it)
            assert not worktree_path.exists()

            # Hook should succeed (unregistered workspace is not a metadata leak)
            assert result.returncode == 0
        finally:
            if worktree_path.exists():
                shutil.rmtree(worktree_path, ignore_errors=True)
            if worktrees_dir.is_dir() and not any(worktrees_dir.iterdir()):
                worktrees_dir.rmdir()

    def test_jj_workspace_list_failure_still_attempts_forget(
        self, jj_repo: Path, tmp_path: Path
    ) -> None:
        """When jj workspace list fails, hook warns but still attempts forget."""
        repo_name = jj_repo.name
        worktrees_dir = jj_repo.parent / f"{repo_name}_worktrees"
        worktrees_dir.mkdir(parents=True, exist_ok=True)

        worktree_name = "list-fail-test"
        worktree_path = worktrees_dir / worktree_name
        workspace_name = f"worktree-{worktree_name}"

        # Create the workspace with real jj
        result = subprocess.run(
            [
                "jj",
                "--no-pager",
                "workspace",
                "add",
                str(worktree_path),
                "--name",
                workspace_name,
            ],
            cwd=str(jj_repo),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"jj workspace add failed: {result.stderr}"

        try:
            # Create a fake jj that fails on workspace list but succeeds on forget
            # In `jj workspace list`: $1=workspace, $2=list
            # In `jj workspace forget <name>`: $1=workspace, $2=forget
            fake_bin = tmp_path / "fake_bin"
            fake_bin.mkdir()

            real_jj = shutil.which("jj")
            fake_jj = fake_bin / "jj"
            fake_jj.write_text(
                "#!/bin/sh\n"
                "# Strip --no-pager if present\n"
                '[ "$1" = "--no-pager" ] && shift\n'
                'case "$2" in\n'
                '  list) echo "error: simulated list failure" >&2; exit 1;;\n'
                f'  *) exec {real_jj} "$@";;\n'
                "esac\n"
            )
            fake_jj.chmod(0o755)

            env = os.environ.copy()
            env["PATH"] = f"{fake_bin}:{env['PATH']}"

            result = run_hook({"path": str(worktree_path)}, cwd=jj_repo, env=env)

            # Hook should warn about list failure but still succeed (forget works)
            assert result.returncode == 0, f"stderr: {result.stderr}"
            assert "jj workspace list failed" in result.stderr
            assert not worktree_path.exists()
        finally:
            if worktree_path.exists():
                subprocess.run(
                    [
                        "jj",
                        "--no-pager",
                        "workspace",
                        "forget",
                        workspace_name,
                    ],
                    cwd=str(jj_repo),
                    capture_output=True,
                )
                shutil.rmtree(worktree_path, ignore_errors=True)
            if worktrees_dir.is_dir() and not any(worktrees_dir.iterdir()):
                worktrees_dir.rmdir()

    def test_jj_forget_failure_exits_1(self, jj_repo: Path, tmp_path: Path) -> None:
        """jj workspace forget failure causes exit 1 (metadata leak = hard error)."""
        repo_name = jj_repo.name
        worktrees_dir = jj_repo.parent / f"{repo_name}_worktrees"
        worktrees_dir.mkdir(parents=True, exist_ok=True)

        worktree_name = "forget-fail-test"
        worktree_path = worktrees_dir / worktree_name
        workspace_name = f"worktree-{worktree_name}"

        # Create the workspace with real jj
        result = subprocess.run(
            [
                "jj",
                "--no-pager",
                "workspace",
                "add",
                str(worktree_path),
                "--name",
                workspace_name,
            ],
            cwd=str(jj_repo),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"jj workspace add failed: {result.stderr}"

        try:
            # Create a fake jj that always exits 1 on workspace forget
            fake_bin = tmp_path / "fake_bin"
            fake_bin.mkdir()

            # Fake jj: succeeds on workspace list, fails on workspace forget
            real_jj = shutil.which("jj")
            fake_jj = fake_bin / "jj"
            fake_jj.write_text(
                "#!/bin/sh\n"
                "# Strip --no-pager if present\n"
                '[ "$1" = "--no-pager" ] && shift\n'
                'if [ "$2" = "forget" ]; then\n'
                '  echo "ERROR: fake jj forget failure" >&2\n'
                "  exit 1\n"
                "fi\n"
                f'exec {real_jj} "$@"\n'
            )
            fake_jj.chmod(0o755)

            # Put fake_bin first in PATH so our fake jj takes priority
            env = os.environ.copy()
            env["PATH"] = f"{fake_bin}:{env['PATH']}"

            result = run_hook({"path": str(worktree_path)}, cwd=jj_repo, env=env)

            # jj forget failure = exit 1 (metadata leak = hard error)
            assert result.returncode == 1
            assert "ERROR" in result.stderr
        finally:
            if worktree_path.exists():
                subprocess.run(
                    [
                        "jj",
                        "--no-pager",
                        "workspace",
                        "forget",
                        workspace_name,
                    ],
                    cwd=str(jj_repo),
                    capture_output=True,
                )
                shutil.rmtree(worktree_path, ignore_errors=True)
            if worktrees_dir.is_dir() and not any(worktrees_dir.iterdir()):
                worktrees_dir.rmdir()


# ---------------------------------------------------------------------------
# test_inferred_repo_root_fallback — CWD outside any repo, infer from path
# ---------------------------------------------------------------------------


def test_inferred_repo_root_fallback(git_repo: Path) -> None:
    """When CWD is outside any repo, hook infers repo root from _worktrees path."""
    repo_name = git_repo.name
    worktrees_dir = git_repo.parent / f"{repo_name}_worktrees"
    worktrees_dir.mkdir(parents=True, exist_ok=True)

    worktree_name = "inferred-test"
    worktree_path = worktrees_dir / worktree_name

    # Create worktree
    result = subprocess.run(
        ["git", "worktree", "add", str(worktree_path)],
        cwd=str(git_repo),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"git worktree add failed: {result.stderr}"

    try:
        # Run hook from a directory that is NOT a git repo
        # Use git_repo.parent (the tmp_path) as CWD - not a git repo
        result = run_hook({"path": str(worktree_path)}, cwd=git_repo.parent)

        assert result.returncode == 0, f"hook failed: {result.stderr}"
        assert not worktree_path.exists(), "worktree directory should be removed"
        # Should warn about inference
        assert "inferred" in result.stderr.lower() or "WARNING" in result.stderr
    finally:
        if worktree_path.is_dir():
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(worktree_path)],
                cwd=str(git_repo),
                capture_output=True,
            )
        if worktrees_dir.is_dir() and not any(worktrees_dir.iterdir()):
            worktrees_dir.rmdir()
