# Change Packages

Create a temporary change package only when the work is cross-module, high-impact, multi-agent, migration-related, release-related, provider-related, data-schema-related, or needs explicit rollback.

Directory:

```text
changes/YYYY-MM-DD-short-name/
├── proposal.md
├── acceptance.md
├── tasks.md
└── verify.md
```

`proposal.md` records the current fact, one judgment being changed, scope, non-goals, inputs, unknowns, and chosen approach.

`acceptance.md` records the visible artifact, pass/fail conditions, stop line, rollback, and the one human gate.

`tasks.md` gives each task an input, artifact, verification, pass condition, failure/rollback, and dependency. `[P]` means parallelizable; it does not mean complete.

`verify.md` records actual results and the receipt. A package is not a second state source: after completion, summarize the verified result through the canonical project-card checkpoint and archive or remove the temporary package according to the host workflow.

Do not create a package for a small, reversible, single-file action just to satisfy process.
