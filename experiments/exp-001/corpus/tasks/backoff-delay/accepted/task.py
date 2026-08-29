def backoff_delay(attempt, base_ms, cap_ms):
    if (any(type(value) is not int for value in (attempt, base_ms, cap_ms))
            or attempt < 0 or base_ms <= 0 or cap_ms <= 0):
        raise ValueError("invalid backoff inputs")
    return min(cap_ms, base_ms * 2 ** attempt)
