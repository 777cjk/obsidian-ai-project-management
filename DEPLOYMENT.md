# Local Deployment

This repository is a portable Agent Skill. Its deployment unit is the skill
directory itself; it does not need a Python runtime, a database, an API key, or
an Obsidian vault to pass package validation.

## Verify a checkout

```bash
scripts/verify.sh
```

The verifier checks the required Skill frontmatter, rejects host-specific
absolute paths and credential-like values, and resolves relative Markdown
links. If the optional official validator is available, pass it explicitly:

```bash
SKILL_VALIDATOR=/path/to/quick_validate.py scripts/verify.sh
```

## Install into a host

The installer requires an explicit final target. It validates the source first
and never copies credentials, vault data, or host configuration:

```bash
scripts/install.sh \
  --target "$HOME/.codex/skills/obsidian-ai-project-management"
```

If a target already exists, installation stops. To upgrade it, request an
explicit replacement; the existing target is moved to a timestamped sibling
backup before the new files are moved into place:

```bash
scripts/install.sh \
  --target "$HOME/.codex/skills/obsidian-ai-project-management" \
  --replace
```

Use the equivalent host-supported skills directory for Claude Code. The
package itself does not edit host settings or restart an agent.

## Rollback

The replacement installer keeps the previous skill under:

```text
<skills-parent>/.obsidian-ai-project-management.backups/<timestamp>/
```

To roll back, remove or move the current target aside and move the selected
backup back to the target path. Keep this operation explicit so an active host
cannot be changed accidentally. Re-run `scripts/verify.sh` against the source
checkout and inspect the restored directory before restarting the host.

## Relationship to the ingest adapter

The sibling `obsidian-knowledge-ingest` repository has its own Python-local
deployment and verification flow. Install the two packages independently;
connector OAuth, parser packages, and private vault adapters stay outside this
portable Skill.
