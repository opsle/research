#!/usr/bin/env python3
"""Instantiate and verify EXP-001's committed, subject-blinded allocation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

PROTOCOL = "opsle.exp001.instantiated-allocation/v1"
INDEX_PROTOCOL = "opsle.exp001.blinded-allocation-index/v1"
SEAL_CONTEXT = b"opsle.exp001.allocation-seal/v1\0"


class AllocationError(RuntimeError):
    """A fail-closed allocation error."""


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
        raise AllocationError(f"{path}: invalid or unavailable JSON") from error
    if not isinstance(value, dict):
        raise AllocationError(f"{path}: top-level object required")
    return value


def load_seed(path: Path) -> bytes:
    try:
        encoded = path.read_text(encoding="ascii").strip()
        seed = bytes.fromhex(encoded)
    except (OSError, UnicodeError, ValueError) as error:
        raise AllocationError(
            "seed file must contain exactly 32 random bytes as hex"
        ) from error
    if len(seed) != 32 or len(encoded) != 64:
        raise AllocationError("seed file must contain exactly 32 random bytes as hex")
    return seed


def sort_digest(
    seed: bytes,
    task_id: str,
    configuration_id: str,
    repetition: int,
    arm_id: str,
) -> bytes:
    frame = b"\0".join(
        (
            seed,
            task_id.encode(),
            configuration_id.encode(),
            str(repetition).encode(),
            arm_id.encode(),
        )
    )
    return hashlib.sha256(frame).digest()


def build_allocation(
    *,
    seed: bytes,
    configuration_id: str,
    task_ids: list[str],
    arm_ids: list[str],
    repetitions: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if repetitions <= 0:
        raise AllocationError("repetitions must be positive")
    if len(task_ids) != len(set(task_ids)) or not task_ids:
        raise AllocationError("task identities must be nonempty and unique")
    if len(arm_ids) != len(set(arm_ids)) or not arm_ids:
        raise AllocationError("arm identities must be nonempty and unique")
    seed_commitment = sha256_bytes(seed)
    index_entries: list[dict[str, Any]] = []
    mapping_entries: list[dict[str, Any]] = []
    for task_id in sorted(task_ids):
        for repetition in range(1, repetitions + 1):
            block_frame = b"\0".join(
                (
                    seed,
                    b"block",
                    task_id.encode(),
                    configuration_id.encode(),
                    str(repetition).encode(),
                )
            )
            block_id = hashlib.sha256(block_frame).hexdigest()[:20]
            ordered_arms = sorted(
                arm_ids,
                key=lambda arm_id: (
                    sort_digest(
                        seed,
                        task_id,
                        configuration_id,
                        repetition,
                        arm_id,
                    ),
                    arm_id,
                ),
            )
            for position, arm_id in enumerate(ordered_arms, 1):
                label = f"EXP001-BLOCK-{block_id}-{position}"
                public = {
                    "block_id": block_id,
                    "configuration_id": configuration_id,
                    "position": position,
                    "repetition": repetition,
                    "subject_label": label,
                    "task_id": task_id,
                }
                index_entries.append(public)
                mapping_entries.append({**public, "arm_id": arm_id})

    mapping: dict[str, Any] = {
        "protocol_version": PROTOCOL,
        "experiment_id": "EXP-001",
        "configuration_id": configuration_id,
        "repetition_count": repetitions,
        "seed_commitment": seed_commitment,
        "ordering_algorithm": "SHA256_SORT_V1",
        "entries": mapping_entries,
    }
    mapping["identity"] = object_identity(mapping)
    mapping_bytes = canonical_bytes(mapping)
    index: dict[str, Any] = {
        "protocol_version": INDEX_PROTOCOL,
        "experiment_id": "EXP-001",
        "status": "INSTANTIATED_MAPPING_SEALED",
        "configuration_id": configuration_id,
        "repetition_count": repetitions,
        "block_count": len(task_ids) * repetitions,
        "subject_count": len(mapping_entries),
        "seed_commitment": seed_commitment,
        "mapping_plaintext_sha256": sha256_bytes(mapping_bytes),
        "entries": index_entries,
    }
    index["identity"] = object_identity(index)
    return index, mapping


def seal_mapping(seed: bytes, mapping: dict[str, Any], destination: Path) -> None:
    seal_key = hashlib.sha256(SEAL_CONTEXT + seed).hexdigest()
    environment = {**os.environ, "EXP001_SEAL_KEY": seal_key}
    with tempfile.NamedTemporaryFile(prefix="exp001-map-", mode="wb") as handle:
        handle.write(canonical_bytes(mapping))
        handle.flush()
        result = subprocess.run(
            [
                "openssl",
                "enc",
                "-aes-256-cbc",
                "-pbkdf2",
                "-iter",
                "600000",
                "-md",
                "sha256",
                "-salt",
                "-in",
                handle.name,
                "-out",
                str(destination),
                "-pass",
                "env:EXP001_SEAL_KEY",
            ],
            env=environment,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=False,
        )
    if result.returncode != 0:
        raise AllocationError("OpenSSL failed to seal the allocation mapping")


def unseal_mapping(seed: bytes, source: Path) -> dict[str, Any]:
    seal_key = hashlib.sha256(SEAL_CONTEXT + seed).hexdigest()
    environment = {**os.environ, "EXP001_SEAL_KEY": seal_key}
    result = subprocess.run(
        [
            "openssl",
            "enc",
            "-d",
            "-aes-256-cbc",
            "-pbkdf2",
            "-iter",
            "600000",
            "-md",
            "sha256",
            "-in",
            str(source),
            "-pass",
            "env:EXP001_SEAL_KEY",
        ],
        env=environment,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise AllocationError("seed cannot unseal the allocation mapping")
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise AllocationError("unsealed mapping is not valid JSON") from error
    if not isinstance(value, dict):
        raise AllocationError("unsealed mapping must be an object")
    return value


def validate_public(index: dict[str, Any], sealed: Path) -> dict[str, Any]:
    if index.get("protocol_version") != INDEX_PROTOCOL:
        raise AllocationError("allocation index protocol drifted")
    if index.get("identity") != object_identity(index):
        raise AllocationError("allocation index identity mismatch")
    entries = index.get("entries")
    if not isinstance(entries, list) or len(entries) != index.get("subject_count"):
        raise AllocationError("allocation index subject count mismatch")
    labels = [
        entry.get("subject_label") for entry in entries if isinstance(entry, dict)
    ]
    if len(labels) != len(entries) or len(labels) != len(set(labels)):
        raise AllocationError("allocation index labels must be unique")
    if not sealed.is_file() or sealed.stat().st_size == 0:
        raise AllocationError("sealed mapping artifact is missing or empty")
    return {
        "allocation_index_identity": index["identity"],
        "block_count": index["block_count"],
        "sealed_mapping_bytes": sealed.stat().st_size,
        "sealed_mapping_sha256": sha256_bytes(sealed.read_bytes()),
        "subject_count": len(entries),
        "valid": True,
    }


def validate_secret(
    *,
    seed: bytes,
    index: dict[str, Any],
    sealed: Path,
    task_ids: list[str],
    arm_ids: list[str],
) -> dict[str, Any]:
    public = validate_public(index, sealed)
    if index.get("seed_commitment") != sha256_bytes(seed):
        raise AllocationError("seed commitment mismatch")
    mapping = unseal_mapping(seed, sealed)
    if mapping.get("identity") != object_identity(mapping):
        raise AllocationError("allocation mapping identity mismatch")
    if sha256_bytes(canonical_bytes(mapping)) != index.get("mapping_plaintext_sha256"):
        raise AllocationError("sealed mapping plaintext commitment mismatch")
    rebuilt_index, rebuilt_mapping = build_allocation(
        seed=seed,
        configuration_id=index["configuration_id"],
        task_ids=task_ids,
        arm_ids=arm_ids,
        repetitions=index["repetition_count"],
    )
    if rebuilt_index != index or rebuilt_mapping != mapping:
        raise AllocationError(
            "sealed mapping does not match frozen allocation algorithm"
        )
    counts: dict[str, int] = {arm_id: 0 for arm_id in arm_ids}
    for entry in mapping["entries"]:
        counts[entry["arm_id"]] += 1
    if len(set(counts.values())) != 1:
        raise AllocationError("allocation arms are not balanced")
    return {
        **public,
        "arm_counts": counts,
        "mapping_identity": mapping["identity"],
        "mapping_verified_with_seed": True,
        "seed_commitment_verified": True,
    }


def corpus_and_arms(corpus_path: Path, arms_path: Path) -> tuple[list[str], list[str]]:
    corpus = load_object(corpus_path)
    arms = load_object(arms_path)
    task_ids = [
        item.get("id") for item in corpus.get("tasks", []) if isinstance(item, dict)
    ]
    arm_ids = [
        item.get("id") for item in arms.get("arms", []) if isinstance(item, dict)
    ]
    if not all(isinstance(item, str) and item for item in task_ids + arm_ids):
        raise AllocationError("corpus or arm manifest contains an invalid identity")
    return task_ids, arm_ids


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    instantiate = subparsers.add_parser("instantiate")
    instantiate.add_argument("--seed-file", type=Path, required=True)
    instantiate.add_argument("--configuration-id", required=True)
    instantiate.add_argument("--repetitions", type=int, required=True)
    instantiate.add_argument("--corpus", type=Path, required=True)
    instantiate.add_argument("--arms", type=Path, required=True)
    instantiate.add_argument("--index", type=Path, required=True)
    instantiate.add_argument("--sealed", type=Path, required=True)
    verify = subparsers.add_parser("verify")
    verify.add_argument("--index", type=Path, required=True)
    verify.add_argument("--sealed", type=Path, required=True)
    verify.add_argument("--seed-file", type=Path)
    verify.add_argument("--corpus", type=Path)
    verify.add_argument("--arms", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "instantiate":
            seed = load_seed(args.seed_file)
            task_ids, arm_ids = corpus_and_arms(args.corpus, args.arms)
            index, mapping = build_allocation(
                seed=seed,
                configuration_id=args.configuration_id,
                task_ids=task_ids,
                arm_ids=arm_ids,
                repetitions=args.repetitions,
            )
            args.index.write_bytes(canonical_bytes(index))
            seal_mapping(seed, mapping, args.sealed)
            result = validate_secret(
                seed=seed,
                index=index,
                sealed=args.sealed,
                task_ids=task_ids,
                arm_ids=arm_ids,
            )
        else:
            index = load_object(args.index)
            if args.seed_file is None:
                result = validate_public(index, args.sealed)
            else:
                if args.corpus is None or args.arms is None:
                    raise AllocationError(
                        "secret verification requires corpus and arms"
                    )
                task_ids, arm_ids = corpus_and_arms(args.corpus, args.arms)
                result = validate_secret(
                    seed=load_seed(args.seed_file),
                    index=index,
                    sealed=args.sealed,
                    task_ids=task_ids,
                    arm_ids=arm_ids,
                )
        sys.stdout.buffer.write(canonical_bytes(result))
        return 0
    except AllocationError as error:
        sys.stderr.buffer.write(
            canonical_bytes(
                {
                    "code": "ALLOCATION_VALIDATION_FAILED",
                    "message": str(error),
                }
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
