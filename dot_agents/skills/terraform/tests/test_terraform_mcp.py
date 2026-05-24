#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pytest", "httpx", "pyyaml"]
# ///
"""Tests for terraform_mcp.py using real MCP response fixtures."""

import json
import sys
from pathlib import Path

import pytest

# Add parent scripts dir to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from terraform_mcp import (
    parse_provider_search_markdown,
    unwrap_result,
    format_output,
    _is_mcp_list_runs_broken,
    _extract_runs_from_api_response,
)

# Load fixtures
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    """Load a JSON fixture file."""
    with open(FIXTURES_DIR / f"{name}.json") as f:
        return json.load(f)


class TestParseProviderSearchMarkdown:
    """Tests for parse_provider_search_markdown function."""

    def test_parse_real_search_providers_response(self):
        """Test parsing real markdown from search_providers MCP response."""
        fixture = load_fixture("search_providers")
        # Get the raw text from the MCP response
        text = fixture["result"]["content"][0]["text"]

        entries = parse_provider_search_markdown(text)

        # Should parse multiple entries (includes header explanation)
        assert len(entries) >= 5

        # Should find connect_lambda_function_association
        connect_entries = [
            e for e in entries if e["title"] == "connect_lambda_function_association"
        ]
        assert len(connect_entries) == 1
        assert connect_entries[0]["id"] == "10930629"
        assert connect_entries[0]["category"] == "resources"

        # Should find lambda_function
        lambda_entries = [e for e in entries if e["title"] == "lambda_function"]
        assert len(lambda_entries) == 1
        assert lambda_entries[0]["id"] == "10931109"

    def test_parse_with_target_slug_exact_match(self):
        """Test that target_slug prioritizes exact title matches."""
        fixture = load_fixture("search_providers")
        text = fixture["result"]["content"][0]["text"]

        entries = parse_provider_search_markdown(text, target_slug="lambda_function")

        # Should return only the exact match
        assert len(entries) == 1
        assert entries[0]["title"] == "lambda_function"
        assert entries[0]["id"] == "10931109"

    def test_parse_with_target_slug_case_insensitive(self):
        """Test that target_slug matching is case-insensitive."""
        fixture = load_fixture("search_providers")
        text = fixture["result"]["content"][0]["text"]

        entries = parse_provider_search_markdown(text, target_slug="LAMBDA_FUNCTION")

        assert len(entries) == 1
        assert entries[0]["title"] == "lambda_function"

    def test_parse_with_no_match_returns_all(self):
        """Test that unmatched target_slug returns all entries."""
        fixture = load_fixture("search_providers")
        text = fixture["result"]["content"][0]["text"]

        entries = parse_provider_search_markdown(
            text, target_slug="nonexistent_resource"
        )

        # Should return all entries since no exact match
        assert len(entries) >= 5

    def test_parse_empty_text(self):
        """Test parsing empty text returns empty list."""
        entries = parse_provider_search_markdown("")
        assert entries == []

    def test_parse_text_without_entries(self):
        """Test parsing text without any provider entries."""
        text = "Some random text without provider entries"
        entries = parse_provider_search_markdown(text)
        assert entries == []


class TestUnwrapResult:
    """Tests for unwrap_result function."""

    def test_unwrap_json_content(self):
        """Test unwrapping JSON content from MCP response."""
        fixture = load_fixture("list_workspaces")
        result = unwrap_result(fixture)

        # Should parse the JSON string in the text field
        assert isinstance(result, dict)
        assert "data" in result
        assert isinstance(result["data"], list)
        assert len(result["data"]) >= 1

        # Check first workspace structure
        workspace = result["data"][0]
        assert workspace["type"] == "workspaces"
        assert "attributes" in workspace
        assert workspace["attributes"]["name"] == "main-cluster-bootstrap"

    def test_unwrap_markdown_content(self):
        """Test unwrapping markdown (non-JSON) content from MCP response."""
        fixture = load_fixture("get_provider_details")
        result = unwrap_result(fixture)

        # Should return raw text since it's not JSON
        assert isinstance(result, str)
        assert "aws_lambda_function" in result
        assert "# Resource:" in result

    def test_unwrap_unsuccessful_result(self):
        """Test that unsuccessful results are returned as-is."""
        data = {"success": False, "error": "Something went wrong"}
        result = unwrap_result(data)
        assert result == data

    def test_unwrap_empty_content(self):
        """Test unwrapping empty content."""
        data = {"success": True, "result": {"content": []}}
        result = unwrap_result(data)
        assert result == []


class TestFormatOutput:
    """Tests for format_output function."""

    def test_format_json(self):
        """Test JSON output format."""
        data = {"key": "value", "number": 42}
        output = format_output(data, "json")
        assert output == '{"key":"value","number":42}'

    def test_format_yaml(self):
        """Test YAML output format."""
        data = {"key": "value"}
        output = format_output(data, "yaml")
        assert "key: value" in output

    def test_format_compact(self):
        """Test compact output format."""
        data = {"key": "value"}
        output = format_output(data, "compact")
        # Compact uses flow style
        assert "{" in output or "key: value" in output


class TestListRunsResponseHandling:
    """Tests for list_runs response handling with real fixture."""

    def test_empty_runs_response_structure(self):
        """Test that empty list_runs response is handled correctly."""
        fixture = load_fixture("list_runs")
        result = unwrap_result(fixture)

        # The MCP server returns {"data":{"type":""}} for empty results
        assert isinstance(result, dict)
        assert "data" in result
        # data is a dict, not a list - this is the upstream MCP bug
        assert isinstance(result["data"], dict)

    def test_is_mcp_list_runs_broken_detects_bug(self):
        """Test that _is_mcp_list_runs_broken detects the MCP bug."""
        fixture = load_fixture("list_runs")
        result = unwrap_result(fixture)

        assert _is_mcp_list_runs_broken(result) is True

    def test_is_mcp_list_runs_broken_false_for_valid(self):
        """Test that _is_mcp_list_runs_broken returns False for valid data."""
        valid_data = {"data": [{"id": "run-123", "type": "runs"}]}
        assert _is_mcp_list_runs_broken(valid_data) is False

    def test_is_mcp_list_runs_broken_false_for_non_dict(self):
        """Test that _is_mcp_list_runs_broken handles non-dict input."""
        assert _is_mcp_list_runs_broken([]) is False
        assert _is_mcp_list_runs_broken("string") is False
        assert _is_mcp_list_runs_broken(None) is False


class TestExtractRunsFromApiResponse:
    """Tests for _extract_runs_from_api_response function."""

    def test_extract_from_api_response(self):
        """Test extracting runs from direct API response."""
        fixture = load_fixture("list_runs_api")
        data = fixture["data"]

        runs = _extract_runs_from_api_response(data)

        assert isinstance(runs, list)
        assert len(runs) >= 1
        # Check first run structure
        assert runs[0]["type"] == "runs"
        assert "attributes" in runs[0]
        assert "status" in runs[0]["attributes"]

    def test_extract_from_list(self):
        """Test extracting runs from a list directly."""
        data = [{"id": "run-1"}, {"id": "run-2"}]
        runs = _extract_runs_from_api_response(data)
        assert runs == data

    def test_extract_from_items_key(self):
        """Test extracting runs from items key."""
        data = {"items": [{"id": "run-1"}]}
        runs = _extract_runs_from_api_response(data)
        assert runs == [{"id": "run-1"}]

    def test_extract_empty_for_broken_response(self):
        """Test that broken MCP response returns empty list."""
        data = {"data": {"type": ""}}
        runs = _extract_runs_from_api_response(data)
        assert runs == []


class TestWorkspaceDetailsResponse:
    """Tests for workspace details response with real fixture."""

    def test_workspace_details_structure(self):
        """Test that workspace details response is parsed correctly."""
        fixture = load_fixture("get_workspace_details")
        result = unwrap_result(fixture)

        assert isinstance(result, dict)
        assert "data" in result
        assert result["data"]["type"] == "tool"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
