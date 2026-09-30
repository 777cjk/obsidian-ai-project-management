# Verification receipt: v0.4.3 structural hardening

Status: released and locally verified on 2026-09-30.

- `bash scripts/verify.sh`: package verification and 33 tests passed.
- Pinned Agent Skills validator: checksum passed and `Skill is valid!`.
- Fresh clone of `v0.4.3`: checked out `c922ca9ab254032f8863ed142e4836c1d8741500` and passed the same checks.
- Local Codex Skill install: `VERSION=0.4.3`; old `0.4.1` kept in the installer's timestamped backup.
- GitHub Release: https://github.com/777cjk/obsidian-ai-project-management/releases/tag/v0.4.3
- GitHub Actions: release push/tag checks must remain green; the friend-vault canary is still an external human gate.
