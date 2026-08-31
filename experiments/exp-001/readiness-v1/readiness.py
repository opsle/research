"""Provider-free EXP-001 entitlement and model-identity contract validator."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
READINESS_ROOT = Path(__file__).resolve().parent
CONTRACT_PATH = READINESS_ROOT / "contract.json"
DOCUMENTATION_PATH = READINESS_ROOT / "documentation-snapshot.json"
ENTITLEMENT_FIXTURE_PATH = READINESS_ROOT / "fixtures/entitlement-unverified.json"
MODEL_IDENTITY_FIXTURE_PATH = READINESS_ROOT / "fixtures/model-identity-blocked.json"

CONTRACT_PROTOCOL = "opsle.exp001.readiness-contract/v1"
DOCUMENTATION_PROTOCOL = "opsle.exp001.provider-documentation-snapshot/v1"
ENTITLEMENT_PROTOCOL = "opsle.exp001.entitlement-evidence/v1"
MODEL_IDENTITY_PROTOCOL = "opsle.exp001.model-identity-evidence/v1"
REPORT_PROTOCOL = "opsle.exp001.readiness-qualification/v1"

REQUIRED_MODEL = "gpt-5.6-sol"
REQUIRED_PROVIDER = "openai"
REQUIRED_WIRE_API = "Responses API"
REQUIRED_ENDPOINT = "/v1/responses"
ENTITLEMENT_MAX_AGE_SECONDS = 300
DOCUMENTATION_MAX_AGE_SECONDS = 86_400

REQUIRED_ENTITLEMENT_CHECKS = {
    "project_status",
    "credential_project_binding",
    "project_model_permissions",
    "model_list",
    "model_retrieve",
    "project_rate_limits",
}
ALLOWED_CLASSIFICATIONS = {
    "ENTITLED",
    "NOT_ENTITLED",
    "UNVERIFIED",
    "PROVIDER_UNAVAILABLE",
    "AMBIGUOUS",
}
FORBIDDEN_KEY_FRAGMENTS = {
    "api_key",
    "bearer",
    "authorization_header",
    "credential_value",
    "secret",
    "access_token",
    "refresh_token",
    "raw_response",
    "request_headers",
    "response_headers",
}
FORBIDDEN_VALUE_PATTERNS = (
    re.compile(r"\bBearer\s+[A-Za-z0-9._-]{12,}", re.IGNORECASE),
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}"),
)
PROVIDER_ID_PATTERN = re.compile(r"^(org|proj|key|svcacct)_[A-Za-z0-9_-]+$")


class ReadinessError(ValueError):
    """Fail-closed provider-free readiness validation error."""


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode()


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def object_identity(value: dict[str, Any]) -> str:
    payload = {key: item for key, item in value.items() if key != "identity"}
    return sha256_bytes(canonical_bytes(payload))


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ReadinessError(f"cannot read JSON evidence: {path}") from error
    if not isinstance(value, dict):
        raise ReadinessError(f"JSON evidence must be an object: {path}")
    return value


def parse_time(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ReadinessError(f"{field} must be an ISO-8601 UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise ReadinessError(f"{field} must be an ISO-8601 UTC timestamp") from error
    return parsed.astimezone(timezone.utc)


def assert_identity(value: dict[str, Any], label: str) -> None:
    if value.get("identity") != object_identity(value):
        raise ReadinessError(f"{label} identity mismatch")


def assert_public_safe(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(fragment in normalized for fragment in FORBIDDEN_KEY_FRAGMENTS):
                raise ReadinessError(f"secret or reusable authentication field rejected at {path}.{key}")
            assert_public_safe(item, f"{path}.{key}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            assert_public_safe(item, f"{path}[{index}]")
        return
    if isinstance(value, str) and any(pattern.search(value) for pattern in FORBIDDEN_VALUE_PATTERNS):
        raise ReadinessError(f"secret or reusable authentication value rejected at {path}")


def validate_contract(contract: dict[str, Any]) -> dict[str, Any]:
    if contract.get("protocol_version") != CONTRACT_PROTOCOL:
        raise ReadinessError("readiness contract protocol mismatch")
    assert_identity(contract, "readiness contract")
    required = contract.get("required_configuration")
    if required != {
        "experiment_id": "EXP-001",
        "provider_id": REQUIRED_PROVIDER,
        "model_id": REQUIRED_MODEL,
        "wire_api": REQUIRED_WIRE_API,
        "endpoint": REQUIRED_ENDPOINT,
    }:
        raise ReadinessError("readiness required configuration drifted")
    entitlement = contract.get("entitlement_policy")
    if not isinstance(entitlement, dict):
        raise ReadinessError("entitlement policy is missing")
    if entitlement.get("freshness_seconds") != ENTITLEMENT_MAX_AGE_SECONDS:
        raise ReadinessError("entitlement freshness policy drifted")
    if entitlement.get("positive_metadata_without_invocation_guarantee") != "UNVERIFIED":
        raise ReadinessError("entitlement positive-evidence ceiling drifted")
    identity_policy = contract.get("model_identity_policy")
    if not isinstance(identity_policy, dict):
        raise ReadinessError("model identity policy is missing")
    if identity_policy.get("required_class") != "IMMUTABLE_PROVIDER_SNAPSHOT":
        raise ReadinessError("immutable provider snapshot is not required")
    if identity_policy.get("aliases_permitted") is not False:
        raise ReadinessError("model aliases must be forbidden")
    validate_launch_sequence(contract)
    return contract


def validate_documentation_snapshot(
    snapshot: dict[str, Any],
    *,
    evaluated_at: str,
    require_fresh: bool = True,
) -> dict[str, Any]:
    assert_public_safe(snapshot)
    if snapshot.get("protocol_version") != DOCUMENTATION_PROTOCOL:
        raise ReadinessError("documentation snapshot protocol mismatch")
    assert_identity(snapshot, "documentation snapshot")
    retrieved = parse_time(snapshot.get("retrieved_at"), "retrieved_at")
    evaluated = parse_time(evaluated_at, "evaluated_at")
    age = (evaluated - retrieved).total_seconds()
    if age < 0:
        raise ReadinessError("documentation snapshot is from the future")
    if require_fresh and age > DOCUMENTATION_MAX_AGE_SECONDS:
        raise ReadinessError("documentation snapshot is stale")
    sources = snapshot.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ReadinessError("documentation sources are missing")
    for source in sources:
        if not isinstance(source, dict):
            raise ReadinessError("documentation source is malformed")
        url = source.get("url")
        if not isinstance(url, str) or not url.startswith("https://developers.openai.com/"):
            raise ReadinessError("documentation source is not an official allowed URL")
    facts = snapshot.get("normalized_facts")
    if not isinstance(facts, dict):
        raise ReadinessError("normalized documentation facts are missing")
    if snapshot.get("normalized_evidence_sha256") != sha256_bytes(canonical_bytes(facts)):
        raise ReadinessError("normalized documentation evidence hash mismatch")
    expected = {
        "provider_id": REQUIRED_PROVIDER,
        "model_id": REQUIRED_MODEL,
        "wire_api": REQUIRED_WIRE_API,
        "endpoint": REQUIRED_ENDPOINT,
    }
    if any(facts.get(key) != value for key, value in expected.items()):
        raise ReadinessError("documentation snapshot model binding drifted")
    if facts.get("distinct_immutable_snapshot_id") is not None:
        snapshots = facts.get("published_snapshot_ids")
        if facts["distinct_immutable_snapshot_id"] not in snapshots:
            raise ReadinessError("immutable snapshot is not bound to the published list")
    if facts.get("provider_documented_invocation_equivalence") is not False:
        raise ReadinessError("current documentation does not establish invocation equivalence")
    return facts


def _validate_provider_identifier(value: Any, field: str) -> str:
    if not isinstance(value, str) or not PROVIDER_ID_PATTERN.fullmatch(value):
        raise ReadinessError(f"{field} must be a provider-returned non-secret identifier")
    return value


def _entitlement_classification(
    checks: dict[str, dict[str, Any]],
    evidence: dict[str, Any],
    documentation_facts: dict[str, Any],
) -> str:
    if any(check["outcome"] == "PROVIDER_UNAVAILABLE" for check in checks.values()):
        return "PROVIDER_UNAVAILABLE"
    if any(check["outcome"] == "DENY" for check in checks.values()):
        return "NOT_ENTITLED"
    if any(check["outcome"] == "AMBIGUOUS" for check in checks.values()):
        return "AMBIGUOUS"
    documented_equivalence = documentation_facts.get(
        "provider_documented_invocation_equivalence"
    )
    if evidence.get("provider_documented_invocation_equivalence") is not documented_equivalence:
        raise ReadinessError("entitlement invocation-equivalence claim is not documentation-bound")
    if documented_equivalence is True:
        guarantee = documentation_facts.get("invocation_equivalence_source")
        if not isinstance(guarantee, str) or not guarantee.startswith(
            "https://developers.openai.com/"
        ):
            raise ReadinessError("ENTITLED requires an official invocation-equivalence source")
        if evidence.get("invocation_equivalence_source") != guarantee:
            raise ReadinessError("entitlement invocation-equivalence source drifted")
        return "ENTITLED"
    return "UNVERIFIED"


def validate_entitlement_evidence(
    evidence: dict[str, Any],
    *,
    evaluated_at: str,
    expected_account: dict[str, str],
    documentation_facts: dict[str, Any],
) -> str:
    assert_public_safe(evidence)
    if evidence.get("protocol_version") != ENTITLEMENT_PROTOCOL:
        raise ReadinessError("entitlement evidence protocol mismatch")
    assert_identity(evidence, "entitlement evidence")
    expected_binding = {
        "provider_id": REQUIRED_PROVIDER,
        "model_id": REQUIRED_MODEL,
        "wire_api": REQUIRED_WIRE_API,
        "endpoint": REQUIRED_ENDPOINT,
    }
    if any(evidence.get(key) != value for key, value in expected_binding.items()):
        raise ReadinessError("entitlement model or API-surface binding mismatch")
    for field in ("organization_id", "project_id", "credential_id"):
        observed = _validate_provider_identifier(evidence.get(field), field)
        if observed != expected_account.get(field):
            raise ReadinessError(f"entitlement {field} does not match the launch account")
    if evidence.get("credential_identity_method") != "PROVIDER_RETURNED_NON_SECRET_ID":
        raise ReadinessError("credential identity must not be derived from an API-key hash")
    probed = parse_time(evidence.get("probed_at"), "probed_at")
    fresh_until = parse_time(evidence.get("fresh_until"), "fresh_until")
    evaluated = parse_time(evaluated_at, "evaluated_at")
    if fresh_until <= probed:
        raise ReadinessError("entitlement freshness interval is invalid")
    if (fresh_until - probed).total_seconds() > ENTITLEMENT_MAX_AGE_SECONDS:
        raise ReadinessError("entitlement freshness interval exceeds policy")
    if evaluated < probed or evaluated > fresh_until:
        raise ReadinessError("entitlement evidence is stale")
    raw_checks = evidence.get("checks")
    if not isinstance(raw_checks, list):
        raise ReadinessError("entitlement checks are missing")
    checks: dict[str, dict[str, Any]] = {}
    for check in raw_checks:
        if not isinstance(check, dict):
            raise ReadinessError("entitlement check is malformed")
        mechanism = check.get("mechanism")
        if mechanism in checks or mechanism not in REQUIRED_ENTITLEMENT_CHECKS:
            raise ReadinessError("entitlement check set is duplicated or unknown")
        if check.get("method") != "GET":
            raise ReadinessError("entitlement checks must be non-mutating GET requests")
        if any(check.get(field) is not False for field in ("causes_inference", "model_token_charges", "mutates_provider_state")):
            raise ReadinessError("entitlement check violates the non-inference contract")
        status = check.get("response_status")
        if not isinstance(status, int) or status < 100 or status > 599:
            raise ReadinessError("entitlement response status is malformed")
        response_fields = check.get("relevant_response_fields")
        if not isinstance(response_fields, dict):
            raise ReadinessError("entitlement relevant response fields are malformed")
        expected_hash = sha256_bytes(canonical_bytes(response_fields))
        if check.get("sanitized_response_sha256") != expected_hash:
            raise ReadinessError("entitlement sanitized response hash mismatch")
        if check.get("outcome") not in {"ALLOW", "DENY", "AMBIGUOUS", "PROVIDER_UNAVAILABLE"}:
            raise ReadinessError("entitlement check outcome is malformed")
        checks[mechanism] = check
    if set(checks) != REQUIRED_ENTITLEMENT_CHECKS:
        raise ReadinessError("entitlement evidence is missing required checks")
    computed = _entitlement_classification(checks, evidence, documentation_facts)
    declared = evidence.get("classification")
    if declared not in ALLOWED_CLASSIFICATIONS or declared != computed:
        raise ReadinessError("entitlement classification does not match evidence")
    return computed


def validate_model_identity_evidence(
    evidence: dict[str, Any],
    *,
    documentation_facts: dict[str, Any],
    require_runtime: bool,
) -> str:
    assert_public_safe(evidence)
    if evidence.get("protocol_version") != MODEL_IDENTITY_PROTOCOL:
        raise ReadinessError("model identity evidence protocol mismatch")
    assert_identity(evidence, "model identity evidence")
    if evidence.get("requested_model_id") != REQUIRED_MODEL:
        raise ReadinessError("model identity requested model mismatch")
    snapshot_id = evidence.get("immutable_provider_snapshot_id")
    published = documentation_facts.get("published_snapshot_ids")
    if snapshot_id is None:
        if evidence.get("prelaunch_status") != "BLOCKED_NO_IMMUTABLE_PROVIDER_SNAPSHOT":
            raise ReadinessError("missing immutable snapshot must block launch")
        if require_runtime:
            raise ReadinessError("a blocked model identity cannot admit runtime evidence")
        return "BLOCKED"
    if not isinstance(published, list) or snapshot_id not in published:
        raise ReadinessError("immutable snapshot is absent from documentation evidence")
    if snapshot_id != documentation_facts.get("distinct_immutable_snapshot_id"):
        raise ReadinessError("provider snapshot is not the documented immutable identity")
    if snapshot_id == REQUIRED_MODEL:
        raise ReadinessError("mutable or unproven model identifier is forbidden")
    if evidence.get("prelaunch_status") != "PASS_IMMUTABLE_PROVIDER_SNAPSHOT":
        raise ReadinessError("immutable provider snapshot status mismatch")
    if require_runtime:
        runtime = evidence.get("runtime_identity")
        if not isinstance(runtime, dict) or not isinstance(runtime.get("returned_model_id"), str):
            raise ReadinessError("runtime model identity is missing")
        if runtime["returned_model_id"] != snapshot_id:
            raise ReadinessError("runtime model identity mismatch")
    return "PASS"


def validate_launch_sequence(contract: dict[str, Any]) -> None:
    sequence = contract.get("launch_sequence")
    if not isinstance(sequence, list) or len(sequence) != 12:
        raise ReadinessError("launch sequence must contain exactly twelve gates")
    if [step.get("order") for step in sequence] != list(range(1, 13)):
        raise ReadinessError("launch sequence order is not contiguous")
    names = [step.get("gate") for step in sequence]
    consume_index = names.index("atomically_claim_and_consume_authorization")
    launch_index = names.index("launch_exactly_one_subject")
    required_before_consumption = {
        "verify_frozen_artifacts",
        "verify_public_catalogue_and_pricing",
        "verify_model_identity_policy",
        "run_initial_non_inference_entitlement_probe",
        "validate_unconsumed_authorization_set",
        "recheck_entitlement_immediately_before_consumption",
    }
    if not required_before_consumption.issubset(set(names[:consume_index])):
        raise ReadinessError("pre-consumption blockers are ordered after authorization consumption")
    if launch_index != consume_index + 1:
        raise ReadinessError("authorization consumption must be immediately followed by one launch")
    if any(step.get("authorization_consumed") is True for step in sequence[:consume_index]):
        raise ReadinessError("authorization is consumed before all readiness blockers pass")
    if sequence[consume_index].get("authorization_consumed") is not True:
        raise ReadinessError("atomic authorization consumption gate is malformed")


def qualify(
    *,
    contract: dict[str, Any],
    documentation: dict[str, Any],
    entitlement: dict[str, Any],
    model_identity: dict[str, Any],
    evaluated_at: str,
) -> dict[str, Any]:
    validate_contract(contract)
    facts = validate_documentation_snapshot(documentation, evaluated_at=evaluated_at)
    account = {
        field: entitlement[field]
        for field in ("organization_id", "project_id", "credential_id")
    }
    entitlement_status = validate_entitlement_evidence(
        entitlement,
        evaluated_at=evaluated_at,
        expected_account=account,
        documentation_facts=facts,
    )
    model_status = validate_model_identity_evidence(
        model_identity,
        documentation_facts=facts,
        require_runtime=False,
    )
    blockers = []
    if entitlement_status != "ENTITLED":
        blockers.append("ACCOUNT_ENTITLEMENT_NOT_PROVEN")
    if model_status != "PASS":
        blockers.append("IMMUTABLE_PROVIDER_MODEL_IDENTITY_UNAVAILABLE")
    report = {
        "protocol_version": REPORT_PROTOCOL,
        "experiment_id": "EXP-001",
        "evaluated_at": evaluated_at,
        "provider_free": True,
        "entitlement_classification": entitlement_status,
        "model_identity_status": model_status,
        "readiness": "BLOCKED" if blockers else "PASS",
        "blockers": blockers,
        "documentation_snapshot_identity": documentation["identity"],
        "documentation_normalized_evidence_sha256": documentation[
            "normalized_evidence_sha256"
        ],
        "entitlement_evidence_identity": entitlement["identity"],
        "model_identity_evidence_identity": model_identity["identity"],
        "provider_model_subject_count": 0,
        "authenticated_provider_probe_count": 0,
        "authorization_consumption_count": 0,
        "experiment_run_count": 0,
        "experiment_result_count": 0,
        "result_envelope_count": 0,
        "lifecycle_status": "PLANNED",
    }
    report["identity"] = object_identity(report)
    return report


def provider_free_source_audit() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
    forbidden_roots = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "openai",
    }
    hits = sorted(imported_roots & forbidden_roots)
    if hits:
        raise ReadinessError(f"provider transport capability is forbidden: {hits}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("qualify", nargs="?")
    parser.add_argument("--evaluated-at", required=True)
    arguments = parser.parse_args()
    provider_free_source_audit()
    report = qualify(
        contract=load_json(CONTRACT_PATH),
        documentation=load_json(DOCUMENTATION_PATH),
        entitlement=load_json(ENTITLEMENT_FIXTURE_PATH),
        model_identity=load_json(MODEL_IDENTITY_FIXTURE_PATH),
        evaluated_at=arguments.evaluated_at,
    )
    print(canonical_bytes(report).decode(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
