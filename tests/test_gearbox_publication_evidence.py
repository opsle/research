from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "program" / "evidence" / "gearbox-publication"


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path} must contain an object")
    return value


class GearboxPublicationEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = load(ROOT / "program" / "registry.json")
        self.theory = load(ROOT / "program" / "theory-registry.json")
        self.decision = load(EVIDENCE / "decision-evidence-validation.json")
        self.trajectory = load(EVIDENCE / "trajectory-summary.json")
        self.repositories = {
            item["name"]: item for item in self.registry["repositories"]
        }

    def test_consumers_bind_one_public_receipt(self):
        self.assertEqual(self.decision["input"], self.trajectory["input"])
        self.assertRegex(self.decision["input"]["sha256"], r"^[0-9a-f]{64}$")
        self.assertIn(
            self.repositories["gearbox"]["last_verified_head_sha"],
            self.decision["input"]["locator"],
        )

    def test_consumer_revisions_and_results_are_exact(self):
        self.assertEqual(
            self.decision["validator"]["revision"],
            self.repositories["decision-evidence-protocol"]["last_verified_head_sha"],
        )
        self.assertEqual(
            self.trajectory["profiler"]["revision"],
            self.repositories["agent-trajectory-profiler"]["last_verified_head_sha"],
        )
        self.assertEqual(
            self.decision["result"],
            {"valid": True, "violation_count": 0, "violations": []},
        )
        self.assertTrue(self.trajectory["result"]["valid"])
        self.assertEqual(self.trajectory["result"]["violation_count"], 0)
        self.assertRegex(
            self.trajectory["result"]["summary_identity"],
            r"^sha256:[0-9a-f]{64}$",
        )

    def test_program_registries_reference_the_evidence(self):
        reference = "program/evidence/gearbox-publication/README.md"
        self.assertIn(reference, self.repositories["gearbox"]["evidence"])
        gearbox_concept = next(
            item for item in self.theory["concepts"] if item["id"] == "gearbox"
        )
        self.assertIn(reference, gearbox_concept["evidence_references"])


if __name__ == "__main__":
    unittest.main()
