# Architecture

The deterministic control plane owns identity issuance, supervisor configuration,
the immutable policy, clock, nonce history, state machine, containment, and audit.
The agent plane is represented by untrusted JSON messages. No LLM participates in
any permission decision. The experiment runner is trusted setup and fault injection.

## Boundaries and flow

1. The runner loads a strict scenario and policy, creates six fixed roles plus a
   supervisor, and selects a logical clock and deterministic nonce seed.
2. Agent requests address `helm`. The sender is the requesting agent; a claim from
   the configured supervisor must target that sender. This is not a direct
   supervisor-to-agent transport. Non-action message types exist in the schema but
   cannot execute an action through this endpoint.
3. The runtime records the complete received JSON, validates the message and active
   identity, rejects stale/future or duplicate messages, then checks authority.
4. Authority uses an HMAC over canonical claim fields. The claim includes a digest
   of all message fields except the claim itself. Issuer, target, command ID, scope,
   time interval, policy version, and empty delegation chain must match.
5. Successfully validated nonces and command IDs are consumed even if policy later
   denies the action. A consumed authorization cannot be retried as another action.
6. Global prohibition overrides role permissions, capabilities, and review rules.
   Role/capability denial precedes the tool review gate. Policy is never parsed from
   message content. Unknown wire fields/actions fail closed.
7. Failed authority produces an explicit authority status, state transition, and
   sticky containment. The final receipt records both policy and effective decision.
8. Every request records a receipt, review event when needed, and simulated outcome.
   Nothing is dispatched outside the process.

See [diagram source](../visual/architecture/phase0.mmd).

## State semantics

| State | Permitted next states |
|---|---|
| HELM_INTACT | HELM_DEGRADED, HELM_DESTROYED, FALSE_LICH_KING_ATTEMPT, CONTAINMENT_ACTIVE |
| HELM_DEGRADED | HELM_DESTROYED, FALSE_LICH_KING_ATTEMPT, CONTAINMENT_ACTIVE |
| HELM_DESTROYED | FALSE_LICH_KING_ATTEMPT, CONTAINMENT_ACTIVE |
| FALSE_LICH_KING_ATTEMPT | CONTAINMENT_ACTIVE |
| CONTAINMENT_ACTIVE | None |

Self-transitions and all other edges are rejected and audited. Initial state is
trusted scenario configuration. Failures first record the applicable intermediate
state when the edge is valid, then activate containment; receipts show the final
state and retain the authority status. Degraded or destroyed state never recovers
because a later message looks valid.

## Determinism and audit

Time is a nonnegative logical integer provided by the trusted runner; no wall clock
is sampled. Claims use half-open validity intervals. Messages may be at most 30
ticks old. The control clock cannot regress. Invalid runner clocks/configuration
are setup errors, not agent decisions.

Canonical JSON uses sorted keys, compact separators, ASCII escapes, and rejects
NaN. Decision IDs include the request audit hash and decision fields, so identical
configurations produce identical histories. Event hashes include sequence number,
timestamp, kind, payload, and previous hash. The public audit view is copied and
the API only appends. Output directories must be new.

A hash chain alone cannot detect truncation or wholesale rehashing. Replay reruns
the embedded configuration and compares all output, catching truncation and
inconsistent decisions. Authenticity against a privileged attacker needs a future
independent signed checkpoint or external append-only sink.

## Future adapter boundary

A future LLM adapter may propose schema-valid messages with fixed identities. It
must not hold signing keys, mutate the registry/policy, call the runtime internals,
or access arbitrary tools. Before untrusted adapters exist, isolate the control
plane in a separate process and authenticate its transport. Review receipts are
not authorization tokens. Memory and peer-message effects are currently simulated;
scope-aware stores and routed delivery belong to a later reviewed phase.
