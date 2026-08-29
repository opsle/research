def merge_ranges(ranges):
    normalized = []
    for item in ranges:
        if (not isinstance(item, (list, tuple)) or len(item) != 2
                or any(type(value) is not int for value in item)
                or item[0] > item[1]):
            raise ValueError("invalid closed range")
        normalized.append([item[0], item[1]])
    normalized.sort()
    merged = []
    for start, end in normalized:
        if merged and start <= merged[-1][1] + 1:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged
