from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE_PATH = REPO_ROOT / ".agents" / "plugins" / "marketplace.json"
EXPECTED_PLUGIN_ORDER = ["homelab", "pr-review", "jj", "superpowers"]
EXPECTED_EXTRA_PATHS = {
    "homelab": [".mcp.json"],
    "pr-review": ["agents", "references"],
    "jj": ["hooks", "commands"],
    "superpowers": ["agents", "hooks", "references", "scripts", "commands"],
}


def load_json(path: Path) -> dict:
    with path.open() as handle:
        return json.load(handle)


def test_codex_marketplace_lists_expected_plugins() -> None:
    assert MARKETPLACE_PATH.exists(), f"Missing marketplace manifest: {MARKETPLACE_PATH}"

    marketplace = load_json(MARKETPLACE_PATH)
    plugin_names = [entry["name"] for entry in marketplace["plugins"]]

    assert plugin_names == EXPECTED_PLUGIN_ORDER

    for plugin_name, entry in zip(EXPECTED_PLUGIN_ORDER, marketplace["plugins"], strict=True):
        assert entry["source"] == {
            "source": "local",
            "path": f"./plugins/{plugin_name}",
        }
        assert entry["policy"] == {
            "installation": "AVAILABLE",
            "authentication": "ON_INSTALL",
        }
        assert entry["category"] == "Developer Tools"


def test_codex_plugin_manifests_reference_existing_paths() -> None:
    assert MARKETPLACE_PATH.exists(), f"Missing marketplace manifest: {MARKETPLACE_PATH}"

    marketplace = load_json(MARKETPLACE_PATH)

    for entry in marketplace["plugins"]:
        plugin_root = REPO_ROOT / entry["source"]["path"].removeprefix("./")
        manifest_path = plugin_root / ".codex-plugin" / "plugin.json"

        assert plugin_root.exists(), f"Missing plugin root: {plugin_root}"
        assert manifest_path.exists(), f"Missing plugin manifest: {manifest_path}"

        manifest = load_json(manifest_path)
        assert manifest["name"] == entry["name"]

        for component_key in ("skills", "hooks", "mcpServers", "apps"):
            component_path = manifest.get(component_key)
            if component_path is None:
                continue
            assert component_path.startswith("./"), (
                f"{manifest_path} field '{component_key}' must use a relative path"
            )
            resolved_path = plugin_root / component_path.removeprefix("./")
            assert resolved_path.exists(), (
                f"{manifest_path} points '{component_key}' at missing path {resolved_path}"
            )

        for extra_path in EXPECTED_EXTRA_PATHS[entry["name"]]:
            assert (plugin_root / extra_path).exists(), (
                f"Expected compatibility path missing: {plugin_root / extra_path}"
            )
