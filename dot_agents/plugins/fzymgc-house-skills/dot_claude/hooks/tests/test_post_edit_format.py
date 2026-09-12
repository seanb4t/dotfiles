"""Tests for post-edit-format hook."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

RUFF_AVAILABLE = shutil.which("ruff") is not None
RUMDL_AVAILABLE = shutil.which("rumdl") is not None


HOOK_DIR = Path(__file__).parent.parent
HOOK = HOOK_DIR / "post-edit-format"


def run_hook(
    data: dict | None = None, raw: str | None = None
) -> subprocess.CompletedProcess:
    """Run the hook as a subprocess with the given JSON input."""
    if raw is not None:
        stdin_input = raw
    elif data is not None:
        stdin_input = json.dumps(data)
    else:
        stdin_input = ""

    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=stdin_input,
        capture_output=True,
        text=True,
    )


def test_python_file_runs_ruff(tmp_path: Path) -> None:
    """Python files should invoke ruff and exit 0."""
    py_file = tmp_path / "example.py"
    py_file.write_text("x=1\n")

    data = {"tool_input": {"file_path": str(py_file)}}
    result = run_hook(data)

    assert result.returncode == 0


def test_markdown_file_runs_rumdl(tmp_path: Path) -> None:
    """Markdown files should invoke rumdl and exit 0."""
    md_file = tmp_path / "README.md"
    md_file.write_text("# Hello\n\nWorld.\n")

    data = {"tool_input": {"file_path": str(md_file)}}
    result = run_hook(data)

    assert result.returncode == 0


@pytest.mark.skipif(not RUFF_AVAILABLE, reason="ruff is not installed")
def test_python_file_formatted_by_ruff(tmp_path: Path) -> None:
    """Ruff actually formats the Python file (not just exits 0)."""
    py_file = tmp_path / "example.py"
    # Missing spaces around = is a formatting issue ruff will fix
    py_file.write_text("x=1\n")

    data = {"tool_input": {"file_path": str(py_file)}}
    result = run_hook(data)
    assert result.returncode == 0

    # ruff format should have added spaces: x = 1
    content = py_file.read_text()
    assert "x = 1" in content, (
        f"Expected ruff to format 'x=1' to 'x = 1', got: {content!r}"
    )


@pytest.mark.skipif(not RUMDL_AVAILABLE, reason="rumdl is not installed")
def test_markdown_file_formatted_by_rumdl(tmp_path: Path) -> None:
    """rumdl actually formats the Markdown file (not just exits 0)."""
    md_file = tmp_path / "test.md"
    # Trailing whitespace is fixable by rumdl
    md_file.write_text("# Hello   \n\nWorld.\n")

    data = {"tool_input": {"file_path": str(md_file)}}
    result = run_hook(data)
    assert result.returncode == 0

    content = md_file.read_text()
    # rumdl should strip trailing whitespace from the heading line
    assert "# Hello" in content
    assert "Hello   \n" not in content, (
        f"Expected rumdl to strip trailing whitespace, got: {content!r}"
    )


def test_unknown_extension_exits_zero(tmp_path: Path) -> None:
    """Files with unknown extensions should exit 0 without error."""
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("some content\n")

    data = {"tool_input": {"file_path": str(txt_file)}}
    result = run_hook(data)

    assert result.returncode == 0


def test_missing_file_exits_zero(tmp_path: Path) -> None:
    """Non-existent file paths should exit 0 without error."""
    data = {"tool_input": {"file_path": str(tmp_path / "nonexistent.py")}}
    result = run_hook(data)

    assert result.returncode == 0


def test_empty_input_exits_zero() -> None:
    """Empty stdin should exit 0 without error."""
    result = run_hook(raw="")
    assert result.returncode == 0


def test_missing_file_path_field_exits_zero(tmp_path: Path) -> None:
    """JSON with no file_path exits 0."""
    data = {"tool_input": {}}
    result = run_hook(data)

    assert result.returncode == 0


def test_invalid_json_exits_zero() -> None:
    """Malformed JSON input should exit 0 without error."""
    result = run_hook(raw="{not valid json}")
    assert result.returncode == 0
