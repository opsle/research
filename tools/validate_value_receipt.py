#!/usr/bin/env python3
"""Validate opsle.value-receipt.v1 structure and evidence ceilings."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

SCHEMA = "opsle.value-receipt.v1"
CLASSES = {"EXACT", "OBSERVED", "ESTIMATED", "MODELED", "EXPERIMENTAL"}
UNITS = {"byte", "event", "count", "ratio", "percent", "boolean", "millisecond", "token", "usd", "state"}
DIRECTIONS = {"HIGHER_IS_VALUE", "LOWER_IS_VALUE", "NEUTRAL", "PROTECTION_SIGNAL", "NOT_APPLICABLE"}
VERIFICATION = {"VERIFIED", "OBSERVED", "CALLER_SUPPLIED", "UNVERIFIED", "NOT_APPLICABLE"}
EVIDENCE_KINDS = {"CONTENT_HASH", "JSON_POINTER", "RUN_ARTIFACT", "PROVIDER_RECORD", "URI", "CALLER_ASSERTION"}
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def _object(value: Any) -> bool:
    return isinstance(value, dict)


def _finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def validate(receipt: Any) -> list[str]:
    errors: list[str] = []
    if not _object(receipt):
        return ["receipt must be an object"]
    required = {"schema", "mechanism", "run", "operation", "measurements", "evidence", "limitations"}
    for field in sorted(required - set(receipt)):
        errors.append(f"/{field}: required field missing")
    if receipt.get("schema") != SCHEMA:
        errors.append(f"/schema: only {SCHEMA} is supported")

    mechanism = receipt.get("mechanism")
    if not _object(mechanism):
        errors.append("/mechanism: object required")
    else:
        for field in ("id", "name", "version", "revision"):
            if field not in mechanism:
                errors.append(f"/mechanism/{field}: required field missing")
        for field in ("id", "name", "version"):
            if not isinstance(mechanism.get(field), str) or not mechanism[field]:
                errors.append(f"/mechanism/{field}: nonempty string required")
        if mechanism.get("revision") is not None and not isinstance(mechanism.get("revision"), str):
            errors.append("/mechanism/revision: nonempty string or null required")

    run = receipt.get("run")
    if not _object(run) or "id" not in run:
        errors.append("/run/id: string or null required")
    elif run["id"] is not None and (not isinstance(run["id"], str) or not run["id"]):
        errors.append("/run/id: nonempty string or null required")

    operation = receipt.get("operation")
    if not _object(operation):
        errors.append("/operation: object required")
    else:
        for field in ("id", "name", "configuration_id", "policy_id"):
            if field not in operation:
                errors.append(f"/operation/{field}: required field missing")
        if not isinstance(operation.get("name"), str) or not operation.get("name"):
            errors.append("/operation/name: nonempty string required")

    evidence = receipt.get("evidence")
    evidence_ids: set[str] = set()
    evidence_by_id: dict[str, dict[str, Any]] = {}
    if not isinstance(evidence, list) or not evidence:
        errors.append("/evidence: nonempty array required")
    else:
        for index, item in enumerate(evidence):
            path = f"/evidence/{index}"
            if not _object(item):
                errors.append(f"{path}: object required")
                continue
            evidence_id = item.get("id")
            if not isinstance(evidence_id, str) or not evidence_id:
                errors.append(f"{path}/id: nonempty string required")
            elif evidence_id in evidence_ids:
                errors.append(f"{path}/id: duplicate evidence identity")
            else:
                evidence_ids.add(evidence_id)
                evidence_by_id[evidence_id] = item
            if item.get("kind") not in EVIDENCE_KINDS:
                errors.append(f"{path}/kind: unsupported evidence kind")
            locator = item.get("locator")
            if not isinstance(locator, str) or not locator:
                errors.append(f"{path}/locator: nonempty locator required")
            elif item.get("kind") == "CONTENT_HASH" and not SHA256_RE.fullmatch(locator):
                errors.append(f"{path}/locator: malformed sha256 content hash")
            if item.get("trust") not in VERIFICATION:
                errors.append(f"{path}/trust: unsupported trust state")

    measurements = receipt.get("measurements")
    measurement_ids: set[str] = set()
    measurement_by_id: dict[str, dict[str, Any]] = {}
    if not isinstance(measurements, list) or not measurements:
        errors.append("/measurements: nonempty array required")
        return sorted(errors)

    for index, item in enumerate(measurements):
        path = f"/measurements/{index}"
        if not _object(item):
            errors.append(f"{path}: object required")
            continue
        required_measurement = {"id", "baseline", "result", "delta", "unit", "direction", "class", "evidence_refs", "source_verification", "operator_display", "aggregation", "derivation", "limitations"}
        for field in sorted(required_measurement - set(item)):
            errors.append(f"{path}/{field}: required field missing")
        measurement_id = item.get("id")
        if not isinstance(measurement_id, str) or not ID_RE.fullmatch(measurement_id):
            errors.append(f"{path}/id: lowercase measurement identity required")
        elif measurement_id in measurement_ids:
            errors.append(f"{path}/id: duplicate measurement identity")
        else:
            measurement_ids.add(measurement_id)
            measurement_by_id[measurement_id] = item
        unit = item.get("unit")
        measurement_class = item.get("class")
        if unit not in UNITS:
            errors.append(f"{path}/unit: unsupported unit")
        if measurement_class not in CLASSES:
            errors.append(f"{path}/class: unsupported measurement class")
        if item.get("direction") not in DIRECTIONS:
            errors.append(f"{path}/direction: unsupported value direction")
        if item.get("source_verification") not in VERIFICATION:
            errors.append(f"{path}/source_verification: unsupported verification state")
        if not isinstance(item.get("operator_display"), bool):
            errors.append(f"{path}/operator_display: boolean required")

        for field in ("baseline", "result", "delta"):
            value = item.get(field)
            if isinstance(value, float) and not math.isfinite(value):
                errors.append(f"{path}/{field}: finite JSON value required")
        baseline, result, delta = item.get("baseline"), item.get("result"), item.get("delta")
        if _finite_number(baseline) and _finite_number(result):
            if not _finite_number(delta) or not math.isclose(delta, result - baseline, rel_tol=0, abs_tol=1e-12):
                errors.append(f"{path}/delta: must equal result minus baseline")
        elif delta is not None:
            errors.append(f"{path}/delta: must be null without numeric baseline and result")
        if unit in {"byte", "event", "count", "token", "millisecond"}:
            for field in ("baseline", "result"):
                value = item.get(field)
                if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 0):
                    errors.append(f"{path}/{field}: nonnegative integer required for {unit}")
        if unit == "boolean" and any(value is not None and not isinstance(value, bool) for value in (baseline, result)):
            errors.append(f"{path}: boolean unit requires boolean baseline/result")
        if unit == "state" and any(value is not None and not isinstance(value, str) for value in (baseline, result)):
            errors.append(f"{path}: state unit requires string baseline/result")

        refs = item.get("evidence_refs")
        if not isinstance(refs, list) or not refs:
            errors.append(f"{path}/evidence_refs: nonempty array required")
        else:
            for ref in refs:
                if ref not in evidence_ids:
                    errors.append(f"{path}/evidence_refs: unresolved evidence reference {ref!r}")

        derivation = item.get("derivation")
        if measurement_class in {"ESTIMATED", "MODELED"}:
            if not _object(derivation) or not derivation.get("method") or not derivation.get("assumptions"):
                errors.append(f"{path}/derivation: {measurement_class} requires method and assumptions")
        if measurement_class == "EXPERIMENTAL":
            if not _object(derivation) or not derivation.get("experiment_id") or derivation.get("comparability") != "CONTROLLED":
                errors.append(f"{path}/derivation: EXPERIMENTAL requires controlled experiment identity")
        if measurement_class in {"EXACT", "OBSERVED"} and derivation not in (None, {}):
            assumptions = derivation.get("assumptions", []) if _object(derivation) else []
            if assumptions:
                errors.append(f"{path}/derivation: {measurement_class} cannot depend on assumptions")
        if measurement_class == "EXACT" and item.get("source_verification") != "VERIFIED":
            errors.append(f"{path}/source_verification: EXACT requires VERIFIED evidence")

        aggregation = item.get("aggregation")
        safe = _object(aggregation) and aggregation.get("safe") is True
        method = aggregation.get("method") if _object(aggregation) else None
        if not _object(aggregation) or not isinstance(aggregation.get("safe"), bool) or method not in {None, "SUM"}:
            errors.append(f"{path}/aggregation: safe boolean and SUM or null method required")
        if safe and (measurement_class not in {"EXACT", "OBSERVED"} or method != "SUM" or unit in {"ratio", "percent", "boolean", "state"}):
            errors.append(f"{path}/aggregation: measurement is not safely summable")
        if not safe and method is not None:
            errors.append(f"{path}/aggregation: unsafe measurement must use null method")

        lowered_id = measurement_id or ""
        if ("failure_prevented" in lowered_id or "failures_prevented" in lowered_id) and measurement_class in {"EXACT", "OBSERVED"}:
            errors.append(f"{path}/class: prevented-failure claims require MODELED or EXPERIMENTAL evidence")

    for index, item in enumerate(measurements):
        if not _object(item) or item.get("unit") != "usd" or item.get("class") not in {"ESTIMATED", "MODELED"}:
            continue
        inputs = item.get("derivation", {}).get("input_measurement_ids", []) if _object(item.get("derivation")) else []
        input_units = {measurement_by_id.get(identity, {}).get("unit") for identity in inputs}
        if "token" not in input_units:
            errors.append(f"/measurements/{index}/derivation: monetary estimate requires a token measurement input")

    if not isinstance(receipt.get("limitations"), list):
        errors.append("/limitations: array required")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    try:
        value = json.loads(args.receipt.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}")
        return 1
    errors = validate(value)
    if errors:
        print("FAIL: invalid value receipt")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"PASS: {SCHEMA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
