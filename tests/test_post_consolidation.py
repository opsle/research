"""Reject topology regressions without reactivating archived research sources."""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from validate_program import DEFAULT_REGISTRY, DEFAULT_EXPERIMENTS, DEFAULT_THEORY_REGISTRY, load_json, validate, validate_theory
from render_program_status import render, render_priority, render_theory_map


class PostConsolidationTests(unittest.TestCase):
    def setUp(self):
        self.registry = load_json(DEFAULT_REGISTRY)
        self.experiments = load_json(DEFAULT_EXPERIMENTS)
        self.theory = load_json(DEFAULT_THEORY_REGISTRY)

    def reject(self, fragment):
        self.assertTrue(any(fragment in e for e in validate(self.registry, self.experiments)))

    def test_retired_system_cannot_be_current_authority(self):
        self.registry['program_control']['workload_authority'] = 'paperclip'
        self.reject('current workload authority')

    def test_retired_system_cannot_be_next_action_or_gate(self):
        for field in ('exact_next_execution', 'operating_question'):
            with self.subTest(field=field):
                registry = copy.deepcopy(self.registry)
                registry['program_control'][field] = 'Wait for Durable Supervisor v0.1.'
                self.assertTrue(any('retired system' in e for e in validate(registry, self.experiments)))

    def test_current_repo_cannot_depend_on_retired_source(self):
        repo = next(r for r in self.registry['repositories'] if r['name'] == 'research')
        repo['dependencies'] = ['agent-state-ledger']
        self.reject('current relationship targets historical')

    def test_retired_repo_cannot_gain_work(self):
        repo = next(r for r in self.registry['repositories'] if r['name'] == 'durable-supervisor')
        repo['next_task'] = 'Implement a new measurement.'
        self.reject('retired repository has active work')

    def test_dangling_consolidation_destination_fails(self):
        repo = next(r for r in self.registry['repositories'] if r['name'] == 'agent-state-ledger')
        repo['consolidated_into'] = 'missing-home'
        self.reject('dangling consolidation destination')

    def test_repository_count_drift_fails(self):
        self.registry['repository_counts']['current'] += 1
        self.reject('repository count drift')

    def test_retired_membership_cannot_be_deleted_with_counts(self):
        self.registry['membership']['historical'].remove('durable-supervisor')
        self.registry['repository_counts']['historical'] -= 1
        self.reject('historical membership differs')

    def test_github_housekeeping_is_not_workload_eligibility(self):
        repo = next(r for r in self.registry['repositories'] if r['name'] == '.github')
        self.assertEqual(repo['repository_disposition'], 'ACTIVE')
        self.assertFalse(repo['workload_eligible'])
        repo['workload_eligible'] = True
        self.reject('workload eligibility drift')

    def test_graphify_capability_claim_fails(self):
        self.registry['optional_tools']['graphify']['tasks_capability'] = True
        self.reject('Graphify')

    def test_graphify_cannot_enter_tasks_capability_inventory(self):
        self.registry['program_control']['opsle_tasks']['capability_ids'].append('opsle.graphify')
        self.reject('Graphify is standalone only')

    def test_retirement_cannot_promote_repository_maturity(self):
        repo = next(r for r in self.registry['repositories'] if r['name'] == 'agent-state-ledger')
        repo['lifecycle_stage'] = 'PROTOTYPED'
        self.reject('retirement must preserve highest evidenced maturity')

    def test_missing_inventory_object_reports_error(self):
        self.registry['membership'] = None
        self.reject('registry.membership must be an object')

    def test_concept_count_drift_fails(self):
        self.theory['concept_counts']['CONSOLIDATED'] -= 1
        errors = validate_theory(self.theory, self.registry, render_theory_map(self.theory, self.registry))
        self.assertTrue(any('disposition count drift' in e for e in errors))

    def test_retired_concept_cannot_gain_a_current_home(self):
        concept = next(c for c in self.theory['concepts'] if c['id'] == 'durable-supervisor')
        concept['current_repository'] = 'tasks'
        errors = validate_theory(self.theory, self.registry, render_theory_map(self.theory, self.registry))
        self.assertTrue(any('current home drift' in e for e in errors))

    def test_historical_experiment_participation_survives(self):
        repo = next(r for r in self.registry['repositories'] if r['name'] == 'verifiable-agent-handoff')
        self.assertEqual(repo['active_experiment_ids'], [])
        self.assertIn('EXP-001', repo['historical_experiment_ids'])
        repo['historical_experiment_ids'] = []
        self.reject('does not reciprocally list')

    def test_experiment_readiness_and_failed_verdict_are_preserved(self):
        exp = next(e for e in self.experiments['experiments'] if e['id'] == 'EXP-001')
        self.assertEqual(exp['status'], 'PLANNED')
        self.assertEqual(exp['run_identities'], [])
        failed = next(e for e in self.experiments['experiments'] if e['id'] == 'AV-EXP-002')
        self.assertIn('FAIL', failed['verdict'])

    def test_all_generated_views_are_deterministic(self):
        views = (
            (render, (self.registry, self.experiments), ROOT / 'PROGRAM_STATUS.md'),
            (render_priority, (self.registry, self.experiments), ROOT / 'program/PRIORITY.md'),
            (render_theory_map, (self.theory, self.registry), ROOT / 'program/THEORY_MAP.md'),
        )
        for renderer, args, path in views:
            with self.subTest(path=path.name):
                self.assertEqual(renderer(*args), renderer(*copy.deepcopy(args)))
                self.assertEqual(renderer(*args), path.read_text())
        priority = render_priority(self.registry, self.experiments)
        self.assertNotIn('Durable Supervisor', priority)
        self.assertNotIn('stopping criteria', priority)
        self.assertIn('current workload and task-management authority', priority)


if __name__ == '__main__':
    unittest.main()
