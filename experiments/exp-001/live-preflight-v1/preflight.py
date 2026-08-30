#!/usr/bin/env python3
"""Provider-free EXP-001 live authorization and catalogue preflight."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import secrets
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments/exp-001"
PREREG_ROOT = EXP_ROOT / "preregistration-v1"
CATALOGUE_PATH = Path(__file__).with_name("model-catalogue.json")
VALUE_VALIDATOR_PATH = ROOT / "tools/validate_value_receipt.py"

AUTHORIZATION_PROTOCOL = "opsle.exp001.live-provider-authorization/v1"
SET_PROTOCOL = "opsle.exp001.live-provider-authorization-set/v1"
CATALOGUE_PROTOCOL = "opsle.exp001.model-catalogue/v1"
PRICING_PROTOCOL = "opsle.exp001.pricing-preflight/v1"
REPORT_PROTOCOL = "opsle.exp001.live-preflight-qualification/v1"
LIVE_AUTHORIZATION = "LIVE_PROVIDER_RUN"
FIXTURE_AUTHORIZATION = "PROVIDER_FREE_FIXTURE"


class PreflightError(RuntimeError):
    """Fail-closed provider-free preflight error."""


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        + b"\n"
    )


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def object_identity(value: dict[str, Any]) -> str:
    payload = {key: item for key, item in value.items() if key != "identity"}
    return sha256_bytes(canonical_bytes(payload))


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PreflightError(f"invalid JSON artifact: {path.name}") from error
    if not isinstance(value, dict):
        raise PreflightError(f"JSON artifact must be an object: {path.name}")
    return value


def parse_timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise PreflightError(f"{field} must be an RFC3339 UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise PreflightError(f"{field} must be an RFC3339 UTC timestamp") from error
    if parsed.tzinfo != timezone.utc:
        raise PreflightError(f"{field} must be UTC")
    return parsed


def selected_public_block(block_id: str) -> list[dict[str, Any]]:
    index = load_json(PREREG_ROOT / "allocation-index.json")
    entries = [
        entry
        for entry in index.get("entries", [])
        if isinstance(entry, dict) and entry.get("block_id") == block_id
    ]
    if len(entries) != 4:
        raise PreflightError("selected public block must contain exactly four labels")
    labels = [entry.get("subject_label") for entry in entries]
    if any(not isinstance(label, str) or not label for label in labels):
        raise PreflightError("selected public block contains a malformed label")
    if len(set(labels)) != 4:
        raise PreflightError("selected public block contains duplicate labels")
    if {entry.get("position") for entry in entries} != {1, 2, 3, 4}:
        raise PreflightError("selected public block positions are malformed")
    configuration_ids = {entry.get("configuration_id") for entry in entries}
    if configuration_ids != {index.get("configuration_id")}:
        raise PreflightError("selected public block configuration binding drifted")
    return sorted(entries, key=lambda entry: entry["position"])


def first_public_block_id() -> str:
    index = load_json(PREREG_ROOT / "allocation-index.json")
    entries = index.get("entries")
    if not isinstance(entries, list) or not entries:
        raise PreflightError("allocation index contains no public block")
    block_id = entries[0].get("block_id")
    if not isinstance(block_id, str) or not block_id:
        raise PreflightError("first public block ID is malformed")
    return block_id


def authorization_payload(
    *,
    entry: dict[str, Any],
    set_id: str,
    authorization_id: str,
    issued_at: str,
    valid_from: str,
    expires_at: str,
    preregistration_identity: str,
    maximum_spend_usd: float,
) -> dict[str, Any]:
    return {
        "protocol_version": AUTHORIZATION_PROTOCOL,
        "authorization_id": authorization_id,
        "authorization_set_id": set_id,
        "authorization_class": LIVE_AUTHORIZATION,
        "experiment_id": "EXP-001",
        "preregistration_identity": preregistration_identity,
        "configuration_id": entry["configuration_id"],
        "block_id": entry["block_id"],
        "subject_label": entry["subject_label"],
        "provider_run_authorized": True,
        "max_provider_runs": 1,
        "maximum_spend_usd": maximum_spend_usd,
        "fixture_only": False,
        "provider_launch_permitted": True,
        "issued_at": issued_at,
        "valid_from": valid_from,
        "expires_at": expires_at,
        "authorization_state": "UNCONSUMED",
        "consumed_at": None,
        "result_envelope": None,
    }


def build_set_manifest(
    *,
    set_id: str,
    block_id: str,
    issued_at: str,
    valid_from: str,
    expires_at: str,
    authorization_records: list[dict[str, Any]],
    authorization_files: dict[str, bytes],
    preregistration_identity: str,
    configuration_id: str,
) -> dict[str, Any]:
    manifest = {
        "protocol_version": SET_PROTOCOL,
        "authorization_set_id": set_id,
        "authorization_class": LIVE_AUTHORIZATION,
        "experiment_id": "EXP-001",
        "preregistration_identity": preregistration_identity,
        "configuration_id": configuration_id,
        "block_id": block_id,
        "issued_at": issued_at,
        "valid_from": valid_from,
        "expires_at": expires_at,
        "authorization_count": 4,
        "authorization_state": "UNCONSUMED",
        "authorization_consumption_count": 0,
        "result_envelope_count": 0,
        "provider_model_launch_count": 0,
        "experiment_run_count": 0,
        "experiment_result_count": 0,
        "authorizations": [
            {
                "subject_label": record["subject_label"],
                "authorization_id": record["authorization_id"],
                "path": f"authorizations/{record['subject_label']}.json",
                "sha256": sha256_bytes(authorization_files[record["subject_label"]]),
            }
            for record in authorization_records
        ],
    }
    manifest["identity"] = object_identity(manifest)
    return manifest


def materialize_authorization_set(
    *,
    destination: Path,
    block_id: str,
    set_id: str,
    authorization_ids: list[str],
    issued_at: str,
    valid_from: str,
    expires_at: str,
) -> dict[str, Any]:
    if destination.exists():
        raise PreflightError("authorization set destination must be absent")
    if len(authorization_ids) != 4 or len(set(authorization_ids)) != 4:
        raise PreflightError("exactly four unique authorization IDs are required")
    issued = parse_timestamp(issued_at, "issued_at")
    starts = parse_timestamp(valid_from, "valid_from")
    ends = parse_timestamp(expires_at, "expires_at")
    if not issued <= starts < ends:
        raise PreflightError("authorization temporal bounds are inconsistent")

    entries = selected_public_block(block_id)
    preregistration = load_json(PREREG_ROOT / "preregistration.json")
    configuration = load_json(PREREG_ROOT / "subject-config.json")
    maximum_spend = configuration["subject_limits"]["maximum_spend_usd_per_subject"]
    records = [
        authorization_payload(
            entry=entry,
            set_id=set_id,
            authorization_id=authorization_id,
            issued_at=issued_at,
            valid_from=valid_from,
            expires_at=expires_at,
            preregistration_identity=preregistration["identity"],
            maximum_spend_usd=maximum_spend,
        )
        for entry, authorization_id in zip(entries, authorization_ids, strict=True)
    ]
    files = {record["subject_label"]: canonical_bytes(record) for record in records}
    manifest = build_set_manifest(
        set_id=set_id,
        block_id=block_id,
        issued_at=issued_at,
        valid_from=valid_from,
        expires_at=expires_at,
        authorization_records=records,
        authorization_files=files,
        preregistration_identity=preregistration["identity"],
        configuration_id=configuration["identity"],
    )

    destination.mkdir(mode=0o700, parents=True)
    authorization_dir = destination / "authorizations"
    authorization_dir.mkdir(mode=0o700)
    for label, content in files.items():
        path = authorization_dir / f"{label}.json"
        path.write_bytes(content)
        path.chmod(0o600)
    manifest_path = destination / "set-manifest.json"
    manifest_path.write_bytes(canonical_bytes(manifest))
    manifest_path.chmod(0o600)
    return manifest


def validate_authorization_set(
    set_directory: Path,
    *,
    validated_at: str,
) -> dict[str, Any]:
    validation_time = parse_timestamp(validated_at, "validated_at")
    if not set_directory.is_dir() or set_directory.is_symlink():
        raise PreflightError("authorization set directory is unavailable or unsafe")
    manifest_path = set_directory / "set-manifest.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise PreflightError("authorization set manifest is unavailable or unsafe")
    manifest = load_json(manifest_path)
    if manifest.get("protocol_version") != SET_PROTOCOL:
        raise PreflightError("authorization set protocol is malformed")
    if manifest.get("identity") != object_identity(manifest):
        raise PreflightError("authorization set identity mismatch")
    if manifest.get("authorization_count") != 4:
        raise PreflightError("authorization set must declare exactly four labels")

    block_id = manifest.get("block_id")
    if not isinstance(block_id, str):
        raise PreflightError("authorization set block binding is malformed")
    entries = selected_public_block(block_id)
    expected_by_label = {entry["subject_label"]: entry for entry in entries}
    authorization_dir = set_directory / "authorizations"
    if not authorization_dir.is_dir() or authorization_dir.is_symlink():
        raise PreflightError("authorization directory is unavailable or unsafe")
    expected_names = {f"{label}.json" for label in expected_by_label}
    observed_names = {path.name for path in authorization_dir.iterdir()}
    if observed_names != expected_names:
        raise PreflightError("authorization directory must contain exactly four labels")

    preregistration = load_json(PREREG_ROOT / "preregistration.json")
    configuration = load_json(PREREG_ROOT / "subject-config.json")
    required_set = {
        "authorization_class": LIVE_AUTHORIZATION,
        "experiment_id": "EXP-001",
        "preregistration_identity": preregistration["identity"],
        "configuration_id": configuration["identity"],
        "authorization_state": "UNCONSUMED",
        "authorization_consumption_count": 0,
        "result_envelope_count": 0,
        "provider_model_launch_count": 0,
        "experiment_run_count": 0,
        "experiment_result_count": 0,
    }
    if any(manifest.get(key) != value for key, value in required_set.items()):
        raise PreflightError("authorization set binding or state drifted")
    starts = parse_timestamp(manifest.get("valid_from"), "valid_from")
    ends = parse_timestamp(manifest.get("expires_at"), "expires_at")
    if validation_time < starts:
        raise PreflightError("authorization set is not yet valid")
    if validation_time >= ends:
        raise PreflightError("authorization set is expired")

    records: list[dict[str, Any]] = []
    labels: set[str] = set()
    authorization_ids: set[str] = set()
    manifest_records = manifest.get("authorizations")
    if not isinstance(manifest_records, list) or len(manifest_records) != 4:
        raise PreflightError("authorization manifest must contain exactly four labels")
    manifest_by_label = {
        item.get("subject_label"): item
        for item in manifest_records
        if isinstance(item, dict)
    }
    if set(manifest_by_label) != set(expected_by_label):
        raise PreflightError("authorization manifest labels are missing or duplicated")

    for label, entry in expected_by_label.items():
        path = authorization_dir / f"{label}.json"
        if path.is_symlink() or not path.is_file():
            raise PreflightError("authorization files must be regular files")
        content = path.read_bytes()
        record = load_json(path)
        required = {
            "protocol_version": AUTHORIZATION_PROTOCOL,
            "authorization_set_id": manifest["authorization_set_id"],
            "authorization_class": LIVE_AUTHORIZATION,
            "experiment_id": "EXP-001",
            "preregistration_identity": preregistration["identity"],
            "configuration_id": configuration["identity"],
            "block_id": block_id,
            "subject_label": label,
            "provider_run_authorized": True,
            "max_provider_runs": 1,
            "fixture_only": False,
            "provider_launch_permitted": True,
            "authorization_state": "UNCONSUMED",
            "consumed_at": None,
            "result_envelope": None,
        }
        if any(record.get(key) != value for key, value in required.items()):
            raise PreflightError("authorization schema, class, or binding drifted")
        if record.get("block_id") != entry["block_id"]:
            raise PreflightError("authorization block binding drifted")
        authorization_id = record.get("authorization_id")
        if not isinstance(authorization_id, str) or not authorization_id:
            raise PreflightError("authorization identity is malformed")
        if label in labels:
            raise PreflightError("authorization labels must be unique")
        if authorization_id in authorization_ids:
            raise PreflightError("authorization identities must be unique")
        labels.add(label)
        authorization_ids.add(authorization_id)
        budget = record.get("maximum_spend_usd")
        required_budget = configuration["subject_limits"][
            "maximum_spend_usd_per_subject"
        ]
        if not isinstance(budget, (int, float)) or budget < required_budget:
            raise PreflightError("authorization budget is below the frozen ceiling")
        record_start = parse_timestamp(record.get("valid_from"), "valid_from")
        record_end = parse_timestamp(record.get("expires_at"), "expires_at")
        if validation_time < record_start:
            raise PreflightError("authorization is not yet valid")
        if validation_time >= record_end:
            raise PreflightError("authorization is expired")
        manifest_record = manifest_by_label[label]
        if (
            manifest_record.get("authorization_id") != authorization_id
            or manifest_record.get("path") != f"authorizations/{label}.json"
            or manifest_record.get("sha256") != sha256_bytes(content)
        ):
            raise PreflightError("authorization manifest binding mismatch")
        records.append(record)

    return {
        "authorization_set_id": manifest["authorization_set_id"],
        "authorization_set_identity": manifest["identity"],
        "authorization_class": LIVE_AUTHORIZATION,
        "authorization_count": len(records),
        "label_count": len(labels),
        "authorization_consumption_count": 0,
        "result_envelope_count": 0,
        "provider_model_launch_count": 0,
        "experiment_run_count": 0,
        "experiment_result_count": 0,
        "valid": True,
    }


def validate_catalogue(catalogue: dict[str, Any]) -> dict[str, Any]:
    if catalogue.get("protocol_version") != CATALOGUE_PROTOCOL:
        raise PreflightError("model catalogue protocol is malformed")
    if catalogue.get("identity") != object_identity(catalogue):
        raise PreflightError("model catalogue identity mismatch")
    candidates = catalogue.get("eligible_candidates")
    if not isinstance(candidates, list) or len(candidates) != 1:
        raise PreflightError("catalogue must contain the one preregistered candidate")
    candidate = candidates[0]
    configuration = load_json(PREREG_ROOT / "subject-config.json")
    model = configuration["model_provider_configuration"]
    required = {
        "provider_id": model["provider_id"],
        "model_id": model["model_id"],
        "wire_api": model["wire_api"],
        "availability": "DOCUMENTED_API_MODEL_ACCOUNT_ACCESS_UNVERIFIED",
        "pricing_basis": "USD_PER_1M_TEXT_TOKENS_STANDARD_SHORT_CONTEXT",
        "input_price_usd": 4.0,
        "cached_input_price_usd": 0.4,
        "output_price_usd": 20.0,
        "context_window_tokens": 1_050_000,
        "max_output_tokens": 128_000,
    }
    if any(candidate.get(key) != value for key, value in required.items()):
        raise PreflightError("catalogue candidate drifted from current documentation")
    if candidate.get("subscription_api_distinction") != (
        "Direct API usage pricing; ChatGPT or Codex subscription access is not "
        "used and does not authorize this experiment."
    ):
        raise PreflightError("catalogue API/subscription distinction is missing")
    sources = candidate.get("sources")
    if not isinstance(sources, list) or len(sources) < 2:
        raise PreflightError("catalogue provenance is incomplete")
    parse_timestamp(catalogue.get("retrieved_at"), "retrieved_at")
    return candidate


def pricing_preflight(catalogue: dict[str, Any]) -> dict[str, Any]:
    candidate = validate_catalogue(catalogue)
    configuration = load_json(PREREG_ROOT / "subject-config.json")
    limits = configuration["subject_limits"]
    input_ceiling = limits["max_api_calls"] * limits["max_request_body_bytes"]
    output_ceiling = limits["max_api_calls"] * limits["max_output_tokens_per_response"]
    spend_ceiling = (
        input_ceiling * candidate["input_price_usd"] / 1_000_000
        + output_ceiling * candidate["output_price_usd"] / 1_000_000
    )
    result = {
        "protocol_version": PRICING_PROTOCOL,
        "experiment_id": "EXP-001",
        "subject_configuration_id": configuration["identity"],
        "model_catalogue_identity": catalogue["identity"],
        "provider_id": candidate["provider_id"],
        "model_id": candidate["model_id"],
        "pricing_basis": candidate["pricing_basis"],
        "input_price_usd_per_million_tokens": candidate["input_price_usd"],
        "cached_input_price_usd_per_million_tokens": candidate[
            "cached_input_price_usd"
        ],
        "output_price_usd_per_million_tokens": candidate["output_price_usd"],
        "conservative_input_token_ceiling": input_ceiling,
        "conservative_output_token_ceiling": output_ceiling,
        "derived_spend_ceiling_usd": spend_ceiling,
        "registered_spend_ceiling_usd": limits["maximum_spend_usd_per_subject"],
        "long_context_threshold_tokens": 272_000,
        "long_context_multiplier_applies": False,
        "price_drift_from_frozen_configuration": False,
        "account_access_verified": False,
        "provider_call_count": 0,
        "admission": "PASS_PROVIDER_FREE_CURRENT_DOCUMENTATION",
        "limitations": [
            "Provider documentation establishes catalogue availability, not this account's entitlement.",
            "No API request was made and no provider/model subject was launched.",
            "Promotional pricing may change; launch requires a fresh fail-closed catalogue check.",
        ],
    }
    if spend_ceiling > limits["maximum_spend_usd_per_subject"]:
        raise PreflightError("current pricing exceeds the registered spend ceiling")
    result["identity"] = object_identity(result)
    return result


def snapshot(directory: Path) -> dict[str, bytes]:
    return {
        path.relative_to(directory).as_posix(): path.read_bytes()
        for path in sorted(item for item in directory.rglob("*") if item.is_file())
    }


def replay_inputs(manifest: dict[str, Any]) -> dict[str, Any]:
    records = manifest.get("authorizations")
    if not isinstance(records, list) or len(records) != 4:
        raise PreflightError("authorization replay inputs are malformed")
    return {
        "block_id": manifest["block_id"],
        "set_id": manifest["authorization_set_id"],
        "authorization_ids": [record["authorization_id"] for record in records],
        "issued_at": manifest["issued_at"],
        "valid_from": manifest["valid_from"],
        "expires_at": manifest["expires_at"],
    }


def mutate_case(source: Path, root: Path, name: str) -> Path:
    destination = root / name
    shutil.copytree(source, destination)
    return destination


def first_authorization_path(directory: Path) -> Path:
    return min((directory / "authorizations").glob("*.json"))


def second_authorization_path(directory: Path) -> Path:
    return sorted((directory / "authorizations").glob("*.json"))[1]


def rewrite_record(path: Path, mutator: Any) -> None:
    record = load_json(path)
    mutator(record)
    path.write_bytes(canonical_bytes(record))


def rewrite_manifest(directory: Path, mutator: Any) -> None:
    path = directory / "set-manifest.json"
    manifest = load_json(path)
    mutator(manifest)
    manifest["identity"] = object_identity(manifest)
    path.write_bytes(canonical_bytes(manifest))


def expect_rejection(
    directory: Path,
    *,
    validated_at: str,
    expected: str,
) -> None:
    try:
        validate_authorization_set(directory, validated_at=validated_at)
    except PreflightError as error:
        if expected not in str(error):
            raise PreflightError(
                f"negative validation returned unexpected reason: {error}"
            ) from error
    else:
        raise PreflightError("negative authorization validation unexpectedly passed")


def provider_free_source_audit() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    forbidden_modules = {"http", "requests", "socket", "subprocess", "urllib"}
    forbidden_calls = {"exec", "eval", "system", "popen", "spawn"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(
            alias.name.split(".")[0] in forbidden_modules for alias in node.names
        ):
            raise PreflightError("validation path imports provider-capable transport")
        if (
            isinstance(node, ast.ImportFrom)
            and (node.module or "").split(".")[0] in forbidden_modules
        ):
            raise PreflightError("validation path imports provider-capable transport")
        if isinstance(node, ast.Call):
            name = None
            if isinstance(node.func, ast.Name):
                name = node.func.id.lower()
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr.lower()
            if name in forbidden_calls:
                raise PreflightError(
                    "validation path contains process-launch capability"
                )


def measurement(identity: str, result: int, evidence_ref: str) -> dict[str, Any]:
    return {
        "id": identity,
        "unit": "count",
        "class": "EXACT",
        "direction": "PROTECTION_SIGNAL",
        "baseline": None,
        "result": result,
        "delta": None,
        "derivation": None,
        "source_verification": "VERIFIED",
        "evidence_refs": [evidence_ref],
        "operator_display": True,
        "aggregation": {"method": "SUM", "safe": True},
        "limitations": [],
    }


def value_receipt(
    *,
    set_id: str,
    set_identity: str,
    catalogue_identity: str,
    pricing_identity: str,
    validation_count: int,
) -> dict[str, Any]:
    return {
        "schema": "opsle.value-receipt.v1",
        "mechanism": {
            "id": "opsle.exp001-live-provider-preflight",
            "name": "EXP-001 Live Provider Authorization Preflight",
            "version": "1.0.0",
            "revision": sha256_bytes(Path(__file__).read_bytes()),
        },
        "operation": {
            "id": set_id,
            "name": "prepare-live-authorization-set",
            "configuration_id": catalogue_identity,
            "policy_id": pricing_identity,
        },
        "run": {
            "id": set_id,
            "repository": "opsle/research",
            "task_classification": "EXP-001_PROVIDER_FREE_LIVE_AUTHORIZATION_PREFLIGHT",
            "work_classification": "DETERMINISTIC_COORDINATION",
        },
        "measurements": [
            measurement("live_authorization_label_count", 4, "authorization_set"),
            measurement(
                "authorization_validation_count", validation_count, "qualification"
            ),
            measurement("subject_rendering_count", 0, "qualification"),
            measurement(
                "subject_visible_canonical_arm_identifier_count", 0, "qualification"
            ),
            measurement("provider_model_launch_count", 0, "qualification"),
            measurement("authorization_consumption_count", 0, "authorization_set"),
            measurement("experiment_run_count", 0, "qualification"),
            measurement("experiment_result_count", 0, "qualification"),
        ],
        "evidence": [
            {
                "id": "authorization_set",
                "kind": "CONTENT_HASH",
                "locator": set_identity,
                "trust": "VERIFIED",
            },
            {
                "id": "model_catalogue",
                "kind": "CONTENT_HASH",
                "locator": catalogue_identity,
                "trust": "VERIFIED",
            },
            {
                "id": "pricing_preflight",
                "kind": "CONTENT_HASH",
                "locator": pricing_identity,
                "trust": "VERIFIED",
            },
            {
                "id": "qualification",
                "kind": "RUN_ARTIFACT",
                "locator": set_id,
                "trust": "VERIFIED",
            },
        ],
        "limitations": [
            "Preparation and validation do not consume authorization or execute a provider/model subject.",
            "No subject rendering or result envelope was created by this path.",
            "Account-specific model access is unverified because no provider call was made.",
            "No token, cost, latency, correctness, savings, or causal-benefit claim is made.",
        ],
    }


def qualify(
    *,
    set_directory: Path,
    catalogue_path: Path,
    validated_at: str,
) -> dict[str, bytes]:
    provider_free_source_audit()
    catalogue = load_json(catalogue_path)
    pricing = pricing_preflight(catalogue)
    validation = validate_authorization_set(
        set_directory,
        validated_at=validated_at,
    )
    manifest = load_json(set_directory / "set-manifest.json")
    inputs = replay_inputs(manifest)
    validation_count = 1

    with tempfile.TemporaryDirectory(prefix="opsle-exp001-live-preflight-") as temp:
        root = Path(temp)
        first = root / "replay-first"
        second = root / "replay-second"
        materialize_authorization_set(destination=first, **inputs)
        materialize_authorization_set(destination=second, **inputs)
        first_validation = validate_authorization_set(first, validated_at=validated_at)
        second_validation = validate_authorization_set(
            second, validated_at=validated_at
        )
        validation_count += 2
        if first_validation != second_validation or snapshot(first) != snapshot(second):
            raise PreflightError("deterministic authorization replay drifted")
        if snapshot(set_directory) != snapshot(first):
            raise PreflightError(
                "created authorization set differs from deterministic replay"
            )

        fixture = mutate_case(set_directory, root, "fixture")
        fixture_path = first_authorization_path(fixture)
        rewrite_record(
            fixture_path,
            lambda record: record.update(
                {
                    "authorization_class": FIXTURE_AUTHORIZATION,
                    "fixture_only": True,
                    "provider_launch_permitted": False,
                }
            ),
        )
        expect_rejection(
            fixture,
            validated_at=validated_at,
            expected="class, or binding",
        )
        validation_count += 1

        duplicate_label = mutate_case(set_directory, root, "duplicate-label")
        first_record = load_json(first_authorization_path(duplicate_label))
        rewrite_record(
            second_authorization_path(duplicate_label),
            lambda record: record.update(
                {"subject_label": first_record["subject_label"]}
            ),
        )
        expect_rejection(
            duplicate_label,
            validated_at=validated_at,
            expected="class, or binding",
        )
        validation_count += 1

        duplicate_identity = mutate_case(set_directory, root, "duplicate-identity")
        first_record = load_json(first_authorization_path(duplicate_identity))
        rewrite_record(
            second_authorization_path(duplicate_identity),
            lambda record: record.update(
                {"authorization_id": first_record["authorization_id"]}
            ),
        )
        expect_rejection(
            duplicate_identity,
            validated_at=validated_at,
            expected="identities must be unique",
        )
        validation_count += 1

        missing = mutate_case(set_directory, root, "missing")
        first_authorization_path(missing).unlink()
        expect_rejection(missing, validated_at=validated_at, expected="exactly four")
        validation_count += 1

        extra = mutate_case(set_directory, root, "extra")
        (extra / "authorizations" / "unexpected.json").write_text(
            "{}\n", encoding="utf-8"
        )
        expect_rejection(extra, validated_at=validated_at, expected="exactly four")
        validation_count += 1

        wrong_experiment = mutate_case(set_directory, root, "wrong-experiment")
        rewrite_record(
            first_authorization_path(wrong_experiment),
            lambda record: record.update({"experiment_id": "EXP-OTHER"}),
        )
        expect_rejection(
            wrong_experiment,
            validated_at=validated_at,
            expected="class, or binding",
        )
        validation_count += 1

        wrong_block = mutate_case(set_directory, root, "wrong-block")
        rewrite_record(
            first_authorization_path(wrong_block),
            lambda record: record.update({"block_id": "wrong-block"}),
        )
        expect_rejection(
            wrong_block,
            validated_at=validated_at,
            expected="class, or binding",
        )
        validation_count += 1

        malformed = mutate_case(set_directory, root, "malformed")
        first_authorization_path(malformed).write_bytes(b"{\n")
        expect_rejection(malformed, validated_at=validated_at, expected="invalid JSON")
        validation_count += 1

        expired = mutate_case(set_directory, root, "expired")
        rewrite_manifest(
            expired,
            lambda value: value.update({"expires_at": "2026-08-30T00:00:00Z"}),
        )
        expect_rejection(expired, validated_at=validated_at, expected="expired")
        validation_count += 1

        not_yet_valid = mutate_case(set_directory, root, "not-yet-valid")
        rewrite_manifest(
            not_yet_valid,
            lambda value: value.update({"valid_from": "2026-12-01T00:00:00Z"}),
        )
        expect_rejection(
            not_yet_valid,
            validated_at=validated_at,
            expected="not yet valid",
        )
        validation_count += 1

    if validation_count != 13:
        raise PreflightError("authorization validation accounting drifted")

    receipt = value_receipt(
        set_id=validation["authorization_set_id"],
        set_identity=validation["authorization_set_identity"],
        catalogue_identity=catalogue["identity"],
        pricing_identity=pricing["identity"],
        validation_count=validation_count,
    )
    report = {
        "protocol_version": REPORT_PROTOCOL,
        "experiment_id": "EXP-001",
        "qualification": "PASS",
        "classification": "PROVIDER_FREE_LIVE_AUTHORIZATION_PREFLIGHT",
        "validated_at": validated_at,
        "authorization_set_id": validation["authorization_set_id"],
        "authorization_set_identity": validation["authorization_set_identity"],
        "authorization_class": LIVE_AUTHORIZATION,
        "live_authorization_label_count": 4,
        "live_authorization_record_count": 4,
        "authorization_validation_count": validation_count,
        "fixture_rejected_from_live_gate": True,
        "duplicate_label_rejected": True,
        "duplicate_authorization_identity_rejected": True,
        "missing_label_rejected": True,
        "extra_label_rejected": True,
        "wrong_experiment_binding_rejected": True,
        "wrong_block_binding_rejected": True,
        "malformed_authorization_rejected": True,
        "expired_authorization_rejected": True,
        "not_yet_valid_authorization_rejected": True,
        "deterministic_replay_count": 2,
        "deterministic_payloads_byte_identical": True,
        "model_catalogue_identity": catalogue["identity"],
        "pricing_preflight_identity": pricing["identity"],
        "catalogue_candidate_count": 1,
        "catalogue_unresolved_field_count": 2,
        "subject_rendering_count": 0,
        "subject_visible_canonical_arm_identifier_count": 0,
        "private_mapping_access_count": 0,
        "raw_evidence_access_count": 0,
        "provider_model_launch_count": 0,
        "authorization_consumption_count": 0,
        "result_envelope_count": 0,
        "experiment_run_count": 0,
        "experiment_result_count": 0,
        "lifecycle_status": "PLANNED",
        "lifecycle_impact": "NONE_NO_ADVANCEMENT",
        "value_receipt_sha256": sha256_bytes(canonical_bytes(receipt)),
        "limitations": [
            "This provider-free preparation does not establish account-specific model access.",
            "No subject was rendered or launched and no authorization was consumed.",
            "No experiment run, result envelope, or experiment result was created.",
            "No token, cost, latency, correctness, savings, or causal-benefit claim is made.",
        ],
    }
    public_bytes = canonical_bytes(report)
    forbidden = (
        b'"subject_label"',
        b'"authorization_id"',
        manifest["block_id"].encode("utf-8"),
    )
    if any(value in public_bytes for value in forbidden):
        raise PreflightError("public qualification evidence leaks private set detail")
    return {
        "model-catalogue.json": canonical_bytes(catalogue),
        "pricing-preflight.json": canonical_bytes(pricing),
        "qualification-report.json": public_bytes,
        "value-receipt.json": canonical_bytes(receipt),
    }


def write_evidence(destination: Path, evidence: dict[str, bytes]) -> None:
    if destination.exists():
        raise PreflightError("evidence destination must be absent")
    destination.mkdir(mode=0o755, parents=True)
    for name, content in evidence.items():
        (destination / name).write_bytes(content)


def new_id(prefix: str) -> str:
    return f"{prefix}-{secrets.token_hex(16)}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser("create")
    create.add_argument("--destination", type=Path, required=True)
    create.add_argument("--block-id", default=None)
    create.add_argument("--set-id", default=None)
    create.add_argument("--issued-at", required=True)
    create.add_argument("--valid-from", required=True)
    create.add_argument("--expires-at", required=True)
    qualify_parser = subparsers.add_parser("qualify")
    qualify_parser.add_argument("--authorization-set", type=Path, required=True)
    qualify_parser.add_argument("--catalogue", type=Path, default=CATALOGUE_PATH)
    qualify_parser.add_argument("--validated-at", required=True)
    qualify_parser.add_argument("--evidence-dir", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "create":
            manifest = materialize_authorization_set(
                destination=args.destination,
                block_id=args.block_id or first_public_block_id(),
                set_id=args.set_id or new_id("exp001-live-authset"),
                authorization_ids=[new_id("exp001-live-authz") for _ in range(4)],
                issued_at=args.issued_at,
                valid_from=args.valid_from,
                expires_at=args.expires_at,
            )
            print(
                canonical_bytes(
                    {
                        "authorization_set_id": manifest["authorization_set_id"],
                        "authorization_count": 4,
                        "authorization_consumption_count": 0,
                        "provider_model_launch_count": 0,
                    }
                ).decode("utf-8"),
                end="",
            )
        else:
            evidence = qualify(
                set_directory=args.authorization_set,
                catalogue_path=args.catalogue,
                validated_at=args.validated_at,
            )
            if args.evidence_dir is not None:
                write_evidence(args.evidence_dir, evidence)
            report = json.loads(evidence["qualification-report.json"])
            print(canonical_bytes(report).decode("utf-8"), end="")
        return 0
    except PreflightError as error:
        parser.error(str(error))


if __name__ == "__main__":
    raise SystemExit(main())
