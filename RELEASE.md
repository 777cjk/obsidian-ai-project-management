# obsidian-ai-project-management v0.5.0

Version: `0.5.0` (`v0.5.0`).

## Feature Changes

- Added the bounded `scripts/profile_scan.py` first-run entry point for common
  Desktop/Documents/Downloads/Pictures/Obsidian/AI workspace roots.
- Added private scope previews, credential/cache/browser/WeChat denylist rules,
  file and byte budgets, and an explicit `--confirm-scope` collection gate.
- Added dependency-free visible-text extraction for DOCX, PPTX, and XLSX.
- Added source-cited, unreviewed personal-background and project-map
  candidates, an explicit profile approval gate, stable private
  `profile-context` assets, and bounded read-only Codex context output.
- Added 6 focused scanner tests covering scope preview, privacy exclusion,
  Office text extraction, discovery-budget limits, plan tampering, replaced
  roots, approval, and context output.
- Hardened collection against changed scan plans, directory-root replacement,
  and file/root identity drift between preview and collection.

This release keeps the v0.4.3 source/candidate/review/query/receipt loop and
does not claim friend-machine usefulness until a real canary is observed.

The profile scanner is bounded and local: it does not read passwords, browser
profiles, Keychain, raw WeChat databases, or the entire disk; it does not use
cloud APIs or write canonical Obsidian notes automatically.

---

# Previous v0.4.3 Notes

## Patch Changes

- `status` and `next` now fail closed when manifest entries/history contain
  non-object values, or when query application history contains malformed
  events.
- Markdown application history uses an internal marker so a result containing
  `## Application History` is preserved when later results are appended.

This patch supersedes v0.4.2 without rewriting its published tag.

## What Changed

- Added read-only `status` and `next` commands so a first-time user can see
  whether to initialize, ingest, review, query, or record an application
  result without changing the workspace.
- Hardened the local loop against source/workspace overlap, stale source
  records, ambiguous scopes, unbounded snippets, partial ingest, and lost
  application history.
- Added a dated public GitHub and X/Twitter research snapshot with explicit
  adoption and deferral decisions.

The clean-room friend-vault canary remains the human usefulness gate for this
release; local tests do not promote it to a product-success claim.

## Included

- Portable Agent Skill for Obsidian-backed project context and progress.
- Canonical project-card, bounded-context, verification, and result-receipt
  guidance.
- A source-to-asset pipeline that explicitly treats imported material as
  untrusted evidence, preserves provenance, and separates reviewed assets from
  project application results.
- Updated reuse guidance for the official Feishu CLI, Obsidian Web Clipper,
  and read-only configured Obsidian MCP access.
- Host adaptation, installation, and rollback instructions.
- Dependency-free WeChat Moments JSON/JSONL staging adapter with owner-only
  filtering, deduplication, private normalized output, SHA-256 manifest, and
  unreviewed Obsidian candidate generation.
- GitHub Moments exporter findings refreshed: the historical Apache-2.0 pin is
  distinguished from the current license-unverified HEAD; its decryptor uses
  pre-acquired keys, and no third-party extraction or decryption code is bundled.
- Research-backed knowledge-base methods baseline covering PARA, Zettelkasten,
  local-first Markdown vaults, hybrid retrieval, context layers, review queues,
  query receipts, and explicit GraphRAG/vector-database boundaries.
- Dependency-free `scripts/knowledge_loop.py` canary loop: explicit local
  ingest, immutable raw snapshot, unreviewed candidate, explicit review,
  deterministic keyword query with citations, and application result receipt.
- First-run installation instructions now cover cloning a published tag,
  Python prerequisites, host skill paths, and loading the Skill in a fresh
  agent session; ingest output lists candidate paths directly.
- Owner-only normalized output by default, explicit non-owner opt-in, and
  collision-safe staging that refuses to overwrite existing output files.
- Unattributed records, including the companion bridge's `未知作者`
  placeholder, are excluded by default. `--assume-self` applies only to
  unattributed records and does not override known other authors.
- Background synthesis instructions requiring dated record citations and a
  separate unreviewed knowledge candidate.
- GitHub Actions checks for repository hygiene and Anthropic's pinned Agent
  Skills validator.

## Validation

```bash
scripts/verify.sh
```

The CI workflow fetches the upstream validator at a pinned commit, checks its
SHA-256, and runs it as part of `scripts/verify.sh`.

## Scope

This release contains the portable Skill, its executable local canary loop, and its documentation. It does not
include a configured user's Obsidian vault, credentials, platform OAuth
connections, raw WeChat databases, or a running-process extractor. The sibling
ingest adapter is maintained and installed separately.
