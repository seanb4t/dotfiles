import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).parents[1]


@unittest.skipUnless(shutil.which('chezmoi'), 'chezmoi is required')
class CodexTemplateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name)
        templates = self.source / '.chezmoitemplates'
        templates.mkdir()
        for name in ['codex-settings.toml.tmpl', 'user-preferences.md.tmpl']:
            shutil.copy2(ROOT / '.chezmoitemplates' / name, templates / name)
        (templates / 'codex-mcp.json.tmpl').write_text(json.dumps({
            'firecrawl': {'url': 'https://example.invalid/mcp', 'http_headers': {'Authorization': 'fixture'}}
        }))
        (templates / 'claude-settings.json').write_text('{"model":"opus"}')
        (templates / 'claude-guidance.md').write_text('Claude-specific guidance\n')
        (self.source / 'config.toml').write_text('')

    def render(self, name, text, valid=True, agent='dot_codex'):
        result = subprocess.run([
            'chezmoi', '--source', str(self.source), '--config', str(self.source / 'config.toml'),
            'execute-template', '--with-stdin', '--file', str(ROOT / agent / name)
        ], input=text, capture_output=True, text=True)
        if valid:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
        return result.stdout

    def test_config_preserves_runtime_state_and_replaces_owned_transport(self):
        source = '''model = "old"
[mcp_servers.firecrawl]
command = "obsolete"
args = ["old"]
[mcp_servers.personal]
command = "keep-me"
[hooks.state]
approved = true
[plugins.personal]
enabled = false
'''
        output = self.render('modify_private_config.toml', source)
        self.assertIn('keep-me', output)
        self.assertIn('approved = true', output)
        self.assertIn('enabled = false', output)
        self.assertNotIn('obsolete', output)
        self.assertIn('https://example.invalid/mcp', output)
        self.assertEqual(output, self.render('modify_private_config.toml', output))

    def test_new_user_config(self):
        output = self.render('modify_private_config.toml', '')
        self.assertIn('mcp_servers', output)
        self.assertIn('workspace-write', output)

    def test_invalid_input_fails_instead_of_replacing_it(self):
        self.render('modify_private_config.toml', '[invalid', valid=False)

    def test_global_instructions_preserve_installer_blocks(self):
        existing = '<!-- GSD Configuration -->\nGSD-owned instructions\n<!-- engram:skills:start -->\nKeep Engram\n'
        output = self.render('modify_AGENTS.md', existing)
        self.assertIn(existing.strip(), output)
        self.assertEqual(output.count('<!-- chezmoi:user-preferences:start -->'), 1)
        self.assertEqual(output, self.render('modify_AGENTS.md', output))

    def test_claude_settings_preserve_native_hooks_and_status_line(self):
        existing = {'model': 'old', 'hooks': {'SessionStart': [{'hooks': [{'command': 'GSD owns this'}]}]},
                    'statusLine': {'command': 'native-status'}, 'custom': True}
        output = self.render('modify_settings.json', json.dumps(existing), agent='dot_claude')
        result = json.loads(output)
        self.assertEqual(result['hooks'], existing['hooks'])
        self.assertEqual(result['statusLine'], existing['statusLine'])
        self.assertTrue(result['custom'])
        self.assertEqual(result['model'], 'opus')
        self.assertEqual(output, self.render('modify_settings.json', output, agent='dot_claude'))

    def test_claude_local_marketplace_path_expands_user_home(self):
        settings = {'extraKnownMarketplaces': {'local': {'source': {
            'source': 'directory', 'path': '~/.agents/plugins'}}}}
        (self.source / '.chezmoitemplates/claude-settings.json').write_text(json.dumps(settings))
        output = self.render('modify_settings.json', '{}', agent='dot_claude')
        source = json.loads(output)['extraKnownMarketplaces']['local']['source']
        self.assertEqual(Path(source['path']), Path.home() / '.agents/plugins')
        self.assertEqual(output, self.render('modify_settings.json', output, agent='dot_claude'))

    def test_claude_instructions_preserve_installer_content(self):
        existing = '<!-- GSD -->\nGSD owns this\n'
        output = self.render('modify_CLAUDE.md', existing, agent='dot_claude')
        self.assertIn('GSD owns this', output)
        self.assertEqual(output, self.render('modify_CLAUDE.md', output, agent='dot_claude'))


if __name__ == '__main__':
    unittest.main()
