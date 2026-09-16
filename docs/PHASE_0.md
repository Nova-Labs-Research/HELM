# Phase 0 — Frozen Throne

Goal: build deterministic governance before introducing probabilistic agents.

## Frozen interface v1

- Python 3.13+, no runtime dependencies; `unittest` and Ruff for verification.
- Authority outcomes: VALID_AUTHORITY, DEGRADED_AUTHORITY, NO_AUTHORITY, FALSE_AUTHORITY.
- Policy/effective decisions: ALLOW, DENY, REVIEW_REQUIRED, CONTAIN.
- Fixed roles, immutable policies, strict JSON messages, synthetic HMAC claims.
- No delegation, live tool execution, LLMs, external action, or in-run recovery.
- Trusted logical clock, seeded nonces, canonical JSON, SHA-256 decision IDs and audit chain.
- Receipts contain decision_id, timestamp, agent_id, requested_action, authority_status,
  policy_result, system_state, decision, reason_code, human_review_required, containment_triggered.

An invalid claim yields containment; known agents can still perform policy-approved
local reasoning. This exception does not accept the false claim or grant its scope.
A malformed message, unknown sender, duplicate request, or invalid message envelope
does not qualify for that exception.

## Exit checks

- Deterministic authority and policy checks, including replay rejection.
- False authority rejected and missing authority contained.
- Degraded authority visible in receipts and transitions.
- Sticky containment with no agent self-release.
- Replayable logs and exact result verification.
- Four scenario files with integration/adversarial tests.
- Documentation matches the simulated runtime.
- Tests and lint/format checks pass without any model service.

Run the commands in the README. The verification report records the actual checks
performed for this implementation. The `v0.1.0-frozen-throne` tag freezes this
synthetic contract, not a production authentication or isolation guarantee.

## Scenario semantics

Intact permits baseline reasoning, messaging, and synthetic memory proposals.
Degraded injects stale claims, duplicates, outdated policy, contradiction, dropped
messages, state loss, and latency. Contradiction/drop/state-loss signals are trusted
fault-injection events that conservatively activate containment; Phase 0 does not
infer semantic contradictions from prose or simulate distributed consensus.
Destroyed revokes the supervisor while retaining policy and role definitions;
there is no actual persistent memory store yet. False Lich King introduces rogue
issuers, forged tokens, emergency/safety/continuity text, fake delegation, and
role/policy mutation attempts. Independent adversarial fixtures prevent an early
containment event from masking the first response to each fault.

## Deferred work

Concept artwork is pending the original asset. Composite Break-Free Index, persistent
memory, behavior detection, live agent adapters, and interactive visualization are
later milestones. Passing Phase 0 does not automatically start Phase 1: adapter
choice and an isolated agent boundary must be designed first.
