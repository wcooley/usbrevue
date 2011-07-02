#!/usr/bin/env python

import sys
import usb.core
import usb.util
import pcapy
from usbrevue import Packet
import optparse
import traceback
#from optparse import OptionParser

#For skype handset
#VENDOR_ID = 0x1778
#PRODUCT_ID = 0x0406
#EP_ADDRESS = 0x83
#CFG_NUM = 0
#IFACE_NUM = 3
#ALT_SETTING_NUM = 0

#For my mouse on Ubuntu linux Virtual Box for ep 1
#VENDOR_ID = 0x80ee
#PRODUCT_ID = 0x0021
#EP_ADDRESS = 0x81
#CFG_NUM = 0
#IFACE_NUM = 0
#ALT_SETTING_NUM = 0

#For capstone14.cs.pdx.edu USB keyboard 
VENDOR_ID = 0x413c    # Dell Computer Corp.
PRODUCT_ID = 0x2105   # Model L100 Keyboard
LOGICAL_CFG = 0   # 1 interface, bConfigurationValue=1
LOGICAL_IFACE = 0 # HID Device Descriptor.bHID=1.10, 1 ep descriptor
                      # bInterfaceClass=3 (Human Interface device)
LOGICAL_ALT_SETTING = 0
LOGICAL_EP = 0    # EP 1 IN
EP_ADDRESS = 0x81     # EP 1 IN, xferType=Interrupt, bmAttributes=3 
                      # (Transfer Type, Synch Type, Usage Type)
BUS = 0x6
DEVICE = 0x3


class Replayer(object):
  """
  Class that encapsulates functionality to replay pcap steam packets 
  to a USB device.
  """

  def __init__(self, options):
    """
    Constructor to initialize to the various usb fields, such as vendor
    id, product id, configuration, interface, alternate setting and 
    endpoint address.  Based on vendor and product id, it will get
    the USB device and set the appropriate parameters.  The options
    argument contains either defaults values for these fields or 
    user designated values.
    """

    print '\nIn __init__'
    self.vid = options.vid
    self.pid = options.pid
    self.logical_cfg = options.logical_cfg
    self.logical_iface = options.logical_iface
    self.logical_alt_setting = options.logical_alt_setting
    self.ep_address = options.ep_address
    self.logical_ep = options.ep_address & 0x0f
    print 'Logical ep = %d' % self.logical_ep

    self.device = self.get_usb_device(self.vid, self.pid)
    if self.device is None:
      raise ValueError('The device with vid=0x%x, pid=0x%x is not connected') % (self.vid, self.pid)

    self.set_configuration(self.logical_cfg)
    self.set_interface(self.logical_iface, self.logical_alt_setting)
    self.print_descriptor_info()

    self.ep = usb.util.find_descriptor(self.iface, custom_match=lambda e: e.bEndpointAddress==self.ep_address)
    #assert self.ep is not None
    if not self.ep:
      raise ValueError('Could not find USB Device with endpoint address', self.ep_address)



  def initialize_descriptors(self, packet):
    """ 
    After getting the first pcap packet from the stream, extract the vendorId,
    productId, endpoint address from the packet.  Then, if there are differences,
    set the configuration, interface and endpoint descriptors to match what's
    in the packet.  
    """
    print 'In initialize_descriptors'
    modified = False

    #if (packet.vid != self.vid): 
    #  print 'Changing pcap packet vendorId from ', self.vid, ' to ', packet.vid
    #  self.vid = packet.vid
    #  modified = True

    #if (packet.pid != self.pid): 
    #  print 'Changing pcap packet productId from ', self.pid, ' to ', packet.pid
    #  self.pid = packet.pid
    #  modified = True

    #if modified:
    #  self.device = get_usb_device(vid, pid)

    if (packet.epnum != self.ep_address):
      print 'Changing pcap packet endpoint address from ', self.ep_address, ' to ', packet.epnum
      self.ep_address = packet.epnum

    #res = self.device.iskernel_driver_active(self.iface_num)
    #if res:
    #  self.device.detach_kernel_driver()

    self.set_configuration(self.logical_cfg)
    self.set_interface(self.logical_iface, self.logical_alt_setting)
    self.print_descriptor_info()
    # set_configuration is used to enable a device and should contain
    # the value of bConfigurationValue of the desired configuration
    # descriptor in the lower byte of wValue to select which configuration
    # to enable.
    #self.device.set_configuration(self.cfg_num)



  def reset_device(self):
    """ 
    Utility function to reset device. 
    and endpoint address.
    """
    print 'In reset_device'
    dev = self.device
    dev.reset()
    res = dev.is_kernel_driver_active(self.logical_iface)
    if not res:
      dev.attach_kernel_driver(self.logical_iface)


  def print_descriptor_info(self):
    """ 
    Utility function to print out some basic device hierarcy numbers, ids, 
    and endpoint address.
    """
    print '--------------------------------'
    print 'In print_descriptor_info'
    print 'vid = 0x%x' % self.vid
    print 'pid = 0x%x' % self.pid
    print 'logical_cfg_idx = %d' % self.logical_cfg
    print 'logical_iface_idx = %d' % self.logical_iface
    print 'logical_alt_setting_idx = %d' % self.logical_alt_setting
    print 'ep_address = 0x%x' % self.ep_address
    print 'logical_ep_idx = %d' % self.logical_ep
    


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
    print 'In get_usb_device'
    device = usb.core.find(idVendor=vid, idProduct=pid)
    if device is None:
      raise ValueError('USB Device with vendorId', vid, ', and productId', pid, 'not found')
    return device
    


  # Got this from USB in a NutShell, chp 5.
  def print_device_descriptor_fields(self):
    """ 
    Utility function to print out all device descriptor fields.
    """
    print '--------------------------------'
    print 'In print_device_descriptor_fields'
    dev = self.device
    # bLength = Size of device descriptor in bytes (18 bytes) (number).
    print 'bLength = ', dev.bLength
    # bDescriptorType = Device descriptor (0x01) in bytes (constant).
    print 'bDescriptorType = ', dev.bDescriptorType
    # bDescriptorType = USB spec number which device complies to (bcd). 
    print 'bcdUSB = 0x%x' % dev.bcdUSB
    # bDeviceClass = Class code assigned by USB org (0 or 0xff) (class).
    print 'bDeviceClass = ', dev.bDeviceClass
    # bDeviceSubClass = Sublass code assigned by USB org (subClass).
    print 'bDeviceSubClass = ', dev.bDeviceSubClass
    # bDeviceProtocol = Protocol code assigned by USB org (protocol).
    print 'bDeviceProtocol = ', dev.bDeviceProtocol
    #bMaxPacketSize = Max packet size for zero endpoint (8, 16, 32, 64).
    #print 'bMaxPacketSize = ', dev.bMaxPacketSize
    # idVendor = Vendor ID assigned by USB org (ID).
    print 'idVendor = 0x%x' % dev.idVendor
    # idProduct = Product ID assigned by USB org (ID).
    print 'idProduct = 0x%x' % dev.idProduct
    # bcdDevice = Device release number (bcd).
    print 'bcdDevice = ', dev.bcdDevice
    # iManufacturer = Index of manufacturer string descriptor (index).
    if dev.iManufacturer is not None:
      print 'iManufacturer = ', dev.iManufacturer
    # iProduct = Index of product string descriptor (index).
    if dev.iProduct is not None:
      print 'iProduct = ', dev.iProduct
    # iSerialNumber = Index of serial number string descriptor (index).
    if dev.iSerialNumber is not None:
      print 'iSerialNumber = ', dev.iSerialNumber
    # iNumConfigurations = Number of possible configurations (integer).
    print 'bNumConfigurations = ', dev.bNumConfigurations


  # Got this from USB in a NutShell, chp 5.
  def print_cfg_descriptor_fields(self):
    """ 
    Utility function to print out all configuration descriptor fields.
    """
    print '--------------------------------'
    print 'In print_cfg_descriptor_fields'
    cfg = self.cfg
    # bLength = Size of configuration descriptor in bytes (number).
    print 'bLength = ', cfg.bLength
    # bDescriptorType = Configuration descriptor (0x02) in bytes (constant).
    print 'bDescriptorType = ', cfg.bDescriptorType
    # bTotalLength = Total length in bytes of data returned (number). 
    # This indicates the number of bytes in the configuration hierarchy.
    print 'wTotalLength = ', cfg.wTotalLength
    # bNumInterfaces = Total length in bytes of data returned (number). 
    print 'bNumInterfaces = ', cfg.bNumInterfaces
    # bConfigurationValue = Value to use as an arg to select this cfg (number).
    print 'bConfigurationValue = ', cfg.bConfigurationValue
    # iConfiguration = Index of string descriptor describing this cfg (index).
    # This string is in human readable form.
    print 'iConfiguration = ', cfg.iConfiguration
    # bmAttributes = Bus or self powered, remote wakeup or reserved (bitmap). 
    # Remote wakeup allows device to wake up the host when the host is in suspend.
    print 'bmAttributes = ', cfg.bmAttributes
    # bMaxPower = Maximum power consumption in 2mA units (mA).
    print 'bMaxPower = ', cfg.bMaxPower


  # Got this from USB in a NutShell, chp 5.
  # Interface descriptor is a grouping of endpoints into a functional 
  # group performing a single feature of the device.
  def print_iface_descriptor_fields(self):
    """ 
    Utility function to print out all interface descriptor fields.
    """
    print '--------------------------------'
    print 'In print_iface_descriptor_fields'
    iface = self.iface
    # bLength = Size of interface descriptor in bytes (number).
    print 'bLength = ', iface.bLength
    # bDescriptorType = Interface descriptor (0x04) in bytes (constant).
    print 'bDescriptorType = ', iface.bDescriptorType
    # bInterfaceNumber = Number of interface (number).
    print 'bInterfaceNumber = ', iface.bInterfaceNumber
    # bAlternateSetting = Value used to select alternate setting (number).
    print 'bAlternateSetting = ', iface.bAlternateSetting
    # bNumEndpoints = Number of endpoints used for this interface (number).
    # This excludes endpoint 0.
    print 'bNumEndpoints = ', iface.bNumEndpoints
    # bInterfaceClass = Class code assigned by USB org (class).
    # Class could be HID, communicatins, mass storage, etc.
    print 'bInterfaceClass = ', iface.bInterfaceClass
    # bInterfaceSubClass = SubClass code assigned by USB org (subClass).
    print 'bInterfaceSubClass = ', iface.bInterfaceSubClass
    # bInterfaceProtocol = Protocol code assigned by USB org (protocol).
    print 'bInterfaceProtocol = ', iface.bInterfaceProtocol
    # iInterface = Index of string descriptor describing this interface (index).
    print 'iInterface = ', iface.iInterface



  # Got this from USB in a NutShell, chp 5.
  def print_ep_descriptor_fields(self):
    """ 
    Utility function to print out all endpoint descriptor fields.
    """
    print '--------------------------------'
    print 'In print_ep_descriptor_fields'
    ep = self.ep
    # bLength = Size of endpoint descriptor in bytes (number).
    print 'bLength = ', ep.bLength
    # bDescriptorType = Endpoint descriptor (0x05) in bytes (constant).
    print 'bDescriptorType = ', ep.bDescriptorType
    # bEndpointAddress = Endpoint descriptor (0x05) in bytes (constant).
    # Bits 0-3=endpoint number, Bits 4-6=0, Bit 7=0(out) or 1(in).
    print 'bEndpointAddress = 0x%x' % ep.bEndpointAddress
    # Endpoint logical index is derived from Bits 0-3=endpoint number of
    # the bEndpointAddress.
    print 'endpoint logical index = ', ep.bEndpointAddress & 0xf
    # bmAttributes = Bits 0-1=Transfer type, other bits refer to 
    # synchronization type, usage type (iso mode) (bitmap).
    # Transfer types: 00=Control, 01=Isochronous, 10=Bulk, 11=Interrupt.
    print 'bmAttributes = ', ep.bmAttributes
    # wMaxPacketSize = Max packet size this endpoint is capable of 
    # sending or receiving (number).
    # This is the maximum payload size for this endpoint.
    print 'wMaxPacketSize = ', ep.wMaxPacketSize
    # bInterval = Interval for polling endpoint data transfers.  
    # Value in frame counts (?).  Ignored for bulk and control endpoints.
    # Isochronous must equal 1.  This field for interrupt endpoints may 
    # range from 1 to 255 (number).
    # bInterval is used to specify the polling interval of certain transfers.
    # The units are expressed in frames.  This equates to 1ms for low/full
    # speed devices, and 125us for high speed devices.
    print 'bInterval = ', ep.bInterval


  def print_device_enumeration_tree(self):
    """ 
    Utility function to print out the device enumeration, which includes
    device configuration, interface and endpoint descriptors.
    """
    print '--------------------------------'
    print 'In print_device_enumeration_tree'
    dev = self.device
    for cfg in dev:
      print 'configuration value = %s ' % (cfg.bConfigurationValue)
      for iface in cfg:
        print '  interface number = %s ' % (iface.bInterfaceNumber)
        print '  alternate setting = %s ' % (iface.bAlternateSetting)
        for ep in iface:
          print '    endpoint address = 0x%x ' % (ep.bEndpointAddress)

  
  def set_configuration(self, logical_cfg=0):
    """ 
    Set configuration descriptor based on the cfg_logical_idx for desired 
    configuration in the hierarchy. 
    Example to set the second configuration:  
      config = dev[1]
    """
    print 'In set_configuration'
    self.cfg = self.device[logical_cfg]
    #dev.set_configuration(logical_cfg)


  def set_interface(self, logical_iface=0, logical_alt_setting=0):
    """ 
    Set interface descriptor based on interface and alternate setting numbers
    Example to access the first interface and first alternate setting:  
      iface = cfg[(0,0)]
    """
    print 'In set_interface'
    self.iface = self.cfg[(logical_iface, logical_alt_setting)]
    try:
      self.device.set_interface_altsetting(self.iface)
    except usb.core.USBError:
      pass


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
    """
    Run the replayer loop.  The loop will get each consecutive pcap 
    packet and replay it as nearly as possible.
    """
    print 'In run'
    initialized = False
    dev = self.device
    i = 0
    self.print_device_enumeration_tree()
    self.print_device_descriptor_fields()
    self.print_cfg_descriptor_fields()
    self.print_iface_descriptor_fields()
    self.print_ep_descriptor_fields()
    res = dev.is_kernel_driver_active(self.logical_iface)
    # TODO: make this more safe.  How?
    if res:
      self.device.detach_kernel_driver(self.logical_iface)

    while True:
      try:
        print 'In run: Loop ', i
        i += 1
        hdr, pack = pcap.next()
        if hdr is None:
          break # EOF

        packet = Packet(hdr, pack)
        print '\nIn run: Dumping pcap packet data ...'
        out.dump(hdr, packet.repack())

        print '\nIn run: Printing pcap field information ...'
        packet.print_pcap_fields()

        print '\nIn run: Printing pcap summary information ...'
        packet.print_pcap_summary()

        #if not initialized:
        #  print 'Not initialized, initializing descriptors ...'
        #  self.initialize_descriptors(packet)
        #  initialized = True

        self.send_usb_packet(packet)
      
        #sys.exit("In run: Early exit for debug purposes")
      except Exception:
        sys.stderr.write("An error occured in replayer run loop. Here's the traceback")
        res = dev.is_kernel_driver_active(self.logical_iface)
        if not res:
          dev.attach_kernel_driver(self.logical_iface)
        traceback.print_exc()
        sys.exit(1)



  def send_usb_packet(self, packet):
  """ 
  Send the usb packet to the device.  It will be either a control packet
  with IN or OUT direction (with respect to the host), or a non-control
  packet (Bulk, Isochronous, or Interrupt) with IN or OUT direction.
  It can also be a submission from the host or a callback from the 
  device.  In any case, there may or may not be a data payload.
  """
    print 'In send_usb_packet'
    ret_array = []
    send_array = []
    ep = usb.util.find_descriptor(self.iface, custom_match=lambda e: e.bEndpointAddress==self.ep_address)

    # Check to see if this is a setup packet.
    # It is safe to decode setup packet if setup flag is 's'
    #if packet.flag_setup == 's':
    if packet.flag_setup == 's':
      #
      print 'In send_usb_packet: this is a setup packet'
      bmRequestType, bmRequest, wValue, wIndex = packet.data[0:3]
      #if bmRequestType == IN_DIRECTION:  # IN means get bytes to read

      # IN means read bytes from device to host.
      if bmRequestType == usb.util.ENDPOINT_IN: 
        # If no data payload then numbytes should be 0
        numbytes = packet.data[4]
        ret_array = self.device.ctrl_transfer(bmRequestType, bmRequest, wValue, wIndex, numbytes)
        print stderr, '*************    Return array before join =', ret_array
        if len(ret_array) != numbytes:
          print 'Error: %d bytes read in IN control transfer out of %d bytes we attempted to send' % (len(ret_array), numbytes)
        ret_array = ''.join([chr(x) for x in ret])
        print '*************    Return array after join =', ret_array

      # OUT means write bytes from host to device.
      elif bmRequestType == usb.util.ENDPOINT_OUT:
        # If no data payload then send_array should be None
        print 'In send_usb_packet: OUT - writing from host to device'
        send_array = packet.data[4:] 
        numbytes = self.device.ctrl_transfer(bmRequestType, bmRequest, wValue, wIndex, send_array)
        if numbytes != len(send_array):
          print 'Error: %d bytes sent in OUT control transfer out of %d bytes we attempted to send' % (numbytes, len(send_array))

    # Otherwise check to see if it is a submission packet.
    # Submission means xfer from host to USB device.
    elif packet.type == 'S':       
      print 'In send_usb_packet: this is a submission packet'
      send_array = packet.data[5:]
      print 'Packet data is: ', packet.data
      #numbytes = ep.write(self.ep_address, array, self.iface_num, TIMEOUT)

      # Can also do:
      #   dev.write(ep_address, send_array, interface_number, TIMEOUT)
      if packet.data:
        numbytes = ep.write(send_array)
        print 'Wrote %d bytes to USB device', numbytes, ', expected to write %d bytes ', len(send_array)
        if numbytes != len(send_array):
          print 'Error: %d bytes sent in submission (transfer to USB device) out of %d bytes we attempted to send' % (numbytes, len(send_array))
      else:
        print 'Packet data is empty.  Not sending any data'

    # Otherwise check to see it it is a callback packet.
    # Callback means xfer from USB to host.
    elif packet.type == 'C':   
      print 'In send_usb_packet: this is a callback packet'
      #array = ep.read(self.ep_address, pack.datalen, self.iface_num, TIMEOUT)
      #ret_array = ep.read(packet.datalen)
      try:
        #ret_array = ep.read(len(packet.data))
        #ret_array = ep.read(packet.length)
        #ret_array = self.device.read(self.logical_ep, packet.length, self.logical_iface)
        ret_array = self.device.read(self.ep_address, len(packet.data), self.logical_iface, 1000)
        if ret_array:
          print '%d data items read.  Data = ' % (len(ret_array), ret_array)
          if numbytes != len(ret_array):
            print 'Error: %d bytes sent in submission (transfer to USB device) out of %d bytes we attempted to send' % (numbytes, len(ret_array))
        else:
          print 'No data items were read.  '
          
      except:
        print 'Error when trying to read data from callback'
        print 'Data read was ', ret_array
        res = self.device.is_kernel_driver_active(self.logical_iface)
        if not res:
          self.device.attach_kernel_driver(self.logical_iface)
        self.reset_device()
        #print 'Printing traceback ...'
        #traceback.print_exc()



def get_arguments(argv):
  """ python usbreplay.py -h will show a help message """

  parser = optparse.OptionParser(usage="usage: %prog [options] [filename]")

  # Get the input file stream (pcap stream or filename
  parser.add_option("-f", "--file", 
                    dest="infile", 
                    default="-",
                    help="Input pcap stream (filename or '-' for stdin)"
                   )

  # Get the vendor id
  parser.add_option('-v', '--vid', 
                    dest='vid', 
                    default=VENDOR_ID, 
                    type="int", 
                    help="The vendor id for the USB device"
                   )

  # Get the product id
  parser.add_option("-p", "--pid", 
                    dest="pid", 
                    default=PRODUCT_ID, 
                    type="int", 
                    help="The product id for the USB device"
                   )

  # Get the configuration index (defaults to 0)
  parser.add_option("-c", "--cfg", 
                    dest="logical_cfg", 
                    default=LOGICAL_CFG, 
                    type="int", 
                    help="The logical configuration index of the device (starting at 0) in the device hierarchy"
                   )

  # Get the interface index (defaults to 3)
  parser.add_option("-i", "--iface", 
                    dest="logical_iface", 
                    default=LOGICAL_IFACE, 
                    type="int", 
                    help="The logical interface index in the configuration (starting at 0) in the device hierarchy"
                   )

  # Get the alternate setting index (defaults to 0)
  parser.add_option("-a", "--altsetting", 
                    dest="logical_alt_setting", 
                    default=LOGICAL_ALT_SETTING, 
                    type="int", 
                    help="The logical alternate setting index in the interface (starting at 0) in the device hierarchy"
                   )

  # Get the endpoint index (defaults to 0)
  parser.add_option("-e", "--epaddress", 
                    dest="ep_address", 
                    default=EP_ADDRESS, 
                    type="int", 
                    help="The endpoint address for the USB device in the device hierarchy"
                   )

  # Set the debug mode to quiet or verbose
  parser.add_option("-q", "--quiet", 
                    dest="debug", 
                    default=True,
                    action="store_false", 
                    help="Don't print debug messages to stdout"
                   )

#  parser.add_option("-h", "--help", 
#                    dest="help", 
#                    default=False,
#                    action="store_false", 
#                    help="Help for %prog:  
#       cat k.mon | sudo python usbreplay.py
#       cat k.mon | sudo python usbview.py | sudo python usbreplay.py"
#                   )
  options, remaining_args = parser.parse_args()
  print 'Options:  %s' % options
  print 'Remaining_args:  %s' % remaining_args
  return options


def print_options(options):
  """ 
  Utility function to print out command line options or their defaults.
  """

  print 'options.infile = %s' % options.infile
  print 'options.vid = 0x%x' % options.vid
  print 'options.pid = 0x%x ' % options.pid
  print 'options.cfg = %d' % options.logical_cfg
  print 'options.iface = %d' % options.logical_iface
  print 'options.altsetting = %d' % options.logical_alt_setting
  print 'options.epaddress = 0x%x' % options.ep_address
  if options.debug == 1: 
    dbg = 'True'
  else: 
    dbg = 'False'

  print 'options.debug = %s' % dbg


if __name__ == '__main__':
  # read a pcap stream from a file or from stdin, write the contents back
  # to stdout (for debug info), convert input stream to USB packets, and 
  # send USB packets to the device or stdout.
  #args_dict = {}
  options = get_arguments(sys.argv)
  print_options(options)
  pcap = pcapy.open_offline('-')
  out = pcap.dump_open('-')
  replayer = Replayer(options)
  replayer.run(pcap, out)

