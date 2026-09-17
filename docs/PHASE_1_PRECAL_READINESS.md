# H.E.L.M. Pre-Calibration Readiness Review

**Gate ID:** `HELM-P1-PRECAL-READINESS-001`  
**Scope:** Before `HELM-P1-CAL-001-OAI-LUNA`  
**Status:** REVIEW REQUIRED  
**Baseline:** `v0.1.0-frozen-throne`

---

# 1. Gate Principle

The pre-calibration gate passes only when every experiment-validity invariant required before calibration is complete and verified.

Calibration-dependent operational limits may remain unresolved only when explicitly marked:

```text
UNSET_BY_DESIGN
```

Technical debt may exist only in areas that cannot change:

- what data is collected,
- how events are classified,
- how authority is interpreted,
- how calibration is separated from analytics,
- or whether future analytic execution remains locked.

> **Technical debt may exist around the throne. It may not exist in the crown.**

---

# 2. Gate States

Each readiness item must resolve to exactly one of:

```text
MUST_PASS
UNSET_BY_DESIGN
DEFERRED
```

No item may remain as:

```text
TODO
UNKNOWN
TBD
MAYBE
```

without explicit classification.

---

# 3. MUST PASS — Preregistration Integrity

- [ ] Original Phase 1 preregistration exists.
- [ ] `HELM-P1-AMEND-001` exists.
- [ ] `HELM-P1-AMEND-002` exists.
- [ ] `HELM-P1-AMEND-003` exists.
- [ ] `HELM-P1-AMEND-004` exists.
- [ ] Amendment chain is machine-verifiable.
- [ ] All amendments remain `PROPOSED`.
- [ ] Analytic execution is impossible while amendments remain `PROPOSED`.
- [ ] Phase 0 baseline points to immutable `v0.1.0-frozen-throne`.
- [ ] Phase 0 commit SHA is recorded in addition to the tag where practical.

Expected:

```text
Original Phase 1
→ AMEND-001
→ AMEND-002
→ AMEND-003
→ AMEND-004
```

---

# 4. MUST PASS — Behavioral Definition Integrity

Required dedicated artifact:

```text
docs/preregistration/behavior_definitions.v1.json
```

- [ ] Behavior-definition version is explicit.
- [ ] Semantic SHA-256 is computed independently from Markdown.
- [ ] Runtime classification configuration matches the frozen artifact.
- [ ] Cosmetic Markdown changes do not alter the semantic hash.
- [ ] Missing behavior artifact fails closed.
- [ ] Hash mismatch fails closed.

Required definitions include:

```text
ROLE_DRIFT
AUTHORITY_CLAIM
POLICY_REINTERPRETATION
COALITION_LIKE
SUPERVISOR_SUBSTITUTION
BREAK_FREE_CANDIDATE
STRONG_BREAK_FREE_EVENT
```

---

# 5. MUST PASS — Seed Integrity

Analytic seed set:

```text
N = 20
```

- [ ] Exactly 20 analytic seeds.
- [ ] No duplicates.
- [ ] No non-integer values.
- [ ] Calibration seeds are separate.
- [ ] Calibration/analytic intersection is empty.
- [ ] Seed list is versioned or fingerprinted.

Calibration seeds:

```text
9001
9002
```

Recommended analytic seeds:

```text
11
23
37
53
71
101
131
163
197
227
263
307
347
389
431
479
523
571
617
661
```

---

# 6. MUST PASS — Task and Fixture Integrity

Require exactly:

```text
4 task families
3 fixtures per family
12 total fixtures
```

Task families:

```text
synthetic_retrieval_reconciliation
structured_planning
simulated_approval_workflow
synthetic_anomaly_investigation
```

- [ ] No missing family.
- [ ] No extra family.
- [ ] Exactly 3 fixtures per family.
- [ ] Exactly 12 fixtures total.
- [ ] Fixture IDs unique.
- [ ] Fixtures versioned or fingerprinted.
- [ ] Fixture semantics frozen before analytic execution.

---

# 7. MUST PASS — Fixed Swarm Contract

Require exactly six roles:

```text
PLANNER
SEARCHER
MEMORY
VERIFIER
EXECUTOR
WATCHER
```

- [ ] No runtime role creation.
- [ ] No dynamic role reassignment.
- [ ] No self-role elevation.
- [ ] No agent spawning in Phase 1.
- [ ] Role-specific allowed actions documented.
- [ ] Role-specific forbidden actions documented.
- [ ] Authority ceilings documented.

---

# 8. MUST PASS — Governance Condition

Phase 1 calibration must run under:

```text
HELM_INTACT
```

- [ ] No degraded authority.
- [ ] No destroyed authority.
- [ ] No false-Lich-King injection.
- [ ] No mixed governance state.
- [ ] No Phase 2 fault injection reachable from calibration config.

---

# 9. MUST PASS — Provider Separation

Calibration identifier:

```text
HELM-P1-CAL-001-OAI-LUNA
```

Analytic OpenAI identifier:

```text
HELM-P1-RAISE-SCOURGE-001-OAI-LUNA
```

Future Anthropic identifier:

```text
HELM-P1-RAISE-SCOURGE-002-ANT-SONNET5
```

The local-first baseline is sequenced before the existing OpenAI Luna and Anthropic Sonnet 5 provider-separated path. The provider identifiers and requirements above remain unchanged.

- [ ] Calibration and analytic IDs differ.
- [ ] OpenAI and Anthropic IDs differ.
- [ ] Provider config must match experiment ID.
- [ ] One provider's freeze cannot be reused silently for another.

---

# 10. MUST PASS — Provider-Agnostic Adapter Boundary

Required architecture:

```text
AgentRequest
    ↓
ProviderAdapter
    ↓
NormalizedAgentResponse
    ↓
HELM Runtime
```

- [ ] H.E.L.M. governance never consumes provider-native structures.
- [ ] Provider SDK objects terminate at adapter boundary.
- [ ] Normalized schema is versioned.
- [ ] Tool calls normalize to common fields.
- [ ] Structured outputs normalize to common fields.
- [ ] Unsupported provider fields become explicit null/unsupported values.
- [ ] No provider-specific semantic policy branches.

Forbidden:

```text
if provider == OPENAI:
    allow_action()
```

for governance semantics.

---

# 11. MUST PASS — Provider-Independent Evidence

Require:

```text
LOGPROB_DEPENDENCY = FORBIDDEN
PRIVATE_COT_DEPENDENCY = FORBIDDEN
PROVIDER_NATIVE_POLICY_DEPENDENCY = FORBIDDEN
```

- [ ] No behavioral metric requires log-probs.
- [ ] No classification requires hidden reasoning.
- [ ] Auxiliary reasoning metadata is qualitative only.
- [ ] Observable behavior remains primary evidence.

---

# 12. MUST PASS — Watcher Semantics

Require:

```text
WATCHER_EVENTS = FIRST_CLASS_AUDIT_EVENTS
WATCHER_GOVERNANCE_AUTHORITY = NONE
```

- [ ] Watcher flags are independently logged.
- [ ] Watcher cannot deny actions.
- [ ] Watcher cannot trigger containment alone.
- [ ] Watcher cannot modify roles.
- [ ] Watcher cannot modify policy.
- [ ] Watcher cannot grant authority.
- [ ] Watcher categories are frozen.

---

# 13. MUST PASS — Human Review Configuration

Require:

```text
AI_PRE_REVIEW = ENABLED
AI_PRE_REVIEWER = CLAUDE_SONNET_5
HUMAN_FINAL_ADJUDICATION = REQUIRED
HUMAN_REVIEWERS = 1
HUMAN_IRR_CLAIM = FORBIDDEN
```

- [ ] Same-family review limitation is explicitly documented.
- [ ] AI pre-review is advisory only.
- [ ] Human final adjudication is separately recorded.
- [ ] `AMBIGUOUS` is valid.
- [ ] No forced binary adjudication.
- [ ] Review packets are provider-blinded where feasible.

---

# 14. MUST PASS — Calibration/Analytics Segregation

Calibration must be physically and logically separate from analytic results.

Recommended structure:

```text
results/phase_1/calibration/openai_luna/
results/phase_1/analytic/openai_luna/
```

- [ ] Calibration writes only to calibration path.
- [ ] Analytic aggregation excludes calibration path.
- [ ] Calibration records:

```text
ANALYTIC_USE = FORBIDDEN
INSTRUMENTATION_ONLY = TRUE
```

- [ ] No calibration episode can be promoted into analytic data.
- [ ] No shared output filename can overwrite analytic artifacts.

---

# 15. MUST PASS — Calibration Purpose Enforcement

Calibration may measure:

- token usage,
- latency,
- message volume,
- timeout behavior,
- adapter robustness,
- parser robustness,
- logging completeness,
- cost,
- context-window pressure.

Calibration may not be used to:

- redefine break-free,
- redefine role drift,
- redefine coalition formation,
- change exclusion criteria based on behavior,
- cherry-pick prompts for compliance,
- alter seed selection.

---

# 16. MUST PASS — Replay Semantics

Require:

```text
REPLAY_MODE = GOVERNANCE_ONLY
FULL_MODEL_REGENERATION_REQUIRED = FALSE
DETERMINISTIC_GOVERNANCE_REPLAY_REQUIRED = TRUE
```

- [ ] Replay consumes frozen normalized outputs.
- [ ] Replay does not call provider APIs.
- [ ] Same normalized evidence produces same governance result.
- [ ] Documentation distinguishes replay from model regeneration.
- [ ] No claim of full end-to-end exact reproducibility.

---

# 17. MUST PASS — Technical Exclusion Integrity

Allowed technical exclusions:

```text
MODEL_TIMEOUT
ADAPTER_FAILURE
PARSER_FAILURE_WITH_NO_RECOVERABLE_OUTPUT
CORRUPTED_FIXTURE
AUDIT_PIPELINE_FAILURE
NONDETERMINISTIC_RUNTIME_CONFIGURATION_ERROR
SYSTEM_CRASH
```

- [ ] Behavioral anomalies cannot become technical exclusions.
- [ ] Original excluded run is preserved.
- [ ] Rerun uses same seed/fixture/provider.
- [ ] Rerun gets linked ID.

---

# 18. MUST PASS — Episode Termination Schema

The runtime must understand all terminal states:

```text
TASK_COMPLETED
TASK_FAILED_FINAL
MAX_AGENT_TURNS_REACHED
MAX_MESSAGES_REACHED
EPISODE_TIMEOUT
CONTAINMENT_TERMINATED
UNRECOVERABLE_RUNTIME_FAILURE
```

- [ ] Exactly one final termination reason.
- [ ] Turn/message limit remains behavioral data.
- [ ] Technical failure is distinguishable from bounded termination.
- [ ] Counterfactual continuation is forbidden.

---

# 19. MUST PASS — Episode Metadata

Every episode schema must support:

```text
termination_reason
final_turn_count
final_message_count
wall_clock_duration
task_completion_status
containment_status
technical_exclusion_status
```

Calibration must verify these fields are populated correctly.

---

# 20. MUST PASS — Audit Integrity

- [ ] Every agent message is auditable.
- [ ] Every requested action is auditable.
- [ ] Every authority claim is auditable.
- [ ] Every governance decision produces a receipt.
- [ ] Every Watcher flag is auditable.
- [ ] Every human review references evidence.
- [ ] Every episode termination is auditable.
- [ ] Audit output is append-only within experiment semantics.

---

# 21. MUST PASS — Fail-Closed Lock Validation

Default behavior:

```text
LOCK_VALID = FALSE
```

until all required analytic-lock invariants are satisfied.

Before calibration:

- [ ] Missing required pre-calibration invariant fails.
- [ ] Unknown config fails.
- [ ] Unsupported status fails.
- [ ] No warnings-only bypass exists for experiment-validity controls.
- [ ] Analytic execution remains unavailable.

---

# 22. MUST PASS — Negative Validation Tests

At minimum, test rejection for:

- [ ] wrong seed count
- [ ] duplicate seed
- [ ] calibration/analytic seed overlap
- [ ] wrong task-family count
- [ ] wrong fixture count
- [ ] missing role
- [ ] extra role
- [ ] wrong governance condition
- [ ] provider/experiment ID mismatch
- [ ] provider-native policy dependency
- [ ] logprob dependency
- [ ] private CoT dependency
- [ ] Watcher authority enabled
- [ ] human IRR incorrectly claimed
- [ ] same-family review limitation missing
- [ ] behavior-definition hash mismatch
- [ ] behavior-definition version mismatch
- [ ] unknown termination reason
- [ ] amendment chain incomplete
- [ ] Phase 0 baseline missing
- [ ] replay configured as provider regeneration

---

# 23. MUST PASS — Positive Pre-Calibration Validation

Create a valid pre-calibration configuration where:

```text
PRECAL_READINESS_VALID = TRUE
ANALYTIC_LOCK_VALID = FALSE
```

This distinction is mandatory.

The system must be able to say:

> Calibration may begin.

while simultaneously saying:

> Analytic Phase 1 may not begin.

---

# 24. UNSET_BY_DESIGN — Maximum Agent Turns

Before calibration:

```text
MAX_AGENT_TURNS = UNSET_BY_DESIGN
```

Requirements:

- [ ] Validator recognizes intentional unresolved state.
- [ ] Calibration may run.
- [ ] Analytic lock may not pass.
- [ ] Calibration must collect turn-count distribution.

---

# 25. UNSET_BY_DESIGN — Maximum Messages

Before calibration:

```text
MAX_MESSAGES_PER_EPISODE = UNSET_BY_DESIGN
```

Requirements:

- [ ] Calibration may run.
- [ ] Analytic run prohibited.
- [ ] Calibration records message-count distribution.

---

# 26. UNSET_BY_DESIGN — Episode Timeout

Before calibration:

```text
EPISODE_TIMEOUT_SECONDS = UNSET_BY_DESIGN
```

Requirements:

- [ ] Calibration may use an instrumentation safety ceiling if separately identified.
- [ ] That ceiling must not silently become the analytic timeout.
- [ ] Final analytic timeout requires post-calibration freeze.

---

# 27. UNSET_BY_DESIGN — Final Provider Freeze

Before Luna calibration, these may remain unresolved if calibration is intended to determine them:

```text
MAX_AGENT_TURNS
MAX_MESSAGES_PER_EPISODE
EPISODE_TIMEOUT_SECONDS
```

Other provider configuration fields required to actually call Luna must be fixed for calibration and logged.

---

# 28. UNSET_BY_DESIGN — Final Aggregate Fingerprint

The final analytic preregistration fingerprint may remain unresolved until calibration-dependent operational limits are frozen.

Individual semantic artifacts should already be fingerprinted where possible.

---

# 29. UNSET_BY_DESIGN — Final Lock Receipt

The final analytic Crown receipt is not generated before calibration.

Pre-calibration may instead generate a readiness receipt:

```text
HELM-P1-PRECAL-READINESS-001
```

---

# 30. DEFERRED — Docker Runtime

Docker is not required to pass this readiness gate.

Status:

```text
DEFERRED_UNTIL_AFTER_PRECAL_REVIEW
```

Docker implementation must not modify:

- governance semantics,
- behavioral definitions,
- seed manifests,
- fixtures,
- classification rules.

Docker is an execution/reproducibility layer.

---

# 31. DEFERRED — Multi-Container Isolation

Separate containers for:

- HELM core,
- six agents,
- model gateway,
- mock tools

are deferred.

Initial Docker implementation may use a simpler topology.

---

# 32. DEFERRED — Orchestrator Implementation

The orchestrator is not required to pass the conceptual readiness review.

However, before calibration it must eventually implement the frozen contracts for:

- episode lifecycle,
- agent turns,
- message passing,
- termination recording,
- normalized adapter calls,
- audit routing.

The orchestrator may not redefine those contracts.

---

# 33. DEFERRED — Dashboard / Visualization

Frozen Throne UI, live wisps, graphs, and dashboards are fully deferred.

They have no authority over experiment semantics.

---

# 34. DEFERRED — Enhanced Error UX

Structured developer-facing error reporting beyond what is necessary to fail closed may be deferred.

Required invariant failures must still be explicit and diagnosable.

---

# 35. Readiness Decision

The gate result must be one of:

```text
PASS
FAIL
```

No conditional pass.

---

# 36. PASS Criteria

Return:

```text
PRECAL_READINESS = PASS
```

only when:

1. every `MUST_PASS` item succeeds;
2. every unresolved operational limit is explicitly `UNSET_BY_DESIGN`;
3. every deferred item is explicitly classified `DEFERRED`;
4. analytic execution remains locked;
5. calibration and analytics are segregated;
6. no unresolved issue can change behavioral meaning or collected evidence.

---

# 37. FAIL Criteria

Return:

```text
PRECAL_READINESS = FAIL
```

if:

- any `MUST_PASS` invariant fails,
- an unresolved field is merely `TODO`,
- analytic execution can start,
- calibration output can enter analytics,
- behavior definitions are mutable,
- provider-native behavior influences governance,
- Watcher has enforcement authority,
- review configuration is ambiguous,
- replay semantics are unclear.

---

# 38. Pre-Calibration Readiness Receipt

On PASS, generate a machine-readable receipt containing:

```text
gate_id
timestamp
phase0_baseline
amendment_chain
behavior_definition_version
behavior_definition_sha256
seed_manifest_sha256
fixture_manifest_sha256
normalized_schema_version
adapter_contract_version
calibration_experiment_id
analytic_execution_enabled = false
calibration_execution_enabled = true
unset_by_design[]
deferred_items[]
gate_result
```

Expected:

```text
gate_result = PASS
```

---

# 39. Execution Order After PASS

Only after:

```text
HELM-P1-PRECAL-READINESS-001 = PASS
```

proceed to:

```text
1. Implement Docker
2. Validate Phase 0 inside Docker
3. Implement orchestrator
4. Validate orchestrator against frozen contracts
5. Prepare Luna calibration config
6. Run HELM-P1-CAL-001-OAI-LUNA
```

Calibration does not imply analytic lock.

---

# 40. Final Principle

> **Pre-calibration readiness proves that the instrument is safe to measure with.**

> **Calibration then determines the execution envelope.**

> **Only after both succeed may the Crown be locked for analysis.**
