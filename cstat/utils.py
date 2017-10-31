# -*- coding: utf-8; -*-
# vi: set encoding=utf-8


BYTE_SIZES = ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']

def byte_size(value, suffix='b', k=1024):
    for unit in BYTE_SIZES:
        if abs(value) < k:
            break
        value /= k
    return '{0:.1f}{1}{2}'.format(value, unit, suffix)

