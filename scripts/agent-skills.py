#!/usr/bin/env python3
"""Restore the curated non-GSD skill selection without upgrading existing skills."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent


def content_hash(path):
    digest = hashlib.sha256()
    for file in sorted(path.rglob('*')):
        if file.is_file() and file.name != '.DS_Store' and '.git' not in file.parts:
            digest.update(str(file.relative_to(path)).encode())
            digest.update(file.read_bytes())
    return digest.hexdigest()


def load_manifest(path):
    manifest = json.loads(path.read_text())
    seen = set()
    plugin_owned = {name for group in manifest.get('plugin_owned_skills', {}).values() for name in group}
    for entry in manifest['skills']:
        name = entry['name']
        if name.startswith('gsd-'):
            raise ValueError('GSD owns its skills; remove {} from the manifest'.format(name))
        if name in plugin_owned:
            raise ValueError('A native plugin owns {}; remove it from the standalone selection'.format(name))
        if name in seen or Path(name).name != name or name in ('.', '..'):
            raise ValueError('Invalid or duplicate skill name: ' + name)
        seen.add(name)
    return manifest


def link_state(target, canonical):
    if target.is_symlink() and target.resolve() == canonical.resolve():
        return 'linked'
    if target.is_symlink() and not target.exists():
        return 'broken'
    if not target.exists():
        return 'missing'
    if target.is_dir() and content_hash(target) == content_hash(canonical):
        return 'duplicate'
    return 'conflict'


def repair_link(target, canonical, backup_root):
    state = link_state(target, canonical)
    if state == 'linked':
        return
    if state == 'conflict':
        raise ValueError('Preserving different local content at {}; reconcile it first'.format(target))
    if target.is_symlink():
        target.unlink()
    elif target.exists():
        backup_root.mkdir(parents=True, exist_ok=True, mode=0o700)
        backup = Path(tempfile.mkdtemp(prefix=target.name + '-', dir=backup_root))
        shutil.move(str(target), str(backup / target.name))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.symlink_to(os.path.relpath(canonical, target.parent), target_is_directory=True)


def run(manifest, home, apply=False):
    if apply and home != Path.home():
        raise ValueError('Restore can only target the current user home')
    failures = []
    drift = False
    backup_root = home / '.local/state/agent-setup/skill-backups'
    for entry in manifest['skills']:
        name = entry['name']
        canonical = home / '.agents/skills' / name
        source = entry['source']
        if source.startswith('./'):
            source = str(ROOT / source)
        if not (canonical / 'SKILL.md').is_file():
            drift = True
            print('install: ' + name)
            if apply:
                agent_directories = set(manifest['link_directories']) | {'.codex/skills'}
                conflicts = [home / directory / name for directory in sorted(agent_directories)
                             if (home / directory / name).exists()
                             and (not Path(source).is_dir()
                                  or content_hash(home / directory / name) != content_hash(Path(source)))]
                if conflicts:
                    failures.append('Preserving existing skill before install: ' + str(conflicts[0]))
                    continue
                command = ['npx', '--yes', 'skills@' + manifest['cli_version'],
                           'add', source, '--global', '--skill', name,
                           '--agent', *manifest['agents'], '--yes']
                result = subprocess.run(command, cwd=ROOT)
                if result.returncode or not (canonical / 'SKILL.md').is_file():
                    failures.append('Install failed: ' + name)
                    continue
            else:
                continue
        for agent_dir in manifest['link_directories']:
            target = home / agent_dir / name
            state = link_state(target, canonical)
            if state != 'linked':
                drift = True
                print('{}: {} ({})'.format(state, name, agent_dir))
                if state == 'conflict':
                    failures.append('Different local skill: ' + str(target))
                elif apply:
                    repair_link(target, canonical, backup_root)
        # Codex reads .agents directly. Remove only redundant or broken legacy
        # aliases for a skill whose canonical replacement is present.
        legacy = home / '.codex/skills' / name
        if legacy.is_symlink():
            state = link_state(legacy, canonical)
            if state in ('linked', 'broken', 'duplicate'):
                drift = True
                print('legacy Codex link: ' + name)
                if apply:
                    legacy.unlink()
            else:
                failures.append('Different legacy Codex skill: ' + str(legacy))
        elif legacy.exists():
            failures.append('Separate legacy Codex skill: {}; reconcile it first'.format(legacy))
    for failure in failures:
        print(failure, file=sys.stderr)
    return bool(failures) or (drift and not apply)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['audit', 'restore'])
    parser.add_argument('--manifest', type=Path, default=ROOT / 'agent-skills.json')
    parser.add_argument('--home', type=Path, default=Path.home(), help='Alternate home for audit only')
    args = parser.parse_args()
    try:
        manifest = load_manifest(args.manifest)
        return run(manifest, args.home, apply=args.action == 'restore')
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
