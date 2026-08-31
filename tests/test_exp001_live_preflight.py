from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import ClassVar

ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT_ROOT = ROOT / "experiments/exp-001/live-preflight-v1"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PREFLIGHT = load_module(
    "exp001_live_preflight",
    PREFLIGHT_ROOT / "preflight.py",
)
VALUE_VALIDATOR = load_module(
    "exp001_live_preflight_value_validator",
    ROOT / "tools/validate_value_receipt.py",
)


class Exp001LivePreflightTests(unittest.TestCase):
    issued_at = "2026-08-30T18:49:10Z"
    valid_from = "2026-08-30T18:49:10Z"
    expires_at = "2026-09-13T18:49:10Z"
    validated_at = "2026-08-30T18:49:10Z"
    set_id = "exp001-live-authset-11111111111111111111111111111111"
    authorization_ids: ClassVar[list[str]] = [
        f"exp001-live-authz-{index:032x}" for index in range(1, 5)
    ]

    def materialize(self, root: Path) -> Path:
        destination = root / "authorization-set"
        PREFLIGHT.materialize_authorization_set(
            destination=destination,
            block_id=PREFLIGHT.first_public_block_id(),
            set_id=self.set_id,
            authorization_ids=self.authorization_ids,
            issued_at=self.issued_at,
            valid_from=self.valid_from,
            expires_at=self.expires_at,
        )
        return destination

    def test_catalogue_matches_exact_preregistered_candidate(self):
        catalogue = PREFLIGHT.load_json(PREFLIGHT.CATALOGUE_PATH)
        candidate = PREFLIGHT.validate_catalogue(catalogue)
        self.assertEqual(candidate["provider_id"], "openai")
        self.assertEqual(candidate["model_id"], "gpt-5.6-sol")
        self.assertEqual(candidate["model_family"], "GPT-5.6")
        self.assertEqual(candidate["input_price_usd"], 4.0)
        self.assertEqual(candidate["cached_input_price_usd"], 0.4)
        self.assertEqual(candidate["output_price_usd"], 20.0)
        self.assertEqual(candidate["context_window_tokens"], 1_050_000)
        self.assertEqual(candidate["max_output_tokens"], 128_000)
        self.assertEqual(len(candidate["uncertainty_or_unavailable_fields"]), 2)

    def test_pricing_preflight_preserves_registered_ceiling(self):
        catalogue = PREFLIGHT.load_json(PREFLIGHT.CATALOGUE_PATH)
        pricing = PREFLIGHT.pricing_preflight(catalogue)
        self.assertEqual(pricing["derived_spend_ceiling_usd"], 6.25152)
        self.assertEqual(pricing["registered_spend_ceiling_usd"], 6.3)
        self.assertFalse(pricing["long_context_multiplier_applies"])
        self.assertFalse(pricing["price_drift_from_frozen_configuration"])
        self.assertFalse(pricing["account_access_verified"])
        self.assertEqual(pricing["provider_call_count"], 0)

    def test_pricing_drift_is_computed_and_rejected(self):
        catalogue = PREFLIGHT.load_json(PREFLIGHT.CATALOGUE_PATH)
        configuration = PREFLIGHT.load_json(
            PREFLIGHT.PREREG_ROOT / "subject-config.json"
        )
        candidate = catalogue["eligible_candidates"][0]
        self.assertFalse(
            PREFLIGHT.price_drift_from_frozen_configuration(
                candidate,
                configuration,
            )
        )
        for field, value in (
            ("input_price_usd", 100.0),
            ("output_price_usd", 100.0),
        ):
            with self.subTest(field=field):
                changed = copy.deepcopy(catalogue)
                changed["eligible_candidates"][0][field] = value
                changed["identity"] = PREFLIGHT.object_identity(changed)
                self.assertTrue(
                    PREFLIGHT.price_drift_from_frozen_configuration(
                        changed["eligible_candidates"][0],
                        configuration,
                    )
                )
                with self.assertRaisesRegex(
                    PREFLIGHT.PreflightError,
                    "price drifted from frozen subject configuration",
                ):
                    PREFLIGHT.pricing_preflight(changed)

        changed_cached = copy.deepcopy(catalogue)
        changed_cached["eligible_candidates"][0]["cached_input_price_usd"] = 100.0
        changed_cached["identity"] = PREFLIGHT.object_identity(changed_cached)
        with self.assertRaisesRegex(
            PREFLIGHT.PreflightError,
            "drifted from current documentation",
        ):
            PREFLIGHT.pricing_preflight(changed_cached)

    def test_exact_four_live_labels_validate_unconsumed(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = self.materialize(Path(temporary))
            result = PREFLIGHT.validate_authorization_set(
                directory,
                validated_at=self.validated_at,
            )
            self.assertTrue(result["valid"])
            self.assertEqual(result["authorization_class"], "LIVE_PROVIDER_RUN")
            self.assertEqual(result["label_count"], 4)
            self.assertEqual(result["authorization_count"], 4)
            self.assertEqual(result["authorization_consumption_count"], 0)
            self.assertEqual(result["provider_model_launch_count"], 0)
            self.assertEqual(result["experiment_run_count"], 0)
            self.assertEqual(result["experiment_result_count"], 0)

    def test_authorizations_have_unique_auditable_identities_and_no_results(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = self.materialize(Path(temporary))
            records = [
                json.loads(path.read_text())
                for path in sorted((directory / "authorizations").glob("*.json"))
            ]
            self.assertEqual(len({record["authorization_id"] for record in records}), 4)
            self.assertEqual(len({record["subject_label"] for record in records}), 4)
            for record in records:
                self.assertEqual(record["authorization_set_id"], self.set_id)
                self.assertEqual(record["authorization_class"], "LIVE_PROVIDER_RUN")
                self.assertEqual(record["authorization_state"], "UNCONSUMED")
                self.assertIsNone(record["consumed_at"])
                self.assertIsNone(record["result_envelope"])

    def test_fixture_duplicate_missing_extra_binding_malformed_and_time_reject(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = self.materialize(Path(temporary))
            evidence = PREFLIGHT.qualify(
                set_directory=directory,
                catalogue_path=PREFLIGHT.CATALOGUE_PATH,
                validated_at=self.validated_at,
            )
            report = json.loads(evidence["qualification-report.json"])
            self.assertEqual(report["authorization_validation_count"], 13)
            self.assertTrue(report["fixture_rejected_from_live_gate"])
            self.assertTrue(report["duplicate_label_rejected"])
            self.assertTrue(report["duplicate_authorization_identity_rejected"])
            self.assertTrue(report["missing_label_rejected"])
            self.assertTrue(report["extra_label_rejected"])
            self.assertTrue(report["wrong_experiment_binding_rejected"])
            self.assertTrue(report["wrong_block_binding_rejected"])
            self.assertTrue(report["malformed_authorization_rejected"])
            self.assertTrue(report["expired_authorization_rejected"])
            self.assertTrue(report["not_yet_valid_authorization_rejected"])

    def test_replay_is_byte_identical_and_creation_is_exclusive(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory = self.materialize(root)
            manifest = PREFLIGHT.load_json(directory / "set-manifest.json")
            replay = root / "replay"
            PREFLIGHT.materialize_authorization_set(
                destination=replay,
                **PREFLIGHT.replay_inputs(manifest),
            )
            self.assertEqual(PREFLIGHT.snapshot(directory), PREFLIGHT.snapshot(replay))
            with self.assertRaisesRegex(
                PREFLIGHT.PreflightError,
                "destination must be absent",
            ):
                PREFLIGHT.materialize_authorization_set(
                    destination=replay,
                    **PREFLIGHT.replay_inputs(manifest),
                )

    def test_public_evidence_discloses_no_labels_mapping_or_arm_ids(self):
        arms = json.loads((ROOT / "experiments/exp-001/arms.json").read_text())
        arm_ids = [arm["id"].encode() for arm in arms["arms"]]
        with tempfile.TemporaryDirectory() as temporary:
            directory = self.materialize(Path(temporary))
            manifest = PREFLIGHT.load_json(directory / "set-manifest.json")
            labels = [
                record["subject_label"].encode()
                for record in manifest["authorizations"]
            ]
            evidence = PREFLIGHT.qualify(
                set_directory=directory,
                catalogue_path=PREFLIGHT.CATALOGUE_PATH,
                validated_at=self.validated_at,
            )
            self.assertEqual(set(evidence), set(PREFLIGHT.PUBLIC_EVIDENCE_NAMES))
            public = b"".join(evidence.values())
            self.assertFalse(any(label in public for label in labels))
            self.assertFalse(any(arm_id in public for arm_id in arm_ids))
            report = json.loads(evidence["qualification-report.json"])
            self.assertEqual(report["subject_rendering_count"], 0)
            self.assertEqual(
                report["subject_visible_canonical_arm_identifier_count"], 0
            )
            self.assertEqual(report["private_mapping_access_count"], 0)
            self.assertEqual(report["raw_evidence_access_count"], 0)

    def test_public_evidence_privacy_assertion_covers_every_output(self):
        clean = {
            name: PREFLIGHT.canonical_bytes({"public": name})
            for name in PREFLIGHT.PUBLIC_EVIDENCE_NAMES
        }
        sentinel = "synthetic-private-sentinel"
        PREFLIGHT.assert_public_evidence_privacy(
            clean,
            forbidden_values=(sentinel,),
        )
        for name in PREFLIGHT.PUBLIC_EVIDENCE_NAMES:
            with self.subTest(output=name, leak="field"):
                leaked_field = dict(clean)
                leaked_field[name] = PREFLIGHT.canonical_bytes(
                    {"subject_label": "synthetic-subject"}
                )
                with self.assertRaisesRegex(
                    PREFLIGHT.PreflightError,
                    "leaks private set detail",
                ):
                    PREFLIGHT.assert_public_evidence_privacy(
                        leaked_field,
                        forbidden_values=(sentinel,),
                    )
            with self.subTest(output=name, leak="value"):
                leaked_value = dict(clean)
                leaked_value[name] = PREFLIGHT.canonical_bytes(
                    {"public_note": sentinel}
                )
                with self.assertRaisesRegex(
                    PREFLIGHT.PreflightError,
                    "leaks private set detail",
                ):
                    PREFLIGHT.assert_public_evidence_privacy(
                        leaked_value,
                        forbidden_values=(sentinel,),
                    )

    def test_receipt_is_valid_and_claims_only_provider_free_counts(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = self.materialize(Path(temporary))
            evidence = PREFLIGHT.qualify(
                set_directory=directory,
                catalogue_path=PREFLIGHT.CATALOGUE_PATH,
                validated_at=self.validated_at,
            )
            receipt = json.loads(evidence["value-receipt.json"])
            self.assertEqual(VALUE_VALIDATOR.validate(receipt), [])
            measurements = {
                item["id"]: item["result"] for item in receipt["measurements"]
            }
            self.assertEqual(measurements["live_authorization_label_count"], 4)
            self.assertEqual(measurements["authorization_validation_count"], 13)
            self.assertEqual(measurements["subject_rendering_count"], 0)
            self.assertEqual(measurements["provider_model_launch_count"], 0)
            self.assertEqual(measurements["authorization_consumption_count"], 0)
            self.assertEqual(measurements["experiment_run_count"], 0)
            self.assertEqual(measurements["experiment_result_count"], 0)

    def test_validation_path_has_no_provider_or_process_launch_capability(self):
        PREFLIGHT.provider_free_source_audit()


if __name__ == "__main__":
    unittest.main()
