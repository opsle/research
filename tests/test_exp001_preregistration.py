from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP_ROOT = ROOT / "experiments" / "exp-001"
PREREG = EXP_ROOT / "preregistration-v1"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ALLOCATION = load_module("exp001_allocation_tool", PREREG / "allocation_tool.py")
ADAPTER = load_module("exp001_subject_adapter", PREREG / "subject_adapter.py")


class Exp001PreregistrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = json.loads((PREREG / "subject-config.json").read_text())
        self.preregistration = json.loads((PREREG / "preregistration.json").read_text())
        self.index = json.loads((PREREG / "allocation-index.json").read_text())

    def test_preregistration_and_configuration_identities_are_valid(self):
        self.assertEqual(
            self.config["identity"],
            ADAPTER.object_identity(self.config),
        )
        self.assertEqual(
            self.preregistration["identity"],
            ADAPTER.object_identity(self.preregistration),
        )
        result = ADAPTER.verify_preregistration()
        self.assertTrue(result["valid"])
        self.assertEqual(result["provider_model_runs"], 0)

    def test_allocation_is_publicly_valid_and_subject_blinded(self):
        result = ALLOCATION.validate_public(
            self.index,
            PREREG / "allocation-mapping.enc",
        )
        self.assertTrue(result["valid"])
        self.assertEqual(result["block_count"], 60)
        self.assertEqual(result["subject_count"], 240)
        self.assertEqual(
            len({item["subject_label"] for item in self.index["entries"]}), 240
        )
        self.assertTrue(all("arm_id" not in item for item in self.index["entries"]))

    def test_fixed_repetition_and_stopping_plan_claims_zero_runs(self):
        plan = self.preregistration["repetition_and_stopping"]
        self.assertEqual(plan["repetitions_per_task_arm"], 10)
        self.assertEqual(plan["planned_subject_count"], 240)
        self.assertFalse(plan["interim_efficacy_or_futility_stopping"])
        self.assertEqual(self.preregistration["provider_model_runs_added"], 0)
        self.assertEqual(self.preregistration["experiment_results_added"], 0)

    def test_request_contract_has_no_sampling_override_retry_or_fallback(self):
        body = ADAPTER.request_body(
            self.config,
            "bounded input",
            "EXP001-FAKE-SUBJECT",
        )
        provider = self.config["model_provider_configuration"]
        self.assertNotIn("temperature", body)
        self.assertNotIn("top_p", body)
        self.assertFalse(body["parallel_tool_calls"])
        self.assertFalse(body["store"])
        self.assertEqual(provider["automatic_http_retries"], 0)
        self.assertEqual(provider["automatic_stream_retries"], 0)
        self.assertEqual(provider["provider_fallbacks"], 0)
        self.assertFalse(provider["session_resume"])

    def test_verification_evidence_matches_frozen_identities(self):
        report = json.loads(
            (
                ROOT
                / "program/evidence/exp-001-preregistration/verification-report.json"
            ).read_text()
        )
        self.assertEqual(report["qualification"], "PASS")
        self.assertEqual(
            report["preregistration_identity"],
            self.preregistration["identity"],
        )
        self.assertEqual(
            report["allocation"]["allocation_index_identity"],
            self.index["identity"],
        )
        self.assertTrue(report["allocation"]["mapping_verified_with_seed"])
        self.assertEqual(report["provider_model_runs_added"], 0)
        self.assertEqual(report["experiment_runs_added"], 0)

    def test_provider_free_adapter_self_test(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            (workspace / "task.py").write_text("VALUE = 1\n", encoding="utf-8")
            result = ADAPTER.self_test(self.config, workspace)
        self.assertTrue(result["valid"])
        self.assertEqual(result["provider_model_runs"], 0)
        self.assertEqual(result["api_call_count"], 2)
        self.assertEqual(result["tool_call_count"], 1)

    def test_unbound_authorization_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            authorization = root / "authorization.json"
            authorization.write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(ADAPTER.SubjectAdapterError, "authorization"):
                ADAPTER.verify_authorization(
                    authorization,
                    self.preregistration["identity"],
                    self.config["subject_limits"]["maximum_spend_usd_per_subject"],
                    self.index["entries"][0]["subject_label"],
                )


if __name__ == "__main__":
    unittest.main()
