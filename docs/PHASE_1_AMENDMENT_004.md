# H.E.L.M. Phase 1 Preregistration Amendment 004

**Project:** H.E.L.M. — Hierarchical Execution & Legitimacy Manager  
**Parent Preregistration:** `HELM-P1-RAISE-SCOURGE`  
**Prior Amendments:** `HELM-P1-AMEND-001`, `HELM-P1-AMEND-002`, `HELM-P1-AMEND-003`  
**Amendment ID:** `HELM-P1-AMEND-004`  
**Title:** Local-First Runtime Sequencing  
**Status:** PROPOSED — MUST BE LOCKED BEFORE ANALYTIC EXECUTION  
**Baseline:** `v0.1.0-frozen-throne`

The machine-readable record is [HELM-P1-AMEND-004.json](preregistration/HELM-P1-AMEND-004.json).
This amendment extends the existing preregistration lineage without changing the
Phase 0 governance baseline, behavioral definitions, or analytic meaning.

---

# 1. Amendment Purpose

Amendment 004 formally adds a local-first runtime baseline and sequences it before
the already-planned cloud/API provider path.

The existing Phase 1 design established provider-separated cloud/API execution. Since
that design was created, a local runtime path has been implemented, unit-tested,
live-smoke-tested, independently reviewed, and version-controlled. This amendment
adds that local-first baseline to be validated and exercised before the previously
planned external-provider runs.

The local-first sequence supports:

- instrument reproducibility,
- local execution control,
- runtime inspectability,
- and reduced external dependency during initial validation.

The existing OpenAI Luna and Anthropic Sonnet 5 provider-separated plan from
Amendments 001–002 remains intact and is deferred to a subsequent execution phase
rather than replaced by the local-first baseline.

This is runtime and provider-sequencing infrastructure. It does not introduce new
experimental semantics.

---

# 2. Lineage

The amendment extends the existing chain:

```text
HELM-P1-RAISE-SCOURGE
→ HELM-P1-AMEND-001
→ HELM-P1-AMEND-002
→ HELM-P1-AMEND-003
→ HELM-P1-AMEND-004
```

The parent preregistration remains `HELM-P1-RAISE-SCOURGE`. The prior amendments are
`HELM-P1-AMEND-001`, `HELM-P1-AMEND-002`, and `HELM-P1-AMEND-003`.

Amendments 001–003 retain their committed content and canonical hashes. Amendment 004
is `PROPOSED` and must be locked before analytic execution.

---

# 3. Local-First Execution Sequence

The additive execution sequence is:

```text
LOCAL GRANITE BASELINE
        ↓
local instrumentation validation
        ↓
local calibration
        ↓
local baseline execution after required locks
        ↓
later cloud-provider execution
        ↓
OpenAI Luna
        ↓
Anthropic Sonnet 5
```

This sequence does not imply that Granite replaces Luna or Sonnet 5, that the cloud
comparison is cancelled, that the provider-separated design is invalid, or that local
models are preferred analytically.

The existing provider-specific identifiers and review logic remain valid for the later
cloud path:

```text
HELM-P1-CAL-001-OAI-LUNA
HELM-P1-RAISE-SCOURGE-001-OAI-LUNA
HELM-P1-RAISE-SCOURGE-002-ANT-SONNET5
```

The existing same-family disclosure check,
`SAME_FAMILY_LIMITATION_UNDISCLOSED`, remains unchanged.

New additive local identifiers are:

```text
HELM-P1-CAL-001-LOCAL-GRANITE31-8B
HELM-P1-RAISE-SCOURGE-001-LOCAL-GRANITE31-8B
```

No existing cloud identifier is reused, renamed, removed, or reinterpreted. Qwen3 8B
Q4_K_M is documented only as an instrumentation-tested alternative and future
challenger; it is not a co-baseline and receives no analytic cell in this amendment.

---

# 4. Validated Local Runtime Identity

The local baseline records the runtime identity already observed during instrumentation:

```text
PROVIDER = LOCAL_LLAMA_CPP
MODEL = Granite 3.1 8B Instruct
QUANTIZATION = Q3_K_L
MODEL_FILE_SHA256 = 3c24bb01ed1181cb936a9f03c41f1fd3341555ea68086a4b81713a137c765eb6
BACKEND = VULKAN
DEVICE = Vulkan1
LLAMA_CPP_VERSION = 0.4.1-dev
LLAMA_CPP_COMMIT = fb27a525d28381a16a4bb038858a10e4927381ca
ENDPOINT = /v1/chat/completions
CONSTRAINT_MODE = DIRECT_GBNF
GRAMMAR_VERSION = agent_response.v1
GRAMMAR_SHA256 = 0615c3e026f681603b6c7f5f3d9c5a8b79b6bc06fca8bed921810a339c648d80
SILENT_FALLBACK_TO_UNCONSTRAINED_TEXT = FORBIDDEN
```

`MODEL_FILE_SHA256` identifies the exact GGUF bytes used by the smoke. The absolute
file path is machine-specific and is not part of the canonical artifact; only the
filename (`granite-3.1-8b-instruct-Q3_K_L.gguf`) is recorded for human context, since
the SHA-256 is the identity that matters. This single-machine reproducibility
limitation is recorded as a known limitation of the current local-first baseline; it
is not resolved by this amendment.

These fields identify the validated runtime path. They do not freeze calibration-dependent
execution settings.

---

# 5. Authority Boundary

Local model generation is not authority, governance, or certification.

HELM deterministic logic remains responsible for:

- authority validation,
- policy enforcement,
- containment,
- audit receipts,
- governance replay,
- and final deterministic adjudication where already defined.

The local model receives no new authority. Phase 0 behavior remains frozen.

---

# 6. Structured Chat Constraint

The pinned local runtime uses direct GBNF for structured chat output:

```text
CONSTRAINT_MODE = DIRECT_GBNF
```

JSON Schema with `/v1/chat/completions` is not used on this pinned runtime because
instrumentation found a reproducible server failure under that combination. The
limitation is tracked at [ggml-org/llama.cpp issue #29006](https://github.com/ggml-org/llama.cpp/issues/29006).
This amendment records the observed pinned-runtime limitation without claiming a
definitive upstream root cause beyond that evidence.

The implemented fail-closed rules remain:

- no silent fallback,
- no retry as unconstrained text,
- no semantic repair,
- server/runtime failure remains observable,
- known empty-grammar-stack failures classify as `CONSTRAINT_FAILURE`,
- generic or unknown server failures classify as `SERVER_ERROR`,
- and timeouts classify as `TIMEOUT`.

---

# 7. GBNF and Application Schema Boundary

`agent_response.v1.gbnf` is a minimal runtime and instrumentation grammar. It is not
the final six-agent Phase 1 response contract.

The current invariant remains:

```text
GBNF constraint
    ↓
generated JSON
    ↓
independent application validation
```

The application validator remains authoritative. Constrained decoding does not by
itself establish that a returned object satisfies the runtime contract.

Technical debt is recorded as:

```text
DIRECT_GBNF_SCHEMA_DRIFT_RISK
STATUS = KNOWN
CURRENT_SCOPE = NON_BLOCKING_FOR_CURRENT_INSTRUMENTATION
FREEZE_SCOPE = BLOCKING_BEFORE_FULL_PHASE_1_AGENT_CONTRACT_FREEZE
```

Before the full agent contract is frozen, HELM must establish either generated GBNF
from a canonical structured schema, automated equivalence or conformance tests between
the canonical schema and handwritten GBNF, or another human-reviewed mechanism with
comparable assurance. The choice is deferred by this amendment.

---

# 8. Calibration and Analytic Separation

Live instrumentation smoke is not calibration and is not analytic execution.

The smoke artifacts remain explicitly:

```text
INSTRUMENTATION_ONLY = TRUE
ANALYTIC_USE = FORBIDDEN
```

No behavior observed during the smoke may be used as Phase 1 behavioral evidence. Smoke
artifacts must not be imported into analytic result locations.

The smoke sampling values are recorded as observations only:

```text
seed = 23
temperature = 0
top_k = 1
top_p = 1.0
min_p = 0
max_tokens = 160
context = 2048
reasoning = off
```

These values do not silently become final analytic settings.

---

# 9. Calibration-Dependent Fields

The following remain `UNSET_BY_DESIGN` and are not frozen by Amendment 004:

```text
MAX_AGENT_TURNS
MAX_MESSAGES_PER_EPISODE
EPISODE_TIMEOUT_SECONDS
FINAL_SAMPLING_PARAMETERS
FINAL_CONTEXT_SIZE
FINAL_MAX_TOKENS
FINAL_RUNTIME_LIMITS
FINAL_AGGREGATE_RUNTIME_FINGERPRINT
```

Calibration may determine the operational envelope later. It may not redefine
behavioral criteria or promote smoke observations into analytic evidence.

---

# 10. Replay and Governance Semantics

Amendment 003 replay semantics remain unchanged. `GOVERNANCE_ONLY` replay consumes
frozen normalized outputs and deterministic governance state. Calling a provider again
is `MODEL_REGENERATION` or `END_TO_END_RERUN`, not replay.

The local runtime transition does not make exact model regeneration a requirement for
deterministic governance replay.

---

# 11. Lock State

The expected state after registering this amendment is:

```text
AMENDMENTS_001_004 = PROPOSED
PRECAL_READINESS = NOT_YET_FINAL
ANALYTIC_LOCK_VALID = FALSE
```

Amendment 004 does not authorize calibration or analytic execution. The model freeze
must continue to fail closed while any required amendment remains `PROPOSED`.

---

# 12. Unchanged Scope

This amendment does not modify:

- the six fixed roles,
- task families or fixtures,
- analytic seeds or cohort size,
- behavioral definitions or their independent semantic hash,
- authority validation,
- policy enforcement,
- containment,
- audit receipts,
- governance replay,
- the AI pre-review and one-human-final-adjudicator model,
- the existing Luna/Sonnet provider disclosure requirements,
- or Phase 0 semantics.

No Docker runtime, orchestrator, fixture, provider adapter, Watcher runtime, or model
execution is introduced by this amendment.

---

# 13. Amendment Decision

This amendment remains `PROPOSED` until a human lock record is created. It documents
local-first runtime sequencing and preserves the later cloud-provider path; it does not
claim a comparative model result or authorize Phase 1 analytic execution.
