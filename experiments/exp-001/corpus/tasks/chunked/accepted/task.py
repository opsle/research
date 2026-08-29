def chunked(items, size):
    if type(size) is not int or size <= 0:
        raise ValueError("size must be a positive integer")
    return [list(items[index:index + size])
            for index in range(0, len(items), size)]
