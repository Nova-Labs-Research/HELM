"""Governance state machine. Recovery is an offline human experiment boundary."""

from helm.audit import AuditLog
from helm.schema import State

TRANSITIONS = {
    State.INTACT: frozenset({State.DEGRADED, State.DESTROYED, State.FALSE, State.CONTAINED}),
    State.DEGRADED: frozenset({State.DESTROYED, State.FALSE, State.CONTAINED}),
    State.DESTROYED: frozenset({State.FALSE, State.CONTAINED}),
    State.FALSE: frozenset({State.CONTAINED}),
    State.CONTAINED: frozenset(),
}


class Governance:
    def __init__(self, audit: AuditLog, initial: State = State.INTACT):
        if not isinstance(initial, State):
            raise ValueError("INVALID_INITIAL_STATE")
        self._state = initial
        self.audit = audit

    @property
    def state(self) -> State:
        return self._state

    def transition(self, target: State, now: int, reason: str) -> None:
        if target not in TRANSITIONS[self.state]:
            self.audit.append(
                "invalid_transition", now, {"from": self.state, "to": target, "reason": reason}
            )
            raise ValueError("INVALID_TRANSITION")
        self.audit.append(
            "state_transition", now, {"from": self.state, "to": target, "reason": reason}
        )
        self._state = target
