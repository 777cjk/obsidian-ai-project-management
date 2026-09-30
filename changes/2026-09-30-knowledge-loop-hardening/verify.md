# Verification receipt: knowledge loop hardening

Status: implementation complete; local verification passed on 2026-09-30.

Expected evidence:

- focused `test_knowledge_loop.py` pass;
- `scripts/verify.sh` pass;
- `python3 -m py_compile scripts/knowledge_loop.py` pass;
- `git diff --check` pass;
- a clean friend-vault canary remains an external human gate.

Observed receipt:

- `bash scripts/verify.sh`: passed package verification and 31 tests.
- `python3 -m py_compile scripts/knowledge_loop.py`: passed.
- `git diff --check`: passed.
- Focused `python3 -m unittest tests.test_knowledge_loop -v`: 20 tests passed.
- The suite covers read-only `status`/`next`, legacy receipts, all pending
  receipts, malformed manifests, stale sources, bounded retrieval, and
  same-file label changes.

The release must also confirm that `status` and `next` are read-only when the
workspace is missing, and that all pending query receipts are surfaced.
