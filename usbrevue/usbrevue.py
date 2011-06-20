#!/usr/bin/env python
from struct import unpack_from
import datetime

USB_PACKET_FORMAT = dict(
    # Attr        fmt     offset
    _id         = ('=Q',  0),
    _type       = ('=c',  8),
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
)

# Incomplete - Danny's comments below conflict with the 
# Linux kernel headers <linux/usb/ch9.h>:
#define USB_ENDPOINT_XFER_CONTROL       0
#define USB_ENDPOINT_XFER_ISOC          1
#define USB_ENDPOINT_XFER_BULK          2
#define USB_ENDPOINT_XFER_INT           3
USB_TRANSFER_TYPE = dict(
        isochronous = 0,
        interrupt   = 1,
# ...
        )

class Packet(object):

  def __init__(self, hdr, pack):
    if len(pack) < 64:
      raise RuntimeError("Not a USB Packet")

    self._data = list(unpack_from('=%dB' % self.datalen, pack, 64))
    self._hdr, self._pack = hdr, pack

    if self._type not in ['C', 'S', 'E'] or self.xfer_type not in USB_TRANSFER_TYPE.values():
      raise RuntimeError("Not a USB Packet")

  def datalen(self):
    return len(self._pack) - 64

  # Generic attribute accessor
  # Note that we unpack the single item from the tuple in __getattr__ due to
  # setup()
  def unpacket(self, attr):
    fmt, offset = USB_PACKET_FORMAT[attr]
    return unpack_from(fmt, self._pack, offset)

  def __getattr__(self, attr):
      return self.unpacket(attr)[0]

  # Special attribute accessors that have additional restrictions
  def setup(self):
    # setup is only meaningful if flag_setup == 's'
    if self.flag_setup == 's':
        return list(self.unpacket('setup'))

  # error_count and numdesc are only meaningful for isochronous transfers
  # (xfer_type == 0)
  def error_count(self):
    if self.is_isochronous_xfer():
        return self.unpacket('error_count')[0]

  def numdesc(self):
    if self.is_isochronous_xfer():
        return self.unpacket('numdesc')[0]

  # interval is only meaningful for isochronous or interrupt transfers
  # (xfer_type in [0,1])
  def interval(self):
    if self.is_isochronous_xfer() or self.is_interrupt_xfer():
        return self.unpacket('interval')[0]

  def start_frame(self):
    # start_frame is only meaningful for isochronous transfers
    if self.is_isochronous_xfer():
        return self.unpacket('start_frame')[0]

  # Boolean tests for transfer types
  def is_isochronous_xfer(self):
      return self.xfer_type == USB_TRANSFER_TYPE['isochronous']

  def is_bulk_xfer(self):
      return self.xfer_type == USB_TRANSFER_TYPE['bulk']

  def is_control_xfer(self):
      return self.xfer_type == USB_TRANSFER_TYPE['control']

  def is_interrupt_xfer(self):
      return self.xfer_type == USB_TRANSFER_TYPE['interrupt']


  def print_pcap_fields(self):
    """ 
    Print detailed packet information for debug purposes.  
    Assumes header exists.
    """
    print "id = " % (self.id)
    print "type = " % (self.type)
    print "xfer_type = " % (self.xfer_type)
    print "epnum = " % (self.epnum)
    print "devnum = " % (self.devnum)
    print "busnum = " % (self.busnum)
    print "flag_setup = " % (self.flag_setup)
    print "flag_data = " % (self.flag_data)
    print "ts_sec = " % (self.ts_sec,)
    print "ts_usec = " % (self.ts_usec)
    print "status = " % (self.status)
    print "length = " % (self.length)
    print "len_cap = " % (self.len_cap)
    # setup is only meaningful if flag_setup == 's')
    if (self.flag_setup == 's'):
      print "setup = " % (self.setup)
    # error_count and numdesc are only meaningful for isochronous transfers
    # (xfer_type == 0)
    if (self.xfer_type == 0):
      print "error_count = " % (self.error_count)
      print "numdesc = " % (self.numdesc)
    # interval is only meaningful for isochronous or interrupt transfers)
    # (xfer_type in [0,1]))
    if (self.xfer_type in [0,1]):
      print "interval = " % (self.interval)
    # start_frame is only meaningful for isochronous transfers)
    if (self.xfer_type == 0):
      print "start_frame = " % (self.start_frame)
    print "xfer_flags = " % (self.xfer_flags)
    print "ndesc = " % (self.ndesc)
    print "datalen = " % (datalen)
    print "data = " % (self.data)
    print "hdr = " % (self.hdr)
    print "packet = " % (self.pack)


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

# Really? This is Python, not Ruby....
# vim:sts=2 sw=2
