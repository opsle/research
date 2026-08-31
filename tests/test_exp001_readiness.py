from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
READINESS_ROOT = ROOT / "experiments/exp-001/readiness-v1"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


READINESS = load_module(
    "exp001_readiness",
    READINESS_ROOT / "readiness.py",
)
VALUE_VALIDATOR = load_module(
    "exp001_readiness_value_validator",
    ROOT / "tools/validate_value_receipt.py",
)


class Exp001ReadinessTests(unittest.TestCase):
    evaluated_at = "2026-08-31T02:10:00Z"

    def setUp(self):
        self.contract = READINESS.load_json(READINESS.CONTRACT_PATH)
        self.documentation = READINESS.load_json(READINESS.DOCUMENTATION_PATH)
        self.documentation_facts = self.documentation["normalized_facts"]
        self.entitlement = READINESS.load_json(READINESS.ENTITLEMENT_FIXTURE_PATH)
        self.model_identity = READINESS.load_json(
            READINESS.MODEL_IDENTITY_FIXTURE_PATH
        )
        self.account = {
            field: self.entitlement[field]
            for field in ("organization_id", "project_id", "credential_id")
        }

    def reidentify(self, value):
        value["identity"] = READINESS.object_identity(value)
        return value

    def rehash_check(self, check):
        check["sanitized_response_sha256"] = READINESS.sha256_bytes(
            READINESS.canonical_bytes(check["relevant_response_fields"])
        )

    def test_current_positive_metadata_remains_unverified(self):
        result = READINESS.validate_entitlement_evidence(
            self.entitlement,
            evaluated_at=self.evaluated_at,
            expected_account=self.account,
            documentation_facts=self.documentation_facts,
        )
        self.assertEqual(result, "UNVERIFIED")

    def test_synthetic_entitled_evidence_shape_requires_documented_guarantee(self):
        entitled = copy.deepcopy(self.entitlement)
        entitled["provider_documented_invocation_equivalence"] = True
        entitled["invocation_equivalence_source"] = (
            "https://developers.openai.com/future-invocation-guarantee"
        )
        entitled["classification"] = "ENTITLED"
        documentation_facts = copy.deepcopy(self.documentation_facts)
        documentation_facts["provider_documented_invocation_equivalence"] = True
        documentation_facts["invocation_equivalence_source"] = entitled[
            "invocation_equivalence_source"
        ]
        self.reidentify(entitled)
        self.assertEqual(
            READINESS.validate_entitlement_evidence(
                entitled,
                evaluated_at=self.evaluated_at,
                expected_account=self.account,
                documentation_facts=documentation_facts,
            ),
            "ENTITLED",
        )

    def test_not_entitled_project_policy_denial(self):
        denied = copy.deepcopy(self.entitlement)
        permission = next(
            item
            for item in denied["checks"]
            if item["mechanism"] == "project_model_permissions"
        )
        permission["relevant_response_fields"] = {
            "mode": "deny_list",
            "model_ids": ["gpt-5.6-sol"],
            "object": "project.model_permissions",
        }
        permission["outcome"] = "DENY"
        self.rehash_check(permission)
        denied["classification"] = "NOT_ENTITLED"
        self.reidentify(denied)
        self.assertEqual(
            READINESS.validate_entitlement_evidence(
                denied,
                evaluated_at=self.evaluated_at,
                expected_account=self.account,
                documentation_facts=self.documentation_facts,
            ),
            "NOT_ENTITLED",
        )

    def test_stale_entitlement_evidence_rejected(self):
        with self.assertRaisesRegex(READINESS.ReadinessError, "stale"):
            READINESS.validate_entitlement_evidence(
                self.entitlement,
                evaluated_at="2026-08-31T02:15:01Z",
                expected_account=self.account,
                documentation_facts=self.documentation_facts,
            )

    def test_wrong_account_project_and_credential_rejected(self):
        for field, wrong in (
            ("organization_id", "org_wrong"),
            ("project_id", "proj_wrong"),
            ("credential_id", "key_wrong"),
        ):
            with self.subTest(field=field), self.assertRaisesRegex(
                READINESS.ReadinessError,
                "does not match the launch account",
            ):
                READINESS.validate_entitlement_evidence(
                    self.entitlement,
                    evaluated_at=self.evaluated_at,
                    expected_account={**self.account, field: wrong},
                    documentation_facts=self.documentation_facts,
                )

    def test_wrong_model_and_api_surface_rejected(self):
        for field, wrong in (
            ("model_id", "gpt-5.6"),
            ("wire_api", "Chat Completions"),
            ("endpoint", "/v1/chat/completions"),
        ):
            changed = copy.deepcopy(self.entitlement)
            changed[field] = wrong
            self.reidentify(changed)
            with self.subTest(field=field), self.assertRaisesRegex(
                READINESS.ReadinessError,
                "model or API-surface binding mismatch",
            ):
                READINESS.validate_entitlement_evidence(
                    changed,
                    evaluated_at=self.evaluated_at,
                    expected_account=self.account,
                    documentation_facts=self.documentation_facts,
                )

    def test_malformed_missing_and_tampered_entitlement_evidence_rejected(self):
        malformed = copy.deepcopy(self.entitlement)
        malformed["checks"][0]["response_status"] = "200"
        self.reidentify(malformed)
        with self.assertRaisesRegex(READINESS.ReadinessError, "status is malformed"):
            READINESS.validate_entitlement_evidence(
                malformed,
                evaluated_at=self.evaluated_at,
                expected_account=self.account,
                documentation_facts=self.documentation_facts,
            )

        missing = copy.deepcopy(self.entitlement)
        missing["checks"].pop()
        self.reidentify(missing)
        with self.assertRaisesRegex(READINESS.ReadinessError, "missing required checks"):
            READINESS.validate_entitlement_evidence(
                missing,
                evaluated_at=self.evaluated_at,
                expected_account=self.account,
                documentation_facts=self.documentation_facts,
            )

        tampered = copy.deepcopy(self.entitlement)
        tampered["checks"][0]["relevant_response_fields"]["status"] = "archived"
        self.reidentify(tampered)
        with self.assertRaisesRegex(READINESS.ReadinessError, "response hash mismatch"):
            READINESS.validate_entitlement_evidence(
                tampered,
                evaluated_at=self.evaluated_at,
                expected_account=self.account,
                documentation_facts=self.documentation_facts,
            )

    def test_secret_and_header_material_rejected(self):
        for key, value in (
            ("api_key", "sk-synthetic-not-a-real-key"),
            ("request_headers", {"Authorization": "Bearer syntheticcredential123"}),
            ("credential_value", "syntheticcredential123"),
        ):
            leaked = copy.deepcopy(self.entitlement)
            leaked[key] = value
            self.reidentify(leaked)
            with self.subTest(key=key), self.assertRaisesRegex(
                READINESS.ReadinessError,
                "secret or reusable authentication",
            ):
                READINESS.validate_entitlement_evidence(
                    leaked,
                    evaluated_at=self.evaluated_at,
                    expected_account=self.account,
                    documentation_facts=self.documentation_facts,
                )

    def test_api_key_hash_is_not_an_account_identity(self):
        changed = copy.deepcopy(self.entitlement)
        changed["credential_identity_method"] = "API_KEY_SHA256"
        self.reidentify(changed)
        with self.assertRaisesRegex(READINESS.ReadinessError, "must not be derived"):
            READINESS.validate_entitlement_evidence(
                changed,
                evaluated_at=self.evaluated_at,
                expected_account=self.account,
                documentation_facts=self.documentation_facts,
            )

    def immutable_documentation_and_evidence(self):
        facts = copy.deepcopy(self.documentation["normalized_facts"])
        snapshot_id = "gpt-5.6-sol-2026-08-31"
        facts["published_snapshot_ids"] = [snapshot_id]
        facts["distinct_immutable_snapshot_id"] = snapshot_id
        evidence = copy.deepcopy(self.model_identity)
        evidence["immutable_provider_snapshot_id"] = snapshot_id
        evidence["prelaunch_status"] = "PASS_IMMUTABLE_PROVIDER_SNAPSHOT"
        self.reidentify(evidence)
        return facts, evidence

    def test_exact_immutable_snapshot_and_runtime_match(self):
        facts, evidence = self.immutable_documentation_and_evidence()
        evidence["runtime_identity"] = {
            "returned_model_id": "gpt-5.6-sol-2026-08-31"
        }
        self.reidentify(evidence)
        self.assertEqual(
            READINESS.validate_model_identity_evidence(
                evidence,
                documentation_facts=facts,
                require_runtime=True,
            ),
            "PASS",
        )

    def test_mutable_identifier_forbidden(self):
        facts = copy.deepcopy(self.documentation["normalized_facts"])
        facts["published_snapshot_ids"] = ["gpt-5.6-sol"]
        evidence = copy.deepcopy(self.model_identity)
        evidence["immutable_provider_snapshot_id"] = "gpt-5.6-sol"
        evidence["prelaunch_status"] = "PASS_IMMUTABLE_PROVIDER_SNAPSHOT"
        self.reidentify(evidence)
        with self.assertRaisesRegex(READINESS.ReadinessError, "not the documented immutable"):
            READINESS.validate_model_identity_evidence(
                evidence,
                documentation_facts=facts,
                require_runtime=False,
            )

    def test_runtime_identity_mismatch_and_missing_rejected(self):
        facts, evidence = self.immutable_documentation_and_evidence()
        mismatch = copy.deepcopy(evidence)
        mismatch["runtime_identity"] = {"returned_model_id": "gpt-5.6-sol"}
        self.reidentify(mismatch)
        with self.assertRaisesRegex(READINESS.ReadinessError, "runtime model identity mismatch"):
            READINESS.validate_model_identity_evidence(
                mismatch,
                documentation_facts=facts,
                require_runtime=True,
            )
        with self.assertRaisesRegex(READINESS.ReadinessError, "runtime model identity is missing"):
            READINESS.validate_model_identity_evidence(
                evidence,
                documentation_facts=facts,
                require_runtime=True,
            )

    def test_stale_wrong_binding_and_tampered_documentation_rejected(self):
        with self.assertRaisesRegex(READINESS.ReadinessError, "stale"):
            READINESS.validate_documentation_snapshot(
                self.documentation,
                evaluated_at="2026-09-01T02:10:01Z",
            )
        wrong = copy.deepcopy(self.documentation)
        wrong["normalized_facts"]["model_id"] = "gpt-5.6"
        wrong["normalized_evidence_sha256"] = READINESS.sha256_bytes(
            READINESS.canonical_bytes(wrong["normalized_facts"])
        )
        self.reidentify(wrong)
        with self.assertRaisesRegex(READINESS.ReadinessError, "model binding drifted"):
            READINESS.validate_documentation_snapshot(
                wrong,
                evaluated_at=self.evaluated_at,
            )
        tampered = copy.deepcopy(self.documentation)
        tampered["normalized_facts"]["max_output_tokens"] = 1
        self.reidentify(tampered)
        with self.assertRaisesRegex(READINESS.ReadinessError, "evidence hash mismatch"):
            READINESS.validate_documentation_snapshot(
                tampered,
                evaluated_at=self.evaluated_at,
            )

    def test_launch_ordering_keeps_blockers_before_consumption(self):
        READINESS.validate_contract(self.contract)
        changed = copy.deepcopy(self.contract)
        sequence = changed["launch_sequence"]
        consume = next(
            item
            for item in sequence
            if item["gate"] == "atomically_claim_and_consume_authorization"
        )
        identity = next(
            item for item in sequence if item["gate"] == "verify_model_identity_policy"
        )
        consume["order"], identity["order"] = identity["order"], consume["order"]
        sequence.sort(key=lambda item: item["order"])
        self.reidentify(changed)
        with self.assertRaisesRegex(READINESS.ReadinessError, "ordered after"):
            READINESS.validate_contract(changed)

    def test_current_qualification_is_blocked_and_all_counters_zero(self):
        report = READINESS.qualify(
            contract=self.contract,
            documentation=self.documentation,
            entitlement=self.entitlement,
            model_identity=self.model_identity,
            evaluated_at=self.evaluated_at,
        )
        self.assertEqual(report["readiness"], "BLOCKED")
        self.assertEqual(report["entitlement_classification"], "UNVERIFIED")
        self.assertEqual(report["model_identity_status"], "BLOCKED")
        self.assertEqual(report["lifecycle_status"], "PLANNED")
        for field in (
            "provider_model_subject_count",
            "authenticated_provider_probe_count",
            "authorization_consumption_count",
            "experiment_run_count",
            "experiment_result_count",
            "result_envelope_count",
        ):
            self.assertEqual(report[field], 0)

    def test_validator_has_no_provider_transport(self):
        READINESS.provider_free_source_audit()

    def test_visible_value_receipt_is_valid(self):
        receipt = READINESS.load_json(
            ROOT / "program/evidence/exp-001-readiness/value-receipt.json"
        )
        self.assertEqual(VALUE_VALIDATOR.validate(receipt), [])


if __name__ == "__main__":
    unittest.main()
