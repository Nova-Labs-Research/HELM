"""Provider-neutral Phase 1 episode envelope and termination metadata.

This module does not call a model or classify behavior. It records only observable
episode boundaries so a later provider adapter can apply one frozen envelope to all
episodes in that provider run.
"""

import hashlib
import json
from dataclasses import asdict, dataclass
from enum import StrEnum
from math import isfinite
from pathlib import Path
from typing import Any

from helm.schema import canonical

BEHAVIOR_DEFINITION_VERSION = 1
AMENDMENT_CHAIN = (
    "HELM-P1-AMEND-001",
    "HELM-P1-AMEND-002",
    "HELM-P1-AMEND-003",
    "HELM-P1-AMEND-004",
)
LATEST_AMENDMENT_ID = AMENDMENT_CHAIN[-1]
CLOUD_PROVIDER_EXPERIMENT_IDS = frozenset(
    {
        "HELM-P1-CAL-001-OAI-LUNA",
        "HELM-P1-RAISE-SCOURGE-001-OAI-LUNA",
        "HELM-P1-RAISE-SCOURGE-002-ANT-SONNET5",
    }
)
LOCAL_PROVIDER_EXPERIMENT_IDS = frozenset(
    {
        "HELM-P1-CAL-001-LOCAL-GRANITE31-8B",
        "HELM-P1-RAISE-SCOURGE-001-LOCAL-GRANITE31-8B",
    }
)
DEFAULT_BEHAVIOR_DEFINITION_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "preregistration"
    / "behavior_definitions.v1.json"
)
FROZEN_REPLAY_INPUTS = (
    "normalized_agent_outputs",
    "normalized_messages",
    "requested_actions",
    "authority_claims",
    "tool_intents",
    "fixture_state",
    "policy_state",
    "identity_state",
    "governance_configuration",
    "behavior_definition_version",
)
PREREGISTRATION_LINEAGE = (
    ("HELM-P1-RAISE-SCOURGE", "docs/preregistration/HELM-P1-RAISE-SCOURGE.json"),
    ("HELM-P1-AMEND-001", "docs/preregistration/HELM-P1-AMEND-001.json"),
    ("HELM-P1-AMEND-002", "docs/preregistration/HELM-P1-AMEND-002.json"),
    ("HELM-P1-AMEND-003", "docs/preregistration/HELM-P1-AMEND-003.json"),
    ("HELM-P1-AMEND-004", "docs/preregistration/HELM-P1-AMEND-004.json"),
)
EXPECTED_PREREGISTRATION_HASHES = {
    "HELM-P1-RAISE-SCOURGE": "acddfe9978d2e81d2fb36b6a9a51423cdd901804f8ef34f0747fced25342a0a9",
    "HELM-P1-AMEND-001": "b49b8b8668f7c07952ea2629bd7a8e8bd4eb8137f719f0e8193d291e6c15ba8c",
    "HELM-P1-AMEND-002": "b7713ac02ce35e531ca36692bb71425a8cade083476c4c8b0245a67d6f3af0bb",
    "HELM-P1-AMEND-003": "6ccadd28d96b74973cb5122e6fd730cde678edd208d53883a12adee11efbdf32",
    "HELM-P1-AMEND-004": "1857efbd6cfdf9299883ad8ff44d02068688b9cf57a7f7d1f5b961c0dd40527a",
}


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


class ReplayMode(StrEnum):
    GOVERNANCE_ONLY = "GOVERNANCE_ONLY"
    MODEL_REGENERATION = "MODEL_REGENERATION"
    END_TO_END_RERUN = "END_TO_END_RERUN"


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


def _nonempty_text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"INVALID_{name.upper()}")
    return value


def validate_behavior_definitions(artifact: Any) -> dict[str, Any]:
    """Validate the semantic artifact independently of Markdown presentation."""

    required = {"behavior_definition_version", "definitions"}
    if not isinstance(artifact, dict) or set(artifact) != required:
        raise ValueError("INVALID_BEHAVIOR_DEFINITION_FIELDS")
    if artifact["behavior_definition_version"] != BEHAVIOR_DEFINITION_VERSION:
        raise ValueError("BEHAVIOR_DEFINITION_VERSION_MISMATCH")
    definitions = artifact["definitions"]
    if not isinstance(definitions, list) or len(definitions) != 7:
        raise ValueError("INVALID_BEHAVIOR_DEFINITION_COUNT")
    required_item = {
        "id",
        "version",
        "definition",
        "required_evidence",
        "excluded_evidence",
        "persistence_required",
        "coordination_required",
        "deterministic_preconditions",
    }
    expected_ids = {
        "ROLE_DRIFT",
        "AUTHORITY_CLAIM",
        "POLICY_REINTERPRETATION",
        "COALITION_LIKE",
        "SUPERVISOR_SUBSTITUTION",
        "BREAK_FREE_CANDIDATE",
        "STRONG_BREAK_FREE_EVENT",
    }
    seen: set[str] = set()
    for item in definitions:
        if not isinstance(item, dict) or set(item) != required_item:
            raise ValueError("INVALID_BEHAVIOR_DEFINITION_ITEM_FIELDS")
        identifier = _nonempty_text(item["id"], "behavior_id")
        if identifier in seen or identifier not in expected_ids:
            raise ValueError("INVALID_BEHAVIOR_DEFINITION_ID")
        seen.add(identifier)
        if item["version"] != BEHAVIOR_DEFINITION_VERSION:
            raise ValueError("BEHAVIOR_DEFINITION_ITEM_VERSION_MISMATCH")
        _nonempty_text(item["definition"], "behavior_definition")
        for field in ("required_evidence", "excluded_evidence", "deterministic_preconditions"):
            values = item[field]
            if (
                not isinstance(values, list)
                or not values
                or any(not isinstance(value, str) or not value for value in values)
            ):
                raise ValueError(f"INVALID_{field.upper()}")
        for field in ("persistence_required", "coordination_required"):
            if type(item[field]) is not bool:
                raise ValueError(f"INVALID_{field.upper()}")
    if seen != expected_ids:
        raise ValueError("MISSING_BEHAVIOR_DEFINITION")
    return artifact


def load_behavior_definitions(path: Path = DEFAULT_BEHAVIOR_DEFINITION_PATH) -> dict[str, Any]:
    try:
        artifact = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("BEHAVIOR_DEFINITION_ARTIFACT_UNAVAILABLE") from error
    return validate_behavior_definitions(artifact)


def behavior_definition_sha256(artifact: dict[str, Any] | None = None) -> str:
    """Hash canonical semantic JSON; Markdown and JSON formatting are excluded."""

    validated = validate_behavior_definitions(
        load_behavior_definitions() if artifact is None else artifact
    )
    return hashlib.sha256(canonical(validated).encode("utf-8")).hexdigest()


def canonical_json_sha256(path: Path) -> str:
    """Hash a JSON artifact by canonical content, independent of whitespace."""

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("PREREGISTRATION_ARTIFACT_MISSING") from error
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def _artifact_identifier(value: dict[str, Any]) -> str | None:
    identifier = value.get("preregistration_id")
    if identifier is None:
        identifier = value.get("amendment_id")
    return identifier if isinstance(identifier, str) else None


def validate_preregistration_lineage(
    lineage: Any | None = None,
    *,
    root: Path | None = None,
) -> list[dict[str, str]]:
    """Validate the five materialized preregistration artifacts and their chain."""

    root = Path(__file__).resolve().parents[1] if root is None else Path(root)
    actual: list[dict[str, str]] = []
    documents: dict[str, dict[str, Any]] = {}
    for expected_id, relative_path in PREREGISTRATION_LINEAGE:
        path = root / relative_path
        if not path.is_file():
            raise ValueError("PREREGISTRATION_ARTIFACT_MISSING")
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError("PREREGISTRATION_ARTIFACT_MISSING") from error
        identifier = _artifact_identifier(value)
        if identifier != expected_id:
            raise ValueError("PREREGISTRATION_ID_MISMATCH")
        documents[expected_id] = value
        actual.append({"id": expected_id, "sha256": canonical_json_sha256(path)})
    original = documents["HELM-P1-RAISE-SCOURGE"]
    amend_001 = documents["HELM-P1-AMEND-001"]
    amend_002 = documents["HELM-P1-AMEND-002"]
    amend_003 = documents["HELM-P1-AMEND-003"]
    if any(
        key in original for key in ("parent_preregistration", "prior_amendment", "prior_amendments")
    ):
        raise ValueError("PREREGISTRATION_PARENT_RELATIONSHIP_INVALID")
    if amend_001.get("parent_preregistration") != "HELM-P1-RAISE-SCOURGE":
        raise ValueError("PREREGISTRATION_PARENT_RELATIONSHIP_INVALID")
    if (
        amend_002.get("parent_preregistration") != "HELM-P1-RAISE-SCOURGE"
        or amend_002.get("prior_amendment") != "HELM-P1-AMEND-001"
    ):
        raise ValueError("PREREGISTRATION_PARENT_RELATIONSHIP_INVALID")
    if amend_003.get("parent_preregistration") != "HELM-P1-RAISE-SCOURGE" or amend_003.get(
        "prior_amendments"
    ) != ["HELM-P1-AMEND-001", "HELM-P1-AMEND-002"]:
        raise ValueError("PREREGISTRATION_PARENT_RELATIONSHIP_INVALID")
    amend_004 = documents["HELM-P1-AMEND-004"]
    if amend_004.get("parent_preregistration") != "HELM-P1-RAISE-SCOURGE" or amend_004.get(
        "prior_amendments"
    ) != [
        "HELM-P1-AMEND-001",
        "HELM-P1-AMEND-002",
        "HELM-P1-AMEND-003",
    ]:
        raise ValueError("PREREGISTRATION_PARENT_RELATIONSHIP_INVALID")
    for item in actual:
        if item["sha256"] != EXPECTED_PREREGISTRATION_HASHES[item["id"]]:
            raise ValueError("PREREGISTRATION_HASH_MISMATCH")
    if lineage is None:
        return actual
    if not isinstance(lineage, list) or len(lineage) != len(PREREGISTRATION_LINEAGE):
        raise ValueError("AMENDMENT_CHAIN_INCOMPLETE")
    normalized: list[dict[str, str]] = []
    for item in lineage:
        if not isinstance(item, dict) or set(item) != {"id", "sha256"}:
            raise ValueError("AMENDMENT_CHAIN_INCOMPLETE")
        if not isinstance(item["id"], str) or not isinstance(item["sha256"], str):
            raise ValueError("AMENDMENT_CHAIN_INCOMPLETE")
        normalized.append({"id": item["id"], "sha256": item["sha256"]})
    if [item["id"] for item in normalized] != [item["id"] for item in actual]:
        raise ValueError("AMENDMENT_CHAIN_INCOMPLETE")
    for expected, provided in zip(actual, normalized, strict=True):
        if provided["sha256"] != expected["sha256"]:
            raise ValueError("PREREGISTRATION_HASH_MISMATCH")
    return actual


def _document_is_locked(identifier: str, value: dict[str, Any]) -> bool:
    """Read each document's own lock signal in the vocabulary it actually uses.

    The original preregistration predates the amendment convention and already
    carries a populated ``preregistration_lock_fields.PREREGISTRATION_STATUS``
    (locked with Phase 0). Amendments use a top-level ``status`` that starts as
    ``PROPOSED`` and must be explicitly edited to ``LOCKED`` before an analytic
    run may reference it. Neither vocabulary is invented here; both already
    exist in the materialized documents.
    """

    if identifier == "HELM-P1-RAISE-SCOURGE":
        lock_fields = value.get("preregistration_lock_fields")
        return (
            isinstance(lock_fields, dict) and lock_fields.get("PREREGISTRATION_STATUS") == "LOCKED"
        )
    return value.get("status") == "LOCKED"


def validate_preregistration_lock_status(root: Path | None = None) -> None:
    """Require every lineage document to show itself as locked, not just correct.

    This is independent of ``validate_preregistration_lineage``: a document can
    be the exact, unaltered, hash-verified artifact and still be ``PROPOSED``.
    Content correctness and lock status are separate invariants with separate
    failure modes, so they get separate checks and separate error codes.
    """

    root = Path(__file__).resolve().parents[1] if root is None else Path(root)
    for expected_id, relative_path in PREREGISTRATION_LINEAGE:
        path = root / relative_path
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError("PREREGISTRATION_ARTIFACT_MISSING") from error
        if not _document_is_locked(expected_id, value):
            raise ValueError("PREREGISTRATION_ARTIFACT_NOT_LOCKED")


def validate_frozen_replay_inputs(
    inputs: Any, behavior_version: int = BEHAVIOR_DEFINITION_VERSION
) -> None:
    """Require the normalized artifacts consumed by governance-only replay."""

    if not isinstance(inputs, dict) or not set(FROZEN_REPLAY_INPUTS) <= set(inputs):
        raise ValueError("MISSING_NORMALIZED_REPLAY_INPUTS")
    if inputs["behavior_definition_version"] != behavior_version:
        raise ValueError("REPLAY_BEHAVIOR_DEFINITION_VERSION_MISMATCH")


def validate_replay_configuration(
    record: dict[str, Any], artifact: dict[str, Any] | None = None
) -> None:
    """Validate the replay semantics required by Amendment 003."""

    expected_hash = behavior_definition_sha256(artifact)
    if record.get("behavior_definition_version") != BEHAVIOR_DEFINITION_VERSION:
        raise ValueError("BEHAVIOR_DEFINITION_VERSION_MISMATCH")
    if record.get("behavior_definition_sha256") != expected_hash:
        raise ValueError("BEHAVIOR_DEFINITION_HASH_MISMATCH")
    if record.get("replay_mode") != ReplayMode.GOVERNANCE_ONLY:
        raise ValueError("REPLAY_MUST_BE_GOVERNANCE_ONLY")
    if record.get("full_model_regeneration_required") is not False:
        raise ValueError("FULL_MODEL_REGENERATION_FORBIDDEN")
    if record.get("deterministic_governance_replay_required") is not True:
        raise ValueError("DETERMINISTIC_GOVERNANCE_REPLAY_REQUIRED")
    inputs = record.get("frozen_replay_inputs")
    if inputs != list(FROZEN_REPLAY_INPUTS):
        raise ValueError("FROZEN_REPLAY_INPUTS_MISMATCH")


def validate_replay_report_language(
    report: str, mode: ReplayMode = ReplayMode.GOVERNANCE_ONLY
) -> None:
    """Prevent a governance-only report from claiming model regeneration."""

    if not isinstance(report, str):
        raise ValueError("INVALID_REPLAY_REPORT")
    normalized = " ".join(report.upper().split())
    if mode == ReplayMode.GOVERNANCE_ONLY and (
        "FULL PHASE 1 EXPERIMENT REPLAYED EXACTLY" in normalized
        or "IDENTICAL MODEL REGENERATION" in normalized
    ):
        raise ValueError("REPLAY_REPORT_OVERCLAIMS_MODEL_REGENERATION")


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


def frozen_limits(
    record: dict[str, Any],
    artifact: dict[str, Any] | None = None,
    *,
    runtime_behavior_definition_version: int | None = None,
    runtime_behavior_definition_hash: str | None = None,
    preregistration_root: Path | None = None,
) -> EpisodeLimits:
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
        "behavior_definition_version",
        "behavior_definition_sha256",
        "replay_mode",
        "full_model_regeneration_required",
        "deterministic_governance_replay_required",
        "frozen_replay_inputs",
        "preregistration_lineage",
    }
    if not isinstance(record, dict) or not required <= set(record):
        raise ValueError("INVALID_MODEL_FREEZE_FIELDS")
    unexpected = set(record) - required
    if unexpected != set() and unexpected != {"amendment_chain"}:
        raise ValueError("INVALID_MODEL_FREEZE_FIELDS")
    if record["amendment_id"] != LATEST_AMENDMENT_ID:
        raise ValueError("WRONG_AMENDMENT")
    if "amendment_chain" in record and record["amendment_chain"] != list(AMENDMENT_CHAIN):
        raise ValueError("AMENDMENT_CHAIN_INCOMPLETE")
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
    validate_preregistration_lineage(record["preregistration_lineage"], root=preregistration_root)
    validate_preregistration_lock_status(root=preregistration_root)
    validate_replay_configuration(record, artifact)
    if runtime_behavior_definition_version is not None:
        if runtime_behavior_definition_version != record["behavior_definition_version"]:
            raise ValueError("RUNTIME_BEHAVIOR_DEFINITION_VERSION_MISMATCH")
    if runtime_behavior_definition_hash is not None:
        if runtime_behavior_definition_hash != record["behavior_definition_sha256"]:
            raise ValueError("RUNTIME_BEHAVIOR_DEFINITION_HASH_MISMATCH")
    return EpisodeLimits(
        record["max_agent_turns"],
        record["max_messages_per_episode"],
        record["episode_timeout_seconds"],
    )
