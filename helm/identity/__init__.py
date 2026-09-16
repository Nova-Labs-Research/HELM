"""Identities are issued by the trusted experiment setup, never agent messages."""

from dataclasses import dataclass, replace
from enum import StrEnum

from helm.schema import Action, integer, text


class Role(StrEnum):
    SUPERVISOR = "supervisor"
    PLANNER = "planner"
    SEARCHER = "searcher"
    MEMORY = "memory"
    VERIFIER = "verifier"
    EXECUTOR = "executor"
    WATCHER = "watcher"


@dataclass(frozen=True)
class AgentIdentity:
    agent_id: str
    role: Role
    instance_id: str
    authority_level: int
    capabilities: frozenset[Action]
    issued_at: int
    expires_at: int
    parent_authority: str | None
    status: str = "active"

    def __post_init__(self) -> None:
        text(self.agent_id)
        text(self.instance_id)
        integer(self.authority_level)
        integer(self.issued_at)
        integer(self.expires_at)
        if not isinstance(self.role, Role) or not isinstance(self.capabilities, frozenset):
            raise ValueError("INVALID_IDENTITY")
        if any(not isinstance(action, Action) for action in self.capabilities):
            raise ValueError("INVALID_CAPABILITY")
        ceiling = 100 if self.role == Role.SUPERVISOR else 10
        if self.authority_level > ceiling or self.expires_at <= self.issued_at:
            raise ValueError("IDENTITY_CEILING_OR_EXPIRY")
        if self.status not in {"active", "revoked"}:
            raise ValueError("INVALID_IDENTITY_STATUS")
        if self.parent_authority is not None:
            text(self.parent_authority)


class IdentityRegistry:
    def __init__(self) -> None:
        self._identities: dict[str, AgentIdentity] = {}

    def add(self, identity: AgentIdentity) -> None:
        if identity.agent_id in self._identities or any(
            item.instance_id == identity.instance_id for item in self._identities.values()
        ):
            raise ValueError("DUPLICATE_IDENTITY")
        self._identities[identity.agent_id] = identity

    def lookup(self, agent_id: str, now: int) -> tuple[AgentIdentity | None, str]:
        identity = self._identities.get(agent_id)
        if identity is None:
            return None, "UNKNOWN_AGENT"
        if identity.status != "active":
            return None, "REVOKED_IDENTITY"
        if not identity.issued_at <= now < identity.expires_at:
            return None, "EXPIRED_IDENTITY"
        return identity, "IDENTITY_VALID"

    def revoke(self, agent_id: str) -> None:
        if agent_id not in self._identities:
            raise ValueError("UNKNOWN_AGENT")
        self._identities[agent_id] = replace(self._identities[agent_id], status="revoked")
