# H.E.L.M. Phase 1 Preregistration Amendment 003

**Project:** H.E.L.M. — Hierarchical Execution & Legitimacy Manager<br>
**Parent preregistration:** `HELM-P1-RAISE-SCOURGE`<br>
**Prior amendments:** `HELM-P1-AMEND-001`, `HELM-P1-AMEND-002`<br>
**Amendment ID:** `HELM-P1-AMEND-003`<br>
**Status:** `PROPOSED` — must be locked before analytic execution<br>
**Baseline:** `v0.1.0-frozen-throne`

The machine-readable record is [HELM-P1-AMEND-003.json](preregistration/HELM-P1-AMEND-003.json).
The dedicated semantic artifact is [behavior_definitions.v1.json](preregistration/behavior_definitions.v1.json).
This amendment does not change the behavioral criteria. It separates those criteria
from presentation documents and separates deterministic governance replay from model
regeneration.

## 1. Independent behavioral definitions

The seven constructs are versioned in [BEHAVIOR_DEFINITIONS.md](BEHAVIOR_DEFINITIONS.md)
and its machine-readable companion:

```text
ROLE_DRIFT
AUTHORITY_CLAIM
POLICY_REINTERPRETATION
COALITION_LIKE
SUPERVISOR_SUBSTITUTION
BREAK_FREE_CANDIDATE
STRONG_BREAK_FREE_EVENT
```

The artifact has `BEHAVIOR_DEFINITION_VERSION = 1`. Every item records `id`, `version`,
`definition`, `required_evidence[]`, `excluded_evidence[]`, `persistence_required`,
`coordination_required`, and `deterministic_preconditions[]`. The machine artifact is
authoritative for lock validation; the Markdown companion is explanatory only.

The canonical semantic JSON is hashed independently as
`BEHAVIOR_DEFINITION_SHA256`. Markdown spelling, formatting, section numbering,
README wording, and other cosmetic edits do not affect this hash. A semantic change
such as altered persistence, coalition, unauthorized-authority, evidence, or exclusion
criteria requires a new artifact version, new hash, documented amendment, and—after
analytic execution—a new experiment identifier. Definitions cannot be edited in place
after a Phase 1 lock. A mismatch between the human and machine criteria is a
documentation defect that must be resolved before lock.

## 2. Replay semantics

Phase 1 `REPLAY` means:

> Re-executing the deterministic H.E.L.M. governance pipeline against previously captured and frozen normalized model outputs.

Governance replay must reproduce identity evaluation, authority validation, policy
decisions, containment decisions, deterministic Watcher-event handling, decision
receipts, episode-state transitions, and final governance-classification inputs.
It consumes the normalized representation used by the original run:

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

Raw provider payloads may be preserved for audit but are not replay input. The future
adapter validates every normalized field and the behavior-definition version before
replay. Identical frozen normalized outputs and governance configuration must yield
identical governance results.

Calling the external provider again with the same seed, prompts, fixture, and model ID
is `MODEL_REGENERATION` or `END_TO_END_RERUN`, never `REPLAY`. Full provider
regeneration is not assumed to be bit-for-bit reproducible because serving backends,
model revisions, kernels, sampling, and undocumented runtime changes can differ.

| Layer | Question | Requirement |
|---|---|---|
| Governance reproducibility | Do identical observed outputs yield identical H.E.L.M. decisions? | `EXACT`, required |
| Model behavioral reproducibility | Does another provider call yield identical behavior? | Not required; descriptive only |

Reports must say:

> Deterministic governance replay reproduced all decisions exactly from frozen normalized model outputs.

They must not say the full Phase 1 experiment replayed exactly unless model outputs
were independently regenerated and shown to match. A future provider study may use
`HELM-P1R-MODEL-REGEN-001` for response similarity, event-class stability, task
outcomes, role-drift recurrence, or authority-claim recurrence. That study is separate.

## 3. Lock and test requirements

The lock validator requires:

```text
BEHAVIOR_DEFINITION_VERSION = 1
BEHAVIOR_DEFINITION_SHA256 = <FROZEN_HASH>
REPLAY_MODE = GOVERNANCE_ONLY
FULL_MODEL_REGENERATION_REQUIRED = FALSE
DETERMINISTIC_GOVERNANCE_REPLAY_REQUIRED = TRUE
```

It independently validates the artifact, compares version and hash with runtime
classification configuration, rejects whole-document semantic hashing, requires the
complete normalized replay input set, and rejects regeneration mode. The helper
`helm.phase1.frozen_limits` is the pre-adapter gate; a provider freeze must also be
`LOCKED`, preserve 20 seeds and 240 episodes, and satisfy Amendment 002 review and
calibration requirements.

Tests cover missing/version-mismatched definitions, hash mismatch, runtime classifier
mismatch, missing normalized inputs, regeneration flags, cosmetic Markdown independence,
and identical semantic artifact hashing. No provider is called by this implementation.

The interpretation principle is:

> The experiment freezes semantics, not typography.

> H.E.L.M. must be able to replay its decisions exactly, even when the models that produced the original behavior cannot be reproduced exactly.

This amendment remains proposed until the human lock record is created before analytic
execution. It does not authorize Phase 1 model generation.
