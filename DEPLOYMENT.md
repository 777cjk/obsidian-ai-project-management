# Local Deployment

This repository is a portable Agent Skill. Its deployment unit is the skill
directory itself. Python 3.10 or newer is required to install and validate the
package and to run the local knowledge loop. No third-party Python packages, a
database, an API key, or an Obsidian vault are required.

## Get A Release

To install a published release, clone its tag and install to the host's skill
directory:

```bash
git clone --branch v0.4.1 https://github.com/777cjk/obsidian-ai-project-management.git
cd obsidian-ai-project-management
python3 --version
scripts/verify.sh
scripts/install.sh \
  --target "$HOME/.codex/skills/obsidian-ai-project-management"
```

For Claude Code, use
`"$HOME/.claude/skills/obsidian-ai-project-management"` as the target. After
installation, start a new agent session and ask it explicitly to use
`obsidian-ai-project-management`. The installer does not modify host settings
or restart an active agent.

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
