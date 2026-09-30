#!/usr/bin/env python3
"""Run a small, local-first knowledge-base loop without third-party packages.

The loop is deliberately explicit:

    ingest -> review -> query -> record-result

It only reads files below a user-selected file or directory, keeps immutable
raw snapshots in a private workspace, and never writes an Obsidian canonical
note. The host can promote an approved asset through its own checkpoint later.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import secrets
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = 1
MAX_FILE_BYTES = 20 * 1024 * 1024
TEXT_SUFFIXES = {
    ".c", ".cc", ".cpp", ".csv", ".go", ".h", ".html", ".htm", ".java",
    ".js", ".json", ".md", ".markdown", ".org", ".py", ".rst", ".rs",
    ".sh", ".sql", ".toml", ".ts", ".tsv", ".txt", ".xml", ".yaml", ".yml",
}
DEFAULT_EXCLUDES = {".git", ".venv", "node_modules", "__pycache__", ".cache"}
TOKEN_PATTERN = re.compile(r"[\u4e00-\u9fff]+|[A-Za-z0-9_]+")


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest_text(text: str) -> str:
    return digest_bytes(text.encode("utf-8"))


def atomic_write(path: Path, data: bytes, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def atomic_json(path: Path, value: Any) -> None:
    atomic_write(path, (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def ensure_private_dir(path: Path) -> None:
    if path.is_symlink():
        raise ValueError(f"拒绝使用符号链接目录：{path}")
    if path.exists() and not path.is_dir():
        raise ValueError(f"输出目录不是目录：{path}")
    path.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise ValueError(f"拒绝使用符号链接目录：{path}")
    try:
        os.chmod(path, 0o700)
    except OSError:
        pass


def workspace_dirs(workspace: Path) -> dict[str, Path]:
    return {
        "root": workspace,
        "raw": workspace / "raw",
        "candidates": workspace / "candidates",
        "knowledge": workspace / "knowledge",
        "receipts": workspace / "receipts",
        "manifest": workspace / "manifest.json",
    }


def load_manifest(workspace: Path) -> dict[str, Any]:
    paths = workspace_dirs(workspace)
    ensure_private_dir(workspace)
    for key in ("raw", "candidates", "knowledge", "receipts"):
        ensure_private_dir(paths[key])
    if paths["manifest"].is_symlink():
        raise ValueError("拒绝读取符号链接 manifest")
    if not paths["manifest"].exists():
        data = {
            "manifest_version": SCHEMA_VERSION,
            "created_at": utc_now(),
            "updated_at": None,
            "entries": [],
            "history": [],
        }
        atomic_json(paths["manifest"], data)
        return data
    if not paths["manifest"].is_file():
        raise ValueError("workspace manifest 不是普通文件")
    data = json.loads(paths["manifest"].read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("manifest_version") != SCHEMA_VERSION:
        raise ValueError("不支持的 workspace manifest")
    if not isinstance(data.get("entries"), list) or not isinstance(data.get("history"), list):
        raise ValueError("workspace manifest 缺少 entries/history")
    return data


def safe_name(value: str, fallback: str) -> str:
    value = Path(value).name.replace("\x00", "").strip()
    value = re.sub(r"[^\w.\-\u4e00-\u9fff]+", "-", value, flags=re.UNICODE).strip(".-")
    return (value or fallback)[:160]


def lexical_path(value: str | Path) -> Path:
    """Return an absolute path without resolving symlinks."""
    expanded = Path(value).expanduser()
    if not expanded.is_absolute():
        expanded = Path.cwd() / expanded
    return Path(os.path.abspath(os.fspath(expanded)))


def resolve_source(value: str | Path) -> Path:
    """Resolve an explicitly selected source after rejecting a symlink source."""
    lexical = lexical_path(value)
    # macOS commonly exposes /tmp and /var as system symlinks. Reject the
    # explicitly selected source itself, then resolve its normal parent path.
    if lexical.is_symlink():
        raise ValueError(f"拒绝读取符号链接 source：{lexical}")
    try:
        source = lexical.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ValueError(f"source 不存在：{lexical}") from exc
    if not source.is_file() and not source.is_dir():
        raise ValueError(f"source 不是文件或目录：{lexical}")
    return source


def source_files(source: Path, excludes: set[str]) -> Iterable[tuple[Path, Path, Path]]:
    """Yield (file, relative path, root) for a selected file or directory."""
    if source.is_symlink():
        raise ValueError("拒绝读取符号链接 source")
    if source.is_file():
        relative = Path(source.name)
        yield source, relative, source.parent
        return
    if not source.is_dir():
        raise ValueError(f"source 不是文件或目录：{source}")
    root = source.resolve()
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in excludes for part in relative.parts):
            continue
        yield path, relative, root


def read_text_file(path: Path) -> tuple[bytes, str]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"source 不是普通文件：{path}")
    size = path.stat().st_size
    if size > MAX_FILE_BYTES:
        raise ValueError(f"文件超过 {MAX_FILE_BYTES} bytes：{path}")
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError(f"只支持 UTF-8 文本：{path}") from exc
    return raw, text


def quote(value: Any) -> str:
    return json.dumps(str(value), ensure_ascii=False)


def fenced(text: str) -> str:
    fence = "````"
    while fence in text:
        fence += "`"
    return f"{fence}text\n{text.rstrip()}\n{fence}"


def candidate_markdown(entry: dict[str, Any], text: str) -> str:
    return "\n".join(
        [
            "---",
            f"title: {quote(entry['title'])}",
            "type: knowledge_candidate",
            "knowledge_type: candidate",
            "source_refs:",
            f"  - {quote(entry['source_id'])}",
            f"source_revision: {quote(entry['revision_id'])}",
            f"source_hash: {quote(entry['source_hash'])}",
            f"raw_path: {quote(entry['raw_path'])}",
            'provenance: "local_import"',
            'source_content_trust: "untrusted_data"',
            'review_status: "unreviewed"',
            'evidence_status: "verified_source_unreviewed"',
            "---",
            "",
            f"# {entry['title']}",
            "",
            "## Source Snapshot",
            "",
            f"- source: `{entry['source_id']}`",
            f"- revision: `{entry['revision_id']}`",
            f"- captured_at: `{entry['captured_at']}`",
            f"- content_sha256: `{entry['source_hash']}`",
            "",
            "## Extracted Content",
            "",
            fenced(text),
            "",
            "## Review Gate",
            "",
            "当前候选未审核。使用 `review --decision approve` 或 `reject`，再进入查询层。",
            "",
        ]
    )


def knowledge_markdown(entry: dict[str, Any], text: str, summary: str | None) -> str:
    reviewed_at = entry["reviewed_at"]
    summary_text = summary.strip() if summary and summary.strip() else "已人工确认来源摘录；未添加超出原文的推断。"
    return "\n".join(
        [
            "---",
            f"title: {quote(entry['title'])}",
            "type: knowledge_asset",
            "knowledge_type: concept",
            "source_refs:",
            f"  - {quote(entry['source_id'])}",
            f"source_revision: {quote(entry['revision_id'])}",
            f"source_hash: {quote(entry['source_hash'])}",
            'provenance: "extracted_and_reviewed"',
            'review_status: "approved"',
            'evidence_status: "verified"',
            f"reviewed_at: {quote(reviewed_at)}",
            "contradictions: []",
            f"raw_path: {quote(entry['raw_path'])}",
            "---",
            "",
            f"# {entry['title']}",
            "",
            "## Reviewed Summary",
            "",
            summary_text,
            "",
            "## Source Evidence",
            "",
            f"- source_ref: `{entry['source_id']}`",
            f"- source_revision: `{entry['revision_id']}`",
            f"- content_sha256: `{entry['source_hash']}`",
            "",
            fenced(text),
            "",
            "## Application Receipt",
            "",
            "查询和应用结果通过 workspace/receipts/ 单独记录；本文件不代表已产生用户结果。",
            "",
        ]
    )


def choose_entry(manifest: dict[str, Any], selector: str) -> dict[str, Any]:
    entries = manifest["entries"]
    for entry in entries:
        if selector in {entry.get("source_id"), entry.get("candidate_path"), entry.get("knowledge_path")}:
            return entry
        if Path(str(entry.get("candidate_path", ""))).name == Path(selector).name:
            return entry
    raise ValueError(f"找不到候选或来源：{selector}")


def save_manifest(workspace: Path, manifest: dict[str, Any]) -> None:
    manifest["updated_at"] = utc_now()
    atomic_json(workspace_dirs(workspace)["manifest"], manifest)


def init_workspace(args: argparse.Namespace) -> dict[str, Any]:
    workspace = Path(args.workspace).expanduser().resolve()
    manifest = load_manifest(workspace)
    return {"workspace": str(workspace), "manifest": str(workspace / "manifest.json"), "entries": len(manifest["entries"])}


def ingest(args: argparse.Namespace) -> dict[str, Any]:
    workspace = Path(args.workspace).expanduser().resolve()
    manifest = load_manifest(workspace)
    paths = workspace_dirs(workspace)
    source = resolve_source(args.source)
    label = safe_name(args.label or source.name, "local-source")
    current_by_id = {entry["source_id"]: entry for entry in manifest["entries"]}
    counts = {"new": 0, "modified": 0, "unchanged": 0, "skipped": 0}
    errors: list[dict[str, str]] = []

    for path, relative, root in source_files(source, DEFAULT_EXCLUDES | set(args.exclude)):
        if path.suffix.lower() not in TEXT_SUFFIXES:
            counts["skipped"] += 1
            continue
        source_id = f"local:{label}:{relative.as_posix()}"
        try:
            raw, text = read_text_file(path)
        except ValueError as exc:
            counts["skipped"] += 1
            errors.append({"path": str(path), "error": str(exc)})
            continue
        source_hash = digest_bytes(raw)
        previous = current_by_id.get(source_id)
        if previous and previous.get("source_hash") == source_hash:
            counts["unchanged"] += 1
            continue
        if previous:
            counts["modified"] += 1
            old = dict(previous)
            # A changed source starts a new review cycle. The prior immutable
            # asset remains in history for audit but is intentionally not part
            # of current retrieval until the new revision is approved.
            old["record_status"] = "superseded"
            old["superseded_at"] = utc_now()
            manifest["history"].append(old)
        else:
            counts["new"] += 1

        prefix = hashlib.sha256(source_id.encode("utf-8")).hexdigest()[:10]
        raw_name = f"{prefix}-{source_hash[:16]}-{safe_name(path.name, 'source')}{path.suffix.lower()}"
        raw_path = paths["raw"] / raw_name
        if raw_path.exists():
            existing_hash = digest_bytes(raw_path.read_bytes())
            if existing_hash != source_hash:
                raise ValueError(f"raw snapshot collision：{raw_path}")
        else:
            atomic_write(raw_path, raw)
        relative_candidate = Path("candidates") / f"{prefix}-{source_hash[:16]}.md"
        candidate_path = workspace / relative_candidate
        entry = {
            "source_id": source_id,
            "revision_id": f"{source_id}@{source_hash[:16]}",
            "label": label,
            "relative_path": relative.as_posix(),
            "locator": str(path),
            "title": path.stem or path.name,
            "source_hash": source_hash,
            "size_bytes": len(raw),
            "captured_at": utc_now(),
            "raw_path": str(raw_path.relative_to(workspace)),
            "candidate_path": str(relative_candidate),
            "knowledge_path": None,
            "review_status": "unreviewed",
            "record_status": "active",
            "evidence_status": "verified_source_unreviewed",
            "reviewed_at": None,
            "parser": {"name": "utf-8-fixture", "version": "1"},
        }
        if candidate_path.exists():
            existing_candidate = candidate_path.read_text(encoding="utf-8")
            if digest_text(existing_candidate) != digest_text(candidate_markdown(entry, text)):
                raise ValueError(f"拒绝覆盖已有候选：{candidate_path}")
        else:
            atomic_write(candidate_path, candidate_markdown(entry, text).encode("utf-8"))
        manifest["entries"] = [item for item in manifest["entries"] if item["source_id"] != source_id]
        manifest["entries"].append(entry)
        current_by_id[source_id] = entry

    save_manifest(workspace, manifest)
    return {
        "workspace": str(workspace),
        "source": str(source),
        "counts": counts,
        "entries": len(manifest["entries"]),
        "errors": errors,
        "next": "review",
    }


def review(args: argparse.Namespace) -> dict[str, Any]:
    workspace = Path(args.workspace).expanduser().resolve()
    manifest = load_manifest(workspace)
    entry = choose_entry(manifest, args.candidate)
    decision = args.decision
    if decision not in {"approve", "reject", "contradictory"}:
        raise ValueError("decision 必须是 approve/reject/contradictory")
    if entry.get("review_status") in {"approved", "rejected", "contradictory"}:
        raise ValueError(f"候选已经完成审核：{entry['review_status']}")
    candidate_path = workspace / entry["candidate_path"]
    if candidate_path.is_symlink() or not candidate_path.is_file():
        raise ValueError(f"候选文件不存在：{candidate_path}")
    raw_path = workspace / entry["raw_path"]
    _, text = read_text_file(raw_path)
    now = utc_now()
    entry["review_status"] = {"approve": "approved", "reject": "rejected", "contradictory": "contradictory"}[decision]
    entry["evidence_status"] = {"approve": "verified", "reject": "rejected", "contradictory": "contradictory"}[decision]
    entry["reviewed_at"] = now
    entry["review_note"] = args.note or ""
    if decision == "approve":
        prefix = hashlib.sha256(entry["source_id"].encode("utf-8")).hexdigest()[:10]
        knowledge_rel = Path("knowledge") / f"{prefix}-{entry['source_hash'][:16]}.md"
        knowledge_path = workspace / knowledge_rel
        if knowledge_path.exists():
            raise ValueError(f"拒绝覆盖已有知识资产：{knowledge_path}")
        atomic_write(knowledge_path, knowledge_markdown(entry, text, args.summary).encode("utf-8"))
        entry["knowledge_path"] = str(knowledge_rel)
    else:
        entry["knowledge_path"] = None
    save_manifest(workspace, manifest)
    return {
        "workspace": str(workspace),
        "source_id": entry["source_id"],
        "decision": decision,
        "review_status": entry["review_status"],
        "candidate": entry["candidate_path"],
        "knowledge": entry["knowledge_path"],
        "next": "query" if decision == "approve" else "ingest_or_review",
    }


def query_tokens(value: str) -> list[str]:
    tokens: list[str] = []
    for token in TOKEN_PATTERN.findall(value.casefold()):
        if not token.strip():
            continue
        if all("\u4e00" <= char <= "\u9fff" for char in token):
            tokens.append(token)
            if len(token) >= 2:
                tokens.extend(token[index : index + 2] for index in range(len(token) - 1))
        else:
            tokens.append(token)
    return list(dict.fromkeys(tokens))


def query(args: argparse.Namespace) -> dict[str, Any]:
    workspace = Path(args.workspace).expanduser().resolve()
    manifest = load_manifest(workspace)
    tokens = query_tokens(args.query)
    if not tokens:
        raise ValueError("query 不能为空")
    results: list[dict[str, Any]] = []
    for entry in manifest["entries"]:
        if entry.get("review_status") != "approved" or not entry.get("knowledge_path"):
            continue
        path = workspace / entry["knowledge_path"]
        if path.is_symlink() or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        haystack = text.casefold()
        matched = [token for token in tokens if token in haystack]
        if not matched:
            continue
        score = sum(haystack.count(token) for token in matched)
        first_match_line = 1
        for line_number, line in enumerate(text.splitlines(), start=1):
            if any(token in line.casefold() for token in matched):
                first_match_line = line_number
                break
        results.append(
            {
                "score": score,
                "title": entry["title"],
                "knowledge_path": entry["knowledge_path"],
                "source_refs": [entry["source_id"]],
                "source_revision": entry["revision_id"],
                "source_hash": entry["source_hash"],
                "matched_tokens": sorted(set(matched)),
                "line": first_match_line,
                "citation": f"{entry['knowledge_path']}:{first_match_line}#source:{entry['source_id']}",
            }
        )
    results.sort(key=lambda item: (-item["score"], item["knowledge_path"]))
    results = results[: max(1, args.limit)]
    receipt_id = hashlib.sha256(
        f"{args.query}|{utc_now()}|{secrets.token_hex(8)}".encode("utf-8")
    ).hexdigest()[:16]
    receipt_rel = Path("receipts") / f"query-{receipt_id}.json"
    receipt = {
        "query_receipt_version": 1,
        "query": args.query,
        "scope": args.scope or "approved knowledge assets",
        "retrieval": {"modes": ["keyword"], "context_budget": args.context_budget},
        "sources_selected": [item["knowledge_path"] for item in results],
        "citations": [item["citation"] for item in results],
        "missing_evidence": [] if results else ["没有命中已审核知识资产"],
        "contradictions": [
            entry["source_id"] for entry in manifest["entries"] if entry.get("review_status") == "contradictory"
        ],
        "freshness_checked": False,
        "human_usefulness": "unknown",
        "application": {
            "project": None,
            "result_observed": "unknown",
            "decision_changed": "unknown",
        },
        "results": results,
        "created_at": utc_now(),
    }
    atomic_json(workspace / receipt_rel, receipt)
    receipt_md = workspace / receipt_rel.with_suffix(".md")
    citation_lines = [f"- `{citation}`" for citation in receipt["citations"]] or ["- 无"]
    missing_lines = [f"- {item}" for item in receipt["missing_evidence"]] or ["- 无"]
    markdown = "\n".join(
        [
            "---",
            "type: query_receipt",
            "query_receipt_version: 1",
            f"query: {quote(args.query)}",
            f"scope: {quote(receipt['scope'])}",
            "retrieval_modes:",
            "  - keyword",
            f"json_receipt: {quote(str(receipt_rel))}",
            "---",
            "",
            "# Query Receipt",
            "",
            "## Citations",
            "",
            *citation_lines,
            "",
            "## Missing Evidence",
            "",
            *missing_lines,
            "",
            "## Outcome",
            "",
            "- Human usefulness: `unknown`",
            "- Application result: `unknown`",
            "",
        ]
    )
    atomic_write(receipt_md, markdown.encode("utf-8"))
    return {"workspace": str(workspace), "query": args.query, "results": results, "receipt": str(receipt_rel), "next": "record-result"}


def record_result(args: argparse.Namespace) -> dict[str, Any]:
    workspace = Path(args.workspace).expanduser().resolve()
    load_manifest(workspace)
    receipt_input = Path(args.receipt).expanduser()
    if not receipt_input.is_absolute():
        receipt_input = workspace / receipt_input
    if receipt_input.is_symlink():
        raise ValueError(f"receipt 不存在或是符号链接：{receipt_input}")
    receipt_path = receipt_input.resolve(strict=False)
    receipts_dir = workspace / "receipts"
    if receipt_path.parent != receipts_dir or receipt_path.suffix != ".json":
        raise ValueError("receipt 必须是 workspace/receipts 下的 JSON")
    if not receipt_path.is_file() or receipt_path.is_symlink():
        raise ValueError(f"receipt 不存在或是符号链接：{receipt_path}")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if (
        not isinstance(receipt, dict)
        or receipt.get("query_receipt_version") != 1
        or "query" not in receipt
        or not isinstance(receipt.get("application"), dict)
    ):
        raise ValueError("receipt 不是有效的 query receipt")
    receipt["application"] = {
        "project": args.project or None,
        "result_observed": args.result_observed,
        "decision_changed": args.decision_changed,
        "result": args.result or "",
    }
    receipt["human_usefulness"] = args.human_usefulness
    receipt["updated_at"] = utc_now()
    atomic_json(receipt_path, receipt)
    markdown_path = receipt_path.with_suffix(".md")
    if markdown_path.is_symlink():
        raise ValueError(f"receipt Markdown 是符号链接：{markdown_path}")
    if markdown_path.is_file():
        markdown = markdown_path.read_text(encoding="utf-8")
        application_block = "\n".join(
            [
                "",
                "## Application",
                "",
                f"- Project: `{args.project or 'unknown'}`",
                f"- Result observed: `{args.result_observed}`",
                f"- Decision changed: `{args.decision_changed}`",
                f"- Human usefulness: `{args.human_usefulness}`",
                f"- Result: {args.result or 'unknown'}",
                "",
            ]
        )
        if "\n## Application\n" in markdown:
            markdown = markdown.split("\n## Application\n", 1)[0].rstrip() + application_block
        else:
            markdown = markdown.rstrip() + application_block
        atomic_write(markdown_path, markdown.encode("utf-8"))
    return {"receipt": str(receipt_path.relative_to(workspace)), "application": receipt["application"], "human_usefulness": receipt["human_usefulness"]}


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description=__doc__)
    sub = command.add_subparsers(dest="command", required=True)

    init_parser = sub.add_parser("init", help="create a private workspace")
    init_parser.add_argument("--workspace", required=True)
    init_parser.set_defaults(handler=init_workspace)

    ingest_parser = sub.add_parser("ingest", help="ingest one explicit file or directory")
    ingest_parser.add_argument("--workspace", required=True)
    ingest_parser.add_argument("--source", required=True)
    ingest_parser.add_argument("--label")
    ingest_parser.add_argument("--exclude", action="append", default=[])
    ingest_parser.set_defaults(handler=ingest)

    review_parser = sub.add_parser("review", help="approve, reject, or mark a candidate contradictory")
    review_parser.add_argument("--workspace", required=True)
    review_parser.add_argument("--candidate", required=True, help="candidate path or source_id")
    review_parser.add_argument("--decision", required=True, choices=("approve", "reject", "contradictory"))
    review_parser.add_argument("--summary")
    review_parser.add_argument("--note")
    review_parser.set_defaults(handler=review)

    query_parser = sub.add_parser("query", help="keyword query approved knowledge and write a receipt")
    query_parser.add_argument("--workspace", required=True)
    query_parser.add_argument("--query", required=True)
    query_parser.add_argument("--scope")
    query_parser.add_argument("--limit", type=int, default=5)
    query_parser.add_argument("--context-budget", type=int, default=4000)
    query_parser.set_defaults(handler=query)

    result_parser = sub.add_parser("record-result", help="attach an observed application result to a receipt")
    result_parser.add_argument("--workspace", required=True)
    result_parser.add_argument("--receipt", required=True)
    result_parser.add_argument("--project")
    result_parser.add_argument("--result")
    result_parser.add_argument("--result-observed", choices=("yes", "no", "unknown"), default="unknown")
    result_parser.add_argument("--decision-changed", choices=("yes", "no", "unknown"), default="unknown")
    result_parser.add_argument("--human-usefulness", choices=("useful", "not_useful", "unknown"), default="unknown")
    result_parser.set_defaults(handler=record_result)
    return command


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        result = args.handler(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({"ok": True, **result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
