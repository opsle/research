from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXP_ROOT = ROOT / "experiments" / "exp-001"
SPEC = importlib.util.spec_from_file_location("exp001_harness", EXP_ROOT / "harness.py")
assert SPEC is not None and SPEC.loader is not None
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)


class Exp001OfflineFreezeTests(unittest.TestCase):
    def test_frozen_manifests_and_visibility_boundaries_are_valid(self):
        benchmark, arms, corpus = HARNESS.verify_static_freeze()
        self.assertEqual(benchmark["status"], "OFFLINE_COMPONENTS_FROZEN")
        self.assertEqual(benchmark["provider_model_run_count"], 0)
        self.assertEqual(len(arms["arms"]), 4)
        self.assertEqual(len(corpus["tasks"]), 6)
        for task in corpus["tasks"]:
            self.assertTrue(set(task["subject_visible"]).isdisjoint(task["evaluator_only"]))

    def test_every_initial_candidate_fails_and_accepted_candidate_passes(self):
        corpus = json.loads((EXP_ROOT / "corpus/manifest.json").read_text())
        total_cases = 0
        for task in corpus["tasks"]:
            task_id = task["id"]
            initial = HARNESS.oracle_result(
                task_id,
                EXP_ROOT / f"corpus/tasks/{task_id}/workspace/task.py",
            )
            accepted = HARNESS.oracle_result(
                task_id,
                EXP_ROOT / f"corpus/tasks/{task_id}/accepted/task.py",
            )
            self.assertEqual(initial.returncode, 1, task_id)
            self.assertEqual(accepted.returncode, 0, task_id)
            total_cases += HARNESS.tap_test_count(accepted.stdout)
        self.assertEqual(total_cases, 252)

    def test_freeze_identity_changes_on_semantic_mutation(self):
        benchmark = json.loads((EXP_ROOT / "benchmark.json").read_text())
        changed = copy.deepcopy(benchmark)
        changed["provider_model_run_count"] = 1
        self.assertNotEqual(HARNESS.object_identity(changed), benchmark["identity"])

    def test_cli_fails_closed_for_wrong_dependency_revision(self):
        result = subprocess.run(
            [
                sys.executable,
                str(EXP_ROOT / "harness.py"),
                "verify",
                "--context-firewall",
                str(ROOT),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        error = json.loads(result.stderr)
        self.assertEqual(error["code"], "OFFLINE_QUALIFICATION_FAILED")


if __name__ == "__main__":
    unittest.main()
