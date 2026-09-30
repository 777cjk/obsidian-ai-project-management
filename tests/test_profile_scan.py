import json
import hashlib
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts" / "profile_scan.py"


class ProfileScanTests(unittest.TestCase):
    def _run(self, *args: str):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            check=False,
            capture_output=True,
            text=True,
        )

    @staticmethod
    def _json(result: subprocess.CompletedProcess[str]) -> dict:
        if result.returncode != 0:
            raise AssertionError(f"command failed: {result.stderr}")
        return json.loads(result.stdout)

    def _fixture(self, root: Path) -> tuple[Path, Path]:
        home = root / "friend-home"
        workspace = root / "private-staging"
        (home / "Desktop").mkdir(parents=True)
        (home / "Documents" / "项目Alpha").mkdir(parents=True)
        (home / "Documents" / ".ssh").mkdir(parents=True)
        (home / "Documents" / "关于我.md").write_text(
            "# 关于我\n\n我是一名摄影师，目前负责审美教育和个人项目。\n",
            encoding="utf-8",
        )
        (home / "Documents" / "项目Alpha" / "README.md").write_text(
            "# 项目 Alpha\n\n当前项目用于整理客户资料。\n",
            encoding="utf-8",
        )
        (home / "Documents" / "credentials.json").write_text(
            '{"api_key":"should-not-be-read"}\n', encoding="utf-8"
        )
        (home / "Documents" / ".ssh" / "id_rsa").write_text(
            "PRIVATE KEY\n", encoding="utf-8"
        )
        (home / "Documents" / "参考资料.pdf").write_bytes(b"%PDF-1.7 not parsed")
        docx = home / "Desktop" / "工作简介.docx"
        with zipfile.ZipFile(docx, "w") as archive:
            archive.writestr(
                "word/document.xml",
                "<document><body><p>我在上海从事人像摄影。</p></body></document>",
            )
        xlsx = home / "Desktop" / "项目数据.xlsx"
        with zipfile.ZipFile(xlsx, "w") as archive:
            archive.writestr(
                "xl/sharedStrings.xml",
                "<sst xmlns='http://schemas.openxmlformats.org/spreadsheetml/2006/main'><si><t>项目 Alpha</t></si></sst>",
            )
            archive.writestr(
                "xl/worksheets/sheet1.xml",
                "<worksheet xmlns='http://schemas.openxmlformats.org/spreadsheetml/2006/main'><sheetData><row><c t='s'><v>0</v></c></row></sheetData></worksheet>",
            )
        return home, workspace

    def test_plan_is_preview_only_and_excludes_sensitive_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home, workspace = self._fixture(root)
            result = self._run("plan", "--workspace", str(workspace), "--home", str(home))
            payload = self._json(result)
            self.assertFalse(payload["scope_confirmed"])
            self.assertGreaterEqual(payload["counts"]["selected"], 3)
            self.assertIn("credential_or_secret_pattern", payload["skipped_counts"])
            self.assertIn("sensitive_or_cache_directory", payload["skipped_counts"])
            self.assertIn("metadata_only_or_unsupported_format", payload["skipped_counts"])
            self.assertTrue((workspace / "scan-plan.json").is_file())
            self.assertFalse((workspace / "manifest.json").exists())
            plan = json.loads((workspace / "scan-plan.json").read_text(encoding="utf-8"))
            selected_paths = {item["path"] for item in plan["files"]}
            self.assertNotIn(str(home / "Documents" / "credentials.json"), selected_paths)
            self.assertNotIn(str(home / "Documents" / ".ssh" / "id_rsa"), selected_paths)

    def test_plan_stops_at_discovery_budget(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home, workspace = self._fixture(root)
            result = self._json(
                self._run(
                    "plan",
                    "--workspace",
                    str(workspace),
                    "--home",
                    str(home),
                    "--max-discovery-files",
                    "1",
                )
            )
            self.assertTrue(result["counts"]["discovery_budget_reached"])
            self.assertEqual(result["counts"]["files_examined"], 1)
            self.assertEqual(result["counts"]["selected"], 1)

    def test_collect_rejects_tampered_selection_budget(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home, workspace = self._fixture(root)
            self._json(
                self._run(
                    "plan",
                    "--workspace",
                    str(workspace),
                    "--home",
                    str(home),
                    "--max-files",
                    "1",
                    "--max-total-bytes",
                    "200",
                )
            )
            plan_path = workspace / "scan-plan.json"
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            self.assertEqual(len(plan["files"]), 1)
            extra = next(
                item for item in home.joinpath("Documents").rglob("*.md")
                if str(item.resolve()) != plan["files"][0]["path"]
            )
            stat = extra.stat()
            plan["files"].append(
                {
                    **plan["files"][0],
                    "path": str(extra.resolve()),
                    "relative_path": extra.relative_to(home / "Documents").as_posix(),
                    "size_bytes": stat.st_size,
                    "mtime_ns": stat.st_mtime_ns,
                    "st_dev": stat.st_dev,
                    "st_ino": stat.st_ino,
                }
            )
            plan_path.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
            blocked = self._run("collect", "--workspace", str(workspace), "--confirm-scope")
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn("文件数超过预览预算", blocked.stderr)
            self.assertFalse((workspace / "manifest.json").exists())

    def test_collect_rejects_directory_root_replaced_by_symlink(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home, workspace = self._fixture(root)
            self._json(self._run("plan", "--workspace", str(workspace), "--home", str(home)))
            original = home / "Documents"
            moved = home / "Documents-original"
            outside = root / "outside"
            original.rename(moved)
            outside.mkdir()
            (outside / "关于我.md").write_text("OUTSIDE\n", encoding="utf-8")
            original.symlink_to(outside, target_is_directory=True)
            collected = self._json(
                self._run("collect", "--workspace", str(workspace), "--confirm-scope")
            )
            self.assertTrue(collected["errors"])
            self.assertTrue(
                any("扫描根变为符号链接" in item["error"] for item in collected["errors"])
            )
            raw_files = list((workspace / "raw").rglob("*")) if (workspace / "raw").exists() else []
            text_raw = []
            for path in raw_files:
                if not path.is_file() or path.suffix.casefold() not in {".md", ".txt", ".json", ".yaml", ".yml"}:
                    continue
                text_raw.append(path.read_text(encoding="utf-8"))
            self.assertFalse(any("OUTSIDE" in text for text in text_raw))

    def test_collect_requires_scope_confirmation_and_builds_profile_candidates(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home, workspace = self._fixture(root)
            originals = {
                path: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in home.rglob("*")
                if path.is_file()
            }
            self._json(self._run("plan", "--workspace", str(workspace), "--home", str(home)))
            blocked = self._run("collect", "--workspace", str(workspace))
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn("--confirm-scope", blocked.stderr)

            collected = self._json(
                self._run("collect", "--workspace", str(workspace), "--confirm-scope")
            )
            self.assertEqual(collected["counts"]["errors"], 0)
            self.assertEqual(len(collected["profile_candidates"]), 2)
            profile = workspace / collected["profile_candidates"][0]
            project = workspace / collected["profile_candidates"][1]
            self.assertIn('review_status: unreviewed', profile.read_text(encoding="utf-8"))
            self.assertIn("我是一名摄影师", profile.read_text(encoding="utf-8"))
            self.assertIn("我在上海从事人像摄影", profile.read_text(encoding="utf-8"))
            xlsx_import = next(item for item in collected["imported"] if item["path"].endswith("项目数据.xlsx"))
            self.assertIn("项目 Alpha", (workspace / xlsx_import["candidate"]).read_text(encoding="utf-8"))
            self.assertIn("资料分类目录候选", project.read_text(encoding="utf-8"))
            self.assertIn("当前项目", project.read_text(encoding="utf-8"))
            self.assertFalse((workspace / "raw" / "credentials.json").exists())
            self.assertEqual(
                originals,
                {
                    path: hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in originals
                },
            )

            missing_confirm = self._run(
                "review-profile", "--workspace", str(workspace), "--decision", "approve"
            )
            self.assertNotEqual(missing_confirm.returncode, 0)
            approved = self._json(
                self._run(
                    "review-profile",
                    "--workspace",
                    str(workspace),
                    "--decision",
                    "approve",
                    "--confirm",
                )
            )
            self.assertIn("knowledge/profile-context.md", approved["knowledge_paths"])
            repeat = self._run(
                "collect", "--workspace", str(workspace), "--confirm-scope"
            )
            self.assertNotEqual(repeat.returncode, 0)
            self.assertIn("approved profile-context", repeat.stderr)
            context = self._json(self._run("context", "--workspace", str(workspace)))
            self.assertEqual(context["context_status"], "approved")
            self.assertIn("个人背景档案", context["context"])
            self.assertIn("项目地图", context["context"])
            self.assertLessEqual(context["context_chars"], context["context_budget"])

            status = self._json(self._run("status", "--workspace", str(workspace)))
            self.assertEqual(status["stage"], "ready_for_context")

            codex_home = root / "codex-home"
            codex_dir = codex_home / ".codex"
            codex_dir.mkdir(parents=True)
            agents = codex_dir / "AGENTS.md"
            agents.write_text("# Existing user rules\n\nKeep this text.\n", encoding="utf-8")
            missing_install_confirm = self._run(
                "install-codex-context",
                "--workspace",
                str(workspace),
                "--home",
                str(codex_home),
            )
            self.assertNotEqual(missing_install_confirm.returncode, 0)
            installed = self._json(
                self._run(
                    "install-codex-context",
                    "--workspace",
                    str(workspace),
                    "--home",
                    str(codex_home),
                    "--confirm",
                )
            )
            self.assertTrue(installed["updated"])
            agents_text = agents.read_text(encoding="utf-8")
            self.assertIn("# Existing user rules", agents_text)
            self.assertIn(str(workspace / "knowledge/profile-context.md"), agents_text)
            self.assertEqual(len(list(codex_dir.glob("AGENTS.md.profile-context-backup-*"))), 1)
            installed_again = self._json(
                self._run(
                    "install-codex-context",
                    "--workspace",
                    str(workspace),
                    "--home",
                    str(codex_home),
                    "--confirm",
                )
            )
            self.assertFalse(installed_again["updated"])
            self.assertEqual(len(list(codex_dir.glob("AGENTS.md.profile-context-backup-*"))), 1)

            removed = self._json(
                self._run(
                    "remove-codex-context",
                    "--home",
                    str(codex_home),
                    "--confirm",
                )
            )
            self.assertTrue(removed["removed"])
            self.assertIn("# Existing user rules", agents.read_text(encoding="utf-8"))
            self.assertNotIn("Approved Personal Context", agents.read_text(encoding="utf-8"))

    def test_collect_skips_secret_like_content_even_when_filename_is_generic(self):
        with tempfile.TemporaryDirectory() as temp:
            home, workspace = self._fixture(Path(temp))
            secret_file = home / "Documents" / "meeting-notes.md"
            secret_file.write_text("# notes\napi_key: sk-live-example\n", encoding="utf-8")
            self._json(self._run("plan", "--workspace", str(workspace), "--home", str(home)))
            collected = self._json(
                self._run("collect", "--workspace", str(workspace), "--confirm-scope")
            )
            errors = {item["path"]: item["error"] for item in collected["errors"]}
            secret_key = str(secret_file.resolve())
            self.assertIn(secret_key, errors)
            self.assertIn("credential_or_secret_pattern", errors[secret_key])
            manifest = json.loads((workspace / "manifest.json").read_text(encoding="utf-8"))
            self.assertNotIn(secret_key, {entry.get("locator") for entry in manifest["entries"]})


if __name__ == "__main__":
    unittest.main()
