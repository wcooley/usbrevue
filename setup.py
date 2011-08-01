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

from distutils.core import setup

setup(
        name        = 'usbrevue',
        version     = '0.1.0',
        description = 'USB Reverse-Engineering Toolkit',
        author      = 'TeamC',
        author_email= 'teamc@lists.pdxlinux.org',
        url         = 'https://bitbucket.org/TeamC2011/usbrevue/',
        classifiers = [
            'Development Status :: 3 - Alpha',
            'Environment :: Console',
            'Environment :: X11 Applications :: Qt',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: GNU General Public License (GPL)',
            'Natural Language :: English',
            'Operating System :: POSIX :: Linux',
            'Programming Language :: Python :: 2.7',
            'Topic :: System :: Hardware',
            'Topic :: System :: Hardware :: Hardware Drivers',
          ],
        py_modules  = [
            'usbrevue',
          ],
        scripts = [
            'usbcap',
            'usbgraph.py',
            'usbmodify.py',
            'usbreplay.py',
            'usbstatisfier.py',
            'usbview.py',
          ],
        )
