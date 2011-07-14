#!/usr/bin/env python
"""Unit test for usbmodify.py"""

from __future__ import division

import pcapy
import tutil
import usbmodify
from usbrevue import Packet
import unittest
import struct

from tutil import *

class ModAttrsByRoutineFile(unittest.TestCase):
    """Change each packet attribute to some value. All tests should
    pass.

    """

    modifier = usbmodify.Modifier('', 'test_routine_file', '')

    def test_mod_urb(self):
        f = open('test_routine_file', 'w')
        f.write('urb = 12345')
        f.close()

        for packet in packet_generator():
            self.modifier.apply_routine_file(packet)
            self.assertEqual(getattr(packet, 'urb'), 12345)


    def test_mod_event_type(self):
        f = open('test_routine_file', 'w')
        f.write('event_type = "E"')
        f.close()

        for packet in packet_generator():
            self.modifier.apply_routine_file(packet)
            self.assertEqual(getattr(packet, 'event_type'), 'E')


    def test_mod_xfer_type(self):
        f = open('test_routine_file', 'w')
        f.write('xfer_type = 3')
        f.close()

        for packet in packet_generator():
            self.modifier.apply_routine_file(packet)
            self.assertEqual(getattr(packet, 'xfer_type'), 3)


    def test_mod_epnum(self):
        f = open('test_routine_file', 'w')
        f.write('epnum = 55')
        f.close()

        for packet in packet_generator():
            self.modifier.apply_routine_file(packet)
            self.assertEqual(getattr(packet, 'epnum'), 55)


    def test_mod_devnum(self):
        f = open('test_routine_file', 'w')
        f.write('devnum = 12')
        f.close()

        for packet in packet_generator():
            self.modifier.apply_routine_file(packet)
            self.assertEqual(getattr(packet, 'devnum'), 12)


    def test_mod_busnum(self):
        f = open('test_routine_file', 'w')
        f.write('busnum = 32')
        f.close()

        for packet in packet_generator():
            self.modifier.apply_routine_file(packet)
            self.assertEqual(getattr(packet, 'busnum'), 32)


    def test_mod_flag_setup(self):
        f = open('test_routine_file', 'w')
        f.write('flag_setup = "1"')
        f.close()

        for packet in packet_generator():
            self.modifier.apply_routine_file(packet)
            self.assertEqual(getattr(packet, 'flag_setup'), '1')


    def test_mod_flag_data(self):
        f = open('test_routine_file', 'w')
        f.write('flag_data = "!"')
        f.close()

        for packet in packet_generator():
            self.modifier.apply_routine_file(packet)
            self.assertEqual(getattr(packet, 'flag_data'), '!')


    def test_mod_ts_sec(self):
        f = open('test_routine_file', 'w')
        f.write('ts_sec = 9876543210')
        f.close()

        for packet in packet_generator():
            self.modifier.apply_routine_file(packet)
            self.assertEqual(getattr(packet, 'ts_sec'), 9876543210)


    def test_mod_ts_usec(self):
        f = open('test_routine_file', 'w')
        f.write('ts_usec = 1234567890')
        f.close()

        for packet in packet_generator():
            self.modifier.apply_routine_file(packet)
            self.assertEqual(getattr(packet, 'ts_usec'), 1234567890)


    def test_mod_status(self):
        f = open('test_routine_file', 'w')
        f.write('status = 42')
        f.close()

        for packet in packet_generator():
            self.modifier.apply_routine_file(packet)
            self.assertEqual(getattr(packet, 'status'), 42)


    def test_mod_length(self):
        f = open('test_routine_file', 'w')
        f.write('length = 16')
        f.close()

        for packet in packet_generator():
            self.modifier.apply_routine_file(packet)
            self.assertEqual(getattr(packet, 'length'), 16)


    def test_mod_len_cap(self):
        f = open('test_routine_file', 'w')
        f.write('len_cap = 1')
        f.close()

        for packet in packet_generator():
            self.modifier.apply_routine_file(packet)
            self.assertEqual(getattr(packet, 'len_cap'), 1)


    def test_mod_setup(self):
        f = open('test_routine_file', 'w')
        f.write('if flag_setup == "S": setup = [12]')
        f.close()

        for packet in packet_generator():
            if packet.flag_setup == "s":
                self.modifier.apply_routine_file(packet)
                self.assertEqual(getattr(packet, 'setup'), [12])


    def test_mod_error_count(self):
        f = open('test_routine_file', 'w')
        f.write('if xfer_type == 0: error_count = 99')
        f.close()

        for packet in packet_generator():
            if packet.xfer_type == 0:
                self.modifier.apply_routine_file(packet)
                self.assertEqual(getattr(packet, 'error_count'), 99)


    def test_mod_numdesc(self):
        f = open('test_routine_file', 'w')
        f.write('if xfer_type == 0: numdesc = 200')
        f.close()

        for packet in packet_generator():
            if packet.xfer_type == 0:
                self.modifier.apply_routine_file(packet)
                self.assertEqual(getattr(packet, 'numdesc'), 200)


    def test_mod_interval(self):
        f = open('test_routine_file', 'w')
        f.write('if xfer_type in [0, 1]: interval = 2')
        f.close()

        for packet in packet_generator():
            if packet.xfer_type in [0, 1]:
                self.modifier.apply_routine_file(packet)
                self.assertEqual(getattr(packet, 'interval'), 2)


    def test_mod_start_frame(self):
        f = open('test_routine_file', 'w')
        f.write('if xfer_type == 0: start_frame = 4')
        f.close()

        for packet in packet_generator():
            if packet.xfer_type == 0:
                self.modifier.apply_routine_file(packet)
                self.assertEqual(getattr(packet, 'start_frame'), 4)


    def test_mod_xfer_flags(self):
        f = open('test_routine_file', 'w')
        f.write('xfer_flags = 49294')
        f.close()

        for packet in packet_generator():
            self.modifier.apply_routine_file(packet)
            self.assertEqual(getattr(packet, 'xfer_flags'), 49294)


    def test_mod_ndesc(self):
        f = open('test_routine_file', 'w')
        f.write('ndesc = 847934')
        f.close()

        for packet in packet_generator():
            self.modifier.apply_routine_file(packet)
            self.assertEqual(getattr(packet, 'ndesc'), 847934)



class ModByModule(unittest.TestCase):
    """Change different packet attributes with a user-supplied module."""




class ModDataByExp(unittest.TestCase):
    """Change a data byte to a value based on two other data
    bytes. All tests should pass.

    """

    def test_add(self):
        modifier = usbmodify.Modifier('', '', ['data[0] = data[1] + data[2]'])

        for packet in packet_generator():
            modifier.apply_cmdline_exps(packet)
            if len(packet.data):
                self.assertEqual(packet.data[0], packet.data[1] + packet.data[2])


    def test_sub(self):
        modifier = usbmodify.Modifier('', '', ['data[0] = data[1] - data[2]'])

        for packet in packet_generator():
            modifier.apply_cmdline_exps(packet)
            if len(packet.data):
                self.assertEqual(packet.data[0], packet.data[1] - packet.data[2])


    def test_mult(self):
        modifier = usbmodify.Modifier('', '', ['data[0] = data[1] * data[2]'])

        for packet in packet_generator():
            modifier.apply_cmdline_exps(packet)
            if len(packet.data):
                self.assertEqual(packet.data[0], packet.data[1] * packet.data[2])


    def test_div(self):
        modifier = usbmodify.Modifier('', '', ['data[0] = data[1] / (data[2] + 1)'])

        for packet in packet_generator():
            modifier.apply_cmdline_exps(packet)
            if len(packet.data):
                self.assertEqual(packet.data[0], packet.data[1] / (packet.data[2] + 1))


    def test_bit_and(self):
        modifier = usbmodify.Modifier('', '', ['data[0] = data[1] & data[2]'])

        for packet in packet_generator():
            modifier.apply_cmdline_exps(packet)
            if len(packet.data):
                self.assertEqual(packet.data[0], packet.data[1] & packet.data[2])


    def test_bit_or(self):
        modifier = usbmodify.Modifier('', '', ['data[0] = data[1] | data[2]'])

        for packet in packet_generator():
            modifier.apply_cmdline_exps(packet)
            if len(packet.data):
                self.assertEqual(packet.data[0], packet.data[1] | packet.data[2])


    def test_bit_not(self):
        modifier = usbmodify.Modifier('', '', ['data[0] = ~ data[1]'])

        for packet in packet_generator():
            modifier.apply_cmdline_exps(packet)
            if len(packet.data):
                self.assertEqual(packet.data[0], ~ packet.data[1])


    def test_bit_xor(self):
        modifier = usbmodify.Modifier('', '', ['data[0] = data[1] ^ data[2]'])

        for packet in packet_generator():
            modifier.apply_cmdline_exps(packet)
            if len(packet.data):
                self.assertEqual(packet.data[0], packet.data[1] ^ packet.data[2])


    def test_logical_and(self):
        modifier = usbmodify.Modifier('', '', ['data[0] = data[1] and data[2]'])

        for packet in packet_generator():
            modifier.apply_cmdline_exps(packet)
            if len(packet.data):
                self.assertEqual(packet.data[0], packet.data[1] and packet.data[2])


    def test_logical_or(self):
        modifier = usbmodify.Modifier('', '', ['data[0] = data[1] or data[2]'])

        for packet in packet_generator():
            modifier.apply_cmdline_exps(packet)
            if len(packet.data):
                self.assertEqual(packet.data[0], packet.data[1] or packet.data[2])


    def test_logical_not(self):
        modifier = usbmodify.Modifier('', '', ['data[0] = not data[1]'])

        for packet in packet_generator():
            modifier.apply_cmdline_exps(packet)
            if len(packet.data):
                self.assertEqual(packet.data[0], not packet.data[1])


    def test_logical_xor(self):
        modifier = usbmodify.Modifier('', '', ['data[0] = bool(data[1]) ^ bool(data[2])'])

        for packet in packet_generator():
            modifier.apply_cmdline_exps(packet)
            if len(packet.data):
                self.assertEqual(packet.data[0], bool(packet.data[1]) ^ bool(packet.data[2]))



class BadData(unittest.TestCase):
    """Check that invalid attribute values will be rejected."""

    modifier = usbmodify.Modifier('', 'test_routine_file', '')

    def test_bad_urb(self):
        f = open('test_routine_file', 'w')
        f.write('urb = 100 ** 100')
        f.close()

        for packet in packet_generator():

            self.assertRaises(ValueError, self.modifier.apply_routine_file, packet)

    def test_bad_type(self):
        f = open('test_routine_file', 'w')
        f.write('event_type = "XX"')
        f.close()

        for packet in packet_generator():
            self.assertRaises(ValueError, self.modifier.apply_routine_file, packet)


    def test_bad_xfer_type(self):
        f = open('test_routine_file', 'w')
        f.write('xfer_type = -44')
        f.close()

        for packet in packet_generator():
            self.assertRaises(ValueError, self.modifier.apply_routine_file, packet)


    def test_bad_epnum(self):
        f = open('test_routine_file', 'w')
        f.write('epnum = AB')
        f.close()

        for packet in packet_generator():
            self.assertRaises(ValueError, self.modifier.apply_routine_file, packet)


    def test_bad_devnum(self):
        f = open('test_routine_file', 'w')
        f.write('devnum = YZ')
        f.close()

        for packet in packet_generator():
            self.assertRaises(ValueError, self.modifier.apply_routine_file, packet)


    def test_bad_busnum(self):
        f = open('test_routine_file', 'w')
        f.write('busnum = -100')
        f.close()

        for packet in packet_generator():
            self.assertRaises(ValueError, self.modifier.apply_routine_file, packet)


    def test_bad_flag_setup(self):
        f = open('test_routine_file', 'w')
        f.write('flag_setup = C')
        f.close()

        for packet in packet_generator():
            self.assertRaises(ValueError, self.modifier.apply_routine_file, packet)


    def test_bad_ts_sec(self):
        f = open('test_routine_file', 'w')
        f.write('ts_sec = 100 ** 100')
        f.close()

        for packet in packet_generator():
            self.assertRaises(ValueError, self.modifier.apply_routine_file, packet)


    def test_bad_ts_usec(self):
        f = open('test_routine_file', 'w')
        f.write('ts_usec = -100 ** 100')
        f.close()

        for packet in packet_generator():
            self.assertRaises(ValueError, self.modifier.apply_routine_file, packet)


    def test_bad_status(self):
        f = open('test_routine_file', 'w')
        f.write('status = "a string"')
        f.close()

        for packet in packet_generator():
            self.assertRaises(ValueError, self.modifier.apply_routine_file, packet)


    def test_bad_length(self):
        f = open('test_routine_file', 'w')
        f.write('length = -1')
        f.close()

        for packet in packet_generator():
            self.assertRaises(ValueError, self.modifier.apply_routine_file, packet)


    def test_bad_len_cap(self):
        f = open('test_routine_file', 'w')
        f.write('len_cap = 10 ** 10')
        f.close()

        for packet in packet_generator():
            self.assertRaises(ValueError, self.modifier.apply_routine_file, packet)


    def test_bad_setup(self):
        f = open('test_routine_file', 'w')
        f.write('if flag_setup == "S": setup = [-4]')
        f.close()

        for packet in packet_generator():
            if packet.flag_setup == "S":
                self.assertRaises(ValueError, self.modifier.apply_routine_file, packet)


    def test_bad_error_count(self):
        f = open('test_routine_file', 'w')
        f.write('if xfer_type == 0: error_count = 4.5')
        f.close()

        for packet in packet_generator():
            if packet.xfer_type == 0:
                self.assertRaises(ValueError, self.modifier.apply_routine_file, packet)


    def test_bad_numdesc(self):
        f = open('test_routine_file', 'w')
        f.write('if xfer_type == 0: numdesc = -7 ** 0.5')
        f.close()

        for packet in packet_generator():
            if packet.xfer_type == 0:
                self.assertRaises(ValueError, self.modifier.apply_routine_file, packet)


    def test_bad_interval(self):
        f = open('test_routine_file', 'w')
        f.write('if xfer_type in [0, 1]: interval = -2.5 ** 100')
        f.close()

        for packet in packet_generator():
            if packet.xfer_type in [0, 1]:
                self.assertRaises(ValueError, self.modifier.apply_routine_file, packet)


    def test_bad_start_frame(self):
        f = open('test_routine_file', 'w')
        f.write('if xfer_type == 0: start_frame = 500.0 * 0.284794')
        f.close()

        for packet in packet_generator():
            if packet.xfer_type == 0:
                self.assertRaises(ValueError, self.modifier.apply_routine_file, packet)


    def test_bad_xfer_flags(self):
        f = open('test_routine_file', 'w')
        f.write('xfer_flags = "abcde"')
        f.close()

        for packet in packet_generator():
            self.assertRaises(ValueError, self.modifier.apply_routine_file, packet)


    def test_bad_ndesc(self):
        f = open('test_routine_file', 'w')
        f.write('ndesc = -0.1 ** -100')
        f.close()

        for packet in packet_generator():
            self.assertRaises(ValueError, self.modifier.apply_routine_file, packet)




def packet_generator():
    pcap = pcapy.open_offline(test_data('testdump_usbmodify.pcap'))

    while True:
        (hdr, pack) = pcap.next()
        if hdr is None:
            return # EOF
        yield Packet(hdr, pack)





if __name__ == "__main__":
    unittest.main()
