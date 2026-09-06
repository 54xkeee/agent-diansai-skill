"""Isolated installer checks; retain fixtures for inspection, never touch user skills."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SHELL = shutil.which('powershell')
FIXTURES = Path(tempfile.mkdtemp(prefix='diansai-skill-install-test-')).resolve()


def ps_quote(value):
    return "'" + str(value).replace("'", "''") + "'"


@unittest.skipUnless(SHELL, 'Windows PowerShell required')
class InstallTests(unittest.TestCase):
    def setUp(self):
        self.home = FIXTURES / self._testMethodName

    def install(self, options='', home=True, env=None):
        command = '& ' + ps_quote(ROOT / 'install.ps1')
        if home:
            command += ' -CodexHome ' + ps_quote(self.home)
        command += ' ' + options
        return subprocess.run(
            [SHELL, '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', command],
            capture_output=True, env=env, timeout=90,
        )

    def assert_ok(self, result):
        self.assertEqual(result.returncode, 0, repr(result.stderr))

    def assert_copied(self, name):
        source = ROOT / 'skills' / name
        target = self.home / 'skills' / name
        expected = [p for p in source.rglob('*') if p.is_file()]
        self.assertTrue(expected)
        for file in expected:
            installed = target / file.relative_to(source)
            self.assertTrue(installed.is_file(), str(installed))
            self.assertEqual(hashlib.sha256(file.read_bytes()).digest(),
                             hashlib.sha256(installed.read_bytes()).digest())

    def test_default_one_skill(self):
        self.assert_ok(self.install())
        self.assertEqual([p.name for p in (self.home / 'skills').iterdir()], ['diansai-collab'])
        self.assert_copied('diansai-collab')

    def test_backup_and_unrelated_preserved(self):
        target = self.home / 'skills' / 'diansai-collab'
        target.mkdir(parents=True)
        (target / 'SKILL.md').write_bytes(b'local customization')
        (target / 'personal-note.txt').write_bytes(b'keep me')
        other = self.home / 'skills' / 'unrelated'
        other.mkdir()
        (other / 'SKILL.md').write_bytes(b'not part of this update')
        self.assert_ok(self.install())
        backups = list((self.home / 'skill-backups').glob('*/diansai-collab'))
        self.assertEqual(len(backups), 1)
        self.assertEqual((backups[0] / 'SKILL.md').read_bytes(), b'local customization')
        self.assertEqual((backups[0] / 'personal-note.txt').read_bytes(), b'keep me')
        self.assertEqual((target / 'personal-note.txt').read_bytes(), b'keep me')
        self.assertEqual((other / 'SKILL.md').read_bytes(), b'not part of this update')
        self.assert_copied('diansai-collab')

    def test_selected_legacy(self):
        self.assert_ok(self.install('-SkillName stm32-keil'))
        self.assertEqual([p.name for p in (self.home / 'skills').iterdir()], ['stm32-keil'])
        self.assert_copied('stm32-keil')

    def test_all_skills(self):
        self.assert_ok(self.install('-All'))
        expected = {p.name for p in (ROOT / 'skills').iterdir() if p.is_dir()}
        self.assertEqual(expected, {p.name for p in (self.home / 'skills').iterdir()})
        self.assertEqual(len(expected), 7)
        for name in expected:
            self.assert_copied(name)

    def test_bad_name_before_writes(self):
        result = self.install("-SkillName '../escape'")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b'Invalid skill name', result.stderr)
        self.assertFalse(self.home.exists())

    def test_missing_second_source_before_writes(self):
        result = self.install("-SkillName @('diansai-collab','missing-skill')")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b'Skill source missing', result.stderr)
        self.assertFalse(self.home.exists())

    def test_same_source_rejected(self):
        before = (ROOT / 'skills' / 'diansai-collab' / 'SKILL.md').read_bytes()
        self.home = ROOT
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b'Source and installation path must differ', result.stderr)
        self.assertEqual((ROOT / 'skills' / 'diansai-collab' / 'SKILL.md').read_bytes(), before)

    def test_env_home(self):
        env = os.environ.copy()
        env['CODEX_HOME'] = str(self.home)
        self.assert_ok(self.install(home=False, env=env))
        self.assert_copied('diansai-collab')

    def test_junction_rejected(self):
        destination = FIXTURES / 'linked-destination'
        destination.mkdir()
        self.home.mkdir()
        junction = self.home / 'skills'
        result = subprocess.run(
            [SHELL, '-NoProfile', '-Command',
             'New-Item -ItemType Junction -Path ' + ps_quote(junction)
             + ' -Target ' + ps_quote(destination) + ' | Out-Null'],
            capture_output=True, timeout=30,
        )
        self.assert_ok(result)
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b'Linked path needs manual review', result.stderr)
        self.assertEqual(list(destination.iterdir()), [])


if __name__ == '__main__':
    print('Retained isolated fixtures:', FIXTURES, flush=True)
    unittest.main(verbosity=2)
