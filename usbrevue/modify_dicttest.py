#!/usr/bin/env python

import unittest

import pcapy
from usbmodify import Modifier
from usbrevue import Packet

class TestPacketModifier(unittest.TestCase):

    def setUp(self):
        self.packet = Packet(*pcapy.open_offline('../test-data/usb-single-packet.pcap').next())

        # Verify that we have the right test data
        self.assertEqual(self.packet.length, 40, 'unmodified packet wrong--test bad?')
        self.assertEqual(self.packet.busnum, 7, 'unmodified packet wrong--test bad?')

    def test_length(self):
        packet = self.packet

        exec('length = 99', {}, packet.__dict__)
        self.assertEqual(packet.length, 99, 'length = 99')

    def test_busnum1(self):
        packet = self.packet

        self.assertEqual(packet.busnum, 7)
        exec('packet.busnum = packet.busnum + 1', {'packet':packet}, packet)
        self.assertEqual(packet.busnum, 8)

    def test_busnum2(self):
        packet = self.packet

        self.assertEqual(packet.busnum, 7)
        exec('packet.busnum = busnum + 1', {'packet':packet}, packet)
        self.assertEqual(packet.busnum, 8)

    def test_busnum3(self):
        packet = self.packet

        self.assertEqual(packet.busnum, 7)
        exec('busnum = packet.busnum + 1', {'packet':packet}, packet)

    def test_busnum4(self):
        packet = self.packet

        self.assertEqual(packet.busnum, 7)
        exec('busnum = busnum + 1', {'packet':packet}, packet)
        self.assertEqual(packet.busnum, 8)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPacketModifier)
    unittest.TextTestRunner(verbosity=2).run(suite)
