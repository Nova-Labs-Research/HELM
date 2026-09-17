"""Independent application-level validation for the minimal adapter contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

ALLOWED_ACTIONS = frozenset({"ALLOW", "DENY", "REVIEW"})
EXPECTED_FIELDS = frozenset({"action", "reason"})


@dataclass(frozen=True)
class SchemaValidationResult:
    valid: bool
    errors: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"valid": self.valid, "errors": list(self.errors)}


def validate_agent_response(value: Any) -> SchemaValidationResult:
    """Validate the object independently of whether GBNF was enabled."""

    errors: list[str] = []
    if not isinstance(value, dict):
        return SchemaValidationResult(False, ("OBJECT_REQUIRED",))
    missing = sorted(EXPECTED_FIELDS - value.keys())
    unexpected = sorted(value.keys() - EXPECTED_FIELDS)
    errors.extend(f"MISSING_{field.upper()}" for field in missing)
    errors.extend(f"UNEXPECTED_{field.upper()}" for field in unexpected)
    if "action" in value and value["action"] not in ALLOWED_ACTIONS:
        errors.append("INVALID_ACTION")
    if "reason" in value and not isinstance(value["reason"], str):
        errors.append("INVALID_REASON_TYPE")
    return SchemaValidationResult(not errors, tuple(errors))
