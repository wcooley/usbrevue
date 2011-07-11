#!/usr/bin/env python

"""Module to make testing easier."""

import os.path
from os.path import abspath, dirname

import sys
tests_dir = abspath(dirname(__file__))  # Directory containing this module
mods_dir = abspath(dirname(tests_dir))  # Parent of this directory
sys.path.extend((tests_dir,mods_dir))

from pprint import pprint as pp
#pp(sys.path)

TEST_DATA_DIR = abspath(os.path.join(dirname(mods_dir), 'test-data'))

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
