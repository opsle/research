def merge_headers(pairs):
    result = []
    positions = {}
    for pair in pairs:
        if (not isinstance(pair, (list, tuple)) or len(pair) != 2
                or not isinstance(pair[0], str) or not pair[0]
                or not isinstance(pair[1], str)):
            raise ValueError("invalid header pair")
        key = pair[0].lower()
        if key in positions:
            result[positions[key]][1] = pair[1]
        else:
            positions[key] = len(result)
            result.append([pair[0], pair[1]])
    return result
