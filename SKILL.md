---
name: obsidian-ai-project-management
description: Structure and continue AI projects backed by an Obsidian vault using bounded context, canonical project cards, change packages, verification, and result receipts.
---

# Obsidian AI Project Management

Use this skill when a user wants an AI assistant to manage, continue, review, or improve projects stored in Obsidian. It turns a vault into a lightweight project context system without creating a second project database.

## Operating Contract

Treat one Obsidian project card as the canonical state source. Do not infer project status from chat history, filenames alone, generated candidates, or old reports.

For each request, reduce the work to:

```text
one judgment -> one visible artifact -> one human action -> one result receipt
```

Keep these evidence classes separate:

- engineering output and tests;
- human review or adoption;
- user or audience feedback;
- commercial or operational results.

Never promote an engineering check into adoption, user feedback, or business success.

## Default Workflow

1. Identify the unique project card by explicit project name, alias, path, or the user's current context. If several cards match, ask one ownership question before writing.
2. Read the card frontmatter and handoff sections first. Read at most 2–3 current evidence files, preferring recent results, a current progress board, a README/HANDOFF, a data table, or a runtime receipt.
3. State the current project, evidence level, `single_judgment`, requested artifact, acceptance conditions, stop condition, and the one human action.
4. Execute the smallest reversible slice that produces a visible artifact. Do not expand the system merely because more tools or documents are available.
5. For cross-module, high-impact, multi-agent, migration, provider, data-schema, release, or rollback-sensitive work, create a temporary four-file change package. Read [references/change-packages.md](references/change-packages.md).
6. Verify the artifact with a command, observation, file check, screenshot, user quote, or explicit failure evidence. Record the exact evidence path.
7. End with a structured result receipt. Only a real artifact, explicit failure, or clear stop point may become a canonical checkpoint.

## Context Budget

Use progressive disclosure:

- L0: stable rules and this skill;
- L1: one canonical project card;
- L2: 2–3 current evidence files;
- L3: a temporary change package only when the task needs it.

Do not load the whole vault by default. Older reports are for resolving a current conflict, not routine context.

When the task is knowledge collection, synthesis, or retrieval, use the source-to-asset pipeline in [references/knowledge-pipeline.md](references/knowledge-pipeline.md). Preserve original sources, keep AI extraction in a candidate state until reviewed, and cite vault-relative evidence in durable assets. For architecture or workflow choices, use [references/methods-benchmark.md](references/methods-benchmark.md): keep Markdown and source evidence canonical, separate memory from knowledge and projects, and add semantic or graph indexes only behind a measured retrieval need.
For current public ecosystem signals, use [references/community-research-2026-09-30.md](references/community-research-2026-09-30.md). Treat GitHub metadata and public X/Twitter posts as discovery evidence, not proof of a friend's vault usefulness.

## Knowledge-Base Operating Loop

Treat the knowledge base as a feedback system rather than a folder tree or a
vector database:

```text
explicit scope -> immutable source -> candidate -> review/contradiction check
-> linked knowledge or first-party memory -> bounded retrieval -> cited answer
-> application result -> correction or freshness update
```

Use this retrieval ladder in order:

1. Clarify the question and project scope.
2. Recall with deterministic full-text/keyword search.
3. Add semantic recall only when wording mismatch makes it useful.
4. Rerank by authority, freshness, evidence status, and project relevance.
5. Add graph/context expansion only for multi-hop or global questions.
6. Assemble a bounded context pack and emit a query receipt with citations,
   missing evidence, and the human outcome when known.

Do not silently move notes because an embedding is similar. Do not promote a
candidate into memory, a project card, or a reviewed asset without the relevant
human/evidence gate. `next`/doctor-style status may recommend the next step,
but it must remain read-only until the host checkpoint is explicitly invoked.

## Executable Closed Loop

For a clean local canary, the package includes a dependency-free runner:
`scripts/knowledge_loop.py`. It makes the lifecycle observable instead of
leaving it as prompt guidance:

```text
init -> ingest (explicit file/folder) -> review (approve/reject/contradictory)
-> query (keyword + citations) -> record-result (application receipt)
```

The runner requires Python 3.10 or newer and uses only the standard library.
After `ingest`, it prints the relative paths of new or still-unreviewed
candidates. Read those candidates as source material, synthesize and categorize
them with explicit source citations, and keep the result unreviewed until a
person approves it. The runner preserves source text; it does not itself
generate a summary or decide the category.

The runner copies UTF-8 text sources into a private raw snapshot, writes an
unreviewed candidate with a source hash, promotes only an explicitly approved
candidate into `knowledge/`, and writes JSON/Markdown query receipts under
`receipts/`. It never scans the whole computer, calls a cloud model, or writes
the host's canonical Obsidian notes. A host may later use its checkpoint path
to apply an approved asset.

Use `status` (or its alias `next`) before touching the workspace when the
operator is unsure which step comes next:

```bash
python3 scripts/knowledge_loop.py status --workspace /path/to/private-staging
python3 scripts/knowledge_loop.py next --workspace /path/to/private-staging
```

These commands are strictly read-only. They do not create a missing workspace,
repair a manifest, or update receipts. They report `init`, `ingest`, `review`,
`query`, or `record-result` as the next action and surface all pending query
receipts.

Example:

```bash
python3 scripts/knowledge_loop.py init --workspace /path/to/private-staging
python3 scripts/knowledge_loop.py ingest \
  --workspace /path/to/private-staging \
  --source /path/to/explicit/source-folder \
  --label friend-vault
candidate_path="PASTE_ONE_FULL_CANDIDATE_PATH_HERE"
python3 scripts/knowledge_loop.py review \
  --workspace /path/to/private-staging \
  --candidate "$candidate_path" \
  --decision approve \
  --summary "人工确认的可复用结论"
python3 scripts/knowledge_loop.py query \
  --workspace /path/to/private-staging \
  --query "要查的问题"
python3 scripts/knowledge_loop.py record-result \
  --workspace /path/to/private-staging \
  --receipt receipts/query-<id>.json \
  --project "当前项目" \
  --result "实际采用后的结果" \
  --result-observed unknown \
  --decision-changed unknown \
  --human-usefulness unknown
```

Set `candidate_path` to a complete path from `ingest` output; it already
starts with `candidates/`.

This is the first real functional slice. Semantic search, reranking, graph
expansion, richer parsers, and platform connectors remain optional layers
behind the same receipt contract.

When the task includes local folders, Feishu, Baidu Netdisk, or document parsing, use the optional [references/ingest-adapter.md](references/ingest-adapter.md). It describes the reusable connector stack and the `obsidian-knowledge-ingest` staging adapter. Source manifests and candidates are inputs to this skill; they are never a replacement for the canonical project card or reviewed knowledge assets.

When the task includes a user's own WeChat Moments archive, read
[references/wechat-moments.md](references/wechat-moments.md) and use
`scripts/moments_to_candidate.py`. The adapter accepts an exported
`moments.json`/JSONL, defaults to the account owner's posts, writes private
staging files, and keeps the result unreviewed until a host checkpoint. It is
an import layer, not a live WeChat reader or database decrypter; keep source
acquisition and any platform-specific exporter outside this portable Skill.
When the user asks for a background summary, create a separate unreviewed
knowledge candidate with dated source-record citations; distinguish explicit
self-statements from inferences and unknowns.

## Canonical Card Contract

At minimum, a project card has `project_card: true`, `status`, `category`, `path`, `next_action`, `resume_command`, and `last_updated`. When available, also use `current_stage`, `weekly_outcome`, `evidence`, `evidence_status`, `blocker`, `focus`, and decision-gate fields. Keep `next_action` identical to the card's handoff sentence.

Read [references/protocol.md](references/protocol.md) for the portable YAML context and receipt schemas. Use [assets/templates/](assets/templates/) when the user asks for a copyable template.

## Writeback Boundary

The skill may prepare a checkpoint payload, but the host's canonical write tool remains authoritative. Before applying a checkpoint:

- match exactly one project card;
- preserve unrelated status, focus, role, and business decisions;
- keep the card summary short and link to detailed evidence;
- record the result receipt and evidence references;
- fail closed on ambiguity, secrets, concurrent edits, or missing evidence.

If the host does not provide a checkpoint tool, show the proposed payload and ask the user to approve the canonical edit. Do not silently create a second registry or dashboard.

## Host Adaptation

The skill is portable. Configure the vault root, project-card directory, optional natural-language router, and optional checkpoint command in the host integration. Never hard-code a user's home directory, private project names, tokens, cookies, or local service URLs in this skill. Read [references/adaptation.md](references/adaptation.md) for the integration points.

## Method Provenance

This workflow incorporates the portable ideas from GitHub Spec Kit, OpenSpec, Superpowers, and Agent Skills. Read [references/source-methods.md](references/source-methods.md) for attribution and the exact pieces adopted. It does not copy their repositories or require their command systems.
