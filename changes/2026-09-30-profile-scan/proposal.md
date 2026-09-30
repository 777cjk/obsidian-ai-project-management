# Proposal: zero-setup profile scan

## Current fact

v0.4.3 completes an explicit source-to-knowledge loop, but a friend must know
which folders to select and the package does not create a durable personal
background or project context for later Codex work.

## Judgment to change

Make the first useful entry point a bounded local profile scan: discover common
document roots, show a private scope preview, collect useful text/Office
documents after one scope confirmation, and produce reviewable background and
project-map candidates.

## Scope

- Add `scripts/profile_scan.py` with `plan`, `collect`, `review-profile`,
  `context`, and read-only `status` commands.
- Discover Desktop/Documents/Downloads/Pictures/Obsidian/AI workspace roots
  plus explicitly supplied roots, while excluding secret, browser, WeChat,
  cache, and system paths.
- Add dependency-free visible-text extraction for DOCX/PPTX/XLSX sources.
- Generate source-cited, unreviewed personal-background and project-map
  candidates; approve them into a stable `knowledge/profile-context.md`,
  `knowledge/project-map.md`, and JSON metadata pack.
- Keep the existing source/candidate/review/query/receipt loop intact.

## Non-goals

- No password, Keychain, browser profile, raw WeChat database, or system-data
  extraction.
- No PDF/image OCR, cloud upload, watcher, semantic index, or canonical Vault
  writeback in this slice.
- No claim that a friend has completed a real-world canary.

## Unknowns

- Whether the default roots contain enough useful material on a clean friend
  machine.
- Whether the generated profile signals are sufficiently helpful for a real
  Codex project turn.
