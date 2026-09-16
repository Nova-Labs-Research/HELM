"""Single governance entry point. Allowed actions produce simulated results only."""

from dataclasses import asdict
from typing import Any

from helm.audit import AuditLog
from helm.containment import Containment
from helm.governance import TRANSITIONS, Governance
from helm.governance.authority import AuthorityValidator
from helm.identity import IdentityRegistry
from helm.policy import Policy
from helm.schema import (
    Action,
    AuthorityStatus,
    Decision,
    Message,
    Receipt,
    State,
    digest,
    integer,
)


class Runtime:
    def __init__(
        self,
        registry: IdentityRegistry,
        supervisor: str,
        key: bytes,
        policy: Policy | None = None,
        initial: State = State.INTACT,
    ):
        self.registry = registry
        self.policy = policy or Policy()
        self.audit = AuditLog()
        self.governance = Governance(self.audit, initial)
        self.containment = Containment(self.governance)
        self.authority = AuthorityValidator(registry, supervisor, key, self.policy.version)
        self._seen: set[str] = set()
        self._clock = 0
        self.receipts: list[Receipt] = []

    def _contain(self, status: AuthorityStatus, now: int, reason: str) -> bool:
        target = {
            AuthorityStatus.FALSE: State.FALSE,
            AuthorityStatus.NONE: State.DESTROYED,
            AuthorityStatus.DEGRADED: State.DEGRADED,
        }.get(status)
        state = self.governance.state
        # Never restore a weaker state after a stronger failure.
        if target is not None and state != State.CONTAINED:
            if target in TRANSITIONS[state]:
                self.governance.transition(target, now, reason)
        return self.containment.activate(now, reason)

    def handle(self, raw: Any, now: int) -> Receipt:
        integer(now)
        if now < self._clock:
            raise ValueError("CONTROL_PLANE_CLOCK_REGRESSION")
        self._clock = now
        # Wire inputs are JSON values. Audit stores a canonical copy before parsing.
        received = self.audit.append("received_command", now, {"message": raw})
        status = AuthorityStatus.FALSE
        policy_result = Decision.DENY
        decision = Decision.CONTAIN
        reason = "MALFORMED_MESSAGE"
        authority_reason = None
        policy_reason = "NOT_EVALUATED"
        agent_id = "<unknown>"
        action = "<invalid>"
        triggered = False
        message = None
        try:
            message = Message.parse(raw)
        except (ValueError, TypeError):
            triggered = self._contain(status, now, reason)
        if message is not None:
            agent_id, action = message.sender, message.requested_action
            identity, identity_reason = self.registry.lookup(agent_id, now)
            self.audit.append(
                "identity_result",
                now,
                {
                    "agent_id": agent_id,
                    "reason": identity_reason,
                    "identity": None
                    if identity is None
                    else {**asdict(identity), "capabilities": sorted(identity.capabilities)},
                },
            )
            if identity is None:
                reason = identity_reason
            elif message.recipient != "helm":
                reason = "INVALID_RECIPIENT"
            elif message.message_type not in {"REQUEST", "COMMAND", "AUTHORITY_CLAIM"}:
                reason = "NON_ACTION_MESSAGE"
            elif message.timestamp > now or now - message.timestamp > 30:
                status, reason = AuthorityStatus.DEGRADED, "STALE_OR_FUTURE_MESSAGE"
            elif message.message_id in self._seen:
                reason = "DUPLICATE_MESSAGE"
            else:
                self._seen.add(message.message_id)
                status, reason = self.authority.validate(message, now)
                authority_reason = reason
                policy_result, policy_reason = self.policy.evaluate(
                    identity, message.requested_action
                )
                if message.requested_action in {
                    Action.ROLE_CHANGE,
                    Action.AGENT_SPAWN,
                    Action.POLICY_CHANGE,
                    Action.AUTHORITY_DELEGATION,
                }:
                    self.audit.append(
                        "restricted_action_attempt", now, {"agent_id": agent_id, "action": action}
                    )
                if status != AuthorityStatus.VALID:
                    triggered = self._contain(status, now, reason)
                    # A known identity may continue bounded, side-effect-free reasoning.
                    if (
                        message.requested_action == Action.LOCAL_REASONING
                        and policy_result == Decision.ALLOW
                    ):
                        decision = Decision.ALLOW
                        reason = "CONTAINED_LOCAL_REASONING"
                elif policy_result == Decision.CONTAIN:
                    reason = policy_reason
                    triggered = self._contain(status, now, reason)
                elif self.governance.state != State.INTACT:
                    if self.governance.state != State.CONTAINED:
                        status = {
                            State.DESTROYED: AuthorityStatus.NONE,
                            State.DEGRADED: AuthorityStatus.DEGRADED,
                            State.FALSE: AuthorityStatus.FALSE,
                        }[self.governance.state]
                        authority_reason = "GOVERNANCE_UNAVAILABLE"
                    triggered = self._contain(status, now, "GOVERNANCE_UNAVAILABLE")
                    if (
                        message.requested_action == Action.LOCAL_REASONING
                        and policy_result == Decision.ALLOW
                    ):
                        decision, reason = Decision.ALLOW, "CONTAINED_LOCAL_REASONING"
                    else:
                        decision, reason = Decision.DENY, "CONTAINMENT_ACTIVE"
                else:
                    decision, reason = policy_result, policy_reason
            if decision == Decision.CONTAIN and not self.containment.active:
                triggered = self._contain(status, now, reason)
        self.audit.append(
            "authority_result", now, {"status": status, "reason": authority_reason or reason}
        )
        self.audit.append(
            "policy_result",
            now,
            {"result": policy_result, "action": action, "reason": policy_reason},
        )
        review = self.containment.active or decision in {Decision.REVIEW, Decision.CONTAIN}
        values = {
            "timestamp": now,
            "agent_id": agent_id,
            "requested_action": action,
            "authority_status": status,
            "policy_result": policy_result,
            "system_state": self.governance.state,
            "decision": decision,
            "reason_code": reason,
            "human_review_required": review,
            "containment_triggered": triggered,
        }
        receipt = Receipt(decision_id=digest({"input_hash": received["hash"], **values}), **values)
        self.receipts.append(receipt)
        self.audit.append("decision", now, receipt.to_dict())
        if review:
            self.audit.append("human_review", now, {"decision_id": receipt.decision_id})
        self.audit.append(
            "action_result",
            now,
            {
                "decision_id": receipt.decision_id,
                "result": "simulated" if decision == Decision.ALLOW else "not_executed",
            },
        )
        return receipt
