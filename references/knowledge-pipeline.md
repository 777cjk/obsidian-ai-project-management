# Knowledge Pipeline

Use this reference when the task concerns collecting, learning from, organizing, or querying a knowledge base.

## Four Layers

```text
source -> candidate -> reviewed asset -> application result
```

### Source

Preserve the original URL, file, transcript, screenshot, code, or user quote before synthesis. Record capture date, authority, privacy, and an optional content hash. A summary is not a replacement for the source.

### Candidate

AI may extract summaries, entities, concepts, links, and claims into a candidate note. Candidates must carry `source_refs`, `provenance`, `review_status`, `evidence_status`, and contradictions. A candidate is not canonical project state.

### Reviewed asset

Promote a candidate only after a human or explicit evidence gate confirms it. Separate confirmed facts, current inferences, reusable rules, and what cannot be inferred. Add `reviewed_at`, `freshness_due`, and links to the sources.

### Application result

Record which project, decision, content item, or user interaction adopted the asset. Keep `adopted`, `result_observed`, and `decision_changed` unknown until observed.

## Retrieval

Use a bounded retrieval loop:

```text
clarify query -> keyword/full-text recall -> optional semantic recall
-> rerank by authority, freshness, evidence status, and project relevance
-> assemble only within the context budget -> answer with relative citations
```

Hybrid retrieval, graph context, query expansion, reranking, and token-aware assembly are optional upgrades. A plain Markdown vault remains useful with full-text search, links, tags, and Maps of Content.

## Maintenance

- New material enters an inbox or source directory before extraction.
- Contradictory claims stay visible with both sources.
- Stale assets are marked stale; do not silently overwrite them.
- Batch or destructive writes require a preview/diff and the host's canonical checkpoint.
- Count sources, candidates, reviewed assets, and application outcomes separately.

## Recommended Metadata

```yaml
knowledge_type: "source | candidate | concept | method | decision | experience | feedback"
source_refs: []
provenance: "extracted | inferred | ai_generated | first_party | official | community"
review_status: "unreviewed | human_reviewed | approved | rejected | contradictory"
evidence_status: "planned | partial | verified | contradictory | stale"
reviewed_at: null
freshness_due: null
applies_to: []
```
