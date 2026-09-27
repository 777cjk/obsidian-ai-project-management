# Source Methods and Attribution

This skill is an original integration layer. It adopts small, portable workflow ideas and does not bundle or modify the upstream repositories.

| Source | Adopted idea | Deliberately omitted |
|---|---|---|
| [GitHub Spec Kit](https://github.com/github/spec-kit) | specify → plan → tasks → verify; acceptance scenarios early | its full CLI and repository layout |
| [OpenSpec](https://github.com/Fission-AI/OpenSpec) | separate current truth from a proposed change; archive after completion | a second `specs/` state database |
| [Superpowers](https://github.com/obra/superpowers) | bind work to artifacts, commands, assertions, and pass conditions | forcing every small action through a long plan |
| [Agent Skills](https://agentskills.io/) | frontmatter, progressive disclosure, and references/scripts/assets separation | loading every reference at startup |
| [AGENTS.md](https://github.com/agentsmd/agents.md) | short discoverable root context with narrower local instructions near the work | assuming every host loads the same files automatically |
| [claude-obsidian](https://github.com/AgriciDaniel/claude-obsidian) | source/claim provenance, inbox, lint, review, linked Markdown, diff-aware writes | its Claude-specific command suite |
| [SwarmVault](https://github.com/swarmclawai/swarmvault) | raw/wiki/schema layers, candidate approval, typed edges, hybrid retrieval, token budgets | a second graph database or state registry |
| [Remember Anything](https://github.com/FrancescoSaverioZuppichini/remember-anything) | preserve raw sources, separate notes/memory/projects, search before creating, relative citations | its OpenCode/QMD-specific setup |
| [Agentic Local Brain](https://github.com/agent-creativity/agentic-local-brain) | multi-source ingestion, graceful fallback, hybrid retrieval, rerank, graph context, staleness | mandatory server and embedding dependencies |
| [Obsidian + Claude Code PKM](https://github.com/ballred/obsidian-claude-pkm) | connect vision, goals, projects, reviews, and daily actions | a parallel goal database |
| [Obsidian OpenAgent](https://github.com/nikitaclicks/obsidian-openagent) | vault-aware tools, consent, and diff previews before writes | automatic remote model routing |
| [PaperBrain](https://github.com/DannyWANGD/PaperBrain) | schema-driven research status, priority, next action, doctor/check | paper-specific pipeline |
| [OpenViking](https://github.com/volcengine/OpenViking) | hierarchical context summaries and context compilation | an AGPL service as the vault source |
| [Hindsight](https://github.com/vectorize-io/hindsight) | retain/recall/reflect separation, temporal validity, superseding facts | a separate memory server by default |
| [Mem0](https://github.com/mem0ai/mem0) | scoped memory and semantic/BM25/entity/time retrieval | hosted benchmark claims as local evidence |
| [Letta Code](https://github.com/letta-ai/letta-code) | identity, memory blocks, Git-backed context, sleep-time maintenance | replacing the host's session or identity store |
| [agent-memory](https://github.com/tigerless-labs/agent-memory) | Markdown source of truth, rebuildable SQLite index, path-first bounded recall | early-stage runtime as a required dependency |
| [Dataview](https://github.com/blacksmithgu/obsidian-dataview) | frontmatter schema queried through DQL/DataviewJS | using a view as the canonical state source |
| [Obsidian Web Clipper](https://github.com/obsidianmd/obsidian-clipper) | user-reviewed web capture into local Markdown with templates and highlights | treating browser clipping as a bulk crawler or semantic classifier |
| [Obsidian MCP Server](https://github.com/cyanheads/obsidian-mcp-server) | configurable vault search/read and structured frontmatter access through Obsidian Local REST API | connecting with its default full-vault read/write scope; require `OBSIDIAN_READ_ONLY=true` and a narrow `OBSIDIAN_READ_PATHS` first |
| [larksuite/cli](https://github.com/larksuite/cli) | reuse the official CLI and existing OAuth for an explicitly selected Feishu source | duplicating credentials or treating Minutes scopes as Docs/Wiki scopes |
| [larksuite/lark-openapi-mcp](https://github.com/larksuite/lark-openapi-mcp) | official Feishu document/Wiki read connector and OAuth-scoped access | assuming MCP list/search results equal full file contents |
| [larksuite/oapi-sdk-python](https://github.com/larksuite/oapi-sdk-python) | typed Feishu API adapter, pagination, token and retry boundary | embedding platform credentials in the public Skill |
| [baidu-netdisk/mcp](https://github.com/baidu-netdisk/mcp) | official Baidu Netdisk list, metadata, search and summary connector | treating a summary or directory listing as a downloaded source |
| [gorakhargosh/watchdog](https://github.com/gorakhargosh/watchdog) | local change event source for a later incremental worker | making file events the knowledge truth without a manifest |
| [docling-project/docling](https://github.com/docling-project/docling) | high-fidelity document layout, tables and OCR parser | making its heavy runtime a mandatory Skill dependency |
| [run-llama/liteparse](https://github.com/run-llama/liteparse) | lightweight PDF parsing option | dropping page/source references from extracted text |
| [microsoft/markitdown](https://github.com/microsoft/markitdown) | simple Markdown conversion fallback for LLM input | treating Markdown conversion as semantic review |
| [ocrmypdf/OCRmyPDF](https://github.com/ocrmypdf/OCRmyPDF) | optional scanned-PDF preprocessing before parsing | bundling its MPL worker into the MIT Skill |

The upstream projects remain the authoritative source for their own licenses, commands, and changes. Check their current repositories before copying code or extending this skill. The table records ideas observed in public READMEs; it is not a claim that each project has been independently audited.

Repository status checked on 2026-09-28: the official Lark CLI and Obsidian
Web Clipper were actively updated in the preceding week; the reviewed
`baidu-netdisk/mcp` source last showed a code commit on 2025-09-23. Keep the
Baidu integration optional and verify actual file-content retrieval before
depending on it.
