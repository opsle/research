#!/usr/bin/env python3
"""Provider-free freeze validator and interoperability qualifier for EXP-001."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
RESEARCH_ROOT = ROOT.parents[1]
CORPUS_ROOT = ROOT / "corpus"


class QualificationError(RuntimeError):
    """A fail-closed offline qualification error."""


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n").encode()


def sha256_bytes(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def object_identity(value: dict[str, Any]) -> str:
    semantic = dict(value)
    semantic.pop("identity", None)
    return sha256_bytes(canonical_bytes(semantic))


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise QualificationError(f"{path}: invalid or unavailable JSON") from error
    if not isinstance(value, dict):
        raise QualificationError(f"{path}: top-level object required")
    return value


def run_command(
    argv: list[str],
    *,
    accepted: tuple[int, ...] = (0,),
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[bytes]:
    environment = {
        **os.environ,
        "LC_ALL": "C.UTF-8",
        "PYTHONDONTWRITEBYTECODE": "1",
        "TZ": "UTC",
    }
    result = subprocess.run(
        argv,
        cwd=cwd,
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode not in accepted:
        command = " ".join(argv[:3])
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise QualificationError(
            f"command failed closed ({result.returncode}): {command}: {detail}"
        )
    return result


def locate_dependency(name: str, explicit: str | None) -> Path:
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    candidates.extend((RESEARCH_ROOT.parent / name, RESEARCH_ROOT / ".deps" / name))
    for candidate in candidates:
        if candidate.is_dir():
            return candidate.resolve()
    raise QualificationError(
        f"pinned dependency {name} is unavailable; provide its exact checkout path"
    )


def verify_dependency(root: Path, expected_head: str, required_file: str) -> None:
    if not (root / required_file).is_file():
        raise QualificationError(f"{root}: missing {required_file}")
    result = run_command(["git", "rev-parse", "HEAD"], cwd=root)
    actual = result.stdout.decode().strip()
    if actual != expected_head:
        raise QualificationError(
            f"{root.name}: expected HEAD {expected_head}, found {actual}"
        )


def verify_static_freeze() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    benchmark = load_json(ROOT / "benchmark.json")
    arms = load_json(ROOT / "arms.json")
    allocation = load_json(ROOT / "allocation.json")
    corpus = load_json(CORPUS_ROOT / "manifest.json")

    for label, value in (
        ("benchmark", benchmark),
        ("arm manifest", arms),
        ("allocation method", allocation),
        ("corpus", corpus),
    ):
        if value.get("identity") != object_identity(value):
            raise QualificationError(f"{label} identity mismatch")

    artifact_paths: set[str] = set()
    for label, artifact in benchmark.get("artifacts", {}).items():
        if not isinstance(artifact, dict):
            raise QualificationError(f"benchmark artifact {label} must be an object")
        relative = artifact.get("path")
        if not isinstance(relative, str) or relative in artifact_paths:
            raise QualificationError(f"benchmark artifact {label} path is invalid or duplicated")
        artifact_paths.add(relative)
        path = ROOT / relative
        if artifact.get("sha256") != sha256_file(path):
            raise QualificationError(f"benchmark artifact {label} hash mismatch")

    task_ids: set[str] = set()
    for task in corpus.get("tasks", []):
        task_id = task.get("id")
        if not isinstance(task_id, str) or task_id in task_ids:
            raise QualificationError("corpus task identity is invalid or duplicated")
        task_ids.add(task_id)
        subject = task.get("subject_visible")
        evaluator = task.get("evaluator_only")
        if not isinstance(subject, list) or not isinstance(evaluator, list):
            raise QualificationError(f"{task_id}: visibility lists required")
        if set(subject) & set(evaluator):
            raise QualificationError(f"{task_id}: subject/evaluator visibility overlap")
        expected_subject = {
            f"tasks/{task_id}/prompt.md",
            f"tasks/{task_id}/workspace/task.py",
        }
        expected_evaluator = {
            f"tasks/{task_id}/accepted/task.py",
            "../oracle.py",
        }
        if set(subject) != expected_subject or set(evaluator) != expected_evaluator:
            raise QualificationError(f"{task_id}: visibility boundary drifted")
        files = task.get("files")
        expected_files = expected_subject | {f"tasks/{task_id}/accepted/task.py"}
        if not isinstance(files, dict) or set(files) != expected_files:
            raise QualificationError(f"{task_id}: frozen file set drifted")
        for relative, expected_hash in files.items():
            if sha256_file(CORPUS_ROOT / relative) != expected_hash:
                raise QualificationError(f"{task_id}: content hash mismatch for {relative}")

    if benchmark.get("run_count") != 0 or benchmark.get("provider_model_run_count") != 0:
        raise QualificationError("offline freeze must record zero subject and provider/model runs")
    if allocation.get("status") != "METHOD_FROZEN_SEED_UNSET":
        raise QualificationError("allocation method must retain its unset launch boundary")
    if any(value is not None for value in allocation.get("unset_fields", {}).values()):
        raise QualificationError("allocation launch inputs must remain unset")
    if len(arms.get("arms", [])) != 4:
        raise QualificationError("exactly four experimental arms are required")
    return benchmark, arms, corpus


def oracle_result(task_id: str, candidate: Path) -> subprocess.CompletedProcess[bytes]:
    return run_command(
        [sys.executable, str(ROOT / "oracle.py"), task_id, str(candidate)],
        accepted=(0, 1),
    )


def tap_test_count(stdout: bytes) -> int:
    for line in stdout.decode("utf-8").splitlines():
        if line.startswith("# tests "):
            return int(line.removeprefix("# tests "))
    raise QualificationError("oracle transcript lacks a TAP test aggregate")


def profile_input(
    *,
    arm_id: str,
    task_id: str,
    state: str,
    raw: bytes,
    evidence_count: int,
    packet: dict[str, Any] | None = None,
    packet_bytes: bytes | None = None,
    validation: dict[str, Any] | None = None,
    escalation: str = "NONE",
) -> dict[str, Any]:
    run_id = f"exp001-offline-{task_id}-{state}-{arm_id}"
    operation_id = f"{run_id}:oracle"
    value: dict[str, Any] = {
        "arm_id": arm_id,
        "configuration_id": f"exp001/{arm_id}/v1",
        "escalation": escalation,
        "escalation_reason": "Context Firewall declared NEEDS_RAW_EVIDENCE.",
        "evidence_count": evidence_count,
        "kind": "raw" if packet is None else "context-firewall",
        "operation_id": operation_id,
        "raw_bytes": len(raw),
        "raw_identity": sha256_bytes(raw),
        "run_id": run_id,
        "task_id": f"exp001:{task_id}:{state}",
    }
    if packet is not None and packet_bytes is not None and validation is not None:
        value.update({
            "packet": packet,
            "packet_bytes_base64": base64.b64encode(packet_bytes).decode(),
            "validation": validation,
        })
    return value


def run_profile(
    profiler_root: Path,
    work: Path,
    value: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    path = work / "profile-input.json"
    path.write_bytes(canonical_bytes(value))
    result = run_command([
        "node",
        str(ROOT / "interop-profile.mjs"),
        str(profiler_root),
        str(path),
    ])
    profile = json.loads(result.stdout)
    if profile.get("valid") is not True or profile.get("measurement_status") != "MEASURED":
        raise QualificationError("Agent Trajectory Profiler rejected a frozen arm trajectory")
    return profile, result.stderr.decode().strip()


def run_context_firewall_chain(
    *,
    context_firewall: Path,
    decision_evidence: Path,
    profiler: Path,
    context_firewall_head: str,
    decision_evidence_head: str,
    task_id: str,
    state: str,
    arm: dict[str, Any],
    raw: bytes,
    evidence_count: int,
    work: Path,
) -> tuple[dict[str, Any], dict[str, bytes]]:
    arm_id = arm["id"]
    run_id = f"exp001-offline-{task_id}-{state}-{arm_id}"
    operation_id = f"{run_id}:oracle"
    source = {
        "operation_id": operation_id,
        "process": {
            "duration_ms": None,
            "exit_code": 0 if state == "accepted" else 1,
            "interrupted": False,
        },
        "protocol_version": "opsle.context-firewall.test-run-input/v1",
        "source": {
            "id": f"exp001:{task_id}:oracle",
            "raw_evidence_ref": f"artifact:{sha256_bytes(raw)}",
            "run_id": run_id,
        },
        "streams": [{"data": raw.decode("utf-8"), "encoding": "utf8", "name": "stdout"}],
    }
    source_path = work / "source-input.json"
    packet_path = work / "packet.json"
    firewall_receipt_path = work / "context-firewall-value-receipt.json"
    decision_receipt_path = work / "decision-evidence-value-receipt.json"
    source_path.write_bytes(canonical_bytes(source))

    reduce_argv = [
        "node",
        str(context_firewall / "bin/context-firewall.js"),
        "reduce",
        "--input",
        str(source_path),
        "--mechanism-revision",
        context_firewall_head,
        "--value-receipt",
        str(firewall_receipt_path),
    ]
    if arm.get("max_output_bytes") is not None:
        reduce_argv.extend(("--max-bytes", str(arm["max_output_bytes"])))
    reduced = run_command(reduce_argv)
    packet_bytes = reduced.stdout
    packet_path.write_bytes(packet_bytes)
    packet = json.loads(packet_bytes)

    validated = run_command([
        "node",
        str(decision_evidence / "bin/decision-evidence.js"),
        "validate-context-firewall",
        "--packet",
        str(packet_path),
        "--source-input",
        str(source_path),
        "--mechanism-revision",
        decision_evidence_head,
        "--value-receipt",
        str(decision_receipt_path),
    ])
    validation = json.loads(validated.stdout)
    if validation.get("valid") is not True or validation.get("classification") != "VALID":
        raise QualificationError("Decision Evidence rejected a Context Firewall packet/source chain")

    requires_raw = packet["decision_evidence"]["disposition"] == "NEEDS_RAW_EVIDENCE"
    escalation = "NONE"
    if requires_raw:
        escalation = (
            "FULFILLED"
            if arm["on_needs_raw_evidence"] == "FULFILL_ONCE_WITH_EXACT_RAW_TRANSCRIPT"
            else "REQUESTED"
        )
    profile, profiler_indicator = run_profile(
        profiler,
        work,
        profile_input(
            arm_id=arm_id,
            task_id=task_id,
            state=state,
            raw=raw,
            evidence_count=evidence_count,
            packet=packet,
            packet_bytes=packet_bytes,
            validation=validation,
            escalation=escalation,
        ),
    )
    measurements = profile["measurements"]
    record = {
        "arm_id": arm_id,
        "context_firewall_receipt_identity": sha256_file(firewall_receipt_path),
        "decision_evidence_receipt_identity": sha256_file(decision_receipt_path),
        "disposition": packet["decision_evidence"]["disposition"],
        "escalation_state": escalation,
        "final_model_visible_bytes": measurements["final_model_visible_bytes"],
        "initial_model_visible_bytes": measurements["initial_model_visible_bytes"],
        "packet_identity": sha256_bytes(packet_bytes),
        "profile_identity": profile["trajectory_identity"],
        "raw_bytes": len(raw),
        "source_backed_validation": validation["verification"]["input_hash"] == "VERIFIED",
        "suppressed_evidence_count": measurements["suppressed_evidence_count"],
    }
    artifacts = {
        "context-firewall-indicator.txt": reduced.stderr,
        "context-firewall-value-receipt.json": firewall_receipt_path.read_bytes(),
        "decision-evidence-indicator.txt": validated.stderr,
        "decision-evidence-validation.json": validated.stdout,
        "decision-evidence-value-receipt.json": decision_receipt_path.read_bytes(),
        "packet.json": packet_bytes,
        "profile.json": canonical_bytes(profile),
        "source-input.json": source_path.read_bytes(),
        "trajectory-profiler-indicator.txt": (profiler_indicator + "\n").encode(),
    }
    return record, artifacts


def qualify(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, bytes]]:
    benchmark, arms_manifest, corpus = verify_static_freeze()
    pins = benchmark["pinned_dependencies"]
    context_firewall = locate_dependency("context-firewall", args.context_firewall)
    decision_evidence = locate_dependency("decision-evidence-protocol", args.decision_evidence)
    profiler = locate_dependency("agent-trajectory-profiler", args.trajectory_profiler)
    verify_dependency(context_firewall, pins["context-firewall"], "bin/context-firewall.js")
    verify_dependency(decision_evidence, pins["decision-evidence-protocol"], "bin/decision-evidence.js")
    verify_dependency(profiler, pins["agent-trajectory-profiler"], "src/context-evidence.js")

    records = []
    representative: dict[str, bytes] = {}
    with tempfile.TemporaryDirectory(prefix="opsle-exp001-") as temporary:
        temp_root = Path(temporary)
        for task in corpus["tasks"]:
            task_id = task["id"]
            candidates = {
                "initial": CORPUS_ROOT / f"tasks/{task_id}/workspace/task.py",
                "accepted": CORPUS_ROOT / f"tasks/{task_id}/accepted/task.py",
            }
            for state, candidate in candidates.items():
                oracle = oracle_result(task_id, candidate)
                expected_exit = 1 if state == "initial" else 0
                if oracle.returncode != expected_exit:
                    raise QualificationError(
                        f"{task_id}/{state}: oracle exit {oracle.returncode}, expected {expected_exit}"
                    )
                raw = oracle.stdout
                evidence_count = tap_test_count(raw)
                state_records = []
                for arm in arms_manifest["arms"]:
                    arm_id = arm["id"]
                    work = temp_root / task_id / state / arm_id
                    work.mkdir(parents=True)
                    if arm_id == "raw-control":
                        profile, _indicator = run_profile(
                            profiler,
                            work,
                            profile_input(
                                arm_id=arm_id,
                                task_id=task_id,
                                state=state,
                                raw=raw,
                                evidence_count=evidence_count,
                            ),
                        )
                        measurements = profile["measurements"]
                        arm_record = {
                            "arm_id": arm_id,
                            "disposition": "RAW_BASELINE",
                            "escalation_state": "NOT_APPLICABLE",
                            "final_model_visible_bytes": measurements["final_model_visible_bytes"],
                            "initial_model_visible_bytes": measurements["initial_model_visible_bytes"],
                            "profile_identity": profile["trajectory_identity"],
                            "raw_bytes": len(raw),
                            "suppressed_evidence_count": 0,
                        }
                    else:
                        arm_record, artifacts = run_context_firewall_chain(
                            context_firewall=context_firewall,
                            decision_evidence=decision_evidence,
                            profiler=profiler,
                            context_firewall_head=pins["context-firewall"],
                            decision_evidence_head=pins["decision-evidence-protocol"],
                            task_id=task_id,
                            state=state,
                            arm=arm,
                            raw=raw,
                            evidence_count=evidence_count,
                            work=work,
                        )
                        if task_id == "chunked" and state == "accepted" and arm_id == "bounded-escalating":
                            representative = artifacts
                    state_records.append(arm_record)
                records.append({
                    "arm_renderings": state_records,
                    "oracle_exit": oracle.returncode,
                    "oracle_transcript_identity": sha256_bytes(raw),
                    "state": state,
                    "task_id": task_id,
                    "test_count": evidence_count,
                })

    report = {
        "protocol_version": "opsle.exp001.offline-qualification/v1",
        "classification": "PROVIDER_FREE_IMPLEMENTATION_QUALIFICATION",
        "experiment_id": "EXP-001",
        "experiment_result": None,
        "experiment_run_count": 0,
        "provider_model_run_count": 0,
        "freeze_identity": benchmark["identity"],
        "dependency_revisions": pins,
        "mechanisms_exercised": {
            "context-firewall": {"invocation_count": 36, "measurement_class": "EXACT"},
            "decision-evidence-protocol": {"validation_count": 36, "measurement_class": "OBSERVED"},
            "agent-trajectory-profiler": {"profile_count": 48, "measurement_class": "EXACT"},
        },
        "qualification": "PASS",
        "task_count": len(corpus["tasks"]),
        "oracle_invocation_count": len(records),
        "arm_rendering_count": sum(len(item["arm_renderings"]) for item in records),
        "records": records,
        "limitations": benchmark["claim_limits"],
    }
    return report, representative


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("verify", "qualify"), nargs="?", default="verify")
    parser.add_argument("--context-firewall")
    parser.add_argument("--decision-evidence")
    parser.add_argument("--trajectory-profiler")
    parser.add_argument("--evidence-dir", type=Path)
    args = parser.parse_args()
    try:
        report, representative = qualify(args)
        if args.command == "verify":
            evidence_root = RESEARCH_ROOT / "program/evidence/exp-001-offline-freeze"
            expected_report = evidence_root / "qualification-report.json"
            if not expected_report.is_file() or expected_report.read_bytes() != canonical_bytes(report):
                raise QualificationError("committed qualification report is missing or stale")
            for name, content in representative.items():
                path = evidence_root / name
                if not path.is_file() or path.read_bytes() != content:
                    raise QualificationError(f"committed representative evidence is missing or stale: {name}")
        if args.evidence_dir is not None:
            args.evidence_dir.mkdir(parents=True, exist_ok=True)
            (args.evidence_dir / "qualification-report.json").write_bytes(canonical_bytes(report))
            for name, content in representative.items():
                (args.evidence_dir / name).write_bytes(content)
        sys.stdout.buffer.write(canonical_bytes(report))
        print(
            f"[EXP-001 Offline Freeze] {report['task_count']} tasks | "
            f"{report['arm_rendering_count']} provider-free arm renderings | PASS",
            file=sys.stderr,
        )
        return 0
    except (QualificationError, KeyError, TypeError, ValueError) as error:
        sys.stderr.buffer.write(canonical_bytes({
            "code": "OFFLINE_QUALIFICATION_FAILED",
            "message": str(error),
        }))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
