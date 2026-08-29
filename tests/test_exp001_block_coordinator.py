from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COORDINATOR_ROOT = ROOT / "experiments/exp-001/coordinator-v1"
PREREG_ROOT = ROOT / "experiments/exp-001/preregistration-v1"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


COORDINATOR = load_module(
    "exp001_block_coordinator",
    COORDINATOR_ROOT / "coordinator.py",
)
VALUE_VALIDATOR = load_module(
    "exp001_value_receipt_validator",
    ROOT / "tools/validate_value_receipt.py",
)


class Exp001BlockCoordinatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.preregistration = json.loads(
            (PREREG_ROOT / "preregistration.json").read_text()
        )
        self.config = json.loads((PREREG_ROOT / "subject-config.json").read_text())
        self.block_id = "test-block"
        self.arm_ids = [
            "raw-control",
            "failure-focused",
            "bounded-provenance",
            "bounded-escalating",
        ]
        self.private_entries = [
            {
                "block_id": self.block_id,
                "configuration_id": self.config["identity"],
                "position": position,
                "repetition": 1,
                "subject_label": f"EXP001-TEST-{position}",
                "task_id": "slugify",
                "arm_id": arm_id,
            }
            for position, arm_id in enumerate(self.arm_ids, 1)
        ]
        self.public_entries = [
            {key: value for key, value in entry.items() if key != "arm_id"}
            for entry in self.private_entries
        ]

    def write_fixture_authorizations(self, directory: Path) -> None:
        for entry in self.private_entries:
            authorization = COORDINATOR.fixture_authorization(
                entry,
                self.preregistration["identity"],
                self.config["subject_limits"]["maximum_spend_usd_per_subject"],
            )
            (directory / f"{entry['subject_label']}.json").write_bytes(
                COORDINATOR.canonical_bytes(authorization)
            )

    def test_contract_identity_and_frozen_bindings_are_valid(self):
        contract = COORDINATOR.verify_contract()
        self.assertEqual(contract["identity"], COORDINATOR.object_identity(contract))
        self.assertEqual(
            contract["preregistration_identity"],
            self.preregistration["identity"],
        )

    def test_selected_block_requires_exact_public_match_and_four_arms(self):
        selected = COORDINATOR.select_block(
            {"entries": self.public_entries},
            {"entries": self.private_entries},
            self.block_id,
            set(self.arm_ids),
        )
        self.assertEqual(selected, self.private_entries)
        drifted = [dict(entry) for entry in self.private_entries]
        drifted[-1]["arm_id"] = "raw-control"
        with self.assertRaisesRegex(COORDINATOR.CoordinatorError, "each frozen arm"):
            COORDINATOR.select_block(
                {"entries": self.public_entries},
                {"entries": drifted},
                self.block_id,
                set(self.arm_ids),
            )

    def test_four_fixture_authorizations_validate_only_as_fixtures(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_fixture_authorizations(root)
            validated = COORDINATOR.validate_authorizations(
                directory=root,
                block_entries=self.private_entries,
                preregistration_identity=self.preregistration["identity"],
                configuration_id=self.config["identity"],
                maximum_spend_usd=self.config["subject_limits"][
                    "maximum_spend_usd_per_subject"
                ],
                authorization_class=COORDINATOR.FIXTURE_AUTHORIZATION,
            )
            self.assertEqual(len(validated), 4)
            with self.assertRaisesRegex(
                COORDINATOR.CoordinatorError,
                "class or block binding",
            ):
                COORDINATOR.validate_authorizations(
                    directory=root,
                    block_entries=self.private_entries,
                    preregistration_identity=self.preregistration["identity"],
                    configuration_id=self.config["identity"],
                    maximum_spend_usd=self.config["subject_limits"][
                        "maximum_spend_usd_per_subject"
                    ],
                    authorization_class=COORDINATOR.LIVE_AUTHORIZATION,
                )

    def test_authorization_set_rejects_missing_and_extra_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_fixture_authorizations(root)
            (root / f"{self.private_entries[0]['subject_label']}.json").unlink()
            (root / "unexpected.json").write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(
                COORDINATOR.CoordinatorError,
                "exactly four bound files",
            ):
                COORDINATOR.validate_authorizations(
                    directory=root,
                    block_entries=self.private_entries,
                    preregistration_identity=self.preregistration["identity"],
                    configuration_id=self.config["identity"],
                    maximum_spend_usd=self.config["subject_limits"][
                        "maximum_spend_usd_per_subject"
                    ],
                    authorization_class=COORDINATOR.FIXTURE_AUTHORIZATION,
                )

    def test_result_envelope_is_deterministic_and_empty(self):
        entry = self.private_entries[0]
        rendering = {
            "prompt_sha256": "sha256:" + "1" * 64,
            "initial_task_sha256": "sha256:" + "2" * 64,
            "evidence_sha256": "sha256:" + "3" * 64,
            "evidence_bytes": 42,
            "oracle_transcript_sha256": "sha256:" + "4" * 64,
            "arm_record": {
                "disposition": "RAW_BASELINE",
                "escalation_state": "NOT_APPLICABLE",
            },
        }
        authorization = {
            "authorization_class": COORDINATOR.FIXTURE_AUTHORIZATION,
            "authorization_id": "fixture-test",
            "identity": "sha256:" + "5" * 64,
            "maximum_spend_usd": 6.3,
        }
        first = COORDINATOR.result_envelope(
            entry=entry,
            rendering=rendering,
            authorization=authorization,
            preregistration_identity=self.preregistration["identity"],
            configuration_id=self.config["identity"],
        )
        second = COORDINATOR.result_envelope(
            entry=entry,
            rendering=rendering,
            authorization=authorization,
            preregistration_identity=self.preregistration["identity"],
            configuration_id=self.config["identity"],
        )
        self.assertEqual(first, second)
        self.assertEqual(first["identity"], COORDINATOR.object_identity(first))
        self.assertIsNone(first["provider_result"])
        self.assertIsNone(first["correctness_result"])
        self.assertIsNone(first["failure_classification"])
        self.assertEqual(first["provider_model_runs"], 0)
        self.assertEqual(first["experiment_results"], 0)

    def test_private_commitments_are_seed_keyed(self):
        value = COORDINATOR.canonical_bytes({"arm_id": "raw-control"})
        first = COORDINATOR.private_commitment(
            b"a" * 32,
            b"test-context",
            value,
        )
        second = COORDINATOR.private_commitment(
            b"b" * 32,
            b"test-context",
            value,
        )
        self.assertTrue(first.startswith("hmac-sha256:"))
        self.assertNotEqual(first, second)

    def test_value_receipt_is_valid_and_discloses_no_mapping(self):
        receipt = COORDINATOR.value_receipt(
            block_commitment="hmac-sha256:" + "1" * 64,
            configuration_id=self.config["identity"],
            preregistration_identity=self.preregistration["identity"],
            plan_commitment="hmac-sha256:" + "2" * 64,
            manifest_commitment="hmac-sha256:" + "3" * 64,
        )
        self.assertEqual(VALUE_VALIDATOR.validate(receipt), [])
        encoded = COORDINATOR.canonical_bytes(receipt)
        self.assertNotIn(b"arm_id", encoded)
        self.assertNotIn(b"subject_label", encoded)
        self.assertNotIn(self.block_id.encode(), encoded)

    def test_committed_qualification_is_current_and_claims_zero_runs(self):
        evidence_root = ROOT / "program/evidence/exp-001-block-coordinator"
        report = json.loads((evidence_root / "qualification-report.json").read_text())
        receipt_path = evidence_root / "value-receipt.json"
        receipt = json.loads(receipt_path.read_text())
        self.assertEqual(report["qualification"], "PASS")
        self.assertEqual(
            report["coordinator_revision"],
            COORDINATOR.sha256_file(COORDINATOR_ROOT / "coordinator.py"),
        )
        self.assertEqual(report["provider_model_run_count"], 0)
        self.assertEqual(report["experiment_run_count"], 0)
        self.assertEqual(report["experiment_result_count"], 0)
        self.assertFalse(report["authorization_consumed"])
        self.assertFalse(report["private_artifacts_persisted"])
        self.assertEqual(report["subject_visible_arm_identity_count"], 0)
        self.assertEqual(
            report["value_receipt_sha256"],
            COORDINATOR.sha256_file(receipt_path),
        )
        self.assertEqual(VALUE_VALIDATOR.validate(receipt), [])
        encoded = COORDINATOR.canonical_bytes(report)
        self.assertNotIn(b"EXP001-BLOCK-", encoded)
        self.assertNotIn(b'"arm_id"', encoded)
        self.assertNotIn(b'"subject_label"', encoded)


if __name__ == "__main__":
    unittest.main()
