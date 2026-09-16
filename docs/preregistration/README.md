# Phase 1 preregistration records

`HELM-P1-AMEND-002.json` is the machine-readable amendment record. It is currently
`PROPOSED` and must be locked before analytic execution. The amendment freezes the
same-family AI pre-review disclosure, episode termination rules, descriptive `N = 20`
seed rationale, and required termination metadata.

Copy [model_freeze.template.json](model_freeze.template.json) once per provider after
instrumentation-only calibration. Fill the three operational limits, record the
calibration rationale, disclose same-family review where applicable, and lock the
record before generating analytic episodes. The future adapter must call
`helm.phase1.frozen_limits` before generating analytic episodes. Do not use calibration or observed
behavior to retroactively alter the Phase 1 cohort.
