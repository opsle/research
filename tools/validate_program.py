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
    "affected-verification",
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

PRIORITY_LANES = ("NOW", "NEXT", "THEN", "LATER", "PARKED")

WORK_ITEM_QUALIFYING_REASONS = frozenset(
    {
        "violated invariant",
        "demonstrated defect",
        "measured inefficiency",
        "missing capability blocking the current program objective",
        "experiment requirement",
        "security or safety issue",
        "externally required release condition",
    }
)

PER_CHILD_VALUE_FIELDS = frozenset(
    {
        "child/task identity",
        "model",
        "reasoning effort",
        "Gearbox route",
        "routing rationale",
        "input tokens",
        "output tokens",
        "raw evidence/context size",
        "Context Firewall retained size",
        "reduction percentage",
        "estimated tokens avoided",
        "estimated cost avoided",
        "duration",
        "attempt number",
        "success/failure",
        "escalation/retry reason",
        "retry potentially avoidable through deterministic preflight",
    }
)

SUPERVISOR_VALUE_FIELDS = frozenset(
    {
        "total children",
        "model/effort distribution",
        "total model tokens consumed",
        "work completed deterministically without model use",
        "Context Firewall reduction",
        "estimated token/cost savings",
        "first-pass success rate",
        "repair-child rate",
        "tokens spent on retries",
        "avoidable-intelligence estimate",
    }
)

OPSLE_TASKS_MEASUREMENTS = frozenset(
    {
        "Gearbox",
        "Context Firewall",
        "Decision Evidence Protocol",
        "Agent Trajectory Profiler",
        "Affected Verification",
    }
)

OPSLE_TASKS_PROHIBITIONS = frozenset(
    {
        "move apps/taslos-tasks",
        "transfer sneakocom/taslos-tasks",
        "rename production services",
        "change schemas merely for rebranding",
        "public release",
        "DNS or TLS changes",
        "launch provider work",
    }
)

LATER_ITEMS = frozenset(
    {
        "controlled empirical experiments",
        "frozen real-workload benchmark corpus",
        "independent replication",
        "Opsle Tasks public and self-hosted release",
        "opsle.com research and public site",
        "hosted Opsle offering",
    }
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
    "The offline benchmark, launch controls, one-block coordinator, exact live "
    "authorization set, and current catalogue/pricing preflight are provider-free "
    "validated; zero authorizations are consumed and zero model/provider subjects "
    "or experiment runs/results exist."
)

EXP001_OFFLINE_RELEASE_SHA = "04234a65bf36192d63f1dd173c440d45a6604d2b"
EXP001_PREREGISTRATION_RELEASE_SHA = "31848c3f25ff9371055932657e8e2f8ad54cc8c7"
EXP001_COORDINATOR_RELEASE_SHA = "9ee43197880c18d4e185cf7e29e02a151d22a12e"
EXP001_FREEZE_IDENTITY = (
    "sha256:6ac668a2fd6b4390825a7f1470f1f8cdab05a6d2d01b41d4cfd4412e93df74d8"
)
EXP001_CORPUS_IDENTITY = (
    "sha256:07f8ef2810267a02b3aa03a45b7de3512f6066b03bd82c833394121825f98d60"
)
EXP001_ARM_IDENTITY = (
    "sha256:7ce68d9c53232f5941140edb5e3fa2fff0ac0f5bba33bda14cdf1e09888b64f3"
)
EXP001_ALLOCATION_IDENTITY = (
    "sha256:6ef1e63dd51bdd967cd9ea472ebd70714bbd50a053ba1df7491f4dbe64595a57"
)
EXP001_PREREGISTRATION_IDENTITY = (
    "sha256:e8a0ed7a303e5f4b1f5df089046b6e2fe5ab281b60f9aaeba64ddd2fe972f8c7"
)
EXP001_SUBJECT_CONFIGURATION_ID = (
    "sha256:bc46a7d72ab776db966e84d9d473efbd0a7e2028ce993eecf4a09d22577ee6cf"
)
EXP001_ALLOCATION_INDEX_IDENTITY = (
    "sha256:e32f0a4c94842f44b713d40e89c81ea85c98db13927834792620629a5ed95600"
)
EXP001_SEED_COMMITMENT = (
    "sha256:a10f7985f6fc0268ab42bc25270c3ebe434ad5655f92156ee4a5471c46a51bd3"
)
EXP001_COORDINATOR_CONTRACT_IDENTITY = (
    "sha256:873d28781f9f7fed3ffabb8e95b73cdf5d88bdb5f5b04dd7189b8e55f3466a89"
)
EXP001_COORDINATOR_REVISION = (
    "sha256:d7a2e5709fdc3b36b0fedd464bd7ccb791b067da5f327d17f7a76314f3d0af90"
)
EXP001_LIVE_PREFLIGHT_BASE_SHA = "9056b35703d94d85055868ed6778d7d79804485d"
EXP001_LIVE_AUTHORIZATION_SET_ID = (
    "exp001-live-authset-03703f1af7db48c4eab9fe33b8f55073"
)
EXP001_LIVE_AUTHORIZATION_SET_IDENTITY = (
    "sha256:8259f5b664235e5914ad4a53966a1155f8f90ad2014dc704f50ea394af32d0ec"
)
EXP001_MODEL_CATALOGUE_IDENTITY = (
    "sha256:334a48850dacf3d9ad5d5c9088287fecc78925e64e10f974cb63575b74592b3c"
)
EXP001_PRICING_PREFLIGHT_IDENTITY = (
    "sha256:a19e793c2c2453d949687f614bee65be84b9abfa6218ea25c5302af7608a38db"
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
        "program_control",
        "visible_value",
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

    control = registry.get("program_control")
    if not isinstance(control, dict):
        errors.append("registry.program_control must be an object")
    else:
        if control.get("schema_version") != 1:
            errors.append("program_control.schema_version must be 1")
        if control.get("priority_order") != list(PRIORITY_LANES):
            errors.append("program_control.priority_order must be NOW, NEXT, THEN, LATER, PARKED")
        if control.get("current_lane") != "NOW":
            errors.append("program_control.current_lane must be NOW")
        for field in ("operating_question", "exact_next_execution"):
            if not _nonempty_string(control.get(field)):
                errors.append(f"program_control.{field} must be a nonempty string")

        admission = control.get("work_item_admission")
        if not isinstance(admission, dict):
            errors.append("program_control.work_item_admission must be an object")
        else:
            if not _nonempty_string(admission.get("rule")):
                errors.append("program_control.work_item_admission.rule must be nonempty")
            reasons = admission.get("qualifying_reasons")
            if (
                not _string_list(reasons, allow_empty=False)
                or set(reasons) != WORK_ITEM_QUALIFYING_REASONS
            ):
                errors.append("program_control work-item qualifying reasons drifted")
            if not _string_list(admission.get("parked_by_default"), allow_empty=False):
                errors.append("program_control parked_by_default must be a nonempty string array")

        lanes = control.get("lanes")
        if not isinstance(lanes, list):
            errors.append("program_control.lanes must be an array")
            lanes = []
        lane_names = [lane.get("name") for lane in lanes if isinstance(lane, dict)]
        if lane_names != list(PRIORITY_LANES):
            errors.append("program_control lanes must appear once in canonical priority order")
        priority_repositories: list[str] = []
        current_lane_repositories: list[str] = []
        for lane in lanes:
            if not isinstance(lane, dict):
                errors.append("program_control lane entries must be objects")
                continue
            name = lane.get("name")
            for field in ("objective", "entry_condition", "exit_condition"):
                if not _nonempty_string(lane.get(field)):
                    errors.append(f"program_control lane {name}: {field} must be nonempty")
            lane_repositories = lane.get("repositories")
            if not _string_list(lane_repositories, allow_empty=False):
                errors.append(f"program_control lane {name}: repositories must be nonempty strings")
                continue
            priority_repositories.extend(lane_repositories)
            if name == control.get("current_lane"):
                current_lane_repositories = lane_repositories
        priority_counts = Counter(priority_repositories)
        duplicate_priority_repositories = sorted(
            name for name, count in priority_counts.items() if count > 1
        )
        if duplicate_priority_repositories:
            errors.append(
                "program_control duplicate priority repositories: "
                + ", ".join(duplicate_priority_repositories)
            )
        missing_priority_repositories = sorted(expected - set(priority_repositories))
        unexpected_priority_repositories = sorted(set(priority_repositories) - expected)
        if missing_priority_repositories:
            errors.append(
                "program_control missing priority repositories: "
                + ", ".join(missing_priority_repositories)
            )
        if unexpected_priority_repositories:
            errors.append(
                "program_control unexpected priority repositories: "
                + ", ".join(unexpected_priority_repositories)
            )
        active_repositories = sorted(
            name for name, repo in repo_by_name.items() if repo.get("program_state") == "active"
        )
        if active_repositories != sorted(current_lane_repositories):
            errors.append("active repositories must exactly match the current priority lane")

        ds = control.get("durable_supervisor_v0_1")
        if not isinstance(ds, dict):
            errors.append("program_control.durable_supervisor_v0_1 must be an object")
        else:
            if ds.get("status") not in {"IN_PROGRESS", "DECLARED_FROZEN"}:
                errors.append("durable_supervisor_v0_1 has invalid status")
            if ds.get("verified_runtime_state") != "PAUSED_NO_ACTIVE_TASK_OR_ATTEMPT":
                errors.append("durable_supervisor_v0_1 runtime state drifted")
            if not _valid_timestamp(ds.get("runtime_state_recorded_at")):
                errors.append("durable_supervisor_v0_1 runtime state needs a recorded timestamp")
            if not _nonempty_string(ds.get("runtime_state_source")):
                errors.append("durable_supervisor_v0_1 runtime observation needs a source")
            durable_repository = repo_by_name.get("durable-supervisor", {})
            if ds.get("verified_main_sha") != durable_repository.get("last_verified_head_sha"):
                errors.append("durable_supervisor_v0_1 SHA must match the repository ledger")
            criteria = ds.get("stopping_criteria")
            if not isinstance(criteria, list):
                errors.append("durable_supervisor_v0_1.stopping_criteria must be an array")
                criteria = []
            expected_ids = [f"DS-V0.1-{index:02d}" for index in range(1, 11)]
            if [item.get("id") for item in criteria if isinstance(item, dict)] != expected_ids:
                errors.append("durable_supervisor_v0_1 must retain ten ordered stopping criteria")
            for item in criteria:
                if not isinstance(item, dict):
                    errors.append("durable_supervisor_v0_1 criteria must be objects")
                    continue
                if item.get("status") not in {"OPEN", "SATISFIED"}:
                    errors.append(f"{item.get('id')}: invalid stopping-criterion status")
                if not _nonempty_string(item.get("criterion")):
                    errors.append(f"{item.get('id')}: criterion must be nonempty")

        opsle_tasks = control.get("opsle_tasks")
        if not isinstance(opsle_tasks, dict):
            errors.append("program_control.opsle_tasks must be an object")
        else:
            if opsle_tasks.get("current_repository") != "sneakocom/taslos-tasks":
                errors.append("Opsle Tasks current repository identity drifted")
            if "NEXT primary real-world workload" not in str(opsle_tasks.get("role")):
                errors.append("Opsle Tasks must remain the NEXT primary real-world workload")
            measurements = opsle_tasks.get("measurements")
            if (
                not _string_list(measurements, allow_empty=False)
                or set(measurements) != OPSLE_TASKS_MEASUREMENTS
            ):
                errors.append("Opsle Tasks integrated measurements drifted")
            prohibitions = opsle_tasks.get("prohibited_without_separate_authorization")
            if (
                not _string_list(prohibitions, allow_empty=False)
                or set(prohibitions) != OPSLE_TASKS_PROHIBITIONS
            ):
                errors.append("Opsle Tasks prohibitions drifted")
        for field in ("concept_activation", "later_items", "parked_items"):
            value = control.get(field)
            if not isinstance(value, list) or not value:
                errors.append(f"program_control.{field} must be a nonempty array")
        activations = control.get("concept_activation")
        if isinstance(activations, list):
            for index, activation in enumerate(activations):
                if not isinstance(activation, dict):
                    errors.append(f"concept_activation index {index} must be an object")
                    continue
                if not _nonempty_string(activation.get("deficiency")):
                    errors.append(f"concept_activation index {index} needs a deficiency")
                activation_repositories = activation.get("repositories")
                if not _string_list(activation_repositories, allow_empty=False):
                    errors.append(
                        f"concept_activation index {index} repositories must be nonempty strings"
                    )
                elif not set(activation_repositories).issubset(expected):
                    errors.append(
                        f"concept_activation index {index} references an unknown repository"
                    )
        later_items = control.get("later_items")
        if (
            not _string_list(later_items, allow_empty=False)
            or set(later_items) != LATER_ITEMS
        ):
            errors.append("program_control later items drifted")
        parked_items = control.get("parked_items")
        if _string_list(parked_items, allow_empty=False):
            required_parked_fragments = (
                "src/cli.js",
                "Background projection",
                "Historical pre-fix",
                "architectural polishing",
            )
            for fragment in required_parked_fragments:
                if not any(fragment in item for item in parked_items):
                    errors.append(f"program_control parked item missing {fragment}")

    visible_value = registry.get("visible_value")
    if not isinstance(visible_value, dict):
        errors.append("registry.visible_value must be an object")
    else:
        for field in ("baseline", "baseline_rule"):
            if not _nonempty_string(visible_value.get(field)):
                errors.append(f"visible_value.{field} must be a nonempty string")
        value_kinds = visible_value.get("value_kinds")
        if not isinstance(value_kinds, list):
            errors.append("visible_value.value_kinds must be an array")
            value_kinds = []
        class_names = [
            item.get("name") for item in value_kinds if isinstance(item, dict)
        ]
        if class_names != ["MEASURED", "DERIVED", "ESTIMATED", "UNAVAILABLE"]:
            errors.append("visible_value value kinds drifted")
        for item in value_kinds:
            if not isinstance(item, dict) or not _nonempty_string(item.get("definition")):
                errors.append("visible_value value kinds require definitions")
        child_fields = visible_value.get("per_child_receipt_fields")
        if (
            not _string_list(child_fields, allow_empty=False)
            or set(child_fields) != PER_CHILD_VALUE_FIELDS
        ):
            errors.append("visible_value per-child receipt fields drifted")
        summary_fields = visible_value.get("supervisor_summary_fields")
        if (
            not _string_list(summary_fields, allow_empty=False)
            or set(summary_fields) != SUPERVISOR_VALUE_FIELDS
        ):
            errors.append("visible_value supervisor summary fields drifted")

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
            elif label not in repo_by_name.get(project, {}).get("active_experiment_ids", []):
                errors.append(
                    f"experiment {label}: participating repository {project} "
                    "does not reciprocally list the experiment"
                )
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
        freeze = exp001.get("offline_benchmark_freeze")
        if not isinstance(freeze, dict):
            errors.append("EXP-001 offline_benchmark_freeze must be an object")
        else:
            expected_freeze_values = {
                "status": "OFFLINE_COMPONENTS_FROZEN",
                "research_release_sha": EXP001_OFFLINE_RELEASE_SHA,
                "freeze_identity": EXP001_FREEZE_IDENTITY,
                "corpus_identity": EXP001_CORPUS_IDENTITY,
                "arm_manifest_identity": EXP001_ARM_IDENTITY,
                "allocation_method_identity": EXP001_ALLOCATION_IDENTITY,
                "qualification": "PASS",
                "task_count": 6,
                "oracle_case_count": 252,
                "arm_rendering_count": 48,
                "context_firewall_invocation_count": 36,
                "decision_evidence_validation_count": 36,
                "trajectory_profile_count": 48,
                "experiment_runs_added": 0,
                "provider_model_runs_added": 0,
                "allocation_status": "METHOD_FROZEN_SEED_UNSET",
            }
            for field, expected_value in expected_freeze_values.items():
                if freeze.get(field) != expected_value:
                    errors.append(
                        f"EXP-001 offline freeze {field} must be {expected_value!r}"
                    )
            artifact = freeze.get("qualification_artifact")
            if artifact != (
                "program/evidence/exp-001-offline-freeze/qualification-report.json"
            ):
                errors.append("EXP-001 offline freeze qualification artifact path drifted")
            else:
                artifact_path = ROOT / artifact
                if not artifact_path.is_file():
                    errors.append("EXP-001 offline freeze qualification artifact is missing")
                else:
                    artifact_digest = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
                    artifact_identity = f"sha256:{artifact_digest}"
                    if freeze.get("qualification_artifact_sha256") != artifact_identity:
                        errors.append("EXP-001 offline freeze qualification artifact hash drifted")
            if not _string_list(freeze.get("limitations"), allow_empty=False):
                errors.append(
                    "EXP-001 offline freeze limitations must be a nonempty string array"
                )
        launch = exp001.get("launch_preregistration")
        if not isinstance(launch, dict):
            errors.append("EXP-001 launch_preregistration must be an object")
        else:
            expected_launch_values = {
                "status": "PREREGISTERED_AWAITING_EXACT_BUDGETED_LAUNCH_AUTHORIZATION",
                "preregistration_identity": EXP001_PREREGISTRATION_IDENTITY,
                "subject_configuration_id": EXP001_SUBJECT_CONFIGURATION_ID,
                "allocation_index_identity": EXP001_ALLOCATION_INDEX_IDENTITY,
                "seed_commitment": EXP001_SEED_COMMITMENT,
                "planned_subject_count": 240,
                "block_count": 60,
                "subjects_per_arm": 60,
                "repetition_count": 10,
                "provider_model_runs_added": 0,
                "experiment_runs_added": 0,
                "qualification": "PASS",
            }
            for field, expected_value in expected_launch_values.items():
                if launch.get(field) != expected_value:
                    errors.append(
                        f"EXP-001 launch preregistration {field} must be "
                        f"{expected_value!r}"
                    )
            if (
                launch.get("research_release_sha")
                != EXP001_PREREGISTRATION_RELEASE_SHA
            ):
                errors.append(
                    "EXP-001 launch preregistration release SHA drifted"
                )
            artifact = launch.get("verification_artifact")
            if artifact != (
                "program/evidence/exp-001-preregistration/verification-report.json"
            ):
                errors.append(
                    "EXP-001 launch preregistration verification artifact path drifted"
                )
            else:
                artifact_path = ROOT / artifact
                if not artifact_path.is_file():
                    errors.append(
                        "EXP-001 launch preregistration verification artifact is missing"
                    )
                else:
                    artifact_digest = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
                    artifact_identity = f"sha256:{artifact_digest}"
                    if launch.get("verification_artifact_sha256") != artifact_identity:
                        errors.append(
                            "EXP-001 launch preregistration verification artifact hash drifted"
                        )
            if not _string_list(launch.get("limitations"), allow_empty=False):
                errors.append(
                    "EXP-001 launch preregistration limitations must be a nonempty string array"
                )
        coordinator = exp001.get("block_coordinator_qualification")
        if not isinstance(coordinator, dict):
            errors.append("EXP-001 block_coordinator_qualification must be an object")
        else:
            expected_coordinator_values = {
                "status": "PROVIDER_FREE_QUALIFIED_NO_SUBJECT_RUN",
                "research_release_sha": EXP001_COORDINATOR_RELEASE_SHA,
                "contract_identity": EXP001_COORDINATOR_CONTRACT_IDENTITY,
                "coordinator_revision": EXP001_COORDINATOR_REVISION,
                "preregistration_identity": EXP001_PREREGISTRATION_IDENTITY,
                "allocation_index_identity": EXP001_ALLOCATION_INDEX_IDENTITY,
                "qualification": "PASS",
                "block_count": 1,
                "fixture_authorization_count": 4,
                "live_authorization_count": 0,
                "arm_rendering_count": 8,
                "result_envelope_count": 8,
                "context_firewall_invocation_count": 6,
                "decision_evidence_validation_count": 6,
                "trajectory_profile_count": 8,
                "subject_visible_arm_identity_count": 0,
                "provider_model_runs_added": 0,
                "experiment_runs_added": 0,
                "experiment_results_added": 0,
                "authorization_consumed": False,
                "private_artifacts_persisted": False,
            }
            for field, expected_value in expected_coordinator_values.items():
                if coordinator.get(field) != expected_value:
                    errors.append(
                        f"EXP-001 block coordinator {field} must be "
                        f"{expected_value!r}"
                    )
            artifacts = (
                (
                    "qualification_artifact",
                    "qualification_artifact_sha256",
                    "program/evidence/exp-001-block-coordinator/qualification-report.json",
                ),
                (
                    "value_receipt_artifact",
                    "value_receipt_artifact_sha256",
                    "program/evidence/exp-001-block-coordinator/value-receipt.json",
                ),
            )
            for path_field, hash_field, expected_path in artifacts:
                artifact = coordinator.get(path_field)
                if artifact != expected_path:
                    errors.append(
                        f"EXP-001 block coordinator {path_field} path drifted"
                    )
                    continue
                artifact_path = ROOT / artifact
                if not artifact_path.is_file():
                    errors.append(
                        f"EXP-001 block coordinator {path_field} is missing"
                    )
                    continue
                artifact_digest = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
                if coordinator.get(hash_field) != f"sha256:{artifact_digest}":
                    errors.append(
                        f"EXP-001 block coordinator {hash_field} drifted"
                    )
            if not _string_list(coordinator.get("limitations"), allow_empty=False):
                errors.append(
                    "EXP-001 block coordinator limitations must be a nonempty string array"
                )
        live_preflight = exp001.get("live_authorization_preflight")
        if not isinstance(live_preflight, dict):
            errors.append("EXP-001 live_authorization_preflight must be an object")
        else:
            expected_live_preflight_values = {
                "status": "PROVIDER_FREE_VALIDATED_UNRELEASED",
                "implementation_base_sha": EXP001_LIVE_PREFLIGHT_BASE_SHA,
                "authorization_set_id": EXP001_LIVE_AUTHORIZATION_SET_ID,
                "authorization_set_identity": (
                    EXP001_LIVE_AUTHORIZATION_SET_IDENTITY
                ),
                "authorization_class": "LIVE_PROVIDER_RUN",
                "live_authorization_label_count": 4,
                "authorization_validation_count": 13,
                "model_catalogue_identity": EXP001_MODEL_CATALOGUE_IDENTITY,
                "pricing_preflight_identity": EXP001_PRICING_PREFLIGHT_IDENTITY,
                "qualification": "PASS",
                "deterministic_replay_count": 2,
                "deterministic_payloads_byte_identical": True,
                "fixture_rejected_from_live_gate": True,
                "subject_rendering_count": 0,
                "subject_visible_canonical_arm_identifier_count": 0,
                "provider_model_runs_added": 0,
                "authorization_consumptions_added": 0,
                "experiment_runs_added": 0,
                "experiment_results_added": 0,
                "result_envelopes_added": 0,
                "lifecycle_status": "PLANNED",
            }
            for field, expected_value in expected_live_preflight_values.items():
                if live_preflight.get(field) != expected_value:
                    errors.append(
                        f"EXP-001 live preflight {field} must be "
                        f"{expected_value!r}"
                    )
            artifacts = (
                (
                    "model_catalogue_artifact",
                    "model_catalogue_artifact_sha256",
                    "program/evidence/exp-001-live-preflight/model-catalogue.json",
                ),
                (
                    "pricing_preflight_artifact",
                    "pricing_preflight_artifact_sha256",
                    "program/evidence/exp-001-live-preflight/pricing-preflight.json",
                ),
                (
                    "qualification_artifact",
                    "qualification_artifact_sha256",
                    "program/evidence/exp-001-live-preflight/qualification-report.json",
                ),
                (
                    "value_receipt_artifact",
                    "value_receipt_artifact_sha256",
                    "program/evidence/exp-001-live-preflight/value-receipt.json",
                ),
            )
            for path_field, hash_field, expected_path in artifacts:
                artifact = live_preflight.get(path_field)
                if artifact != expected_path:
                    errors.append(
                        f"EXP-001 live preflight {path_field} path drifted"
                    )
                    continue
                artifact_path = ROOT / artifact
                if not artifact_path.is_file():
                    errors.append(
                        f"EXP-001 live preflight {path_field} is missing"
                    )
                    continue
                artifact_digest = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
                if live_preflight.get(hash_field) != f"sha256:{artifact_digest}":
                    errors.append(f"EXP-001 live preflight {hash_field} drifted")
            if not _string_list(live_preflight.get("limitations"), allow_empty=False):
                errors.append(
                    "EXP-001 live preflight limitations must be a nonempty string array"
                )

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
    if theory.get("current_concept_repository_count") != 18:
        errors.append("theory.current_concept_repository_count must be 18")
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
    if len(concepts) != 18:
        errors.append(f"expected 18 theory concepts, found {len(concepts)}")

    current_concept_repositories = set(EXPECTED_REPOSITORIES[:18])
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
    if len(current_mappings) != 18:
        errors.append(f"expected 18 current concept repository mappings, found {len(current_mappings)}")

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
        errors.append("the authoritative repository registry must contain gearbox")
    if "affected-verification" not in repo_names:
        errors.append("the authoritative repository registry must contain affected-verification")
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
