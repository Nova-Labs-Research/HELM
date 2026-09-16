import unittest

from helm.phase1 import (
    ContainmentStatus,
    EpisodeLimits,
    EpisodeMetadata,
    EpisodeRecorder,
    TaskCompletionStatus,
    TechnicalExclusionStatus,
    TerminationReason,
    frozen_limits,
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


if __name__ == "__main__":
    unittest.main()
