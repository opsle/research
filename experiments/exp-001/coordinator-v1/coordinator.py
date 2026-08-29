#!/usr/bin/env python3
"""Provider-free preparation of one blinded EXP-001 four-arm block."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import importlib.util
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
EXP_ROOT = ROOT.parent
RESEARCH_ROOT = EXP_ROOT.parents[1]
PREREG_ROOT = EXP_ROOT / "preregistration-v1"
CORPUS_ROOT = EXP_ROOT / "corpus"

CONTRACT_PROTOCOL = "opsle.exp001.block-coordinator-contract/v1"
PLAN_PROTOCOL = "opsle.exp001.private-block-plan/v1"
ENVELOPE_PROTOCOL = "opsle.exp001.result-envelope-template/v1"
SUMMARY_PROTOCOL = "opsle.exp001.block-preflight-summary/v1"
QUALIFICATION_PROTOCOL = "opsle.exp001.block-coordinator-qualification/v1"
LIVE_AUTHORIZATION = "LIVE_PROVIDER_RUN"
FIXTURE_AUTHORIZATION = "PROVIDER_FREE_FIXTURE"


class CoordinatorError(RuntimeError):
    """A fail-closed coordinator error."""


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise CoordinatorError(f"cannot load required module {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ALLOCATION = load_module(
    "opsle_exp001_allocation_tool",
    PREREG_ROOT / "allocation_tool.py",
)
ADAPTER = load_module(
    "opsle_exp001_subject_adapter",
    PREREG_ROOT / "subject_adapter.py",
)
HARNESS = load_module(
    "opsle_exp001_offline_harness",
    EXP_ROOT / "harness.py",
)


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode()


def sha256_bytes(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def object_identity(value: dict[str, Any]) -> str:
    semantic = dict(value)
    semantic.pop("identity", None)
    return sha256_bytes(canonical_bytes(semantic))


def private_commitment(seed: bytes, context: bytes, value: bytes) -> str:
    return (
        "hmac-sha256:"
        + hmac.new(
            seed,
            context + b"\0" + value,
            hashlib.sha256,
        ).hexdigest()
    )


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CoordinatorError(f"{path}: invalid or unavailable JSON") from error
    if not isinstance(value, dict):
        raise CoordinatorError(f"{path}: top-level object required")
    return value


def verify_contract() -> dict[str, Any]:
    contract = load_json(ROOT / "contract.json")
    if contract.get("protocol_version") != CONTRACT_PROTOCOL:
        raise CoordinatorError("coordinator contract protocol drifted")
    if contract.get("identity") != object_identity(contract):
        raise CoordinatorError("coordinator contract identity mismatch")
    preregistration = load_json(PREREG_ROOT / "preregistration.json")
    index = load_json(PREREG_ROOT / "allocation-index.json")
    if contract.get("preregistration_identity") != preregistration.get("identity"):
        raise CoordinatorError("coordinator contract preregistration binding drifted")
    if contract.get("allocation_index_identity") != index.get("identity"):
        raise CoordinatorError("coordinator contract allocation binding drifted")
    return contract


def write_private(path: Path, content: bytes) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.is_symlink() or path.exists():
        raise CoordinatorError(f"refusing to overwrite private artifact {path.name}")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(content)


def select_block(
    index: dict[str, Any],
    mapping: dict[str, Any],
    block_id: str,
    required_arms: set[str],
) -> list[dict[str, Any]]:
    public = [
        entry
        for entry in index.get("entries", [])
        if isinstance(entry, dict) and entry.get("block_id") == block_id
    ]
    private = [
        entry
        for entry in mapping.get("entries", [])
        if isinstance(entry, dict) and entry.get("block_id") == block_id
    ]
    if len(public) != 4 or len(private) != 4:
        raise CoordinatorError("selected block must contain exactly four subjects")
    public_by_label = {entry.get("subject_label"): entry for entry in public}
    if len(public_by_label) != 4:
        raise CoordinatorError("selected block has duplicate public labels")
    for entry in private:
        label = entry.get("subject_label")
        public_entry = public_by_label.get(label)
        if (
            public_entry is None
            or {key: value for key, value in entry.items() if key != "arm_id"}
            != public_entry
        ):
            raise CoordinatorError("private allocation does not match public index")
    arms = {entry.get("arm_id") for entry in private}
    if arms != required_arms:
        raise CoordinatorError("selected block does not contain each frozen arm")
    task_ids = {entry.get("task_id") for entry in private}
    repetitions = {entry.get("repetition") for entry in private}
    configurations = {entry.get("configuration_id") for entry in private}
    if len(task_ids) != 1 or len(repetitions) != 1 or len(configurations) != 1:
        raise CoordinatorError("selected block control variables are inconsistent")
    return sorted(private, key=lambda entry: entry["position"])


def validate_authorizations(
    *,
    directory: Path,
    block_entries: list[dict[str, Any]],
    preregistration_identity: str,
    configuration_id: str,
    maximum_spend_usd: float,
    authorization_class: str,
) -> dict[str, dict[str, Any]]:
    if not directory.is_dir() or directory.is_symlink():
        raise CoordinatorError("authorization directory is unavailable or unsafe")
    expected_names = {f"{entry['subject_label']}.json" for entry in block_entries}
    observed_names = {path.name for path in directory.iterdir()}
    if observed_names != expected_names:
        raise CoordinatorError(
            "authorization directory must contain exactly four bound files"
        )
    validated: dict[str, dict[str, Any]] = {}
    authorization_ids: set[str] = set()
    for entry in block_entries:
        label = entry["subject_label"]
        path = directory / f"{label}.json"
        if path.is_symlink() or not path.is_file():
            raise CoordinatorError(
                "authorization files must be regular non-symlink files"
            )
        try:
            ADAPTER.verify_authorization(
                path,
                preregistration_identity,
                maximum_spend_usd,
                label,
            )
        except ADAPTER.SubjectAdapterError as error:
            raise CoordinatorError(str(error)) from error
        authorization = load_json(path)
        required = {
            "authorization_class": authorization_class,
            "block_id": entry["block_id"],
            "configuration_id": configuration_id,
            "fixture_only": authorization_class == FIXTURE_AUTHORIZATION,
            "provider_launch_permitted": authorization_class == LIVE_AUTHORIZATION,
        }
        if any(authorization.get(key) != value for key, value in required.items()):
            raise CoordinatorError("authorization class or block binding drifted")
        authorization_id = authorization.get("authorization_id")
        if not isinstance(authorization_id, str) or not authorization_id:
            raise CoordinatorError("authorization_id must be a nonempty string")
        if authorization_id in authorization_ids:
            raise CoordinatorError("authorization_id must be unique within the block")
        authorization_ids.add(authorization_id)
        validated[label] = {
            "authorization_class": authorization_class,
            "authorization_id": authorization_id,
            "identity": sha256_bytes(canonical_bytes(authorization)),
            "maximum_spend_usd": authorization["maximum_spend_usd"],
        }
    return validated


def locate_dependencies(
    args: argparse.Namespace,
) -> tuple[dict[str, str], Path, Path, Path]:
    benchmark, _arms, _corpus = HARNESS.verify_static_freeze()
    pins = benchmark["pinned_dependencies"]
    context_firewall = HARNESS.locate_dependency(
        "context-firewall", args.context_firewall
    )
    decision_evidence = HARNESS.locate_dependency(
        "decision-evidence-protocol", args.decision_evidence
    )
    profiler = HARNESS.locate_dependency(
        "agent-trajectory-profiler", args.trajectory_profiler
    )
    HARNESS.verify_dependency(
        context_firewall,
        pins["context-firewall"],
        "bin/context-firewall.js",
    )
    HARNESS.verify_dependency(
        decision_evidence,
        pins["decision-evidence-protocol"],
        "bin/decision-evidence.js",
    )
    HARNESS.verify_dependency(
        profiler,
        pins["agent-trajectory-profiler"],
        "src/context-evidence.js",
    )
    return pins, context_firewall, decision_evidence, profiler


def render_block(
    *,
    block_entries: list[dict[str, Any]],
    arms_by_id: dict[str, dict[str, Any]],
    stage: Path,
    dependencies: tuple[dict[str, str], Path, Path, Path],
) -> list[dict[str, Any]]:
    pins, context_firewall, decision_evidence, profiler = dependencies
    task_id = block_entries[0]["task_id"]
    prompt = CORPUS_ROOT / f"tasks/{task_id}/prompt.md"
    initial = CORPUS_ROOT / f"tasks/{task_id}/workspace/task.py"
    oracle = HARNESS.oracle_result(task_id, initial)
    if oracle.returncode != 1:
        raise CoordinatorError("frozen initial workspace no longer fails the oracle")
    raw = oracle.stdout
    evidence_count = HARNESS.tap_test_count(raw)
    renderings: list[dict[str, Any]] = []
    for entry in block_entries:
        label = entry["subject_label"]
        arm_id = entry["arm_id"]
        arm = arms_by_id[arm_id]
        work = stage / "coordinator-evidence" / label
        work.mkdir(mode=0o700, parents=True)
        if arm_id == "raw-control":
            profile, indicator = HARNESS.run_profile(
                profiler,
                work,
                HARNESS.profile_input(
                    arm_id=arm_id,
                    task_id=task_id,
                    state="initial",
                    raw=raw,
                    evidence_count=evidence_count,
                ),
            )
            write_private(work / "profile.json", canonical_bytes(profile))
            write_private(
                work / "trajectory-profiler-indicator.txt",
                (indicator + "\n").encode(),
            )
            evidence = raw
            arm_record = {
                "disposition": "RAW_BASELINE",
                "escalation_state": "NOT_APPLICABLE",
                "profile_identity": profile["trajectory_identity"],
                "raw_bytes": len(raw),
                "suppressed_evidence_count": 0,
            }
        else:
            arm_record, artifacts = HARNESS.run_context_firewall_chain(
                context_firewall=context_firewall,
                decision_evidence=decision_evidence,
                profiler=profiler,
                context_firewall_head=pins["context-firewall"],
                decision_evidence_head=pins["decision-evidence-protocol"],
                task_id=task_id,
                state="initial",
                arm={**arm, "id": label},
                raw=raw,
                evidence_count=evidence_count,
                work=work,
            )
            arm_record["arm_id"] = arm_id
            evidence = artifacts["packet.json"]
            if arm_record["escalation_state"] == "FULFILLED":
                evidence += raw
        subject = stage / "subjects" / label
        write_private(subject / "prompt.md", prompt.read_bytes())
        write_private(subject / "task.py", initial.read_bytes())
        write_private(subject / "evidence.txt", evidence)
        for artifact in work.iterdir():
            artifact.chmod(0o600)
        renderings.append(
            {
                "arm_id": arm_id,
                "arm_record": arm_record,
                "evidence_bytes": len(evidence),
                "evidence_sha256": sha256_bytes(evidence),
                "initial_task_sha256": sha256_file(initial),
                "oracle_transcript_sha256": sha256_bytes(raw),
                "prompt_sha256": sha256_file(prompt),
                "subject_label": label,
            }
        )
    return renderings


def result_envelope(
    *,
    entry: dict[str, Any],
    rendering: dict[str, Any],
    authorization: dict[str, Any],
    preregistration_identity: str,
    configuration_id: str,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "protocol_version": ENVELOPE_PROTOCOL,
        "experiment_id": "EXP-001",
        "state": "AWAITING_SEPARATE_PROVIDER_EXECUTION",
        "preregistration_identity": preregistration_identity,
        "configuration_id": configuration_id,
        "block_id": entry["block_id"],
        "task_id": entry["task_id"],
        "repetition": entry["repetition"],
        "position": entry["position"],
        "subject_label": entry["subject_label"],
        "arm_id": entry["arm_id"],
        "authorization": authorization,
        "subject_inputs": {
            "prompt_sha256": rendering["prompt_sha256"],
            "initial_task_sha256": rendering["initial_task_sha256"],
            "evidence_sha256": rendering["evidence_sha256"],
            "evidence_bytes": rendering["evidence_bytes"],
            "oracle_transcript_sha256": rendering["oracle_transcript_sha256"],
        },
        "arm_evidence": rendering["arm_record"],
        "provider_result": None,
        "correctness_result": None,
        "failure_classification": None,
        "provider_model_runs": 0,
        "experiment_results": 0,
    }
    value["identity"] = object_identity(value)
    return value


def artifact_manifest(stage: Path) -> dict[str, Any]:
    artifacts = []
    for path in sorted(item for item in stage.rglob("*") if item.is_file()):
        artifacts.append(
            {
                "path": path.relative_to(stage).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    value: dict[str, Any] = {
        "protocol_version": "opsle.exp001.private-preflight-manifest/v1",
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }
    value["identity"] = object_identity(value)
    return value


def measurement(identity: str, result: int, evidence_ref: str) -> dict[str, Any]:
    return {
        "id": identity,
        "baseline": None,
        "result": result,
        "delta": None,
        "unit": "count",
        "direction": "PROTECTION_SIGNAL",
        "class": "EXACT",
        "evidence_refs": [evidence_ref],
        "source_verification": "VERIFIED",
        "operator_display": True,
        "aggregation": {"safe": True, "method": "SUM"},
        "derivation": None,
        "limitations": [],
    }


def value_receipt(
    *,
    block_commitment: str,
    configuration_id: str,
    preregistration_identity: str,
    plan_commitment: str,
    manifest_commitment: str,
) -> dict[str, Any]:
    return {
        "schema": "opsle.value-receipt.v1",
        "mechanism": {
            "id": "opsle.exp001-block-coordinator",
            "name": "EXP-001 Block Coordinator",
            "version": "1.0.0",
            "revision": sha256_file(Path(__file__)),
        },
        "run": {
            "id": block_commitment,
            "task_classification": "EXP-001_PROVIDER_FREE_PREFLIGHT",
            "work_classification": "DETERMINISTIC_COORDINATION",
            "repository": "opsle/research",
        },
        "operation": {
            "id": block_commitment,
            "name": "prepare-one-block",
            "configuration_id": configuration_id,
            "policy_id": preregistration_identity,
        },
        "measurements": [
            measurement("validated_block_count", 1, "private_plan"),
            measurement("validated_authorization_count", 4, "private_plan"),
            measurement("materialized_arm_rendering_count", 4, "manifest"),
            measurement("recorded_result_envelope_count", 4, "manifest"),
            measurement("provider_model_run_count", 0, "private_plan"),
            measurement("experiment_result_count", 0, "private_plan"),
        ],
        "evidence": [
            {
                "id": "private_plan",
                "kind": "RUN_ARTIFACT",
                "locator": plan_commitment,
                "trust": "VERIFIED",
            },
            {
                "id": "manifest",
                "kind": "RUN_ARTIFACT",
                "locator": manifest_commitment,
                "trust": "VERIFIED",
            },
            {
                "id": "preregistration",
                "kind": "CONTENT_HASH",
                "locator": sha256_file(PREREG_ROOT / "preregistration.json"),
                "trust": "VERIFIED",
            },
        ],
        "limitations": [
            "Preflight does not consume authorization or execute a provider/model subject.",
            "Prepared result envelopes contain no correctness or experimental result.",
            "Private artifact hashes commit the arm mapping without exposing it.",
            "No token, cost, latency, correctness, or causal savings claim is made.",
        ],
    }


def prepare_block(
    *,
    seed_file: Path,
    block_id: str,
    authorization_dir: Path,
    output_dir: Path,
    authorization_class: str,
    require_environment: bool,
    args: argparse.Namespace,
) -> tuple[dict[str, Any], dict[str, Any]]:
    contract = verify_contract()
    try:
        verification = ADAPTER.verify_preregistration(
            require_environment=require_environment
        )
    except ADAPTER.SubjectAdapterError as error:
        raise CoordinatorError(str(error)) from error
    index = load_json(PREREG_ROOT / "allocation-index.json")
    arms = load_json(EXP_ROOT / "arms.json")
    corpus = load_json(CORPUS_ROOT / "manifest.json")
    task_ids = [item["id"] for item in corpus["tasks"]]
    arm_ids = [item["id"] for item in arms["arms"]]
    try:
        seed = ALLOCATION.load_seed(seed_file)
        ALLOCATION.validate_secret(
            seed=seed,
            index=index,
            sealed=PREREG_ROOT / "allocation-mapping.enc",
            task_ids=task_ids,
            arm_ids=arm_ids,
        )
        mapping = ALLOCATION.unseal_mapping(
            seed,
            PREREG_ROOT / "allocation-mapping.enc",
        )
    except ALLOCATION.AllocationError as error:
        raise CoordinatorError(str(error)) from error
    block_entries = select_block(index, mapping, block_id, set(arm_ids))
    authorizations = validate_authorizations(
        directory=authorization_dir,
        block_entries=block_entries,
        preregistration_identity=verification["preregistration_identity"],
        configuration_id=verification["subject_configuration_id"],
        maximum_spend_usd=load_json(PREREG_ROOT / "subject-config.json")[
            "subject_limits"
        ]["maximum_spend_usd_per_subject"],
        authorization_class=authorization_class,
    )
    if output_dir.exists() or output_dir.is_symlink():
        raise CoordinatorError("private output directory must not already exist")
    output_dir.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    stage = Path(
        tempfile.mkdtemp(
            prefix=f".{output_dir.name}-",
            dir=output_dir.parent,
        )
    )
    stage.chmod(0o700)
    try:
        renderings = render_block(
            block_entries=block_entries,
            arms_by_id={item["id"]: item for item in arms["arms"]},
            stage=stage,
            dependencies=locate_dependencies(args),
        )
        rendering_by_label = {item["subject_label"]: item for item in renderings}
        envelopes = []
        for entry in block_entries:
            label = entry["subject_label"]
            envelope = result_envelope(
                entry=entry,
                rendering=rendering_by_label[label],
                authorization=authorizations[label],
                preregistration_identity=verification["preregistration_identity"],
                configuration_id=verification["subject_configuration_id"],
            )
            write_private(
                stage / "result-envelopes" / f"{label}.json",
                canonical_bytes(envelope),
            )
            envelopes.append(envelope)
        block_semantics = {
            "block_id": block_id,
            "entries": block_entries,
        }
        block_commitment = private_commitment(
            seed,
            b"opsle.exp001.private-block-commitment/v1",
            canonical_bytes(block_semantics),
        )
        plan: dict[str, Any] = {
            "protocol_version": PLAN_PROTOCOL,
            "experiment_id": "EXP-001",
            "state": "PREFLIGHT_ONLY_NOT_LAUNCHED",
            "contract_identity": contract["identity"],
            "preregistration_identity": verification["preregistration_identity"],
            "configuration_id": verification["subject_configuration_id"],
            "allocation_index_identity": verification["allocation_index_identity"],
            "block": block_semantics,
            "block_commitment": block_commitment,
            "authorization_class": authorization_class,
            "subjects": [
                {
                    "subject_label": envelope["subject_label"],
                    "arm_id": envelope["arm_id"],
                    "authorization_identity": envelope["authorization"]["identity"],
                    "result_envelope_identity": envelope["identity"],
                }
                for envelope in envelopes
            ],
            "provider_model_runs": 0,
            "experiment_results": 0,
        }
        plan["identity"] = object_identity(plan)
        write_private(stage / "block-plan.json", canonical_bytes(plan))
        manifest = artifact_manifest(stage)
        write_private(stage / "manifest.json", canonical_bytes(manifest))
        plan_commitment = private_commitment(
            seed,
            b"opsle.exp001.private-plan-commitment/v1",
            (stage / "block-plan.json").read_bytes(),
        )
        manifest_commitment = private_commitment(
            seed,
            b"opsle.exp001.private-manifest-commitment/v1",
            (stage / "manifest.json").read_bytes(),
        )
        receipt = value_receipt(
            block_commitment=block_commitment,
            configuration_id=verification["subject_configuration_id"],
            preregistration_identity=verification["preregistration_identity"],
            plan_commitment=plan_commitment,
            manifest_commitment=manifest_commitment,
        )
        write_private(stage / "value-receipt.json", canonical_bytes(receipt))
        summary: dict[str, Any] = {
            "protocol_version": SUMMARY_PROTOCOL,
            "experiment_id": "EXP-001",
            "qualification": "PASS",
            "authorization_class": authorization_class,
            "preregistration_identity": verification["preregistration_identity"],
            "configuration_id": verification["subject_configuration_id"],
            "allocation_index_identity": verification["allocation_index_identity"],
            "block_commitment": block_commitment,
            "private_plan_commitment": plan_commitment,
            "private_manifest_commitment": manifest_commitment,
            "value_receipt_sha256": sha256_file(stage / "value-receipt.json"),
            "block_count": 1,
            "authorization_count": 4,
            "arm_rendering_count": 4,
            "result_envelope_count": 4,
            "context_firewall_invocation_count": 3,
            "decision_evidence_validation_count": 3,
            "trajectory_profile_count": 4,
            "provider_model_run_count": 0,
            "experiment_result_count": 0,
            "authorization_consumed": False,
            "provider_launch_executed": False,
        }
        summary["identity"] = object_identity(summary)
        stage.rename(output_dir)
        return summary, receipt
    except Exception:
        shutil.rmtree(stage)
        raise


def fixture_authorization(
    entry: dict[str, Any],
    preregistration_identity: str,
    maximum_spend_usd: float,
) -> dict[str, Any]:
    return {
        "authorization_id": "fixture-"
        + hashlib.sha256(entry["subject_label"].encode()).hexdigest()[:24],
        "authorization_class": FIXTURE_AUTHORIZATION,
        "experiment_id": "EXP-001",
        "preregistration_identity": preregistration_identity,
        "configuration_id": entry["configuration_id"],
        "block_id": entry["block_id"],
        "subject_label": entry["subject_label"],
        "provider_run_authorized": True,
        "max_provider_runs": 1,
        "maximum_spend_usd": maximum_spend_usd,
        "fixture_only": True,
        "provider_launch_permitted": False,
    }


def snapshot(directory: Path) -> dict[str, bytes]:
    return {
        path.relative_to(directory).as_posix(): path.read_bytes()
        for path in sorted(item for item in directory.rglob("*") if item.is_file())
    }


def qualify(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, bytes]]:
    verification = ADAPTER.verify_preregistration()
    index = load_json(PREREG_ROOT / "allocation-index.json")
    first_block = index["entries"][0]["block_id"]
    seed = ALLOCATION.load_seed(args.seed_file)
    mapping = ALLOCATION.unseal_mapping(seed, PREREG_ROOT / "allocation-mapping.enc")
    arms = load_json(EXP_ROOT / "arms.json")
    entries = select_block(
        index,
        mapping,
        first_block,
        {item["id"] for item in arms["arms"]},
    )
    maximum_spend_usd = load_json(PREREG_ROOT / "subject-config.json")[
        "subject_limits"
    ]["maximum_spend_usd_per_subject"]
    with tempfile.TemporaryDirectory(prefix="opsle-exp001-coordinator-") as temporary:
        root = Path(temporary)
        authorizations = root / "authorizations"
        authorizations.mkdir(mode=0o700)
        for entry in entries:
            write_private(
                authorizations / f"{entry['subject_label']}.json",
                canonical_bytes(
                    fixture_authorization(
                        entry,
                        verification["preregistration_identity"],
                        maximum_spend_usd,
                    )
                ),
            )
        first_summary, first_receipt = prepare_block(
            seed_file=args.seed_file,
            block_id=first_block,
            authorization_dir=authorizations,
            output_dir=root / "first",
            authorization_class=FIXTURE_AUTHORIZATION,
            require_environment=False,
            args=args,
        )
        second_summary, second_receipt = prepare_block(
            seed_file=args.seed_file,
            block_id=first_block,
            authorization_dir=authorizations,
            output_dir=root / "second",
            authorization_class=FIXTURE_AUTHORIZATION,
            require_environment=False,
            args=args,
        )
        if first_summary != second_summary or first_receipt != second_receipt:
            raise CoordinatorError(
                "provider-free coordinator summary is not deterministic"
            )
        if snapshot(root / "first") != snapshot(root / "second"):
            raise CoordinatorError(
                "provider-free private artifacts are not deterministic"
            )
        subject_snapshot = snapshot(root / "first" / "subjects")
        opaque_arm_ids = [item["id"].encode() for item in arms["arms"]]
        for path, content in subject_snapshot.items():
            if any(arm_id in content for arm_id in opaque_arm_ids):
                raise CoordinatorError(
                    f"subject-visible artifact discloses an opaque arm identity: {path}"
                )
        report = {
            "protocol_version": QUALIFICATION_PROTOCOL,
            "experiment_id": "EXP-001",
            "classification": "PROVIDER_FREE_COORDINATOR_QUALIFICATION",
            "qualification": "PASS",
            "coordinator_revision": sha256_file(Path(__file__)),
            "contract_identity": verify_contract()["identity"],
            "preregistration_identity": verification["preregistration_identity"],
            "allocation_index_identity": verification["allocation_index_identity"],
            "block_commitment": first_summary["block_commitment"],
            "deterministic_replay": True,
            "block_count": 1,
            "fixture_authorization_count": 4,
            "live_authorization_count": 0,
            "arm_rendering_count": 8,
            "result_envelope_count": 8,
            "context_firewall_invocation_count": 6,
            "decision_evidence_validation_count": 6,
            "trajectory_profile_count": 8,
            "provider_model_run_count": 0,
            "experiment_run_count": 0,
            "experiment_result_count": 0,
            "authorization_consumed": False,
            "private_artifacts_persisted": False,
            "subject_visible_arm_identity_count": 0,
            "value_receipt_sha256": sha256_bytes(canonical_bytes(first_receipt)),
            "limitations": [
                "Fixture authorizations cannot pass the live authorization-class gate.",
                "Qualification invoked no provider and produced no EXP-001 run or result.",
                "The selected block ID, subject labels, arm mapping, and seed remain absent.",
                "No token, cost, latency, correctness, or causal savings claim is made.",
            ],
        }
        evidence = {
            "qualification-report.json": canonical_bytes(report),
            "value-receipt.json": canonical_bytes(first_receipt),
        }
    return report, evidence


def add_dependency_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--context-firewall")
    parser.add_argument("--decision-evidence")
    parser.add_argument("--trajectory-profiler")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    verify = subparsers.add_parser("verify")
    verify.add_argument("--seed-file", type=Path, required=True)
    add_dependency_arguments(verify)
    qualify_parser = subparsers.add_parser("qualify")
    qualify_parser.add_argument("--seed-file", type=Path, required=True)
    qualify_parser.add_argument("--evidence-dir", type=Path)
    qualify_parser.add_argument("--verify-committed", action="store_true")
    add_dependency_arguments(qualify_parser)
    preflight = subparsers.add_parser("preflight")
    preflight.add_argument("--seed-file", type=Path, required=True)
    preflight.add_argument("--block-id", required=True)
    preflight.add_argument("--authorization-dir", type=Path, required=True)
    preflight.add_argument("--output-dir", type=Path, required=True)
    add_dependency_arguments(preflight)
    args = parser.parse_args(argv)
    try:
        if args.command == "preflight":
            summary, _receipt = prepare_block(
                seed_file=args.seed_file,
                block_id=args.block_id,
                authorization_dir=args.authorization_dir,
                output_dir=args.output_dir,
                authorization_class=LIVE_AUTHORIZATION,
                require_environment=True,
                args=args,
            )
            result = summary
            indicator = (
                "[EXP-001 Block Coordinator] 1 block | 4 authorizations | "
                "4 renderings | PREFLIGHT PASS"
            )
        else:
            result, evidence = qualify(args)
            evidence_root = RESEARCH_ROOT / "program/evidence/exp-001-block-coordinator"
            if args.command == "verify" or args.verify_committed:
                for name, content in evidence.items():
                    path = evidence_root / name
                    if not path.is_file() or path.read_bytes() != content:
                        raise CoordinatorError(
                            f"committed coordinator evidence is missing or stale: {name}"
                        )
            if args.command == "qualify" and args.evidence_dir is not None:
                args.evidence_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
                for name, content in evidence.items():
                    target = args.evidence_dir / name
                    if target.exists():
                        raise CoordinatorError("refusing to overwrite evidence output")
                    target.write_bytes(content)
            indicator = (
                "[EXP-001 Block Coordinator Qualification] 1 block | "
                "8 provider-free renderings | PASS"
            )
        sys.stdout.buffer.write(canonical_bytes(result))
        print(indicator, file=sys.stderr)
        return 0
    except (
        ADAPTER.SubjectAdapterError,
        ALLOCATION.AllocationError,
        CoordinatorError,
        HARNESS.QualificationError,
        KeyError,
        OSError,
        TypeError,
        ValueError,
    ) as error:
        sys.stderr.buffer.write(
            canonical_bytes(
                {
                    "code": "BLOCK_COORDINATOR_FAILED",
                    "message": str(error),
                }
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
