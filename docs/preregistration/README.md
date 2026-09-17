# Phase 1 preregistration records

`HELM-P1-AMEND-002.json`, `HELM-P1-AMEND-003.json`, and
`HELM-P1-AMEND-004.json` are the machine-readable amendment records. Amendments
001–004 are currently `PROPOSED` and must be locked before analytic execution.
Amendment 004 adds a local-first runtime baseline while preserving the later
provider-separated OpenAI Luna and Anthropic Sonnet 5 path.

Copy [model_freeze.template.json](model_freeze.template.json) once per provider after
instrumentation-only calibration. Fill the three operational limits, record the
calibration rationale, disclose same-family review where applicable, and lock the
record before generating analytic episodes. The future adapter must call
`helm.phase1.frozen_limits` before generating analytic episodes. Do not use calibration or observed
behavior to retroactively alter the Phase 1 cohort.

The freeze lineage must contain the original preregistration followed by Amendments
001, 002, 003, and 004. Each entry is an object with `id` and canonical JSON `sha256`;
the validator checks the five files, their expected hashes, and each parent/prior
relationship before accepting a locked provider freeze. The pre-calibration readiness
gate is [PHASE_1_PRECAL_READINESS.md](../PHASE_1_PRECAL_READINESS.md).
