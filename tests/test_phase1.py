import unittest

from helm.phase1 import (
    BEHAVIOR_DEFINITION_VERSION,
    FROZEN_REPLAY_INPUTS,
    ContainmentStatus,
    EpisodeLimits,
    EpisodeMetadata,
    EpisodeRecorder,
    TaskCompletionStatus,
    TechnicalExclusionStatus,
    TerminationReason,
    behavior_definition_sha256,
    frozen_limits,
    load_behavior_definitions,
    validate_behavior_definitions,
    validate_frozen_replay_inputs,
    validate_replay_configuration,
    validate_replay_report_language,
)


class EpisodeRecorderTests(unittest.TestCase):
    def setUp(self):
        self.limits = EpisodeLimits(
            max_agent_turns=3,
            max_messages_per_episode=5,
            episode_timeout_seconds=10.0,
        )

    def test_limits_are_strict_and_positive(self):
        for changes in (
            {"max_agent_turns": 0},
            {"max_messages_per_episode": -1},
            {"episode_timeout_seconds": 0},
            {"episode_timeout_seconds": float("inf")},
            {"max_agent_turns": True},
        ):
            values = self.limits.to_dict()
            values.update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                EpisodeLimits(**values)

    def test_turn_and_message_boundaries_record_triggering_counts(self):
        recorder = EpisodeRecorder(self.limits)
        self.assertIsNone(recorder.update(1, turns=1, messages=2))
        metadata = recorder.update(2, turns=2, messages=1)
        self.assertEqual(metadata.termination_reason, TerminationReason.MAX_AGENT_TURNS_REACHED)
        self.assertEqual(metadata.final_turn_count, 3)
        self.assertEqual(metadata.final_message_count, 3)
        with self.assertRaises(RuntimeError):
            recorder.update(3, messages=1)

        recorder = EpisodeRecorder(self.limits)
        metadata = recorder.update(1, messages=5)
        self.assertEqual(metadata.termination_reason, TerminationReason.MAX_MESSAGES_REACHED)

    def test_timeout_uses_injected_clock_and_no_wall_clock_sampling(self):
        recorder = EpisodeRecorder(self.limits, started_at=100.0)
        self.assertIsNone(recorder.update(109.99))
        metadata = recorder.update(110.0)
        self.assertEqual(metadata.termination_reason, TerminationReason.EPISODE_TIMEOUT)
        self.assertEqual(metadata.wall_clock_duration, 10.0)
        with self.assertRaises(ValueError):
            EpisodeRecorder(self.limits, started_at=2).update(1)

    def test_explicit_completion_and_failure_are_observed(self):
        recorder = EpisodeRecorder(self.limits)
        metadata = recorder.update(1, turns=1, task_completed=True)
        self.assertEqual(metadata.termination_reason, TerminationReason.TASK_COMPLETED)
        self.assertEqual(metadata.task_completion_status, TaskCompletionStatus.COMPLETED)
        self.assertEqual(metadata.technical_exclusion_status, TechnicalExclusionStatus.NONE)

        recorder = EpisodeRecorder(self.limits)
        metadata = recorder.update(1, task_failed_final=True)
        self.assertEqual(metadata.termination_reason, TerminationReason.TASK_FAILED_FINAL)
        self.assertEqual(metadata.task_completion_status, TaskCompletionStatus.FAILED)

    def test_containment_and_runtime_failure_metadata(self):
        recorder = EpisodeRecorder(self.limits)
        metadata = recorder.update(
            1,
            containment_terminal=True,
            containment_status=ContainmentStatus.ACTIVE,
        )
        self.assertEqual(metadata.termination_reason, TerminationReason.CONTAINMENT_TERMINATED)
        self.assertEqual(metadata.containment_status, ContainmentStatus.TERMINATED)
        self.assertEqual(metadata.technical_exclusion_status, TechnicalExclusionStatus.NONE)

        recorder = EpisodeRecorder(self.limits)
        metadata = recorder.update(1, runtime_failure=True)
        self.assertEqual(
            metadata.termination_reason, TerminationReason.UNRECOVERABLE_RUNTIME_FAILURE
        )
        self.assertEqual(metadata.technical_exclusion_status, TechnicalExclusionStatus.EXCLUDED)

    def test_boundary_precedence_is_frozen_and_conflicts_rejected(self):
        recorder = EpisodeRecorder(self.limits)
        metadata = recorder.update(10, turns=3, task_completed=True)
        self.assertEqual(metadata.termination_reason, TerminationReason.TASK_COMPLETED)
        for kwargs in (
            {"task_completed": True, "task_failed_final": True},
            {"runtime_failure": True, "containment_terminal": True},
            {"runtime_failure": True, "task_completed": True},
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    EpisodeRecorder(self.limits).update(1, **kwargs)

    def test_metadata_validation_and_serialization(self):
        metadata = EpisodeMetadata(
            TerminationReason.MAX_MESSAGES_REACHED,
            2,
            5,
            1.25,
            TaskCompletionStatus.INCOMPLETE,
            ContainmentStatus.INACTIVE,
            TechnicalExclusionStatus.NONE,
        )
        self.assertEqual(
            metadata.to_dict()["termination_reason"], TerminationReason.MAX_MESSAGES_REACHED
        )
        with self.assertRaises(ValueError):
            EpisodeMetadata(
                TerminationReason.CONTAINMENT_TERMINATED,
                0,
                0,
                0,
                TaskCompletionStatus.INCOMPLETE,
                ContainmentStatus.ACTIVE,
                TechnicalExclusionStatus.NONE,
            )
        with self.assertRaises(ValueError):
            EpisodeMetadata(
                TerminationReason.UNRECOVERABLE_RUNTIME_FAILURE,
                0,
                0,
                0,
                TaskCompletionStatus.INCOMPLETE,
                ContainmentStatus.INACTIVE,
                TechnicalExclusionStatus.NONE,
            )

    def test_unlocked_freeze_is_rejected(self):
        import json
        from pathlib import Path

        template = json.loads(
            (
                Path(__file__).parents[1] / "docs/preregistration/model_freeze.template.json"
            ).read_text()
        )
        with self.assertRaises(ValueError) as error:
            frozen_limits(template)
        self.assertEqual(str(error.exception), "MODEL_FREEZE_NOT_LOCKED")

    def test_locked_freeze_requires_disclosure_and_calibration(self):
        artifact_hash = behavior_definition_sha256()
        record = {
            "provider_run_id": "run-1",
            "provider": "synthetic",
            "model": "test-model",
            "model_freeze_status": "LOCKED",
            "amendment_id": "HELM-P1-AMEND-002",
            "analytic_seed_count": 20,
            "episodes_per_provider": 240,
            "max_agent_turns": 10,
            "max_messages_per_episode": 20,
            "episode_timeout_seconds": 60.0,
            "behavior_definition_version": BEHAVIOR_DEFINITION_VERSION,
            "behavior_definition_sha256": artifact_hash,
            "replay_mode": "GOVERNANCE_ONLY",
            "full_model_regeneration_required": False,
            "deterministic_governance_replay_required": True,
            "frozen_replay_inputs": list(FROZEN_REPLAY_INPUTS),
            "calibration": {
                "instrumentation_only": True,
                "limit_selection_rationale": "Enough room for ordinary fixture completion.",
            },
            "review": {
                "advisory_only": True,
                "independent_validation_claim": False,
                "human_final_adjudication": "REQUIRED",
                "same_family_limitation_disclosed": True,
            },
            "termination_rules": [reason.value for reason in TerminationReason],
            "lock": {"status": "LOCKED"},
        }
        limits = frozen_limits(record)
        self.assertEqual(limits.max_agent_turns, 10)
        record["review"]["same_family_limitation_disclosed"] = False
        record["provider_run_id"] = "HELM-P1-OTHER-PROVIDER"
        self.assertEqual(frozen_limits(record).max_agent_turns, 10)
        record["provider_run_id"] = "HELM-P1-RAISE-SCOURGE-002-ANT-SONNET5"
        with self.assertRaises(ValueError):
            frozen_limits(record)


class SemanticReplayTests(unittest.TestCase):
    def test_behavior_artifact_is_independently_versioned_and_hashed(self):
        artifact = load_behavior_definitions()
        self.assertEqual(artifact["behavior_definition_version"], 1)
        self.assertEqual(len(artifact["definitions"]), 7)
        self.assertEqual(len(behavior_definition_sha256(artifact)), 64)
        self.assertEqual(behavior_definition_sha256(artifact), behavior_definition_sha256())
        validate_behavior_definitions(artifact)

    def test_behavior_artifact_mismatch_and_missing_file_fail(self):
        artifact = load_behavior_definitions()
        for mutation in (
            {"behavior_definition_version": 2},
            {"definitions": artifact["definitions"][:-1]},
        ):
            changed = {**artifact, **mutation}
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                validate_behavior_definitions(changed)
        from pathlib import Path

        with self.assertRaises(ValueError):
            load_behavior_definitions(Path("does-not-exist/behavior_definitions.json"))

    def test_normalized_replay_inputs_are_required(self):
        valid = {name: [] for name in FROZEN_REPLAY_INPUTS}
        valid["behavior_definition_version"] = BEHAVIOR_DEFINITION_VERSION
        validate_frozen_replay_inputs(valid)
        for missing in FROZEN_REPLAY_INPUTS:
            changed = {**valid}
            del changed[missing]
            with self.subTest(missing=missing), self.assertRaises(ValueError):
                validate_frozen_replay_inputs(changed)
        changed = {**valid, "behavior_definition_version": 2}
        with self.assertRaises(ValueError):
            validate_frozen_replay_inputs(changed)

    def test_replay_configuration_rejects_regeneration_and_hash_changes(self):
        base = {
            "behavior_definition_version": 1,
            "behavior_definition_sha256": behavior_definition_sha256(),
            "replay_mode": "GOVERNANCE_ONLY",
            "full_model_regeneration_required": False,
            "deterministic_governance_replay_required": True,
            "frozen_replay_inputs": list(FROZEN_REPLAY_INPUTS),
        }
        validate_replay_configuration(base)
        for field, value in (
            ("behavior_definition_version", 2),
            ("behavior_definition_sha256", "0" * 64),
            ("replay_mode", "MODEL_REGENERATION"),
            ("full_model_regeneration_required", True),
            ("deterministic_governance_replay_required", False),
            ("frozen_replay_inputs", list(FROZEN_REPLAY_INPUTS[:-1])),
        ):
            changed = {**base, field: value}
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_replay_configuration(changed)

    def test_runtime_classifier_must_match_frozen_definition(self):
        record = {
            "provider_run_id": "run-1",
            "provider": "synthetic",
            "model": "test-model",
            "model_freeze_status": "LOCKED",
            "amendment_id": "HELM-P1-AMEND-002",
            "analytic_seed_count": 20,
            "episodes_per_provider": 240,
            "max_agent_turns": 10,
            "max_messages_per_episode": 20,
            "episode_timeout_seconds": 60.0,
            "behavior_definition_version": 1,
            "behavior_definition_sha256": behavior_definition_sha256(),
            "replay_mode": "GOVERNANCE_ONLY",
            "full_model_regeneration_required": False,
            "deterministic_governance_replay_required": True,
            "frozen_replay_inputs": list(FROZEN_REPLAY_INPUTS),
            "calibration": {
                "instrumentation_only": True,
                "limit_selection_rationale": "Enough room for ordinary fixture completion.",
            },
            "review": {
                "advisory_only": True,
                "independent_validation_claim": False,
                "human_final_adjudication": "REQUIRED",
                "same_family_limitation_disclosed": True,
            },
            "termination_rules": [reason.value for reason in TerminationReason],
            "lock": {"status": "LOCKED"},
        }
        with self.assertRaises(ValueError):
            frozen_limits(record, runtime_behavior_definition_version=2)
        with self.assertRaises(ValueError):
            frozen_limits(record, runtime_behavior_definition_hash="0" * 64)

    def test_governance_only_report_cannot_claim_full_exact_replay(self):
        validate_replay_report_language(
            "Deterministic governance replay reproduced all decisions exactly."
        )
        with self.assertRaises(ValueError):
            validate_replay_report_language("The full Phase 1 experiment replayed exactly.")
        with self.assertRaises(ValueError):
            validate_replay_report_language("Identical model regeneration is required.")

    def test_cosmetic_documentation_is_outside_semantic_hash(self):
        import json
        from pathlib import Path

        artifact = json.loads(
            (
                Path(__file__).parents[1] / "docs/preregistration/behavior_definitions.v1.json"
            ).read_text()
        )
        before = behavior_definition_sha256(artifact)
        markdown = (Path(__file__).parents[1] / "docs/BEHAVIOR_DEFINITIONS.md").read_text()
        self.assertEqual(before, behavior_definition_sha256(artifact))
        self.assertTrue(markdown)


if __name__ == "__main__":
    unittest.main()
