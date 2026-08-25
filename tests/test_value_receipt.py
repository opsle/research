from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from validate_value_receipt import validate  # noqa: E402


def valid_receipt():
    return {
        "schema": "opsle.value-receipt.v1",
        "mechanism": {
            "id": "opsle.context-firewall",
            "name": "Context Firewall",
            "version": "0.3.0",
            "revision": None,
        },
        "run": {"id": "run-synthetic"},
        "operation": {
            "id": "op-synthetic",
            "name": "test-output-reduction",
            "configuration_id": "sha256:" + "1" * 64,
            "policy_id": "tap-subset-policy/v1",
        },
        "measurements": [
            {
                "id": "initial_model_visible_bytes",
                "baseline": 100,
                "result": 40,
                "delta": -60,
                "unit": "byte",
                "direction": "LOWER_IS_VALUE",
                "class": "EXACT",
                "evidence_refs": ["packet"],
                "source_verification": "VERIFIED",
                "operator_display": True,
                "aggregation": {"safe": True, "method": "SUM"},
                "derivation": None,
                "limitations": [],
            }
        ],
        "evidence": [
            {
                "id": "packet",
                "kind": "CONTENT_HASH",
                "locator": "sha256:" + "a" * 64,
                "trust": "VERIFIED",
            }
        ],
        "limitations": ["No token, cost, latency, or correctness claim is made."],
    }


class ValueReceiptValidationTests(unittest.TestCase):
    def test_valid_receipt(self):
        self.assertEqual(validate(valid_receipt()), [])

    def test_missing_fields(self):
        value = valid_receipt()
        del value["mechanism"]
        self.assertTrue(any("/mechanism" in error for error in validate(value)))

    def test_unsupported_schema_version(self):
        value = valid_receipt()
        value["schema"] = "opsle.value-receipt.v2"
        self.assertTrue(any("only opsle.value-receipt.v1" in error for error in validate(value)))

    def test_invalid_unit_and_class(self):
        value = valid_receipt()
        value["measurements"][0]["unit"] = "vibes"
        value["measurements"][0]["class"] = "MARKETING"
        errors = validate(value)
        self.assertTrue(any("unsupported unit" in error for error in errors))
        self.assertTrue(any("unsupported measurement class" in error for error in errors))

    def test_impossible_numeric_values(self):
        value = valid_receipt()
        value["measurements"][0]["result"] = -1
        value["measurements"][0]["delta"] = -101
        self.assertTrue(any("nonnegative integer" in error for error in validate(value)))

    def test_delta_must_use_one_sign_convention(self):
        value = valid_receipt()
        value["measurements"][0]["delta"] = 60
        self.assertTrue(any("result minus baseline" in error for error in validate(value)))

    def test_malformed_evidence_reference(self):
        value = valid_receipt()
        value["evidence"][0]["locator"] = "sha256:not-a-hash"
        value["measurements"][0]["evidence_refs"] = ["missing"]
        errors = validate(value)
        self.assertTrue(any("malformed sha256" in error for error in errors))
        self.assertTrue(any("unresolved evidence" in error for error in errors))

    def test_exact_requires_verified_source(self):
        value = valid_receipt()
        value["measurements"][0]["source_verification"] = "CALLER_SUPPLIED"
        self.assertTrue(any("EXACT requires VERIFIED" in error for error in validate(value)))

    def test_estimate_requires_inspectable_assumptions(self):
        value = valid_receipt()
        measurement = value["measurements"][0]
        measurement["class"] = "ESTIMATED"
        measurement["aggregation"] = {"safe": False, "method": None}
        self.assertTrue(any("requires method and assumptions" in error for error in validate(value)))

    def test_modeled_measurement_cannot_be_safely_aggregated(self):
        value = valid_receipt()
        measurement = value["measurements"][0]
        measurement["class"] = "MODELED"
        measurement["derivation"] = {
            "method": "counterfactual model",
            "assumptions": ["policy would remain unchanged"],
            "input_measurement_ids": [],
            "experiment_id": None,
            "comparability": "NOT_COMPARABLE",
        }
        self.assertTrue(any("not safely summable" in error for error in validate(value)))

    def test_experimental_requires_controlled_identity(self):
        value = valid_receipt()
        measurement = value["measurements"][0]
        measurement["class"] = "EXPERIMENTAL"
        measurement["aggregation"] = {"safe": False, "method": None}
        measurement["derivation"] = {
            "method": "comparison",
            "assumptions": [],
            "input_measurement_ids": [],
            "experiment_id": None,
            "comparability": "NOT_COMPARABLE",
        }
        self.assertTrue(any("controlled experiment identity" in error for error in validate(value)))

    def test_byte_only_evidence_cannot_become_cost(self):
        value = valid_receipt()
        byte_id = value["measurements"][0]["id"]
        value["measurements"].append({
            **copy.deepcopy(value["measurements"][0]),
            "id": "estimated_cost_usd",
            "baseline": 0.0,
            "result": 0.42,
            "delta": 0.42,
            "unit": "usd",
            "class": "ESTIMATED",
            "aggregation": {"safe": False, "method": None},
            "derivation": {
                "method": "price times input",
                "assumptions": ["published price applies"],
                "input_measurement_ids": [byte_id],
                "experiment_id": None,
                "comparability": "NOT_APPLICABLE",
            },
        })
        self.assertTrue(any("requires a token measurement input" in error for error in validate(value)))

    def test_failure_prevented_cannot_be_exact(self):
        value = valid_receipt()
        value["measurements"][0]["id"] = "failure_prevented_count"
        self.assertTrue(any("prevented-failure claims" in error for error in validate(value)))

    def test_unsafe_ratio_cannot_claim_sum(self):
        value = valid_receipt()
        measurement = value["measurements"][0]
        measurement["unit"] = "ratio"
        measurement["baseline"] = 0.0
        measurement["result"] = 0.6
        measurement["delta"] = 0.6
        self.assertTrue(any("not safely summable" in error for error in validate(value)))


if __name__ == "__main__":
    unittest.main()
