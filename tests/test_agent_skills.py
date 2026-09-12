import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('agent_skills', Path(__file__).parents[1] / 'scripts/agent-skills.py')
skills = importlib.util.module_from_spec(spec)
spec.loader.exec_module(skills)


class SkillsRestoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        home_patch = patch.object(skills.Path, 'home', return_value=self.home)
        home_patch.start()
        self.addCleanup(home_patch.stop)
        self.canonical = self.home / '.agents/skills/example'
        self.canonical.mkdir(parents=True)
        (self.canonical / 'SKILL.md').write_text('canonical')
        self.target = self.home / '.claude/skills/example'
        self.target.parent.mkdir(parents=True)
        self.manifest = {'cli_version': '1.5.26', 'agents': ['claude-code', 'codex'],
                         'link_directories': ['.claude/skills'],
                         'skills': [{'name': 'example', 'source': 'owner/repo'}]}

    def test_conflicting_local_edits_survive(self):
        self.target.mkdir()
        (self.target / 'SKILL.md').write_text('personal edits')
        self.assertTrue(skills.run(self.manifest, self.home, apply=True))
        self.assertEqual((self.target / 'SKILL.md').read_text(), 'personal edits')

    def test_existing_skills_are_not_reinstalled_and_second_run_is_stable(self):
        with patch.object(skills.subprocess, 'run') as install:
            self.assertFalse(skills.run(self.manifest, self.home, apply=True))
            first = self.target.lstat().st_mtime_ns
            self.assertFalse(skills.run(self.manifest, self.home, apply=True))
            self.assertEqual(first, self.target.lstat().st_mtime_ns)
            install.assert_not_called()

    def test_redundant_copy_is_backed_up(self):
        self.target.mkdir()
        (self.target / 'SKILL.md').write_text('canonical')
        self.assertFalse(skills.run(self.manifest, self.home, apply=True))
        self.assertTrue(self.target.is_symlink())
        self.assertEqual(len(list((self.home / '.local/state/agent-setup/skill-backups').rglob('SKILL.md'))), 1)

    def test_gsd_entries_are_rejected(self):
        self.manifest['skills'][0]['name'] = 'gsd-plan-phase'
        path = self.home / 'manifest.json'
        path.write_text(json.dumps(self.manifest))
        with self.assertRaisesRegex(ValueError, 'GSD owns'):
            skills.load_manifest(path)

    def test_plugin_owned_entries_are_rejected(self):
        self.manifest['plugin_owned_skills'] = {'example@native': ['example']}
        path = self.home / 'manifest.json'
        path.write_text(json.dumps(self.manifest))
        with self.assertRaisesRegex(ValueError, 'native plugin owns'):
            skills.load_manifest(path)

    def test_missing_canonical_does_not_overwrite_an_agent_copy(self):
        import shutil
        shutil.rmtree(self.canonical)
        self.target.mkdir()
        (self.target / 'SKILL.md').write_text('personal edits')
        with patch.object(skills.subprocess, 'run') as install:
            self.assertTrue(skills.run(self.manifest, self.home, apply=True))
            install.assert_not_called()
        self.assertEqual((self.target / 'SKILL.md').read_text(), 'personal edits')

    def test_audit_reports_missing_links_without_writing(self):
        self.assertTrue(skills.run(self.manifest, self.home))
        self.assertFalse(self.target.exists())

    def test_physical_codex_copy_is_reported_and_preserved(self):
        legacy = self.home / '.codex/skills/example'
        legacy.mkdir(parents=True)
        (legacy / 'SKILL.md').write_text('different Codex content')
        self.assertTrue(skills.run(self.manifest, self.home))
        self.assertTrue(skills.run(self.manifest, self.home, apply=True))
        self.assertEqual((legacy / 'SKILL.md').read_text(), 'different Codex content')

    def test_missing_canonical_preserves_codex_copy_before_install(self):
        import shutil
        shutil.rmtree(self.canonical)
        legacy = self.home / '.codex/skills/example'
        legacy.mkdir(parents=True)
        (legacy / 'SKILL.md').write_text('different Codex content')
        with patch.object(skills.subprocess, 'run') as install:
            self.assertTrue(skills.run(self.manifest, self.home, apply=True))
            install.assert_not_called()
        self.assertTrue((legacy / 'SKILL.md').exists())

    def test_restore_rejects_alternate_home_before_repairing_links(self):
        with patch.object(skills.Path, 'home', return_value=self.home / 'real-home'):
            with self.assertRaisesRegex(ValueError, 'current user home'):
                skills.run(self.manifest, self.home, apply=True)
        self.assertFalse(self.target.exists())

    def test_gsd_and_unrelated_broken_links_are_untouched(self):
        path = self.home / '.codex/skills/gsd-plan-phase'
        path.parent.mkdir(parents=True)
        path.symlink_to('/nonexistent/gsd')
        self.assertFalse(skills.run(self.manifest, self.home, apply=True))
        self.assertTrue(path.is_symlink())


if __name__ == '__main__':
    unittest.main()
