# obsidian-ai-project-management v0.4.0

Version: `0.4.0` (`v0.4.0`).

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
python3 /path/to/skill-creator/scripts/quick_validate.py .
```

The CI workflow additionally fetches the upstream validator at a pinned commit,
checks its SHA-256, and runs it as part of `scripts/verify.sh`.

## Scope

This release contains the portable Skill, its executable local canary loop, and its documentation. It does not
include a configured user's Obsidian vault, credentials, platform OAuth
connections, raw WeChat databases, or a running-process extractor. The sibling
ingest adapter is maintained and installed separately.
