#!/usr/bin/env python3
"""Validate the authoritative Opsle program and experiment registries."""

from __future__ import annotations

import argparse
import hashlib
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
DEFAULT_THEORY_REGISTRY = ROOT / "program" / "theory-registry.json"
DEFAULT_THEORY_MAP = ROOT / "program" / "THEORY_MAP.md"

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
    "gearbox",
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

THEORY_CLASSIFICATIONS = frozenset(
    {
        "INDEPENDENT_OPSLE_TOOL",
        "CROSS_CUTTING_PROTOCOL",
        "GEARBOX_CORE",
        "GEARBOX_SUPPORTING_POLICY",
        "DURABLE_ORCHESTRATION",
        "EXECUTION_ISOLATION_INFRASTRUCTURE",
        "RESEARCH_ONLY_HYPOTHESIS",
    }
)

THEORY_DISPOSITIONS = frozenset(
    {
        "KEEP_STANDALONE",
        "KEEP_AS_PROTOCOL",
        "KEEP_AS_RESEARCH",
        "FUTURE_GEARBOX_MODULE",
        "FUTURE_GEARBOX_POLICY",
        "CONSOLIDATE_WITH_OTHER",
        "RENAME",
        "DEPRECATE_AFTER_PROVENANCE_PRESERVATION",
    }
)

THEORY_CONFIDENCE_LEVELS = frozenset({"HIGH", "MEDIUM_HIGH", "MEDIUM", "LOW"})

REQUIRED_THEORY_CONCEPT_FIELDS = (
    "id",
    "canonical_concept_name",
    "one_sentence_definition",
    "original_problem",
    "primary_classification",
    "current_repository",
    "recommended_disposition",
    "disposition_rationale",
    "disposition_gain",
    "disposition_risk",
    "provenance_concerns",
    "relationship_to_gearbox",
    "relationship_to_context_firewall",
    "dependencies",
    "consumers",
    "current_implementation_fidelity",
    "drift_status",
    "current_name_accuracy",
    "evidence_references",
    "confidence",
    "unresolved_questions",
)

CANONICAL_GEARBOX_DEFINITION = (
    "Agent Gearbox lets a powerful primary developer delegate routine operations "
    "and bounded work to deterministic software or less expensive models, then "
    "receive only the compact result needed to continue."
)

CANONICAL_CONTEXT_FIREWALL_DEFINITION = (
    "Context Firewall is a deterministic boundary that keeps operational noise out "
    "of an AI agent's context while preserving the compact evidence, provenance, "
    "and escalation path the agent needs to make correct decisions."
)

GEARBOX_VS_DURABLE_SUPERVISOR = (
    "Gearbox enhances a primary developer; durable orchestration owns autonomous "
    "objective progress across durable state and multiple activations without "
    "requiring that developer to remain continuously active."
)

EXP001_CONTEXT_FIREWALL_SCOPE = (
    "The deterministic multi-adapter evidence boundary is the concept; the current "
    "TAP-subset reducer is one adapter prototype."
)

EXP001_RECONCILED_HYPOTHESIS = (
    "The experiment continues to test correctness under reduced model-visible "
    "context, not the definition or existence of Context Firewall."
)

EXP001_RECONCILED_SEQUENCE = (
    "The offline benchmark freeze is the immediate next execution after the "
    "completed public Gearbox publication; no model/provider subject is "
    "authorized by the freeze."
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


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(value: Any, *, allow_empty: bool = True) -> bool:
    return (
        isinstance(value, list)
        and (allow_empty or bool(value))
        and all(_nonempty_string(item) for item in value)
    )


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
    names: list[str] = []
    for index, repo in enumerate(repositories):
        if not isinstance(repo, dict):
            continue
        name = repo.get("name")
        if isinstance(name, str):
            names.append(name)
        else:
            errors.append(f"repository index {index}: name must be a string")
    counts = Counter(names)
    duplicates = sorted(name for name, count in counts.items() if count > 1)
    missing = sorted(expected - set(names))
    unexpected = sorted(set(names) - expected, key=str)

    if len(repositories) != len(EXPECTED_REPOSITORIES):
        errors.append(
            f"expected {len(EXPECTED_REPOSITORIES)} repositories, found {len(repositories)}"
        )
    if registry.get("authoritative_repository_count") != len(EXPECTED_REPOSITORIES):
        errors.append(
            f"authoritative_repository_count must be {len(EXPECTED_REPOSITORIES)}"
        )
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
        "theory_registry",
        "theory_map",
        "theory_reconciliation",
        "current_highest_priority_workstream",
        "recommended_next_execution",
        "last_verified_at",
    ):
        if not registry.get(field):
            errors.append(f"registry.{field} is required")
    if not _valid_timestamp(registry.get("last_verified_at")):
        errors.append("registry.last_verified_at must be an ISO-8601 UTC timestamp")

    experiment_ids: list[str] = []
    for index, item in enumerate(experiment_entries):
        if not isinstance(item, dict):
            continue
        experiment_id = item.get("id")
        if isinstance(experiment_id, str):
            experiment_ids.append(experiment_id)
        else:
            errors.append(f"experiment index {index}: id must be a string")
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
        label = (
            repo.get("name")
            if isinstance(repo, dict) and isinstance(repo.get("name"), str)
            else f"index {index}"
        )
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

        dependencies = repo.get("dependencies")
        if not isinstance(dependencies, list):
            dependencies = []
        for dependency in dependencies:
            if not isinstance(dependency, str):
                errors.append(f"{label}: dependency entries must be strings")
                continue
            if dependency not in expected:
                errors.append(f"{label}: dependency references nonexistent project {dependency}")
            elif label not in repo_by_name.get(dependency, {}).get("dependents", []):
                errors.append(f"{label}: dependency {dependency} lacks reciprocal dependent entry")
        dependents = repo.get("dependents")
        if not isinstance(dependents, list):
            dependents = []
        for dependent in dependents:
            if not isinstance(dependent, str):
                errors.append(f"{label}: dependent entries must be strings")
                continue
            if dependent not in expected:
                errors.append(f"{label}: dependent references nonexistent project {dependent}")
            elif label not in repo_by_name.get(dependent, {}).get("dependencies", []):
                errors.append(f"{label}: dependent {dependent} lacks reciprocal dependency entry")
        active_experiment_ids = repo.get("active_experiment_ids")
        if not isinstance(active_experiment_ids, list):
            active_experiment_ids = []
        for experiment_id in active_experiment_ids:
            if not isinstance(experiment_id, str):
                errors.append(f"{label}: active experiment IDs must be strings")
                continue
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
                if not isinstance(gate, str):
                    errors.append(f"{label}: completion evidence gate must be a string")
                    continue
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
        label = (
            experiment.get("id")
            if isinstance(experiment, dict) and isinstance(experiment.get("id"), str)
            else f"index {index}"
        )
        if not isinstance(experiment, dict):
            errors.append(f"experiment {label} must be an object")
            continue
        for field in _missing_fields(experiment, REQUIRED_EXPERIMENT_FIELDS):
            errors.append(f"experiment {label}: missing required field {field}")
        participating = experiment.get("participating_repositories")
        if not isinstance(participating, list):
            errors.append(f"experiment {label}: participating_repositories must be an array")
            participating = []
        for project in participating:
            if not isinstance(project, str):
                errors.append(f"experiment {label}: participating repository entries must be strings")
                continue
            if project not in expected:
                errors.append(f"experiment {label}: references nonexistent project {project}")
        roles = experiment.get("roles", {})
        role_projects: list[Any] = []
        if isinstance(roles, dict):
            role_projects.append(roles.get("primary"))
            for field in ("expected_support", "potential_support"):
                support = roles.get(field)
                if isinstance(support, list):
                    role_projects.extend(support)
                else:
                    errors.append(f"experiment {label}: roles.{field} must be an array")
        else:
            errors.append(f"experiment {label}: roles must be an object")
        for project in role_projects:
            if not isinstance(project, str):
                errors.append(f"experiment {label}: role repository entries must be strings")
                continue
            if project not in expected:
                errors.append(f"experiment {label}: role references nonexistent project {project}")
        if experiment.get("status") == "PLANNED":
            if experiment.get("run_identities") or experiment.get("result_artifacts"):
                errors.append(f"experiment {label}: PLANNED experiment cannot claim runs or results")

    exp001 = next(
        (
            item
            for item in experiment_entries
            if isinstance(item, dict) and item.get("id") == "EXP-001"
        ),
        None,
    )
    if exp001 is None:
        errors.append("EXP-001 is required")
    else:
        if exp001.get("status") != "PLANNED":
            errors.append("EXP-001 must remain PLANNED during bootstrap")
        roles = exp001.get("roles")
        if not isinstance(roles, dict) or roles.get("primary") != "context-firewall":
            errors.append("EXP-001 primary project must be context-firewall")
        reconciliation = exp001.get("theory_reconciliation")
        if not isinstance(reconciliation, dict):
            errors.append("EXP-001 theory_reconciliation must be an object")
        else:
            if not _valid_timestamp(reconciliation.get("verified_at")):
                errors.append("EXP-001 reconciliation verified_at must be an ISO-8601 UTC timestamp")
            if reconciliation.get("context_firewall_definition") != EXP001_CONTEXT_FIREWALL_SCOPE:
                errors.append("EXP-001 reconciliation Context Firewall scope drifted")
            if reconciliation.get("experimental_hypothesis") != EXP001_RECONCILED_HYPOTHESIS:
                errors.append("EXP-001 reconciled hypothesis drifted")
            if reconciliation.get("gearbox_dependency") != "NONE":
                errors.append("EXP-001 must remain independent of Gearbox")
            if reconciliation.get("sequence") != EXP001_RECONCILED_SEQUENCE:
                errors.append("EXP-001 reconciliation sequence drifted")
            if reconciliation.get("model_provider_runs_added") != 0:
                errors.append("EXP-001 reconciliation must record zero model/provider runs")
            if (
                reconciliation.get("gearbox_publication_status")
                != "COMPLETED_INDEPENDENT_PREREQUISITE"
            ):
                errors.append("EXP-001 must record the completed independent Gearbox publication")
            gearbox_repository = repo_by_name.get("gearbox", {})
            if reconciliation.get("gearbox_repository_head_sha") != gearbox_repository.get(
                "last_verified_head_sha"
            ):
                errors.append("EXP-001 Gearbox publication SHA must match the registry")

    return errors


def _canonical_json_sha256(value: dict[str, Any]) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_theory(
    theory: dict[str, Any],
    registry: dict[str, Any],
    theory_map_text: str,
) -> list[str]:
    errors: list[str] = []
    concepts = theory.get("concepts")
    repositories = registry.get("repositories")
    if not isinstance(concepts, list):
        return ["theory.concepts must be an array"]
    if not isinstance(repositories, list):
        return ["registry.repositories must be an array before theory validation"]

    if theory.get("registry_id") != "opsle.theory-registry.v1":
        errors.append("theory.registry_id must be opsle.theory-registry.v1")
    if theory.get("schema_version") != 1:
        errors.append("theory.schema_version must be 1")
    if theory.get("source_repository_count") != len(EXPECTED_REPOSITORIES):
        errors.append(
            f"theory.source_repository_count must be {len(EXPECTED_REPOSITORIES)}"
        )
    if theory.get("current_concept_repository_count") != 17:
        errors.append("theory.current_concept_repository_count must be 17")
    if not _valid_timestamp(theory.get("verified_at")):
        errors.append("theory.verified_at must be an ISO-8601 UTC timestamp")

    canonical = theory.get("canonical_definitions", {})
    if not isinstance(canonical, dict):
        canonical = {}
        errors.append("theory.canonical_definitions must be an object")
    if canonical.get("gearbox") != CANONICAL_GEARBOX_DEFINITION:
        errors.append("theory canonical Gearbox definition drifted")
    if canonical.get("context_firewall") != CANONICAL_CONTEXT_FIREWALL_DEFINITION:
        errors.append("theory canonical Context Firewall definition drifted")

    ids: list[str] = []
    for index, item in enumerate(concepts):
        if not isinstance(item, dict):
            continue
        concept_id = item.get("id")
        if isinstance(concept_id, str):
            ids.append(concept_id)
        else:
            errors.append(f"theory concept index {index}: id must be a string")
    duplicate_ids = sorted(item for item, count in Counter(ids).items() if count > 1)
    if duplicate_ids:
        errors.append(f"duplicate theory concept IDs: {', '.join(duplicate_ids)}")
    if len(concepts) != 17:
        errors.append(f"expected 17 theory concepts, found {len(concepts)}")

    current_concept_repositories = set(EXPECTED_REPOSITORIES[:17])
    current_mappings: list[str] = []
    concept_ids = set(ids)
    concept_by_id = {
        item["id"]: item
        for item in concepts
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    for index, concept in enumerate(concepts):
        label = (
            concept.get("id")
            if isinstance(concept, dict) and isinstance(concept.get("id"), str)
            else f"index {index}"
        )
        if not isinstance(concept, dict):
            errors.append(f"theory concept {label} must be an object")
            continue
        for field in _missing_fields(concept, REQUIRED_THEORY_CONCEPT_FIELDS):
            errors.append(f"theory concept {label}: missing required field {field}")
        for field in (
            "id",
            "canonical_concept_name",
            "one_sentence_definition",
            "original_problem",
            "disposition_rationale",
            "disposition_gain",
            "disposition_risk",
            "provenance_concerns",
            "relationship_to_gearbox",
            "relationship_to_context_firewall",
            "drift_status",
            "current_name_accuracy",
        ):
            if not _nonempty_string(concept.get(field)):
                errors.append(f"theory concept {label}: {field} must be a nonempty string")
        if concept.get("primary_classification") not in THEORY_CLASSIFICATIONS:
            errors.append(f"theory concept {label}: invalid primary classification")
        if concept.get("recommended_disposition") not in THEORY_DISPOSITIONS:
            errors.append(f"theory concept {label}: invalid recommended disposition")
        if concept.get("confidence") not in THEORY_CONFIDENCE_LEVELS:
            errors.append(f"theory concept {label}: invalid confidence")
        current_repository = concept.get("current_repository")
        if current_repository is not None:
            if not isinstance(current_repository, str):
                errors.append(
                    f"theory concept {label}: current_repository must be a string or null"
                )
            else:
                current_mappings.append(current_repository)
            if (
                isinstance(current_repository, str)
                and current_repository not in current_concept_repositories
            ):
                errors.append(
                    f"theory concept {label}: invalid current repository {current_repository!r}"
                )
        for field in ("dependencies", "consumers", "evidence_references", "unresolved_questions"):
            values = concept.get(field)
            if not isinstance(values, list) or not values:
                if field in {"dependencies", "consumers"} and values == []:
                    continue
                errors.append(f"theory concept {label}: {field} must be a nonempty array")
                continue
            for value in values:
                if not _nonempty_string(value):
                    errors.append(
                        f"theory concept {label}: {field} entries must be nonempty strings"
                    )
                    continue
                if field in {"dependencies", "consumers"} and value not in concept_ids:
                    errors.append(
                        f"theory concept {label}: relationship references missing concept {value}"
                    )
        fidelity = concept.get("current_implementation_fidelity")
        if (
            not isinstance(fidelity, dict)
            or not _nonempty_string(fidelity.get("status"))
            or not _nonempty_string(fidelity.get("assessment"))
        ):
            errors.append(
                f"theory concept {label}: current_implementation_fidelity requires status and assessment"
            )

    mapping_counts = Counter(current_mappings)
    duplicate_mappings = sorted(name for name, count in mapping_counts.items() if count > 1)
    missing_mappings = sorted(current_concept_repositories - set(current_mappings))
    if duplicate_mappings:
        errors.append(f"duplicate current concept repository mappings: {', '.join(duplicate_mappings)}")
    if missing_mappings:
        errors.append(f"missing current concept repository mappings: {', '.join(missing_mappings)}")
    if len(current_mappings) != 17:
        errors.append(f"expected 17 current concept repository mappings, found {len(current_mappings)}")

    gearbox = concept_by_id.get("gearbox")
    if gearbox is None:
        errors.append("theory concept gearbox is required")
    else:
        if gearbox.get("current_repository") != "gearbox":
            errors.append("Gearbox must claim the current gearbox repository")
        if gearbox.get("primary_classification") != "GEARBOX_CORE":
            errors.append("Gearbox primary classification must be GEARBOX_CORE")
        if gearbox.get("one_sentence_definition") != CANONICAL_GEARBOX_DEFINITION:
            errors.append("Gearbox concept definition drifted")
    context_firewall = concept_by_id.get("context-firewall")
    if context_firewall is None:
        errors.append("theory concept context-firewall is required")
    else:
        if context_firewall.get("one_sentence_definition") != CANONICAL_CONTEXT_FIREWALL_DEFINITION:
            errors.append("Context Firewall concept definition drifted")
        required_adapters = {
            "tests",
            "lint",
            "typecheck",
            "git",
            "build_compiler",
            "process_service",
            "helper_agent_result",
        }
        adapters = context_firewall.get("intended_adapter_families")
        if not _string_list(adapters, allow_empty=False) or set(adapters) != required_adapters:
            errors.append("Context Firewall intended adapter families are incomplete")

    repo_names = {
        item.get("name")
        for item in repositories
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    if "gearbox" not in repo_names:
        errors.append("the 20-repository registry must contain gearbox")
    if registry.get("theory_registry") != "program/theory-registry.json":
        errors.append("registry.theory_registry path is invalid")
    if registry.get("theory_map") != "program/THEORY_MAP.md":
        errors.append("registry.theory_map path is invalid")
    reconciliation = registry.get("theory_reconciliation", {})
    if not isinstance(reconciliation, dict):
        reconciliation = {}
        errors.append("registry.theory_reconciliation must be an object")
    if reconciliation.get("canonical_gearbox_definition") != CANONICAL_GEARBOX_DEFINITION:
        errors.append("registry Gearbox reconciliation definition drifted")
    if reconciliation.get("canonical_context_firewall_definition") != CANONICAL_CONTEXT_FIREWALL_DEFINITION:
        errors.append("registry Context Firewall reconciliation definition drifted")
    if reconciliation.get("status") != "IMPLEMENTED_HOME_REGISTERED":
        errors.append(
            "registry theory reconciliation status must record the implemented home"
        )
    if not _valid_timestamp(reconciliation.get("verified_at")):
        errors.append("registry theory reconciliation verified_at must be an ISO-8601 UTC timestamp")
    if reconciliation.get("gearbox_vs_durable_supervisor") != GEARBOX_VS_DURABLE_SUPERVISOR:
        errors.append("registry Gearbox versus Durable Supervisor distinction drifted")
    if reconciliation.get("gearbox_repository_status") != "CREATED_PROTOTYPED":
        errors.append("registry must record Gearbox as created and prototyped")
    if reconciliation.get("repository_topology_operations_executed") is not True:
        errors.append("registry must record the authorized Gearbox repository creation")
    if reconciliation.get("lifecycle_changes_executed") is not True:
        errors.append("registry must record the evidence-backed Gearbox lifecycle assignment")
    if reconciliation.get("existing_repository_lifecycle_changes_executed") is not False:
        errors.append("registry must record no existing-repository lifecycle changes")
    if reconciliation.get("existing_repository_dispositions_executed") is not False:
        errors.append("registry must record no executed existing-repository dispositions")
    if reconciliation.get("model_provider_runs_added") != 0:
        errors.append("registry must record zero model/provider runs for Gearbox publication")
    if reconciliation.get("taslos_tasks_source_modified") is not False:
        errors.append("registry must record Taslos Tasks as unmodified")

    publication = registry.get("gearbox_publication")
    if not isinstance(publication, dict):
        errors.append("registry.gearbox_publication must be an object")
    else:
        gearbox_repository = next(
            (
                item
                for item in repositories
                if isinstance(item, dict) and item.get("name") == "gearbox"
            ),
            {},
        )
        if publication.get("status") != "RELEASED":
            errors.append("registry Gearbox publication status must be RELEASED")
        if publication.get("repository") != "gearbox":
            errors.append("registry Gearbox publication repository must be gearbox")
        if publication.get("github_url") != "https://github.com/opsle/gearbox":
            errors.append("registry Gearbox publication URL is invalid")
        if publication.get("pull_request") != "https://github.com/opsle/gearbox/pull/1":
            errors.append("registry Gearbox publication PR is invalid")
        if publication.get("ci_status") != "SUCCESS":
            errors.append("registry Gearbox publication CI must be successful")
        if not _nonempty_string(publication.get("ci_run")):
            errors.append("registry Gearbox publication CI run is required")
        if publication.get("final_main_sha") != gearbox_repository.get(
            "last_verified_head_sha"
        ):
            errors.append("registry Gearbox publication SHA must match repository HEAD")
        if gearbox_repository.get("lifecycle_stage") != "PROTOTYPED":
            errors.append("registered Gearbox lifecycle stage must be PROTOTYPED")
        for field in ("final_main_sha", "implementation_revision", "source_revision"):
            if not isinstance(publication.get(field), str) or not SHA_RE.fullmatch(
                publication[field]
            ):
                errors.append(f"registry Gearbox publication {field} must be a Git SHA")
        if publication.get("source_repository") != "sneakocom/taslos-tasks":
            errors.append("registry Gearbox publication source repository is invalid")
        if publication.get("source_modified") is not False:
            errors.append("registry Gearbox publication must record an unchanged source")
        if publication.get("provider_model_runs") != 0:
            errors.append("registry Gearbox publication must record zero provider/model runs")
        if publication.get("repository_consolidations") != 0:
            errors.append("registry Gearbox publication must record zero consolidations")

    expected_hash = _canonical_json_sha256(theory)
    hash_match = re.search(
        r"Theory registry canonical SHA-256:\s*\n`([0-9a-f]{64})`\.",
        theory_map_text,
    )
    if hash_match is None or hash_match.group(1) != expected_hash:
        errors.append("THEORY_MAP canonical theory-registry hash is stale")

    rows = re.findall(
        r"^\| `([^`]+)` \| `([A-Z_]+)` \| `([A-Z_]+)` \| `([A-Z_]+)` \| .+ \|$",
        theory_map_text,
        flags=re.MULTILINE,
    )
    row_counts = Counter(row[0] for row in rows)
    for repository in sorted(current_concept_repositories):
        concept = next(
            (
                item
                for item in concepts
                if isinstance(item, dict)
                and item.get("current_repository") == repository
            ),
            None,
        )
        matching = [row for row in rows if row[0] == repository]
        if row_counts.get(repository) != 1 or concept is None:
            errors.append(f"THEORY_MAP must contain exactly one classification row for {repository}")
            continue
        _, classification, disposition, confidence = matching[0]
        if classification != concept.get("primary_classification"):
            errors.append(f"THEORY_MAP classification drift for {repository}")
        if disposition != concept.get("recommended_disposition"):
            errors.append(f"THEORY_MAP disposition drift for {repository}")
        if confidence != concept.get("confidence"):
            errors.append(f"THEORY_MAP confidence drift for {repository}")
    unexpected_rows = sorted(set(row_counts) - current_concept_repositories)
    if unexpected_rows:
        errors.append(f"THEORY_MAP contains unexpected classification rows: {', '.join(unexpected_rows)}")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--experiments", type=Path, default=DEFAULT_EXPERIMENTS)
    parser.add_argument("--theory-registry", type=Path, default=DEFAULT_THEORY_REGISTRY)
    parser.add_argument("--theory-map", type=Path, default=DEFAULT_THEORY_MAP)
    args = parser.parse_args(argv)
    try:
        registry = load_json(args.registry)
        experiments = load_json(args.experiments)
        theory = load_json(args.theory_registry)
        theory_map_text = args.theory_map.read_text(encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    errors = validate(registry, experiments)
    errors.extend(validate_theory(theory, registry, theory_map_text))
    if errors:
        print("FAIL: program registry is invalid", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(
        f"PASS: {len(EXPECTED_REPOSITORIES)} repositories, "
        f"{len(theory['concepts'])} concepts, and "
        f"{len(experiments['experiments'])} experiments validated"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
