# Proposal: v0.4.3 structural hardening

## Current fact

The v0.4.2 release is published and its normal canary is green, but an
independent release audit found two malformed-input cases that were not
fail-closed: read-only status could ignore non-object manifest members, and
Markdown history reconstruction could treat a result's heading-like text as
the generated history boundary.

## Scope

- Validate manifest entry/history member types during read-only status checks.
- Validate query application-history event member types during read-only reads.
- Add a stable generated-history marker and preserve legacy receipt Markdown.
- Add focused regression coverage and publish a patch release.

## Non-goals

- Do not move or rewrite the immutable v0.4.2 tag.
- Do not add a database, semantic index, watcher, full-machine crawler, or
  friend-vault claim.
