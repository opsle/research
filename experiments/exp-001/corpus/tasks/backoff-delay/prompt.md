Implement `backoff_delay(attempt, base_ms, cap_ms)` in `task.py`.

All inputs must be integers but not booleans. `attempt` is non-negative and
`base_ms` and `cap_ms` are positive; invalid input raises `ValueError`. Return
`min(cap_ms, base_ms * 2 ** attempt)` as an integer.
