import numpy as np

def none_max(a, b):
    if a is None:
        return b
    if b is None:
        return a
    return max(a, b)


def max_dict(dict_a, dict_b):
    all_keys = dict_a.keys() | dict_b.keys()
    return {k: none_max(dict_a.get(k), dict_b.get(k)) for k in all_keys}


def time_to_seconds(t):
    """Convert a human-readable time string to seconds
    Time in a format ___s, ___m, ___h where ___ is any number. E.g. 5s, 5m, 5h"""
    time_units = {'s': 1, 'm': 60, 'h': 3600}
    unit = t[-1]
    val = int(t[0:-1])
    if unit in time_units and val > 0:
        return int(val * time_units[unit])
    return 0


