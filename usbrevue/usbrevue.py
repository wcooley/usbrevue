#!/usr/bin/env python
import sys

from struct import unpack_from
import datetime

USBMON_PACKET_FORMAT = dict(
    # Attr        fmt     offset
    urb         = ('=Q',  0),
    type_       = ('=c',  8),
    xfer_type   = ('=B',  9),
    epnum       = ('=B',  10),
    devnum      = ('=B',  11),
    busnum      = ('=H',  12),
    flag_setup  = ('=c',  14),
    flag_data   = ('=c',  15),
    ts_sec      = ('=q',  16),
    ts_usec     = ('=i',  24),
    status      = ('=i',  28),
    length      = ('=I',  32),
    len_cap     = ('=I',  36),
    setup       = ('=8B', 40),
    error_count = ('=i',  40),
    numdesc     = ('=i',  44),
    interval    = ('=i',  48),
    start_frame = ('=i',  52),
    xfer_flags  = ('=I',  56),
    ndesc       = ('=I',  60),
    data        = ('=%dB', 64),
)

# Note that the packet transfer type has different numeric identifiers then the
# endpoint control types in the Linux kernel headers <linux/usb/ch9.h>:
#define USB_ENDPOINT_XFER_CONTROL       0
#define USB_ENDPOINT_XFER_ISOC          1
#define USB_ENDPOINT_XFER_BULK          2
#define USB_ENDPOINT_XFER_INT           3
USBMON_TRANSFER_TYPE = dict(
    isochronous = 0,
    interrupt   = 1,
    control     = 2,
    bulk        = 3,
)

class Packet(object):

    def __init__(self, hdr=None, pack=None):

        if None not in (hdr, pack):
            if len(pack) < 64:
                raise RuntimeError("Not a USB Packet")

            self.__dict__['_hdr'], self.__dict__['_pack'] = hdr, pack

            if self.type_ not in ['C', 'S', 'E'] or \
                    self.xfer_type not in USBMON_TRANSFER_TYPE.values():
                raise RuntimeError("Not a USB Packet")

        self.__dict__['_cache'] = dict()

    # Generic attribute accessor
    # Note that we unpack the single item from the tuple in __getattr__ due to
    # setup()
    def unpacket(self, attr, fmtx=None):
        fmt, offset = USBMON_PACKET_FORMAT[attr]
        if fmtx != None: fmt %= fmtx
        return unpack_from(fmt, self._pack, offset)

    def __getattr__(self, attr):
        if self._cache.has_key(attr):
            return self._cache[attr]
        else:
            self.unpacket(attr)[0]

    def __setattr__(self, attr, val):
        raise NotImplementedError("setter %s = %s" % (attr, val))

    def get_field_dict(self):
        """Return a dict of attributes and values."""
        pdict = dict()

        for attr in USBMON_PACKET_FORMAT:
            pdict[attr] = getattr(self, attr)

        return pdict

    def get_fields(self):
        """Return a list of packet header fields"""
        return [ attr for attr in USBMON_PACKET_FORMAT ]

    @property
    def datalen(self):
        return len(self._pack) - 64

    # Special attribute accessors that have additional restrictions
    @property
    def data(self):
        return list(self.unpacket('data', self.datalen))

    @property
    def setup(self):
        # setup is only meaningful if flag_setup == 's'
        if self.flag_setup == 's':
            return list(self.unpacket('setup'))

    # error_count and numdesc are only meaningful for isochronous transfers
    # (xfer_type == 0)
    @property
    def error_count(self):
        if self.is_isochronous_xfer():
            return self.unpacket('error_count')[0]

    @property
    def numdesc(self):
        if self.is_isochronous_xfer():
            return self.unpacket('numdesc')[0]

    # interval is only meaningful for isochronous or interrupt transfers
    # (xfer_type in [0,1])
    @property
    def interval(self):
        if self.is_isochronous_xfer() or self.is_interrupt_xfer():
            return self.unpacket('interval')[0]

    @property
    def start_frame(self):
        # start_frame is only meaningful for isochronous transfers
        if self.is_isochronous_xfer():
            return self.unpacket('start_frame')[0]

    # Boolean tests for transfer types
    def is_isochronous_xfer(self):
        return self.xfer_type == USBMON_TRANSFER_TYPE['isochronous']

    def is_bulk_xfer(self):
        return self.xfer_type == USBMON_TRANSFER_TYPE['bulk']

    def is_control_xfer(self):
        return self.xfer_type == USBMON_TRANSFER_TYPE['control']

    def is_interrupt_xfer(self):
        return self.xfer_type == USBMON_TRANSFER_TYPE['interrupt']

    def copy(self):
        new_packet = Packet(self.hdr, self.pack)
        return new_packet


    def print_pcap_fields(self):
        """
        Print detailed packet information for debug purposes.
        Assumes header exists.
        """
        print "urb = %d" % (self.urb)
        print "type = %s" % (self.type)
        print "xfer_type = %d" % (self.xfer_type)
        print "epnum = %d" % (self.epnum)
        print "devnum = %d" % (self.devnum)
        print "busnum = %d" % (self.busnum)
        print "flag_setup = %s" % (self.flag_setup)
        print "flag_data = %s" % (self.flag_data)
        print "ts_sec = %d" % (self.ts_sec,)
        print "ts_usec = %d" % (self.ts_usec)
        print "status = %d" % (self.status)
        print "length = %d" % (self.length)
        print "len_cap = %d" % (self.len_cap)
        # setup is only meaningful if flag_setup == 's')
        if (self.flag_setup == 's'):
            print "setup = %d" % (self.setup)
        # error_count and numdesc are only meaningful for isochronous transfers
        # (xfer_type == 0)
        if (self.xfer_type == 0):
            print "error_count = %d" % (self.error_count)
            print "numdesc = %d" % (self.numdesc)
        # interval is only meaningful for isochronous or interrupt transfers)
        # (xfer_type in [0,1]))
        if (self.xfer_type in [0,1]):
            print "interval = %d" % (self.interval)
        # start_frame is only meaningful for isochronous transfers)
        if (self.xfer_type == 0):
            print "start_frame = %d" % (self.start_frame)
        print "xfer_flags = %d" % (self.xfer_flags)
        print "ndesc = %d" % (self.ndesc)
        # print "datalen = " % (datalen)
        # print "data = " % (self.data)
        print "data =", self.data
        # print "hdr = " % (self.hdr)
        print "hdr =", self.hdr
        # print "packet = " % (self.pack)


    def print_pcap_summary(self):
        """
        Print concise packet summary information for debug purposes.
        Assumes header exists.
        """
        print ('%s: Captured %d bytes, truncated to %d bytes' % (datetime.datetime.now(), self.hdr.getlen(), self.hdr.getcaplen()))


    def repack(self):
        """
        Returns a binary string of the packet information. Currently
        ignores changes to anything but data.
        """
        return self.pack[:64] + ''.join(map(chr, self.data))


if __name__ == '__main__':
    # read a pcap file from stdin, replace the first byte of any data found
    # with 0x42, and write the modified packets to stdout
    import pcapy
    pcap = pcapy.open_offline('-')
    out = pcap.dump_open('-')

    while 1:
        hdr, pack = pcap.next()
        if hdr is None:
            break # EOF
        p = Packet(hdr, pack)
        p.print_pcap_fields()
        p.print_pcap_summary()
        if len(p.data) > 0:
            p.data[0] = 0x42
        out.dump(hdr, p.repack())

