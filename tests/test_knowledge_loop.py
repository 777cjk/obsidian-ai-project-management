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
    def test_review_examples_use_full_ingest_path_without_reprefixing(self):
        for document in ("README.md", "SKILL.md"):
            text = (ROOT / document).read_text(encoding="utf-8")
            self.assertIn('candidate_path="PASTE_ONE_FULL_CANDIDATE_PATH_HERE"', text)
            self.assertIn('--candidate "$candidate_path"', text)
            self.assertNotIn("--candidate candidates/", text)
            self.assertIn("--result-observed unknown", text)
            self.assertIn("--decision-changed unknown", text)
            self.assertIn("--human-usefulness unknown", text)

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
            self.assertEqual(
                set(ingested["candidates"]),
                {approved["candidate_path"], contradictory["candidate_path"]},
            )

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

    def test_overlap_and_internal_obsidian_directories_are_excluded(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace = root / "workspace"
            source = root / "source"
            (source / ".obsidian").mkdir(parents=True)
            (source / ".trash").mkdir()
            (source / ".vscode").mkdir()
            (source / "keep.md").write_text("保留内容\n", encoding="utf-8")
            (source / ".obsidian" / "hidden.md").write_text("不应读取\n", encoding="utf-8")
            (source / ".trash" / "deleted.md").write_text("不应读取\n", encoding="utf-8")
            (source / ".vscode" / "settings.md").write_text("不应读取\n", encoding="utf-8")

            self._json_stdout(self._run("init", "--workspace", str(workspace)))
            ingested = self._json_stdout(
                self._run("ingest", "--workspace", str(workspace), "--source", str(source))
            )
            self.assertEqual(ingested["counts"]["new"], 1)
            manifest = json.loads((workspace / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual([entry["relative_path"] for entry in manifest["entries"]], ["keep.md"])

            rejected = self._run(
                "ingest", "--workspace", str(source), "--source", str(source)
            )
            self.assertEqual(rejected.returncode, 2)
            self.assertIn("重叠", rejected.stderr)

    def test_duplicate_labels_keep_distinct_source_roots_and_scope_filters(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace = root / "workspace"
            source_a = root / "source-a"
            source_b = root / "source-b"
            source_a.mkdir()
            source_b.mkdir()
            (source_a / "same.md").write_text("甲来源的摄影知识\n", encoding="utf-8")
            (source_b / "same.md").write_text("乙来源的摄影知识\n", encoding="utf-8")
            self._json_stdout(self._run("init", "--workspace", str(workspace)))
            for source in (source_a, source_b):
                self._json_stdout(
                    self._run(
                        "ingest", "--workspace", str(workspace), "--source", str(source),
                        "--label", "same-label",
                    )
                )
            manifest = json.loads((workspace / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(len(manifest["entries"]), 2)
            self.assertEqual(len({entry["source_id"] for entry in manifest["entries"]}), 2)
            self.assertEqual(len({entry["source_root_id"] for entry in manifest["entries"]}), 2)
            for entry in manifest["entries"]:
                self._json_stdout(
                    self._run(
                        "review", "--workspace", str(workspace), "--candidate", entry["candidate_path"],
                        "--decision", "approve",
                    )
                )
            scope = manifest["entries"][0]["source_root_id"]
            queried = self._json_stdout(
                self._run(
                    "query", "--workspace", str(workspace), "--query", "摄影知识",
                    "--scope", scope,
                )
            )
            self.assertEqual(len(queried["results"]), 1)
            self.assertEqual(queried["results"][0]["source_root_id"], scope)

    def test_deleted_source_becomes_stale_and_is_not_queryable(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace = root / "workspace"
            source = root / "source"
            source.mkdir()
            (source / "keep.md").write_text("仍然保留的知识\n", encoding="utf-8")
            (source / "gone.md").write_text("删除后不应返回的知识\n", encoding="utf-8")
            self._json_stdout(self._run("init", "--workspace", str(workspace)))
            self._json_stdout(self._run("ingest", "--workspace", str(workspace), "--source", str(source)))
            manifest = json.loads((workspace / "manifest.json").read_text(encoding="utf-8"))
            for entry in manifest["entries"]:
                self._json_stdout(
                    self._run(
                        "review", "--workspace", str(workspace), "--candidate", entry["candidate_path"],
                        "--decision", "approve",
                    )
                )
            (source / "gone.md").unlink()
            updated = self._json_stdout(
                self._run("ingest", "--workspace", str(workspace), "--source", str(source))
            )
            self.assertEqual(updated["counts"]["stale"], 1)
            after = json.loads((workspace / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual([entry["relative_path"] for entry in after["entries"]], ["keep.md"])
            stale = [entry for entry in after["history"] if entry["relative_path"] == "gone.md"]
            self.assertEqual(len(stale), 1)
            self.assertEqual(stale[0]["record_status"], "stale")
            queried = self._json_stdout(
                self._run("query", "--workspace", str(workspace), "--query", "删除后")
            )
            self.assertEqual(queried["results"], [])

    def test_partial_ingest_is_explicit_and_strict_returns_nonzero(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace = root / "workspace"
            source = root / "source"
            source.mkdir()
            (source / "good.md").write_text("可读内容\n", encoding="utf-8")
            (source / "broken.txt").write_bytes(b"\xff\xfe\x00")
            self._json_stdout(self._run("init", "--workspace", str(workspace)))
            partial = self._json_stdout(
                self._run("ingest", "--workspace", str(workspace), "--source", str(source))
            )
            self.assertEqual(partial["status"], "partial")
            self.assertFalse(partial["complete"])
            self.assertEqual(len(partial["errors"]), 1)
            strict = self._run(
                "ingest", "--workspace", str(workspace), "--source", str(source), "--strict"
            )
            self.assertEqual(strict.returncode, 2)
            self.assertIn("--strict", strict.stderr)

    def test_scope_and_context_budget_are_applied_to_results(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace = root / "workspace"
            source_a = root / "source-a"
            source_b = root / "source-b"
            source_a.mkdir()
            source_b.mkdir()
            (source_a / "a.md").write_text("目标词 " + ("甲" * 100) + "\n", encoding="utf-8")
            (source_b / "b.md").write_text("目标词 " + ("乙" * 100) + "\n", encoding="utf-8")
            self._json_stdout(self._run("init", "--workspace", str(workspace)))
            for source in (source_a, source_b):
                self._json_stdout(self._run("ingest", "--workspace", str(workspace), "--source", str(source)))
            manifest = json.loads((workspace / "manifest.json").read_text(encoding="utf-8"))
            for entry in manifest["entries"]:
                self._json_stdout(self._run("review", "--workspace", str(workspace), "--candidate", entry["candidate_path"], "--decision", "approve"))
            scope = manifest["entries"][0]["source_root_id"]
            queried = self._json_stdout(self._run("query", "--workspace", str(workspace), "--query", "目标词", "--scope", scope, "--context-budget", "12"))
            self.assertEqual(len(queried["results"]), 1)
            self.assertLessEqual(sum(item["context_chars"] for item in queried["results"]), 12)
            self.assertLessEqual(len(queried["results"][0]["snippet"]), 12)
            receipt = json.loads((workspace / queried["receipt"]).read_text(encoding="utf-8"))
            self.assertEqual(receipt["retrieval"]["context_chars_used"], queried["results"][0]["context_chars"])

    def test_record_result_appends_application_history_and_summary_is_single(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace = root / "workspace"
            source = root / "source.md"
            source.write_text("可应用的知识\n", encoding="utf-8")
            self._json_stdout(self._run("init", "--workspace", str(workspace)))
            self._json_stdout(self._run("ingest", "--workspace", str(workspace), "--source", str(source)))
            manifest = json.loads((workspace / "manifest.json").read_text(encoding="utf-8"))
            reviewed = self._json_stdout(self._run("review", "--workspace", str(workspace), "--candidate", manifest["entries"][0]["candidate_path"], "--decision", "approve", "--summary", "唯一摘要标记"))
            knowledge = (workspace / reviewed["knowledge"]).read_text(encoding="utf-8")
            self.assertEqual(knowledge.count("唯一摘要标记"), 1)
            queried = self._json_stdout(self._run("query", "--workspace", str(workspace), "--query", "知识"))
            for project, result in (("第一次", "第一次结果"), ("第二次", "第二次结果")):
                self._json_stdout(self._run("record-result", "--workspace", str(workspace), "--receipt", queried["receipt"], "--project", project, "--result", result, "--human-usefulness", "useful"))
            receipt_path = workspace / queried["receipt"]
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(len(receipt["application_events"]), 2)
            self.assertEqual(receipt["application_events"][0]["result"], "第一次结果")
            self.assertEqual(receipt["application_events"][1]["result"], "第二次结果")
            markdown = receipt_path.with_suffix(".md").read_text(encoding="utf-8")
            self.assertIn("Event 1", markdown)
            self.assertIn("Event 2", markdown)
            self.assertIn("第一次结果", markdown)
            self.assertIn("第二次结果", markdown)

    def test_record_result_preserves_heading_like_text_inside_result(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace = root / "workspace"
            source = root / "source.md"
            source.write_text("可应用的知识\n", encoding="utf-8")
            self._json_stdout(self._run("init", "--workspace", str(workspace)))
            self._json_stdout(self._run("ingest", "--workspace", str(workspace), "--source", str(source)))
            manifest = json.loads((workspace / "manifest.json").read_text(encoding="utf-8"))
            self._json_stdout(
                self._run(
                    "review", "--workspace", str(workspace),
                    "--candidate", manifest["entries"][0]["candidate_path"], "--decision", "approve",
                )
            )
            queried = self._json_stdout(self._run("query", "--workspace", str(workspace), "--query", "知识"))
            embedded = "第一结果\n\n## Application History\n\n嵌入标题"
            self._json_stdout(
                self._run(
                    "record-result", "--workspace", str(workspace), "--receipt", queried["receipt"],
                    "--result", embedded, "--human-usefulness", "useful",
                )
            )
            self._json_stdout(
                self._run(
                    "record-result", "--workspace", str(workspace), "--receipt", queried["receipt"],
                    "--result", "第二结果", "--human-usefulness", "useful",
                )
            )
            markdown = (workspace / queried["receipt"]).with_suffix(".md").read_text(encoding="utf-8")
            self.assertEqual(markdown.count("## Application History"), 2)
            self.assertIn(embedded, markdown)
            self.assertIn("第二结果", markdown)

    def test_query_rejects_non_positive_limit_and_context_budget(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace = root / "workspace"
            source = root / "source.md"
            source.write_text("可检索内容\n", encoding="utf-8")
            self._json_stdout(self._run("init", "--workspace", str(workspace)))
            self._json_stdout(self._run("ingest", "--workspace", str(workspace), "--source", str(source)))
            manifest = json.loads((workspace / "manifest.json").read_text(encoding="utf-8"))
            self._json_stdout(self._run("review", "--workspace", str(workspace), "--candidate", manifest["entries"][0]["candidate_path"], "--decision", "approve"))
            for option, value, message in (("--limit", "0", "limit 必须至少为 1"), ("--context-budget", "0", "context-budget 必须至少为 1")):
                rejected = self._run("query", "--workspace", str(workspace), "--query", "内容", option, value)
                self.assertEqual(rejected.returncode, 2)
                self.assertIn(message, rejected.stderr)

    def test_status_and_next_are_read_only_and_follow_the_closed_loop(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace = root / "workspace"
            source = root / "source.md"
            source.write_text("# 摄影知识\n\n上海人像摄影实践。\n", encoding="utf-8")

            before = set(root.rglob("*"))
            uninitialized = self._json_stdout(self._run("status", "--workspace", str(workspace)))
            self.assertEqual(uninitialized["stage"], "uninitialized")
            self.assertEqual(uninitialized["next"], "init")
            self.assertFalse(workspace.exists())
            next_uninitialized = self._json_stdout(self._run("next", "--workspace", str(workspace)))
            self.assertEqual(next_uninitialized, uninitialized)
            self.assertEqual(set(root.rglob("*")), before)

            self._json_stdout(self._run("init", "--workspace", str(workspace)))
            after_init = {path: path.read_bytes() for path in workspace.rglob("*") if path.is_file()}
            empty = self._json_stdout(self._run("status", "--workspace", str(workspace)))
            self.assertEqual(empty["stage"], "needs_ingest")
            self.assertEqual(empty["next"], "ingest")
            self.assertEqual(
                {path: path.read_bytes() for path in workspace.rglob("*") if path.is_file()},
                after_init,
            )

            ingested = self._json_stdout(
                self._run("ingest", "--workspace", str(workspace), "--source", str(source))
            )
            self.assertEqual(ingested["entries"], 1)
            pending_review = self._json_stdout(self._run("next", "--workspace", str(workspace)))
            self.assertEqual(pending_review["stage"], "needs_review")
            self.assertEqual(pending_review["next"], "review")
            self.assertEqual(pending_review["counts"]["active_unreviewed"], 1)
            manifest = json.loads((workspace / "manifest.json").read_text(encoding="utf-8"))
            candidate = manifest["entries"][0]["candidate_path"]
            self._json_stdout(
                self._run(
                    "review", "--workspace", str(workspace), "--candidate", candidate,
                    "--decision", "approve",
                )
            )

            ready = self._json_stdout(self._run("status", "--workspace", str(workspace)))
            self.assertEqual(ready["stage"], "ready_to_query")
            self.assertEqual(ready["next"], "query")
            first = self._json_stdout(
                self._run("query", "--workspace", str(workspace), "--query", "摄影")
            )
            awaiting = self._json_stdout(self._run("status", "--workspace", str(workspace)))
            self.assertEqual(awaiting["stage"], "awaiting_result")
            self.assertEqual(awaiting["next"], "record-result")
            self.assertEqual(awaiting["pending_receipts"], [first["receipt"]])

            recorded = self._json_stdout(
                self._run(
                    "record-result", "--workspace", str(workspace), "--receipt", first["receipt"],
                    "--human-usefulness", "useful",
                )
            )
            self.assertEqual(recorded["human_usefulness"], "useful")
            ready_again = self._json_stdout(self._run("next", "--workspace", str(workspace)))
            self.assertEqual(ready_again["stage"], "ready_to_query")
            self.assertEqual(ready_again["next"], "query")

    def test_status_scans_all_pending_receipts_and_accepts_not_useful(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace = root / "workspace"
            source = root / "source.md"
            source.write_text("可复用知识\n", encoding="utf-8")
            self._json_stdout(self._run("init", "--workspace", str(workspace)))
            self._json_stdout(self._run("ingest", "--workspace", str(workspace), "--source", str(source)))
            manifest = json.loads((workspace / "manifest.json").read_text(encoding="utf-8"))
            self._json_stdout(
                self._run(
                    "review", "--workspace", str(workspace),
                    "--candidate", manifest["entries"][0]["candidate_path"], "--decision", "approve",
                )
            )
            first = self._json_stdout(self._run("query", "--workspace", str(workspace), "--query", "知识"))
            second = self._json_stdout(self._run("query", "--workspace", str(workspace), "--query", "知识"))
            awaiting = self._json_stdout(self._run("status", "--workspace", str(workspace)))
            self.assertEqual(awaiting["stage"], "awaiting_result")
            self.assertEqual(set(awaiting["pending_receipts"]), {first["receipt"], second["receipt"]})
            self.assertEqual(awaiting["counts"]["pending_receipts"], 2)

            self._json_stdout(
                self._run(
                    "record-result", "--workspace", str(workspace), "--receipt", second["receipt"],
                    "--human-usefulness", "useful",
                )
            )
            one_pending = self._json_stdout(self._run("status", "--workspace", str(workspace)))
            self.assertEqual(one_pending["stage"], "awaiting_result")
            self.assertEqual(one_pending["pending_receipts"], [first["receipt"]])

            self._json_stdout(
                self._run(
                    "record-result", "--workspace", str(workspace), "--receipt", first["receipt"],
                    "--human-usefulness", "not_useful",
                )
            )
            ready = self._json_stdout(self._run("status", "--workspace", str(workspace)))
            self.assertEqual(ready["stage"], "ready_to_query")
            self.assertEqual(ready["next"], "query")

    def test_status_fails_closed_on_bad_manifest_or_receipt_without_writing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace = root / "workspace"
            workspace.mkdir()
            manifest_path = workspace / "manifest.json"
            manifest_path.write_text("{broken\n", encoding="utf-8")
            before = {path: path.read_bytes() for path in workspace.rglob("*") if path.is_file()}
            bad_manifest = self._run("status", "--workspace", str(workspace))
            self.assertEqual(bad_manifest.returncode, 2)
            self.assertIn("manifest", bad_manifest.stderr)
            self.assertEqual(
                {path: path.read_bytes() for path in workspace.rglob("*") if path.is_file()},
                before,
            )

            valid_workspace = root / "valid-workspace"
            self._json_stdout(self._run("init", "--workspace", str(valid_workspace)))
            bad_receipt = valid_workspace / "receipts" / "query-bad.json"
            bad_receipt.write_text("{}\n", encoding="utf-8")
            valid_before = {path: path.read_bytes() for path in valid_workspace.rglob("*") if path.is_file()}
            rejected = self._run("next", "--workspace", str(valid_workspace))
            self.assertEqual(rejected.returncode, 2)
            self.assertIn("有效的 query receipt", rejected.stderr)
            self.assertEqual(
                {path: path.read_bytes() for path in valid_workspace.rglob("*") if path.is_file()},
                valid_before,
            )

    def test_status_fails_closed_on_structurally_invalid_manifest_and_events(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace = root / "workspace"
            self._json_stdout(self._run("init", "--workspace", str(workspace)))
            manifest_path = workspace / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["entries"] = [1]
            manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")
            rejected_manifest = self._run("status", "--workspace", str(workspace))
            self.assertEqual(rejected_manifest.returncode, 2)
            self.assertIn("entries", rejected_manifest.stderr)

            manifest["entries"] = []
            manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")
            bad_receipt = workspace / "receipts" / "query-events.json"
            bad_receipt.write_text(
                json.dumps(
                    {
                        "query_receipt_version": 1,
                        "query": "结构损坏",
                        "application": {},
                        "application_events": [1],
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            rejected_receipt = self._run("next", "--workspace", str(workspace))
            self.assertEqual(rejected_receipt.returncode, 2)
            self.assertIn("application_events", rejected_receipt.stderr)

    def test_status_accepts_legacy_v1_receipt_with_top_level_usefulness(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace = root / "workspace"
            source = root / "source.md"
            source.write_text("旧版回执兼容知识\n", encoding="utf-8")
            self._json_stdout(self._run("init", "--workspace", str(workspace)))
            self._json_stdout(self._run("ingest", "--workspace", str(workspace), "--source", str(source)))
            manifest = json.loads((workspace / "manifest.json").read_text(encoding="utf-8"))
            self._json_stdout(
                self._run(
                    "review", "--workspace", str(workspace),
                    "--candidate", manifest["entries"][0]["candidate_path"], "--decision", "approve",
                )
            )
            legacy = workspace / "receipts" / "query-legacy.json"
            legacy.write_text(
                json.dumps(
                    {
                        "query_receipt_version": 1,
                        "query": "旧版回执兼容知识",
                        "application": {"project": "legacy", "result_observed": "yes", "decision_changed": "no"},
                        "human_usefulness": "useful",
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            observed = self._json_stdout(self._run("status", "--workspace", str(workspace)))
            self.assertEqual(observed["stage"], "ready_to_query")
            self.assertEqual(observed["next"], "query")
            self.assertEqual(observed["pending_receipts"], [])

    def test_reingest_same_physical_source_with_new_label_updates_in_place(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace = root / "workspace"
            source = root / "source"
            source.mkdir()
            (source / "same.md").write_text("同一物理来源\n", encoding="utf-8")
            self._json_stdout(self._run("init", "--workspace", str(workspace)))
            self._json_stdout(
                self._run("ingest", "--workspace", str(workspace), "--source", str(source), "--label", "first")
            )
            self._json_stdout(
                self._run("ingest", "--workspace", str(workspace), "--source", str(source), "--label", "second")
            )
            manifest = json.loads((workspace / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(len(manifest["entries"]), 1)
            self.assertEqual(manifest["entries"][0]["label"], "second")
            observed = self._json_stdout(self._run("status", "--workspace", str(workspace)))
            self.assertEqual(observed["duplicates"], [])


if __name__ == "__main__":
    unittest.main()
