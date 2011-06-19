#!/usr/bin/env python

import sys
import usb.core
import usb.util
import pcapy
from usbrevue import Packet
from optparse import OptionParser

#For skype handset
#VENDOR_ID = 0x1778
#PRODUCT_ID = 0x0406
#EP_ADDRESS = 0x83
#CFG_NUM = 0
#IFACE_NUM = 3
#ALT_SETTING_NUM = 0

#For my mouse on Ubuntu linux Virtual Box for ep 1
VENDOR_ID = 0x80ee
PRODUCT_ID = 0x0021
EP_ADDRESS = 0x81
CFG_NUM = 0
IFACE_NUM = 0
ALT_SETTING_NUM = 0

class Replayer(object):
  def __init__(self, vid=VENDOR_ID, pid=PRODUCT_ID):
    self.device = get_usb_device(vid, pid)
    self.vid = vid
    self.pid = pid


  def initialize_descriptors(self, pcap_packet):
    """ 
    After getting the first pcap packet from the stream, extract the vendorId,
    productId, endpoint address from the packet.  Then set the configuration,
    interface and endpoint descriptors to match what's in the packet.  
    """
    modified = False

    if (pcap_packet.vid is not None and pcap_packet.vid != self.vid): 
      print 'Changing pcap packet vendorId from ', self.vid, ' to ', pack.vid
      self.vid = pack.vid
      modified = True

    if (pcap_pack.pid is not None and pcap_pack.pid != self.pid): 
      print 'Changing pcap packet productId from ', self.pid, ' to ', pack.pid
      self.pid = pack.pid
      modified = True

    if modified:
      self.device = get_usb_device(vid, pid)

    if (pcap_pack.epnum is not None and pcap_pack.epnum != self.ep_address):
      print 'Changing pcap packet endpoint address from ', self.ep_address, ' to ', pack.epnum
      self.ep_address = pack.epnum

    #res = self.device.iskernel_driver_active(self.iface_num)
    #if res:
    #  self.device.detach_kernel_driver()

    set_cfg_descriptor(self.cfg_num):
    set_iface_descriptor(self.iface_num, self.alt_setting_num):
    self.device.set_configuration(self.cfg_num)



  def reset_device(self):
    """ 
    Utility function to reset device. 
    and endpoint address.
    """
    dev.reset()
    dev.attach_kernel_driver(iface_num)


  def print_descriptor_info():
    """ 
    Utility function to print out some basic device hierarcy numbers, ids, 
    and endpoint address.
    """
    print 'vid = ', self.vid
    print 'pid = ', self.pid
    print 'cfg_num = ', self.cfg_num
    print 'iface_num = ', self.iface_num
    print 'alt_setting_num = ', self.alt_setting_num
    print 'ep_address = ', self.ep_address
    


  # Execute lsusb to see USB devices on your system
  #
  # Descriptor class hierarchy is:
  #                                      device
  #                                   /          \
  #                      configuration            configuration
  #                     /             \
  #          interface                 interface        ...
  #         /         \
  #  endpoint         endpoint            ...           ...
  #
  #
  # Device descriptor represents entire device.
  #def get_usb_device(self, vid=0x1778, pid=0x0406):  # for skype handset
  def get_usb_device(self, vid=VENDOR_ID, pid=PRODUCT_ID):   # for my vm mouse
    """ 
    Get the usb.core.Device object based on vendorId and productId.  
    """
    device = usb.core.find(idVendor=vid, idProduct=pid)
    if device is None:
      raise ValueError('USB Device with vendorId', vid, ', and productId', pid, 'not found')
    return device
    


  def print_device_descriptor_fields(self, dev):
    """ 
    Utility function to print out all device descriptor fields.
    """
    print 'bLength = ' % dev.bLength
    print 'bDescriptorType = ' % dev.DescriptorType
    print 'bcdUSB = ' % dev.bcdUSB
    print 'bDeviceClass = ' % dev.bDeviceClass
    print 'bDeviceSubClass = ' % dev.bDeviceSubClass
    print 'bDeviceProtocol = ' % dev.bDeviceProtocol
    print 'bMaxPacketSize = ' % dev.bMaxPacketSize
    print 'idVendor = ' % dev.idVendor
    print 'idProduct = ' % dev.idProduct
    print 'bcdDevice = ' % dev.bcdDevice
    if dev.iManufacturer is not None:
      print 'iManufacturer = ' % dev.iManufacturer
    if dev.iProduct is not None:
      print 'iProduct = ' % dev.iProduct
    if dev.iSerialNumber is not None:
      print 'iSerialNumber = ' % dev.iSerialNumber
    print 'bNumConfigurations = ' % dev.bNumConfigurations



  def print_configuration_descriptor_fields(self, dev):
    """ 
    Utility function to print out all configuration descriptor fields.
    Assumes configuration number, self.cfg_num, has already been set.
    """
    print 'bLength = ' % dev.bLength



  def print_device_enumeration_tree(self, dev):
    """ 
    Utility function to print out the device enumeration, which includes
    device configurations, interfaces and endpoints.
    """
    for cfg in dev:
      print 'configuration %s ' % (cfg.bConfigurationValue)
      for iface in cfg:
        print '  interface %s ' % (iface.bInterfaceNumber)
        print '  interface %s ' % (iface.bAlternateSetting)
        for ep in iface:
          print '    endpoint %s ' % (ep.bEndpointAddress)

  
  def set_cfg_descriptor(self, cfg_num=0):
    """ 
    Set configuration descriptor based on the cfg_num for desired 
    configuration in the hierarchy. 
    Example to set the second configuration:  
      config = dev[1]
    """
    self.cfg_descriptor = self.dev[cfg_num]


  def set_iface_descriptor(self, iface_num=0, alt_setting_num=0):
    """ 
    Set interface descriptor based on interface and alternate setting numbers
    Example to access the first interface and first alternate setting:  
      iface = cfg[(0,0)]
    """
    self.iface_descriptor = self.cfg_descriptor[(iface_num, alt_setting_num)]



  # Interface descriptor resolves into a functional group performing a
  # single feature of the device.  For example, you could have an 
  # all-in-one printer, where interface 1 describes the endpoints of a
  # fax function, interface 2 describes the endpoints of a scanner 
  # function, and interface 3 describes the endpoints of a printer 
  # function.  More than one interface may be enabled at one time.  The
  # altsetting function will allow the interface to change settings on
  # the fly.  
  # For example, interface 0 could have an altsetting of 0, and interface
  # 1 could have an altsetting of 0 or an altsetting of 1.  A 
  # set_interface request can be used to enable one or the other of those
  # interface descriptors.  If interface 1, altsetting 1 is set, then
  # we can change the endpoint settings of interface 1, altsetting 1 
  # without affecting the endpoint settings of interface 1, altsetting 0.
  #def get_first_interface(self, device):
  #  """ 
  #  Get the first interface for the given device.
  #  """
  #  iface = device.getinterface_altsetting()
  #  return iface


  # Configuration descriptor specifies values such as amount of power
  # this particular configuration uses, if device is self or bus 
  # powered and number of interfaces it has. Few devices have more
  # than 1 configuration, so cfg index will usually be empty and we will
  # simply select the only active configuration at index 0. Only 1 
  # configuration may be enabled at a time
  #def set_configuration(self, device, cfg_num=None):
  #  """ 
  #  Set the configuration.  If conf is None then set to the
  #  active configuration.
  #  """
  #  if conf is None:
  #    device.set_configuration()
  #  else:
  #    device.set_configuration(cfg_num)



  def run(self, pcap, out):
    initialized = False
    res = self.device.iskernel_driver_active()
    if res:
      self.device.detach_kernel_driver()

    while True:
      hdr, pack = pcap.next()
      if hdr is None:
        break # EOF

      pcap_packet = Packet(hdr, pack)
      print "Dumping pcap input data ..."
      out.dump(hdr, p.repack())

      print "Printing pcap field information ..."
      pcap_packet.print_pcap_fields()

      print "Printing pcap summary information ..."
      pcap_packet.print_pcap_summary()

      if not initialized:
        initialize_descriptors(pcap_packet)
        initialized = True

      send_usb_packet(pcap_packet)
      sys.exit("Early exit for debug purposes")



  def send_usb_packet(self, pack):
    read_array = []
    ep = usb.util.find_descriptor(iface, custom_match=lambda e: e.bEndpointAddress==self.ep_address)

    # It is safe to decode setup packet if setup flag is 's'
    if pack.flag_setup == 's':
      bmRequestType, bmRequest, wValue, wIndex, numBytes = pack.data[0:4]
      bytes_sent = self.device.ctrl_transfer(bmRequestType, bmRequest, wValue, numBytes, pack.data[5:]
      if bytes_sent != num_bytes:
        print 'Error: %d bytes sent in control transfer and %d bytes actually got there' % (num_bytes, bytes_sent)

    # Submission means xfer from host to USB device
    else if pack.type == 'S':        
      num_bytes = ep.write(pack, TIMEOUT)
      print 'Wrote %d bytes to USB device', num_bytes, ', expected to write %d bytes ', pack.length

    else if pack.type == 'C':   # Callback means xfer from USB to host
      read_array = ep.read(pack.length, TIMEOUT)
      print '%d data items read.  Data = ', read_array



  def get_arguments(argv):
    parser = OptionParser()

    # Get the input file stream (pcap stream or filename
    parser.add_option("-f", "--file", dest="infile", default="-",
      help="Input pcap stream (filename or '-' for stdin)")

    # Get the vendor id
    parser.add_option("-v", "--vid", type="int", dest="vid", 
      default=VENDOR_ID, help="The vendor id for the USB device")

    # Get the product id
    parser.add_option("-p", "--pid", type="int", dest="pid", 
      default=0x0406, help="The product id for the USB device")

    # Get the configuration index (defaults to 0)
    parser.add_option("-c", "--cfgnum", type="int", dest="cfg_num", 
      default=CONFIG_NUM, help="Which configuration of the device (starting at 0) in the device hierarchy")

    # Get the interface index (defaults to 3)
    parser.add_option("-i", "--ifacenum", type="int", dest="iface_num", 
      default=IFACE_NUM, help="Which interface of the configuration (starting at 0) in the device hierarchy")

    # Get the alternate setting index (defaults to 0)
    parser.add_option("-a", "--altsettingnum", type="int", dest="alt_setting_num", 
      default=ALT_SETTING_NUM, help="Which alternate setting of the interface (starting at 0) in the device hierarchy")

    # Get the endpoint index (defaults to 0)
    parser.add_option("-e", "--epaddress", type="int", dest="ep_address", 
      default=EP_ADDRESS, help="The endpoint address for the USB device in the device hierarchy")

    # Set the debug mode to quiet or verbose
    parser.add_option("-q", "--quiet", action="store_false", 
      dest="verbose", default=True,
      help="Don't print debug messages to stdout")

    self.vid = vid
    self.pid = pid 
    self.cfg_num = cfg_num
    self.iface_num = iface_num
    self.alt_setting_num = alt_setting_num
    self.ep_address = ep_address



if __name__ == '__main__':
  # read a pcap stream from a file or from stdin, write the contents back
  # to stdout (for debug info), convert input stream to USB packets, and 
  # send USB packets to the device or stdout.
  get_arguments(sys.argv)
  pcap = pcapy.open_offline('-')
  out = pcap.dump_open('-')
  replayer = Replayer(pcap, out)
  replayer.run()

