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

When the task is knowledge collection, synthesis, or retrieval, use the source-to-asset pipeline in [references/knowledge-pipeline.md](references/knowledge-pipeline.md). Preserve original sources, keep AI extraction in a candidate state until reviewed, and cite vault-relative evidence in durable assets.

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
