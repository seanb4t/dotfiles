# Hook Python Migration Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents
> available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`)
> syntax for tracking.

**Goal:** Migrate `.claude/hooks/` bash scripts (worktree-create.sh, worktree-remove.sh,
worktree-helpers.sh, post-edit-format.sh) to standalone uv-based Python scripts with pytest tests.

**Architecture:** Extensionless uv scripts with `#!/usr/bin/env -S uv run --script` shebang.
Shared logic in `worktree_helpers.py` (imported via sys.path). Tests in `tests/` subdirectory
using pytest with subprocess mocking for unit tests and real git repos for integration tests.

**Tech Stack:** Python 3.11+ (stdlib only), uv (script runner), pytest (test runner)

**Spec:** `docs/superpowers/specs/2026-03-11-hook-python-migration-design.md`

---

## File Structure

```text
.claude/hooks/
  worktree-create          # NEW: uv script replacing worktree-create.sh
  worktree-remove          # NEW: uv script replacing worktree-remove.sh
  post-edit-format         # NEW: uv script replacing post-edit-format.sh
  worktree_helpers.py      # NEW: shared module (sanitize, validate, detect_repo_root)
  worktree-create.sh       # EXISTING: kept during migration, deleted in final task
  worktree-remove.sh       # EXISTING: kept during migration, deleted in final task
  worktree-helpers.sh      # EXISTING: kept during migration, deleted in final task
  post-edit-format.sh      # EXISTING: kept during migration, deleted in final task
  tests/
    conftest.py            # NEW: shared pytest fixtures
    test_worktree_helpers.py  # NEW
    test_worktree_create.py   # NEW
    test_worktree_remove.py   # NEW
    test_post_edit_format.py  # NEW
```

**Responsibility boundaries:**

| File | Responsibility |
|------|---------------|
| `worktree_helpers.py` | Pure functions for sanitization, validation, VCS detection, subprocess wrapper |
| `worktree-create` | Stdin JSON parsing, orchestration of create flow, atexit cleanup |
| `worktree-remove` | Stdin JSON parsing, orchestration of remove flow, temp file management |
| `post-edit-format` | Stdin JSON parsing, formatter dispatch (ruff/rumdl) |
| `tests/conftest.py` | `git_repo`, `jj_repo`, `mock_stdin`, `mock_run_cmd` fixtures |

---

## Chunk 1: Shared Helpers and Tests

### Task 1: Create `worktree_helpers.py` — `sanitize_for_output`

**Files:**

- Create: `.claude/hooks/worktree_helpers.py`
- Create: `.claude/hooks/tests/__init__.py`
- Create: `.claude/hooks/tests/test_worktree_helpers.py`

- [ ] **Step 1: Write the failing test for `sanitize_for_output`**

In `.claude/hooks/tests/test_worktree_helpers.py`:

```python
"""Tests for worktree_helpers module."""

import sys
from pathlib import Path

# Add hooks dir to path so we can import worktree_helpers
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from worktree_helpers import sanitize_for_output


class TestSanitizeForOutput:
    def test_passthrough_normal_text(self):
        assert sanitize_for_output("hello world") == "hello world"

    def test_preserves_tab_newline_cr(self):
        assert sanitize_for_output("line1\tval\nline2\r") == "line1\tval\nline2\r"

    def test_strips_null_byte(self):
        assert sanitize_for_output("ab\x00cd") == "abcd"

    def test_strips_bell(self):
        assert sanitize_for_output("ab\x07cd") == "abcd"

    def test_strips_escape(self):
        assert sanitize_for_output("ab\x1bcd") == "abcd"

    def test_strips_del(self):
        assert sanitize_for_output("ab\x7fcd") == "abcd"

    def test_strips_c1_control_chars(self):
        # C1 range: 0x80-0x9F
        assert sanitize_for_output("ab\x80\x9fcd") == "abcd"

    def test_preserves_unicode_above_c1(self):
        assert sanitize_for_output("caf\u00e9") == "caf\u00e9"

    def test_empty_string(self):
        assert sanitize_for_output("") == ""
```

- [ ] **Step 2: Create minimal `worktree_helpers.py` and run test to verify it fails**

Create `.claude/hooks/worktree_helpers.py`:

```python
"""Shared helpers for worktree hook scripts.

Functions:
    sanitize_for_output(s)       -- strip control chars for safe logging
    validate_safe_name(name, label) -- reject path traversal/metacharacters
    cleanup_empty_parent(parent) -- rmdir if empty after worktree removal
    detect_repo_root()           -- find repo root via git or jj
    run_cmd(args, *, cwd)        -- thin subprocess wrapper for git/jj CLI
"""

from __future__ import annotations


def sanitize_for_output(s: str) -> str:
    """Strip control characters for safe logging output.

    Removes C0 control chars (0x00-0x1F) except tab/newline/CR,
    DEL (0x7F), and C1 control chars (0x80-0x9F).
    """
    raise NotImplementedError
```

Create `.claude/hooks/tests/__init__.py` (empty file).

Run: `cd /Volumes/Code/github.com/fzymgc-house/fzymgc-house-skills && python -m pytest .claude/hooks/tests/test_worktree_helpers.py::TestSanitizeForOutput -v`
Expected: FAIL with `NotImplementedError`

- [ ] **Step 3: Implement `sanitize_for_output`**

Replace the function body in `.claude/hooks/worktree_helpers.py`:

```python
def sanitize_for_output(s: str) -> str:
    """Strip control characters for safe logging output.

    Removes C0 control chars (0x00-0x1F) except tab/newline/CR,
    DEL (0x7F), and C1 control chars (0x80-0x9F).
    """
    # Match bash: tr -d '\000-\010\013\014\016-\037\177\200-\237'
    return "".join(
        c
        for c in s
        if not (
            (0x00 <= ord(c) <= 0x08)       # C0 below tab
            or ord(c) == 0x0B              # vertical tab
            or ord(c) == 0x0C              # form feed
            or (0x0E <= ord(c) <= 0x1F)    # C0 above CR
            or ord(c) == 0x7F              # DEL
            or (0x80 <= ord(c) <= 0x9F)    # C1
        )
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Volumes/Code/github.com/fzymgc-house/fzymgc-house-skills && python -m pytest .claude/hooks/tests/test_worktree_helpers.py::TestSanitizeForOutput -v`
Expected: All 9 tests PASS

- [ ] **Step 5: Commit**

```bash
git add .claude/hooks/worktree_helpers.py .claude/hooks/tests/__init__.py .claude/hooks/tests/test_worktree_helpers.py
git commit -m "feat(hooks): add sanitize_for_output in worktree_helpers.py with tests"
```

---

### Task 2: Add `validate_safe_name` to `worktree_helpers.py`

**Files:**

- Modify: `.claude/hooks/worktree_helpers.py`
- Modify: `.claude/hooks/tests/test_worktree_helpers.py`

- [ ] **Step 1: Write the failing tests for `validate_safe_name`**

Append to `.claude/hooks/tests/test_worktree_helpers.py`:

```python
import pytest
from worktree_helpers import validate_safe_name


class TestValidateSafeName:
    def test_valid_alphanumeric(self):
        validate_safe_name("my-worktree", "worktree name")  # should not raise

    def test_valid_with_dots_underscores(self):
        validate_safe_name("agent_1.2", "name")  # should not raise

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            validate_safe_name("", "worktree name")

    def test_leading_dot_raises(self):
        with pytest.raises(ValueError, match="no leading dot"):
            validate_safe_name(".hidden", "name")

    def test_trailing_dot_raises(self):
        with pytest.raises(ValueError, match="no.*trailing dot"):
            validate_safe_name("name.", "name")

    def test_double_dot_raises(self):
        with pytest.raises(ValueError, match="double-dot"):
            validate_safe_name("path..traversal", "name")

    def test_slash_raises(self):
        with pytest.raises(ValueError, match="alphanumeric"):
            validate_safe_name("path/traversal", "name")

    def test_space_raises(self):
        with pytest.raises(ValueError, match="alphanumeric"):
            validate_safe_name("has space", "name")

    def test_shell_metachar_raises(self):
        with pytest.raises(ValueError, match="alphanumeric"):
            validate_safe_name("name;rm -rf", "name")

    def test_control_chars_in_label_sanitized(self):
        with pytest.raises(ValueError, match="must not be empty"):
            validate_safe_name("", "bad\x07label")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Volumes/Code/github.com/fzymgc-house/fzymgc-house-skills && python -m pytest .claude/hooks/tests/test_worktree_helpers.py::TestValidateSafeName -v`
Expected: FAIL — `validate_safe_name` not defined

- [ ] **Step 3: Implement `validate_safe_name`**

Add to `.claude/hooks/worktree_helpers.py`:

```python
import re

def validate_safe_name(name: str, label: str) -> None:
    """Validate a name contains only safe characters.

    Raises ValueError for empty names, path traversal patterns,
    or characters outside [a-zA-Z0-9_.-].
    """
    if not name:
        raise ValueError(f"{sanitize_for_output(label)} must not be empty")

    # Match bash regex: [^a-zA-Z0-9_.-] || starts-with-dot || double-dot || ends-with-dot
    if (
        re.search(r"[^a-zA-Z0-9_.\-]", name)
        or name.startswith(".")
        or ".." in name
        or name.endswith(".")
    ):
        safe_name = sanitize_for_output(name)
        safe_label = sanitize_for_output(label)
        raise ValueError(
            f"invalid {safe_label} '{safe_name}' "
            "(alphanumeric, dots, hyphens, underscores only; "
            "no leading dot, trailing dot, or double-dot)"
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Volumes/Code/github.com/fzymgc-house/fzymgc-house-skills && python -m pytest .claude/hooks/tests/test_worktree_helpers.py::TestValidateSafeName -v`
Expected: All 10 tests PASS

- [ ] **Step 5: Commit**

```bash
git add .claude/hooks/worktree_helpers.py .claude/hooks/tests/test_worktree_helpers.py
git commit -m "feat(hooks): add validate_safe_name to worktree_helpers.py with tests"
```

---

### Task 3: Add `run_cmd` and `detect_repo_root` to `worktree_helpers.py`

**Files:**

- Modify: `.claude/hooks/worktree_helpers.py`
- Create: `.claude/hooks/tests/conftest.py`
- Modify: `.claude/hooks/tests/test_worktree_helpers.py`

- [ ] **Step 1: Write `conftest.py` with shared fixtures**

Create `.claude/hooks/tests/conftest.py`:

```python
"""Shared pytest fixtures for hook tests."""

from __future__ import annotations

import io
import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.fixture()
def git_repo(tmp_path: Path) -> Path:
    """Create a minimal git repo with one commit."""
    subprocess.run(
        ["git", "init", str(tmp_path)],
        check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit",
         "--allow-empty", "-m", "initial"],
        check=True, capture_output=True,
        env={**__import__("os").environ,
             "GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "t@t",
             "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "t@t"},
    )
    return tmp_path


@pytest.fixture()
def mock_stdin(monkeypatch):
    """Return a helper that patches sys.stdin with JSON data."""
    def _set(data: dict):
        monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(data)))
    return _set
```

- [ ] **Step 2: Write the failing tests for `run_cmd` and `detect_repo_root`**

Append to `.claude/hooks/tests/test_worktree_helpers.py`:

```python
import subprocess
from pathlib import Path
from unittest.mock import patch

from worktree_helpers import run_cmd, detect_repo_root


class TestRunCmd:
    def test_success_returns_stdout(self, tmp_path):
        result = run_cmd(["echo", "hello"], cwd=tmp_path)
        assert result.stdout.strip() == "hello"

    def test_captures_stderr(self, tmp_path):
        result = run_cmd(
            ["python3", "-c", "import sys; sys.stderr.write('err')"],
            cwd=tmp_path,
        )
        assert result.stderr == "err"

    def test_does_not_raise_on_failure(self, tmp_path):
        result = run_cmd(["false"], cwd=tmp_path)
        assert result.returncode != 0


class TestDetectRepoRoot:
    def test_git_repo(self, git_repo):
        root = detect_repo_root(cwd=git_repo)
        assert root == git_repo.resolve()

    def test_no_repo_raises(self, tmp_path):
        with pytest.raises(RuntimeError, match="not inside a git/jj repository"):
            detect_repo_root(cwd=tmp_path)

    def test_git_repo_from_subdirectory(self, git_repo):
        sub = git_repo / "sub" / "dir"
        sub.mkdir(parents=True)
        root = detect_repo_root(cwd=sub)
        assert root == git_repo.resolve()
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd /Volumes/Code/github.com/fzymgc-house/fzymgc-house-skills && python -m pytest .claude/hooks/tests/test_worktree_helpers.py::TestRunCmd .claude/hooks/tests/test_worktree_helpers.py::TestDetectRepoRoot -v`
Expected: FAIL — functions not defined

- [ ] **Step 4: Implement `run_cmd` and `detect_repo_root`**

Add to `.claude/hooks/worktree_helpers.py`:

```python
import subprocess
import shutil
from pathlib import Path


def run_cmd(
    args: list[str],
    *,
    cwd: Path | str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a command and return the result. Does not raise on failure."""
    return subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def detect_repo_root(*, cwd: Path | str | None = None) -> Path:
    """Find repo root via git rev-parse or jj root.

    Tries git first (works for plain git and colocated jj repos),
    then falls back to jj root for pure jj repos.

    Raises RuntimeError if neither succeeds.
    """
    # Try git first
    result = run_cmd(["git", "rev-parse", "--show-toplevel"], cwd=cwd)
    if result.returncode == 0 and result.stdout.strip():
        root = Path(result.stdout.strip())
        if root.is_dir():
            return root.resolve()

    # Try jj root for non-colocated jj repos
    jj_attempted = False
    jj_err = "(not run)"
    if shutil.which("jj"):
        jj_attempted = True
        jj_result = run_cmd(["jj", "root"], cwd=cwd)
        jj_err = jj_result.stderr.strip()
        if jj_result.returncode == 0 and jj_result.stdout.strip():
            jj_root = Path(jj_result.stdout.strip())
            if jj_root.is_dir():
                return jj_root.resolve()

        # jj was found but failed
        if jj_result.returncode != 0:
            detail = f"; jj: {sanitize_for_output(jj_err)}" if jj_err else ""
            raise RuntimeError(
                f"not inside a git/jj repository "
                f"(git rev-parse and jj root both failed{detail})"
            )
        if not jj_result.stdout.strip():
            raise RuntimeError(
                "not inside a git/jj repository "
                "(git rev-parse failed; jj root returned empty output)"
            )
        jj_root_str = jj_result.stdout.strip()
        raise RuntimeError(
            f"not inside a git/jj repository "
            f"(git rev-parse failed; jj root returned "
            f"'{sanitize_for_output(jj_root_str)}' but directory does not exist)"
        )

    # jj not in PATH
    raise RuntimeError(
        "not inside a git/jj repository "
        "(git rev-parse failed; jj not in PATH)"
    )
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /Volumes/Code/github.com/fzymgc-house/fzymgc-house-skills && python -m pytest .claude/hooks/tests/test_worktree_helpers.py::TestRunCmd .claude/hooks/tests/test_worktree_helpers.py::TestDetectRepoRoot -v`
Expected: All 6 tests PASS

- [ ] **Step 6: Commit**

```bash
git add .claude/hooks/worktree_helpers.py .claude/hooks/tests/conftest.py .claude/hooks/tests/test_worktree_helpers.py
git commit -m "feat(hooks): add run_cmd and detect_repo_root to worktree_helpers.py"
```

---

### Task 4: Add `cleanup_empty_parent` to `worktree_helpers.py`

**Files:**

- Modify: `.claude/hooks/worktree_helpers.py`
- Modify: `.claude/hooks/tests/test_worktree_helpers.py`

- [ ] **Step 1: Write the failing tests**

Append to `.claude/hooks/tests/test_worktree_helpers.py`:

```python
from worktree_helpers import cleanup_empty_parent


class TestCleanupEmptyParent:
    def test_removes_empty_directory(self, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        cleanup_empty_parent(empty)
        assert not empty.exists()

    def test_preserves_nonempty_directory(self, tmp_path):
        nonempty = tmp_path / "nonempty"
        nonempty.mkdir()
        (nonempty / "file.txt").write_text("x")
        cleanup_empty_parent(nonempty)
        assert nonempty.exists()

    def test_nonexistent_is_noop(self, tmp_path):
        cleanup_empty_parent(tmp_path / "nonexistent")  # should not raise

    def test_path_as_string(self, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        cleanup_empty_parent(str(empty))
        assert not empty.exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Volumes/Code/github.com/fzymgc-house/fzymgc-house-skills && python -m pytest .claude/hooks/tests/test_worktree_helpers.py::TestCleanupEmptyParent -v`
Expected: FAIL — `cleanup_empty_parent` not defined

- [ ] **Step 3: Implement `cleanup_empty_parent`**

Add to `.claude/hooks/worktree_helpers.py`:

```python
import sys


def cleanup_empty_parent(parent: Path | str) -> None:
    """Remove parent directory if it exists and is empty.

    Safe to call even if the directory does not exist.
    Warns on stderr if rmdir fails.
    """
    parent = Path(parent)
    if not parent.is_dir():
        return
    try:
        entries = list(parent.iterdir())
    except OSError:
        print(
            f"WARNING: could not list parent directory "
            f"'{sanitize_for_output(str(parent))}' -- skipping rmdir",
            file=sys.stderr,
        )
        return
    if not entries:
        try:
            parent.rmdir()
        except OSError as e:
            print(
                f"WARNING: failed to remove empty parent "
                f"'{sanitize_for_output(str(parent))}': "
                f"{sanitize_for_output(str(e)[:500])}",
                file=sys.stderr,
            )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Volumes/Code/github.com/fzymgc-house/fzymgc-house-skills && python -m pytest .claude/hooks/tests/test_worktree_helpers.py::TestCleanupEmptyParent -v`
Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add .claude/hooks/worktree_helpers.py .claude/hooks/tests/test_worktree_helpers.py
git commit -m "feat(hooks): add cleanup_empty_parent to worktree_helpers.py"
```

---

## Chunk 2: `post-edit-format` Script and Tests

### Task 5: Create `post-edit-format` uv script

**Files:**

- Create: `.claude/hooks/post-edit-format`
- Create: `.claude/hooks/tests/test_post_edit_format.py`

This is the simplest hook — good to migrate first as a proof of concept.

- [ ] **Step 1: Write the failing tests**

Create `.claude/hooks/tests/test_post_edit_format.py`:

```python
"""Tests for post-edit-format hook."""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import call, patch

import pytest

# Import the module under test by running it as a module
HOOK_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOK_DIR))


def run_hook(stdin_data: dict, hook_dir: Path = HOOK_DIR) -> subprocess.CompletedProcess:
    """Run post-edit-format as a subprocess with JSON on stdin."""
    return subprocess.run(
        [sys.executable, str(hook_dir / "post-edit-format")],
        input=json.dumps(stdin_data),
        capture_output=True,
        text=True,
    )


class TestPostEditFormat:
    def test_python_file_runs_ruff(self, tmp_path):
        py_file = tmp_path / "test.py"
        py_file.write_text("x=1\n")
        result = run_hook({"tool_input": {"file_path": str(py_file)}})
        assert result.returncode == 0

    def test_markdown_file_runs_rumdl(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("# Hello\n")
        result = run_hook({"tool_input": {"file_path": str(md_file)}})
        assert result.returncode == 0

    def test_unknown_extension_exits_zero(self, tmp_path):
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("hello\n")
        result = run_hook({"tool_input": {"file_path": str(txt_file)}})
        assert result.returncode == 0

    def test_missing_file_exits_zero(self):
        result = run_hook({"tool_input": {"file_path": "/nonexistent/file.py"}})
        assert result.returncode == 0

    def test_empty_input_exits_zero(self):
        result = run_hook({})
        assert result.returncode == 0

    def test_no_file_path_exits_zero(self):
        result = run_hook({"tool_input": {}})
        assert result.returncode == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Volumes/Code/github.com/fzymgc-house/fzymgc-house-skills && python -m pytest .claude/hooks/tests/test_post_edit_format.py -v`
Expected: FAIL — file not found

- [ ] **Step 3: Implement `post-edit-format`**

Create `.claude/hooks/post-edit-format`:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
"""PostToolUse hook: auto-format edited files.

Reads hook JSON from stdin, extracts file_path, runs appropriate formatter.
Always exits 0 (formatting is best-effort).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return

    file_path = (data.get("tool_input") or {}).get("file_path", "")
    if not file_path or not Path(file_path).is_file():
        return

    suffix = Path(file_path).suffix

    if suffix == ".py":
        subprocess.run(
            ["ruff", "check", "--fix", "--quiet", file_path],
            capture_output=True,
        )
        subprocess.run(
            ["ruff", "format", "--quiet", file_path],
            capture_output=True,
        )
    elif suffix == ".md":
        subprocess.run(
            ["rumdl", "check", "--fix", file_path],
            capture_output=True,
        )


if __name__ == "__main__":
    main()
```

Make executable: `chmod +x .claude/hooks/post-edit-format`

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Volumes/Code/github.com/fzymgc-house/fzymgc-house-skills && python -m pytest .claude/hooks/tests/test_post_edit_format.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add .claude/hooks/post-edit-format .claude/hooks/tests/test_post_edit_format.py
git commit -m "feat(hooks): add post-edit-format Python uv script with tests"
```

---

## Chunk 3: `worktree-create` Script and Tests

### Task 6: Create `worktree-create` uv script

**Files:**

- Create: `.claude/hooks/worktree-create`
- Create: `.claude/hooks/tests/test_worktree_create.py`

- [ ] **Step 1: Write the failing tests**

Create `.claude/hooks/tests/test_worktree_create.py`:

```python
"""Tests for worktree-create hook."""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

HOOK_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOK_DIR))


def run_hook(stdin_data: dict, env: dict | None = None) -> subprocess.CompletedProcess:
    """Run worktree-create as a subprocess with JSON on stdin."""
    import os
    run_env = {**os.environ, **(env or {})}
    return subprocess.run(
        [sys.executable, str(HOOK_DIR / "worktree-create")],
        input=json.dumps(stdin_data),
        capture_output=True,
        text=True,
        env=run_env,
    )


class TestWorktreeCreateInputValidation:
    def test_no_name_exits_1(self):
        result = run_hook({})
        assert result.returncode == 1
        assert "no worktree name" in result.stderr.lower()

    def test_empty_name_exits_1(self):
        result = run_hook({"name": ""})
        assert result.returncode == 1

    def test_path_traversal_exits_1(self):
        result = run_hook({"name": "../escape"})
        assert result.returncode == 1
        assert "invalid" in result.stderr.lower() or "alphanumeric" in result.stderr.lower()

    def test_shell_metachar_exits_1(self):
        result = run_hook({"name": "test;rm"})
        assert result.returncode == 1


class TestWorktreeCreateGitIntegration:
    """Integration tests using real git repos."""

    def test_creates_worktree_in_sibling_dir(self, git_repo):
        """Run worktree-create in a real git repo, verify worktree is created."""
        result = subprocess.run(
            [sys.executable, str(HOOK_DIR / "worktree-create")],
            input=json.dumps({"name": "test-wt"}),
            capture_output=True,
            text=True,
            cwd=str(git_repo),
        )
        assert result.returncode == 0
        worktree_path = result.stdout.strip()
        assert worktree_path.endswith("test-wt")
        assert Path(worktree_path).is_dir()

        # Verify it's registered as a git worktree
        wt_list = subprocess.run(
            ["git", "worktree", "list"],
            capture_output=True, text=True, cwd=str(git_repo),
        )
        assert "test-wt" in wt_list.stdout

        # Cleanup
        subprocess.run(
            ["git", "worktree", "remove", "--force", worktree_path],
            capture_output=True, cwd=str(git_repo),
        )
        parent = Path(worktree_path).parent
        if parent.is_dir() and not list(parent.iterdir()):
            parent.rmdir()

    def test_worktree_parent_is_sibling(self, git_repo):
        """Verify worktree parent is <repo>_worktrees/ (sibling, not nested)."""
        result = subprocess.run(
            [sys.executable, str(HOOK_DIR / "worktree-create")],
            input=json.dumps({"name": "sibling-check"}),
            capture_output=True,
            text=True,
            cwd=str(git_repo),
        )
        assert result.returncode == 0
        wt_path = Path(result.stdout.strip())
        assert wt_path.parent.name == f"{git_repo.name}_worktrees"
        assert wt_path.parent.parent == git_repo.parent

        # Cleanup
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(wt_path)],
            capture_output=True, cwd=str(git_repo),
        )
        if wt_path.parent.is_dir() and not list(wt_path.parent.iterdir()):
            wt_path.parent.rmdir()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Volumes/Code/github.com/fzymgc-house/fzymgc-house-skills && python -m pytest .claude/hooks/tests/test_worktree_create.py -v`
Expected: FAIL — script not found

- [ ] **Step 3: Implement `worktree-create`**

Create `.claude/hooks/worktree-create`:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
"""WorktreeCreate hook: create worktrees in sibling directory.

Input:  JSON on stdin with "name" field
Output: worktree path printed to stdout (framework reads this)

Behavior:
  1. Validate name (reject path traversal, shell metacharacters, empty)
  2. Detect repo root via git rev-parse or jj root
  3. Create parent dir: <repo-parent>/<repo-name>_worktrees/
  4. VCS-aware workspace creation:
     - jj repos (.jj/): jj workspace add --name worktree-<name>
     - git repos: git worktree add -b worktree/<name>
  5. Install git hooks (lefthook) if configured
  6. Print worktree path to stdout

Cleanup: atexit handler reverts partial state on failure (VCS deregistration,
         directory removal). Uses parent_created and workspace_created flags
         to avoid cleaning up resources that were never created.
"""

from __future__ import annotations

import atexit
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from worktree_helpers import (
    cleanup_empty_parent,
    detect_repo_root,
    run_cmd,
    sanitize_for_output,
    validate_safe_name,
)

# State flags for cleanup
_parent_created = False
_workspace_created = False
_cleanup_registered = False
_repo_root: Path | None = None
_worktree_path: Path | None = None
_worktree_parent: Path | None = None
_name: str = ""


def _cleanup_on_error() -> None:
    """Revert partial state on failure."""
    global _cleanup_registered
    if not _cleanup_registered:
        return

    cleanup_failed = False

    if _repo_root and not _repo_root.is_dir():
        print(
            f"WARNING: cleanup: REPO_ROOT "
            f"'{sanitize_for_output(str(_repo_root))}' missing "
            f"-- VCS workspace cleanup skipped",
            file=sys.stderr,
        )
    elif _repo_root and (_repo_root / ".jj").is_dir():
        # jj repo cleanup
        if not _parent_created:
            pass  # mkdir never succeeded, nothing to forget
        elif shutil.which("jj"):
            result = run_cmd(
                ["jj", "workspace", "forget", f"worktree-{_name}"],
                cwd=_repo_root,
            )
            if result.returncode != 0:
                if _workspace_created:
                    print(
                        f"ERROR: cleanup: jj workspace forget worktree-{_name} "
                        f"failed -- workspace metadata may be leaked: "
                        f"{sanitize_for_output(result.stderr[:500])}",
                        file=sys.stderr,
                    )
                    cleanup_failed = True
                else:
                    print(
                        f"WARNING: cleanup: jj workspace forget worktree-{_name} "
                        f"failed (may not have been registered): "
                        f"{sanitize_for_output(result.stderr[:500])}",
                        file=sys.stderr,
                    )
        else:
            if _workspace_created:
                print(
                    f"ERROR: cleanup: .jj/ found but jj not installed -- "
                    f"workspace 'worktree-{_name}' was created and cannot be "
                    f"cleaned up; run 'jj workspace forget worktree-{_name}' manually",
                    file=sys.stderr,
                )
                cleanup_failed = True
            else:
                print(
                    "INFO: cleanup: .jj/ found but jj not installed -- "
                    "no workspace was registered, no cleanup needed",
                    file=sys.stderr,
                )
    elif _workspace_created and _worktree_path:
        # git repo: remove worktree registration
        result = run_cmd(
            ["git", "worktree", "remove", "--force", str(_worktree_path)],
            cwd=_repo_root,
        )
        if result.returncode != 0:
            print(
                f"WARNING: cleanup: git worktree remove failed: "
                f"{sanitize_for_output(result.stderr[:500])}",
                file=sys.stderr,
            )
            prune = run_cmd(["git", "worktree", "prune"], cwd=_repo_root)
            if prune.returncode != 0:
                print(
                    f"WARNING: cleanup: git worktree prune also failed: "
                    f"{sanitize_for_output(prune.stderr[:500])}",
                    file=sys.stderr,
                )
    elif _repo_root:
        # Partial git worktree add -- prune stale metadata
        prune = run_cmd(["git", "worktree", "prune"], cwd=_repo_root)
        if prune.returncode != 0:
            print(
                f"WARNING: cleanup: git worktree prune failed for partial "
                f"create: {sanitize_for_output(prune.stderr[:500])}",
                file=sys.stderr,
            )

    if _worktree_path and _worktree_path.exists():
        try:
            shutil.rmtree(_worktree_path)
        except OSError as e:
            print(
                f"WARNING: cleanup failed for "
                f"'{sanitize_for_output(str(_worktree_path))}': "
                f"{sanitize_for_output(str(e)[:500])}",
                file=sys.stderr,
            )
            cleanup_failed = True

    if _worktree_parent:
        cleanup_empty_parent(_worktree_parent)


def main() -> int:
    global _parent_created, _workspace_created, _cleanup_registered
    global _repo_root, _worktree_path, _worktree_parent, _name

    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        data = {}

    _name = data.get("name") or ""
    if not _name:
        print("ERROR: no worktree name provided", file=sys.stderr)
        return 1

    try:
        validate_safe_name(_name, "worktree name")
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    try:
        _repo_root = detect_repo_root()
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    repo_name = _repo_root.name
    try:
        validate_safe_name(repo_name, "repository directory name")
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    _worktree_parent = _repo_root.parent / f"{repo_name}_worktrees"
    _worktree_path = _worktree_parent / _name

    # Register cleanup before any state-changing operations
    _cleanup_registered = True
    atexit.register(_cleanup_on_error)

    # Check jj availability before creating directories
    is_jj = (_repo_root / ".jj").is_dir()
    if is_jj and not shutil.which("jj"):
        print(
            "ERROR: .jj/ directory found but jj is not installed",
            file=sys.stderr,
        )
        return 1

    try:
        _worktree_parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(
            f"ERROR: failed to create worktree parent directory "
            f"'{_worktree_parent}': {e}",
            file=sys.stderr,
        )
        return 1
    _parent_created = True

    if is_jj:
        result = run_cmd(
            ["jj", "workspace", "add", str(_worktree_path),
             "--name", f"worktree-{_name}"],
            cwd=_repo_root,
        )
        if result.returncode != 0:
            err = result.stderr + result.stdout
            if "--name" in err.lower() and any(
                w in err.lower() for w in ("unexpected", "unrecognized", "unknown")
            ):
                print(
                    f"ERROR: jj version too old -- 'jj workspace add --name' "
                    f"not supported (jj output: "
                    f"{sanitize_for_output(err[:200])}). Update jj.",
                    file=sys.stderr,
                )
            else:
                print(
                    f"ERROR: jj workspace add failed: "
                    f"{sanitize_for_output(err[:500])}",
                    file=sys.stderr,
                )
            return 1
        _workspace_created = True
    else:
        result = run_cmd(
            ["git", "worktree", "add", str(_worktree_path),
             "-b", f"worktree/{_name}", "HEAD"],
            cwd=_repo_root,
        )
        if result.returncode != 0:
            print(
                f"ERROR: git worktree add failed: "
                f"{sanitize_for_output(result.stderr[:500])}",
                file=sys.stderr,
            )
            return 1
        _workspace_created = True

    # Install lefthook if configured
    if (_repo_root / "lefthook.yml").is_file():
        lh = run_cmd(["lefthook", "install"], cwd=_worktree_path)
        if lh.returncode != 0:
            print(
                f"WARNING: lefthook install failed in worktree: "
                f"{sanitize_for_output(lh.stderr[:500])}",
                file=sys.stderr,
            )

    # Disarm cleanup -- success
    _cleanup_registered = False

    print(_worktree_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Make executable: `chmod +x .claude/hooks/worktree-create`

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Volumes/Code/github.com/fzymgc-house/fzymgc-house-skills && python -m pytest .claude/hooks/tests/test_worktree_create.py -v`
Expected: All 6 tests PASS (4 unit + 2 integration)

- [ ] **Step 5: Commit**

```bash
git add .claude/hooks/worktree-create .claude/hooks/tests/test_worktree_create.py
git commit -m "feat(hooks): add worktree-create Python uv script with tests"
```

---

## Chunk 4: `worktree-remove` Script and Tests

### Task 7: Create `worktree-remove` uv script

**Files:**

- Create: `.claude/hooks/worktree-remove`
- Create: `.claude/hooks/tests/test_worktree_remove.py`

- [ ] **Step 1: Write the failing tests**

Create `.claude/hooks/tests/test_worktree_remove.py`:

```python
"""Tests for worktree-remove hook."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOK_DIR))


def run_hook(stdin_data: dict, cwd: str | Path | None = None) -> subprocess.CompletedProcess:
    """Run worktree-remove as a subprocess with JSON on stdin."""
    return subprocess.run(
        [sys.executable, str(HOOK_DIR / "worktree-remove")],
        input=json.dumps(stdin_data),
        capture_output=True,
        text=True,
        cwd=cwd,
    )


class TestWorktreeRemoveInputValidation:
    def test_no_path_exits_0(self):
        result = run_hook({})
        assert result.returncode == 0
        assert "no path" in result.stderr.lower() or "warning" in result.stderr.lower()

    def test_nonexistent_path_exits_0(self):
        result = run_hook({"path": "/nonexistent/path"})
        assert result.returncode == 0
        assert "already removed" in result.stderr.lower()


class TestWorktreeRemoveGitIntegration:
    """Integration tests: create a worktree, then remove it."""

    def _create_worktree(self, git_repo: Path, name: str) -> Path:
        """Helper: create a git worktree and return its path."""
        wt_parent = git_repo.parent / f"{git_repo.name}_worktrees"
        wt_parent.mkdir(exist_ok=True)
        wt_path = wt_parent / name
        subprocess.run(
            ["git", "worktree", "add", str(wt_path), "-b", f"worktree/{name}", "HEAD"],
            check=True, capture_output=True, cwd=str(git_repo),
        )
        return wt_path

    def test_removes_git_worktree(self, git_repo):
        wt_path = self._create_worktree(git_repo, "to-remove")
        assert wt_path.is_dir()

        result = run_hook({"path": str(wt_path)}, cwd=str(git_repo))
        assert result.returncode == 0
        assert not wt_path.exists()

        # Verify deregistered from git
        wt_list = subprocess.run(
            ["git", "worktree", "list"],
            capture_output=True, text=True, cwd=str(git_repo),
        )
        assert "to-remove" not in wt_list.stdout

    def test_cleans_up_empty_parent(self, git_repo):
        wt_path = self._create_worktree(git_repo, "only-child")

        result = run_hook({"path": str(wt_path)}, cwd=str(git_repo))
        assert result.returncode == 0

        # Parent should be removed since it's now empty
        assert not wt_path.parent.exists()

    def test_outside_expected_parent_exits_1(self, git_repo, tmp_path):
        """A worktree outside _worktrees/ should be refused."""
        rogue = tmp_path / "rogue-wt"
        rogue.mkdir()
        result = run_hook({"path": str(rogue)}, cwd=str(git_repo))
        assert result.returncode == 1
        assert "outside expected parent" in result.stderr.lower() or "refusing" in result.stderr.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Volumes/Code/github.com/fzymgc-house/fzymgc-house-skills && python -m pytest .claude/hooks/tests/test_worktree_remove.py -v`
Expected: FAIL — script not found

- [ ] **Step 3: Implement `worktree-remove`**

Create `.claude/hooks/worktree-remove`:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
"""WorktreeRemove hook: remove worktrees from sibling directory.

Input:  JSON on stdin with "path" field
Output: none (exit 0 on success, exit 1 on failure)

Behavior:
  1. Validate path is under a *_worktrees/ parent (reject traversal, symlinks)
  2. Detect repo root (from git/jj, or inferred from _worktrees path)
  3. VCS-aware workspace deregistration:
     - jj repos (.jj/): jj workspace forget worktree-<name>
     - git repos (.git/): git worktree remove, then git worktree prune
  4. rm -rf the worktree directory
  5. Clean up empty parent directory

Safety: exits cleanly (0) for nonexistent paths. Warns but continues
        when VCS deregistration fails -- directory is always removed.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from worktree_helpers import (
    cleanup_empty_parent,
    detect_repo_root,
    run_cmd,
    sanitize_for_output,
    validate_safe_name,
)


def _infer_repo_root(worktree_path: Path) -> Path | None:
    """Infer repo root from worktree path: strip name + _worktrees suffix."""
    worktrees_dir = worktree_path.parent
    if worktrees_dir.name.endswith("_worktrees"):
        repo_name = worktrees_dir.name.removesuffix("_worktrees")
        return worktrees_dir.parent / repo_name
    return None


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        data = {}

    raw_path = data.get("path") or ""
    if not raw_path:
        print(
            '{"warning":"no path field in WorktreeRemove input -- skipping removal"}',
            file=sys.stderr,
        )
        return 0

    worktree_path = Path(raw_path)
    if not worktree_path.is_dir():
        print(
            f'{{"warning":"worktree directory already removed: '
            f'{sanitize_for_output(raw_path)}"}}',
            file=sys.stderr,
        )
        return 0

    # Canonicalize path
    try:
        worktree_path = worktree_path.resolve(strict=True)
    except OSError as e:
        print(
            f"ERROR: could not resolve canonical path for "
            f"'{sanitize_for_output(raw_path)}': "
            f"{sanitize_for_output(str(e)[:500])}",
            file=sys.stderr,
        )
        return 1

    workspace_name = worktree_path.name

    # Validate basename -- lenient: warn but allow non-conforming names
    try:
        validate_safe_name(workspace_name, "worktree name")
    except ValueError:
        print(
            f"WARNING: worktree name "
            f"'{sanitize_for_output(workspace_name)}' contains unusual "
            f"characters -- proceeding with removal",
            file=sys.stderr,
        )

    # Detect repo root
    repo_root_inferred = False
    try:
        repo_root = detect_repo_root(cwd=worktree_path)
    except RuntimeError as detect_err:
        # Fallback: infer from _worktrees path
        inferred = _infer_repo_root(worktree_path)
        if inferred:
            repo_root = inferred
            repo_root_inferred = True
            print(
                f"WARNING: detect_repo_root failed -- inferred repo root as "
                f"'{sanitize_for_output(str(repo_root))}' from worktree path "
                f"(detect_repo_root: {sanitize_for_output(str(detect_err)[:500])})",
                file=sys.stderr,
            )
        else:
            print(
                "ERROR: could not determine repo root and path does not match "
                "expected _worktrees pattern -- refusing removal for safety",
                file=sys.stderr,
            )
            print(
                f"Manual cleanup required: rm -rf "
                f"'{sanitize_for_output(str(worktree_path))}'",
                file=sys.stderr,
            )
            return 1

    # Validate repo name
    repo_name = repo_root.name
    try:
        validate_safe_name(repo_name, "repository directory name")
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    # Validate path is inside expected sibling directory
    expected_parent = repo_root.parent / f"{repo_name}_worktrees"
    try:
        expected_parent_resolved = expected_parent.resolve(strict=True)
    except OSError as e:
        print(
            f"ERROR: _worktrees parent directory "
            f"'{sanitize_for_output(str(expected_parent))}' does not exist "
            f"but WORKTREE_PATH '{sanitize_for_output(str(worktree_path))}' "
            f"does -- inconsistent state: {sanitize_for_output(str(e)[:500])}",
            file=sys.stderr,
        )
        return 1

    if not str(worktree_path).startswith(str(expected_parent_resolved) + "/"):
        print(
            f"ERROR: WORKTREE_PATH '{sanitize_for_output(str(worktree_path))}' "
            f"is outside expected parent "
            f"'{sanitize_for_output(str(expected_parent_resolved))}' "
            f"-- refusing removal",
            file=sys.stderr,
        )
        return 1

    # When repo root was inferred, verify it actually contains a repo
    skip_vcs_cleanup = False
    if repo_root_inferred:
        has_jj = (repo_root / ".jj").is_dir()
        has_git = (repo_root / ".git").is_dir()
        if not has_jj and not has_git:
            print(
                f"WARNING: inferred repo root "
                f"'{sanitize_for_output(str(repo_root))}' has no .jj/ or "
                f".git/ -- skipping VCS cleanup",
                file=sys.stderr,
            )
            skip_vcs_cleanup = True
        elif not has_jj:
            verify = run_cmd(
                ["git", "rev-parse", "--git-dir"], cwd=repo_root
            )
            if verify.returncode != 0:
                print(
                    f"WARNING: inferred repo root "
                    f"'{sanitize_for_output(str(repo_root))}' has .git/ but "
                    f"git rev-parse failed -- VCS state may be corrupt; "
                    f"skipping VCS cleanup",
                    file=sys.stderr,
                )
                skip_vcs_cleanup = True

    # VCS cleanup
    jj_forget_failed = False
    git_remove_failed = False

    if skip_vcs_cleanup:
        pass
    elif (repo_root / ".jj").is_dir():
        jj_forget_failed = _jj_cleanup(repo_root, workspace_name)
    else:
        result = run_cmd(
            ["git", "worktree", "remove", "--force", str(worktree_path)],
            cwd=repo_root,
        )
        if result.returncode != 0:
            print(
                f"WARNING: git worktree remove failed for "
                f"'{sanitize_for_output(str(worktree_path))}': "
                f"{sanitize_for_output(result.stderr[:500])}",
                file=sys.stderr,
            )
            git_remove_failed = True

    # Always remove directory
    try:
        if worktree_path.exists():
            shutil.rmtree(worktree_path)
    except OSError as e:
        print(
            f"ERROR: failed to remove worktree directory "
            f"'{sanitize_for_output(str(worktree_path))}': "
            f"{sanitize_for_output(str(e)[:500])}",
            file=sys.stderr,
        )
        return 1

    # If git worktree remove failed, prune now
    if git_remove_failed:
        prune = run_cmd(["git", "worktree", "prune"], cwd=repo_root)
        if prune.returncode != 0:
            print(
                f"WARNING: git worktree prune also failed: "
                f"{sanitize_for_output(prune.stderr[:500])} "
                f"-- stale metadata may remain in .git/worktrees/",
                file=sys.stderr,
            )

    cleanup_empty_parent(worktree_path.parent)

    # jj forget failure is a hard error (metadata leak);
    # git prune failure is cosmetic (exit 0).
    if jj_forget_failed:
        return 1

    return 0


def _jj_cleanup(repo_root: Path, workspace_name: str) -> bool:
    """Handle jj workspace forget. Returns True if forget failed."""
    if not shutil.which("jj"):
        print(
            f"WARNING: .jj/ found but jj not installed -- workspace metadata "
            f"not cleaned (run: jj workspace forget "
            f"worktree-{sanitize_for_output(workspace_name)} from "
            f"{sanitize_for_output(str(repo_root))} after reinstalling jj)",
            file=sys.stderr,
        )
        return True

    # Check workspace list first
    ws_list_result = run_cmd(
        ["jj", "workspace", "list"], cwd=repo_root
    )
    if ws_list_result.returncode == 0:
        ws_output = ws_list_result.stdout
        ws_key = f"worktree-{workspace_name}"
        if f"{ws_key}:" not in ws_output:
            if ws_key in ws_output:
                print(
                    f"WARNING: workspace '{ws_key}' found in jj workspace "
                    f"list but format differs from expected (missing colon "
                    f"separator) -- attempting forget anyway",
                    file=sys.stderr,
                )
            else:
                print(
                    f"INFO: workspace '{ws_key}' not found in jj workspace "
                    f"list output -- attempting forget anyway (idempotent)",
                    file=sys.stderr,
                )
    else:
        print(
            f"WARNING: jj workspace list failed: "
            f"{sanitize_for_output(ws_list_result.stderr[:500] or '(no details)')} "
            f"-- attempting workspace forget anyway for "
            f"worktree-{sanitize_for_output(workspace_name)}",
            file=sys.stderr,
        )

    # Attempt forget
    result = run_cmd(
        ["jj", "workspace", "forget", f"worktree-{workspace_name}"],
        cwd=repo_root,
    )
    if result.returncode != 0:
        print(
            f"ERROR: jj workspace forget failed for "
            f"worktree-{sanitize_for_output(workspace_name)}: "
            f"{sanitize_for_output(result.stderr[:500])}; workspace directory "
            f"will still be removed (run 'jj workspace forget "
            f"worktree-{sanitize_for_output(workspace_name)}' manually to "
            f"clean up)",
            file=sys.stderr,
        )
        return True

    return False


if __name__ == "__main__":
    sys.exit(main())
```

Make executable: `chmod +x .claude/hooks/worktree-remove`

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Volumes/Code/github.com/fzymgc-house/fzymgc-house-skills && python -m pytest .claude/hooks/tests/test_worktree_remove.py -v`
Expected: All 5 tests PASS (2 unit + 3 integration)

- [ ] **Step 5: Commit**

```bash
git add .claude/hooks/worktree-remove .claude/hooks/tests/test_worktree_remove.py
git commit -m "feat(hooks): add worktree-remove Python uv script with tests"
```

---

## Chunk 5: Cutover and Cleanup

### Task 8: Run full test suite

**Files:** None (verification only)

- [ ] **Step 1: Run all hook tests together**

Run: `cd /Volumes/Code/github.com/fzymgc-house/fzymgc-house-skills && python -m pytest .claude/hooks/tests/ -v`
Expected: All tests PASS

- [ ] **Step 2: Verify Python scripts produce same output as bash**

For `post-edit-format`, create a test `.py` file and run both versions:

```bash
echo "x=1" > /tmp/test_fmt.py
echo '{"tool_input":{"file_path":"/tmp/test_fmt.py"}}' | bash .claude/hooks/post-edit-format.sh
echo '{"tool_input":{"file_path":"/tmp/test_fmt.py"}}' | python3 .claude/hooks/post-edit-format
```

Both should exit 0 and format the file identically.

- [ ] **Step 3: Verify worktree-create/remove round-trip**

```bash
cd /Volumes/Code/github.com/fzymgc-house/fzymgc-house-skills
echo '{"name":"migration-test"}' | python3 .claude/hooks/worktree-create
# Should print path like /Volumes/Code/.../fzymgc-house-skills_worktrees/migration-test
echo '{"path":"/Volumes/Code/.../fzymgc-house-skills_worktrees/migration-test"}' | python3 .claude/hooks/worktree-remove
# Should exit 0, directory gone
```

---

### Task 9: Update `settings.json` and delete bash scripts

**Files:**

- Modify: `.claude/settings.json`
- Delete: `.claude/hooks/worktree-create.sh`
- Delete: `.claude/hooks/worktree-remove.sh`
- Delete: `.claude/hooks/worktree-helpers.sh`
- Delete: `.claude/hooks/post-edit-format.sh`

- [ ] **Step 1: Update `.claude/settings.json`**

Change hook commands from `.sh` scripts to extensionless Python scripts:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/post-edit-format",
            "timeout": 15
          }
        ]
      }
    ],
    "WorktreeCreate": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/worktree-create",
            "timeout": 30
          }
        ]
      }
    ],
    "WorktreeRemove": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/worktree-remove",
            "timeout": 15
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 2: Delete bash scripts**

```bash
git rm .claude/hooks/worktree-create.sh
git rm .claude/hooks/worktree-remove.sh
git rm .claude/hooks/worktree-helpers.sh
git rm .claude/hooks/post-edit-format.sh
```

- [ ] **Step 3: Run tests one more time**

Run: `cd /Volumes/Code/github.com/fzymgc-house/fzymgc-house-skills && python -m pytest .claude/hooks/tests/ -v`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add .claude/settings.json
git commit -m "refactor(hooks): switch to Python uv scripts, delete bash originals"
```

- [ ] **Step 5: Push**

```bash
git push
```
