# Host Adaptation

The public skill is intentionally independent of one person's vault layout.

## Required configuration

Configure these values in the host integration, not inside the skill:

- `vault_root`: the Obsidian vault root;
- `project_cards_dir`: the directory containing canonical project cards;
- `project_card_selector`: the frontmatter marker, normally `project_card: true`;
- `evidence_roots`: optional directories for current results and handoff files.

## Optional integrations

- A natural-language router can map an informal request to `owner_project`, `parent_project`, and `supporting_projects`.
- A deterministic checkpoint command can validate exact card selectors, compare file hashes, write the card and append-only evolution log atomically, and emit a checksum receipt.
- A derived view or launcher may run after a successful checkpoint. It must not become a second state source.

If an optional integration is absent, the skill still works by reading Markdown and returning a proposed checkpoint payload.

## Privacy checklist before publishing

Search the package for:

- home directories and personal names;
- private project names and customer data;
- API keys, cookies, tokens, emails, phone numbers, and private URLs;
- local ports, tunnel addresses, account identifiers, and machine-specific commands;
- copied chat transcripts or internal system prompts.

Replace them with placeholders or remove them. Keep personal defaults in a local, ignored adapter file.

## Installing for a friend

Copy the skill folder into the compatible agent's skills directory, then configure the friend's vault root and project-card directory. Start with one sample project card and one current evidence file. Run one real project turn before adding any router or automatic writeback.
