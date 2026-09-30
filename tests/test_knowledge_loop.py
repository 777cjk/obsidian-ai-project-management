import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts" / "knowledge_loop.py"


class KnowledgeLoopTests(unittest.TestCase):
    def _run(self, *args: str):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            check=False,
            capture_output=True,
            text=True,
        )

    @staticmethod
    def _json_stdout(result: subprocess.CompletedProcess[str]) -> dict:
        if result.returncode != 0:
            raise AssertionError(f"command failed: {result.stderr}")
        return json.loads(result.stdout)

    @staticmethod
    def _sha256(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def _workspace_with_sources(self, root: Path) -> tuple[Path, Path, dict[str, str]]:
        workspace = root / "workspace"
        source = root / "source"
        source.mkdir()
        contents = {
            "approved.md": "# 人像摄影\n\n我在上海持续记录人像摄影与审美教育。\n",
            "contradiction.md": "# 待核对经历\n\n这条经历与现有来源相互矛盾。\n",
        }
        for name, text in contents.items():
            (source / name).write_text(text, encoding="utf-8")
        return workspace, source, {name: self._sha256(source / name) for name in contents}

    def test_ingest_review_query_and_record_result_form_one_closed_loop(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace, source, source_hashes = self._workspace_with_sources(root)

            initialized = self._json_stdout(
                self._run("init", "--workspace", str(workspace))
            )
            self.assertEqual(initialized["entries"], 0)

            ingested = self._json_stdout(
                self._run(
                    "ingest",
                    "--workspace",
                    str(workspace),
                    "--source",
                    str(source),
                    "--label",
                    "friend-vault-fixture",
                )
            )
            self.assertEqual(ingested["counts"]["new"], 2)
            self.assertEqual(ingested["entries"], 2)

            manifest_path = workspace / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            entries = {entry["relative_path"]: entry for entry in manifest["entries"]}
            approved = entries["approved.md"]
            contradictory = entries["contradiction.md"]

            self.assertEqual(approved["review_status"], "unreviewed")
            self.assertEqual(approved["evidence_status"], "verified_source_unreviewed")
            candidate = workspace / approved["candidate_path"]
            self.assertIn('review_status: "unreviewed"', candidate.read_text(encoding="utf-8"))
            raw_snapshot = workspace / approved["raw_path"]
            self.assertEqual(self._sha256(raw_snapshot), source_hashes["approved.md"])

            approved_review = self._json_stdout(
                self._run(
                    "review",
                    "--workspace",
                    str(workspace),
                    "--candidate",
                    approved["candidate_path"],
                    "--decision",
                    "approve",
                    "--summary",
                    "已确认上海人像摄影经历。",
                )
            )
            self.assertEqual(approved_review["review_status"], "approved")
            self.assertIsNotNone(approved_review["knowledge"])
            knowledge = workspace / approved_review["knowledge"]
            self.assertTrue(knowledge.is_file())
            knowledge_text = knowledge.read_text(encoding="utf-8")
            self.assertIn('review_status: "approved"', knowledge_text)
            self.assertIn(approved["source_id"], knowledge_text)
            self.assertIn("已确认上海人像摄影经历", knowledge_text)

            contradictory_review = self._json_stdout(
                self._run(
                    "review",
                    "--workspace",
                    str(workspace),
                    "--candidate",
                    contradictory["candidate_path"],
                    "--decision",
                    "contradictory",
                    "--note",
                    "等待另一份来源核对。",
                )
            )
            self.assertEqual(contradictory_review["review_status"], "contradictory")
            self.assertIsNone(contradictory_review["knowledge"])

            queried = self._json_stdout(
                self._run(
                    "query",
                    "--workspace",
                    str(workspace),
                    "--query",
                    "人像摄影",
                    "--scope",
                    "friend-vault-fixture",
                )
            )
            self.assertEqual(len(queried["results"]), 1)
            self.assertEqual(queried["results"][0]["source_refs"], [approved["source_id"]])
            self.assertIn(approved_review["knowledge"], queried["results"][0]["citation"])
            self.assertIn("人像摄影", queried["results"][0]["matched_tokens"])
            self.assertNotIn("人", queried["results"][0]["matched_tokens"])
            receipt_path = workspace / queried["receipt"]
            self.assertTrue(receipt_path.is_file())
            self.assertTrue(receipt_path.with_suffix(".md").is_file())
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["retrieval"]["modes"], ["keyword"])
            self.assertEqual(receipt["citations"], [queried["results"][0]["citation"]])
            self.assertIn(contradictory["source_id"], receipt["contradictions"])
            self.assertEqual(receipt["human_usefulness"], "unknown")
            self.assertEqual(receipt["application"]["result_observed"], "unknown")

            recorded = self._json_stdout(
                self._run(
                    "record-result",
                    "--workspace",
                    str(workspace),
                    "--receipt",
                    queried["receipt"],
                    "--project",
                    "朋友知识库试用",
                    "--result",
                    "回答引用了上海人像摄影来源。",
                    "--result-observed",
                    "yes",
                    "--decision-changed",
                    "no",
                    "--human-usefulness",
                    "useful",
                )
            )
            self.assertEqual(recorded["human_usefulness"], "useful")
            receipt_after = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(receipt_after["application"]["project"], "朋友知识库试用")
            self.assertEqual(receipt_after["application"]["result_observed"], "yes")
            self.assertEqual(receipt_after["application"]["decision_changed"], "no")
            self.assertEqual(receipt_after["application"]["result"], "回答引用了上海人像摄影来源。")
            self.assertEqual(receipt_after["human_usefulness"], "useful")
            receipt_markdown = receipt_path.with_suffix(".md").read_text(encoding="utf-8")
            self.assertIn("Human usefulness: `useful`", receipt_markdown)
            self.assertIn("朋友知识库试用", receipt_markdown)

            for name, expected_hash in source_hashes.items():
                self.assertEqual(self._sha256(source / name), expected_hash)

            final_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            statuses = {entry["relative_path"]: entry["review_status"] for entry in final_manifest["entries"]}
            self.assertEqual(statuses, {"approved.md": "approved", "contradiction.md": "contradictory"})

    def test_rejected_candidate_is_excluded_from_query_and_records_no_asset(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace = root / "workspace"
            source = root / "rejected.md"
            source.write_text("# 暂不采用\n\n只保留在候选层的内容。\n", encoding="utf-8")

            self._json_stdout(self._run("init", "--workspace", str(workspace)))
            ingested = self._json_stdout(
                self._run("ingest", "--workspace", str(workspace), "--source", str(source))
            )
            manifest = json.loads((workspace / "manifest.json").read_text(encoding="utf-8"))
            candidate = manifest["entries"][0]["candidate_path"]
            reviewed = self._json_stdout(
                self._run(
                    "review",
                    "--workspace",
                    str(workspace),
                    "--candidate",
                    candidate,
                    "--decision",
                    "reject",
                    "--note",
                    "来源不足。",
                )
            )
            self.assertEqual(ingested["entries"], 1)
            self.assertEqual(reviewed["review_status"], "rejected")
            self.assertIsNone(reviewed["knowledge"])
            self.assertFalse(list((workspace / "knowledge").glob("*.md")))

            queried = self._json_stdout(
                self._run(
                    "query",
                    "--workspace",
                    str(workspace),
                    "--query",
                    "候选层",
                )
            )
            self.assertEqual(queried["results"], [])
            receipt = json.loads((workspace / queried["receipt"]).read_text(encoding="utf-8"))
            self.assertEqual(receipt["missing_evidence"], ["没有命中已审核知识资产"])

    def test_empty_query_fails_closed_without_writing_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp) / "workspace"
            initialized = self._json_stdout(self._run("init", "--workspace", str(workspace)))
            self.assertEqual(initialized["entries"], 0)

            result = self._run("query", "--workspace", str(workspace), "--query", "   ")
            self.assertEqual(result.returncode, 2)
            error = json.loads(result.stderr)
            self.assertFalse(error["ok"])
            self.assertIn("query 不能为空", error["error"])
            self.assertEqual(list((workspace / "receipts").iterdir()), [])

    def test_symlink_source_and_private_output_directories_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            real_source = root / "real-source"
            real_source.mkdir()
            (real_source / "note.md").write_text("不应越过符号链接读取。\n", encoding="utf-8")
            source_link = root / "source-link"
            source_link.symlink_to(real_source, target_is_directory=True)
            workspace = root / "workspace"
            self._json_stdout(self._run("init", "--workspace", str(workspace)))

            rejected_source = self._run(
                "ingest",
                "--workspace",
                str(workspace),
                "--source",
                str(source_link),
            )
            self.assertEqual(rejected_source.returncode, 2)
            self.assertIn("符号链接", rejected_source.stderr)
            self.assertFalse(list((workspace / "raw").glob("*")))

            outside = root / "outside"
            outside.mkdir()
            redirected_workspace = root / "redirected-workspace"
            redirected_workspace.mkdir()
            (redirected_workspace / "raw").symlink_to(outside, target_is_directory=True)
            rejected_output = self._run("init", "--workspace", str(redirected_workspace))
            self.assertEqual(rejected_output.returncode, 2)
            self.assertIn("符号链接", rejected_output.stderr)
            self.assertEqual(list(outside.iterdir()), [])

    def test_queries_in_one_second_get_distinct_receipts(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace = root / "workspace"
            source = root / "source.md"
            source.write_text("# 可检索\n\n稳定的知识内容。\n", encoding="utf-8")
            self._json_stdout(self._run("init", "--workspace", str(workspace)))
            self._json_stdout(
                self._run("ingest", "--workspace", str(workspace), "--source", str(source))
            )
            manifest = json.loads((workspace / "manifest.json").read_text(encoding="utf-8"))
            self._json_stdout(
                self._run(
                    "review",
                    "--workspace",
                    str(workspace),
                    "--candidate",
                    manifest["entries"][0]["candidate_path"],
                    "--decision",
                    "approve",
                )
            )
            first = self._json_stdout(
                self._run("query", "--workspace", str(workspace), "--query", "知识")
            )
            second = self._json_stdout(
                self._run("query", "--workspace", str(workspace), "--query", "知识")
            )
            self.assertNotEqual(first["receipt"], second["receipt"])
            self.assertEqual(len(list((workspace / "receipts").glob("query-*.json"))), 2)

    def test_record_result_cannot_mutate_manifest_or_invalid_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp) / "workspace"
            self._json_stdout(self._run("init", "--workspace", str(workspace)))
            manifest_path = workspace / "manifest.json"
            before = manifest_path.read_bytes()
            rejected_manifest = self._run(
                "record-result",
                "--workspace",
                str(workspace),
                "--receipt",
                "manifest.json",
                "--project",
                "should-not-write",
            )
            self.assertEqual(rejected_manifest.returncode, 2)
            self.assertIn("receipts 下", rejected_manifest.stderr)
            self.assertEqual(manifest_path.read_bytes(), before)

            invalid_receipt = workspace / "receipts" / "not-a-query.json"
            invalid_receipt.write_text("{}\n", encoding="utf-8")
            rejected_schema = self._run(
                "record-result",
                "--workspace",
                str(workspace),
                "--receipt",
                str(invalid_receipt),
            )
            self.assertEqual(rejected_schema.returncode, 2)
            self.assertIn("有效的 query receipt", rejected_schema.stderr)

    def test_modified_source_marks_prior_approved_asset_superseded(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace = root / "workspace"
            source = root / "source.md"
            source.write_text("旧版本经历\n", encoding="utf-8")
            self._json_stdout(self._run("init", "--workspace", str(workspace)))
            self._json_stdout(
                self._run("ingest", "--workspace", str(workspace), "--source", str(source))
            )
            manifest = json.loads((workspace / "manifest.json").read_text(encoding="utf-8"))
            self._json_stdout(
                self._run(
                    "review",
                    "--workspace",
                    str(workspace),
                    "--candidate",
                    manifest["entries"][0]["candidate_path"],
                    "--decision",
                    "approve",
                )
            )
            source.write_text("新版本经历\n", encoding="utf-8")
            updated = self._json_stdout(
                self._run("ingest", "--workspace", str(workspace), "--source", str(source))
            )
            self.assertEqual(updated["counts"]["modified"], 1)
            manifest_after = json.loads((workspace / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(len(manifest_after["history"]), 1)
            self.assertEqual(manifest_after["history"][0]["record_status"], "superseded")
            old_query = self._json_stdout(
                self._run("query", "--workspace", str(workspace), "--query", "旧版本")
            )
            self.assertEqual(old_query["results"], [])


if __name__ == "__main__":
    unittest.main()
