# Obsidian AI Project Management

A portable Agent Skill for using an Obsidian vault as the canonical project context for AI work.

It gives an agent a small, auditable workflow:

```text
project card -> 2–3 current evidence files -> one judgment -> one artifact -> verification -> result receipt
```

The package is designed to work with Codex, Claude Code, and other agents that support the open Agent Skills format. It does not require a particular router, dashboard, model provider, or second project database.

## What it includes

- bounded context and progressive disclosure;
- a canonical project-card contract;
- a portable context package and result receipt;
- temporary four-file change packages for high-impact work;
- a source → candidate → reviewed asset → application knowledge pipeline;
- a dependency-free executable `init → ingest → review → query → record-result`
  canary loop with private raw snapshots and cited receipts;
- a bounded first-run `profile_scan.py` that discovers common document roots,
  previews scope, excludes sensitive/cache paths, extracts text from Markdown,
  text, JSON/CSV/YAML/HTML and common OOXML documents, and builds reviewable
  personal-background/project-map candidates;
- a research-backed knowledge-base methods baseline covering PARA, Zettelkasten,
  local-first vaults, hybrid retrieval, context layers, review queues, and
  graph/RAG boundaries;
- an optional source-ingest adapter for local files, Feishu, Baidu Netdisk, and document parsers;
- a dependency-free WeChat Moments JSON/JSONL adapter that stages private, unreviewed Obsidian candidates;
- provenance, freshness, contradiction, and token-budget retrieval guidance;
- a dated GitHub and public X/Twitter community-research snapshot;
- privacy and host-adaptation guidance;
- source attribution for Spec Kit, OpenSpec, Superpowers, and Agent Skills.

## Install From GitHub

Requirements: Git and Python 3.10 or newer. The package uses only the Python
standard library; the version requirement is for validation and the local
knowledge-loop runner.

```bash
git clone --branch v0.5.0 https://github.com/777cjk/obsidian-ai-project-management.git
cd obsidian-ai-project-management
python3 --version
scripts/verify.sh
scripts/install.sh \
  --target "$HOME/.codex/skills/obsidian-ai-project-management"
```

For Claude Code, use
`"$HOME/.claude/skills/obsidian-ai-project-management"` as the install target.
If upgrading, add `--replace`; the previous copy is moved to a timestamped
backup. The installer does not edit host configuration or restart the agent.
After installation, start a new agent session and explicitly ask it to use
`obsidian-ai-project-management` with one selected Markdown folder. Confirm the
Skill is loaded before asking it to ingest personal material.

Then configure the host adapter with the user's Obsidian vault root and
project-card directory. Start with one real project card and one current
evidence file before enabling automatic routing or writeback. The skill does
not assume that a host exposes a checkpoint command; without one, it returns a
proposed payload for review.

The smallest context package looks like this:

```yaml
context_version: 2
project_card: "/path/to/vault/projects/example.md"
owner_project: "Example project"
intent: "Continue the current project"
requested_artifact: "One visible result"
acceptance:
  pass: "The result can be opened and verified"
writeback: "checkpoint_preview"
```

## First Run: Build Personal Context

For a zero-setup friend workflow, use the bounded profile scanner. It looks
for common document roots under the user's home directory (Desktop, Documents,
Downloads, Pictures, Obsidian, and AI workspace), plus any explicitly supplied
folder. It shows a private scope preview before it reads document contents.

```bash
python3 scripts/profile_scan.py plan \
  --workspace /path/to/private-staging/profile
python3 scripts/profile_scan.py status \
  --workspace /path/to/private-staging/profile
```

Inspect `scan-plan.json` and its root/count summary. After the person confirms
the scope, collect the selected sources:

```bash
python3 scripts/profile_scan.py collect \
  --workspace /path/to/private-staging/profile \
  --confirm-scope
```

This reuses the existing immutable raw/candidate staging loop and writes two
unreviewed candidates: a personal-background candidate and a project-map
candidate. It excludes credentials, `.env` files, SSH/Keychain/browser/WeChat
data, caches, binaries, and oversized files by default. DOCX/PPTX/XLSX visible
text is extracted locally with the standard library; PDF and image files are
reported in the preview as metadata-only and are not parsed in this release.

Read both candidate files, then approve them together:

```bash
python3 scripts/profile_scan.py review-profile \
  --workspace /path/to/private-staging/profile \
  --decision approve \
  --confirm
python3 scripts/profile_scan.py context \
  --workspace /path/to/private-staging/profile \
  --context-budget 12000
```

The scanner produces source-cited drafts and heuristic categories; it does not
replace the agent's synthesis. Have Codex read the source candidates in batches,
correct the personal background/project map using evidence, and show the draft
for a human accuracy check before approval. To make future Codex sessions
automatically discover the approved profile, install a managed pointer into
the user's global Codex instructions after approval:

```bash
python3 scripts/profile_scan.py install-codex-context \
  --workspace /path/to/private-staging/profile --confirm
```

This preserves existing `~/.codex/AGENTS.md` rules and creates a timestamped
backup. To remove only the managed block later:

```bash
python3 scripts/profile_scan.py remove-codex-context --confirm
```

Approval creates the stable private files
`knowledge/profile-context.md`, `knowledge/project-map.md`, and
`knowledge/profile-context.json`. A later Codex turn should read the bounded
`context` output together with the current canonical project card. The context
pack contains source citations and unknowns; it does not replace a current
project card or the user's latest instruction. The package never edits the
original files or writes the host's canonical Obsidian Vault automatically.

For source collection, read [references/ingest-adapter.md](references/ingest-adapter.md)
and use the sibling `obsidian-knowledge-ingest` adapter. It stages manifests and
candidates without changing the canonical vault. Connector OAuth, parser
dependencies, and platform scopes remain explicit host configuration.

For architecture decisions, read
[references/methods-benchmark.md](references/methods-benchmark.md). It records
what mature personal-knowledge and RAG projects actually do, which parts this
Skill adopts, and which heavier components stay deferred until a real canary
proves they are needed.

For the latest public ecosystem comparison, read
[references/community-research-2026-09-30.md](references/community-research-2026-09-30.md).
GitHub stars, README claims, and public social posts are discovery signals;
they do not replace a clean friend-vault canary.

## Run The Functional Canary

The repository now contains a small runnable loop that proves the core
knowledge lifecycle without installing a vector database or sending files to a
cloud service:

```bash
python3 scripts/knowledge_loop.py init --workspace /path/to/private-staging
python3 scripts/knowledge_loop.py status --workspace /path/to/private-staging
python3 scripts/knowledge_loop.py ingest \
  --workspace /path/to/private-staging \
  --source /path/to/explicit/source-folder \
  --label friend-vault
```

Review one emitted file under `candidates/`, then approve it explicitly:

```bash
candidate_path="PASTE_ONE_FULL_CANDIDATE_PATH_HERE"
python3 scripts/knowledge_loop.py review \
  --workspace /path/to/private-staging \
  --candidate "$candidate_path" \
  --decision approve \
  --summary "人工确认的可复用结论"
```

Replace the variable value with one complete path from the `candidates` array
printed by `ingest` (for example, `candidates/<filename>.md`). Do not prepend
`candidates/` a second time.

Query approved assets and record whether the result was useful:

```bash
python3 scripts/knowledge_loop.py query \
  --workspace /path/to/private-staging \
  --query "来源正文中出现的关键词"
python3 scripts/knowledge_loop.py record-result \
  --workspace /path/to/private-staging \
  --receipt receipts/query-<id>.json \
  --project "当前项目" \
  --result "实际采用后的结果" \
  --result-observed unknown \
  --decision-changed unknown \
  --human-usefulness unknown
```

At any point, `status` is a read-only view of the next lifecycle step. The
same result is available as `next`; neither command creates a workspace or
changes the manifest. A new workspace reports `init`, an ingested candidate
reports `review`, an approved asset reports `query`, and an unrecorded query
receipt reports `record-result`.

The `knowledge_loop.py` runner still reads an explicitly selected file or
folder, while `profile_scan.py` provides the bounded common-root discovery
entry point above. Both keep raw snapshots and candidates private and do not
modify canonical Obsidian notes. Check the query receipt's citations before recording an outcome; set
`human-usefulness` to `useful` or `not_useful` only after a person judges the
result. The agent can summarize and categorize selected sources into
reviewable candidates; the runner itself preserves source text and does not
autonomously summarize it. Keep the staging workspace separate from the
canonical vault. Start with a small, non-sensitive folder and expand only
after reviewing the first results. This is a bounded profile scan, not an
unrestricted full-disk reader; the live-WeChat reader, semantic index, graph
backend, OCR, and automatic canonical writeback are not silently enabled.

For a user's own exported WeChat Moments, use the portable adapter:

```bash
python3 scripts/moments_to_candidate.py \
  --input /path/to/moments.json \
  --output-dir /path/to/private-staging/wechat-moments \
  --self-name "Your nickname"
```

It accepts exported JSON or JSONL and emits a normalized JSONL file, a
SHA-256 manifest, and an unreviewed candidate Markdown note. See
[references/wechat-moments.md](references/wechat-moments.md) for the current
GitHub source matrix and the boundary between an export tool and this Skill.
Raw WeChat databases, running-process extraction, and automatic canonical
vault writes are intentionally outside the portable package.

Validate a checkout with the included command:

```bash
scripts/verify.sh
```

GitHub Actions additionally runs Anthropic's upstream Agent Skills validator
from a pinned source and verifies its SHA-256.

For a dependency-free local check and an explicit host install with a
timestamped replacement backup, use [DEPLOYMENT.md](DEPLOYMENT.md):
`scripts/verify.sh` and `scripts/install.sh`.

## Privacy

The public package contains placeholders only. Keep personal vault paths, customer information, credentials, local service URLs, and host-specific commands in a separate ignored adapter.

## License

This integration package is released under the [MIT License](LICENSE). The
upstream projects listed in the attribution table keep their own licenses; see
[references/source-methods.md](references/source-methods.md) and check each
upstream repository before copying code or extending this skill.

## Before Publishing A Vault Adapter

Keep private vault paths, customer information, credentials, local service
URLs, and host-specific commands in an ignored adapter such as
`private-adapter/`. Publish this portable package separately from any personal
Obsidian vault. Run the skill validator and a repository-wide secret/path scan
before pushing.
