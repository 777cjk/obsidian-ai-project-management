# Source Ingest Adapter

Use this reference when a project needs to collect local files, Feishu
documents, Baidu Netdisk items, or parsed document text for review in Obsidian.

## Reusable stack

```text
official connector (Feishu / Baidu) or local allowlist
        -> Source Manifest
        -> hash + duplicate + version + permission status
        -> optional parser (MarkItDown / LiteParse / Docling / OCRmyPDF)
        -> candidate Markdown
        -> human/evidence review
        -> reviewed knowledge asset
        -> project application and result receipt
```

The reference implementation is the sibling adapter at
`../obsidian-knowledge-ingest/` when both repositories are checked out. Its
`manifest_scan.py` is read-only with respect to source files and the Obsidian
vault. It emits staging candidates and a JSON manifest; it does not approve
knowledge, update a project card, or upload data.

For document content, use its `scripts/parser_adapter.py` contract. The
adapter returns one versioned result shape with source hash, parser identity,
text, outline, assets, page references, and errors. The built-in UTF-8 parser
has no dependency; MarkItDown and LiteParse are optional lazy backends, while
Docling remains an explicit heavier backend. Read
`obsidian-knowledge-ingest/references/parser-adapter-schema.md` before adding a
new parser.

## Connector boundaries

- Feishu: prefer the official `larksuite/lark-openapi-mcp` for a small read-only
  integration, or `larksuite/oapi-sdk-python` when a host needs typed API calls,
  pagination, retries, and explicit token handling.
- Baidu Netdisk: prefer the official `baidu-netdisk/mcp` for the supported list,
  metadata, search, and summary operations. Verify per-file content access
  before claiming that a complete source was retrieved.
- Local files: scan an explicit allowlist. A recursive scan is not permission
  to upload or parse every file on the machine.

## Promotion gate

Before a candidate becomes a reviewed asset, require the source locator,
capture time, content hash when available, privacy scope, parser/version, and
an evidence status. Keep source, candidate, reviewed asset, and application
result in separate Markdown records. Indexes, vectors, and graph databases
remain rebuildable accelerators; Obsidian Markdown remains the canonical store.

## Validation order

1. Run the local scanner against one fixture directory.
2. Connect one Feishu document with a read-only OAuth scope.
3. Connect one Baidu Netdisk folder with the user's granted scope.
4. Parse a small fixture set and preserve page/asset references.
5. Promote one candidate through review and record the result receipt.

Do not add a watcher, semantic index, or automatic project writeback until the
previous stage has a visible, repeatable result.
