"""Unit test for usbmodify.py"""

import pcapy
import usbmodify
from usbrevue import Packet
import unittest

class ModFieldsByRoutineFile(unittest.TestCase):
    """Change each packet routine to some value. All tests should
    pass.

    """
    
    pcap = pcapy.open_offline('usbmodifytestdump.pcap')
    modifier = usbmodify.Modifier(pcap, 'test_routine_file', 'test_cmd_exps')


    def test_all(self):
        while True:
            (hdr, pack) = self.pcap.next()
            if hdr is None:
                break # EOF
            packet = Packet(hdr, pack)

            self.modify_id(packet)
            self.modify_type(packet)


    def modify_id(self, packet):
        f = open('test_routine_file', 'w')
        f.write('id = 12345')
        f.close()
        self.modifier.apply_routine_file(packet)
        self.assertEqual(packet.id, 12345)

    
    def modify_type(self, packet):
        f = open('test_routine_file', 'w')
        f.write('type = "E"')
        f.close()
        self.modifier.apply_routine_file(packet)
        self.assertEqual(packet.type, 'E')



if __name__ == "__main__":
    unittest.main()
