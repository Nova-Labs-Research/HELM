# Phase 1 replay semantics

`REPLAY` in Phase 1 means **governance-only replay**: re-executing the deterministic
H.E.L.M. pipeline against previously captured and frozen normalized model outputs.
It must reproduce identity evaluation, authority validation, policy decisions,
containment decisions, deterministic Watcher-event handling, receipts, episode-state
transitions, and final governance classification inputs.

The replay input is the normalized representation used by the original run:

```text
normalized_agent_outputs
normalized_messages
requested_actions
authority_claims
tool_intents
fixture_state
policy_state
identity_state
governance_configuration
behavior_definition_version
```

Raw provider payloads may remain in the audit archive, but they are not replay input.
The future adapter must validate all normalized fields and the behavior-definition
version before replay. Identical normalized outputs plus identical frozen governance
configuration must produce identical governance results.

Calling a provider again—even with the same seed, prompts, fixture, and model ID—is
`MODEL_REGENERATION` or `END_TO_END_RERUN`, never `REPLAY`. Bit-for-bit provider
regeneration is not assumed because backend revisions, serving infrastructure,
nondeterministic kernels, sampling behavior, and undocumented runtime changes can
change outputs.

| Layer | Question | Lock requirement |
|---|---|---|
| Governance reproducibility | Do identical observed outputs yield identical H.E.L.M. decisions? | `EXACT`, required |
| Model behavioral reproducibility | Does calling the provider again yield identical behavior? | Not required; descriptive future study only |

Preferred report language:

> Deterministic governance replay reproduced all decisions exactly from frozen normalized model outputs.

Avoid claiming that the full Phase 1 experiment replayed exactly unless provider
outputs were independently regenerated and shown to match. A future study may use
`HELM-P1R-MODEL-REGEN-001` to measure same-seed response similarity, event stability,
task outcomes, role-drift recurrence, or authority-claim recurrence. That study is
separate from the governance replay lock.
