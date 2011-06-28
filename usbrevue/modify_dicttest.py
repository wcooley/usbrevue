#!/usr/bin/env python

import pcapy
from usbmodify import Modifier
from usbrevue import Packet

pcap = pcapy.open_offline('usbmodifytestdump.pcap')
modifier = Modifier(None, '', '')

while True:
    hdr, pack = pcap.next()
    if hdr is None:
        break

    packet = Packet(hdr, pack)

    # debug print
    # should be length = 40, 18, 8 or 4, busnum = 7
    print 'before exec, length = ', packet.length, ', busnum = ', packet.busnum

    # pass in __dict__ as local namespace and apply "id = 12345 + busnum" to each packet
    exec('length = 99', {}, packet.__dict__)

    # explicitly referencing the packet object on the left or right of
    # the statement works too if you pass in 'packet' as part of the
    # global namespace
    exec('packet.busnum = packet.busnum + 1', {'packet':packet}, packet.__dict__)
    exec('packet.busnum = busnum + 1', {'packet':packet}, packet.__dict__)
    exec('busnum = packet.busnum + 1', {'packet':packet}, packet.__dict__)


    # debug print
    # should be length = 99, busnum = 10
    print 'after exec, length =', packet.length, ', busnum = ', packet.busnum
