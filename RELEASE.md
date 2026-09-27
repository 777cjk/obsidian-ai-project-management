# obsidian-ai-project-management v0.1.0

Version: `0.1.0` (`v0.1.0`).

## Included

- Portable Agent Skill for Obsidian-backed project context and progress.
- Canonical project-card, bounded-context, verification, and result-receipt
  guidance.
- Source-to-asset knowledge workflow and optional `obsidian-knowledge-ingest`
  adapter contract.
- Host adaptation, installation, and rollback instructions.
- GitHub Actions checks for repository hygiene and Anthropic's pinned Agent
  Skills validator.

## Validation

```bash
scripts/verify.sh
```

The CI workflow additionally fetches the upstream validator at a pinned commit,
checks its SHA-256, and runs it as part of `scripts/verify.sh`.

## Scope

This release contains the portable Skill and its documentation. It does not
include a configured user's Obsidian vault, credentials, or platform OAuth
connections. The sibling ingest adapter is maintained and installed separately.
