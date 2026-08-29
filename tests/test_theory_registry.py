from __future__ import annotations

import copy
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from validate_program import (  # noqa: E402
    DEFAULT_REGISTRY,
    DEFAULT_THEORY_MAP,
    DEFAULT_THEORY_REGISTRY,
    load_json,
    validate_theory,
)


class TheoryRegistryValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = load_json(DEFAULT_REGISTRY)
        self.theory = load_json(DEFAULT_THEORY_REGISTRY)
        self.theory_map = DEFAULT_THEORY_MAP.read_text(encoding="utf-8")

    def errors_for(self, theory=None, registry=None, theory_map=None):
        return validate_theory(
            theory or self.theory,
            registry or self.registry,
            theory_map or self.theory_map,
        )

    def test_authoritative_theory_registry_is_valid(self):
        self.assertEqual(self.errors_for(), [])

    def test_every_current_concept_repository_is_mapped_once(self):
        theory = copy.deepcopy(self.theory)
        theory["concepts"][-1]["current_repository"] = "context-firewall"
        errors = self.errors_for(theory=theory)
        self.assertTrue(any("duplicate current concept repository mappings" in error for error in errors))
        self.assertTrue(any("missing current concept repository mappings" in error for error in errors))

    def test_gearbox_must_claim_its_current_repository(self):
        theory = copy.deepcopy(self.theory)
        theory["concepts"][0]["current_repository"] = None
        errors = self.errors_for(theory=theory)
        self.assertTrue(any("Gearbox must claim the current gearbox repository" in error for error in errors))

    def test_unknown_classification_fails(self):
        theory = copy.deepcopy(self.theory)
        theory["concepts"][1]["primary_classification"] = "PRODUCT"
        errors = self.errors_for(theory=theory)
        self.assertTrue(any("invalid primary classification" in error for error in errors))

    def test_malformed_concept_id_reports_error(self):
        theory = copy.deepcopy(self.theory)
        theory["concepts"][1]["id"] = ["agent-trajectory-profiler"]
        errors = self.errors_for(theory=theory)
        self.assertTrue(any("id must be a string" in error for error in errors))

    def test_non_object_concept_reports_error(self):
        theory = copy.deepcopy(self.theory)
        theory["concepts"][1] = None
        errors = self.errors_for(theory=theory)
        self.assertTrue(any("must be an object" in error for error in errors))

    def test_malformed_relation_reports_error(self):
        theory = copy.deepcopy(self.theory)
        theory["concepts"][0]["dependencies"][0] = ["context-firewall"]
        errors = self.errors_for(theory=theory)
        self.assertTrue(any("entries must be nonempty strings" in error for error in errors))

    def test_required_semantic_text_cannot_be_blank(self):
        theory = copy.deepcopy(self.theory)
        theory["concepts"][0]["original_problem"] = "  "
        errors = self.errors_for(theory=theory)
        self.assertTrue(any("original_problem must be a nonempty string" in error for error in errors))

    def test_registry_reconciliation_distinction_is_required(self):
        registry = copy.deepcopy(self.registry)
        del registry["theory_reconciliation"]["gearbox_vs_durable_supervisor"]
        errors = self.errors_for(registry=registry)
        self.assertTrue(
            any("Gearbox versus Durable Supervisor distinction" in error for error in errors)
        )

    def test_registry_gearbox_repository_status_is_required(self):
        registry = copy.deepcopy(self.registry)
        del registry["theory_reconciliation"]["gearbox_repository_status"]
        errors = self.errors_for(registry=registry)
        self.assertTrue(
            any("created and prototyped" in error for error in errors)
        )

    def test_gearbox_publication_head_must_match_registry(self):
        registry = copy.deepcopy(self.registry)
        registry["gearbox_publication"]["final_main_sha"] = "0" * 40
        errors = self.errors_for(registry=registry)
        self.assertTrue(
            any("publication SHA must match repository HEAD" in error for error in errors)
        )

    def test_existing_repository_lifecycle_changes_are_forbidden(self):
        registry = copy.deepcopy(self.registry)
        registry["theory_reconciliation"][
            "existing_repository_lifecycle_changes_executed"
        ] = True
        errors = self.errors_for(registry=registry)
        self.assertTrue(
            any("no existing-repository lifecycle changes" in error for error in errors)
        )

    def test_theory_map_classification_drift_fails(self):
        drifted = self.theory_map.replace(
            "| `context-firewall` | `INDEPENDENT_OPSLE_TOOL` |",
            "| `context-firewall` | `GEARBOX_CORE` |",
        )
        errors = self.errors_for(theory_map=drifted)
        self.assertTrue(any("THEORY_MAP classification drift for context-firewall" in error for error in errors))

    def test_theory_map_hash_drift_fails(self):
        drifted = re.sub(
            r"(?<=Theory registry canonical SHA-256:\n`)[0-9a-f]{64}",
            "0" * 64,
            self.theory_map,
            count=1,
        )
        errors = self.errors_for(theory_map=drifted)
        self.assertTrue(any("THEORY_MAP canonical theory-registry hash is stale" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
