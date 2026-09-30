# Proposal: knowledge-methods baseline

## Current fact

The portable Skill already protects source provenance, staging, review status,
and canonical Obsidian writeback. It does not yet document the common design
principles found across mature personal-knowledge and RAG projects, so a new
host can over-focus on folders, embeddings, or autonomous collection.

## Judgment to change

Treat a knowledge base as a source-backed, reviewable, linked, and usable
system. Search and vector indexes are rebuildable accelerators; they are not
the knowledge source of truth.

## Scope

- Capture and cite public method evidence from Obsidian, PARA, Zettelkasten,
  local-first vaults, and RAG/agent projects.
- Add an adoption/defer matrix to the portable Skill.
- Add a bounded retrieval ladder and a small query-evaluation receipt contract.
- Keep personal vault data, credentials, runtime collectors, vector databases,
  and platform exporters outside this public package.

## Non-goals

- No automatic scan of a friend's entire computer.
- No live WeChat database reader or decrypter.
- No mandatory vector database, graph database, watcher, or cloud model.
- No automatic promotion of AI output into canonical notes.

## Unknowns

- The user's friend's actual vault size, source mix, and preferred interface.
- Which local model or embedding runtime is available on a friend's machine.
- Real-world retrieval quality after a first clean-room canary.
