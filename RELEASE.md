# obsidian-ai-project-management v0.1.1

Version: `0.1.1` (`v0.1.1`).

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
include a configured user's Obsidian vault, credentials, or platform OAuth
connections. The sibling ingest adapter is maintained and installed separately.
