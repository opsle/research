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

    def test_dashboard_is_current(self):
        expected = (ROOT / "PROGRAM_STATUS.md").read_text(encoding="utf-8")
        self.assertEqual(render(self.registry, self.experiments), expected)


if __name__ == "__main__":
    unittest.main()
