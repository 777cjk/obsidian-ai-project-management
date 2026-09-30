# Acceptance: first-run onboarding

## Visible artifact

A versioned Quick Start describes GitHub clone through host installation and a
complete local lifecycle. `ingest` directly prints unreviewed candidate paths.

## Pass conditions

- README and DEPLOYMENT agree on Python 3.10+ and third-party dependency
  requirements.
- A new user can clone a release tag, verify it, install the Skill, and learn
  that a fresh host session is needed.
- The ingest JSON lists new or still-unreviewed candidate paths.
- Test coverage asserts those paths, all package tests pass, and the official
  Agent Skills validator passes.
- Synthetic canary results keep `human_usefulness: unknown`.

## Stop line

Stop after local/release-package onboarding is verified. Do not automate
full-computer discovery or canonical note writeback.

## Human gate

A friend must still run the package on their own selected Vault copy and judge
whether the results are useful.

## Rollback

Restore the previous version and revert the CLI response field and onboarding
documentation. No canonical vault data is modified by this package change.
