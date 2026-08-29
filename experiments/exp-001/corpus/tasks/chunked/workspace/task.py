def chunked(items, size):
    return [items[index * size:(index + 1) * size]
            for index in range(len(items) // size)]
