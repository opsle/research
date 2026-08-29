#!/usr/bin/env python3
"""Deterministic evaluator-only correctness oracle for the EXP-001 corpus."""

from __future__ import annotations

import copy
import importlib.util
import json
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable


def _slugify(value: Any) -> str:
    if not isinstance(value, str):
        raise TypeError
    return "-".join(re.findall(r"[a-z0-9]+", value.lower(), flags=re.ASCII))


def _chunked(items: list[Any], size: Any) -> list[list[Any]]:
    if type(size) is not int or size <= 0:
        raise ValueError
    return [items[index:index + size] for index in range(0, len(items), size)]


def _merge_ranges(ranges: list[Any]) -> list[list[int]]:
    normalized = []
    for item in ranges:
        if (not isinstance(item, (list, tuple)) or len(item) != 2
                or any(type(value) is not int for value in item)
                or item[0] > item[1]):
            raise ValueError
        normalized.append([item[0], item[1]])
    normalized.sort()
    merged: list[list[int]] = []
    for start, end in normalized:
        if merged and start <= merged[-1][1] + 1:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged


def _merge_headers(pairs: list[Any]) -> list[list[str]]:
    result: list[list[str]] = []
    positions: dict[str, int] = {}
    for pair in pairs:
        if (not isinstance(pair, (list, tuple)) or len(pair) != 2
                or not isinstance(pair[0], str) or not pair[0]
                or not isinstance(pair[1], str)):
            raise ValueError
        key = pair[0].lower()
        if key in positions:
            result[positions[key]][1] = pair[1]
        else:
            positions[key] = len(result)
            result.append([pair[0], pair[1]])
    return result


def _backoff_delay(attempt: Any, base_ms: Any, cap_ms: Any) -> int:
    if (any(type(value) is not int for value in (attempt, base_ms, cap_ms))
            or attempt < 0 or base_ms <= 0 or cap_ms <= 0):
        raise ValueError
    return min(cap_ms, base_ms * 2 ** attempt)


def _parse_duration(value: Any) -> int:
    if not isinstance(value, str):
        raise ValueError
    match = re.fullmatch(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(ms|s|m|h)", value)
    if match is None:
        raise ValueError
    try:
        number = Decimal(value[:-len(match.group(1))])
    except InvalidOperation as error:
        raise ValueError from error
    factor = {"ms": 1, "s": 1000, "m": 60000, "h": 3600000}[match.group(1)]
    milliseconds = number * factor
    if milliseconds != milliseconds.to_integral_value():
        raise ValueError
    return int(milliseconds)


def _normal_cases(task_id: str) -> list[tuple[str, list[Any], Callable[..., Any]]]:
    if task_id == "slugify":
        values = [
            "", "alpha", "Alpha Beta", "  spaced  ", "a--b", "a___b",
            "a/b/c", "ONE.two THREE", "123", "A1 B2", "---", "café",
            "naïve test", "tabs\tand\nlines", "x+y=z", "already-slugged",
            "CAPS", "0 leading", "trailing 0", "emoji 😀 split", "a..b",
            "MiXeD_123", "中文", "aéb", " many   separators ", "v1.2.3",
            "under_score", "dash—dash", "!a!", "9lives",
        ]
        return [(f"value-{index:02d}", [value], _slugify) for index, value in enumerate(values)]
    if task_id == "chunked":
        cases = []
        for length in range(17):
            for size in (1, 2, 3, 5, 8):
                cases.append((f"length-{length:02d}-size-{size}", [list(range(length)), size], _chunked))
        return cases
    if task_id == "merge-ranges":
        values = [
            [], [[1, 1]], [[1, 2], [3, 4]], [[1, 2], [4, 5]],
            [[5, 8], [1, 3], [3, 6]], [[0, 0], [2, 2], [1, 1]],
            [[-5, -3], [-2, 0]], [[10, 20], [11, 12]],
            [[1, 10], [2, 3], [4, 5]], [[8, 9], [1, 2], [4, 7]],
            [[1, 2], [2, 2]], [[1, 1], [1, 1]], [[-1, 1], [3, 3]],
            [[100, 200], [0, 99]], [[0, 5], [6, 6], [8, 10]],
            [[3, 4], [1, 1], [2, 2]], [[0, 0], [0, 2], [2, 4]],
            [[-10, -8], [-6, -4], [-7, -7]], [[5, 5], [7, 7], [6, 6]],
            [[1, 100], [-50, -1], [0, 0]],
        ]
        return [(f"ranges-{index:02d}", [value], _merge_ranges) for index, value in enumerate(values)]
    if task_id == "merge-headers":
        values = [
            [], [["A", "1"]], [["A", "1"], ["B", "2"]],
            [["A", "1"], ["a", "2"]], [["Content-Type", "a"], ["content-type", "b"]],
            [["x", "1"], ["Y", "2"], ["X", "3"]],
            [["a", "1"], ["b", "2"], ["A", "3"], ["B", "4"]],
            [["Z", ""], ["z", "last"]], [["1", "one"], ["1", "two"]],
            [["Host", "a"], ["Accept", "b"], ["HOST", "c"]],
            [["a-b", "1"], ["A-B", "2"]], [["Ü", "1"], ["ü", "2"]],
            [["x", "1"], ["X", "2"], ["x", "3"]],
            [["First", "1"], ["Second", "2"], ["third", "3"]],
            [["Case", "1"], ["CASE", "2"], ["case", "3"], ["Other", "4"]],
            [["a", "v"], ["B", "w"], ["c", "x"], ["b", "y"]],
            [["0", "zero"]], [["x_y", "1"], ["X_Y", "2"]],
            [["one", "1"], ["two", "2"], ["ONE", "3"]],
            [["a", "1"], ["b", "2"], ["c", "3"], ["A", "4"]],
        ]
        return [(f"headers-{index:02d}", [value], _merge_headers) for index, value in enumerate(values)]
    if task_id == "backoff-delay":
        return [
            (f"attempt-{attempt:02d}-base-{base}-cap-{cap}", [attempt, base, cap], _backoff_delay)
            for attempt in range(11)
            for base, cap in ((1, 100), (25, 1000), (100, 10000))
        ]
    if task_id == "parse-duration":
        values = [
            "0ms", "1ms", "999ms", "1000ms", "0s", "1s", "1.5s",
            "0.001s", "2.25s", "60s", "0m", "1m", "1.5m", "2.25m",
            "60m", "0h", "1h", "1.5h", "24h", "100h", "10.000ms",
            "0.5s", "0.0005m", "12.345s", "123456ms", "9.001s",
            "3.333m", "7.25h", "42m", "3600s",
        ]
        return [(f"duration-{index:02d}", [value], _parse_duration) for index, value in enumerate(values)]
    raise KeyError(task_id)


def _error_cases(task_id: str) -> list[tuple[str, list[Any], type[BaseException]]]:
    return {
        "slugify": [("non-string-null", [None], TypeError), ("non-string-int", [1], TypeError), ("non-string-list", [[]], TypeError)],
        "chunked": [("zero", [[1], 0], ValueError), ("negative", [[1], -1], ValueError), ("bool", [[1], True], ValueError), ("float", [[1], 1.5], ValueError), ("string", [[1], "1"], ValueError)],
        "merge-ranges": [("reversed", [[[2, 1]]], ValueError), ("short", [[[1]]], ValueError), ("long", [[[1, 2, 3]]], ValueError), ("bool", [[[False, 1]]], ValueError), ("string", [[['1', 2]]], ValueError)],
        "merge-headers": [("empty-name", [[['', 'v']]], ValueError), ("non-string-name", [[[1, 'v']]], ValueError), ("non-string-value", [[['a', 1]]], ValueError), ("short", [[['a']]], ValueError), ("scalar", [['bad']], ValueError)],
        "backoff-delay": [("negative", [-1, 1, 10], ValueError), ("zero-base", [0, 0, 10], ValueError), ("zero-cap", [0, 1, 0], ValueError), ("bool", [True, 1, 10], ValueError), ("float", [1, 1.0, 10], ValueError)],
        "parse-duration": [(name, [value], ValueError) for name, value in [
            ("space", " 1s"), ("suffix-space", "1s "), ("sign", "+1s"),
            ("negative", "-1s"), ("exponent", "1e3ms"), ("missing-unit", "1"),
            ("unknown-unit", "1d"), ("fractional-ms", "0.5ms"),
            ("leading-zero", "01s"), ("empty", ""), ("non-string", None),
        ]],
    }[task_id]


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _load_module(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("exp001_candidate", path)
    if spec is None or spec.loader is None:
        raise ImportError
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: oracle.py TASK_ID CANDIDATE", file=sys.stderr)
        return 2
    task_id, candidate = sys.argv[1], Path(sys.argv[2])
    function_name = task_id.replace("-", "_")
    print("TAP version 13")
    try:
        function = getattr(_load_module(candidate), function_name)
    except Exception as error:  # Candidate import is part of the correctness gate.
        print(f"not ok 1 - {task_id} :: candidate import")
        print("  operator: imports")
        print("  expected: callable export")
        print(f"  actual: {_canonical({'exception': type(error).__name__})}")
        print("1..1")
        print("# tests 1")
        print("# pass 0")
        print("# fail 1")
        print("# skipped 0")
        return 1

    cases: list[tuple[str, list[Any], Any, bool]] = []
    for name, args, reference in _normal_cases(task_id):
        cases.append((name, args, reference(*copy.deepcopy(args)), False))
    for name, args, error_type in _error_cases(task_id):
        cases.append((name, args, error_type.__name__, True))

    failures = 0
    for index, (name, args, expected, expects_error) in enumerate(cases, start=1):
        supplied = copy.deepcopy(args)
        before = copy.deepcopy(supplied)
        try:
            result = function(*supplied)
            actual: Any = {"returned": result}
            passed = not expects_error and result == expected and supplied == before
        except Exception as error:  # Exact exception class is an observable contract.
            actual = {"exception": type(error).__name__}
            passed = expects_error and type(error).__name__ == expected and supplied == before
        identity = f"{task_id} :: {name} :: deterministic contract case"
        if passed:
            print(f"ok {index} - {identity}")
        else:
            failures += 1
            print(f"not ok {index} - {identity}")
            print("  operator: deepStrictEqual")
            print(f"  expected: {_canonical({'input_unchanged': True, 'outcome': expected})}")
            print(f"  actual: {_canonical({'input_unchanged': supplied == before, 'outcome': actual})}")
    passed_count = len(cases) - failures
    print(f"1..{len(cases)}")
    print(f"# tests {len(cases)}")
    print(f"# pass {passed_count}")
    print(f"# fail {failures}")
    print("# skipped 0")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
