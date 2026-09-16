"""Strict wire schemas and canonical encoding shared by governance and replay."""

import hashlib
import json
from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any


def canonical(value: Any) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    )


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def fields(value: Any, required: set[str]) -> None:
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError("INVALID_FIELDS")


def text(value: Any) -> str:
    if not isinstance(value, str) or not value or len(value) > 16384:
        raise ValueError("INVALID_TEXT")
    return value


def integer(value: Any) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("INVALID_INTEGER")
    return value


class AuthorityStatus(StrEnum):
    VALID = "VALID_AUTHORITY"
    DEGRADED = "DEGRADED_AUTHORITY"
    NONE = "NO_AUTHORITY"
    FALSE = "FALSE_AUTHORITY"


class State(StrEnum):
    INTACT = "HELM_INTACT"
    DEGRADED = "HELM_DEGRADED"
    DESTROYED = "HELM_DESTROYED"
    FALSE = "FALSE_LICH_KING_ATTEMPT"
    CONTAINED = "CONTAINMENT_ACTIVE"


class Decision(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REVIEW = "REVIEW_REQUIRED"
    CONTAIN = "CONTAIN"


class Action(StrEnum):
    LOCAL_REASONING = "LOCAL_REASONING"
    AGENT_MESSAGE = "AGENT_MESSAGE"
    MEMORY_READ = "MEMORY_READ"
    MEMORY_WRITE = "MEMORY_WRITE"
    TOOL_REQUEST = "TOOL_REQUEST"
    ROLE_CHANGE = "ROLE_CHANGE"
    AGENT_SPAWN = "AGENT_SPAWN"
    POLICY_CHANGE = "POLICY_CHANGE"
    EXTERNAL_ACTION = "EXTERNAL_ACTION"
    AUTHORITY_DELEGATION = "AUTHORITY_DELEGATION"


@dataclass(frozen=True)
class Claim:
    issuer: str
    target: str
    command_id: str
    authority_scope: Action
    issued_at: int
    expires_at: int
    nonce: str
    signature_or_test_token: str
    delegation_chain: tuple[str, ...]
    request_digest: str
    policy_version: str

    @classmethod
    def parse(cls, value: Any) -> "Claim":
        fields(value, set(cls.__dataclass_fields__))
        chain = value["delegation_chain"]
        if not isinstance(chain, list):
            raise ValueError("INVALID_DELEGATION")
        for item in chain:
            text(item)
        for key in set(cls.__dataclass_fields__) - {
            "issued_at",
            "expires_at",
            "delegation_chain",
            "authority_scope",
        }:
            text(value[key])
        integer(value["issued_at"])
        integer(value["expires_at"])
        return cls(
            **{
                **value,
                "authority_scope": Action(value["authority_scope"]),
                "delegation_chain": tuple(chain),
            }
        )

    def unsigned(self) -> dict:
        return {k: v for k, v in asdict(self).items() if k != "signature_or_test_token"}


@dataclass(frozen=True)
class Message:
    message_id: str
    sender: str
    recipient: str
    timestamp: int
    message_type: str
    content: str
    requested_action: Action
    claimed_authority: Claim | None
    parent_message: str | None

    @classmethod
    def parse(cls, value: Any) -> "Message":
        fields(value, set(cls.__dataclass_fields__))
        for key in ("message_id", "sender", "recipient", "message_type", "content"):
            text(value[key])
        integer(value["timestamp"])
        if value["parent_message"] is not None:
            text(value["parent_message"])
        if value["message_type"] not in {
            "INFO",
            "PROPOSAL",
            "COMMAND",
            "REQUEST",
            "RESPONSE",
            "ALERT",
            "AUTHORITY_CLAIM",
        }:
            raise ValueError("INVALID_MESSAGE_TYPE")
        claim = value["claimed_authority"]
        return cls(
            **{
                **value,
                "requested_action": Action(value["requested_action"]),
                "claimed_authority": None if claim is None else Claim.parse(claim),
            }
        )

    def binding(self) -> dict:
        return {k: v for k, v in asdict(self).items() if k != "claimed_authority"}


@dataclass(frozen=True)
class Receipt:
    decision_id: str
    timestamp: int
    agent_id: str
    requested_action: str
    authority_status: AuthorityStatus
    policy_result: Decision
    system_state: State
    decision: Decision
    reason_code: str
    human_review_required: bool
    containment_triggered: bool

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return canonical(self.to_dict())
