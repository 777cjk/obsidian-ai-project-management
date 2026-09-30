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
- a research-backed knowledge-base methods baseline covering PARA, Zettelkasten,
  local-first vaults, hybrid retrieval, context layers, review queues, and
  graph/RAG boundaries;
- an optional source-ingest adapter for local files, Feishu, Baidu Netdisk, and document parsers;
- a dependency-free WeChat Moments JSON/JSONL adapter that stages private, unreviewed Obsidian candidates;
- provenance, freshness, contradiction, and token-budget retrieval guidance;
- privacy and host-adaptation guidance;
- source attribution for Spec Kit, OpenSpec, Superpowers, and Agent Skills.

## Install

From a checked-out repository, install to an explicit host path:

```bash
scripts/install.sh \
  --target "$HOME/.codex/skills/obsidian-ai-project-management"
```

For Claude Code, pass its supported skills directory as `--target`. To upgrade
an existing installation, add `--replace`; the previous copy is kept in a
timestamped backup. The installer validates the package and does not edit host
settings or restart an agent. See [DEPLOYMENT.md](DEPLOYMENT.md) for rollback.

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

For source collection, read [references/ingest-adapter.md](references/ingest-adapter.md)
and use the sibling `obsidian-knowledge-ingest` adapter. It stages manifests and
candidates without changing the canonical vault. Connector OAuth, parser
dependencies, and platform scopes remain explicit host configuration.

For architecture decisions, read
[references/methods-benchmark.md](references/methods-benchmark.md). It records
what mature personal-knowledge and RAG projects actually do, which parts this
Skill adopts, and which heavier components stay deferred until a real canary
proves they are needed.

## Run The Functional Canary

The repository now contains a small runnable loop that proves the core
knowledge lifecycle without installing a vector database or sending files to a
cloud service:

```bash
python3 scripts/knowledge_loop.py init --workspace /path/to/private-staging
python3 scripts/knowledge_loop.py ingest \
  --workspace /path/to/private-staging \
  --source /path/to/explicit/source-folder \
  --label friend-vault
```

Review one emitted file under `candidates/`, then approve it explicitly:

```bash
python3 scripts/knowledge_loop.py review \
  --workspace /path/to/private-staging \
  --candidate candidates/<candidate-file>.md \
  --decision approve \
  --summary "人工确认的可复用结论"
```

Query approved assets and record whether the result was useful:

```bash
python3 scripts/knowledge_loop.py query \
  --workspace /path/to/private-staging \
  --query "要查的问题"
python3 scripts/knowledge_loop.py record-result \
  --workspace /path/to/private-staging \
  --receipt receipts/query-<id>.json \
  --project "当前项目" \
  --result "实际采用后的结果" \
  --result-observed yes \
  --decision-changed yes \
  --human-usefulness useful
```

The runner only reads an explicitly selected file or folder, keeps raw
snapshots and candidates private, and does not modify canonical Obsidian
notes. It is the minimal functional canary; the full-computer scanner,
live-WeChat reader, semantic index, and graph backend are not silently enabled.

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

Validate a checkout with:

```bash
python3 /path/to/skill-creator/scripts/quick_validate.py .
```

GitHub Actions runs the repository checks and Anthropic's upstream Agent
Skills validator on pushes and pull requests. The workflow pins the upstream
validator source to a commit and verifies its SHA-256 before execution.

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
