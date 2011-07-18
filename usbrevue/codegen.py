#!/usr/bin/env python
from usbrevue import *

def packet_to_libusb_code(pack):
    """
    Convert a captured USB packet into the libusb C code that would
    replicate it. Currently assumes:
        a) 'handle' is a valid libusb device handle
        b) 'data' is a char array large enough for any incoming data
        c) 'TIMEOUT' is a constant or int
        d) 'err' and 'n_transferred' are ints
        e) 'handle_error()' is defined, and takes an int
    """
    if pack.event_type != 'S':
        return ''
    if pack.is_control_xfer:
        data = 'data'
        if pack.setup.bmRequestTypeDirection == 'host_to_device':
            data = '"%s"' % ''.join(map(lambda x: "\\x%02x" % x, pack.data))
        return 'if ((err = libusb_control_transfer(handle, 0x%02x, 0x%x, 0x%x, 0x%x, %s, %s, TIMEOUT)) < 0)\n\thandle_error(err);\n' % (
                pack.setup.bmRequestType,
                pack.setup.bRequest,
                pack.setup.wValue,
                pack.setup.wIndex,
                data,
                pack.length)
    if pack.is_bulk_xfer or pack.is_interrupt_xfer:
        data = 'data'
        if pack.epnum & 0x80 == 0:
            data = '"%s"' % ''.join(map(lambda x: "\\x%02x" % x, pack.data))
        return 'if ((err = libusb_%s_transfer(handle, 0x%02x, %s, %s, &n_transferred, TIMEOUT)) < 0)\n\thandle_error(err);\n' % (
                'bulk' if pack.is_bulk_xfer else 'interrupt',
                pack.epnum,
                data,
                pack.length)
    if pack.is_isochronous_xfer:
        return '/* unsupported isochronous transfer */\n'
    return '/* unsupported transfer */\n'



if __name__ == '__main__':
    import pcapy
    import sys
    pcap = pcapy.open_offline(sys.argv[1])
    while 1:
        h, p = pcap.next();
        if h is None: break
        pack = Packet(h,p)
        sys.stdout.write(packet_to_libusb_code(pack))
                


