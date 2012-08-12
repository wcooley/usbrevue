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

import array
import logging

from logging import debug

#logging.basicConfig(level=logging.DEBUG)

def _add_or_minus(base, addor):
    """Add 'addor' to positive base; pass negative unchanged"""
    if base >= 0:
        base += addor
    return base

def _calc_offset(index, offset):
    """Calculate offset, taking into account the possibility that 'index'
    is a slice"""
    if isinstance(index, slice):
        start = index.start if index.start != None else 0
        stop = index.stop if index.stop != None else 0
        start = _add_or_minus(start, offset)
        stop = _add_or_minus(stop, offset)
        index = slice(start, stop, index.step)
    else:
        index = _add_or_minus(index, offset)
    return index

class subarray(object):
    """The `subarray` class creates an wrapper for an array which allows
    indexing from zero at a given offset, giving the appearance of a separate
    array.

    For example:
    >>> parent = array.array('c', ['a', 'b', 'c', 'd', 'e', 'f', 'g'])
    >>> subarr = subarray(parent, 3)
    >>> subarr[0] == 'd'
    True

    Note that currently only the beginning of offset; ending the subarray
    shorter than the parent array is not currently supported.
    >>> subarr[-1] == 'g'
    True
    """

    def __init__(self, parent_array=None, subarray_offset=0):
        self.parent_array = parent_array
        self.offset = subarray_offset

        super(subarray, self).__init__()

    def __getitem__(self, index):
        return self.parent_array[_calc_offset(index, self.offset)]

    def __setitem__(self, index, val):
        self.parent_array[_calc_offset(index, self.offset)] = val

if __name__ == '__main__':
    import doctest
    doctest.testmod()
