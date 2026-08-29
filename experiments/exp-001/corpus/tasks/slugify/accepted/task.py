import re


def slugify(value):
    if not isinstance(value, str):
        raise TypeError("value must be a string")
    return "-".join(re.findall(r"[a-z0-9]+", value.lower(), flags=re.ASCII))
