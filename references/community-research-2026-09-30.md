# Community Research: Obsidian Knowledge Systems

Research date: 2026-09-30

This note records public discovery evidence used to choose the next small
improvements for this Skill. GitHub metadata and README descriptions are
discovery evidence, not proof that a repository works for a friend's vault.
Public X/Twitter posts are community signals, not independent product tests.

## Design signals

The strongest recurring pattern is not "add a vector database first":

```text
explicit capture -> immutable source -> candidate extraction
-> human review/contradiction/freshness -> linked knowledge
-> bounded retrieval with citations -> observed application result
```

The practical implication for this repository is to make the deterministic
boundary truthful before adding semantic search, graph traversal, or
background automation.

| Signal | Evidence observed | Adopted decision |
| --- | --- | --- |
| Source-backed compilation | `AgriciDaniel/claude-obsidian` keeps raw sources, source/claim ledgers, review state, contradiction and freshness metadata, and uses previewable transactions. | Add truthful source identity, stale/deleted state, bounded retrieval, and preserve the approval boundary. |
| Small local loop first | `ab2891/obsidian-kb` uses raw/topic notes, an index, an append-only log, and query-first Markdown rather than requiring a vector service. | Keep the standard-library canary and make its receipts append-only. |
| Optional semantic fallback | `Vasallo94/ObsidianRAG` uses SQLite FTS5 plus optional vector retrieval with explicit build/refresh/prune and copy-on-write revisions. | Keep lexical retrieval as the default; add semantic search only behind a measured canary. |
| Read-only next action | `swarmclawai/swarmvault` exposes `next` and `doctor` so a new user can see whether to initialize, ingest, review, query, or refresh. | Add a read-only status/next surface before adding infrastructure. |
| Persistent agent memory | `breferrari/obsidian-mind` separates deterministic hooks, session context, typed note routing, and optional QMD semantic search across Claude Code, Codex CLI, and Gemini CLI. | Treat session context and semantic indexing as optional host adapters, not the portable Skill's source of truth. |
| Multi-agent coordination | `vincent-wen789/obsidian-rag-protocol` uses append-only logs, cursors, SHA-256 indexing, and alias-first lookup. | Consider this only for a later multi-agent profile; it is not needed for one friend and one vault. |

## GitHub repositories to keep watching

Metadata was read with the GitHub API on 2026-09-30.

| Repository | Stars | License | Last push observed | Why it matters | Decision |
| --- | ---: | --- | --- | --- | --- |
| [AgriciDaniel/claude-obsidian](https://github.com/AgriciDaniel/claude-obsidian) | 15,306 | MIT | 2026-09-10 | Source/claim provenance, review and contradiction ledgers, linked Markdown, lint, retrieval, Canvas. | Borrow contracts and transaction ideas; do not copy its full command suite. |
| [breferrari/obsidian-mind](https://github.com/breferrari/obsidian-mind) | 4,735 | MIT | 2026-09-02 | Cross-agent persistent memory, session hooks, deterministic validation, optional local QMD. | Good host-adapter reference; too large for the default portable runner. |
| [eugeniughelbur/obsidian-second-brain](https://github.com/eugeniughelbur/obsidian-second-brain) | 4,648 | MIT | 2026-09-28 | Temporal facts, scheduled maintenance, rewrite/reconcile flows, retrieval benchmark. | Study freshness and benchmark ideas; defer autonomous rewrites until a canary. |
| [obsidianmd/obsidian-clipper](https://github.com/obsidianmd/obsidian-clipper) | 5,267 | MIT | 2026-09-22 | Explicit, template-driven source capture. | Use as an acquisition pattern, not as a bulk crawler. |
| [brianpetro/obsidian-smart-connections](https://github.com/brianpetro/obsidian-smart-connections) | 5,474 | NOASSERTION | 2026-09-24 | Local embeddings for related-note discovery. | Optional discovery layer only; similarity is not evidence. |
| [swarmclawai/swarmvault](https://github.com/swarmclawai/swarmvault) | 705 | MIT | 2026-06-30 | Raw/wiki/schema layers, approval queue, typed graph, hybrid retrieval and context packs. | Borrow the layer model and read-only next action; defer the heavier CLI. |
| [Vasallo94/ObsidianRAG](https://github.com/Vasallo94/ObsidianRAG) | 122 | MIT | 2026-09-18 | FTS5 + LanceDB hybrid search, copy-on-write revisions, explicit refresh/prune. | Measure lexical failure first, then consider a rebuildable index. |
| [agent-creativity/agentic-local-brain](https://github.com/agent-creativity/agentic-local-brain) | 78 | no verified SPDX | 2026-09-24 | Multi-source ingestion, entity/relationship discovery and local retrieval. | Research reference only until license and real canary are clear. |
| [fakechris/obsidian_vault_pipeline](https://github.com/fakechris/obsidian_vault_pipeline) | 164 | Apache-2.0 | 2026-09-26 | OVP2 keeps raw sources, grounded quote units, cards, claims, append-only ledgers, deterministic read models, cited ask flow, and a read-only doctor/console. | Strong evidence for making the source/evidence ledger the truth layer; study its operator runbook, but keep this Skill's standard-library runner smaller. |
| [optimus-a1/agent-wiki-hub](https://github.com/optimus-a1/agent-wiki-hub) | 3 | MIT | 2026-09-30 | Raw/candidate/wiki layers, source-review queues, current-fact gates, density audits, and keyword fallback when optional RAG is absent. | Borrow explicit current-fact and source-review markers; do not add its domain pack or crawler to the portable default. |
| [mickeytony0215-png/obsidian-llm-wiki](https://github.com/mickeytony0215-png/obsidian-llm-wiki) | 2 | MIT | 2026-07-06 | Review-gated paper-to-wiki workflow with pre-review throughput, disputed states, citation cascade caveats, and read-only vault search. | Borrow the idea that review status propagates to downstream citations; defer PDF-specific commands. |
| [Jaycelu/Smart-Review](https://github.com/Jaycelu/Smart-Review) | 2 | MIT | 2026-06-29 | Obsidian-native spaced review queues with append-only review history and optional evidence-grounded exams. | Keep spaced review as a later learning layer; it is not part of source ingestion or project-state truth. |

Stars and push dates can change. They are included to make the research
snapshot reproducible, not as a quality ranking.

## Public X/Twitter signals

The existing logged-in X browser surface exposed these public search results on
2026-09-30. No cookies, tokens, or private account data were copied into this
repository.

| Public post | What was visible | How to use it |
| --- | --- | --- |
| [Tom Doerr, 2105025968612028419](https://x.com/tom_doerr/status/2105025968612028419) | Describes `breferrari/obsidian-mind` as connecting Claude Code, Codex CLI, and Gemini CLI to an Obsidian vault so notes, links, and context persist across sessions. Search view showed 269 likes and 15,815 views at capture time. | A community signal that cross-agent persistence is a compelling use case; the repository README is the implementation evidence. |
| [chewa, 2077040344118784109](https://x.com/0xchewa/status/2077040344118784109) | Promotes a "self-writing vault" article about scheduled filing, connected notes, and session context. Search view showed 743 likes and 360,204 views at capture time. | Treat as a discussion signal about automation and maintenance, not proof that unattended writes are reliable. |
| [CyrilXBT, 2076847146251190642](https://x.com/cyrilXBT/status/2076847146251190642) | Presents a short "AI second brain" setup using Claude Desktop and Obsidian. Search view showed 1,441 likes and 262,216 views at capture time. | Supports a low-friction onboarding message; it does not validate the underlying workflow. |

X search is volatile and can return different results by account, query, and
time. These posts are not used as technical proof, and no automated X reader
is added to the Skill by this research.

## Recommendation for this repository

1. Make the existing local loop truthful at its boundaries: no self-ingest,
   no stale approved results, real scope filtering, bounded snippets, and
   append-only application history.
2. Add a read-only `status`/`next` view and an onboarding fixture so a friend
   can see the next action without knowing the internal file layout.
3. Add structured claims/entities/tags/links and freshness fields only after
   the boundary hardening and one real friend-vault canary.
4. Add semantic retrieval as a rebuildable optional accelerator only when a
   measured query set demonstrates keyword failure.
5. Keep full-machine scanning, autonomous vault rewrites, GraphRAG, hosted
   sync, and live social-platform extraction outside the default install.
