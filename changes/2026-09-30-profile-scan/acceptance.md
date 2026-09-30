# Acceptance: zero-setup profile scan

## Visible artifact

An isolated fixture can run:

```text
plan -> collect --confirm-scope -> review-profile --decision approve --confirm -> context
```

and receive a bounded, cited context pack without changing any source file.

## Pass conditions

- `plan` discovers common roots and writes only a private `scan-plan.json`.
- The plan reports selected counts and skipped sensitive/cache/unsupported
  files; `collect` requires explicit scope confirmation.
- DOCX/PPTX/XLSX visible text can enter the existing raw/candidate pipeline.
- Profile and project-map candidates remain `unreviewed` until the explicit
  profile approval gate.
- Approval writes stable private Markdown/JSON context assets with source refs,
  unknowns, and a bounded read-only `context` output.
- Full tests, syntax checks, package verification, and the official validator
  pass.

## Stop line

Stop after local fixture and fresh installed-copy verification. Do not claim
friend usefulness or add cloud connectors/OCR/canonical writeback.

## Human gate

A friend must inspect the scope preview and approve the generated profile on a
clean machine before this becomes a product-usefulness claim.

## Rollback

Restore the prior skill directory/release and remove only the private staging
workspace. Source files and canonical Obsidian notes are never modified by the
scanner.
