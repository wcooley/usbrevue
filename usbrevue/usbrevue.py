#!/usr/bin/env python
import sys

from array import array
from collections import MutableSequence, Sequence
from pprint import pprint, pformat
from struct import unpack_from, pack_into
import datetime

from util import reverse_update_dict

USBMON_PACKET_FORMAT = dict(
    # Attr        fmt     offset
    urb         = ('=Q',  0),
    event_type  = ('=c',  8),
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
    setup       = ('=8s', 40),
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
#define USB_ENDPOINT_XFER_CONTROL       1
#define USB_ENDPOINT_XFER_ISOC          1
#define USB_ENDPOINT_XFER_BULK          2
#define USB_ENDPOINT_XFER_INT           3
USBMON_TRANSFER_TYPE = dict(
    isochronous = 0,
    interrupt   = 1,
    control     = 2,
    bulk        = 3,
)

# Add the reverse to the dict for convenience
reverse_update_dict(USBMON_TRANSFER_TYPE)

class PackedFields(object):
    """Base class for field decodings/unpacking."""

    # This must exist so __setattr__ can find key 'format_table' missing from
    # self.format_table when it is being initialized.
    format_table = dict()

    def __init__(self, format_table=None, datapack=None):
        self._cache = dict()

        if format_table != None:
            self.format_table = format_table

        self.datapack = datapack

    def cache(self, attr, lookup_func):
        if not self._cache.has_key(attr):
            self._cache[attr] = lookup_func(attr)
        return self._cache[attr]

    # Generic attribute accessor
    # Note that we unpack the single item from the tuple in __getattr__ due to
    # setup()
    def unpacket(self, attr, fmtx=None):
        """Unpack attr from self.datapack using (struct) format string and
        offset from self.format_table. fmtx can be used to provide additional
        data for string-formatting that may be in the format string.

        Returns the tuple of data as from struct.unpack_from."""
        fmt, offset = self.format_table[attr]
        if fmtx != None: fmt %= fmtx
        return unpack_from(fmt, self.datapack, offset)

    def __getattr__(self, attr):
        """Pull attr from cache, looking it up with unpacket if necessary."""
        return self.cache(attr, lambda a: self.unpacket(a)[0])

    def repacket(self, attr, vals, fmtx=None):
        """Repack attr into self.datapack using (struct) format string and
        offset from self.format_table. fmtx can be used to provide additional
        data for string-formatting that may be in the format string."""
        fmt, offset = self.format_table[attr]
        if fmtx != None: fmt %= fmtx
        return pack_into(fmt, self.datapack, offset, *vals)

    def __setattr__(self, attr, val):
        # __setattr__ is more complicated than __getattr__ because it is
        # called even for existing attributes, whereas __getattr__ is not. Since
        # the attributes in self.format_table are the only ones that we want to
        # dynamically update, we explicitly check for those and otherwise call up
        # to object's __setattr__ which handles "regular" attributes (including
        # properties) as expected.
        """Dynamically update attributes in self.format_table, otherwise call
        up to object's version."""
        if attr in self.format_table:
            self._cache[attr] = val
            self.repacket(attr, [val])
        else:
            # This makes properties and non-format_table attributes work
            object.__setattr__(self, attr, val)

    # Implementing __getitem__ and __setitem__ permit the object to be used as
    # a mapping type, so it can be used as e.g. the global or local namespace
    # with 'eval'.
    def __getitem__(self, attr):
        return getattr(self, attr)

    def __setitem__(self, attr, val):
        setattr(self, attr, val)

    @property
    def datapack(self):
        """Holds the mutable sequence type (probably array) containing the data
        which is packed into or unpacked from."""
        return self.__dict__['datapack']

    @datapack.setter
    def datapack(self, value):
        if isinstance(value, Sequence) and \
                not isinstance(value, MutableSequence):
            self.__dict__['datapack'] = array('c', value)
        else:
            self.__dict__['datapack'] = value

    def repack(self):
        """
        Returns a binary string of the packet information.
        """
        return self.datapack.tostring()


class Packet(PackedFields):

    def __init__(self, hdr=None, pack=None):
        super(Packet, self).__init__()
        self.format_table = USBMON_PACKET_FORMAT

        if None not in (hdr, pack):
            if len(pack) < 64:
                raise RuntimeError("Not a USB Packet")

            self._hdr = hdr
            self.datapack = array('c', pack)

            if self.event_type not in ['C', 'S', 'E'] or \
                    self.xfer_type not in USBMON_TRANSFER_TYPE.values():
                raise RuntimeError("Not a USB Packet")

    @property
    def hdr(self):
        return self._hdr

    def diff(self, other):
        """Compare self with other packet.

        Return list of 3-tuples of (attr, my_val, other_val)."""

        result = list()

        for f in self.fields:
            m = getattr(self, f)
            o = getattr(other, f)

            if m != o:
                result.append((f, m, o))

        return result

    @property
    def field_dict(self):
        """Return a dict of attributes and values."""
        pdict = dict()

        for attr in USBMON_PACKET_FORMAT:
            pdict[attr] = getattr(self, attr)

        return pdict

    @property
    def fields(self):
        """Return a list of packet header fields"""
        return [ attr for attr in USBMON_PACKET_FORMAT ]

    @property
    def datalen(self):
        return len(self.datapack) - 64

    # Special attribute accessors that have additional restrictions
    @property
    def data(self):
        return self.cache('data',
                lambda a: list(self.unpacket(a, self.datalen)))

    def repack(self):
        self.repacket('data', self.data, self.datalen)
        return super(Packet, self).repack()

    @property
    def setup(self):
        # setup is only meaningful if flag_setup == '\x00'
        # NB: The usbmon doc says flag_setup should be 's' but that seems to be
        # only for the text interface, because is seems to be 0x00 and
        # Wireshark agrees.
        if self.flag_setup == '\x00':
            return self.cache('setup', lambda a: SetupField(self.unpacket(a)[0]))

    # error_count and numdesc are only meaningful for isochronous transfers
    # (xfer_type == 0)
    @property
    def error_count(self):
        if self.is_isochronous_xfer():
            return self.cache('error_count', lambda a: self.unpacket(a)[0])
        else:
            return 0

    @property
    def numdesc(self):
        if self.is_isochronous_xfer():
            return self.cache('numdesc', lambda a: self.unpacket(a)[0])
        else:
            return 0

    # interval is only meaningful for isochronous or interrupt transfers
    # (xfer_type in [0,1])
    @property
    def interval(self):
        if self.is_isochronous_xfer() or self.is_interrupt_xfer():
            return self.cache('interval', lambda a: self.unpacket(a)[0])
        else:
            return 0

    @property
    def start_frame(self):
        # start_frame is only meaningful for isochronous transfers
        if self.is_isochronous_xfer():
            return self.cache('start_frame', lambda a: self.unpacket(a)[0])
        else:
            return 0

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
        new_packet = Packet(self.hdr, self.datapack)
        return new_packet


    def print_pcap_fields(self):
        """
        Print detailed packet information for debug purposes.
        Assumes header exists.
        """
        print "urb = %d" % (self.urb)
        print "event_type = %s" % (self.event_type)
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
        if self.flag_setup == 's':
            print "setup = %d" % (self.setup)
        # error_count and numdesc are only meaningful for isochronous transfers
        # (xfer_type == 0)
        #if (self.xfer_type == 0):
        if self.is_isochronous_xfer():
            print "error_count = %d" % (self.error_count)
            print "numdesc = %d" % (self.numdesc)
        # interval is only meaningful for isochronous or interrupt transfers)
        # (xfer_type in [0,1]))
        #if (self.xfer_type in [0,1]):
        if self.is_isochronous_xfer() or self.is_interrupt_xfer():
            print "interval = %d" % (self.interval)
        # start_frame is only meaningful for isochronous transfers)
        if self.is_isochronous_xfer():
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
        print ('%s: Captured %d bytes, truncated to %d bytes' % (
                datetime.datetime.now(), self.hdr.getlen(),
                self.hdr.getcaplen()))


SETUP_FIELD_FORMAT = dict(
        bmRequestType   =   ('=B',  0),
        bRequest        =   ('=B',  1),
        wValue          =   ('=H',  2),
        wIndex          =   ('=H',  4),
        wLength         =   ('=H',  6),
)

# bRequest values (with particular pmRequestType values)
SETUP_REQUEST_TYPES = dict(
        GET_STATUS          = 0x00,
        CLEAR_FEATURE       = 0x01,
        # Reserved          = 0x02,
        SET_FEATURE         = 0x03,
        # Reserved          = 0x04,
        SET_ADDRESS         = 0x05,
        GET_DESCRIPTOR      = 0x06,
        SET_DESCRIPTOR      = 0x07,
        GET_CONFIGURATION   = 0x08,
        SET_CONFIGURATION   = 0x09,
        GET_INTERFACE       = 0x0A,
        SET_INTERFACE       = 0x0B,
        SYNCH_FRAME         = 0x0C,
        # Reserved          = 0x0D,
        # ...               = 0xFF,
)
reverse_update_dict(SETUP_REQUEST_TYPES)

REQUEST_TYPE_DIRECTION = dict(
                            #-> 7_______
        device_to_host      = 0b10000000,
        host_to_device      = 0b00000000,
)
reverse_update_dict(REQUEST_TYPE_DIRECTION)

REQUEST_TYPE_TYPE = dict(
                    #-> _65_____
        standard    = 0b00000000,
        class_      = 0b00100000,
        vendor      = 0b01000000,
        reserved    = 0b01100000,
)
reverse_update_dict(REQUEST_TYPE_TYPE)

REQUEST_TYPE_RECIPIENT = dict(
                    #-> ___43210
        device      = 0b00000000,
        interface   = 0b00000001,
        endpoint    = 0b00000010,
        other       = 0b00000010,
        # Reserved  = 0b000*****
)
reverse_update_dict(REQUEST_TYPE_RECIPIENT)

REQUEST_TYPE_MASK = dict(
        direction   = 0b10000000,
        type_       = 0b01100000,
        recipient   = 0b00011111,
)

class SetupField(PackedFields):

    def __init__(self, data=None):
        PackedFields.__init__(self, SETUP_FIELD_FORMAT, data)

    def _bmRequestType_mask(self, mask):
        return self.bmRequestType & REQUEST_TYPE_MASK[mask]

    @property
    def bmRequestTypeDirection(self):
        return REQUEST_TYPE_DIRECTION[self._bmRequestType_mask('direction')]

    @bmRequestTypeDirection.setter
    def bmRequestTypeDirection(self, val):
        raise NotImplementedError

    @property
    def bmRequestTypeType(self):
        return REQUEST_TYPE_TYPE[self._bmRequestType_mask('type_')]

    @bmRequestTypeType.setter
    def bmRequestTypeType(self):
        raise NotImplementedError


class WrongPacketXferType(Exception): pass

if __name__ == '__main__':
    # read a pcap file from stdin, replace the first byte of any data found
    # with 0x42, and write the modified packets to stdout
    import pcapy
    #pcap = pcapy.open_offline('-')
    #pcap = pcapy.open_offline('../test-data/usb-single-packet-8bytes-data.pcap')
    pcap = pcapy.open_offline('../test-data/usb-single-packet-2.pcap')
    #out = pcap.dump_open('-')

    while 1:
        hdr, pack = pcap.next()
        if hdr is None:
            break # EOF
        p = Packet(hdr, pack)
        #p.print_pcap_fields()
        #p.print_pcap_summary()
        #if len(p.data) > 0:
        #    p.data[0] = 0x42
        #out.dump(hdr, p.repack())

