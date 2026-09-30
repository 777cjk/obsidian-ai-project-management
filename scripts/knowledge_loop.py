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
DEFAULT_EXCLUDES = {
    ".git", ".venv", "node_modules", "__pycache__", ".cache",
    ".obsidian", ".trash", ".vscode",
}
TOKEN_PATTERN = re.compile(r"[\u4e00-\u9fff]+|[A-Za-z0-9_]+")
APPLICATION_HISTORY_MARKER = "<!-- obsidian-ai-project-management:application-history -->"


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
    if not all(isinstance(entry, dict) for entry in data["entries"]):
        raise ValueError("workspace manifest entries 必须是对象列表")
    if not all(isinstance(event, dict) for event in data["history"]):
        raise ValueError("workspace manifest history 必须是对象列表")
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


def resolve_workspace(value: str | Path) -> Path:
    lexical = lexical_path(value)
    if lexical.is_symlink():
        raise ValueError(f"拒绝使用符号链接 workspace：{lexical}")
    return lexical.resolve(strict=False)


def source_root_id(root: Path) -> str:
    normalized = os.path.normcase(os.fspath(root.resolve(strict=False)))
    return digest_text(normalized)[:20]


def source_identity(label: str, root_id: str, relative: str) -> str:
    """Return the stable physical identity; label is presentation metadata."""
    del label
    return f"local:{root_id}:{relative}"


def physical_identity(root_id: str | None, relative: str | None) -> str | None:
    if not root_id or not relative:
        return None
    return f"local:{root_id}:{relative}"


def entry_identity(entry: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
    """Read stable identity fields, deriving a root id for pre-hardening manifests."""
    label = entry.get("label")
    relative = entry.get("relative_path")
    root_id = entry.get("source_root_id")
    if not root_id and entry.get("locator") and relative:
        locator = lexical_path(str(entry["locator"]))
        root = locator
        for _ in Path(str(relative)).parts:
            root = root.parent
        root_id = source_root_id(root)
    identity = entry.get("source_identity")
    if not identity and label and root_id and relative:
        identity = source_identity(str(label), str(root_id), str(relative))
    return (str(identity) if identity else None, str(root_id) if root_id else None, str(label) if label else None)


def entry_physical_identity(entry: dict[str, Any]) -> str | None:
    identity, root_id, _ = entry_identity(entry)
    relative = entry.get("relative_path")
    return physical_identity(root_id, str(relative) if relative else None) or identity


def reject_source_workspace_overlap(source: Path, workspace: Path) -> None:
    source_path = source.resolve(strict=True)
    workspace_path = workspace.resolve(strict=False)
    if source_path == workspace_path or source_path in workspace_path.parents or workspace_path in source_path.parents:
        raise ValueError(f"source 与 workspace 重叠，拒绝导入：source={source_path} workspace={workspace_path}")


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
    workspace = resolve_workspace(args.workspace)
    manifest = load_manifest(workspace)
    return {"workspace": str(workspace), "manifest": str(workspace / "manifest.json"), "entries": len(manifest["entries"])}


def read_manifest_readonly(workspace: Path) -> dict[str, Any] | None:
    """Read a workspace manifest without creating or changing any path."""
    if workspace.exists() and not workspace.is_dir():
        raise ValueError(f"workspace 不是目录：{workspace}")
    manifest_path = workspace / "manifest.json"
    if manifest_path.is_symlink():
        raise ValueError("拒绝读取符号链接 manifest")
    if not manifest_path.exists():
        return None
    if not manifest_path.is_file():
        raise ValueError("workspace manifest 不是普通文件")
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"workspace manifest JSON 无效：{manifest_path}") from exc
    if not isinstance(data, dict) or data.get("manifest_version") != SCHEMA_VERSION:
        raise ValueError("不支持的 workspace manifest")
    if not isinstance(data.get("entries"), list) or not isinstance(data.get("history"), list):
        raise ValueError("workspace manifest 缺少 entries/history")
    if not all(isinstance(entry, dict) for entry in data["entries"]):
        raise ValueError("workspace manifest entries 必须是对象列表")
    if not all(isinstance(event, dict) for event in data["history"]):
        raise ValueError("workspace manifest history 必须是对象列表")
    return data


def read_query_receipts_readonly(workspace: Path) -> list[tuple[Path, dict[str, Any]]]:
    """Read every query receipt without creating or mutating receipt storage."""
    receipts_dir = workspace / "receipts"
    if not receipts_dir.exists():
        return []
    if receipts_dir.is_symlink() or not receipts_dir.is_dir():
        raise ValueError("workspace receipts 不是普通目录")
    receipts: list[tuple[Path, dict[str, Any]]] = []
    for receipt_path in sorted(receipts_dir.iterdir(), key=lambda item: item.name):
        if not receipt_path.name.startswith("query-") or receipt_path.suffix != ".json":
            continue
        if receipt_path.is_symlink() or not receipt_path.is_file():
            raise ValueError(f"query receipt 不是普通文件：{receipt_path}")
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"query receipt JSON 无效：{receipt_path}") from exc
        if (
            not isinstance(receipt, dict)
            or receipt.get("query_receipt_version") != 1
            or not isinstance(receipt.get("query"), str)
            or not isinstance(receipt.get("application"), dict)
        ):
            raise ValueError(f"query receipt 不是有效的 query receipt：{receipt_path}")
        events = receipt.get("application_events")
        if events is not None and (
            not isinstance(events, list)
            or not all(isinstance(event, dict) for event in events)
        ):
            raise ValueError(f"query receipt application_events 无效：{receipt_path}")
        receipts.append((receipt_path, receipt))
    receipts.sort(
        key=lambda item: (
            str(item[1].get("created_at") or ""),
            item[0].stat().st_mtime_ns,
            item[0].name,
        )
    )
    return receipts


def receipt_usefulness(receipt: dict[str, Any]) -> str | None:
    """Return the latest explicit usefulness, or None while it is pending."""
    events = receipt.get("application_events")
    if events is None or events == []:
        # Receipts written before application_events was introduced only have
        # the top-level field. Preserve that compatibility while treating an
        # unknown value as pending.
        usefulness = receipt.get("human_usefulness")
        if usefulness in {"useful", "not_useful"}:
            return str(usefulness)
        return None
    if not isinstance(events, list):
        return "unknown"
    latest_event = events[-1]
    if not isinstance(latest_event, dict):
        return "unknown"
    event_usefulness = latest_event.get("human_usefulness")
    if event_usefulness in {"useful", "not_useful"}:
        return str(event_usefulness)
    return "unknown"


def source_duplicate_groups(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Expose duplicate active source locations, including label-only drift."""
    groups: dict[str, list[dict[str, Any]]] = {}
    for entry in entries:
        root_id = entry.get("source_root_id")
        relative = entry.get("relative_path")
        identity = entry.get("source_identity") or entry.get("source_id")
        if root_id and relative:
            key = f"{root_id}:{relative}"
        elif identity:
            key = str(identity)
        else:
            continue
        groups.setdefault(key, []).append(entry)
    duplicates: list[dict[str, Any]] = []
    for key, group in sorted(groups.items()):
        if len(group) < 2:
            continue
        duplicates.append(
            {
                "key": key,
                "count": len(group),
                "source_ids": [str(item.get("source_id")) for item in group if item.get("source_id")],
                "labels": [str(item.get("label")) for item in group if item.get("label")],
            }
        )
    return duplicates


def status(args: argparse.Namespace) -> dict[str, Any]:
    """Report the next lifecycle action without touching the workspace."""
    workspace = resolve_workspace(args.workspace)
    manifest = read_manifest_readonly(workspace)
    if manifest is None:
        return {
            "workspace": str(workspace),
            "initialized": False,
            "stage": "uninitialized",
            "next": "init",
            "next_action": "init",
            "reason": "workspace/manifest.json 不存在",
            "counts": {
                "entries": 0,
                "active_entries": 0,
                "active_unreviewed": 0,
                "active_approved": 0,
                "query_receipts": 0,
                "pending_receipts": 0,
            },
            "active_unreviewed": [],
            "active_approved": [],
            "pending_receipts": [],
            "duplicates": [],
        }

    entries = manifest["entries"]
    active_entries = [
        entry for entry in entries
        if isinstance(entry, dict) and entry.get("record_status", "active") == "active"
    ]
    active_unreviewed = [
        entry for entry in active_entries if entry.get("review_status") == "unreviewed"
    ]
    active_approved = [
        entry for entry in active_entries
        if entry.get("review_status") == "approved" and entry.get("knowledge_path")
    ]
    receipts = read_query_receipts_readonly(workspace)
    pending_receipts = [
        receipt_path.relative_to(workspace).as_posix()
        for receipt_path, receipt in receipts
        if receipt_usefulness(receipt) not in {"useful", "not_useful"}
    ]
    duplicates = source_duplicate_groups(active_entries)
    summary = {
        "workspace": str(workspace),
        "initialized": True,
        "counts": {
            "entries": len(entries),
            "active_entries": len(active_entries),
            "active_unreviewed": len(active_unreviewed),
            "active_approved": len(active_approved),
            "query_receipts": len(receipts),
            "pending_receipts": len(pending_receipts),
        },
        "active_unreviewed": [entry.get("candidate_path") for entry in active_unreviewed],
        "active_approved": [entry.get("knowledge_path") for entry in active_approved],
        "pending_receipts": pending_receipts,
        "latest_query": (
            receipts[-1][0].relative_to(workspace).as_posix() if receipts else None
        ),
        "duplicates": duplicates,
        "warnings": (
            [f"发现 {len(duplicates)} 组重复来源 identity；请先确认来源标签或重新 ingest。"]
            if duplicates else []
        ),
    }
    if active_unreviewed:
        summary.update(
            {
                "stage": "needs_review",
                "next": "review",
                "reason": "存在尚未人工审核的 active candidate",
            }
        )
    elif active_approved and pending_receipts:
        summary.update(
            {
                "stage": "awaiting_result",
                "next": "record-result",
                "reason": "存在未记录 usefulness 的 query receipt",
            }
        )
    elif active_approved:
        summary.update(
            {
                "stage": "ready_to_query",
                "next": "query",
                "reason": "存在已审核知识资产，且没有待闭环 query",
            }
        )
    else:
        summary.update(
            {
                "stage": "needs_ingest",
                "next": "ingest",
                "reason": "没有可查询的 active approved knowledge asset",
            }
        )
    summary["next_action"] = summary["next"]
    return summary


def ingest(args: argparse.Namespace) -> dict[str, Any]:
    workspace = resolve_workspace(args.workspace)
    source = resolve_source(args.source)
    reject_source_workspace_overlap(source, workspace)
    label = safe_name(args.label or source.name, "local-source")
    is_directory_source = source.is_dir()
    root = source.resolve() if is_directory_source else source.parent.resolve()
    root_id = source_root_id(root)
    manifest = load_manifest(workspace)
    paths = workspace_dirs(workspace)
    current_by_identity: dict[str, dict[str, Any]] = {}
    for entry in manifest["entries"]:
        identity = entry_physical_identity(entry)
        if identity:
            current_by_identity[identity] = entry
    counts = {"new": 0, "modified": 0, "unchanged": 0, "restored": 0, "stale": 0, "skipped": 0}
    errors: list[dict[str, str]] = []
    candidate_paths: set[str] = set()
    seen_identities: set[str] = set()

    for path, relative, file_root in source_files(source, DEFAULT_EXCLUDES | set(args.exclude)):
        current_root_id = source_root_id(file_root)
        relative_text = relative.as_posix()
        identity = source_identity(label, current_root_id, relative_text)
        seen_identities.add(identity)
        if path.suffix.lower() not in TEXT_SUFFIXES:
            counts["skipped"] += 1
            continue
        try:
            raw, text = read_text_file(path)
        except (OSError, ValueError) as exc:
            counts["skipped"] += 1
            errors.append({"path": str(path), "error": str(exc)})
            continue
        source_hash = digest_bytes(raw)
        previous = current_by_identity.get(identity)
        if previous and previous.get("source_hash") == source_hash:
            counts["unchanged"] += 1
            previous["source_identity"] = identity
            previous["source_root_id"] = current_root_id
            previous["label"] = label
            if previous.get("review_status") == "unreviewed":
                candidate_paths.add(previous["candidate_path"])
            continue
        if previous is None:
            restored_index = next(
                (
                    index for index in range(len(manifest["history"]) - 1, -1, -1)
                    if entry_physical_identity(manifest["history"][index]) == identity
                    and manifest["history"][index].get("source_hash") == source_hash
                    and manifest["history"][index].get("record_status") == "stale"
                ),
                None,
            )
            if restored_index is not None:
                restored = dict(manifest["history"].pop(restored_index))
                restored["record_status"] = "active"
                restored["restored_at"] = utc_now()
                restored["locator"] = str(path)
                restored["source_identity"] = identity
                restored["source_root_id"] = current_root_id
                manifest["entries"].append(restored)
                current_by_identity[identity] = restored
                counts["restored"] += 1
                if restored.get("review_status") == "unreviewed":
                    candidate_paths.add(restored["candidate_path"])
                continue
        source_id = previous.get("source_id") if previous else identity
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
            "source_identity": identity,
            "source_root_id": current_root_id,
            "revision_id": f"{identity}@{source_hash[:16]}",
            "label": label,
            "relative_path": relative_text,
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
        candidate_paths.add(str(relative_candidate))
        manifest["entries"] = [item for item in manifest["entries"] if item["source_id"] != source_id]
        manifest["entries"].append(entry)
        current_by_identity[identity] = entry

    if is_directory_source and not errors:
        active_entries: list[dict[str, Any]] = []
        for entry in manifest["entries"]:
            identity, entry_root_id, entry_label = entry_identity(entry)
            if entry_root_id == root_id and entry_label == label and identity not in seen_identities:
                stale = dict(entry)
                stale["record_status"] = "stale"
                stale["deleted_at"] = utc_now()
                manifest["history"].append(stale)
                counts["stale"] += 1
            else:
                active_entries.append(entry)
        manifest["entries"] = active_entries

    save_manifest(workspace, manifest)
    complete = not errors
    if args.strict and not complete:
        raise ValueError(f"ingest 部分失败（--strict）：{len(errors)} 个文件未导入")
    return {
        "workspace": str(workspace),
        "source": str(source),
        "status": "complete" if complete else "partial",
        "complete": complete,
        "counts": counts,
        "entries": len(manifest["entries"]),
        "candidates": sorted(candidate_paths),
        "errors": errors,
        "next": "review",
    }


def review(args: argparse.Namespace) -> dict[str, Any]:
    workspace = resolve_workspace(args.workspace)
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
    workspace = resolve_workspace(args.workspace)
    manifest = load_manifest(workspace)
    tokens = query_tokens(args.query)
    if not tokens:
        raise ValueError("query 不能为空")
    if args.limit < 1:
        raise ValueError("limit 必须至少为 1")
    if args.context_budget < 1:
        raise ValueError("context-budget 必须至少为 1")
    results: list[dict[str, Any]] = []
    scoped_entries = [
        entry for entry in manifest["entries"]
        if not args.scope
        or args.scope in {
            entry.get("label"), entry.get("source_id"), entry.get("source_identity"), entry.get("source_root_id"),
        }
    ]
    for entry in scoped_entries:
        if entry.get("record_status", "active") != "active" or entry.get("review_status") != "approved" or not entry.get("knowledge_path"):
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
        lines = text.splitlines()
        first_match_index = next(
            (index for index, line in enumerate(lines) if any(token in line.casefold() for token in matched)),
            0,
        )
        first_match_line = first_match_index + 1
        snippet_start = max(0, first_match_index - 1)
        snippet_end = min(len(lines), first_match_index + 2)
        snippet_candidate = "\n".join(lines[snippet_start:snippet_end])
        results.append(
            {
                "score": score,
                "title": entry["title"],
                "knowledge_path": entry["knowledge_path"],
                "source_refs": [entry["source_id"]],
                "source_root_id": entry.get("source_root_id"),
                "label": entry.get("label"),
                "source_revision": entry["revision_id"],
                "source_hash": entry["source_hash"],
                "matched_tokens": sorted(set(matched)),
                "line": first_match_line,
                "_snippet_candidate": snippet_candidate,
                "citation": f"{entry['knowledge_path']}:{first_match_line}#source:{entry['source_id']}",
            }
        )
    results.sort(key=lambda item: (-item["score"], item["knowledge_path"]))
    results = results[:args.limit]
    remaining_context = args.context_budget
    for item in results:
        candidate = item.pop("_snippet_candidate")
        if remaining_context > 0:
            item["snippet"] = candidate[:remaining_context]
        else:
            item["snippet"] = ""
        item["snippet_truncated"] = len(candidate) > len(item["snippet"])
        item["context_chars"] = len(item["snippet"])
        remaining_context -= item["context_chars"]
    receipt_id = hashlib.sha256(
        f"{args.query}|{utc_now()}|{secrets.token_hex(8)}".encode("utf-8")
    ).hexdigest()[:16]
    receipt_rel = Path("receipts") / f"query-{receipt_id}.json"
    receipt = {
        "query_receipt_version": 1,
        "query": args.query,
        "scope": args.scope or "approved knowledge assets",
        "scope_match": "exact label, source_id, source_identity, or source_root_id" if args.scope else "all",
        "retrieval": {
            "modes": ["keyword"],
            "context_budget": args.context_budget,
            "context_budget_unit": "unicode characters",
            "context_chars_used": args.context_budget - remaining_context,
        },
        "sources_selected": [item["knowledge_path"] for item in results],
        "citations": [item["citation"] for item in results],
        "missing_evidence": [] if results else ["没有命中已审核知识资产"],
        "contradictions": [
            entry["source_id"] for entry in scoped_entries
            if entry.get("record_status", "active") == "active" and entry.get("review_status") == "contradictory"
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
    workspace = resolve_workspace(args.workspace)
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
    application_events = receipt.get("application_events")
    if application_events is None:
        application_events = []
    elif not isinstance(application_events, list) or not all(
        isinstance(event, dict) for event in application_events
    ):
        raise ValueError("receipt application_events 无效")
    event = {
        "project": args.project or None,
        "result_observed": args.result_observed,
        "decision_changed": args.decision_changed,
        "result": args.result or "",
        "human_usefulness": args.human_usefulness,
        "recorded_at": utc_now(),
    }
    application_events.append(event)
    receipt["application_events"] = application_events
    receipt["application"] = event
    receipt["human_usefulness"] = args.human_usefulness
    receipt["updated_at"] = event["recorded_at"]
    markdown_path = receipt_path.with_suffix(".md")
    if markdown_path.is_symlink():
        raise ValueError(f"receipt Markdown 是符号链接：{markdown_path}")
    if markdown_path.is_file():
        markdown = markdown_path.read_text(encoding="utf-8")
        if APPLICATION_HISTORY_MARKER in markdown:
            markdown = markdown.split(APPLICATION_HISTORY_MARKER, 1)[0].rstrip()
        else:
            legacy_history = re.search(r"\n## Application History\n\n### Event 1\n", markdown)
            if legacy_history:
                markdown = markdown[:legacy_history.start()].rstrip()
            else:
                markdown = re.split(r"\n## Application(?: History)?\n", markdown, maxsplit=1)[0].rstrip()
        event_blocks = []
        for index, application_event in enumerate(receipt["application_events"], start=1):
            event_blocks.extend(
                [
                    f"### Event {index}",
                    "",
                    f"- Recorded at: `{application_event.get('recorded_at', 'unknown')}`",
                    f"- Project: `{application_event.get('project') or 'unknown'}`",
                    f"- Result observed: `{application_event.get('result_observed', 'unknown')}`",
                    f"- Decision changed: `{application_event.get('decision_changed', 'unknown')}`",
                    f"- Human usefulness: `{application_event.get('human_usefulness', 'unknown')}`",
                    f"- Result: {application_event.get('result') or 'unknown'}",
                    "",
                ]
            )
        markdown = (
            markdown
            + "\n\n"
            + APPLICATION_HISTORY_MARKER
            + "\n## Application History\n\n"
            + "\n".join(event_blocks)
        )
        atomic_write(markdown_path, markdown.encode("utf-8"))
    atomic_json(receipt_path, receipt)
    return {"receipt": str(receipt_path.relative_to(workspace)), "application": receipt["application"], "human_usefulness": receipt["human_usefulness"]}


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description=__doc__)
    sub = command.add_subparsers(dest="command", required=True)

    init_parser = sub.add_parser("init", help="create a private workspace")
    init_parser.add_argument("--workspace", required=True)
    init_parser.set_defaults(handler=init_workspace)

    status_parser = sub.add_parser("status", help="read the current lifecycle stage without writing")
    status_parser.add_argument("--workspace", required=True)
    status_parser.set_defaults(handler=status)

    next_parser = sub.add_parser("next", help="read the next lifecycle action without writing")
    next_parser.add_argument("--workspace", required=True)
    next_parser.set_defaults(handler=status)

    ingest_parser = sub.add_parser("ingest", help="ingest one explicit file or directory")
    ingest_parser.add_argument("--workspace", required=True)
    ingest_parser.add_argument("--source", required=True)
    ingest_parser.add_argument("--label")
    ingest_parser.add_argument("--exclude", action="append", default=[])
    ingest_parser.add_argument(
        "--strict", action="store_true",
        help="遇到任意文件读取错误时以非零退出；已成功写入的 staging 结果保留",
    )
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
    query_parser.add_argument(
        "--context-budget", type=int, default=4000,
        help="maximum total snippet size in Unicode characters (default: 4000)",
    )
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
