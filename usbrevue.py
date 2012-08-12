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

"""Core USB REVue classes: USBMonPacket and SetupField.
    * USBMonPacket represents a USBMon packet.
    * SetupField represents the 'setup' attribute of the USBMonPacket.

"""

__version__= '0.0.1'
import sys

from array import array
from functools import partial
from logging import debug
from pprint import pprint, pformat
from struct import unpack
import datetime
import logging
#logging.basicConfig(level=logging.DEBUG)

from fieldpack import FieldPack
from util import reverse_update_dict, apply_mask

USBMON_PACKET_FORMAT = dict(
    # Attr        fmt     offset
    urb         = ('<Q',  0),
    event_type  = ('<c',  8),
    xfer_type   = ('<B',  9),
    epnum       = ('<B',  10),
    devnum      = ('<B',  11),
    busnum      = ('<H',  12),
    flag_setup  = ('<c',  14),
    flag_data   = ('<c',  15),
    ts_sec      = ('<q',  16),
    ts_usec     = ('<i',  24),
    status      = ('<i',  28),
    length      = ('<I',  32),
    len_cap     = ('<I',  36),
    setup       = ('<8s', 40),
    error_count = ('<i',  40),
    numdesc     = ('<i',  44),
    interval    = ('<i',  48),
    start_frame = ('<i',  52),
    xfer_flags  = ('<I',  56),
    ndesc       = ('<I',  60),
    data        = ('<%dB', 64),
)

# Note that the packet transfer type has different numeric identifiers than the
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

class USBMonPacket(FieldPack):
    """The ``USBMonPacket`` class adds higher-level semantics over the lower-level field
    packing and unpacking.

    The following attributes are extracted dynamically from the packet data and
    re-packed into the data when assigned to.

        * urb
        * event_type
        * xfer_type
        * epnum
        * devnum
        * busnum
        * flag_setup
        * flag_data
        * ts_sec
        * ts_usec
        * status
        * length
        * len_cap
        * xfer_flags
        * ndesc
        * data

    Other attributes are extracted dynamically but require more implementation
    than FieldPack provides by default and thus are separate properties with
    their own docstrings.

    These attributes correspond with the struct usbmon_packet data members from:
        http://www.kernel.org/doc/Documentation/usb/usbmon.txt
    """

    def __init__(self, hdr=None, pack=None):
        """Requires a libpcap/pcapy header and packet data."""

        super(USBMonPacket, self).__init__()
        self.format_table = USBMON_PACKET_FORMAT

        if None not in (hdr, pack):
            if len(pack) < 64:
                raise RuntimeError("Not a USB USBMonPacket")

            self._hdr = hdr
            self.datapack = array('c', pack)

            if self.event_type not in ['C', 'S', 'E'] or \
                    self.xfer_type not in USBMON_TRANSFER_TYPE.values():
                raise RuntimeError("Not a USBMonPacket")

    @property
    def hdr(self):
        """Accessor for libpcap header."""
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
        """Return the length of the data payload of the packet."""
        return len(self.datapack) - 64

    # Special attribute accessors that have additional restrictions
    @property
    def data(self):
        """Data payload. Note that while there is only a get accessor for this
        attribute, it is a list and is therefore mutable. It cannot, however,
        be easily grown or shrunk."""
        return self.cache('data',
                lambda a: list(self.unpacket(a, self.datalen)))

    def data_hexdump(self, maxlen=None):
        """Space-delimited dump of data in hex"""
        return ' '.join(map(lambda x: '%02X' % x, self.data[:maxlen]))

    def repack(self):
        """Returns the packet data as a string, taking care to repack any
        "loose" attributes."""
        self.repacket('data', self.data, self.datalen)
        return super(USBMonPacket, self).repack()

    @property
    def setup(self):
        """An instance of the SetupField class."""

        def _update_setup(self, datapack):
            self.repacket('setup', [datapack.tostring()])

        if self.is_setup_packet:
            return self.cache('setup',
                    lambda a:
                        SetupField(self.unpacket(a)[0],
                            partial(_update_setup, self)))

    # error_count and numdesc are only meaningful for isochronous transfers
    # (xfer_type == 0)
    @property
    def error_count(self):
        """Isochronous error_count"""
        if self.is_isochronous_xfer:
            return self.cache('error_count', lambda a: self.unpacket(a)[0])
        else:
            # FIXME Raise WrongUSBPacketXferType instead
            return 0

    @property
    def numdesc(self):
        """Isochronous numdesc"""
        if self.is_isochronous_xfer:
            return self.cache('numdesc', lambda a: self.unpacket(a)[0])
        else:
            # FIXME Raise WrongUSBPacketXferType instead
            return 0

    # interval is only meaningful for isochronous or interrupt transfers
    # (xfer_type in [0,1])
    @property
    def interval(self):
        """Isochronous/interrupt interval"""
        if self.is_isochronous_xfer or self.is_interrupt_xfer:
            return self.cache('interval', lambda a: self.unpacket(a)[0])
        else:
            # FIXME Raise WrongUSBPacketXferType instead
            return 0

    @property
    def start_frame(self):
        """Isochronous start_frame"""
        # start_frame is only meaningful for isochronous transfers
        if self.is_isochronous_xfer:
            return self.cache('start_frame', lambda a: self.unpacket(a)[0])
        else:
            # FIXME Raise WrongUSBPacketXferType instead
            return 0

    # Boolean tests for transfer types
    @property
    def is_isochronous_xfer(self):
        """Boolean test if transfer-type is isochronous"""
        return self.xfer_type == USBMON_TRANSFER_TYPE['isochronous']

    @property
    def is_bulk_xfer(self):
        """Boolean test if transfer-type is bulk"""
        return self.xfer_type == USBMON_TRANSFER_TYPE['bulk']

    @property
    def is_control_xfer(self):
        """Boolean test if transfer-type is control"""
        return self.xfer_type == USBMON_TRANSFER_TYPE['control']

    @property
    def is_interrupt_xfer(self):
        """Boolean test if transfer-type is interrupt"""
        return self.xfer_type == USBMON_TRANSFER_TYPE['interrupt']

    # NB: The usbmon doc says flag_setup should be 's' but that seems to be
    # only for the text interface, because is seems to be 0x00 and
    # Wireshark agrees.
    @property
    def is_setup_packet(self):
        """Boolean test to determine if packet is a setup packet"""
        return self.flag_setup == '\x00'

    @property
    def is_event_type_submission(self):
        """Boolean test if event-type is submission"""
        return self.event_type == 'S'

    @property
    def is_event_type_callback(self):
        """Boolean test if event-type is callback"""
        return self.event_type == 'C'

    @property
    def is_event_type_error(self):
        """Boolean test if event-type is error"""
        return self.event_type == 'E'

    @property
    def ep_dir_ch(self):
        """Single-char representation of endpoint direction"""
        return ['o', 'i'][self.epnum >> 7]

    @property
    def endpoint_dir(self):
        """Verbose representation of endpoint direction"""
        return ['outgoing', 'incoming'][self.epnum >> 7]

    @property
    def xfer_type_ch(self):
        """Single-char representation of xfer_type"""
        return ['Z', 'I', 'C', 'B'][self.xfer_type]

    @property
    def transfer_type(self):
        """Verbose representation of transfer type"""
        return ['Isochronous', 'Interrupt', 'Control', 'Bulk'][self.xfer_type]

    @property
    def addr(self):
        """Packet address"""
        # Does it make sense to have two decimals followed by a hex?
        return "%d:%02d:%02x" % (self.busnum, self.devnum, self.epnum)

    @property
    def address_verbose(self):
        """Verbose packet address"""
        return "bus %d, device %d, endpoint 0x%x" % (self.busnum,
                                                     self.devnum, self.epnum)
    @property
    def event_type_preposition(self):
        """Verbose event-type"""
        return  {'S': 'Submission to',
                 'C': 'Callback from',
                 'E': 'Error on'}[self.event_type]

    @property
    def typedir(self):
        """Abbreviated packet type & direction, a la usbmon: 'Ci', 'Co', etc."""
        return self.xfer_type_ch + self.ep_dir_ch

    @property
    def packet_summ(self):
        """Summary of packet event type, address, etc."""
        return "%s %s (%s)" % (self.event_type, self.addr, self.typedir)


    def copy(self):
        """Make a complete copy of the Packet."""
        new_packet = USBMonPacket(self.hdr, self.datapack)
        return new_packet


    def print_pcap_fields(self):
        # FIXME This should be __str__ and can probably do most or all of this
        # programmatically--iterating through each attribute by offset.
        # Requires that inappropriate attributes raise exceptions, etc.
        """Print detailed packet header information for debug purposes. """
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
        # setup is only meaningful if self.is_setup_packet is True)
        if self.is_setup_packet:
            print "setup = %s" % (self.setup.data_to_str())
        # error_count and numdesc are only meaningful for isochronous transfers
        # (xfer_type == 0)
        #if (self.xfer_type == 0):
        if self.is_isochronous_xfer:
            print "error_count = %d" % (self.error_count)
            print "numdesc = %d" % (self.numdesc)
        # interval is only meaningful for isochronous or interrupt transfers)
        # (xfer_type in [0,1]))
        #if (self.xfer_type in [0,1]):
        if self.is_isochronous_xfer or self.is_interrupt_xfer:
            print "interval = %d" % (self.interval)
        # start_frame is only meaningful for isochronous transfers)
        if self.is_isochronous_xfer:
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
        """Print concise pcap header summary information for debug purposes."""
        print ('%s: Captured %d bytes, truncated to %d bytes' % (
                datetime.datetime.now(), self.hdr.getlen(),
                self.hdr.getcaplen()))


SETUP_FIELD_FORMAT = dict(
        bmRequestType   =   ('<B',  0),
        bRequest        =   ('<B',  1),
        wValue          =   ('<H',  2),
        wIndex          =   ('<H',  4),
        wLength         =   ('<H',  6),
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
        other       = 0b00000011,
        # Reserved  = 0b000*****
)
reverse_update_dict(REQUEST_TYPE_RECIPIENT)

REQUEST_TYPE_MASK = dict(
        direction   = 0b10000000,
        type_       = 0b01100000,
        recipient   = 0b00011111,
)

class SetupField(FieldPack):
    """The ``SetupField`` class provides access to the ``setup`` field of the
    USBMonPacket class. As the ``setup`` field is a multi-byte field with bit-mapped
    and numeric encodings, this class provides higher-level accessors which
    decode the various subfields.

    Dynamic accessors for this class are:
        * bmRequestType
        * bRequest
        * wValue
        * wIndex
        * wLength

    There are several additional accessors for the subfields of the bit-mapped
    bmRequestType.
    """

    def __init__(self, data=None, update_parent=None):
        FieldPack.__init__(self, SETUP_FIELD_FORMAT, data, update_parent)

    def _bmRequestType_mask(self, mask):
        return self.bmRequestType & REQUEST_TYPE_MASK[mask]

    @property
    def bmRequestTypeDirection(self):
        """Decode 'direction' bits of bmRequestType. Gets and sets the
        following strings:
                * device_to_host
                * host_to_device
        """
        return REQUEST_TYPE_DIRECTION[self._bmRequestType_mask('direction')]

    @bmRequestTypeDirection.setter
    def bmRequestTypeDirection(self, val):
        self.bmRequestType = apply_mask(REQUEST_TYPE_MASK['direction'],
                                        self.bmRequestType,
                                        REQUEST_TYPE_DIRECTION[val])

    @property
    def bmRequestTypeType(self):
        """Decode 'type' bits of bmRequestType. Gets and sets the following
        strings:
                * standard
                * class_
                * vendor
                * reserved
        """
        return REQUEST_TYPE_TYPE[self._bmRequestType_mask('type_')]

    @bmRequestTypeType.setter
    def bmRequestTypeType(self, val):
        self.bmRequestType = apply_mask(REQUEST_TYPE_MASK['type_'],
                                        self.bmRequestType,
                                        REQUEST_TYPE_TYPE[val])

    @property
    def bmRequestTypeRecipient(self):
        """Decode 'recipient' bits of bmRequestType. Gets and sets the
        following strings:
                * device
                * interface
                * endpoint
                * other
        """
        return REQUEST_TYPE_RECIPIENT[self._bmRequestType_mask('recipient')]

    @bmRequestTypeRecipient.setter
    def bmRequestTypeRecipient(self, val):
        self.bmRequestType = apply_mask(REQUEST_TYPE_MASK['recipient'],
                                        self.bmRequestType,
                                        REQUEST_TYPE_RECIPIENT[val])

    @property
    def bRequest_str(self):
        if self.bRequest in SETUP_REQUEST_TYPES:
            return SETUP_REQUEST_TYPES[self.bRequest]
        else:
            return 'unknown'

    def data_to_str(self):
        """Compact hex representation of setup data. Note that due to
        endianness, byte orders may appear to differ from the bytes as
        presented in ``fields_to_str``.
        """
        return '%02X %02X %02X%02X %02X%02X %02X%02X' % \
            unpack('<8B', self.datapack.tostring()) # yuck

    def fields_to_str(self):
        """Verbose but single-line string representation of setup data.
        """
        s = 'bmRequestType: %s, %s, %s (%s)' % (self.bmRequestTypeType,
                                            self.bmRequestTypeDirection,
                                            self.bmRequestTypeRecipient,
                                            bin(self.bmRequestType))
        s += '; bRequest: %s (0x%X)' % (self.bRequest_str, self.bRequest)
        s += '; wValue: (0x%X)' % self.wValue
        s += '; wIndex: (0x%X)' % self.wIndex
        s += '; wLength: (0x%X)' % self.wLength
        return s

    def __str__(self):
        #s = 'type: %s' % self.bmRequestTypeType
        s = ''
        s += self.fields_to_str()
        if self.bmRequestTypeType == 'standard':
            s += ', request: %s' % self.bRequest_str
            s += ', direction: %s' % self.bmRequestTypeDirection
            s += ', recipient: %s' % self.bmRequestTypeRecipient
        #else:
        s += ', data: %s' % self.data_to_str()

        return s

class WrongUSBPacketXferType(Exception):
    """Exception that should be raised when data USBMonPacket fields are accessed for
    inappropriate transfer types. Note that this is currently not done."""
    pass

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
        p = USBMonPacket(hdr, pack)
        #p.print_pcap_fields()
        #p.print_pcap_summary()
        #if len(p.data) > 0:
        #    p.data[0] = 0x42
        #out.dump(hdr, p.repack())

