#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Check configuration and optionally discover tools through the native Codex client.

Never invokes an MCP tool or prints credentials. OAuth login remains client-owned.
"""

import argparse
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import time
import tomllib

ROOT = Path(__file__).resolve().parent.parent


def native_mcp_status():
    """Use the native client so OAuth, STDIO, and header helpers are respected."""
    process = subprocess.Popen(
        ['codex', 'app-server', '--listen', 'stdio://'],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    pending = b''

    def send(message):
        process.stdin.write((json.dumps(message) + '\n').encode())
        process.stdin.flush()

    def receive(request_id, timeout=80):
        nonlocal pending
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            while b'\n' in pending:
                line, pending = pending.split(b'\n', 1)
                try:
                    message = json.loads(line)
                except ValueError:
                    continue
                if message.get('id') == request_id:
                    if 'error' in message:
                        raise RuntimeError('Native MCP status request failed')
                    return message['result']
            if select.select([process.stdout], [], [], 1)[0]:
                data = os.read(process.stdout.fileno(), 65536)
                if not data:
                    raise RuntimeError('Codex app-server closed before replying')
                pending += data
        raise TimeoutError('Codex MCP status timed out')

    try:
        send({'id': 1, 'method': 'initialize', 'params': {
            'clientInfo': {'name': 'agent-setup-check', 'version': '1'},
            'capabilities': {'experimentalApi': True},
        }})
        receive(1, timeout=15)
        send({'method': 'initialized', 'params': {}})
        request_id, cursor, servers = 2, None, []
        while True:
            params = {'limit': 100}
            if cursor:
                params['cursor'] = cursor
            send({'id': request_id, 'method': 'mcpServerStatus/list', 'params': params})
            result = receive(request_id)
            servers.extend(result['data'])
            cursor = result.get('nextCursor')
            if not cursor:
                return servers
            request_id += 1
    finally:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        process.wait(timeout=10)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live-mcp', action='store_true', help='Discover MCP tools through Codex, including its OAuth credentials and STDIO clients')
    args = parser.parse_args()
    home = Path.home()
    config = tomllib.loads((home / '.codex/config.toml').read_text())
    failures = []
    for path in [home / '.codex/AGENTS.md', home / '.claude/CLAUDE.md']:
        text = path.read_text()
        ok = text.count('<!-- chezmoi:user-preferences:start -->') == 1
        print('{}: {}'.format(path.relative_to(home), 'OK' if ok else 'shared instructions missing or duplicated'))
        if not ok:
            failures.append(str(path))
    result = subprocess.run(['python3', str(ROOT / 'scripts/agent-skills.py'), 'audit'])
    print('Shared skills: {}'.format('OK' if result.returncode == 0 else 'drift detected'))
    if result.returncode:
        failures.append('skills')
    manifest = json.loads((ROOT / 'agent-skills.json').read_text())
    known = json.loads((home / '.claude/plugins/known_marketplaces.json').read_text())
    for bridge in manifest.get('plugin_skill_bridges', []):
        location = known.get(bridge['marketplace'], {}).get('installLocation')
        for name in bridge['skills']:
            target = home / '.agents/skills' / name
            source = Path(location) / bridge['skills_path'] / name if location else None
            ok = bool(source and (source / 'SKILL.md').is_file()
                      and target.is_symlink() and target.resolve() == source.resolve())
            print('Native skill {}: {}'.format(name, 'OK' if ok else 'missing or conflicting link'))
            if not ok:
                failures.append('native skill ' + name)
    plugin_result = subprocess.run(
        ['codex', 'plugin', 'list', '--marketplace', 'fzymgc-house-skills', '--json'],
        capture_output=True, text=True, check=True)
    installed = {p['name']: p for p in json.loads(plugin_result.stdout)['installed']}
    marketplace = json.loads((ROOT / 'dot_agents/plugins/marketplace.json').read_text())
    for entry in marketplace['plugins']:
        name = entry['name']
        plugin = installed.get(name)
        source = home / entry['source']['path'] / 'skills'
        expected = {p.relative_to(source) for p in source.glob('*/SKILL.md')}
        cache = home / '.codex/plugins/cache/fzymgc-house-skills' / name / str(plugin['version']) / 'skills' if plugin else None
        actual = {p.relative_to(cache) for p in cache.glob('*/SKILL.md')} if cache else set()
        ok = bool(expected and expected == actual)
        print('Plugin {}: {}'.format(name, '{} bundled skills'.format(len(actual)) if ok else 'missing packaged skills'))
        if not ok:
            failures.append('plugin ' + name)
    rendered = subprocess.run(['chezmoi', 'cat', str(home / '.codex/config.toml')], capture_output=True, text=True, check=True)
    print('Codex config repeat apply: {}'.format('stable' if tomllib.loads(rendered.stdout) == config else 'drift'))
    if tomllib.loads(rendered.stdout) != config:
        failures.append('config drift')
    if args.live_mcp:
        registered = subprocess.run(['codex', 'mcp', 'list', '--json'], capture_output=True, text=True, check=True)
        # Respect project overrides as well as the global configuration.
        selected = {s['name'] for s in json.loads(registered.stdout)
                    if s.get('enabled', True) and s['name'] in config.get('mcp_servers', {})}
        statuses = {s['name']: s for s in native_mcp_status()}
        for name in sorted(selected):
            status = statuses.get(name)
            if status is None or status.get('toolsError'):
                auth = status.get('authStatus') if status else None
                reason = 'native login required' if auth == 'notLoggedIn' else 'tool discovery failed'
                print('MCP {}: {}'.format(name, reason))
                failures.append(name)
            else:
                print('MCP {}: OK: {} tools'.format(name, len(status.get('tools', {}))))
        print('No model turn was started and no MCP tools were invoked.')
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
