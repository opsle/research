def parse_duration(value):
    amount = int(value[:-1])
    unit = value[-1]
    return amount * {"s": 1000, "m": 60000, "h": 3600000}[unit]
