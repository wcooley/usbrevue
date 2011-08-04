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
"""This is the USB Modifier module. It lets the user modify USB
packets programmatically by specifying one or more routines to be
applied to each packet in a pcap stream/file.

"""
from __future__ import division

import sys
import pcapy
import gflags
import re
import struct
import tempfile
import os
from scapy.all import RawPcapWriter, RawPcapReader
from usbrevue import Packet


FLAGS = gflags.FLAGS

gflags.DEFINE_string('mod', None, 'A Python module file containing your custom Python code to be executed.')
gflags.DEFINE_string('routine', None, 'Filename containing your modification routine.')
gflags.DEFINE_list('exp', None, 'A comma-separated list of expressions to be applied at data payload byte offsets. Offsets are referenced as "data[0], data[1], ...". Arithmetic operators (+, -, *, /), logical operators (and, or, not), and bitwise operators (^, &, |, !) are supported. For logical xor, use "bool(a) ^ bool(b)".')
gflags.DEFINE_boolean('verbose', False, 'Verbose mode; display the details of each packet modified.')



class Modifier(object):
    """This class implements all modifier functionality. Does not
    interface with pcapy; instead, it expects to receive pcapy Reader
    and Dumper objects to work with.

    """
    def __init__(self, module_file, routine_file, cmdline_exps):
        self.pcap = None
        self.out = None
        self.module_file = module_file
        self.routine_file = routine_file
        self.cmdline_exps = cmdline_exps

    def run(self):
        """If a user-supplied module file is present, simply run that
        module. Otherwise, Pass each packet from the packet stream
        directly to commit_packet, where the user-supplied routines
        will be applied.

        """

        if self.module_file is not None:
            self.run_module_file()
        else:
            for packet in self.packet_generator('-'):
                self.commit_packet(packet)


    def run_module_file(self):
        """Run the user-supplied module implementing a function called
        modify. It is a assumed that modify will take two arguments,
        both functions: the packet generator and the packet
        committer.

        """
        modfile = __import__(self.module_file)
        try:
            modfile.modify(self.packet_generator, self.commit_packet)
        except (AttributeError, TypeError) as err:
            sys.stderr.write(err.message + '\n')
            sys.stderr.write('(Your module must implement a function called modify with two arguments, both functions: a packet generator and a packet committer)\n')
            sys.exit(1)
        except NameError as err:
            sys.stderr.write('There was an error while executing your module:\n')
            sys.stderr.write(err.message + '\n')
            sys.exit(1)


    def packet_generator(self, input_stream='-'):
        """Open a pcap stream specified by input_stream and yield each
        packet in the stream. Also create the Dumper object and store
        it for later use, since we need the Reader object created here
        in order to create the Dumper.

        """
        self.pcap = pcapy.open_offline(input_stream)

        # create the Dumper object now that we have a Reader
        if not sys.stdout.isatty():
            self.out = self.pcap.dump_open('-')

        while True:
            (hdr, pack) = self.pcap.next()
            if hdr is None:
               return # EOF
            # keep track of the most recent yielding packet, for diffing
            self.orig_packet = Packet(hdr, pack)
            yield Packet(hdr, pack)


    def commit_packet(self, packet):
        """Apply the command line expressions(s) and routine file (if
        any) to the packet and, if output it being piped to somewhere
        other than the terminal, dump the packet into the outgoing
        pcap stream.

        """
        self.apply_cmdline_exps(packet)
        self.apply_routine_file(packet)

        # print out changes to each packet if --verbose
        if FLAGS.verbose:
            diff_list = packet.diff(self.orig_packet)
            if len(diff_list) > 0:
                for (attr, my_val, other_val) in diff_list:
                    sys.stderr.write(attr + ': ' + str(other_val) + ' -> ' + str(my_val) + '\n')
                sys.stderr.write('\n')

        if self.pcap is None:
            sys.stderr.write('Attempted to dump packets without first reading them -- make sure to call packet_generator()')
            sys.exit(1)
        else:
            # make a temp file, use scapy's RawPcapWriter to write the
            # current packet to that file, then read that same packet
            # in using a new instance of pcapy.open_offline, then
            # write out to stdout the packet that we just read back
            # in, then finally delete the temp file
            # 
            # we have to do it this way in case the size of the packet
            # changed, in which case the packet's pcap header needs to
            # be regenerated. RawPcapWriter does this for us
            #
            # on reflection, it would be pretty straightforward to
            # copy RawPcapWriter's code for generating the pcap
            # header(s) and do it ourselves, without the messy temp
            # file stuff. this code should be re-worked to do that.
            temp = tempfile.mkstemp()
            rpw = RawPcapWriter(temp[1], linktype = 220, sync=True)
            rpw.write(packet.repack())
            mypcap = pcapy.open_offline(temp[1])
            (myhdr, mypack) = mypcap.next()
            if not sys.stdout.isatty():
                self.out.dump(myhdr, mypack)
            os.remove(temp[1])


    def apply_routine_file(self, packet):
        """Apply the user-supplied external routine file to a packet."""
        if self.routine_file is not None:
            try:
                execfile(self.routine_file, {}, packet)
            except (ValueError, struct.error, NameError) as err:
                raise ValueError, 'There was an error converting a packet to a binary string (' + err.message + ')'


    def apply_cmdline_exps(self, packet):
        """Apply the expression supplied at the command line to a packet."""
        if self.cmdline_exps is not None:
            for exp in self.cmdline_exps:
                max_offset = 0 # highest offset needed to perform this expression

                # find max_offset
                matches = re.finditer(r"data\[(\d+)\]", exp)
                if matches:
                    for match in matches:
                        if match.group(1) > max_offset:
                            max_offset = int(match.group(1))

                if len(packet.data) > max_offset:
                    exec(exp, {}, packet)


    # accessors and mutators
    def set_routine_file(self, filestr):
        """Set the name of the user-supplied external routine file."""
        self.routine_file = filestr


    def set_cmdline_exp(self, exps):
        """Set the expression(s) meant to be passed in on the command line."""
        self.cmdline_exp = exps



def end_modifier(num_modified):
    """Display the number of modified packets (passed as parameter)
    and exit normally.

    """
    sys.stderr.write('\nSuccessfully modified ' + str(num_modified) + ' packets\n')
    sys.exit(0)



if __name__ == "__main__":
    # Open a pcap file from stdin, apply the user-supplied modification to
    # the stream, re-encode the packet stream, and send it to stdout.

    # Check if the user supplied a separate modification routine file (with the
    # --routine flag) and/or command line expression(s) (with the --exp flag). At
    # least one of these must be specified
    try:
        argv = FLAGS(sys.argv)
    except gflags.FlagsError:
        sys.stderr.write('There was an error parsing the command line arguments. Please use --help.')
        sys.exit(1)
    if FLAGS.routine is None and FLAGS.exp is None and FLAGS.mod is None:
        sys.stderr.write('You must supply at least one of the following: a modification file, one or more command line expressions, or a Python module.\n')
        sys.exit(1)

    modifier = Modifier(FLAGS.mod, FLAGS.routine, FLAGS.exp)
    try:
        modifier.run()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
