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

import logging
import os
import os.path
import struct
import sys
import unittest
from array import array
from functools import partial
from logging import debug
from pprint import pformat

import pcapy

from tutil import *
from usbrevue import *
from util import apply_mask

#logging.basicConfig(level=logging.DEBUG)

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

        fp2 = PackedFields(fmt_table, self.fieldpack.six,
                    partial(_update_six, self.fieldpack))
        fp2.six2 = 'D'

        self.assertEqual(fp2.six2, 'D')
        self.assertEqual(fp2.six2, self.fieldpack.seven)
        self.assertEqual(self.fieldpack.seven, 'D')


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
        self.failIf(self.packet.is_isochronous_xfer, 'Not isoc xfer')
        self.failIf(self.packet.is_bulk_xfer, 'Not bulk xfer')
        self.failUnless(self.packet.is_control_xfer, 'Is control xfer')
        self.failIf(self.packet.is_interrupt_xfer, 'Not interrupt xfer')

    def test_is_setup_packet(self):
        self.failUnless(self.packet.is_setup_packet, 'Is setup packet')

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

    def test_diff_identity(self):
        """Identity: Diff returns empty-list when comparing with itself."""

        self.assertEqual(self.packet.diff(self.packet), list())

    def test_diff_copy(self):
        """Identity-ish: Diff returns empty-list when comparing with copy of itself."""
        self.assertEqual(self.packet.diff(self.packet.copy()), list())

    def test_diff_setup(self):
        """Diff where only setup sub-field has been changed"""

        packet2 = self.packet.copy()
        packet2.setup.bmRequestTypeType = 'reserved'

        # Ensure that the original isn't 'reserved'
        self.assertNotEqual(self.packet.setup.bmRequestTypeType, 'reserved')

        self.assertNotEqual(self.packet.diff(packet2), list())

    def test_diff(self):
        packet2 = self.packet.copy()
        packet2.urb = 0xff

        self.assertNotEqual(self.packet.diff(packet2), ())

    def test_eq_identity(self):
        """Eq: True with itself"""

        self.assertTrue(self.packet == self.packet)

    def test_eq_copy(self):
        """Eq: True with unmodified copy"""

        packet2 = self.packet.copy()
        self.assertTrue(self.packet == packet2)

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

    def test_bmrequest_type_direction_host_to_device(self):
        self.setup.bmRequestType = apply_mask(
                                    REQUEST_TYPE_MASK['direction'],
                                    self.setup.bmRequestType,
                                    REQUEST_TYPE_DIRECTION['host_to_device'])
        self.assertEqual(self.setup.bmRequestTypeDirection, 'host_to_device')

    def test_bmrequest_type_direction_write(self):
        self.assertEqual(self.setup.bmRequestTypeDirection, 'device_to_host')
        self.set_and_test('bmRequestTypeDirection', 'host_to_device')
        self.set_and_test('bmRequestTypeDirection', 'device_to_host')

    def test_bmrequest_type_type(self):
        self.assertEqual(self.setup.bmRequestTypeType, 'standard')
        self.assertEqual(REQUEST_TYPE_TYPE[self.setup.bmRequestTypeType],
                         REQUEST_TYPE_TYPE['standard'])

    def test_bmrequest_type_type_class_(self):
        self.set_and_test('bmRequestTypeType', 'class_')

    def test_bmrequest_type_type_vendor(self):
        self.set_and_test('bmRequestTypeType', 'vendor')

    def test_bmrequest_type_type_reserved(self):
        self.set_and_test('bmRequestTypeType', 'reserved')

    def test_bmrequest_type_type_standard(self):
        self.set_and_test('bmRequestTypeType', 'standard')

    def test_bmrequest_type_recipient(self):
        self.assertEqual(self.setup.bmRequestTypeRecipient, 'device')

    def test_bmrequest_type_recipient_interface(self):
        self.set_and_test('bmRequestTypeRecipient', 'interface')

    def test_bmrequest_type_recipient_endpoint(self):
        self.set_and_test('bmRequestTypeRecipient', 'endpoint')

    def test_bmrequest_type_recipient_other(self):
        self.set_and_test('bmRequestTypeRecipient', 'other')

    def test_brequest_GET_DESCRIPTOR(self):
        # GET_DESCRIPTOR is in the test packet, so we only assertEqual instead
        # of set_and_test
        self.assertEqual(self.setup.bRequest,
                        SETUP_REQUEST_TYPES['GET_DESCRIPTOR'])
        self.assertEqual(SETUP_REQUEST_TYPES[self.setup.bRequest],
                         'GET_DESCRIPTOR')
        self.assertEqual(self.setup.bRequest_str, 'GET_DESCRIPTOR')

    def test_brequest_GET_STATUS(self):
        self.set_and_test('bRequest', SETUP_REQUEST_TYPES['GET_STATUS'])
        self.assertEqual(self.setup.bRequest,
                            SETUP_REQUEST_TYPES['GET_STATUS'])

    def test_brequest_CLEAR_FEATURE(self):
        self.set_and_test('bRequest', SETUP_REQUEST_TYPES['CLEAR_FEATURE'])
        self.assertEqual(self.setup.bRequest,
                            SETUP_REQUEST_TYPES['CLEAR_FEATURE'])

    def test_brequest_SET_FEATURE(self):
        self.set_and_test('bRequest', SETUP_REQUEST_TYPES['SET_FEATURE'])
        self.assertEqual(self.setup.bRequest,
                            SETUP_REQUEST_TYPES['SET_FEATURE'])

    def test_brequest_SET_ADDRESS(self):
        self.set_and_test('bRequest', SETUP_REQUEST_TYPES['SET_ADDRESS'])
        self.assertEqual(self.setup.bRequest,
                            SETUP_REQUEST_TYPES['SET_ADDRESS'])

    def test_brequest_SET_DESCRIPTOR(self):
        self.set_and_test('bRequest', SETUP_REQUEST_TYPES['SET_DESCRIPTOR'])
        self.assertEqual(self.setup.bRequest,
                            SETUP_REQUEST_TYPES['SET_DESCRIPTOR'])

    def test_brequest_GET_CONFIGURATION(self):
        self.set_and_test('bRequest', SETUP_REQUEST_TYPES['GET_CONFIGURATION'])
        self.assertEqual(self.setup.bRequest,
                            SETUP_REQUEST_TYPES['GET_CONFIGURATION'])

    def test_brequest_SET_CONFIGURATION(self):
        self.set_and_test('bRequest', SETUP_REQUEST_TYPES['SET_CONFIGURATION'])
        self.assertEqual(self.setup.bRequest,
                            SETUP_REQUEST_TYPES['SET_CONFIGURATION'])

    def test_brequest_GET_INTERFACE(self):
        self.set_and_test('bRequest', SETUP_REQUEST_TYPES['GET_INTERFACE'])
        self.assertEqual(self.setup.bRequest,
                            SETUP_REQUEST_TYPES['GET_INTERFACE'])

    def test_brequest_SET_INTERFACE(self):
        self.set_and_test('bRequest', SETUP_REQUEST_TYPES['SET_INTERFACE'])
        self.assertEqual(self.setup.bRequest,
                            SETUP_REQUEST_TYPES['SET_INTERFACE'])

    def test_brequest_SYNCH_FRAME(self):
        self.set_and_test('bRequest', SETUP_REQUEST_TYPES['SYNCH_FRAME'])
        self.assertEqual(self.setup.bRequest,
                            SETUP_REQUEST_TYPES['SYNCH_FRAME'])

    def test_brequest_unknown(self):
        self.setup.bRequest = 254   # Reported in the wild
        self.assertEqual(self.setup.bRequest_str, 'unknown')

    def test_wValue(self):
        self.assertEqual(self.setup.wValue, 0b100000000)

    def test_wIndex(self):
        self.assertEqual(self.setup.wIndex, 0x0)

    def test_wLength(self):
        self.assertEqual(self.setup.wLength, 0x28)

class TestSetupFieldPropagation(unittest.TestCase,TestUtil):
    def setUp(self):
        pcap = pcapy.open_offline(test_data('usb-single-packet-2.pcap'))
        self.packet = Packet(*pcap.next())

    def test_packet_manual_unpack(self):
        packet_setup = unpack_from('=8s', self.packet.datapack, 40)[0]
        datapack = self.packet.setup.datapack.tostring()
        self.assertEqual(packet_setup, datapack)

    def test_packet_write_bmrequest_type_direction(self):
        #"""Set bmRequestType direction bitfield and test copy"""
        d = 'host_to_device'
        self.packet.setup.bmRequestTypeDirection = d
        self.assertEqual(self.packet.setup.bmRequestTypeDirection, d)

        packet2 = self.packet.copy()
        self.assertEqual(packet2.setup.bmRequestTypeDirection, d)

    def test_packet_write_bmrequest_type_type(self):
        #"""Set bmRequestType type bitfield and test copy"""
        t = 'vendor'
        self.packet.setup.bmRequestTypeType = t
        self.assertEqual(self.packet.setup.bmRequestTypeType, t)

        packet2 = self.packet.copy()
        self.assertEqual(packet2.setup.bmRequestTypeType, t)

    def test_packet_write_bmrequest_type_recipient(self):
        #"""Set bmRequestType recipient bitfield and test copy"""
        r = 'endpoint'
        self.packet.setup.bmRequestTypeRecipient = r
        self.assertEqual(self.packet.setup.bmRequestTypeRecipient, r)

        packet2 = self.packet.copy()
        self.assertEqual(packet2.setup.bmRequestTypeRecipient, r)

if __name__ == '__main__':
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    suite.addTest(loader.loadTestsFromTestCase(TestPackedFields))
    suite.addTest(loader.loadTestsFromTestCase(TestPacket))
    suite.addTest(loader.loadTestsFromTestCase(TestPacketData))
    suite.addTest(loader.loadTestsFromTestCase(TestSetupField))
    suite.addTest(loader.loadTestsFromTestCase(TestSetupFieldPropagation))
    unittest.TextTestRunner(verbosity=2).run(suite)
