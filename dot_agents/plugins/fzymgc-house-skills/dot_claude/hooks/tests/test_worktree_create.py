"""Tests for .claude/hooks/worktree-create Python uv script."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


HOOK_DIR = Path(__file__).resolve().parent.parent
SCRIPT = HOOK_DIR / "worktree-create"

JJ_AVAILABLE = shutil.which("jj") is not None


def run_hook(
    data: dict,
    *,
    cwd: Path,
    timeout: int = 30,
    env: dict | None = None,
) -> subprocess.CompletedProcess:
    """Run the worktree-create hook as a subprocess with JSON on stdin."""
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
# Input validation tests — all should exit 1
# ---------------------------------------------------------------------------


class TestInputValidation:
    def test_no_name_field(self, git_repo: Path) -> None:
        """Missing name field exits 1 with an error message."""
        result = run_hook({}, cwd=git_repo)
        assert result.returncode == 1
        assert "no worktree name provided" in result.stderr

    def test_empty_name(self, git_repo: Path) -> None:
        """Empty string name exits 1."""
        result = run_hook({"name": ""}, cwd=git_repo)
        assert result.returncode == 1
        assert "no worktree name provided" in result.stderr

    def test_path_traversal_dotdot(self, git_repo: Path) -> None:
        """Name containing '..' exits 1."""
        result = run_hook({"name": "../evil"}, cwd=git_repo)
        assert result.returncode == 1
        assert "ERROR" in result.stderr

    def test_path_traversal_leading_dot(self, git_repo: Path) -> None:
        """Name starting with '.' exits 1."""
        result = run_hook({"name": ".hidden"}, cwd=git_repo)
        assert result.returncode == 1
        assert "ERROR" in result.stderr

    def test_shell_metachar_semicolon(self, git_repo: Path) -> None:
        """Name containing ';' exits 1."""
        result = run_hook({"name": "foo;bar"}, cwd=git_repo)
        assert result.returncode == 1
        assert "ERROR" in result.stderr

    def test_shell_metachar_dollar(self, git_repo: Path) -> None:
        """Name containing '$' exits 1."""
        result = run_hook({"name": "foo$bar"}, cwd=git_repo)
        assert result.returncode == 1
        assert "ERROR" in result.stderr

    def test_shell_metachar_backtick(self, git_repo: Path) -> None:
        """Name containing backtick exits 1."""
        result = run_hook({"name": "foo`bar"}, cwd=git_repo)
        assert result.returncode == 1
        assert "ERROR" in result.stderr

    def test_shell_metachar_space(self, git_repo: Path) -> None:
        """Name containing space exits 1."""
        result = run_hook({"name": "foo bar"}, cwd=git_repo)
        assert result.returncode == 1
        assert "ERROR" in result.stderr

    def test_invalid_json(self, git_repo: Path) -> None:
        """Malformed JSON input exits 1."""
        proc = subprocess.run(
            [sys.executable, str(SCRIPT)],
            input="not json",
            cwd=str(git_repo),
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert proc.returncode == 1
        assert "ERROR" in proc.stderr


# ---------------------------------------------------------------------------
# Git integration test
# ---------------------------------------------------------------------------


class TestGitIntegration:
    def test_creates_worktree_in_git_repo(self, git_repo: Path) -> None:
        """Creates a worktree and prints its path to stdout."""
        worktree_parent = git_repo.parent / f"{git_repo.name}_worktrees"
        worktree_path = worktree_parent / "feature-x"

        try:
            result = run_hook({"name": "feature-x"}, cwd=git_repo)

            assert result.returncode == 0, f"stderr: {result.stderr}"
            output = result.stdout.strip()
            assert output == str(worktree_path), (
                f"Expected {worktree_path}, got {output}"
            )
            assert Path(output).is_dir(), "Worktree directory should exist"

            # Verify it appears in git worktree list
            wt_list = subprocess.run(
                ["git", "worktree", "list", "--porcelain"],
                cwd=str(git_repo),
                capture_output=True,
                text=True,
                check=True,
            )
            assert str(worktree_path) in wt_list.stdout

        finally:
            # Cleanup
            if worktree_path.is_dir():
                subprocess.run(
                    ["git", "worktree", "remove", "--force", str(worktree_path)],
                    cwd=str(git_repo),
                    capture_output=True,
                )
            if worktree_parent.is_dir() and not any(worktree_parent.iterdir()):
                worktree_parent.rmdir()

    def test_creates_branch_in_git_repo(self, git_repo: Path) -> None:
        """Created worktree has branch worktree/<name>."""
        worktree_parent = git_repo.parent / f"{git_repo.name}_worktrees"
        worktree_path = worktree_parent / "my-feature"

        try:
            result = run_hook({"name": "my-feature"}, cwd=git_repo)
            assert result.returncode == 0, f"stderr: {result.stderr}"

            # Verify the branch exists
            branches = subprocess.run(
                ["git", "branch"],
                cwd=str(git_repo),
                capture_output=True,
                text=True,
                check=True,
            )
            assert "worktree/my-feature" in branches.stdout

        finally:
            if worktree_path.is_dir():
                subprocess.run(
                    ["git", "worktree", "remove", "--force", str(worktree_path)],
                    cwd=str(git_repo),
                    capture_output=True,
                )
            if worktree_parent.is_dir() and not any(worktree_parent.iterdir()):
                worktree_parent.rmdir()

    def test_branch_already_exists_exits_1(self, git_repo: Path) -> None:
        """Exits 1 when worktree/<name> branch already exists."""
        # Pre-create the branch that worktree-create will try to create
        subprocess.run(
            ["git", "-C", str(git_repo), "branch", "worktree/duplicate"],
            check=True,
            capture_output=True,
        )

        worktree_parent = git_repo.parent / f"{git_repo.name}_worktrees"
        worktree_path = worktree_parent / "duplicate"

        try:
            result = run_hook({"name": "duplicate"}, cwd=git_repo)

            assert result.returncode == 1
            assert "git worktree add failed" in result.stderr
            # Verify no partial directory left behind
            assert not worktree_path.exists()
        finally:
            if worktree_path.is_dir():
                subprocess.run(
                    ["git", "worktree", "remove", "--force", str(worktree_path)],
                    cwd=str(git_repo),
                    capture_output=True,
                )
            if worktree_parent.is_dir() and not any(worktree_parent.iterdir()):
                worktree_parent.rmdir()


# ---------------------------------------------------------------------------
# Sibling directory test
# ---------------------------------------------------------------------------


class TestSiblingDirectory:
    def test_worktree_parent_is_sibling(self, git_repo: Path) -> None:
        """Worktree parent is <repo>_worktrees at the same level as the repo."""
        worktree_parent = git_repo.parent / f"{git_repo.name}_worktrees"
        worktree_path = worktree_parent / "sibling-test"

        try:
            result = run_hook({"name": "sibling-test"}, cwd=git_repo)
            assert result.returncode == 0, f"stderr: {result.stderr}"

            output_path = Path(result.stdout.strip())

            # Verify the parent directory name pattern
            assert output_path.parent.name == f"{git_repo.name}_worktrees", (
                f"Expected parent name '{git_repo.name}_worktrees', "
                f"got '{output_path.parent.name}'"
            )

            # Verify it's a sibling (same parent as the repo)
            assert output_path.parent.parent == git_repo.parent, (
                f"Worktree parent should be sibling of repo, "
                f"not nested inside it. Repo: {git_repo}, "
                f"Worktree: {output_path}"
            )

            # Verify worktree is NOT inside the repo
            assert not str(output_path).startswith(str(git_repo) + "/"), (
                f"Worktree {output_path} must not be inside repo {git_repo}"
            )

        finally:
            if worktree_path.is_dir():
                subprocess.run(
                    ["git", "worktree", "remove", "--force", str(worktree_path)],
                    cwd=str(git_repo),
                    capture_output=True,
                )
            if worktree_parent.is_dir() and not any(worktree_parent.iterdir()):
                worktree_parent.rmdir()


# ---------------------------------------------------------------------------
# jj integration tests
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not JJ_AVAILABLE, reason="jj is not installed")
class TestJjIntegration:
    def test_creates_worktree_in_jj_repo(self, jj_repo: Path) -> None:
        """Creates a jj workspace and prints its path to stdout."""
        worktree_parent = jj_repo.parent / f"{jj_repo.name}_worktrees"
        worktree_path = worktree_parent / "feature-x"

        try:
            result = run_hook({"name": "feature-x"}, cwd=jj_repo)

            assert result.returncode == 0, f"stderr: {result.stderr}"
            output = result.stdout.strip()
            assert output == str(worktree_path), (
                f"Expected {worktree_path}, got {output}"
            )
            assert Path(output).is_dir(), "Worktree directory should exist"

            # Verify the workspace appears in jj workspace list
            wt_list = subprocess.run(
                ["jj", "--no-pager", "workspace", "list"],
                cwd=str(jj_repo),
                capture_output=True,
                text=True,
                check=True,
            )
            assert "worktree-feature-x" in wt_list.stdout

        finally:
            if worktree_path.exists():
                subprocess.run(
                    ["jj", "--no-pager", "workspace", "forget", "worktree-feature-x"],
                    cwd=str(jj_repo),
                    capture_output=True,
                )
                shutil.rmtree(worktree_path, ignore_errors=True)
            if worktree_parent.is_dir() and not any(worktree_parent.iterdir()):
                worktree_parent.rmdir()

    def test_jj_not_installed_exits_1(
        self, colocated_jj_repo: Path, tmp_path: Path
    ) -> None:
        """Exits 1 with 'jj is not installed' when jj binary is absent."""
        # Use colocated repo so git rev-parse succeeds (detect_repo_root works)
        # but jj is absent from PATH so shutil.which("jj") returns None.
        fake_bin = tmp_path / "fake_bin"
        fake_bin.mkdir()
        git_path = shutil.which("git")
        assert git_path is not None, "git must be available for this test"
        (fake_bin / "git").symlink_to(git_path)

        env = os.environ.copy()
        env["PATH"] = str(fake_bin)

        result = run_hook({"name": "no-jj"}, cwd=colocated_jj_repo, env=env)

        assert result.returncode == 1
        assert "jj is not installed" in result.stderr

    def test_creates_worktree_in_colocated_repo(self, colocated_jj_repo: Path) -> None:
        """Creates a jj workspace in a colocated jj+git repo, using jj (not git)."""
        worktree_parent = (
            colocated_jj_repo.parent / f"{colocated_jj_repo.name}_worktrees"
        )
        worktree_path = worktree_parent / "feature-x"

        try:
            result = run_hook({"name": "feature-x"}, cwd=colocated_jj_repo)

            assert result.returncode == 0, f"stderr: {result.stderr}"
            output = result.stdout.strip()
            assert output == str(worktree_path), (
                f"Expected {worktree_path}, got {output}"
            )
            assert Path(output).is_dir(), "Worktree directory should exist"

            # Verify .jj/ is present in the colocated repo (sanity check)
            assert (colocated_jj_repo / ".jj").is_dir(), (
                "Expected .jj/ in colocated repo"
            )
            assert (colocated_jj_repo / ".git").is_dir(), (
                "Expected .git/ in colocated repo"
            )

            # Verify the workspace appears in jj workspace list (jj was used, not git)
            wt_list = subprocess.run(
                ["jj", "--no-pager", "workspace", "list"],
                cwd=str(colocated_jj_repo),
                capture_output=True,
                text=True,
                check=True,
            )
            assert "worktree-feature-x" in wt_list.stdout

        finally:
            if worktree_path.exists():
                subprocess.run(
                    ["jj", "--no-pager", "workspace", "forget", "worktree-feature-x"],
                    cwd=str(colocated_jj_repo),
                    capture_output=True,
                )
                shutil.rmtree(worktree_path, ignore_errors=True)
            if worktree_parent.is_dir() and not any(worktree_parent.iterdir()):
                worktree_parent.rmdir()

    def test_old_jj_version_error_message(self, jj_repo: Path, tmp_path: Path) -> None:
        """When jj workspace add --name fails with version-related error, shows version message."""
        # Create a fake jj script that simulates old jj behavior
        fake_bin = tmp_path / "fake_bin"
        fake_bin.mkdir()

        # Copy real git so detect_repo_root works
        git_path = shutil.which("git")
        assert git_path is not None, "git must be available for this test"
        (fake_bin / "git").symlink_to(git_path)

        # Create a fake jj that fails with "unexpected argument '--name'"
        fake_jj = fake_bin / "jj"
        fake_jj.write_text(
            "#!/bin/sh\n"
            'case "$*" in\n'
            '  *"workspace add"*)\n'
            "    echo \"error: unexpected argument '--name' found\" >&2\n"
            "    exit 2\n"
            "    ;;\n"
            '  *"root"*)\n'
            '    echo "' + str(jj_repo) + '"\n'
            "    ;;\n"
            "  *)\n"
            "    exit 0\n"
            "    ;;\n"
            "esac\n"
        )
        fake_jj.chmod(0o755)

        env = os.environ.copy()
        env["PATH"] = str(fake_bin)

        result = run_hook({"name": "old-jj-test"}, cwd=jj_repo, env=env)

        assert result.returncode == 1
        assert "jj version too old" in result.stderr


# ---------------------------------------------------------------------------
# Lefthook install tests
# ---------------------------------------------------------------------------


class TestLefthookInstall:
    """Test lefthook install behavior in worktree-create."""

    def _make_env_with_fake_bin(self, tmp_path: Path, fake_bin: Path) -> dict:
        """Build an env dict with fake_bin prepended to PATH."""
        env = os.environ.copy()
        env["PATH"] = str(fake_bin) + os.pathsep + env.get("PATH", "")
        return env

    def test_lefthook_install_called_when_config_exists(
        self, git_repo: Path, tmp_path: Path
    ) -> None:
        """lefthook install is called when lefthook.yml exists in the repo root."""
        # Create lefthook.yml in the repo root
        (git_repo / "lefthook.yml").write_text("pre-commit:\n  commands: {}\n")

        # Create a fake lefthook that records it was called and exits 0
        fake_bin = tmp_path / "fake_bin"
        fake_bin.mkdir()
        called_marker = tmp_path / "lefthook_called"
        fake_lefthook = fake_bin / "lefthook"
        fake_lefthook.write_text(f"#!/bin/sh\ntouch {called_marker}\nexit 0\n")
        fake_lefthook.chmod(0o755)

        # Copy real git so VCS detection works
        git_path = shutil.which("git")
        assert git_path is not None
        (fake_bin / "git").symlink_to(git_path)

        worktree_parent = git_repo.parent / f"{git_repo.name}_worktrees"
        worktree_path = worktree_parent / "lh-test"

        try:
            env = self._make_env_with_fake_bin(tmp_path, fake_bin)
            result = run_hook({"name": "lh-test"}, cwd=git_repo, env=env)

            assert result.returncode == 0, f"stderr: {result.stderr}"
            assert called_marker.exists(), (
                "lefthook install was not called even though lefthook.yml exists"
            )
        finally:
            if worktree_path.is_dir():
                subprocess.run(
                    ["git", "worktree", "remove", "--force", str(worktree_path)],
                    cwd=str(git_repo),
                    capture_output=True,
                )
            if worktree_parent.is_dir() and not any(worktree_parent.iterdir()):
                worktree_parent.rmdir()

    def test_lefthook_install_failure_warns(
        self, git_repo: Path, tmp_path: Path
    ) -> None:
        """lefthook install failure emits a WARNING but the hook still exits 0."""
        (git_repo / "lefthook.yml").write_text("pre-commit:\n  commands: {}\n")

        fake_bin = tmp_path / "fake_bin"
        fake_bin.mkdir()
        fake_lefthook = fake_bin / "lefthook"
        fake_lefthook.write_text("#!/bin/sh\necho 'install failed' >&2\nexit 1\n")
        fake_lefthook.chmod(0o755)

        git_path = shutil.which("git")
        assert git_path is not None
        (fake_bin / "git").symlink_to(git_path)

        worktree_parent = git_repo.parent / f"{git_repo.name}_worktrees"
        worktree_path = worktree_parent / "lh-fail"

        try:
            env = self._make_env_with_fake_bin(tmp_path, fake_bin)
            result = run_hook({"name": "lh-fail"}, cwd=git_repo, env=env)

            # Hook must succeed — lefthook failure is non-fatal
            assert result.returncode == 0, f"stderr: {result.stderr}"
            assert "WARNING" in result.stderr
            assert "lefthook install failed" in result.stderr
        finally:
            if worktree_path.is_dir():
                subprocess.run(
                    ["git", "worktree", "remove", "--force", str(worktree_path)],
                    cwd=str(git_repo),
                    capture_output=True,
                )
            if worktree_parent.is_dir() and not any(worktree_parent.iterdir()):
                worktree_parent.rmdir()

    def test_lefthook_install_not_called_without_config(
        self, git_repo: Path, tmp_path: Path
    ) -> None:
        """lefthook install is NOT called when lefthook.yml is absent."""
        # Deliberately do NOT create lefthook.yml

        fake_bin = tmp_path / "fake_bin"
        fake_bin.mkdir()
        called_marker = tmp_path / "lefthook_called"
        fake_lefthook = fake_bin / "lefthook"
        fake_lefthook.write_text(f"#!/bin/sh\ntouch {called_marker}\nexit 0\n")
        fake_lefthook.chmod(0o755)

        git_path = shutil.which("git")
        assert git_path is not None
        (fake_bin / "git").symlink_to(git_path)

        worktree_parent = git_repo.parent / f"{git_repo.name}_worktrees"
        worktree_path = worktree_parent / "no-lh"

        try:
            env = self._make_env_with_fake_bin(tmp_path, fake_bin)
            result = run_hook({"name": "no-lh"}, cwd=git_repo, env=env)

            assert result.returncode == 0, f"stderr: {result.stderr}"
            assert not called_marker.exists(), (
                "lefthook install was called even though lefthook.yml is absent"
            )
            assert "lefthook" not in result.stderr.lower()
        finally:
            if worktree_path.is_dir():
                subprocess.run(
                    ["git", "worktree", "remove", "--force", str(worktree_path)],
                    cwd=str(git_repo),
                    capture_output=True,
                )
            if worktree_parent.is_dir() and not any(worktree_parent.iterdir()):
                worktree_parent.rmdir()


# ---------------------------------------------------------------------------
# _cleanup() atexit handler tests
# ---------------------------------------------------------------------------


class TestCleanup:
    """Test the _cleanup() atexit handler with various flag combinations."""

    @pytest.fixture()
    def worktree_mod(self):
        """Import the worktree-create script as a module.

        The script has no .py extension so we use SourceFileLoader directly
        rather than spec_from_file_location (which relies on extension sniffing).
        """
        import importlib.machinery
        import importlib.util

        loader = importlib.machinery.SourceFileLoader("worktree_create", str(SCRIPT))
        spec = importlib.util.spec_from_loader("worktree_create", loader)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_cleanup_noop_when_not_registered(self, worktree_mod, capsys) -> None:
        """_cleanup does nothing when _cleanup_registered is False."""
        worktree_mod._cleanup_registered = False
        worktree_mod._cleanup()
        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err == ""

    def test_cleanup_warns_on_missing_repo_root(
        self, worktree_mod, capsys, tmp_path
    ) -> None:
        """_cleanup warns when _repo_root is None."""
        worktree_mod._cleanup_registered = True
        worktree_mod._repo_root = None
        worktree_mod._is_jj = False
        worktree_mod._workspace_created = False
        worktree_mod._worktree_path = None
        worktree_mod._worktree_parent = None
        worktree_mod._cleanup()
        captured = capsys.readouterr()
        assert "REPO_ROOT" in captured.err
        assert "missing" in captured.err

    def test_cleanup_jj_no_jj_installed_workspace_created_warns(
        self, worktree_mod, capsys, tmp_path
    ) -> None:
        """_cleanup warns about leaked jj workspace when jj not installed and workspace was created."""
        import unittest.mock

        worktree_mod._cleanup_registered = True
        worktree_mod._repo_root = tmp_path
        worktree_mod._is_jj = True
        worktree_mod._workspace_created = True
        worktree_mod._parent_created = True
        worktree_mod._name = "test-ws"
        worktree_mod._worktree_path = None
        worktree_mod._worktree_parent = None
        with unittest.mock.patch("shutil.which", return_value=None):
            worktree_mod._cleanup()
        captured = capsys.readouterr()
        assert "jj not installed" in captured.err
        assert "worktree-test-ws" in captured.err

    def test_cleanup_jj_workspace_forget_fails_errors(
        self, worktree_mod, capsys, tmp_path
    ) -> None:
        """_cleanup errors when jj workspace forget fails with jj installed."""
        import unittest.mock

        worktree_mod._cleanup_registered = True
        worktree_mod._repo_root = tmp_path
        worktree_mod._is_jj = True
        worktree_mod._workspace_created = True
        worktree_mod._parent_created = True
        worktree_mod._name = "test-ws"
        worktree_mod._worktree_path = None
        worktree_mod._worktree_parent = None

        fail_result = unittest.mock.MagicMock()
        fail_result.returncode = 1
        fail_result.stderr = "error: workspace not found"

        with unittest.mock.patch("shutil.which", return_value="/usr/bin/jj"):
            with unittest.mock.patch.object(
                worktree_mod, "run_cmd", return_value=fail_result
            ) as mock_run:
                worktree_mod._cleanup()

        mock_run.assert_called_once_with(
            ["jj", "--no-pager", "workspace", "forget", "worktree-test-ws"],
            cwd=tmp_path,
        )
        captured = capsys.readouterr()
        assert "ERROR" in captured.err
        assert "jj workspace forget" in captured.err
        assert "worktree-test-ws" in captured.err

    def test_cleanup_jj_no_parent_created_noop(
        self, worktree_mod, capsys, tmp_path
    ) -> None:
        """_cleanup skips jj forget when parent directory was never created."""
        worktree_mod._cleanup_registered = True
        worktree_mod._repo_root = tmp_path
        worktree_mod._is_jj = True
        worktree_mod._workspace_created = False
        worktree_mod._parent_created = False
        worktree_mod._name = "test-ws"
        worktree_mod._worktree_path = None
        worktree_mod._worktree_parent = None
        worktree_mod._cleanup()
        captured = capsys.readouterr()
        # No error — parent mkdir failed before any workspace creation
        assert "ERROR" not in captured.err

    def test_cleanup_jj_no_jj_installed_no_workspace_info(
        self, worktree_mod, capsys, tmp_path
    ) -> None:
        """_cleanup prints INFO when jj not installed and no workspace was registered."""
        import unittest.mock

        worktree_mod._cleanup_registered = True
        worktree_mod._repo_root = tmp_path
        worktree_mod._is_jj = True
        worktree_mod._workspace_created = False
        worktree_mod._parent_created = True
        worktree_mod._name = "test-ws"
        worktree_mod._worktree_path = None
        worktree_mod._worktree_parent = None
        with unittest.mock.patch("shutil.which", return_value=None):
            worktree_mod._cleanup()
        captured = capsys.readouterr()
        assert "no workspace was registered" in captured.err
        assert "no cleanup needed" in captured.err

    def test_cleanup_git_workspace_created_removes_worktree(
        self, worktree_mod, capsys, tmp_path
    ) -> None:
        """_cleanup calls git worktree remove when workspace was created in a git repo."""
        import unittest.mock

        worktree_path = tmp_path / "worktree-test"
        worktree_path.mkdir()
        fake_result = unittest.mock.MagicMock()
        fake_result.returncode = 0

        worktree_mod._cleanup_registered = True
        worktree_mod._repo_root = tmp_path
        worktree_mod._is_jj = False
        worktree_mod._workspace_created = True
        worktree_mod._worktree_path = worktree_path
        worktree_mod._worktree_parent = None

        with unittest.mock.patch.object(
            worktree_mod, "run_cmd", return_value=fake_result
        ) as mock_run:
            worktree_mod._cleanup()

        mock_run.assert_called_once_with(
            ["git", "worktree", "remove", "--force", str(worktree_path)],
            cwd=tmp_path,
        )
        captured = capsys.readouterr()
        assert "WARNING" not in captured.err

    def test_cleanup_git_worktree_remove_failure_prunes(
        self, worktree_mod, capsys, tmp_path
    ) -> None:
        """_cleanup falls back to git worktree prune when remove fails."""
        import unittest.mock

        worktree_path = tmp_path / "worktree-test"
        worktree_path.mkdir()
        fail_result = unittest.mock.MagicMock()
        fail_result.returncode = 1
        fail_result.stderr = "error: failed to remove worktree"
        ok_result = unittest.mock.MagicMock()
        ok_result.returncode = 0

        worktree_mod._cleanup_registered = True
        worktree_mod._repo_root = tmp_path
        worktree_mod._is_jj = False
        worktree_mod._workspace_created = True
        worktree_mod._worktree_path = worktree_path
        worktree_mod._worktree_parent = None

        with unittest.mock.patch.object(
            worktree_mod, "run_cmd", side_effect=[fail_result, ok_result]
        ) as mock_run:
            worktree_mod._cleanup()

        assert mock_run.call_count == 2
        mock_run.assert_any_call(
            ["git", "worktree", "remove", "--force", str(worktree_path)],
            cwd=tmp_path,
        )
        mock_run.assert_any_call(["git", "worktree", "prune"], cwd=tmp_path)
        captured = capsys.readouterr()
        assert "WARNING" in captured.err
        assert "git worktree remove failed" in captured.err

    def test_cleanup_git_worktree_remove_and_prune_both_fail(
        self, worktree_mod, capsys, tmp_path
    ) -> None:
        """_cleanup emits two WARNINGs when both git worktree remove and prune fail."""
        import unittest.mock

        worktree_path = tmp_path / "worktree-test"
        worktree_path.mkdir()
        fail_result = unittest.mock.MagicMock()
        fail_result.returncode = 1
        fail_result.stderr = "error: remove failed"

        worktree_mod._cleanup_registered = True
        worktree_mod._repo_root = tmp_path
        worktree_mod._is_jj = False
        worktree_mod._workspace_created = True
        worktree_mod._worktree_path = worktree_path
        worktree_mod._worktree_parent = None

        with unittest.mock.patch.object(
            worktree_mod, "run_cmd", side_effect=[fail_result, fail_result]
        ):
            worktree_mod._cleanup()

        captured = capsys.readouterr()
        assert captured.err.count("WARNING") == 2
        assert "git worktree remove failed" in captured.err
        assert "git worktree prune also failed" in captured.err

    def test_cleanup_git_partial_create_prunes(
        self, worktree_mod, capsys, tmp_path
    ) -> None:
        """_cleanup calls git worktree prune for partial creation (no workspace registered)."""
        import unittest.mock

        ok_result = unittest.mock.MagicMock()
        ok_result.returncode = 0

        worktree_mod._cleanup_registered = True
        worktree_mod._repo_root = tmp_path
        worktree_mod._is_jj = False
        worktree_mod._workspace_created = False
        worktree_mod._worktree_path = None
        worktree_mod._worktree_parent = None

        with unittest.mock.patch.object(
            worktree_mod, "run_cmd", return_value=ok_result
        ) as mock_run:
            worktree_mod._cleanup()

        mock_run.assert_called_once_with(["git", "worktree", "prune"], cwd=tmp_path)
        captured = capsys.readouterr()
        assert "WARNING" not in captured.err

    def test_cleanup_rmtree_failure_warns(self, worktree_mod, capsys, tmp_path) -> None:
        """_cleanup emits WARNING when shutil.rmtree raises OSError."""
        import shutil
        import unittest.mock

        worktree_path = tmp_path / "worktree-test"
        ok_result = unittest.mock.MagicMock()
        ok_result.returncode = 0

        worktree_mod._cleanup_registered = True
        worktree_mod._repo_root = tmp_path
        worktree_mod._is_jj = False
        worktree_mod._workspace_created = True
        worktree_mod._worktree_path = worktree_path
        worktree_mod._worktree_parent = None

        with unittest.mock.patch.object(
            worktree_mod, "run_cmd", return_value=ok_result
        ):
            with unittest.mock.patch.object(
                shutil, "rmtree", side_effect=OSError("permission denied")
            ):
                worktree_mod._cleanup()

        captured = capsys.readouterr()
        assert "WARNING" in captured.err
        assert "cleanup failed" in captured.err
