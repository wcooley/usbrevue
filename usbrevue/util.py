#!/usr/bin/env python

"""Miscellaneous utilities"""

def reverse_update_dict(dictionary):
    """Update dictionary by adding val => key

    >>> d = dict(a=1)
    >>> reverse_update_dict(d)
    >>> d
    {'a': 1, 1: 'a'}
    """
    dictionary.update([ (val,key) for key,val in dictionary.items() ])

if __name__ == '__main__':
    import doctest
    doctest.testmod()

