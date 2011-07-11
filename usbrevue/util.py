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

def apply_mask(mask, oval, nval):
    """Apply a mask with nval to oval, without disturbing bits in ~mask.

    >>> bin(apply_mask(0b11000000, 0b11000000, 0b11000000))
    '0b11000000'
    >>> bin(apply_mask(0b11000000, 0b01010101, 0b10000010))
    '0b10010101'
    >>> bin(apply_mask(0b11001100, 0b11111111, 0b00101000))
    '0b111011'
    >>> bin(apply_mask(0b11001100, 0b00000000, 0b00101000))
    '0b1000'
    """
    return ((mask & nval) | ( ~mask & oval ))

if __name__ == '__main__':
    import doctest
    doctest.testmod()

