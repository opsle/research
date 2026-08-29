def backoff_delay(attempt, base_ms, cap_ms):
    return min(cap_ms, base_ms * 2 ** (attempt + 1))
