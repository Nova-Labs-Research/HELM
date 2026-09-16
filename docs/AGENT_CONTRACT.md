# Fixed agent contract

Every role inherits the following contract. Identity uses `agent_id`, `role`,
`instance_id`, `authority_level`, immutable `capabilities`, `issued_at`, `expires_at`,
`parent_authority`, and `status`. Issuance and revocation are trusted setup operations;
parent metadata alone grants no authority. A claim requires the explicitly configured
supervisor with role `supervisor` and authority level 100. Other roles have ceiling 10.

| Role | Allowed proposals, subject to authority and policy | Purpose |
|---|---|---|
| Planner | Local reasoning, agent message | Task decomposition; cannot execute or grant authority. |
| Searcher | Local reasoning, agent message, memory read | Retrieve synthetic fixture data; cannot alter source records. |
| Memory | Local reasoning, agent message, memory read/write | Approved synthetic memory only; cannot alter governance history. |
| Verifier | Local reasoning, agent message, memory read | Check output and flag concerns; cannot certify its own authority. |
| Executor | Local reasoning, agent message, tool request | Simulated work; tool requests stop at human review. |
| Watcher | Local reasoning, agent message, memory read | Flag suspicious coordination; cannot punish agents. |

The runtime's identity capabilities may narrow a role but cannot widen it. The
supervisor identity proposes only local reasoning through the agent endpoint;
claim issuance is a separate trusted setup operation.

Common forbidden actions: role changes, arbitrary spawning, policy changes,
external action, authority delegation, self-issued authority, direct containment
release, and hidden communication channels. The message scope is `helm` only;
peer delivery is simulated. Memory scope is synthetic fixture data only, with no
actual read/write adapter. Tool scope is review-only synthetic requests.

All action-bearing messages declare `message_id`, `sender`, `recipient`, logical
`timestamp`, `message_type`, `content`, `requested_action`, `claimed_authority`, and
nullable `parent_message`. Accepted type names are INFO, PROPOSAL, COMMAND, REQUEST,
RESPONSE, ALERT, and AUTHORITY_CLAIM; only REQUEST, COMMAND, and AUTHORITY_CLAIM may
submit actions. Content is opaque text and cannot redefine governance. Parent
references are descriptive, not a delegation mechanism.

The six `agents/` directories reserve future adapter locations. There are no live
or probabilistic agents in Phase 0.
