"""Small contracts shared by local model adapters and their result records."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any, Protocol


class ParseStatus(StrEnum):
    """Finite, fail-closed statuses for one structured model request."""

    VALID_DIRECT = "VALID_DIRECT"
    INVALID_JSON = "INVALID_JSON"
    SCHEMA_MISMATCH = "SCHEMA_MISMATCH"
    EMPTY_OUTPUT = "EMPTY_OUTPUT"
    SERVER_ERROR = "SERVER_ERROR"
    CONSTRAINT_FAILURE = "CONSTRAINT_FAILURE"
    TIMEOUT = "TIMEOUT"


class ConstraintMode(StrEnum):
    """The only constrained chat mode supported by this first local adapter."""

    DIRECT_GBNF = "DIRECT_GBNF"


@dataclass(frozen=True)
class SamplingParameters:
    """Instrumentation defaults; these values are not Phase 1 frozen limits."""

    seed: int = 23
    temperature: float = 0.0
    top_k: int = 1
    top_p: float = 1.0
    min_p: float = 0.0
    max_tokens: int = 160
    context: int = 2048
    reasoning: str = "off"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RuntimeMetadata:
    """Explicit local-runtime provenance, with unavailable values left null."""

    model: str
    provider: str = "LOCAL_LLAMA_CPP"
    backend: str | None = "VULKAN"
    device: str | None = None
    quantization: str | None = None
    model_file: str | None = None
    model_file_sha256: str | None = None
    llama_cpp_commit: str | None = None
    gpu_layers: int | str | None = None
    context_size: int | None = 2048

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StructuredResponseResult:
    """Observable result for one adapter request; raw output is never discarded."""

    raw_output: str | None
    http_status: int | None
    parse_status: ParseStatus
    parse_error: str | None
    parsed_payload: Any | None
    schema_validation_result: dict[str, Any]
    model_id: str
    model_file_sha256: str | None
    llama_cpp_commit: str | None
    grammar_version: str
    grammar_sha256: str
    temperature: float
    top_p: float
    top_k: int
    min_p: float
    seed: int
    max_tokens: int
    timeout_seconds: float
    endpoint: str
    constraint_mode: ConstraintMode
    elapsed_ms: float
    context: int
    reasoning: str
    runtime_metadata: dict[str, Any]
    transport_attempts: int
    instrumentation_only: bool = True
    analytic_use: str = "FORBIDDEN"

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["parse_status"] = self.parse_status.value
        value["constraint_mode"] = self.constraint_mode.value
        return value


class LocalModelAdapter(Protocol):
    """Provider-agnostic shape used by future runtime integrations."""

    def generate_structured_response(
        self,
        messages: Sequence[dict[str, Any]],
        *,
        model: str | None = None,
        sampling: SamplingParameters | None = None,
        timeout_seconds: float | None = None,
    ) -> StructuredResponseResult: ...
