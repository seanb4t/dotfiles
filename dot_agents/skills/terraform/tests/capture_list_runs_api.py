#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx"]
# ///
"""Capture list_runs response from direct HCP API."""

import json
import os
import httpx

token = os.environ.get("TFE_TOKEN")
if not token:
    print("TFE_TOKEN required")
    exit(1)

client = httpx.Client(
    base_url="https://app.terraform.io",
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/vnd.api+json",
    },
    timeout=30.0,
)

params = {
    "filter[organization][name]": "fzymgc-house",
    "filter[workspace][name]": "main-cluster-cloudflare",
    "page[size]": 5,
}

resp = client.get("/api/v2/runs", params=params)
resp.raise_for_status()

# Save as fixture
with open("fixtures/list_runs_api.json", "w") as f:
    json.dump({"success": True, "data": resp.json()}, f, indent=2)

print("Saved fixtures/list_runs_api.json")
client.close()
