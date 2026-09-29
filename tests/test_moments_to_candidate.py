import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts" / "moments_to_candidate.py"


class MomentsCandidateTests(unittest.TestCase):
    def _run(self, input_path: Path, output_dir: Path, *args: str):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--input", str(input_path), "--output-dir", str(output_dir), *args],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_raw_export_filters_to_self_and_deduplicates(self):
        payload = {
            "account": {"nickname": "小七"},
            "moments": [
                {"id": "1", "content": "在上海拍了一组人像。", "publish_time": 1710000000, "images": ["img-1"]},
                {"id": "1", "content": "在上海拍了一组人像。", "publish_time": 1710000000, "images": ["img-1"]},
                {"id": "2", "nickname": "朋友", "content": "周末去看展。", "publish_time": 1710086400},
            ],
        }
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "moments.json"
            output = root / "staging"
            source.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            result = self._run(source, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads(result.stdout)
            self.assertEqual(summary["records_total"], 2)
            self.assertEqual(summary["records_included"], 1)
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["duplicates_removed"], 1)
            self.assertEqual(manifest["self_records"], 1)
            candidate = (output / "朋友圈-来源候选.md").read_text(encoding="utf-8")
            self.assertIn("在上海拍了一组人像", candidate)
            self.assertNotIn("周末去看展", candidate)
            self.assertEqual((output.stat().st_mode & 0o777), 0o700)
            self.assertEqual((output / "manifest.json").stat().st_mode & 0o777, 0o600)

    def test_include_nonself_and_jsonl_input(self):
        records = [
            {"schema_version": 1, "source_record_id": "a", "author_name": "小七", "is_self": True, "timestamp": 1, "content": "本人记录"},
            {"schema_version": 1, "source_record_id": "b", "author_name": "朋友", "is_self": False, "timestamp": 2, "content": "朋友记录"},
        ]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "moments.jsonl"
            output = root / "staging"
            source.write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in records) + "\n", encoding="utf-8")
            result = self._run(source, output, "--include-nonself")
            self.assertEqual(result.returncode, 0, result.stderr)
            candidate = (output / "朋友圈-来源候选.md").read_text(encoding="utf-8")
            self.assertIn("本人记录", candidate)
            self.assertIn("朋友记录", candidate)
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["scope"], "all")
            self.assertEqual(manifest["records_included"], 2)

    def test_symlink_input_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            real = root / "real.json"
            link = root / "link.json"
            real.write_text('{"moments": [{"id": "1", "content": "x", "publish_time": 1}]}', encoding="utf-8")
            if not hasattr(os, "symlink"):
                self.skipTest("symlink is unavailable")
            link.symlink_to(real)
            result = self._run(link, root / "staging")
            self.assertEqual(result.returncode, 2)
            self.assertIn("符号链接", result.stdout)


if __name__ == "__main__":
    unittest.main()
