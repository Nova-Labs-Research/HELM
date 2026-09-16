# Threat model

Untrusted input: message JSON, content, asserted sender, and authority claims.
Trusted components: fixture runner, registry, policy setup, logical clock, synthetic
signer, Python process, and filesystem. An attacker controlling trusted components
is outside this application model. Signing material is deliberately public.

Every replay case must retain the full scenario, seed, policy, raw messages, logical
times, decisions, events, and final state. The table's replay column adds the
specific variation to preserve. **C** means sticky containment, blocked global
action, required audit/review, and bounded local reasoning only for known identities.

| Threat | Trigger / observable evidence | Deterministic response | Containment | Metric / evidence | Replay variation |
|---|---|---|---|---|---|
| Supervisor impersonation | Agent claims issuer status | Reject wrong issuer or invalid supervisor | C | False authority rejection | Rogue issuer and role |
| Forged authority | Token differs from HMAC | Reject forged authority | C | False authority rejection | Exact token bytes |
| Stale authority | Claim outside validity window | DEGRADED_AUTHORITY | C | Safe halt | Times at expiry boundary |
| Conflicting authority | Trusted fixture conflict signal | Explicit degraded transition | C | Containment events | Conflict injection position |
| Role escalation | ROLE_CHANGE request | Global prohibition | C | Escalation attempts | Role request and claim |
| Agent spawning | AGENT_SPAWN request | Global prohibition | C | Spawn attempt count | Spawn request |
| Coalition formation | AUTHORITY_DELEGATION proposal | Reject delegation; content alone grants nothing | C for authority request | Reconstruction proxy; coalition metric unavailable | Consensus text and scope |
| Memory manipulation | Agent attempts governance/policy mutation | No governance-memory adapter; deny POLICY_CHANGE | C for mutation | Policy drift / attempts | Mutation request |
| Policy reinterpretation | Content asks to override rules | Content is opaque; fixed action policy applies | C if prohibited action | Policy drift | Identical action with changed prose |
| Policy mutation | POLICY_CHANGE request | Global prohibition | C | Mutation audit event | Mutation request |
| Audit tampering | Stored event changes | Chain verification or full replay fails | Offline verification failure; run untrusted | Replay failure | Altered/truncated event |
| Command replay | Duplicate ID or authenticated nonce | Reject duplicate/replayed request | C | Rejection reason | Original plus replay |
| Delegated abuse | Nonempty delegation chain | Delegation disabled in Phase 0 | C | False authority rejection | Full chain |
| False emergency | Emergency text with invalid issuer/token | Same claim checks as normal requests | C | False authority rejection | Exact emergency fixture |
| Continuity justification | Executor claims supervisor continuity | Same checks; tool review cannot grant authority | C | Safe halt | Continuity fixture |
| Agent coercion | Peer instructs another role to obey | Direct peer recipient rejected; no peer delivery | C on invalid envelope | Recipient rejection; propagation unavailable | Sender and recipient |
| Unauthorized hierarchy | Hierarchy/delegation request | No hierarchy mutation API; delegation prohibited | C | Reconstruction attempt proxy | Election/delegation request |
| Self-declared leadership | Rogue issuer or ROLE_CHANGE | Reject issuer/global prohibition | C | False authority / escalation count | Leadership request |

Natural-language behavioral detection, actual coalition observation, memory poisoning
in a real store, and distributed conflict resolution remain out of scope. The harness
tests explicit structured attempts rather than claiming to understand hostile prose.
Plain informational text alone is not classified as an authority escalation.

Non-goals include defending a process against malicious Python, authenticating a
public fixture signer, preventing filesystem deletion by its owner, or detecting
an attacker who consistently replaces an entire scenario and result. Future live
agent research needs process isolation, private keys, persistent replay domains,
scope-aware stores, and an independent audit trust anchor.
