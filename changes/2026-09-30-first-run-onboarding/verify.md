# Verification receipt: first-run onboarding

Status: v0.4.1 published and verified; friend-run Vault canary remains pending.

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

- Release commit: `c57ebc83b2f62dc60b8100fa9867d802d936d833`.
- GitHub Actions Verify Skill run `36679720070` passed for that exact commit:
  https://github.com/777cjk/obsidian-ai-project-management/actions/runs/36679720070
- Pushed annotated tag `v0.4.1` resolves to the same commit.
- Published GitHub Release:
  https://github.com/777cjk/obsidian-ai-project-management/releases/tag/v0.4.1
- A fresh shallow clone of the tag passed all 19 tests and the official
  validator; its isolated install passed the same checks and contained no
  `.git` metadata.

## External user gate

The clean-room synthetic canary is engineering evidence only. The friend-run
canary and human usefulness remain unknown until a real person observes them.
