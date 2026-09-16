"""Provider-neutral Phase 1 episode envelope and termination metadata.

This module does not call a model or classify behavior. It records only observable
episode boundaries so a later provider adapter can apply one frozen envelope to all
episodes in that provider run.
"""

from dataclasses import asdict, dataclass
from enum import StrEnum
from math import isfinite
from typing import Any


class TerminationReason(StrEnum):
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_FAILED_FINAL = "TASK_FAILED_FINAL"
    MAX_AGENT_TURNS_REACHED = "MAX_AGENT_TURNS_REACHED"
    MAX_MESSAGES_REACHED = "MAX_MESSAGES_REACHED"
    EPISODE_TIMEOUT = "EPISODE_TIMEOUT"
    CONTAINMENT_TERMINATED = "CONTAINMENT_TERMINATED"
    UNRECOVERABLE_RUNTIME_FAILURE = "UNRECOVERABLE_RUNTIME_FAILURE"


class TaskCompletionStatus(StrEnum):
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    INCOMPLETE = "INCOMPLETE"


class ContainmentStatus(StrEnum):
    INACTIVE = "INACTIVE"
    ACTIVE = "ACTIVE"
    TERMINATED = "TERMINATED"


class TechnicalExclusionStatus(StrEnum):
    NONE = "NONE"
    EXCLUDED = "EXCLUDED"


def _nonnegative_int(value: Any, name: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"INVALID_{name.upper()}")
    return value


def _positive_int(value: Any, name: str) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError(f"INVALID_{name.upper()}")
    return value


def _nonnegative_float(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"INVALID_{name.upper()}")
    value = float(value)
    if not isfinite(value) or value < 0:
        raise ValueError(f"INVALID_{name.upper()}")
    return value


@dataclass(frozen=True)
class EpisodeLimits:
    """The provider-wide limits frozen after instrumentation-only calibration."""

    max_agent_turns: int
    max_messages_per_episode: int
    episode_timeout_seconds: float

    def __post_init__(self) -> None:
        _positive_int(self.max_agent_turns, "max_agent_turns")
        _positive_int(self.max_messages_per_episode, "max_messages_per_episode")
        if _nonnegative_float(self.episode_timeout_seconds, "episode_timeout_seconds") <= 0:
            raise ValueError("INVALID_EPISODE_TIMEOUT_SECONDS")

    def to_dict(self) -> dict[str, int | float]:
        return asdict(self)


@dataclass(frozen=True)
class EpisodeMetadata:
    """Raw boundary metadata retained alongside derived behavioral results."""

    termination_reason: TerminationReason
    final_turn_count: int
    final_message_count: int
    wall_clock_duration: float
    task_completion_status: TaskCompletionStatus
    containment_status: ContainmentStatus
    technical_exclusion_status: TechnicalExclusionStatus

    def __post_init__(self) -> None:
        _nonnegative_int(self.final_turn_count, "final_turn_count")
        _nonnegative_int(self.final_message_count, "final_message_count")
        _nonnegative_float(self.wall_clock_duration, "wall_clock_duration")
        for value, enum_type in (
            (self.termination_reason, TerminationReason),
            (self.task_completion_status, TaskCompletionStatus),
            (self.containment_status, ContainmentStatus),
            (self.technical_exclusion_status, TechnicalExclusionStatus),
        ):
            if not isinstance(value, enum_type):
                raise ValueError("INVALID_EPISODE_METADATA_ENUM")
        if self.termination_reason == TerminationReason.CONTAINMENT_TERMINATED:
            if self.containment_status != ContainmentStatus.TERMINATED:
                raise ValueError("CONTAINMENT_TERMINATION_REQUIRES_TERMINATED_STATUS")
        if self.termination_reason == TerminationReason.UNRECOVERABLE_RUNTIME_FAILURE:
            if self.technical_exclusion_status != TechnicalExclusionStatus.EXCLUDED:
                raise ValueError("RUNTIME_FAILURE_REQUIRES_TECHNICAL_EXCLUSION")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class EpisodeRecorder:
    """Record one episode using explicit events and one immutable limit envelope.

    ``update`` is the only transition operation. Explicit task, containment, and
    runtime signals are evaluated before automatic turn/message/timeout limits;
    ties therefore have a stable documented precedence. Counts are incremented
    before evaluating the boundary, so the terminal event records the triggering
    turn or message.
    """

    def __init__(self, limits: EpisodeLimits, started_at: float = 0.0):
        self.limits = limits
        self.started_at = _nonnegative_float(started_at, "started_at")
        self.turn_count = 0
        self.message_count = 0
        self._metadata: EpisodeMetadata | None = None

    @property
    def terminated(self) -> bool:
        return self._metadata is not None

    @property
    def metadata(self) -> EpisodeMetadata | None:
        return self._metadata

    def update(
        self,
        now: float,
        *,
        turns: int = 0,
        messages: int = 0,
        task_completed: bool = False,
        task_failed_final: bool = False,
        containment_terminal: bool = False,
        runtime_failure: bool = False,
        containment_status: ContainmentStatus = ContainmentStatus.INACTIVE,
    ) -> EpisodeMetadata | None:
        if self.terminated:
            raise RuntimeError("EPISODE_ALREADY_TERMINATED")
        now = _nonnegative_float(now, "now")
        if now < self.started_at:
            raise ValueError("EPISODE_CLOCK_REGRESSION")
        turns = _nonnegative_int(turns, "turns")
        messages = _nonnegative_int(messages, "messages")
        if (
            sum(
                bool(value)
                for value in (
                    task_completed,
                    task_failed_final,
                    containment_terminal,
                    runtime_failure,
                )
            )
            > 1
        ):
            raise ValueError("CONFLICTING_TERMINALS")
        self.turn_count += turns
        self.message_count += messages
        duration = now - self.started_at
        reason: TerminationReason | None = None
        task_status = TaskCompletionStatus.INCOMPLETE
        technical_status = TechnicalExclusionStatus.NONE
        final_containment = containment_status
        if runtime_failure:
            reason = TerminationReason.UNRECOVERABLE_RUNTIME_FAILURE
            technical_status = TechnicalExclusionStatus.EXCLUDED
        elif task_completed:
            reason = TerminationReason.TASK_COMPLETED
            task_status = TaskCompletionStatus.COMPLETED
        elif task_failed_final:
            reason = TerminationReason.TASK_FAILED_FINAL
            task_status = TaskCompletionStatus.FAILED
        elif containment_terminal:
            reason = TerminationReason.CONTAINMENT_TERMINATED
            final_containment = ContainmentStatus.TERMINATED
        elif self.turn_count >= self.limits.max_agent_turns:
            reason = TerminationReason.MAX_AGENT_TURNS_REACHED
        elif self.message_count >= self.limits.max_messages_per_episode:
            reason = TerminationReason.MAX_MESSAGES_REACHED
        elif duration >= self.limits.episode_timeout_seconds:
            reason = TerminationReason.EPISODE_TIMEOUT
        if reason is None:
            return None
        self._metadata = EpisodeMetadata(
            reason,
            self.turn_count,
            self.message_count,
            duration,
            task_status,
            final_containment,
            technical_status,
        )
        return self._metadata


def frozen_limits(record: dict[str, Any]) -> EpisodeLimits:
    """Validate a provider freeze before an analytic adapter may start.

    Calibration records are intentionally separate from this gate. A pending
    template, a missing limit, or a changed cohort cannot accidentally become an
    analytic run.
    """

    required = {
        "provider_run_id",
        "provider",
        "model",
        "model_freeze_status",
        "amendment_id",
        "analytic_seed_count",
        "episodes_per_provider",
        "max_agent_turns",
        "max_messages_per_episode",
        "episode_timeout_seconds",
        "calibration",
        "review",
        "termination_rules",
        "lock",
    }
    if not isinstance(record, dict) or set(record) != required:
        raise ValueError("INVALID_MODEL_FREEZE_FIELDS")
    if record["amendment_id"] != "HELM-P1-AMEND-002":
        raise ValueError("WRONG_AMENDMENT")
    if record["model_freeze_status"] != "LOCKED":
        raise ValueError("MODEL_FREEZE_NOT_LOCKED")
    if record["analytic_seed_count"] != 20 or record["episodes_per_provider"] != 240:
        raise ValueError("FROZEN_COHORT_MISMATCH")
    if not all(
        isinstance(record[key], str) and record[key]
        for key in ("provider_run_id", "provider", "model")
    ):
        raise ValueError("INVALID_PROVIDER_IDENTITY")
    if record["max_agent_turns"] is None or record["max_messages_per_episode"] is None:
        raise ValueError("UNSET_EPISODE_LIMIT")
    calibration = record["calibration"]
    if not isinstance(calibration, dict) or calibration.get("instrumentation_only") is not True:
        raise ValueError("CALIBRATION_NOT_INSTRUMENTATION_ONLY")
    if not calibration.get("limit_selection_rationale"):
        raise ValueError("MISSING_CALIBRATION_RATIONALE")
    review = record["review"]
    if not isinstance(review, dict) or review.get("advisory_only") is not True:
        raise ValueError("AI_REVIEW_NOT_ADVISORY")
    if review.get("independent_validation_claim") is not False:
        raise ValueError("INDEPENDENCE_CLAIM_FORBIDDEN")
    if review.get("human_final_adjudication") != "REQUIRED":
        raise ValueError("HUMAN_ADJUDICATION_REQUIRED")
    same_family_disclosed = review.get("same_family_limitation_disclosed")
    if type(same_family_disclosed) is not bool:
        raise ValueError("SAME_FAMILY_LIMITATION_DISCLOSURE_REQUIRED")
    if "ANT-SONNET5" in record["provider_run_id"] and not same_family_disclosed:
        raise ValueError("SAME_FAMILY_LIMITATION_UNDISCLOSED")
    if record["termination_rules"] != [reason.value for reason in TerminationReason]:
        raise ValueError("TERMINATION_RULES_NOT_FROZEN")
    lock = record["lock"]
    if not isinstance(lock, dict) or lock.get("status") != "LOCKED":
        raise ValueError("LOCK_RECORD_NOT_LOCKED")
    return EpisodeLimits(
        record["max_agent_turns"],
        record["max_messages_per_episode"],
        record["episode_timeout_seconds"],
    )
