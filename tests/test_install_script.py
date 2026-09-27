import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class InstallScriptTests(unittest.TestCase):
    def _source(self, root: Path) -> Path:
        source = root / "source"
        scripts = source / "scripts"
        scripts.mkdir(parents=True)
        shutil.copy2(ROOT / "scripts/install.sh", scripts / "install.sh")

        verify = scripts / "verify.sh"
        verify.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        verify.chmod(0o755)
        (source / "SKILL.md").write_text("new skill package\n", encoding="utf-8")
        (source / ".git").mkdir()
        (source / ".git/config").write_text("private checkout data\n", encoding="utf-8")
        return source

    def _run(self, source: Path, target: Path, *args: str):
        env = os.environ.copy()
        env["PYTHON_BIN"] = sys.executable
        return subprocess.run(
            [str(source / "scripts/install.sh"), "--target", str(target), *args],
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )

    def test_install_copies_package_without_git_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = self._source(root)
            target = root / "host skills" / "obsidian skill"

            result = self._run(source, target)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((target / "SKILL.md").read_text(encoding="utf-8"), "new skill package\n")
            self.assertFalse((target / ".git").exists())

    def test_existing_target_requires_replace_and_keeps_timestamped_backup(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = self._source(root)
            target = root / "host" / "skill"
            target.mkdir(parents=True)
            (target / "previous.txt").write_text("old install\n", encoding="utf-8")

            rejected = self._run(source, target)
            self.assertEqual(rejected.returncode, 3)
            self.assertEqual((target / "previous.txt").read_text(encoding="utf-8"), "old install\n")

            installed = self._run(source, target, "--replace")

            self.assertEqual(installed.returncode, 0, installed.stderr)
            self.assertEqual((target / "SKILL.md").read_text(encoding="utf-8"), "new skill package\n")
            backups = list((target.parent / ".skill.backups").iterdir())
            self.assertEqual(len(backups), 1)
            self.assertEqual((backups[0] / "previous.txt").read_text(encoding="utf-8"), "old install\n")

    def test_target_inside_source_checkout_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = self._source(root)

            result = self._run(source, source / "installed")

            self.assertEqual(result.returncode, 2)
            self.assertIn("outside the source checkout", result.stderr)
            self.assertFalse((source / "installed").exists())


if __name__ == "__main__":
    unittest.main()
