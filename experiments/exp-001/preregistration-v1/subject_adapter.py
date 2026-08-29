#!/usr/bin/env python3
"""Bounded EXP-001 OpenAI Responses subject adapter with no automatic retry."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import ssl
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
EXP_ROOT = ROOT.parent


class SubjectAdapterError(RuntimeError):
    """A fail-closed subject adapter error."""


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


def object_identity(value: dict[str, Any]) -> str:
    semantic = dict(value)
    semantic.pop("identity", None)
    return sha256_bytes(canonical_bytes(semantic))


def load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SubjectAdapterError(f"{path}: invalid or unavailable JSON") from error
    if not isinstance(value, dict):
        raise SubjectAdapterError(f"{path}: top-level object required")
    return value


def verify_identity(value: dict[str, Any], label: str) -> None:
    if value.get("identity") != object_identity(value):
        raise SubjectAdapterError(f"{label} identity mismatch")


def verify_environment(config: dict[str, Any]) -> dict[str, Any]:
    expected = config["subject_environment"]
    observed = {
        "machine": platform.machine(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "ssl": ssl.OPENSSL_VERSION,
    }
    for field in ("machine", "python", "python_implementation"):
        if observed[field] != expected[field]:
            raise SubjectAdapterError(
                f"subject environment {field} expected {expected[field]!r}, "
                f"found {observed[field]!r}"
            )
    return observed


def response_tools() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "name": "read_file",
            "description": "Read the current UTF-8 contents of task.py.",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "const": "task.py"}},
                "required": ["path"],
                "additionalProperties": False,
            },
        },
        {
            "type": "function",
            "name": "write_file",
            "description": "Replace task.py with the supplied complete UTF-8 content.",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "const": "task.py"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
                "additionalProperties": False,
            },
        },
    ]


def subject_input(prompt: str, source: str, evidence: str) -> str:
    return (
        "Repair task.py. You may read or replace only task.py through the provided "
        "tools. Hidden evaluation runs after you stop. Do not request network access, "
        "additional agents, retries, or hidden evaluator material.\n\n"
        "TASK SPECIFICATION\n" + prompt.rstrip() + "\n\n"
        "INITIAL task.py\n```python\n" + source.rstrip() + "\n```\n\n"
        "INITIAL TOOL EVIDENCE\n" + evidence.rstrip() + "\n"
    )


def request_body(
    config: dict[str, Any],
    initial_input: str,
    subject_label: str,
) -> dict[str, Any]:
    model = config["model_provider_configuration"]
    limits = config["subject_limits"]
    return {
        "model": model["model_id"],
        "input": [
            {
                "role": "user",
                "content": [{"type": "input_text", "text": initial_input}],
            }
        ],
        "reasoning": {
            "effort": model["reasoning_effort"],
            "context": model["reasoning_context"],
        },
        "service_tier": model["service_tier"],
        "store": False,
        "stream": False,
        "parallel_tool_calls": False,
        "max_output_tokens": limits["max_output_tokens_per_response"],
        "tools": response_tools(),
        "tool_choice": "auto",
        "truncation": "disabled",
        "metadata": {
            "experiment_id": "EXP-001",
            "subject_label": subject_label,
        },
    }


def call_openai(
    endpoint: str, api_key: str, body: dict[str, Any], timeout: int
) -> dict[str, Any]:
    request = urllib.request.Request(
        endpoint,
        data=canonical_bytes(body),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = response.read()
    except (urllib.error.URLError, TimeoutError) as error:
        raise SubjectAdapterError(
            "provider request failed; no retry was attempted"
        ) from error
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as error:
        raise SubjectAdapterError(
            "provider returned invalid JSON; no retry was attempted"
        ) from error
    if not isinstance(value, dict):
        raise SubjectAdapterError("provider response must be an object")
    return value


def execute_tool(
    workspace: Path,
    call: dict[str, Any],
    max_file_bytes: int,
) -> dict[str, Any]:
    name = call.get("name")
    call_id = call.get("call_id")
    if not isinstance(call_id, str) or not call_id:
        raise SubjectAdapterError("function call lacks call_id")
    try:
        arguments = json.loads(call.get("arguments", ""))
    except json.JSONDecodeError as error:
        raise SubjectAdapterError("function call arguments are invalid JSON") from error
    if not isinstance(arguments, dict) or arguments.get("path") != "task.py":
        raise SubjectAdapterError("function call attempted an unauthorized path")
    target = workspace / "task.py"
    if name == "read_file":
        output = {"content": target.read_text(encoding="utf-8")}
    elif name == "write_file":
        content = arguments.get("content")
        if not isinstance(content, str):
            raise SubjectAdapterError("write_file content must be a string")
        encoded = content.encode("utf-8")
        if len(encoded) > max_file_bytes:
            raise SubjectAdapterError("write_file exceeded the configured byte ceiling")
        target.write_bytes(encoded)
        output = {"bytes_written": len(encoded), "sha256": sha256_bytes(encoded)}
    else:
        raise SubjectAdapterError(f"unauthorized function tool {name!r}")
    return {
        "type": "function_call_output",
        "call_id": call_id,
        "output": json.dumps(output, ensure_ascii=True, sort_keys=True),
    }


def run_subject(
    *,
    config: dict[str, Any],
    workspace: Path,
    prompt: str,
    evidence: str,
    subject_label: str,
    transport: Callable[[dict[str, Any], int], dict[str, Any]],
) -> dict[str, Any]:
    source = (workspace / "task.py").read_text(encoding="utf-8")
    body = request_body(
        config,
        subject_input(prompt, source, evidence),
        subject_label,
    )
    limits = config["subject_limits"]
    started = time.monotonic()
    responses: list[dict[str, Any]] = []
    tool_call_count = 0
    for api_call in range(1, limits["max_api_calls"] + 1):
        if time.monotonic() - started >= limits["wall_clock_seconds"]:
            raise SubjectAdapterError("subject wall-clock budget exhausted")
        if len(canonical_bytes(body)) > limits["max_request_body_bytes"]:
            raise SubjectAdapterError(
                "provider request exceeded the configured byte ceiling"
            )
        response = transport(body, limits["request_timeout_seconds"])
        responses.append(response)
        if response.get("status") != "completed":
            raise SubjectAdapterError("provider response did not complete")
        model = config["model_provider_configuration"]
        if response.get("model") != model["model_id"]:
            raise SubjectAdapterError("provider response model identity drifted")
        if not isinstance(response.get("usage"), dict):
            raise SubjectAdapterError(
                "provider response omitted required usage telemetry"
            )
        output = response.get("output")
        if not isinstance(output, list):
            raise SubjectAdapterError("provider response output must be an array")
        calls = [
            item
            for item in output
            if isinstance(item, dict) and item.get("type") == "function_call"
        ]
        body["input"].extend(output)
        if not calls:
            return {
                "api_call_count": api_call,
                "final_task_sha256": sha256_bytes((workspace / "task.py").read_bytes()),
                "provider_responses": responses,
                "subject_label": subject_label,
                "tool_call_count": tool_call_count,
            }
        tool_call_count += len(calls)
        if tool_call_count > limits["max_function_calls"]:
            raise SubjectAdapterError("subject function-call budget exhausted")
        body["input"].extend(
            execute_tool(workspace, call, limits["max_writable_file_bytes"])
            for call in calls
        )
    raise SubjectAdapterError("subject API-call budget exhausted")


def verify_preregistration() -> dict[str, Any]:
    config = load_object(ROOT / "subject-config.json")
    preregistration = load_object(ROOT / "preregistration.json")
    index = load_object(ROOT / "allocation-index.json")
    verify_identity(config, "subject configuration")
    verify_identity(preregistration, "preregistration")
    verify_identity(index, "allocation index")
    artifacts = preregistration["artifacts"]
    for label, artifact in artifacts.items():
        path = ROOT / artifact["path"]
        if not path.is_file() or sha256_bytes(path.read_bytes()) != artifact["sha256"]:
            raise SubjectAdapterError(f"preregistration artifact {label} hash mismatch")
    if preregistration["subject_configuration_id"] != config["identity"]:
        raise SubjectAdapterError("subject configuration identity is not bound")
    if index["configuration_id"] != config["identity"]:
        raise SubjectAdapterError("allocation configuration identity is not bound")
    return {
        "allocation_index_identity": index["identity"],
        "environment": verify_environment(config),
        "preregistration_identity": preregistration["identity"],
        "provider_model_runs": 0,
        "subject_configuration_id": config["identity"],
        "valid": True,
    }


def verify_authorization(
    path: Path,
    preregistration_identity: str,
    maximum_spend_usd: float,
    subject_label: str,
) -> None:
    authorization = load_object(path)
    required = {
        "experiment_id": "EXP-001",
        "preregistration_identity": preregistration_identity,
        "provider_run_authorized": True,
        "max_provider_runs": 1,
        "subject_label": subject_label,
    }
    if any(authorization.get(key) != value for key, value in required.items()):
        raise SubjectAdapterError(
            "authorization does not permit exactly one bound provider run"
        )
    budget = authorization.get("maximum_spend_usd")
    if not isinstance(budget, (int, float)) or budget < maximum_spend_usd:
        raise SubjectAdapterError(
            "authorization maximum_spend_usd is below the conservative per-run ceiling"
        )


def self_test(config: dict[str, Any], workspace: Path) -> dict[str, Any]:
    scripted = iter(
        (
            {
                "status": "completed",
                "model": config["model_provider_configuration"]["model_id"],
                "usage": {"input_tokens": 1, "output_tokens": 1},
                "output": [
                    {
                        "type": "function_call",
                        "name": "write_file",
                        "call_id": "fake-call-1",
                        "arguments": json.dumps(
                            {"path": "task.py", "content": "VALUE = 2\n"}
                        ),
                    }
                ],
            },
            {
                "status": "completed",
                "model": config["model_provider_configuration"]["model_id"],
                "usage": {"input_tokens": 1, "output_tokens": 1},
                "output": [{"type": "message", "role": "assistant", "content": []}],
            },
        )
    )

    def fake_transport(body: dict[str, Any], timeout: int) -> dict[str, Any]:
        if timeout != config["subject_limits"]["request_timeout_seconds"]:
            raise SubjectAdapterError("fake transport observed timeout drift")
        if body.get("model") != config["model_provider_configuration"]["model_id"]:
            raise SubjectAdapterError("fake transport observed model drift")
        return next(scripted)

    result = run_subject(
        config=config,
        workspace=workspace,
        prompt="Set VALUE to 2.",
        evidence="The current value is incorrect.",
        subject_label="EXP001-FAKE-SUBJECT",
        transport=fake_transport,
    )
    if (workspace / "task.py").read_text(encoding="utf-8") != "VALUE = 2\n":
        raise SubjectAdapterError(
            "provider-free adapter self-test did not apply the write"
        )
    result.pop("provider_responses")
    return {**result, "provider_model_runs": 0, "valid": True}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("verify")
    test = subparsers.add_parser("self-test")
    test.add_argument("--workspace", type=Path, required=True)
    execute = subparsers.add_parser("execute")
    execute.add_argument("--workspace", type=Path, required=True)
    execute.add_argument("--prompt", type=Path, required=True)
    execute.add_argument("--evidence", type=Path, required=True)
    execute.add_argument("--authorization", type=Path, required=True)
    execute.add_argument("--subject-label", required=True)
    execute.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        verification = verify_preregistration()
        config = load_object(ROOT / "subject-config.json")
        if args.command == "verify":
            result = verification
        elif args.command == "self-test":
            result = self_test(config, args.workspace)
        else:
            index = load_object(ROOT / "allocation-index.json")
            labels = {
                item.get("subject_label")
                for item in index.get("entries", [])
                if isinstance(item, dict)
            }
            if args.subject_label not in labels:
                raise SubjectAdapterError(
                    "subject label is not in the blinded allocation index"
                )
            verify_authorization(
                args.authorization,
                verification["preregistration_identity"],
                config["subject_limits"]["maximum_spend_usd_per_subject"],
                args.subject_label,
            )
            api_key = os.environ.get("OPENAI_API_KEY", "")
            if not api_key:
                raise SubjectAdapterError("OPENAI_API_KEY is unavailable")
            endpoint = config["model_provider_configuration"]["endpoint"]

            def transport(body: dict[str, Any], timeout: int) -> dict[str, Any]:
                return call_openai(endpoint, api_key, body, timeout)

            result = run_subject(
                config=config,
                workspace=args.workspace,
                prompt=args.prompt.read_text(encoding="utf-8"),
                evidence=args.evidence.read_text(encoding="utf-8"),
                subject_label=args.subject_label,
                transport=transport,
            )
            args.output.write_bytes(canonical_bytes(result))
            result = {
                "api_call_count": result["api_call_count"],
                "final_task_sha256": result["final_task_sha256"],
                "provider_result_path": str(args.output),
                "subject_label": result["subject_label"],
                "tool_call_count": result["tool_call_count"],
            }
        sys.stdout.buffer.write(canonical_bytes(result))
        return 0
    except (OSError, SubjectAdapterError, StopIteration) as error:
        sys.stderr.buffer.write(
            canonical_bytes(
                {
                    "code": "SUBJECT_ADAPTER_FAILED",
                    "message": str(error),
                }
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
