# -*- coding: utf-8 -*-

from bisect import insort


def imerge_reversed(*iterables):
    """Merge multiple reversedly sorted inputs into a single reversed sorted
    output.

    Equivalent to:  sorted(itertools.chain(*iterables), reverse=True)

    """
    insort_right = insort
    h = []
    h_append = h.append
    for it in iterables:
        try:
            next = iter(it).next
            h_append((next(), next))
        except StopIteration:
            pass
    h.sort()

    while 1:
        try:
            v, next = h.pop()
            yield v
            insort_right(h, (next(), next))
        except StopIteration:
            pass
        except IndexError:
            return
