Implement `parse_duration(value)` in `task.py`.

Accept a string containing an unsigned integer or decimal immediately followed
by one of `ms`, `s`, `m`, or `h`. Convert it to an exact whole number of
milliseconds. Reject whitespace, signs, exponents, missing units, and values
that are not a whole millisecond by raising `ValueError`. Non-strings also raise
`ValueError`.
