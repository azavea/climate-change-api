
def merge_dicts(x, y):
    """Merge two dicts, returning a shallow copy of both with values in y overwriting x."""
    z = x.copy()
    z.update(y)
    return z
