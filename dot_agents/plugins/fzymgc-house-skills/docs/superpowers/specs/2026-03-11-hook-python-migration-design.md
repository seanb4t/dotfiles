# Hook Python Migration Design

## Overview

Migrate `.claude/hooks/` shell scripts (worktree-create.sh, worktree-remove.sh, worktree-helpers.sh,
post-edit-format.sh) from bash to standalone uv-based Python scripts with pytest tests.

## Motivation

- **Testability**: Bash scripts are difficult to test reliably (BATS EXIT trap conflicts caused test
  hangs). Python + pytest provides a mature, stable testing framework.
- **Maintainability**: The worktree hooks have grown complex (214 lines for worktree-remove.sh with
  multiple VCS paths, error handling, and cleanup logic). Python's structured error handling (try/except)
  and type hints improve readability.
- **Consistency**: The rest of the plugin ecosystem uses Python (uv scripts for pr-review agents).
  Aligning hooks reduces cognitive overhead.

## Architecture: Standalone uv Scripts (Approach A)

Each hook script becomes an extensionless uv script with inline dependency metadata:

```text
.claude/hooks/
  worktree-create        # uv script (was worktree-create.sh)
  worktree-remove        # uv script (was worktree-remove.sh)
  post-edit-format       # uv script (was post-edit-format.sh)
  worktree_helpers.py    # shared module (imported via sys.path)
  tests/
    test_worktree_create.py
    test_worktree_remove.py
    test_worktree_helpers.py
    test_post_edit_format.py
    conftest.py          # shared fixtures
```

### Shebang and Dependencies

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
```

No external dependencies required. Standard library only: `subprocess`, `json`, `sys`, `os`,
`pathlib`, `shutil`, `tempfile`.

### Shared Module Import

Each uv script adds its own directory to `sys.path` to import `worktree_helpers`:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import worktree_helpers
```

## Component Design

### worktree_helpers.py

Shared functions, equivalent to current worktree-helpers.sh:

| Function | Purpose |
|----------|---------|
| `sanitize_for_output(s: str) -> str` | Strip control characters for safe logging |
| `validate_safe_name(name: str, label: str) -> None` | Raise ValueError for path traversal/metacharacters |
| `cleanup_empty_parent(parent: Path) -> None` | rmdir if empty after worktree removal |
| `detect_repo_root() -> Path` | Find repo root via git rev-parse or jj root |
| `run_cmd(args, *, cwd, capture_stderr) -> subprocess.CompletedProcess` | Thin subprocess wrapper for git/jj CLI calls |

### worktree-create

Input: JSON on stdin with `name` field. Output: worktree path on stdout.

Flow:

1. Parse JSON input, extract `name`
2. `validate_safe_name(name, "worktree name")`
3. `detect_repo_root()` to find repo root
4. Create parent dir: `<repo-parent>/<repo-name>_worktrees/`
5. VCS-aware workspace creation:
   - jj repos (`.jj/`): `jj workspace add --name worktree-<name>`
   - git repos: `git worktree add -b worktree/<name>`
6. Install lefthook if configured
7. Print worktree path to stdout

Cleanup: `atexit` handler reverts partial state on failure (VCS deregistration, directory removal).
Uses flags (`parent_created`, `workspace_created`) to avoid cleaning up resources that were never
created.

### worktree-remove

Input: JSON on stdin with `path` field. Output: none (exit 0 on success, exit 1 on failure).

Flow:

1. Parse JSON input, extract `path`
2. Canonicalize path (`Path.resolve()`)
3. Validate path is under `*_worktrees/` parent
4. Detect repo root (from git/jj, or inferred from `_worktrees` path)
5. VCS-aware workspace deregistration:
   - jj repos (`.jj/`): `jj workspace forget worktree-<name>`
   - git repos (`.git/`): `git worktree remove`, then `git worktree prune`
6. `shutil.rmtree()` the worktree directory
7. `cleanup_empty_parent()` on the parent directory

Safety: exits cleanly (0) for nonexistent paths. Warns but continues when VCS deregistration
fails -- directory is always removed.

### post-edit-format

Input: JSON on stdin with `tool_input.file_path` field. Output: none.

Flow:

1. Parse JSON input, extract file path
2. If `.py`: run `ruff check --fix` + `ruff format`
3. If `.md`: run `rumdl check --fix`
4. Exit 0 regardless of formatter success (best-effort)

## Testing Strategy

pytest with `tmp_path` and `unittest.mock.patch` for subprocess isolation.

### Key Fixtures (conftest.py)

- `git_repo(tmp_path)`: Initialize a git repo with an initial commit
- `jj_repo(tmp_path)`: Initialize a jj repo (skip if jj not installed)
- `mock_stdin(data)`: Patch `sys.stdin` with JSON input

### Test Categories

| Category | Example |
|----------|---------|
| Input validation | Empty name, path traversal (`../`), shell metacharacters |
| VCS detection | git-only repo, jj repo, colocated repo, no VCS |
| Happy path | Create/remove worktree in git repo, jj repo |
| Error handling | VCS command fails, directory removal fails, missing tools |
| Edge cases | Nonexistent path (remove), already-exists (create) |

### Subprocess Mocking

Tests mock `subprocess.run` to avoid requiring real git/jj repos for unit tests. Integration tests
(marked `@pytest.mark.integration`) use real repos via the `git_repo`/`jj_repo` fixtures.

```python
@pytest.fixture
def mock_git(monkeypatch):
    """Mock subprocess.run for git commands."""
    results = {}
    def fake_run(args, **kwargs):
        key = tuple(args[:3])
        return results.get(key, CompletedProcess(args, 0, "", ""))
    monkeypatch.setattr(subprocess, "run", fake_run)
    return results
```

## Migration Strategy

1. **Write Python scripts** alongside existing bash scripts
2. **Verify behavior parity** by running both against the same scenarios
3. **Update `.claude/settings.json`** to point hook commands at Python scripts
4. **Delete bash scripts** (worktree-create.sh, worktree-remove.sh, worktree-helpers.sh,
   post-edit-format.sh)

This allows incremental validation -- if the Python version has a bug, the bash version is still
available for rollback.

## settings.json Changes

```json
{
  "hooks": {
    "WorktreeCreate": [
      {
        "type": "command",
        "command": ".claude/hooks/worktree-create"
      }
    ],
    "WorktreeRemove": [
      {
        "type": "command",
        "command": ".claude/hooks/worktree-remove"
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "type": "command",
        "command": ".claude/hooks/post-edit-format"
      }
    ]
  }
}
```

## Constraints

- No external dependencies (stdlib only)
- Python 3.11+ (match uv script convention in this repo)
- Preserve all existing behavior documented in bash script headers
- Exit codes must match: 0 success, 1 failure
- Stderr for warnings/errors, stdout only for worktree path output (create)
- `sanitize_for_output` must handle the same control character ranges as the bash version
