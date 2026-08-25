#!/usr/bin/env python3
"""Validate the authoritative Opsle program and experiment registries."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "program" / "registry.json"
DEFAULT_EXPERIMENTS = ROOT / "program" / "experiments.json"

EXPECTED_REPOSITORIES = (
    "agent-trajectory-profiler",
    "semantic-edit-protocol",
    "durable-supervisor",
    "event-driven-agent-wakeup",
    "context-firewall",
    "decision-evidence-protocol",
    "agent-state-ledger",
    "agent-scheduler-runtime",
    "verifiable-agent-handoff",
    "agent-routing-policy",
    "agent-resource-claims",
    "agent-discovery-control",
    "agent-execution-authorization",
    "controlled-agent-acceptance",
    "agent-recovery-policy",
    "ephemeral-agent-workers",
    "research",
    "site",
    ".github",
)

LIFECYCLE_STAGES = (
    "THEORY",
    "SPECIFIED",
    "PROTOTYPED",
    "VERIFIED",
    "BENCHMARK_READY",
    "EXPERIMENTED",
    "REPRODUCED",
    "DOCUMENTED",
    "COMPLETE",
)

REQUIRED_REPOSITORY_FIELDS = (
    "name",
    "github_url",
    "default_branch",
    "last_verified_head_sha",
    "project_type",
    "purpose",
    "lifecycle_stage",
    "implementation_status",
    "implementation_requirement",
    "specification_status",
    "test_status",
    "benchmark_status",
    "measured_experiment_status",
    "reproducibility_status",
    "documentation_status",
    "site_publication_status",
    "known_limitations",
    "dependencies",
    "dependents",
    "active_experiment_ids",
    "blockers",
    "next_task",
    "evidence",
    "completion_criteria",
    "completion_evidence",
    "completion_status",
    "program_state",
    "last_verified_at",
)

REQUIRED_EXPERIMENT_FIELDS = (
    "id",
    "title",
    "status",
    "hypothesis",
    "participating_repositories",
    "baseline",
    "experimental_arms",
    "primary_metric",
    "secondary_metrics",
    "correctness_gate",
    "failure_classifications",
    "dataset_fixture_identity",
    "model_provider_configuration",
    "run_identities",
    "result_artifacts",
    "replication_status",
    "verdict",
    "blockers",
    "next_task",
)

COMPLETION_GATES = frozenset(
    {
        "problem_statement",
        "public_specification",
        "implementation_or_validator",
        "automated_tests",
        "benchmark_harness",
        "baseline_comparison",
        "measured_experiment",
        "correctness_analysis",
        "failure_modes",
        "reproducibility_instructions",
        "independent_replication",
        "known_limitations",
        "documentation_examples",
        "publication_material",
        "registry_evidence",
        "visible_value_instrumentation",
        "machine_value_receipt",
        "operator_visible_indicator",
        "durable_metric_integration",
        "visible_value_limitations",
    }
)

VISIBLE_VALUE_GATES = frozenset(
    {
        "visible_value_instrumentation",
        "machine_value_receipt",
        "operator_visible_indicator",
        "durable_metric_integration",
        "visible_value_limitations",
    }
)

SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: top-level value must be an object")
    return value


def _valid_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not value.endswith("Z"):
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _missing_fields(value: dict[str, Any], required: tuple[str, ...]) -> list[str]:
    return [field for field in required if field not in value]


def validate(
    registry: dict[str, Any], experiments: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    repositories = registry.get("repositories")
    experiment_entries = experiments.get("experiments")

    if not isinstance(repositories, list):
        return ["registry.repositories must be an array"]
    if not isinstance(experiment_entries, list):
        return ["experiments.experiments must be an array"]

    expected = set(EXPECTED_REPOSITORIES)
    names = [repo.get("name") for repo in repositories if isinstance(repo, dict)]
    counts = Counter(names)
    duplicates = sorted(name for name, count in counts.items() if count > 1)
    missing = sorted(expected - set(names))
    unexpected = sorted(set(names) - expected, key=str)

    if len(repositories) != len(EXPECTED_REPOSITORIES):
        errors.append(
            f"expected {len(EXPECTED_REPOSITORIES)} repositories, found {len(repositories)}"
        )
    if registry.get("authoritative_repository_count") != len(EXPECTED_REPOSITORIES):
        errors.append("authoritative_repository_count must be 19")
    if duplicates:
        errors.append(f"duplicate repositories: {', '.join(duplicates)}")
    if missing:
        errors.append(f"missing repositories: {', '.join(missing)}")
    if unexpected:
        errors.append(f"unexpected repositories: {', '.join(map(str, unexpected))}")

    for field in (
        "program",
        "lifecycle_model",
        "experiment_registry",
        "current_highest_priority_workstream",
        "recommended_next_execution",
        "last_verified_at",
    ):
        if not registry.get(field):
            errors.append(f"registry.{field} is required")
    if not _valid_timestamp(registry.get("last_verified_at")):
        errors.append("registry.last_verified_at must be an ISO-8601 UTC timestamp")

    experiment_ids = [
        item.get("id") for item in experiment_entries if isinstance(item, dict)
    ]
    duplicate_experiments = sorted(
        item for item, count in Counter(experiment_ids).items() if count > 1
    )
    if duplicate_experiments:
        errors.append(f"duplicate experiment IDs: {', '.join(duplicate_experiments)}")
    experiment_id_set = set(experiment_ids)

    repo_by_name = {
        repo["name"]: repo
        for repo in repositories
        if isinstance(repo, dict) and isinstance(repo.get("name"), str)
    }

    for index, repo in enumerate(repositories):
        label = repo.get("name", f"index {index}") if isinstance(repo, dict) else f"index {index}"
        if not isinstance(repo, dict):
            errors.append(f"repository {label} must be an object")
            continue
        for field in _missing_fields(repo, REQUIRED_REPOSITORY_FIELDS):
            errors.append(f"{label}: missing required field {field}")
        if repo.get("lifecycle_stage") not in LIFECYCLE_STAGES:
            errors.append(f"{label}: invalid lifecycle stage {repo.get('lifecycle_stage')!r}")
        if repo.get("project_type") not in {"concept", "program infrastructure"}:
            errors.append(f"{label}: invalid project_type {repo.get('project_type')!r}")
        if repo.get("program_state") not in {"active", "waiting", "complete"}:
            errors.append(f"{label}: invalid program_state {repo.get('program_state')!r}")
        if repo.get("completion_status") not in {
            "INCOMPLETE",
            "COMPLETE",
            "REJECTED",
            "SUPERSEDED",
        }:
            errors.append(f"{label}: invalid completion_status {repo.get('completion_status')!r}")
        if not SHA_RE.fullmatch(str(repo.get("last_verified_head_sha", ""))):
            errors.append(f"{label}: last_verified_head_sha must be 40 lowercase hex characters")
        if repo.get("github_url") != f"https://github.com/opsle/{repo.get('name')}":
            errors.append(f"{label}: GitHub URL does not match repository name")
        if not _valid_timestamp(repo.get("last_verified_at")):
            errors.append(f"{label}: last_verified_at must be an ISO-8601 UTC timestamp")

        for field in (
            "known_limitations",
            "dependencies",
            "dependents",
            "active_experiment_ids",
            "blockers",
            "evidence",
            "completion_criteria",
            "completion_evidence",
        ):
            if field in repo and not isinstance(repo[field], list):
                errors.append(f"{label}: {field} must be an array")
        for field in ("known_limitations", "evidence", "completion_criteria"):
            if isinstance(repo.get(field), list) and not repo[field]:
                errors.append(f"{label}: {field} must not be empty")

        for dependency in repo.get("dependencies", []):
            if dependency not in expected:
                errors.append(f"{label}: dependency references nonexistent project {dependency}")
            elif label not in repo_by_name.get(dependency, {}).get("dependents", []):
                errors.append(f"{label}: dependency {dependency} lacks reciprocal dependent entry")
        for dependent in repo.get("dependents", []):
            if dependent not in expected:
                errors.append(f"{label}: dependent references nonexistent project {dependent}")
            elif label not in repo_by_name.get(dependent, {}).get("dependencies", []):
                errors.append(f"{label}: dependent {dependent} lacks reciprocal dependency entry")
        for experiment_id in repo.get("active_experiment_ids", []):
            if experiment_id not in experiment_id_set:
                errors.append(f"{label}: references nonexistent experiment {experiment_id}")

        complete = repo.get("completion_status") == "COMPLETE"
        complete_stage = repo.get("lifecycle_stage") == "COMPLETE"
        if complete != complete_stage:
            errors.append(f"{label}: COMPLETE stage and completion_status must agree")
        if complete:
            evidence = repo.get("completion_evidence", [])
            gate_ids = set()
            for item in evidence:
                if not isinstance(item, dict) or not item.get("artifact"):
                    continue
                gate = item.get("gate")
                disposition = item.get("disposition", "EVIDENCED")
                if disposition == "EVIDENCED":
                    gate_ids.add(gate)
                    continue
                valid_exception = (
                    disposition == "NOT_APPLICABLE"
                    and gate in VISIBLE_VALUE_GATES
                    and item.get("exception_scope") == "NON_EXECUTABLE_SPECIFICATION"
                    and isinstance(item.get("justification"), str)
                    and len(item["justification"].strip()) >= 20
                )
                if valid_exception:
                    gate_ids.add(gate)
                else:
                    errors.append(
                        f"{label}: invalid completion exception for gate {gate!r}"
                    )
            missing_gates = sorted(COMPLETION_GATES - gate_ids)
            if missing_gates:
                errors.append(
                    f"{label}: COMPLETE without required completion evidence: {', '.join(missing_gates)}"
                )
            if repo.get("blockers"):
                errors.append(f"{label}: COMPLETE project cannot have blockers")
            if repo.get("program_state") != "complete":
                errors.append(f"{label}: COMPLETE project must have program_state complete")

    for index, experiment in enumerate(experiment_entries):
        label = experiment.get("id", f"index {index}") if isinstance(experiment, dict) else f"index {index}"
        if not isinstance(experiment, dict):
            errors.append(f"experiment {label} must be an object")
            continue
        for field in _missing_fields(experiment, REQUIRED_EXPERIMENT_FIELDS):
            errors.append(f"experiment {label}: missing required field {field}")
        for project in experiment.get("participating_repositories", []):
            if project not in expected:
                errors.append(f"experiment {label}: references nonexistent project {project}")
        roles = experiment.get("roles", {})
        role_projects = []
        if isinstance(roles, dict):
            role_projects.append(roles.get("primary"))
            role_projects.extend(roles.get("expected_support", []))
            role_projects.extend(roles.get("potential_support", []))
        for project in role_projects:
            if project not in expected:
                errors.append(f"experiment {label}: role references nonexistent project {project}")
        if experiment.get("status") == "PLANNED":
            if experiment.get("run_identities") or experiment.get("result_artifacts"):
                errors.append(f"experiment {label}: PLANNED experiment cannot claim runs or results")

    exp001 = next((item for item in experiment_entries if item.get("id") == "EXP-001"), None)
    if exp001 is None:
        errors.append("EXP-001 is required")
    else:
        if exp001.get("status") != "PLANNED":
            errors.append("EXP-001 must remain PLANNED during bootstrap")
        if exp001.get("roles", {}).get("primary") != "context-firewall":
            errors.append("EXP-001 primary project must be context-firewall")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--experiments", type=Path, default=DEFAULT_EXPERIMENTS)
    args = parser.parse_args(argv)
    try:
        registry = load_json(args.registry)
        experiments = load_json(args.experiments)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    errors = validate(registry, experiments)
    if errors:
        print("FAIL: program registry is invalid", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(
        f"PASS: {len(EXPECTED_REPOSITORIES)} repositories and "
        f"{len(experiments['experiments'])} experiments validated"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
