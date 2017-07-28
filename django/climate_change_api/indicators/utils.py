from itertools import islice


def merge_dicts(x, y):
    """Merge two dicts, returning a shallow copy of both with values in y overwriting x."""
    z = x.copy()
    z.update(y)
    return z


def sliding_window(it, n=2):
    """Return a sliding window (of width n) over items from the iterable.

    s -> (s0,s1,...s[n-1]), (s1,s2,...,sn), ...

    From https://docs.python.org/release/2.3.5/lib/itertools-example.html
    """
    it = iter(it)
    result = tuple(islice(it, n))
    if len(result) == n:
        yield result
    for elem in it:
        result = result[1:] + (elem,)
        yield result


def running_total(iterator, floor=None):
    """Calculate a running total from a numeric iterator.

    For instance, range(5) becomes (0, 1, 3, 6, 10)

    If floor is set, the running total will never fall beneath that value.
    """
    total = 0
    for val in iterator:
        # If val is negative, ensure we don't go below floor
        total = max(total + val, floor)
        yield total
