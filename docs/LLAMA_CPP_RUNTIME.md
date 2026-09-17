# Local llama.cpp instrumentation runtime

HELM has an isolated local adapter for one structured-output request against
`/v1/chat/completions`. It uses direct GBNF because the pinned llama.cpp build
passed direct GBNF for chat while the equivalent JSON-Schema chat requests
returned the observed empty-grammar-stack failure (tracked as
[ggml-org/llama.cpp issue #29006](https://github.com/ggml-org/llama.cpp/issues/29006)).
The adapter does not silently retry without constraints; a recognized
constrained-decoding failure is recorded as `CONSTRAINT_FAILURE` and all other
non-2xx responses are conservatively `SERVER_ERROR`.

The first grammar is the deliberately minimal instrumentation contract at
`helm/structured_output/grammars/agent_response.v1.gbnf`. Its version and exact
byte hash are captured in every result. GBNF constrains generation, while the
independent application validator still checks object shape, required fields,
the action enum, reason type, and unexpected fields. A grammar-enabled response
therefore never bypasses application validation.

The smoke path is one logical `VERIFIER` request and is explicitly marked
`instrumentation_only = true` and `analytic_use = FORBIDDEN`. It does not write
Phase 1 analytic results or alter preregistration, calibration, behavioral
definitions, or governance behavior.

## Technical debt

`DIRECT_GBNF_SCHEMA_DRIFT_RISK` — **KNOWN**; **NON_BLOCKING_FOR_INSTRUMENTATION**;
**BLOCKING_BEFORE_FULL_PHASE_1_AGENT_CONTRACT_FREEZE**.

The minimal handwritten GBNF and the application-level schema are intentionally
separate in this build. Before the full multi-agent response contract is frozen,
HELM must establish either generated GBNF from a canonical structured schema,
automated equivalence/conformance tests between the canonical schema and the
handwritten grammar, or another human-reviewed mechanism with comparable
assurance. The choice is intentionally deferred.
