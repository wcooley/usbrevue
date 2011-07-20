#!/usr/bin/env python
#
# Copyright (C) 2011 Austin Leirvik <aua at pdx.edu>
# Copyright (C) 2011 Wil Cooley <wcooley at pdx.edu>
# Copyright (C) 2011 Joanne McBride <jirab21@yahoo.com>
# Copyright (C) 2011 Danny Aley <danny.aley@gmail.com>
# Copyright (C) 2011 Erich Ulmer <blurrymadness@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

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

