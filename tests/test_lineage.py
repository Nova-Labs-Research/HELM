import json
import shutil
import tempfile
import unittest
from pathlib import Path

from helm.phase1 import (
    EXPECTED_PREREGISTRATION_HASHES,
    PREREGISTRATION_LINEAGE,
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

    def test_complete_four_artifact_lineage_validates(self):
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

    def test_incorrect_artifact_hash(self):
        root = self.make_materialized_root()
        lineage = expected_lineage()
        lineage[2]["sha256"] = "0" * 64
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


if __name__ == "__main__":
    unittest.main()
