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

import unittest
from functools import partial

from tutil import *
from fieldpack import FieldPack
from util import apply_mask

class TestFieldPack(unittest.TestCase,TestUtil):

    def setUp(self):
                        #0   1   2   3   4   5678   9
        test_data =     '\x80\xb3\x42\xf6\x00ABC\x01\x81'

        self.fieldpack = FieldPack(None, test_data)

        self.fieldpack.format_table = dict(
                    zero    = ( '<I', 0),   # 0-3
                    two     = ( '<c', 2),
                    four    = ( '<?', 4),
                    five    = ( '<c', 5),
                    six     = ( '<2s', 6),  # 6-7
                    seven   = ( '<c', 7),
                    eight   = ( '<h', 8),   # 8-9
                    nine    = ( '<B', 9),
                )
        self.assertEqual(len(test_data), 10)

        self.set_and_test = partial(self.setattr_and_test, self.fieldpack)

    def test_attr_zero(self):
        self.assertEqual(self.fieldpack.zero, 0xf642b380)

        self.set_and_test('zero', 0xffffffff)
        self.set_and_test('zero', 0x00000000)

        self.assertEqual(self.fieldpack.repack()[:4], '\x00' * 4)

    def test_attr_two(self):
        self.assertEqual(self.fieldpack.two, 'B')

        self.set_and_test('two', 'b')
        self.assertEqual(self.fieldpack.repack()[2], 'b')

    def test_attr_four(self):
        self.assertEqual(self.fieldpack.four, False)

        self.set_and_test('four', True)
        self.set_and_test('four', None)

    def test_attr_five(self):
        self.assertEqual(self.fieldpack.five, 'A')
        self.assertEqual(self.fieldpack.repack()[5], 'A')
        self.set_and_test('five', 'a')
        self.assertEqual(self.fieldpack.repack()[5], 'a')

    def test_parent_update(self):
        fmt_table = dict(   six1 = ('<c', 0),
                            six2 = ('<c', 1))

        def _update_six(fp, dp):
            fp.repacket('six', [dp.tostring()])

        fp2 = FieldPack(fmt_table, self.fieldpack.six,
                    partial(_update_six, self.fieldpack))
        fp2.six2 = 'D'

        self.assertEqual(fp2.six2, 'D')
        self.assertEqual(fp2.six2, self.fieldpack.seven)
        self.assertEqual(self.fieldpack.seven, 'D')

if __name__ == '__main__':
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    suite.addTest(loader.loadTestsFromTestCase(TestFieldPack))
    unittest.TextTestRunner(verbosity=2).run(suite)
