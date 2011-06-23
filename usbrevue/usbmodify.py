#!/usr/bin/env python

import sys
import pcapy
import gflags
import re
import copy
from usbrevue import Packet

FLAGS = gflags.FLAGS

gflags.DEFINE_string('routine', None, 'Filename containing your modification routine.')

gflags.DEFINE_list('exp', None, 'A comma-separated list of expressions to be applied at data payload byte offsets. Offsets are referenced as "data[0], data[1], ...". Arithmetic operators (+, -, *, /), logical operators (and, or, not), and bitwise operators (^, &, |, !) are supported. For logical xor, use "bool(a) ^ bool(b)".')


class Modifier(object):
    def __init__(self, pcap, out, routine_file, cmdline_exps):
        self.pcap = pcap
        self.out = out
        self.routine_file = routine_file
        self.cmdline_exps = cmdline_exps

    def run(self):

        # continuously read packets, apply the modification routine, and write out
        while True:
            (hdr, pack) = pcap.next()
            if hdr is None:
                break # EOF
            packet = Packet(hdr, pack)

            # keep track of which parts of the packet, if any, are modified
            modified = {}
            for member in packet.__dict__:
                modified[member] = False
            orig_packet = packet.copy()
            self.apply_routine_file(packet)
            self.apply_cmdline_exps(packet)

            # figure out which parts of the packet were modified and print out
            # the changed parts (for debugging)
            notice_printed = False
            for member in packet.__dict__:
                if eval('packet.' + member) != eval('orig_packet.' + member):
                    if not notice_printed:
                        print 'Packet modified'
                        notice_printed = True
                    print str(eval('orig_packet.' + member)) + ' -> ' + str(eval('packet.' + member))
                    if notice_printed:
                        print '\n'

                    # this needs to be re-examined once repack() does more than update
                    # the data payload
                    if not sys.stdout.isatty():
                        out.dump(packet.hdr, packet.repack())


    def apply_routine_file(self, packet):
        if self.routine_file is not None:
            execfile(self.routine_file, {}, packet.__dict__)


    def apply_cmdline_exps(self, packet):
      if self.cmdline_exps is not None:
        for exp in self.cmdline_exps:
          max_offset = 0 # highest offset needed to perform this expression

          # find max_offset
          matches = re.finditer(r"data\[(\d+)\]", exp)
          if matches:
            for match in matches:
              if match.group(1) > max_offset:
                max_offset = int(match.group(1))

          if len(packet.data) >= max_offset:
            # TODO: Add regex so user can specify logical xor directly in the
            # expression
            # TODO: Error checking for non-supported operations/expressions
            exec(exp, {}, packet.__dict__)
    
if __name__ == "__main__":
    # Open a pcap file from stdin, apply the user-supplied modification to
    # the stream, re-encode the packet stream, and send it to stdout.
    
    # Check if the user supplied a separate modification routine file (with the
    # --routine flag) and/or command line expression(s) (with the --exp flag). At
    # least one of these must be specified
    try:
        argv = FLAGS(sys.argv)
    except gflags.FlagsError:
        sys.exit(1)
    if FLAGS.routine is None and FLAGS.exp is None:
        sys.stderr.write("""You must supply either a modification file, one or more command line expressions, or both.\n""")
        sys.exit(1)

    pcap = pcapy.open_offline('-')
    if not sys.stdout.isatty():
        out = pcap.dump_open('-')
    modifier = Modifier(pcap, out, FLAGS.routine, FLAGS.exp)
    modifier.run()
