from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from render_program_status import render  # noqa: E402
from validate_program import (  # noqa: E402
    COMPLETION_GATES,
    DEFAULT_EXPERIMENTS,
    DEFAULT_REGISTRY,
    load_json,
    validate,
)


class ProgramRegistryValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = load_json(DEFAULT_REGISTRY)
        self.experiments = load_json(DEFAULT_EXPERIMENTS)

    def errors_for(self, registry=None, experiments=None):
        return validate(registry or self.registry, experiments or self.experiments)

    def test_authoritative_registries_are_valid(self):
        self.assertEqual(self.errors_for(), [])

    def test_gearbox_is_the_twentieth_repository(self):
        self.assertEqual(len(self.registry["repositories"]), 20)
        gearbox = next(
            item for item in self.registry["repositories"]
            if item["name"] == "gearbox"
        )
        self.assertEqual(gearbox["lifecycle_stage"], "PROTOTYPED")
        self.assertEqual(
            gearbox["last_verified_head_sha"],
            self.registry["gearbox_publication"]["final_main_sha"],
        )

    def test_missing_expected_repository_fails(self):
        registry = copy.deepcopy(self.registry)
        registry["repositories"].pop()
        errors = self.errors_for(registry=registry)
        self.assertTrue(any("missing repositories" in error for error in errors))

    def test_duplicate_repository_fails(self):
        registry = copy.deepcopy(self.registry)
        registry["repositories"][-1] = copy.deepcopy(registry["repositories"][0])
        errors = self.errors_for(registry=registry)
        self.assertTrue(any("duplicate repositories" in error for error in errors))

    def test_malformed_repository_name_reports_error(self):
        registry = copy.deepcopy(self.registry)
        registry["repositories"][0]["name"] = ["not", "a", "string"]
        errors = self.errors_for(registry=registry)
        self.assertTrue(any("name must be a string" in error for error in errors))

    def test_unexpected_lifecycle_stage_fails(self):
        registry = copy.deepcopy(self.registry)
        registry["repositories"][0]["lifecycle_stage"] = "README_DONE"
        errors = self.errors_for(registry=registry)
        self.assertTrue(any("invalid lifecycle stage" in error for error in errors))

    def test_missing_required_field_fails(self):
        registry = copy.deepcopy(self.registry)
        del registry["repositories"][0]["next_task"]
        errors = self.errors_for(registry=registry)
        self.assertTrue(any("missing required field next_task" in error for error in errors))

    def test_complete_without_all_evidence_fails(self):
        registry = copy.deepcopy(self.registry)
        project = registry["repositories"][0]
        project["lifecycle_stage"] = "COMPLETE"
        project["completion_status"] = "COMPLETE"
        project["program_state"] = "complete"
        project["blockers"] = []
        project["completion_evidence"] = [
            {"gate": next(iter(COMPLETION_GATES)), "artifact": "synthetic"}
        ]
        errors = self.errors_for(registry=registry)
        self.assertTrue(any("COMPLETE without required completion evidence" in error for error in errors))

    def test_complete_requires_visible_value_evidence(self):
        registry = copy.deepcopy(self.registry)
        project = registry["repositories"][0]
        project["lifecycle_stage"] = "COMPLETE"
        project["completion_status"] = "COMPLETE"
        project["program_state"] = "complete"
        project["blockers"] = []
        project["completion_evidence"] = [
            {"gate": gate, "artifact": "https://example.invalid/evidence"}
            for gate in COMPLETION_GATES
            if not gate.startswith("visible_value_")
            and gate not in {"machine_value_receipt", "operator_visible_indicator", "durable_metric_integration"}
        ]
        errors = self.errors_for(registry=registry)
        self.assertTrue(any("machine_value_receipt" in error for error in errors))
        self.assertTrue(any("operator_visible_indicator" in error for error in errors))

    def test_visible_value_exception_must_be_narrow_and_justified(self):
        registry = copy.deepcopy(self.registry)
        project = registry["repositories"][0]
        project["lifecycle_stage"] = "COMPLETE"
        project["completion_status"] = "COMPLETE"
        project["program_state"] = "complete"
        project["blockers"] = []
        project["completion_evidence"] = [
            {"gate": gate, "artifact": "https://example.invalid/evidence"}
            for gate in COMPLETION_GATES
        ]
        target = next(
            item for item in project["completion_evidence"]
            if item["gate"] == "machine_value_receipt"
        )
        target.update({
            "disposition": "NOT_APPLICABLE",
            "exception_scope": "CONVENIENCE",
            "justification": "too hard",
        })
        errors = self.errors_for(registry=registry)
        self.assertTrue(any("invalid completion exception" in error for error in errors))

    def test_nonexistent_dependency_fails(self):
        registry = copy.deepcopy(self.registry)
        registry["repositories"][0]["dependencies"].append("forgotten-project")
        errors = self.errors_for(registry=registry)
        self.assertTrue(any("dependency references nonexistent project" in error for error in errors))

    def test_nonexistent_experiment_project_fails(self):
        experiments = copy.deepcopy(self.experiments)
        experiments["experiments"][0]["participating_repositories"].append("forgotten-project")
        errors = self.errors_for(experiments=experiments)
        self.assertTrue(any("references nonexistent project" in error for error in errors))

    def test_malformed_experiment_id_reports_error(self):
        experiments = copy.deepcopy(self.experiments)
        experiments["experiments"][0]["id"] = ["EXP-001"]
        errors = self.errors_for(experiments=experiments)
        self.assertTrue(any("id must be a string" in error for error in errors))

    def test_exp001_theory_reconciliation_is_required(self):
        experiments = copy.deepcopy(self.experiments)
        del experiments["experiments"][0]["theory_reconciliation"]
        errors = self.errors_for(experiments=experiments)
        self.assertTrue(
            any("theory_reconciliation must be an object" in error for error in errors)
        )

    def test_exp001_offline_freeze_is_required(self):
        experiments = copy.deepcopy(self.experiments)
        del experiments["experiments"][0]["offline_benchmark_freeze"]
        errors = self.errors_for(experiments=experiments)
        self.assertTrue(
            any("offline_benchmark_freeze must be an object" in error for error in errors)
        )

    def test_exp001_offline_freeze_cannot_claim_subject_runs(self):
        experiments = copy.deepcopy(self.experiments)
        experiments["experiments"][0]["offline_benchmark_freeze"][
            "provider_model_runs_added"
        ] = 1
        errors = self.errors_for(experiments=experiments)
        self.assertTrue(
            any("provider_model_runs_added must be 0" in error for error in errors)
        )

    def test_exp001_launch_preregistration_is_required(self):
        experiments = copy.deepcopy(self.experiments)
        del experiments["experiments"][0]["launch_preregistration"]
        errors = self.errors_for(experiments=experiments)
        self.assertTrue(
            any("launch_preregistration must be an object" in error for error in errors)
        )

    def test_exp001_launch_preregistration_cannot_claim_subject_runs(self):
        experiments = copy.deepcopy(self.experiments)
        experiments["experiments"][0]["launch_preregistration"][
            "provider_model_runs_added"
        ] = 1
        errors = self.errors_for(experiments=experiments)
        self.assertTrue(
            any("provider_model_runs_added must be 0" in error for error in errors)
        )

    def test_exp001_subject_configuration_identity_cannot_drift(self):
        experiments = copy.deepcopy(self.experiments)
        experiments["experiments"][0]["launch_preregistration"][
            "subject_configuration_id"
        ] = "sha256:" + "0" * 64
        errors = self.errors_for(experiments=experiments)
        self.assertTrue(
            any("subject_configuration_id must be" in error for error in errors)
        )

    def test_exp001_launch_verification_hash_cannot_drift(self):
        experiments = copy.deepcopy(self.experiments)
        experiments["experiments"][0]["launch_preregistration"][
            "verification_artifact_sha256"
        ] = "sha256:" + "0" * 64
        errors = self.errors_for(experiments=experiments)
        self.assertTrue(
            any("verification artifact hash drifted" in error for error in errors)
        )

    def test_exp001_block_coordinator_qualification_is_required(self):
        experiments = copy.deepcopy(self.experiments)
        del experiments["experiments"][0]["block_coordinator_qualification"]
        errors = self.errors_for(experiments=experiments)
        self.assertTrue(
            any(
                "block_coordinator_qualification must be an object" in error
                for error in errors
            )
        )

    def test_exp001_block_coordinator_cannot_claim_provider_runs(self):
        experiments = copy.deepcopy(self.experiments)
        experiments["experiments"][0]["block_coordinator_qualification"][
            "provider_model_runs_added"
        ] = 1
        errors = self.errors_for(experiments=experiments)
        self.assertTrue(
            any("provider_model_runs_added must be 0" in error for error in errors)
        )

    def test_exp001_block_coordinator_release_cannot_drift(self):
        experiments = copy.deepcopy(self.experiments)
        experiments["experiments"][0]["block_coordinator_qualification"][
            "research_release_sha"
        ] = "0" * 40
        errors = self.errors_for(experiments=experiments)
        self.assertTrue(
            any("release SHA must match research" in error for error in errors)
        )

    def test_exp001_block_coordinator_evidence_hash_cannot_drift(self):
        experiments = copy.deepcopy(self.experiments)
        experiments["experiments"][0]["block_coordinator_qualification"][
            "qualification_artifact_sha256"
        ] = "sha256:" + "0" * 64
        errors = self.errors_for(experiments=experiments)
        self.assertTrue(
            any("qualification_artifact_sha256 drifted" in error for error in errors)
        )

    def test_exp001_live_preflight_is_required(self):
        experiments = copy.deepcopy(self.experiments)
        del experiments["experiments"][0]["live_authorization_preflight"]
        errors = self.errors_for(experiments=experiments)
        self.assertTrue(
            any(
                "live_authorization_preflight must be an object" in error
                for error in errors
            )
        )

    def test_exp001_live_preflight_cannot_claim_consumption_or_runs(self):
        fields = (
            "provider_model_runs_added",
            "authorization_consumptions_added",
            "experiment_runs_added",
            "experiment_results_added",
            "result_envelopes_added",
        )
        for field in fields:
            with self.subTest(field=field):
                experiments = copy.deepcopy(self.experiments)
                experiments["experiments"][0]["live_authorization_preflight"][
                    field
                ] = 1
                errors = self.errors_for(experiments=experiments)
                self.assertTrue(
                    any(f"{field} must be 0" in error for error in errors)
                )

    def test_exp001_live_preflight_evidence_hash_cannot_drift(self):
        fields = (
            "model_catalogue_artifact_sha256",
            "pricing_preflight_artifact_sha256",
            "qualification_artifact_sha256",
            "value_receipt_artifact_sha256",
        )
        for field in fields:
            with self.subTest(field=field):
                experiments = copy.deepcopy(self.experiments)
                experiments["experiments"][0]["live_authorization_preflight"][
                    field
                ] = "sha256:" + "0" * 64
                errors = self.errors_for(experiments=experiments)
                self.assertTrue(any(f"{field} drifted" in error for error in errors))

    def test_exp001_live_preflight_must_remain_planned_and_unrendered(self):
        fields = (
            ("lifecycle_status", "EXPERIMENTED"),
            ("subject_rendering_count", 1),
            ("subject_visible_canonical_arm_identifier_count", 1),
        )
        for field, value in fields:
            with self.subTest(field=field):
                experiments = copy.deepcopy(self.experiments)
                experiments["experiments"][0]["live_authorization_preflight"][
                    field
                ] = value
                errors = self.errors_for(experiments=experiments)
                self.assertTrue(any(f"live preflight {field}" in error for error in errors))

    def test_dashboard_is_current(self):
        expected = (ROOT / "PROGRAM_STATUS.md").read_text(encoding="utf-8")
        self.assertEqual(render(self.registry, self.experiments), expected)


if __name__ == "__main__":
    unittest.main()
