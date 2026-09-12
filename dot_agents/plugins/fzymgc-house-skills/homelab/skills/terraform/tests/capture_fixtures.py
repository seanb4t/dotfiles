#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx", "pyyaml"]
# ///
"""Capture real MCP responses for test fixtures."""

import json
import sys
import os

# Add parent scripts dir to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from terraform_mcp import SessionManager


def capture_response(client, tool_name: str, args: dict) -> dict:
    """Capture raw MCP response before unwrap_result."""
    return client.call_tool(tool_name, args)


def main():
    org = os.environ.get("TFE_ORG", "fzymgc-house")
    fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")

    session = SessionManager()
    try:
        client = session.get_client()

        # Capture list_workspaces
        print("Capturing list_workspaces...")
        resp = capture_response(
            client,
            "list_workspaces",
            {
                "terraform_org_name": org,
                "pageSize": 5,
            },
        )
        with open(os.path.join(fixtures_dir, "list_workspaces.json"), "w") as f:
            json.dump(resp, f, indent=2)
        print(f"  success={resp.get('success')}")

        # Capture list_runs
        print("Capturing list_runs...")
        resp = capture_response(
            client,
            "list_runs",
            {
                "terraform_org_name": org,
                "workspace_name": "main-cluster-bootstrap",
                "pageSize": 3,
            },
        )
        with open(os.path.join(fixtures_dir, "list_runs.json"), "w") as f:
            json.dump(resp, f, indent=2)
        print(f"  success={resp.get('success')}")

        # Capture search_providers
        print("Capturing search_providers...")
        resp = capture_response(
            client,
            "search_providers",
            {
                "provider_name": "aws",
                "provider_namespace": "hashicorp",
                "service_slug": "lambda_function",
                "provider_document_type": "resources",
            },
        )
        with open(os.path.join(fixtures_dir, "search_providers.json"), "w") as f:
            json.dump(resp, f, indent=2)
        print(f"  success={resp.get('success')}")

        # Capture get_provider_details (using a known doc ID)
        print("Capturing get_provider_details...")
        resp = capture_response(
            client,
            "get_provider_details",
            {
                "provider_doc_id": "10931109",  # lambda_function
            },
        )
        with open(os.path.join(fixtures_dir, "get_provider_details.json"), "w") as f:
            json.dump(resp, f, indent=2)
        print(f"  success={resp.get('success')}")

        # Capture get_workspace_details
        print("Capturing get_workspace_details...")
        resp = capture_response(
            client,
            "get_workspace_details",
            {
                "terraform_org_name": org,
                "workspace_name": "main-cluster-bootstrap",
            },
        )
        with open(os.path.join(fixtures_dir, "get_workspace_details.json"), "w") as f:
            json.dump(resp, f, indent=2)
        print(f"  success={resp.get('success')}")

        print("\nAll fixtures captured!")

    finally:
        session.cleanup()


if __name__ == "__main__":
    main()
