# Verification receipt: first-run onboarding

Status: local source and installed-copy verification complete; GitHub publication pending.

## Local verification

- Source checkout: `scripts/verify.sh` passed, including 19 tests and the
  pinned Agent Skills validator (`quick_validate.py`, SHA-256
  `67cf5703402013936c8fb75ad6a1afecd8841d45cc5e606b634eb05825fde365`).
- `python3 -m py_compile scripts/knowledge_loop.py` passed.
- `git diff --check` passed.
- `scripts/install.sh` installed `0.4.1` into an isolated temporary directory;
  the installed copy passed all 19 tests and the validator, and contained no
  `.git` metadata.
- Independent smoke test passed the exact `candidates/<hash>.md` path from
  `ingest` to `review` and received `approved`.

## Remote publication

Pending: record the release commit, successful GitHub Actions run, pushed
`v0.4.1` tag, and GitHub Release URL after they are verified.

## External user gate

The clean-room synthetic canary is engineering evidence only. The friend-run
canary and human usefulness remain unknown until a real person observes them.
