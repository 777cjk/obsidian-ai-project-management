# obsidian-ai-project-management v0.2.1

Version: `0.2.1` (`v0.2.1`).

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
- GitHub Moments exporter capability and license boundary documented without
  bundling third-party extraction or decryption code.
- Owner-only normalized output by default, explicit non-owner opt-in, and
  collision-safe staging that refuses to overwrite existing output files.
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

This release contains the portable Skill and its documentation. It does not
include a configured user's Obsidian vault, credentials, platform OAuth
connections, raw WeChat databases, or a running-process extractor. The sibling
ingest adapter is maintained and installed separately.
