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

    def test_consolidated_concepts_share_a_home(self):
        concepts = [c for c in self.theory["concepts"] if c["current_repository"] == "tasks"]
        self.assertGreater(len(concepts), 1)
        self.assertEqual(self.errors_for(), [])

    def test_wrong_current_home_fails(self):
        theory = copy.deepcopy(self.theory)
        theory["concepts"][-1]["current_repository"] = "context-firewall"
        self.assertTrue(any("current home drift" in e for e in self.errors_for(theory=theory)))

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

    def test_post_consolidation_reconciliation_is_required(self):
        registry = copy.deepcopy(self.registry)
        registry["theory_reconciliation"]["status"] = "IMPLEMENTED_HOME_REGISTERED"
        self.assertTrue(any("post-consolidation state" in e for e in self.errors_for(registry=registry)))

    def test_gearbox_publication_head_must_match_registry(self):
        registry = copy.deepcopy(self.registry)
        registry["gearbox_publication"]["final_main_sha"] = "0" * 40
        errors = self.errors_for(registry=registry)
        self.assertTrue(
            any("publication SHA must match historical publication" in error for error in errors)
        )

    def test_consolidation_does_not_promote_concept_maturity(self):
        theory = copy.deepcopy(self.theory)
        concept = next(c for c in theory["concepts"] if c["id"] == "agent-state-ledger")
        concept["highest_evidenced_stage"] = "COMPLETE"
        self.assertTrue(any("research maturity drift" in e for e in self.errors_for(theory=theory)))

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
