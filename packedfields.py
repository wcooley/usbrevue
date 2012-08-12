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

"""
    Class PackedFields represents a generic interface to unpacking and
    repacking data based on a format table.
"""

__version__ = '0.0.1'

from array import array
from collections import MutableSequence, Sequence
from pprint import pprint, pformat
from struct import unpack_from, pack_into
from logging import debug

class PackedFields(object):
    """Base class for field decodings/unpacking.

    The PackedFields class provides access to named fields in binary data with
    on-demand packing and unpacking.

    A PackedFields object is defined by a format table and sequence of data.
    The format table lists the name of the field (which becomes an object
    attribute), a ``struct`` format code and byte offset.

    The format table is a dict with entries with the following format:

        key: (format, offset)
    """

    # This must exist so __setattr__ can find key 'format_table' missing from
    # self.format_table when it is being initialized.
    format_table = dict()

    def __init__(self, format_table=None, datapack=None, update_parent=None):
        """Takes as arguments:
            1. format_table
                Described above
            2. datapack
                String or array of packed data
            3. update_parent
                Call-back function to enable attribute changes to flow up a
                heirarchy of PackedField objects. It requires, as argument, the
                datapack of the sub-object. Can be None.
                """
        self._cache = dict()

        if format_table != None:
            self.format_table = format_table

        self.datapack = datapack
        self.update_parent = update_parent

    def cache(self, attr, lookup_func):
        if not self._cache.has_key(attr):
            self._cache[attr] = lookup_func(attr)
        return self._cache[attr]

    # Generic attribute accessor
    # Note that we unpack the single item from the tuple in __getattr__ due to
    # setup()
    def unpacket(self, attr, fmtx=None):
        """Unpack attr from self.datapack using (struct) format string and
        offset from self.format_table. fmtx can be used to provide additional
        data for string-formatting that may be in the format string.

        Returns the tuple of data as from struct.unpack_from."""
        fmt, offset = self.format_table[attr]
        if fmtx != None: fmt %= fmtx
        return unpack_from(fmt, self.datapack, offset)

    def __getattr__(self, attr):
        """Pull attr from cache, looking it up with unpacket if necessary."""
        return self.cache(attr, lambda a: self.unpacket(a)[0])

    def repacket(self, attr, vals, fmtx=None):
        """Repack attr into self.datapack using (struct) format string and
        offset from self.format_table. fmtx can be used to provide additional
        data for string-formatting that may be in the format string."""
        debug('repacket: attr: %s, vals: %s, fmtx: %s', attr, pformat(vals), fmtx)
        fmt, offset = self.format_table[attr]
        if fmtx != None: fmt %= fmtx
        return pack_into(fmt, self.datapack, offset, *vals)

    def __setattr__(self, attr, val):
        """__setattr__ is called went setting all attributes, so it must
        differentiate between tabled-based attributes and regular attributes.
        If the attribute is not a key in self.format_table, then it calls up to
        ``object``'s __setattr__, which handles "normal" attributes,
        properties, etc."""
        if attr in self.format_table:
            self._cache[attr] = val
            self.repacket(attr, [val])
            if self.update_parent != None:
                self.update_parent(self.datapack)
        else:
            # This makes properties and non-format_table attributes work
            object.__setattr__(self, attr, val)

    # Implementing __getitem__ and __setitem__ permit the object to be used as
    # a mapping type, so it can be used as e.g. the global or local namespace
    # with 'eval'.
    def __getitem__(self, attr):
        """Allows instance to be accessed as dict using attributes as keys."""
        return getattr(self, attr)

    def __setitem__(self, attr, val):
        """Allows instance to be updated as dict using attributes as keys."""
        setattr(self, attr, val)

    @property
    def datapack(self):
        """Holds the array containing the data which is packed into or unpacked
        from."""
        return self.__dict__['datapack']

    @datapack.setter
    def datapack(self, value):
        if isinstance(value, Sequence) and \
                not isinstance(value, MutableSequence):
            self.__dict__['datapack'] = array('c', value)
        else:
            self.__dict__['datapack'] = value

    def repack(self):
        """
        Returns a string representation of the datapack.
        """
        return self.datapack.tostring()

    def __eq__(self, other):
        return self.datapack == other.datapack

    def __ne__(self, other):
        return self.datapack != other.datapack


