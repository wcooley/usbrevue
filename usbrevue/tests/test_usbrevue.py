#!/usr/bin/env python

import os
import os.path
import struct
import sys
import unittest
from array import array
from functools import partial
from pprint import pformat

import pcapy

from tutil import *
from usbrevue import *

class TestPackedFields(unittest.TestCase,TestUtil):

    def setUp(self):
                        #0   1   2   3   4   5678   9
        test_data =     '\x80\xb3\x42\xf6\x00ABC\x01\x81'

        self.fieldpack = PackedFields(None, test_data)

        self.fieldpack.format_table = dict(
                    zero    = ( '<I', 0),   # 0-3
                    two     = ( '<c', 2),
                    four    = ( '<?', 4),
                    five    = ( '<c', 5),
                    six     = ( '<c', 6),
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


class TestPacket(unittest.TestCase,TestUtil):

    def setUp(self):
        pcap = pcapy.open_offline(test_data('usb-single-packet-2.pcap'))
        self.packet = Packet(*pcap.next())

        self.set_and_test = partial(self.setattr_and_test, self.packet)

        # Long name, but not as long as without it
        self.assertRaisesWrongPacketXferType = partial(self.assertRaises,
                WrongPacketXferType, getattr, self.packet)

        # Verify that we have the right test data
        self.assertEqual(self.packet.length, 40, 'unmodified packet wrong--test bad?')
        self.assertEqual(self.packet.busnum, 7, 'unmodified packet wrong--test bad?')

    #def test_fail(self): self.fail('Fail works as expected')

    def test_urb(self):
        self.assertEqual(self.packet.urb, 0x00000000ef98ef00, 'Unmodified URB')

        self.set_and_test('urb', 0x00000000ef98ef01)
        self.set_and_test('urb', 0xffff0000ef98ef01)
        self.set_and_test('urb', 0)
        self.set_and_test('urb', 0xffffffffffffffff)

        # 2.6 raises TypeError; 2.7 struct.error
        if sys.version_info[0] == 2 and sys.version_info[1] >= 7:
            minus_one_exception = struct.error
        else:
            minus_one_exception = TypeError

        self.assertRaises(minus_one_exception, self.set_and_test, 'urb', -1)
        self.assertRaises(struct.error,         # Too large
                self.set_and_test,'urb', 0xffffffffffffffffff)

    def test_event_type(self):
        self.assertEqual(self.packet.event_type, 'S', 'Unmodified event_type')

        # "Normal" range of values
        self.set_and_test('event_type', 'C')    # Callback
        self.set_and_test('event_type', 'E')    # Error

        # Things that shouldn't be -- perhaps these should be errors?
        self.set_and_test('event_type', chr(0x00))
        self.set_and_test('event_type', chr(0xFF))

    def test_xfer_type(self):
        self.assertEqual(self.packet.xfer_type, 2, 'Unmodified xfer_type')
        self.set_and_test('xfer_type', 0, 'Isoc xfer type')
        self.set_and_test('xfer_type', 1, 'Interrupt xfer type')
        self.set_and_test('xfer_type', 2, 'Control xfer type')
        self.set_and_test('xfer_type', 3, 'Bulk xfer type')

    # Might be good to test all permutations
    def test_xfer_type_tests(self):
        self.failIf(self.packet.is_isochronous_xfer(), 'Not isoc xfer')
        self.failIf(self.packet.is_bulk_xfer(), 'Not bulk xfer')
        self.failUnless(self.packet.is_control_xfer(), 'Is control xfer')
        self.failIf(self.packet.is_interrupt_xfer(), 'Not interrupt xfer')

    def test_epnum(self):
        self.assertEqual(self.packet.epnum, 0x80, 'Unmodified epnum')

    def test_devnum(self):
        self.assertEqual(self.packet.devnum, 3, 'Unmodified devnum')

    def test_busnum(self):
        self.assertEqual(self.packet.busnum, 7, 'Unmodified busnum')

    def test_flag_setup(self):
        self.assertEqual(self.packet.flag_setup, '\x00', 'Unmodified flag_setup')

    def test_flag_data(self):
        self.assertEqual(self.packet.flag_data, '<', 'Unmodified flag_data')

    def test_ts_sec(self):
        self.assertEqual(self.packet.ts_sec, 1309208916, 'Unmodified ts_sec')

    def test_ts_usec(self):
        self.assertEqual(self.packet.ts_usec, 397516, 'Unmodified ts_usec')

    def test_status(self):
        self.assertEqual(self.packet.status, -115, 'Unmodified status')

    def test_length(self):
        self.assertEqual(self.packet.length, 40, 'Unmodified length')
        self.set_and_test('length', 99)

    def test_len_cap(self):
        self.assertEqual(self.packet.len_cap, 0, 'Unmodified len_cap')

    def test_setup(self):
        pass

    # Skipping tests is not supported until 2.7
    if PYTHON_2_7_PLUS:
        @unittest.skip('Exception not yet implemented')
        def test_error_count(self):
            self.assertRaisesWrongPacketXferType('error_count')

        @unittest.skip('Exception not yet implemented')
        def test_numdesc(self):
            self.assertRaisesWrongPacketXferType('numdesc')

        @unittest.skip('Exception not yet implemented')
        def test_interval(self):
            self.assertRaisesWrongPacketXferType('interval')

        @unittest.skip('Exception not yet implemented')
        def test_start_frame(self):
            self.assertRaisesWrongPacketXferType('start_frame')

    def test_xfer_flags(self):
        self.assertEqual(self.packet.xfer_flags, 0x200, 'Unmodified xfer_flags')

    # FIXME Should this be an xfer_type = isoc only attribute also?
    def test_ndesc(self):
        self.assertEqual(self.packet.ndesc, 0, 'Unmodified ndesc')

    def test_data(self):
        self.assertEqual(self.packet.data, [], 'Unmodified data')
        self.assertEqual(self.packet.datalen, 0, 'Unmodified datalen')

        # As implemented, appending to data does not work, even though it appears to.
        self.packet.data.append(0)
        self.assertEqual(self.packet.data, [0], 'Modified data[0] = 0')
        #self.assertEqual(self.packet.datalen, 1, 'Modified datalen')

        self.packet.data[0] = 0xff
        self.assertEqual(self.packet.data, [0xff], 'Modified data[0] = 0xff')

    def test_copy(self):
        packet2 = self.packet.copy()

        self.assertNotEqual(id(packet2), id(self.packet))
        self.assertNotEqual(id(packet2.data), id(self.packet.data))

        packet2.urb = 0xff
        self.assertNotEqual(packet2.urb, self.packet.urb)

class TestPacketData(unittest.TestCase,TestUtil):

    def setUp(self):
        pcap = pcapy.open_offline(test_data('usb-single-packet-8bytes-data.pcap'))
        self.packet = Packet(*pcap.next())

    def test_data(self):
        self.assertEqual(self.packet.data, [1, 0, 6, 0, 0, 0, 0, 0],
                            'Unmodified data')
        self.assertEqual(self.packet.datalen, 8,
                            'datalen of unmodified data')
        self.assertEqual(self.packet.datalen, len(self.packet.data),
                            'len of Packet.data')

        self.packet.data[0] = 0xff
        self.assertEqual(self.packet.data, [0xff, 0, 6, 0, 0, 0, 0, 0],
                            'Modified data[0] = 0xff')

        self.packet.data[-1] = 0xff
        self.assertEqual(self.packet.repack()[-1], chr(0xff),
                            'repack modified data')

    def test_copy(self):
        packet2 = self.packet.copy()

        self.assertNotEqual(id(packet2), id(self.packet))
        self.assertNotEqual(id(packet2.data), id(self.packet.data))

        packet2.urb = 0xff
        self.assertNotEqual(packet2.urb, self.packet.urb)

        packet2.data[0] = 0xbb
        self.assertNotEqual(packet2.data, self.packet.data)

class TestSetupField(unittest.TestCase,TestUtil):

    def setUp(self):
        pcap = pcapy.open_offline(test_data('usb-single-packet-2.pcap'))
        self.packet = Packet(*pcap.next())
        self.setup = self.packet.setup
        self.set_and_test = partial(self.setattr_and_test, self.packet.setup)

    def test_bmrequest_type(self):
        self.assertEqual(self.setup.bmRequestType, 0b10000000)
        self.set_and_test('bmRequestType', 0b00000000)
        self.set_and_test('bmRequestType', 0b11111111)

    def test_bmrequest_type_direction(self):
        self.assertEqual(self.setup.bmRequestTypeDirection, 'device_to_host')

    if PYTHON_2_7_PLUS:
        @unittest.skip('Setter not yet implemented')
        def test_bmrequest_type_direction_write(self):
            self.assertEqual(self.setup.bmRequestTypeDirection, 'device_to_host')
            self.set_and_test('bmRequestTypeDirection', 'host_to_device')
            self.set_and_test('bmRequestTypeDirection', 'device_to_host')

    def test_bmrequest_type_type(self):
        self.assertEqual(self.setup.bmRequestTypeType, 'standard')
        self.assertEqual(REQUEST_TYPE_TYPE[self.setup.bmRequestTypeType],
                         REQUEST_TYPE_TYPE['standard'])
    if PYTHON_2_7_PLUS:
        @unittest.skip('Setter not yet implemented')
        def test_bmrequest_type_type_write(self):
            self.set_and_test('bmRequestTypeType', 'class_')
            self.set_and_test('bmRequestTypeType', 'vendor')
            self.set_and_test('bmRequestTypeType', 'reserved')
            self.set_and_test('bmRequestTypeType', 'standard')

    def test_bmrequest_type_recipient(self):
        self.assertEqual(self.setup.bmRequestTypeRecipient, 'device')

    if PYTHON_2_7_PLUS:
        @unittest.skip('Setting not yet implemented')
        def test_bmrequest_type_recipient_write(self):
            self.set_and_test('bmRequestTypeRecipient', 'interface')
            self.set_and_test('bmRequestTypeRecipient', 'endpoint')
            self.set_and_test('bmRequestTypeRecipient', 'other')

    def test_brequest(self):
        self.assertEqual(self.setup.bRequest,
                        SETUP_REQUEST_TYPES['GET_DESCRIPTOR'])
        self.assertEqual(SETUP_REQUEST_TYPES[self.setup.bRequest],
                        'GET_DESCRIPTOR')

    #def test_wValue(self):
        #self.assertEqual(self.setup.wValue, 'DEVICE')

if __name__ == '__main__':
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    suite.addTest(loader.loadTestsFromTestCase(TestPackedFields))
    suite.addTest(loader.loadTestsFromTestCase(TestPacket))
    suite.addTest(loader.loadTestsFromTestCase(TestPacketData))
    suite.addTest(loader.loadTestsFromTestCase(TestSetupField))
    unittest.TextTestRunner(verbosity=2).run(suite)
