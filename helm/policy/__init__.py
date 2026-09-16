"""Immutable, closed policy: global prohibitions take precedence over role grants."""

from dataclasses import dataclass
from types import MappingProxyType

from helm.identity import AgentIdentity, Role
from helm.schema import Action, Decision, fields, text

PROHIBITED = frozenset(
    {
        Action.ROLE_CHANGE,
        Action.AGENT_SPAWN,
        Action.POLICY_CHANGE,
        Action.EXTERNAL_ACTION,
        Action.AUTHORITY_DELEGATION,
    }
)
ROLE_ACTIONS = MappingProxyType(
    {
        Role.SUPERVISOR: frozenset({Action.LOCAL_REASONING}),
        Role.PLANNER: frozenset({Action.LOCAL_REASONING, Action.AGENT_MESSAGE}),
        Role.SEARCHER: frozenset(
            {Action.LOCAL_REASONING, Action.AGENT_MESSAGE, Action.MEMORY_READ}
        ),
        Role.MEMORY: frozenset(
            {Action.LOCAL_REASONING, Action.AGENT_MESSAGE, Action.MEMORY_READ, Action.MEMORY_WRITE}
        ),
        Role.VERIFIER: frozenset(
            {Action.LOCAL_REASONING, Action.AGENT_MESSAGE, Action.MEMORY_READ}
        ),
        Role.EXECUTOR: frozenset(
            {Action.LOCAL_REASONING, Action.AGENT_MESSAGE, Action.TOOL_REQUEST}
        ),
        Role.WATCHER: frozenset({Action.LOCAL_REASONING, Action.AGENT_MESSAGE, Action.MEMORY_READ}),
    }
)


@dataclass(frozen=True)
class Policy:
    version: str = "phase0-v1"
    deny: frozenset[Action] = PROHIBITED
    review: frozenset[Action] = frozenset({Action.TOOL_REQUEST})

    def __post_init__(self) -> None:
        text(self.version)
        if not isinstance(self.deny, frozenset) or not isinstance(self.review, frozenset):
            raise ValueError("IMMUTABLE_POLICY_REQUIRED")
        if not PROHIBITED <= self.deny or Action.TOOL_REQUEST not in self.review:
            raise ValueError("UNSAFE_POLICY")
        if any(not isinstance(a, Action) for a in self.deny | self.review):
            raise ValueError("INVALID_POLICY_ACTION")

    @classmethod
    def parse(cls, value: dict) -> "Policy":
        fields(value, {"version", "deny", "review"})
        if not isinstance(value["deny"], list) or not isinstance(value["review"], list):
            raise ValueError("INVALID_POLICY")
        return cls(
            text(value["version"]),
            frozenset(Action(a) for a in value["deny"]),
            frozenset(Action(a) for a in value["review"]),
        )

    def to_dict(self) -> dict:
        return {"version": self.version, "deny": sorted(self.deny), "review": sorted(self.review)}

    def evaluate(self, identity: AgentIdentity, action: Action) -> tuple[Decision, str]:
        if action in self.deny:
            return Decision.CONTAIN, "GLOBAL_PROHIBITION"
        if action not in ROLE_ACTIONS[identity.role] or action not in identity.capabilities:
            return Decision.DENY, "ROLE_OR_CAPABILITY_DENIED"
        if action in self.review:
            return Decision.REVIEW, "REVIEW_GATE"
        return Decision.ALLOW, "POLICY_ALLOWED"
