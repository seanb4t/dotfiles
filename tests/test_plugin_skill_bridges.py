import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    'plugin_restore', Path(__file__).parents[1] / 'scripts/restore-claude-plugins.py')
restore = importlib.util.module_from_spec(spec)
spec.loader.exec_module(restore)


class PluginSkillBridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.marketplace = self.home / '.claude/plugins/marketplaces/example'
        self.skill = self.marketplace / 'package/skills/sample'
        self.skill.mkdir(parents=True)
        (self.skill / 'SKILL.md').write_text('native plugin content')
        (self.home / '.claude/plugins/known_marketplaces.json').write_text(
            json.dumps({'example': {'installLocation': str(self.marketplace)}}))
        self.manifest = {'plugin_skill_bridges': [{
            'marketplace': 'example', 'skills_path': 'package/skills', 'skills': ['sample']} ]}
        self.target = self.home / '.agents/skills/sample'

    def test_native_content_is_linked_and_updates_remain_visible(self):
        self.assertEqual(restore.restore_skill_bridges(self.home, self.manifest), 1)
        self.assertTrue(self.target.is_symlink())
        self.assertEqual(restore.restore_skill_bridges(self.home, self.manifest), 0)
        (self.skill / 'SKILL.md').write_text('updated by native installer')
        self.assertEqual((self.target / 'SKILL.md').read_text(), 'updated by native installer')

    def test_conflicting_content_is_preserved(self):
        self.target.mkdir(parents=True)
        (self.target / 'SKILL.md').write_text('personal content')
        with self.assertRaisesRegex(ValueError, 'Preserving existing skill'):
            restore.restore_skill_bridges(self.home, self.manifest)
        self.assertEqual((self.target / 'SKILL.md').read_text(), 'personal content')

    def test_dry_run_does_not_write(self):
        self.assertEqual(restore.restore_skill_bridges(self.home, self.manifest, dry_run=True), 1)
        self.assertFalse(self.target.exists())


if __name__ == '__main__':
    unittest.main()
