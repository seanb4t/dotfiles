#!/bin/sh
set -eu

ROOT="${HOME}/.agents/plugins"
REPO="${ROOT}/fzymgc-house-skills"
MARKETPLACE="${ROOT}/marketplace.json"

if [ ! -d "${REPO}/.git" ]; then
  echo "Missing runtime clone at ${REPO}" >&2
  exit 1
fi

git -C "${REPO}" fetch --prune origin
git -C "${REPO}" checkout main
git -C "${REPO}" pull --ff-only origin main

jq empty \
  "${MARKETPLACE}" \
  "${REPO}/plugins/homelab/.codex-plugin/plugin.json" \
  "${REPO}/plugins/pr-review/.codex-plugin/plugin.json" \
  "${REPO}/plugins/jj/.codex-plugin/plugin.json" \
  "${REPO}/plugins/superpowers/.codex-plugin/plugin.json"

python3 - <<'PY'
import json
from pathlib import Path

home = Path.home()
marketplace_root = home / ".agents" / "plugins"
marketplace = json.loads((marketplace_root / "marketplace.json").read_text())

for plugin in marketplace["plugins"]:
    source = plugin["source"]["path"]
    path = (home / source.removeprefix("./")).resolve()
    if not path.exists():
        raise SystemExit(f"Missing plugin path: {path}")
    print(f"{plugin['name']}: {path}")
PY
