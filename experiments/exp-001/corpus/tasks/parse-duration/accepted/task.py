import re
from decimal import Decimal, InvalidOperation


def parse_duration(value):
    if not isinstance(value, str):
        raise ValueError("duration must be a string")
    match = re.fullmatch(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(ms|s|m|h)", value)
    if match is None:
        raise ValueError("invalid duration")
    try:
        number = Decimal(value[:-len(match.group(1))])
    except InvalidOperation as error:
        raise ValueError("invalid duration") from error
    factor = {"ms": 1, "s": 1000, "m": 60000, "h": 3600000}[match.group(1)]
    milliseconds = number * factor
    if milliseconds != milliseconds.to_integral_value():
        raise ValueError("duration is not a whole millisecond")
    return int(milliseconds)
