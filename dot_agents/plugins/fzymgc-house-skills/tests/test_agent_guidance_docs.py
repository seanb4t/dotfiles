from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
AGENTS_PATH = REPO_ROOT / "AGENTS.md"
CLAUDE_PATH = REPO_ROOT / "CLAUDE.md"
PR_REVIEW_AGENTS_DIR = REPO_ROOT / "pr-review" / "agents"


def test_claude_doc_is_a_shim_to_agents() -> None:
    agents_text = AGENTS_PATH.read_text()
    claude_text = CLAUDE_PATH.read_text()

    assert "source of truth" in agents_text
    assert "Read `AGENTS.md` first." in claude_text
    assert "Claude-specific addendum" in claude_text


def test_pr_review_agents_read_agents_before_claude() -> None:
    agent_files = sorted(PR_REVIEW_AGENTS_DIR.glob("*.md"))
    assert agent_files

    for agent_file in agent_files:
        text = agent_file.read_text()
        assert "Read `AGENTS.md`" in text, f"{agent_file} must read AGENTS.md"
        if "CLAUDE.md" in text:
            assert text.index("AGENTS.md") < text.index("CLAUDE.md"), (
                f"{agent_file} must reference AGENTS.md before CLAUDE.md"
            )
