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

import string
import unittest

from array import array

from tutil import *
from subarray import subarray

class TestSubarray(unittest.TestCase):

    def setUp(self):
        self.test_array = array('c', string.uppercase)
        self.index = 4 # E:Z
        self.subarray = subarray(self.test_array, self.index)

    def test_basic_get1(self):
        self.assertEqual(self.subarray[0], self.test_array[4])

    def test_basic_slice1(self):
        self.assertEqual(self.subarray[:], self.test_array[self.index:])


if __name__ == '__main__':
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    suite.addTest(loader.loadTestsFromTestCase(TestSubarray))
    unittest.TextTestRunner(verbosity=2).run(suite)
