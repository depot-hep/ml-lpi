# coding: utf-8

"""
Helpful utilities.
"""

import functools

import six


# print function with auto-flush
print_ = functools.partial(six.print_, flush=True)


# file download helper
def download(src, dst, bar=None):
    import wget
    return wget.download(src, out=dst, bar=bar)
