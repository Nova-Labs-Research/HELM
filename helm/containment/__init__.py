"""Containment is sticky; an agent cannot release it during an experiment."""

from helm.governance import Governance
from helm.schema import State


class Containment:
    def __init__(self, governance: Governance):
        self.governance = governance
        self.reason: str | None = None

    @property
    def active(self) -> bool:
        return self.governance.state == State.CONTAINED

    def activate(self, now: int, reason: str) -> bool:
        if self.active:
            return False
        self.governance.transition(State.CONTAINED, now, reason)
        self.reason = reason
        self.governance.audit.append("containment", now, {"reason": reason})
        return True

    def request_release(self, now: int, requester: str) -> None:
        self.governance.audit.append("release_rejected", now, {"requester": requester})
        raise PermissionError("OFFLINE_HUMAN_REVIEW_AND_NEW_RUN_REQUIRED")
