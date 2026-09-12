#!/usr/bin/env python3
"""Restore native Claude plugins selected in settings.json, without bulk updates."""

import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess

SOURCE_ROOT = Path(__file__).resolve().parent.parent


def read_json(path):
    return json.loads(path.read_text()) if path.exists() else {}


def restore_skill_bridges(home, manifest, dry_run=False):
    """Expose native plugin skills to Codex without copying or npx ownership."""
    known = read_json(home / '.claude/plugins/known_marketplaces.json')
    count = 0
    for bridge in manifest.get('plugin_skill_bridges', []):
        marketplace = known.get(bridge['marketplace'], {}).get('installLocation')
        if not marketplace:
            raise ValueError('Missing native marketplace: ' + bridge['marketplace'])
        source_root = Path(marketplace) / bridge['skills_path']
        for name in bridge['skills']:
            source = source_root / name
            if not (source / 'SKILL.md').is_file():
                raise ValueError('Missing native plugin skill: ' + str(source))
            target = home / '.agents/skills' / name
            if target.is_symlink() and target.resolve() == source.resolve():
                continue
            if target.exists() or target.is_symlink():
                raise ValueError('Preserving existing skill; reconcile before linking: ' + str(target))
            count += 1
            print('Link native plugin skill: ' + name)
            if not dry_run:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.symlink_to(os.path.relpath(source, target.parent), target_is_directory=True)
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    root = Path.home() / '.claude'
    settings = read_json(root / 'settings.json')
    known = read_json(root / 'plugins/known_marketplaces.json')
    installed = read_json(root / 'plugins/installed_plugins.json').get('plugins', {})
    commands = []
    for name, entry in settings.get('extraKnownMarketplaces', {}).items():
        source = entry['source']
        if known.get(name, {}).get('source') == source:
            continue
        if source.get('source') == 'directory':
            path = Path(source['path']).expanduser()
            if not (path / '.claude-plugin/marketplace.json').is_file():
                raise ValueError('Missing local marketplace: ' + str(path))
            commands.append(['claude', 'plugin', 'marketplace', 'add', str(path)])
        elif source.get('source') == 'github':
            commands.append(['claude', 'plugin', 'marketplace', 'add', source['repo']])
        else:
            raise ValueError('Unsupported marketplace source; configure explicitly: ' + name)
    for name, enabled in settings.get('enabledPlugins', {}).items():
        if any(e.get('scope') == 'user' and Path(e['installPath']).is_dir() for e in installed.get(name, [])):
            continue
        commands.append(['claude', 'plugin', 'install', name, '--scope', 'user'])
        if not enabled:
            commands.append(['claude', 'plugin', 'disable', name, '--scope', 'user'])
    for command in commands:
        print(shlex.join(command))
        if not args.dry_run:
            subprocess.run(command, check=True)
    print('Claude plugin restore: {} actions{}'.format(len(commands), ' planned' if args.dry_run else ' completed'))
    manifest = read_json(SOURCE_ROOT / 'agent-skills.json')
    # A dry run on a fresh machine cannot inspect marketplaces not yet installed.
    if args.dry_run and commands:
        print('Native skill links will be checked after plugin installation.')
    else:
        links = restore_skill_bridges(Path.home(), manifest, dry_run=args.dry_run)
        print('Native plugin skill links: {} actions{}'.format(links, ' planned' if args.dry_run else ' completed'))


if __name__ == '__main__':
    main()
