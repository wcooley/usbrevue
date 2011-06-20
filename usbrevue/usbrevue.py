#!/usr/bin/env python
from struct import unpack_from
import datetime

class Packet(object):
  def __init__(self, hdr, pack):
    if len(pack) < 64:
      raise RuntimeError("Not a USB Packet")

    self.id,          = unpack_from('=Q', pack)
    self.type,        = unpack_from('=c', pack, 8)
    self.xfer_type,   = unpack_from('=B', pack, 9)

    if self.type not in ['C', 'S', 'E'] or self.xfer_type not in range(4):
      raise RuntimeError("Not a USB Packet")

    self.epnum,       = unpack_from('=B', pack, 10)
    self.devnum,      = unpack_from('=B', pack, 11)
    self.busnum,      = unpack_from('=H', pack, 12)
    self.flag_setup,  = unpack_from('=c', pack, 14)
    self.flag_data,   = unpack_from('=c', pack, 15)
    self.ts_sec,      = unpack_from('=q', pack, 16)
    self.ts_usec,     = unpack_from('=i', pack, 24)
    self.status,      = unpack_from('=i', pack, 28)
    self.length,      = unpack_from('=I', pack, 32)
    self.len_cap,     = unpack_from('=I', pack, 36)
    # setup is only meaningful if flag_setup == 's'
    self.setup = list(unpack_from('=8B', pack, 40))
    # error_count and numdesc are only meaningful for isochronous transfers
    # (xfer_type == 0)
    self.error_count, = unpack_from('=i', pack, 40)
    self.numdesc,     = unpack_from('=i', pack, 44)
    # interval is only meaningful for isochronous or interrupt transfers
    # (xfer_type in [0,1])
    self.interval,    = unpack_from('=i', pack, 48)
    # start_frame is only meaningful for isochronous transfers
    self.start_frame, = unpack_from('=i', pack, 52)
    self.xfer_flags,  = unpack_from('=I', pack, 56)
    self.ndesc,       = unpack_from('=I', pack, 60)

    datalen = len(pack) - 64
    self.data = list(unpack_from('=%dB' % datalen, pack, 64))
    self.hdr, self.pack = hdr, pack


  def print_pcap_fields(self):
    """ 
    Print detailed packet information for debug purposes.  
    Assumes header exists.
    """
    print "id = %d" % (self.id)
    print "type = %s" % (self.type)
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

