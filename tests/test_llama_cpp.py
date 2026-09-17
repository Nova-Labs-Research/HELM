import json
import tempfile
import unittest
from pathlib import Path
from urllib.error import URLError

from helm.adapters.base import ConstraintMode, ParseStatus, RuntimeMetadata, SamplingParameters
from helm.adapters.llama_cpp import (
    DEFAULT_GRAMMAR_PATH,
    GRAMMAR_SHA256,
    GRAMMAR_VERSION,
    LlamaCppAdapter,
    TransportResponse,
    classify_llama_cpp_server_error,
    grammar_sha256,
)


def success_body(content: str) -> bytes:
    return json.dumps({"choices": [{"message": {"content": content}}]}).encode()


class FakeTransport:
    def __init__(self, response: TransportResponse):
        self.response = response
        self.calls: list[tuple[str, bytes, float]] = []

    def __call__(self, endpoint: str, payload: bytes, timeout: float) -> TransportResponse:
        self.calls.append((endpoint, payload, timeout))
        return self.response


def adapter_for(response: TransportResponse) -> tuple[LlamaCppAdapter, FakeTransport]:
    transport = FakeTransport(response)
    return (
        LlamaCppAdapter(model="granite-test", transport=transport),
        transport,
    )


class LlamaCppClassificationTests(unittest.TestCase):
    def test_captured_empty_grammar_stack_shape_is_constraint_failure(self):
        body = {
            "error": {
                "code": 400,
                "message": (
                    "Failed to initialize samplers: Unexpected empty grammar stack after "
                    "accepting piece: <|start_of_role|> (49152)"
                ),
                "type": "invalid_request_error",
            }
        }
        self.assertEqual(classify_llama_cpp_server_error(400, body), ParseStatus.CONSTRAINT_FAILURE)

    def test_qwen_token_is_not_a_special_case(self):
        body = {
            "error": {
                "code": 400,
                "message": (
                    "Failed to initialize samplers: Unexpected empty grammar stack after "
                    "accepting piece: <|im_start|> (151644)"
                ),
                "type": "invalid_request_error",
            }
        }
        self.assertEqual(
            classify_llama_cpp_server_error(400, json.dumps(body)), ParseStatus.CONSTRAINT_FAILURE
        )

    def test_malformed_request_is_server_error(self):
        body = {"error": {"code": 400, "message": "Malformed request payload"}}
        self.assertEqual(classify_llama_cpp_server_error(400, body), ParseStatus.SERVER_ERROR)

    def test_http_500_is_server_error(self):
        body = {"error": {"code": 500, "message": "Unexpected server failure"}}
        self.assertEqual(classify_llama_cpp_server_error(500, body), ParseStatus.SERVER_ERROR)

    def test_unknown_future_http_400_is_server_error(self):
        body = {"error": {"code": 400, "message": "A new llama.cpp error wording"}}
        self.assertEqual(classify_llama_cpp_server_error(400, body), ParseStatus.SERVER_ERROR)

    def test_non_json_error_body_is_server_error(self):
        self.assertEqual(
            classify_llama_cpp_server_error(400, b"Failed to initialize samplers: not JSON"),
            ParseStatus.SERVER_ERROR,
        )


class LlamaCppAdapterTests(unittest.TestCase):
    def test_allow_deny_review_are_accepted_and_raw_text_preserved(self):
        for action in ("ALLOW", "DENY", "REVIEW"):
            with self.subTest(action=action):
                raw = json.dumps({"action": action, "reason": "keep this exact text"}, indent=2)
                adapter, transport = adapter_for(TransportResponse(200, success_body(raw)))
                result = adapter.generate_structured_response([{"role": "user", "content": "test"}])
                self.assertEqual(result.parse_status, ParseStatus.VALID_DIRECT)
                self.assertEqual(result.raw_output, raw)
                self.assertEqual(result.parsed_payload["action"], action)
                self.assertTrue(result.schema_validation_result["valid"])
                self.assertEqual(len(transport.calls), 1)

    def test_runtime_metadata_and_direct_grammar_are_recorded(self):
        adapter, transport = adapter_for(
            TransportResponse(200, success_body('{"action":"ALLOW","reason":"ok"}'))
        )
        adapter.runtime_metadata = RuntimeMetadata(
            model="granite-test",
            backend="VULKAN",
            quantization="Q3_K_L",
            llama_cpp_commit="fb27a525d28381a16a4bb038858a10e4927381ca",
        )
        sampling = SamplingParameters(seed=7, temperature=0.2, top_k=4, top_p=0.9, min_p=0.1)
        result = adapter.generate_structured_response([], sampling=sampling, timeout_seconds=12)
        sent = json.loads(transport.calls[0][1])
        self.assertEqual(result.grammar_version, GRAMMAR_VERSION)
        self.assertEqual(result.grammar_sha256, GRAMMAR_SHA256)
        self.assertEqual(result.constraint_mode, ConstraintMode.DIRECT_GBNF)
        self.assertEqual(result.llama_cpp_commit, "fb27a525d28381a16a4bb038858a10e4927381ca")
        self.assertEqual(result.seed, 7)
        self.assertEqual(result.context, 2048)
        self.assertEqual(result.runtime_metadata["quantization"], "Q3_K_L")
        self.assertIsNone(result.runtime_metadata["device"])
        self.assertIsNone(result.runtime_metadata["gpu_layers"])
        self.assertEqual(result.timeout_seconds, 12)
        self.assertEqual(result.transport_attempts, 1)
        self.assertIn("grammar", sent)
        self.assertNotIn("response_format", sent)

    def test_http_400_constraint_failure_does_not_fallback(self):
        body = {
            "error": {
                "code": 400,
                "message": "Failed to initialize samplers: Unexpected empty grammar stack",
                "type": "invalid_request_error",
            }
        }
        adapter, transport = adapter_for(TransportResponse(400, json.dumps(body)))
        result = adapter.generate_structured_response([])
        self.assertEqual(result.parse_status, ParseStatus.CONSTRAINT_FAILURE)
        self.assertEqual(len(transport.calls), 1)
        self.assertIn("grammar", json.loads(transport.calls[0][1]))

    def test_generic_http_400_is_server_error_and_body_is_preserved(self):
        body = '{"error":{"code":400,"message":"Unsupported parameter"}}'
        adapter, transport = adapter_for(TransportResponse(400, body))
        result = adapter.generate_structured_response([])
        self.assertEqual(result.parse_status, ParseStatus.SERVER_ERROR)
        self.assertEqual(result.raw_output, body)
        self.assertEqual(len(transport.calls), 1)

    def test_http_500_is_server_error(self):
        adapter, _ = adapter_for(TransportResponse(500, b"internal failure"))
        self.assertEqual(
            adapter.generate_structured_response([]).parse_status, ParseStatus.SERVER_ERROR
        )

    def test_timeout_is_explicit_and_no_retry_occurs(self):
        calls = 0

        def timeout_transport(
            _endpoint: str, _payload: bytes, _timeout: float
        ) -> TransportResponse:
            nonlocal calls
            calls += 1
            raise TimeoutError("timed out")

        adapter = LlamaCppAdapter(model="granite-test", transport=timeout_transport)
        result = adapter.generate_structured_response([])
        self.assertEqual(result.parse_status, ParseStatus.TIMEOUT)
        self.assertEqual(calls, 1)

    def test_transport_exception_class_and_message_are_preserved(self):
        concrete = ConnectionRefusedError(10061, "connection refused")

        def failing_transport(
            _endpoint: str, _payload: bytes, _timeout: float
        ) -> TransportResponse:
            raise URLError(concrete)

        adapter = LlamaCppAdapter(model="granite-test", transport=failing_transport)
        result = adapter.generate_structured_response([])
        self.assertEqual(result.parse_status, ParseStatus.SERVER_ERROR)
        self.assertIn("URLError", result.parse_error)
        self.assertIn("ConnectionRefusedError", result.parse_error)
        self.assertIn("connection refused", result.parse_error)
        self.assertEqual(result.transport_attempts, 1)

    def test_empty_body_is_empty_output(self):
        adapter, _ = adapter_for(TransportResponse(200, b""))
        self.assertEqual(
            adapter.generate_structured_response([]).parse_status, ParseStatus.EMPTY_OUTPUT
        )

    def test_malformed_model_json_is_invalid_json(self):
        adapter, _ = adapter_for(TransportResponse(200, success_body("not json")))
        self.assertEqual(
            adapter.generate_structured_response([]).parse_status, ParseStatus.INVALID_JSON
        )

    def test_application_validation_does_not_trust_enabled_grammar(self):
        raw = '{"action":"ALLOW","reason":3}'
        adapter, transport = adapter_for(TransportResponse(200, success_body(raw)))
        result = adapter.generate_structured_response([])
        self.assertEqual(result.parse_status, ParseStatus.SCHEMA_MISMATCH)
        self.assertEqual(result.parsed_payload, {"action": "ALLOW", "reason": 3})
        self.assertIn("grammar", json.loads(transport.calls[0][1]))

    def test_missing_invalid_and_unexpected_fields_are_schema_mismatch(self):
        for value in (
            {"reason": "missing action"},
            {"action": "MAYBE", "reason": "invalid enum"},
            {"action": "ALLOW"},
            {"action": "ALLOW", "reason": "ok", "extra": True},
        ):
            with self.subTest(value=value):
                adapter, _ = adapter_for(TransportResponse(200, success_body(json.dumps(value))))
                result = adapter.generate_structured_response([])
                self.assertEqual(result.parse_status, ParseStatus.SCHEMA_MISMATCH)
                self.assertFalse(result.schema_validation_result["valid"])

    def test_grammar_hash_is_exact_and_mutation_is_rejected(self):
        self.assertEqual(grammar_sha256(), GRAMMAR_SHA256)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / DEFAULT_GRAMMAR_PATH.name
            path.write_bytes(DEFAULT_GRAMMAR_PATH.read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "GRAMMAR_HASH_MISMATCH"):
                LlamaCppAdapter(model="granite-test", grammar_path=path)


if __name__ == "__main__":
    unittest.main()
