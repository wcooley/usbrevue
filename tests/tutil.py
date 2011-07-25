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

"""Module to make testing easier."""

import os.path
from os.path import abspath, dirname

import sys
tests_dir = abspath(dirname(__file__))  # Directory containing this module
mods_dir = abspath(dirname(tests_dir))  # Parent of this directory
sys.path.extend((tests_dir,mods_dir))

from pprint import pprint as pp
#pp(sys.path)

TEST_DATA_DIR = tests_dir

# Quick check for Python 2.7+, to control using features which are only
# available in there (such as @unittest.skip)
PYTHON_2_7_PLUS = True  if sys.version_info[0] == 2 and sys.version_info[1] >= 7 \
             else False

def test_data(fname):
    return os.path.join(TEST_DATA_DIR, fname)

class TestUtil(object):
    """Mix-in class of functions supporting testing."""

    def setattr_and_test(self, obj, attr, val, msg=None):
        """Set the field to some provided value and then check that we get the
        same thing reading it.
        """
        # I suspect this will need some magic for errors/exceptions to look right,
        # like Perl's Carp module
        setattr(obj, attr, val)
        self.assertEqual(getattr(obj, attr), val, msg)


if __name__ == '__main__':
    print 'TEST_DATA_DIR:', TEST_DATA_DIR
    print 'PYTHON_2_7_PLUS:', PYTHON_2_7_PLUS
