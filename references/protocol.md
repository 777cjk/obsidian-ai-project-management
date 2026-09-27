# Portable Protocol

## Context Package

Use this structure when handing a project to an AI agent:

```yaml
context_version: 2
project_card: "/path/to/vault/projects/example.md"
owner_project: "Example project"
parent_project: null
supporting_projects: []
intent: "What the user wants now"
primary_view: "producer | developer | entrepreneur"
current_stage: "idea | prepared | engineering | human | user | commercial"
evidence_level: "planned | partial | verified | failed"
single_judgment: "What should be more certain by the end of this turn"
requested_artifact: "One visible file, change, test, or report"
artifact_path: "/path/to/output"
acceptance:
  pass: "Observable pass condition"
  fail: "Observable failure condition"
  stop: "Condition that stops expansion"
human_action: "One irreplaceable human action, or none"
writeback: "none | candidate | checkpoint_preview"
```

## Result Receipt

Use `unknown` when a field has not been observed. Do not infer user adoption.

```yaml
receipt_version: 1
adopted: "yes | no | unknown"
action_started: "yes | no | unknown"
action_completed: "yes | no | unknown"
result_observed: "yes | no | unknown"
decision_changed: "yes | no | unknown"
evidence_ref: []
failure_reason: none
next_route: "continue | adjust | stop | wait_for_human | reconverge"
```

## Agent Output Contract

End a project turn with:

1. current project and evidence level;
2. the single judgment;
3. artifact path and what changed;
4. verification evidence;
5. the one human action;
6. pass, fail, and stop conditions;
7. the result receipt;
8. the next route.

## Card Drift

If current evidence contradicts the card, report the contradiction. Prefer the source with recent, reproducible result evidence, and update the card only through the host's canonical writeback path.
