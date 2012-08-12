from array import array
from usbrevue import USBMonPacket

def modify(packet_gen, commit_func):
    packet_buf = []
    for packet in packet_gen('-'):
        for byte in packet.data:
            if byte >= 0x80:
                packet_template = USBMonPacket(packet.hdr, packet.datapack[:64] + array('c', ''.join(map(chr, packet_buf))))
                
                packet_template.length = len(packet_template.data)
                packet_template.len_cap = len(packet_template.data)

                commit_func(packet_template)
                packet_buf = []
                packet_buf.append(byte)
            else:
                packet_buf.append(byte)
