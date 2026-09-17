"""Direct-GBNF llama.cpp chat adapter with conservative error classification."""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from helm.adapters.base import (
    ConstraintMode,
    LocalModelAdapter,
    ParseStatus,
    RuntimeMetadata,
    SamplingParameters,
    StructuredResponseResult,
)
from helm.structured_output.parser import parse_json_output
from helm.structured_output.validation import validate_agent_response

GRAMMAR_VERSION = "agent_response.v1"
DEFAULT_GRAMMAR_PATH = (
    Path(__file__).resolve().parents[1]
    / "structured_output"
    / "grammars"
    / "agent_response.v1.gbnf"
)

# This is the observed semantic signature, kept in one place so a pinned
# llama.cpp wording change requires one localized update.
LLAMA_CPP_CONSTRAINT_ERROR_SIGNATURE = (
    "failed to initialize samplers",
    "unexpected empty grammar stack",
)


def grammar_sha256(path: Path = DEFAULT_GRAMMAR_PATH) -> str:
    """Return the SHA-256 of the exact grammar bytes on disk."""

    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# Filled from the committed grammar bytes; changing the file requires an
# explicit runtime-artifact update rather than silently accepting mutation.
GRAMMAR_SHA256 = "0615c3e026f681603b6c7f5f3d9c5a8b79b6bc06fca8bed921810a339c648d80"


def _load_grammar(path: Path, expected_sha256: str | None) -> tuple[str, str]:
    raw = Path(path).read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if expected_sha256 is not None and actual != expected_sha256:
        raise ValueError("GRAMMAR_HASH_MISMATCH")
    return raw.decode("utf-8"), actual


def _transport_error_text(error: BaseException, reason: BaseException | None = None) -> str:
    """Preserve both the wrapper and concrete low-level transport exception."""

    details = f"{type(error).__name__}: {error}"
    if reason is not None and reason is not error:
        details += f" (reason {type(reason).__name__}: {reason})"
    return details


def _error_message(error_body: str | bytes | Mapping[str, Any]) -> str | None:
    if isinstance(error_body, Mapping):
        value: Any = error_body
    else:
        try:
            value = json.loads(
                error_body.decode("utf-8") if isinstance(error_body, bytes) else error_body
            )
        except (TypeError, UnicodeDecodeError, json.JSONDecodeError):
            return None
    error = value.get("error") if isinstance(value, Mapping) else None
    message = error.get("message") if isinstance(error, Mapping) else None
    return message if isinstance(message, str) else None


def classify_llama_cpp_server_error(
    http_status: int, error_body: str | bytes | Mapping[str, Any]
) -> ParseStatus:
    """Classify only the known HTTP-400 llama.cpp constrained-decoding failure.

    Generic client errors, unknown future wording, and every non-400 response
    remain ``SERVER_ERROR``. Model names and token IDs are deliberately ignored.
    """

    if http_status != 400:
        return ParseStatus.SERVER_ERROR
    message = _error_message(error_body)
    if message is None:
        return ParseStatus.SERVER_ERROR
    normalized = " ".join(message.casefold().split())
    if all(signature in normalized for signature in LLAMA_CPP_CONSTRAINT_ERROR_SIGNATURE):
        return ParseStatus.CONSTRAINT_FAILURE
    return ParseStatus.SERVER_ERROR


@dataclass(frozen=True)
class TransportResponse:
    status_code: int
    body: bytes | str


Transport = Callable[[str, bytes, float], TransportResponse]


def _default_transport(endpoint: str, payload: bytes, timeout_seconds: float) -> TransportResponse:
    request = Request(
        endpoint,
        data=payload,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 - configured local endpoint
            return TransportResponse(response.status, response.read())
    except HTTPError as error:
        return TransportResponse(error.code, error.read())


class LlamaCppAdapter(LocalModelAdapter):
    """Call llama-server chat completions with direct GBNF and no free-text fallback."""

    def __init__(
        self,
        *,
        endpoint: str = "http://127.0.0.1:8080",
        model: str,
        runtime_metadata: RuntimeMetadata | None = None,
        grammar_path: Path = DEFAULT_GRAMMAR_PATH,
        grammar_version: str = GRAMMAR_VERSION,
        expected_grammar_sha256: str | None = GRAMMAR_SHA256,
        sampling_defaults: SamplingParameters | None = None,
        timeout_seconds: float = 30.0,
        transport: Transport | None = None,
    ):
        self.endpoint = endpoint.rstrip("/")
        if not self.endpoint.endswith("/v1/chat/completions"):
            self.endpoint += "/v1/chat/completions"
        self.model = model
        self.runtime_metadata = runtime_metadata or RuntimeMetadata(model=model)
        self.grammar_path = Path(grammar_path)
        self.grammar_version = grammar_version
        self.grammar_text, self.grammar_sha256 = _load_grammar(
            self.grammar_path, expected_grammar_sha256
        )
        self.sampling_defaults = sampling_defaults or SamplingParameters()
        if timeout_seconds <= 0:
            raise ValueError("INVALID_TIMEOUT")
        self.timeout_seconds = timeout_seconds
        self._transport = transport or _default_transport

    def _result(
        self,
        *,
        raw_output: str | None,
        http_status: int | None,
        parse_status: ParseStatus,
        parse_error: str | None,
        parsed_payload: Any | None,
        schema_validation_result: dict[str, Any],
        sampling: SamplingParameters,
        timeout_seconds: float,
        elapsed_ms: float,
        model: str,
    ) -> StructuredResponseResult:
        metadata = self.runtime_metadata
        return StructuredResponseResult(
            raw_output=raw_output,
            http_status=http_status,
            parse_status=parse_status,
            parse_error=parse_error,
            parsed_payload=parsed_payload,
            schema_validation_result=schema_validation_result,
            model_id=model,
            model_file_sha256=metadata.model_file_sha256,
            llama_cpp_commit=metadata.llama_cpp_commit,
            grammar_version=self.grammar_version,
            grammar_sha256=self.grammar_sha256,
            temperature=sampling.temperature,
            top_p=sampling.top_p,
            top_k=sampling.top_k,
            min_p=sampling.min_p,
            seed=sampling.seed,
            max_tokens=sampling.max_tokens,
            timeout_seconds=timeout_seconds,
            endpoint=self.endpoint,
            constraint_mode=ConstraintMode.DIRECT_GBNF,
            elapsed_ms=elapsed_ms,
            context=sampling.context,
            reasoning=sampling.reasoning,
            runtime_metadata=metadata.to_dict(),
            transport_attempts=1,
        )

    @staticmethod
    def _content_from_server_payload(value: Any) -> str | None:
        if not isinstance(value, Mapping):
            return None
        choices = value.get("choices")
        if not isinstance(choices, list) or not choices:
            return None
        first = choices[0]
        if not isinstance(first, Mapping):
            return None
        message = first.get("message")
        if not isinstance(message, Mapping):
            return None
        content = message.get("content")
        return content if isinstance(content, str) else None

    def generate_structured_response(
        self,
        messages: Sequence[dict[str, Any]],
        *,
        model: str | None = None,
        sampling: SamplingParameters | None = None,
        timeout_seconds: float | None = None,
    ) -> StructuredResponseResult:
        """Send exactly one constrained request and validate its response independently."""

        selected_model = model or self.model
        selected_sampling = sampling or self.sampling_defaults
        selected_timeout = self.timeout_seconds if timeout_seconds is None else timeout_seconds
        if selected_timeout <= 0:
            raise ValueError("INVALID_TIMEOUT")
        payload = {
            "model": selected_model,
            "messages": list(messages),
            "temperature": selected_sampling.temperature,
            "top_p": selected_sampling.top_p,
            "top_k": selected_sampling.top_k,
            "min_p": selected_sampling.min_p,
            "seed": selected_sampling.seed,
            "max_tokens": selected_sampling.max_tokens,
            "grammar": self.grammar_text,
        }
        request_body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode(
            "utf-8"
        )
        started = time.monotonic()
        try:
            response = self._transport(self.endpoint, request_body, selected_timeout)
        except TimeoutError as error:
            error_text = _transport_error_text(error)
            return self._result(
                raw_output=None,
                http_status=None,
                parse_status=ParseStatus.TIMEOUT,
                parse_error=error_text,
                parsed_payload=None,
                schema_validation_result={"valid": False, "errors": ["TIMEOUT"]},
                sampling=selected_sampling,
                timeout_seconds=selected_timeout,
                elapsed_ms=(time.monotonic() - started) * 1000,
                model=selected_model,
            )
        except URLError as error:
            reason = error.reason
            if isinstance(reason, TimeoutError):
                status = ParseStatus.TIMEOUT
            else:
                status = ParseStatus.SERVER_ERROR
            error_text = _transport_error_text(error, reason)
            return self._result(
                raw_output=error_text,
                http_status=None,
                parse_status=status,
                parse_error=error_text,
                parsed_payload=None,
                schema_validation_result={"valid": False, "errors": [status.value]},
                sampling=selected_sampling,
                timeout_seconds=selected_timeout,
                elapsed_ms=(time.monotonic() - started) * 1000,
                model=selected_model,
            )
        except OSError as error:
            error_text = _transport_error_text(error)
            return self._result(
                raw_output=error_text,
                http_status=None,
                parse_status=ParseStatus.SERVER_ERROR,
                parse_error=error_text,
                parsed_payload=None,
                schema_validation_result={"valid": False, "errors": ["SERVER_ERROR"]},
                sampling=selected_sampling,
                timeout_seconds=selected_timeout,
                elapsed_ms=(time.monotonic() - started) * 1000,
                model=selected_model,
            )
        elapsed_ms = (time.monotonic() - started) * 1000
        body = (
            response.body.decode("utf-8", errors="replace")
            if isinstance(response.body, bytes)
            else response.body
        )
        if not 200 <= response.status_code < 300:
            status = classify_llama_cpp_server_error(response.status_code, body)
            return self._result(
                raw_output=body,
                http_status=response.status_code,
                parse_status=status,
                parse_error=f"HTTP_{response.status_code}",
                parsed_payload=None,
                schema_validation_result={"valid": False, "errors": [status.value]},
                sampling=selected_sampling,
                timeout_seconds=selected_timeout,
                elapsed_ms=elapsed_ms,
                model=selected_model,
            )
        if not body.strip():
            return self._result(
                raw_output=body,
                http_status=response.status_code,
                parse_status=ParseStatus.EMPTY_OUTPUT,
                parse_error="EMPTY_OUTPUT",
                parsed_payload=None,
                schema_validation_result={"valid": False, "errors": ["EMPTY_OUTPUT"]},
                sampling=selected_sampling,
                timeout_seconds=selected_timeout,
                elapsed_ms=elapsed_ms,
                model=selected_model,
            )
        try:
            envelope = json.loads(body)
        except (TypeError, json.JSONDecodeError) as error:
            return self._result(
                raw_output=body,
                http_status=response.status_code,
                parse_status=ParseStatus.INVALID_JSON,
                parse_error=str(error),
                parsed_payload=None,
                schema_validation_result={"valid": False, "errors": ["INVALID_JSON"]},
                sampling=selected_sampling,
                timeout_seconds=selected_timeout,
                elapsed_ms=elapsed_ms,
                model=selected_model,
            )
        raw_output = self._content_from_server_payload(envelope)
        if raw_output is None:
            return self._result(
                raw_output=body,
                http_status=response.status_code,
                parse_status=ParseStatus.EMPTY_OUTPUT,
                parse_error="EMPTY_OUTPUT",
                parsed_payload=None,
                schema_validation_result={"valid": False, "errors": ["EMPTY_OUTPUT"]},
                sampling=selected_sampling,
                timeout_seconds=selected_timeout,
                elapsed_ms=elapsed_ms,
                model=selected_model,
            )
        parsed = parse_json_output(raw_output)
        if parsed.status is not None:
            return self._result(
                raw_output=raw_output,
                http_status=response.status_code,
                parse_status=parsed.status,
                parse_error=parsed.error,
                parsed_payload=None,
                schema_validation_result={"valid": False, "errors": [parsed.status.value]},
                sampling=selected_sampling,
                timeout_seconds=selected_timeout,
                elapsed_ms=elapsed_ms,
                model=selected_model,
            )
        validation = validate_agent_response(parsed.payload)
        status = ParseStatus.VALID_DIRECT if validation.valid else ParseStatus.SCHEMA_MISMATCH
        return self._result(
            raw_output=raw_output,
            http_status=response.status_code,
            parse_status=status,
            parse_error=None if validation.valid else ";".join(validation.errors),
            parsed_payload=parsed.payload,
            schema_validation_result=validation.to_dict(),
            sampling=selected_sampling,
            timeout_seconds=selected_timeout,
            elapsed_ms=elapsed_ms,
            model=selected_model,
        )
