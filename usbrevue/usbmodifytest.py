"""Unit test for usbmodify.py"""

from __future__ import division

import pcapy
import usbmodify
from usbrevue import Packet
import unittest
import struct

class ModAttrsByRoutineFile(unittest.TestCase):
    """Change each packet attribute to some value. All tests should
    pass.

    """
    
    pcap = pcapy.open_offline('usbmodifytestdump.pcap')
    modifier = usbmodify.Modifier('test_routine_file', '')


    def test_all(self):
        while True:
            (hdr, pack) = self.pcap.next()
            if hdr is None:
                break # EOF
            packet = Packet(hdr, pack)

            # for attr in packet.__dict__:
                # self.modify_by_file(attr, packet)

 
    def modify_by_file(self, attr, packet):
        f = open('test_routine_file', 'w')
        f.write(attr + ' = "a test string"')
        f.close()
        self.modifier.apply_routine_file(packet)
        self.assertEqual(getattr(packet, attr), "a test string")



class ModDataByExp(unittest.TestCase):
    """Change a data byte to a value based on two other data
    bytes. All tests should pass.

    """

    def packet_generator(self):
        pcap = pcapy.open_offline('usbmodifytestdump.pcap')
        
        while True:
            (hdr, pack) = pcap.next()
            if hdr is None:
                return # EOF
            yield Packet(hdr, pack)


    def test_add(self):
        modifier = usbmodify.Modifier('', ['data[0] = data[1] + data[2]'])
        
        for packet in self.packet_generator():
            modifier.apply_cmdline_exps(packet)
            if len(packet.data):
                self.assertEqual(packet.data[0], packet.data[1] + packet.data[2])


    def test_sub(self):
        modifier = usbmodify.Modifier('', ['data[0] = data[1] - data[2]'])
        
        for packet in self.packet_generator():
            modifier.apply_cmdline_exps(packet)
            if len(packet.data):
                self.assertEqual(packet.data[0], packet.data[1] - packet.data[2])


    def test_mult(self):
        pcap = pcapy.open_offline('usbmodifytestdump.pcap')
        modifier = usbmodify.Modifier('', ['data[0] = data[1] * data[2]'])
        
        while True:
            (hdr, pack) = pcap.next()
            if hdr is None:
                break # EOF
            packet = Packet(hdr, pack)

            modifier.apply_cmdline_exps(packet)
            if len(packet.data):
                self.assertEqual(packet.data[0], packet.data[1] * packet.data[2])


    def test_div(self):
        modifier = usbmodify.Modifier('', ['data[0] = data[1] / (data[2] + 1)'])
        
        for packet in self.packet_generator():
            modifier.apply_cmdline_exps(packet)
            if len(packet.data):
                self.assertEqual(packet.data[0], packet.data[1] / (packet.data[2] + 1))


    def test_bit_and(self):
        modifier = usbmodify.Modifier('', ['data[0] = data[1] & data[2]'])
        
        for packet in self.packet_generator():
            modifier.apply_cmdline_exps(packet)
            if len(packet.data):
                self.assertEqual(packet.data[0], packet.data[1] & packet.data[2])


    def test_bit_or(self):
        modifier = usbmodify.Modifier('', ['data[0] = data[1] | data[2]'])
        
        for packet in self.packet_generator():
            modifier.apply_cmdline_exps(packet)
            if len(packet.data):
                self.assertEqual(packet.data[0], packet.data[1] | packet.data[2])


    def test_bit_not(self):
        modifier = usbmodify.Modifier('', ['data[0] = ~ data[1]'])
        
        for packet in self.packet_generator():
            modifier.apply_cmdline_exps(packet)
            if len(packet.data):
                self.assertEqual(packet.data[0], ~ packet.data[1])


    def test_bit_xor(self):
        modifier = usbmodify.Modifier('', ['data[0] = data[1] ^ data[2]'])
        
        for packet in self.packet_generator():
            modifier.apply_cmdline_exps(packet)
            if len(packet.data):
                self.assertEqual(packet.data[0], packet.data[1] ^ packet.data[2])


    def test_logical_and(self):
        modifier = usbmodify.Modifier('', ['data[0] = data[1] and data[2]'])
        
        for packet in self.packet_generator():
            modifier.apply_cmdline_exps(packet)
            if len(packet.data):
                self.assertEqual(packet.data[0], packet.data[1] and packet.data[2])


    def test_logical_or(self):
        modifier = usbmodify.Modifier('', ['data[0] = data[1] or data[2]'])
        
        for packet in self.packet_generator():
            modifier.apply_cmdline_exps(packet)
            if len(packet.data):
                self.assertEqual(packet.data[0], packet.data[1] or packet.data[2])


    def test_logical_not(self):
        modifier = usbmodify.Modifier('', ['data[0] = not data[1]'])
        
        for packet in self.packet_generator():
            modifier.apply_cmdline_exps(packet)
            if len(packet.data):
                self.assertEqual(packet.data[0], not packet.data[1])


    def test_logical_xor(self):
        modifier = usbmodify.Modifier('', ['data[0] = bool(data[1]) ^ bool(data[2])'])
        
        for packet in self.packet_generator():
            modifier.apply_cmdline_exps(packet)
            if len(packet.data):
                self.assertEqual(packet.data[0], bool(packet.data[1]) ^ bool(packet.data[2]))



class BadData(unittest.TestCase):
    """Check that invalid attribute values will be rejected."""

    modifier = usbmodify.Modifier('test_routine_file', '')

    def test_bad_id(self):
        f = open('test_routine_file', 'w')
        f.write('urb = 100 ** 100')
        f.close()
        
        for packet in packet_generator():
            self.modifier.apply_routine_file(packet)
            self.assertRaises(ValueError, self.modifier.check_valid_data, packet)


    def test_bad_type(self):
        f = open('test_routine_file', 'w')
        f.write('event_type = "XX"')
        f.close()

        for packet in packet_generator():
            self.modifier.apply_routine_file(packet)
            self.assertRaises(ValueError, self.modifier.check_valid_data, packet)



def packet_generator():
    pcap = pcapy.open_offline('usbmodifytestdump.pcap')
    
    while True:
        (hdr, pack) = pcap.next()
        if hdr is None:
            return # EOF
        yield Packet(hdr, pack)





if __name__ == "__main__":
    unittest.main()
