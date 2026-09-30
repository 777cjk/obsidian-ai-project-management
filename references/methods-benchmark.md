# Knowledge-Base Methods Benchmark

Research date: 2026-09-30

This is a design benchmark, not a popularity ranking. The source set combines
official method pages, Obsidian documentation, and public GitHub READMEs. A
README describes an intended design; it is not independent proof that the
system works for a friend's vault.

## What the sources actually do

| Source | Observed design | Transferable lesson | Boundary |
| --- | --- | --- | --- |
| [PARA, Tiago Forte](https://fortelabs.com/blog/para/) | Organizes information by Projects, Areas, Resources, and Archives, with actionability as the primary placement rule. | Use lifecycle and next action to place material; do not force every note into a permanent topic tree. | PARA is an organization method, not a retrieval engine or evidence verifier. |
| [Zettelkasten.de: Introduction](https://zettelkasten.de/introduction/) and [Atomicity](https://zettelkasten.de/atomicity/) | Uses fixed-address, atomic notes and meaningful links so the collection becomes a navigable web of thoughts. | Extract one reusable claim or concept at a time, then connect it with explanatory links and hub notes. | Atomicity is a compass, not a rule to split every document into tiny fragments. |
| [Obsidian Help: how data is stored](https://help.obsidian.md/Getting+started/How+Obsidian+stores+data) | Keeps Markdown files in a local vault; links, metadata cache, and external file access keep the system portable. | Markdown remains the canonical store; indexes and caches must be rebuildable. | Obsidian does not automatically turn captures into reviewed knowledge. |
| [Obsidian Web Clipper](https://github.com/obsidianmd/obsidian-clipper) | Captures selected web material into durable Markdown using templates, variables, filters, and local image saving. | Make capture explicit and template-driven; preserve the source before synthesis. | It is an acquisition surface, not a whole-computer crawler. |
| [Smart Connections](https://github.com/brianpetro/obsidian-smart-connections) | Uses a local embedding model to surface related notes while writing and provides semantic lookup. | Similarity is a discovery hint that helps a human make links; it should not silently reorganize the vault. | Semantic similarity is not proof of identity, authority, or a valid project route. |
| [Remember Anything](https://github.com/FrancescoSaverioZuppichini/remember-anything) | Separates immutable `raw/` sources from compiled `wiki/`, first-party notes, memory, projects, and a local hybrid search layer; answers cite vault-relative evidence. | Search existing knowledge before creating a page, keep raw evidence separate, and answer with traceable citations. | Its OpenCode/QMD stack is optional; the layer model is the reusable part. |
| [SwarmVault](https://github.com/swarmclawai/swarmvault) | Uses raw sources, a generated/human wiki, and an editable schema; adds candidates, approval bundles, contradiction linting, hybrid search, graph traversal, context packs, and a read-only `next` workflow. | Add an explicit schema, approval queue, contradiction status, bounded context packs, and a next-action command. | It is a larger CLI/product; the Skill should absorb contracts, not its full runtime. |
| [OpenViking](https://github.com/volcengine/OpenViking) | Stores resources, memories, and skills in a URI-addressable hierarchy; scopes retrieval to a subtree and reads L0 summary, L1 overview, then L2 full content. | Use hierarchical context and project-scoped retrieval before loading full notes. | A context database is an accelerator; it must not replace portable Markdown. |
| [LlamaIndex](https://github.com/run-llama/llama_index) | Provides connectors, parsing/extraction, data structures, retrievers, rerankers, and query engines as replaceable integrations. | Keep acquisition, parsing, indexing, retrieval, and answer generation as separate interfaces. | The ecosystem is large; a portable Skill should not require its packages. |
| [RAGFlow](https://github.com/infiniflow/ragflow) | Emphasizes document understanding, explainable/template chunking, knowledge compilation, agentic multi-step retrieval, and traceable citations. | Make chunking/compilation inspectable and allow evidence verification for complex questions. | Multi-step retrieval and heavy parsing need a measured use case and resources. |
| [Haystack](https://github.com/deepset-ai/haystack) | Models retrieval, routing, memory, generation, tools, and evaluation as explicit modular pipelines. | Keep retrieval decisions visible and testable instead of hiding them in one prompt. | A framework pipeline is not a reason to add a service to a personal vault. |
| [Open WebUI](https://github.com/open-webui/open-webui) | Supports multiple loaders, vector stores, hybrid BM25+vector search, reranking, full-context mode, and source citations. | Use a retrieval ladder: deterministic recall first, semantic recall and reranking when needed, with citations. | More backends add operational and privacy cost; start with local Markdown search. |
| [Mem0](https://github.com/mem0ai/mem0) | Separates user/session/agent memory and describes semantic, keyword, entity, and temporal signals. | Treat personal facts and preferences as a distinct memory layer with time and entity context. | Memory is not the same as source-backed knowledge; writes need review and expiry. |
| [Microsoft GraphRAG](https://github.com/microsoft/graphrag) | Builds structured entities/relationships from unstructured text to answer global questions; warns that indexing is expensive and the repository is maintenance-mode research. | Add graph compilation only for cross-document/global questions after basic retrieval fails. | Do not make GraphRAG the default path for a small friend's vault. |

## Common core

Across the sources, the durable pattern is:

```text
scope and capture
  -> immutable source evidence
  -> candidate extraction
  -> review, contradiction, and freshness checks
  -> atomic concepts, entities, and meaningful links
  -> bounded retrieval (keyword -> semantic -> rerank/graph when justified)
  -> cited answer or project action
  -> observed result and correction
```

The core is therefore not “a vector database” and not “a large folder tree”.
It is a feedback loop that turns sources into reviewed, connected assets and
then records whether those assets changed a decision or produced a result.

## Adopt in this Skill now

1. **Five explicit layers**: `raw` source evidence, `candidate` extraction,
   `knowledge`/`wiki` reviewed concepts, `memory` reviewed first-party facts,
   and `projects` executable definitions. Keep `application result` as a
   receipt rather than another source of truth.
2. **One source, one identity**: record locator, capture time, content hash,
   parser/version, permission scope, and supersession. Do not merge silently.
3. **Atomic but useful notes**: extract a claim or concept that can stand alone;
   link it to a hub with a sentence that explains the relationship. Tags are
   broad filters, not a substitute for links.
4. **Retrieval ladder**: clarify the query; use full-text/keyword recall;
   optionally add semantic recall; rerank by authority, freshness, evidence
   status, and project relevance; only then assemble a bounded context pack.
5. **Context layers**: read a small summary first, then an overview, and only
   open full source text when the question requires it. Keep the source locator
   in every answer citation.
6. **Review and contradiction loop**: candidates stay unreviewed; conflicting
   claims remain visible; stale material gets a freshness state instead of an
   invisible overwrite.
7. **Query receipt**: record the question, retrieval mode, selected sources,
   citations, missing evidence, and whether a human changed the answer. This is
   the smallest useful quality/evaluation unit.
8. **Next-action loop**: expose one read-only `next`/doctor-style status that
   tells a new user whether to initialize, ingest, compile, review, query, or
   refresh. It must not auto-write canonical notes.

## Defer until a real canary proves the need

- full-machine recursive scanning or live-app database extraction;
- background watchers and automatic semantic reorganization;
- a mandatory vector database, graph database, or cloud model;
- GraphRAG-scale entity extraction and global indexes;
- automatic promotion of AI summaries into memory or project cards;
- multi-user permissions, hosted sync, or a dashboard before the first friend
  can complete one cited query from their own files.

## Portable contract

```text
ingest(source, explicit_scope)
  -> manifest + immutable raw source
compile(raw, existing_neighbors)
  -> candidate with provenance and review status
review(candidate)
  -> reviewed knowledge, memory, or rejected/contradictory state
retrieve(query, project_scope)
  -> bounded context pack + query receipt + citations
apply(context_pack, project)
  -> application result receipt
```

The contract is intentionally implementable with Markdown, links, frontmatter,
and ordinary full-text search. Embeddings, reranking, graphs, and agents can be
added behind the same interfaces later.

## Evidence limits

- GitHub star counts and README feature lists are discovery evidence, not proof
  of quality, safety, or user adoption.
- The research used public GitHub/official documentation and Jina-readable
  pages on 2026-09-30. X/Twitter and private community threads were not treated
  as evidence because no authenticated source was available.
- No source above proves that a friend's actual vault will be useful. That still
  requires a clean-room canary with a real question, citations, and a human
  usefulness judgment.
