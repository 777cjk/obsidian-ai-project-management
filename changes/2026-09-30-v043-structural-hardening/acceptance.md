# Acceptance: v0.4.3 structural hardening

## Pass conditions

- Structurally invalid manifest lists fail closed without writes.
- Structurally invalid `application_events` lists fail closed without writes.
- A result containing a Markdown `## Application History` heading survives a
  later append and the generated history heading remains unique.
- The full package verifier, pinned Agent Skills validator, fresh clone, and
  lifecycle smoke pass.

## Human gate

The friend's real Vault canary and usefulness judgment remain external and
unverified.

## Rollback

Use the existing v0.4.2 release or the installer's timestamped backup.
