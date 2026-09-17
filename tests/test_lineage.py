import json
import shutil
import tempfile
import unittest
from pathlib import Path

from helm.phase1 import (
    CLOUD_PROVIDER_EXPERIMENT_IDS,
    EXPECTED_PREREGISTRATION_HASHES,
    LOCAL_PROVIDER_EXPERIMENT_IDS,
    PREREGISTRATION_LINEAGE,
    behavior_definition_sha256,
    canonical_json_sha256,
    validate_preregistration_lineage,
    validate_preregistration_lock_status,
)

ROOT = Path(__file__).resolve().parents[1]


def expected_lineage() -> list[dict[str, str]]:
    return [
        {"id": identifier, "sha256": EXPECTED_PREREGISTRATION_HASHES[identifier]}
        for identifier, _ in PREREGISTRATION_LINEAGE
    ]


class PreregistrationLineageTests(unittest.TestCase):
    def make_materialized_root(self) -> Path:
        temporary = Path(tempfile.mkdtemp(prefix="helm-lineage-"))
        self.addCleanup(shutil.rmtree, temporary)
        (temporary / "docs/preregistration").mkdir(parents=True)
        for _, relative_path in PREREGISTRATION_LINEAGE:
            source = ROOT / relative_path
            target = temporary / relative_path
            shutil.copy2(source, target)
        return temporary

    def test_complete_five_artifact_lineage_validates(self):
        root = self.make_materialized_root()
        actual = validate_preregistration_lineage(expected_lineage(), root=root)
        self.assertEqual(
            [item["id"] for item in actual], [item["id"] for item in expected_lineage()]
        )
        self.assertEqual(actual, expected_lineage())

    def test_missing_original_preregistration_artifact(self):
        root = self.make_materialized_root()
        (root / "docs/preregistration/HELM-P1-RAISE-SCOURGE.json").unlink()
        with self.assertRaisesRegex(ValueError, "PREREGISTRATION_ARTIFACT_MISSING"):
            validate_preregistration_lineage(expected_lineage(), root=root)

    def test_missing_amendment_001_artifact(self):
        root = self.make_materialized_root()
        (root / "docs/preregistration/HELM-P1-AMEND-001.json").unlink()
        with self.assertRaisesRegex(ValueError, "PREREGISTRATION_ARTIFACT_MISSING"):
            validate_preregistration_lineage(expected_lineage(), root=root)

    def test_missing_amendment_004_artifact(self):
        root = self.make_materialized_root()
        (root / "docs/preregistration/HELM-P1-AMEND-004.json").unlink()
        with self.assertRaisesRegex(ValueError, "PREREGISTRATION_ARTIFACT_MISSING"):
            validate_preregistration_lineage(expected_lineage(), root=root)

    def test_incorrect_artifact_hash(self):
        root = self.make_materialized_root()
        lineage = expected_lineage()
        lineage[2]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "PREREGISTRATION_HASH_MISMATCH"):
            validate_preregistration_lineage(lineage, root=root)

    def test_incorrect_amendment_004_hash(self):
        root = self.make_materialized_root()
        lineage = expected_lineage()
        lineage[-1]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "PREREGISTRATION_HASH_MISMATCH"):
            validate_preregistration_lineage(lineage, root=root)

    def test_reordered_chain(self):
        root = self.make_materialized_root()
        lineage = expected_lineage()
        lineage[1], lineage[2] = lineage[2], lineage[1]
        with self.assertRaisesRegex(ValueError, "AMENDMENT_CHAIN_INCOMPLETE"):
            validate_preregistration_lineage(lineage, root=root)

    def test_missing_chain_member(self):
        root = self.make_materialized_root()
        lineage = expected_lineage()[:-1]
        with self.assertRaisesRegex(ValueError, "AMENDMENT_CHAIN_INCOMPLETE"):
            validate_preregistration_lineage(lineage, root=root)

    def test_broken_parent_or_prior_amendment_link(self):
        root = self.make_materialized_root()
        path = root / "docs/preregistration/HELM-P1-AMEND-002.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["prior_amendment"] = "HELM-P1-AMEND-003"
        path.write_text(json.dumps(value), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "PREREGISTRATION_PARENT_RELATIONSHIP_INVALID"):
            validate_preregistration_lineage(expected_lineage(), root=root)

    def test_broken_amendment_004_prior_amendments_link(self):
        root = self.make_materialized_root()
        path = root / "docs/preregistration/HELM-P1-AMEND-004.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["prior_amendments"] = ["HELM-P1-AMEND-001", "HELM-P1-AMEND-003"]
        path.write_text(json.dumps(value), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "PREREGISTRATION_PARENT_RELATIONSHIP_INVALID"):
            validate_preregistration_lineage(expected_lineage(), root=root)

    def test_amendment_004_identity_and_runtime_fields(self):
        path = ROOT / "docs/preregistration/HELM-P1-AMEND-004.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(value["amendment_id"], "HELM-P1-AMEND-004")
        self.assertEqual(value["parent_preregistration"], "HELM-P1-RAISE-SCOURGE")
        self.assertEqual(
            value["prior_amendments"],
            [
                "HELM-P1-AMEND-001",
                "HELM-P1-AMEND-002",
                "HELM-P1-AMEND-003",
            ],
        )
        self.assertEqual(value["status"], "PROPOSED")
        self.assertEqual(value["local_runtime"]["provider"], "LOCAL_LLAMA_CPP")
        self.assertEqual(value["local_runtime"]["model"], "Granite 3.1 8B Instruct")
        self.assertEqual(value["local_runtime"]["quantization"], "Q3_K_L")
        self.assertEqual(
            value["local_runtime"]["model_file_sha256"],
            "3c24bb01ed1181cb936a9f03c41f1fd3341555ea68086a4b81713a137c765eb6",
        )
        self.assertEqual(value["local_runtime"]["backend"], "VULKAN")
        self.assertEqual(value["local_runtime"]["device"], "Vulkan1")
        self.assertEqual(value["local_runtime"]["llama_cpp_version"], "0.4.1-dev")
        self.assertEqual(
            value["local_runtime"]["llama_cpp_commit"],
            "fb27a525d28381a16a4bb038858a10e4927381ca",
        )
        self.assertEqual(value["local_runtime"]["endpoint"], "/v1/chat/completions")
        self.assertEqual(value["local_runtime"]["constraint_mode"], "DIRECT_GBNF")
        self.assertEqual(value["local_runtime"]["grammar_version"], "agent_response.v1")
        self.assertEqual(
            value["local_runtime"]["grammar_sha256"],
            "0615c3e026f681603b6c7f5f3d9c5a8b79b6bc06fca8bed921810a339c648d80",
        )
        self.assertEqual(
            value["local_runtime"]["silent_fallback_to_unconstrained_text"], "FORBIDDEN"
        )

    def test_amendment_004_model_file_location_is_filename_only(self):
        path = ROOT / "docs/preregistration/HELM-P1-AMEND-004.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        location = value["local_runtime"]["model_file_location"]
        self.assertNotIn("\\", location)
        self.assertNotIn("/", location)
        self.assertNotIn(":", location)
        self.assertEqual(location, "granite-3.1-8b-instruct-Q3_K_L.gguf")

    def test_amendment_004_lock_requirements_field_is_unambiguously_named(self):
        path = ROOT / "docs/preregistration/HELM-P1-AMEND-004.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        lock_requirements = value["lock_requirements"]
        self.assertNotIn("amendment_status", lock_requirements)
        self.assertEqual(lock_requirements["required_amendment_status_for_analytic_lock"], "LOCKED")

    def test_amendment_004_sequence_separates_instrumentation_calibration_execution(self):
        path = ROOT / "docs/preregistration/HELM-P1-AMEND-004.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        sequence = value["local_first_sequence"]
        self.assertEqual(
            sequence,
            [
                "LOCAL_GRANITE_BASELINE",
                "LOCAL_INSTRUMENTATION_VALIDATION",
                "LOCAL_CALIBRATION",
                "LOCAL_BASELINE_EXECUTION_AFTER_REQUIRED_LOCKS",
                "CLOUD_PROVIDER_EXECUTION",
                "OPENAI_LUNA",
                "ANTHROPIC_SONNET5",
            ],
        )
        self.assertNotIn("LOCAL_INSTRUMENTATION_CALIBRATION_BASELINE_EXECUTION", sequence)

    def test_local_provider_ids_are_additive_and_cloud_ids_unchanged(self):
        self.assertEqual(
            CLOUD_PROVIDER_EXPERIMENT_IDS,
            {
                "HELM-P1-CAL-001-OAI-LUNA",
                "HELM-P1-RAISE-SCOURGE-001-OAI-LUNA",
                "HELM-P1-RAISE-SCOURGE-002-ANT-SONNET5",
            },
        )
        self.assertEqual(
            LOCAL_PROVIDER_EXPERIMENT_IDS,
            {
                "HELM-P1-CAL-001-LOCAL-GRANITE31-8B",
                "HELM-P1-RAISE-SCOURGE-001-LOCAL-GRANITE31-8B",
            },
        )
        self.assertTrue(CLOUD_PROVIDER_EXPERIMENT_IDS.isdisjoint(LOCAL_PROVIDER_EXPERIMENT_IDS))

    def test_earlier_amendment_hashes_remain_unchanged(self):
        self.assertEqual(
            {
                key: EXPECTED_PREREGISTRATION_HASHES[key]
                for key in (
                    "HELM-P1-RAISE-SCOURGE",
                    "HELM-P1-AMEND-001",
                    "HELM-P1-AMEND-002",
                    "HELM-P1-AMEND-003",
                )
            },
            {
                "HELM-P1-RAISE-SCOURGE": (
                    "acddfe9978d2e81d2fb36b6a9a51423cdd901804f8ef34f0747fced25342a0a9"
                ),
                "HELM-P1-AMEND-001": (
                    "b49b8b8668f7c07952ea2629bd7a8e8bd4eb8137f719f0e8193d291e6c15ba8c"
                ),
                "HELM-P1-AMEND-002": (
                    "b7713ac02ce35e531ca36692bb71425a8cade083476c4c8b0245a67d6f3af0bb"
                ),
                "HELM-P1-AMEND-003": (
                    "6ccadd28d96b74973cb5122e6fd730cde678edd208d53883a12adee11efbdf32"
                ),
            },
        )

    def test_behavior_definition_hash_remains_unchanged(self):
        self.assertEqual(
            behavior_definition_sha256(),
            "b242631c6aed1dc87d70d394f55890330d69661085e0de805af1e6c915de935a",
        )

    def test_hashes_are_canonical_json_hashes(self):
        root = self.make_materialized_root()
        for identifier, relative_path in PREREGISTRATION_LINEAGE:
            self.assertEqual(
                canonical_json_sha256(root / relative_path),
                EXPECTED_PREREGISTRATION_HASHES[identifier],
            )


class PreregistrationLockStatusTests(unittest.TestCase):
    """``validate_preregistration_lock_status`` is deliberately hash-independent:
    it reads each document's own lock signal, not its content hash, so these
    tests may freely mutate status fields without colliding with the pinned
    ``EXPECTED_PREREGISTRATION_HASHES`` used by the lineage/hash tests above.
    """

    def make_locked_root(self) -> Path:
        temporary = Path(tempfile.mkdtemp(prefix="helm-lock-status-"))
        self.addCleanup(shutil.rmtree, temporary)
        (temporary / "docs/preregistration").mkdir(parents=True)
        for identifier, relative_path in PREREGISTRATION_LINEAGE:
            value = json.loads((ROOT / relative_path).read_text(encoding="utf-8"))
            if identifier == "HELM-P1-RAISE-SCOURGE":
                value["preregistration_lock_fields"]["PREREGISTRATION_STATUS"] = "LOCKED"
            else:
                value["status"] = "LOCKED"
            (temporary / relative_path).write_text(json.dumps(value), encoding="utf-8")
        return temporary

    def test_current_repository_documents_are_not_yet_locked(self):
        with self.assertRaisesRegex(ValueError, "PREREGISTRATION_ARTIFACT_NOT_LOCKED"):
            validate_preregistration_lock_status()

    def test_fully_locked_copy_passes(self):
        root = self.make_locked_root()
        validate_preregistration_lock_status(root=root)

    def test_original_preregistration_uses_its_own_nested_lock_field(self):
        root = self.make_locked_root()
        path = root / "docs/preregistration/HELM-P1-RAISE-SCOURGE.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["preregistration_lock_fields"]["PREREGISTRATION_STATUS"] = "PREREGISTERED_DESIGN"
        path.write_text(json.dumps(value), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "PREREGISTRATION_ARTIFACT_NOT_LOCKED"):
            validate_preregistration_lock_status(root=root)

    def test_a_single_still_proposed_amendment_blocks_the_whole_chain(self):
        for relative_path in (
            "docs/preregistration/HELM-P1-AMEND-001.json",
            "docs/preregistration/HELM-P1-AMEND-002.json",
            "docs/preregistration/HELM-P1-AMEND-003.json",
            "docs/preregistration/HELM-P1-AMEND-004.json",
        ):
            with self.subTest(relative_path=relative_path):
                root = self.make_locked_root()
                path = root / relative_path
                value = json.loads(path.read_text(encoding="utf-8"))
                value["status"] = "PROPOSED"
                path.write_text(json.dumps(value), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "PREREGISTRATION_ARTIFACT_NOT_LOCKED"):
                    validate_preregistration_lock_status(root=root)

    def test_missing_document_is_reported_as_missing_not_unlocked(self):
        root = self.make_locked_root()
        (root / "docs/preregistration/HELM-P1-AMEND-002.json").unlink()
        with self.assertRaisesRegex(ValueError, "PREREGISTRATION_ARTIFACT_MISSING"):
            validate_preregistration_lock_status(root=root)


class PrecalReadinessGateTests(unittest.TestCase):
    def test_gate_references_complete_five_artifact_lineage(self):
        gate = ROOT / "docs/PHASE_1_PRECAL_READINESS.md"
        text = gate.read_text(encoding="utf-8")
        for identifier in (
            "HELM-P1-RAISE-SCOURGE",
            "HELM-P1-AMEND-001",
            "HELM-P1-AMEND-002",
            "HELM-P1-AMEND-003",
            "HELM-P1-AMEND-004",
        ):
            with self.subTest(identifier=identifier):
                self.assertIn(identifier, text)


if __name__ == "__main__":
    unittest.main()
