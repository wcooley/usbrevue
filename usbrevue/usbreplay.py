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
#VENDOR_ID = 0x80ee
#PRODUCT_ID = 0x0021
#EP_ADDRESS = 0x81
#CFG_NUM = 0
#IFACE_NUM = 0
#ALT_SETTING_NUM = 0

#For capstone14.cs.pdx.edu USB keyboard 
VENDOR_ID = 0x413c    # Dell Computer Corp.
PRODUCT_ID = 0x2105   # Model L100 Keyboard
LOGICAL CFG_IDX = 0   # 1 interface, bConfigurationValue=1
LOGICAL IFACE_IDX = 0 # HID Device Descriptor.bHID=1.10, 1 ep descriptor
                      # bInterfaceClass=3 (Human Interface device)
LOGICAL ALT_SETTING_IDX = 0
LOGICAL_EP_IDX = 0    # EP 1 IN
EP_ADDRESS = 0x81     # EP 1 IN, xferType=Interrupt, bmAttributes=3 
                      # (Transfer Type, Synch Type, Usage Type)


class Replayer(object):

  def __init__(self, args_dict):
    self.vid = args_dict{"vid"}
    self.pid = args_dict{"pid"}
    self.logical_cfg = args_dict{"logical_cfg"}
    self.logical_iface = args_dict{"logical_iface"}
    self.logical_alt_setting = args_dict{"logical_alt_setting"}
    self.ep_address = args_dict{"ep_address"}
    self.logical_ep = self.ep_address[0:3]
    self.device = get_usb_device(vid, pid)
    self.ep_descriptor = usb.util.find_descriptor(iface, custom_match=lambda e: e.bEndpointAddress==self.ep_address)


  def initialize_descriptors(self, packet):
    """ 
    After getting the first pcap packet from the stream, extract the vendorId,
    productId, endpoint address from the packet.  Then, if there are differences,
    set the configuration, interface and endpoint descriptors to match what's
    in the packet.  
    """
    modified = False

    if (packet.vid != self.vid): 
      print 'Changing pcap packet vendorId from ', self.vid, ' to ', packet.vid
      self.vid = packet.vid
      modified = True

    if (packet.pid != self.pid): 
      print 'Changing pcap packet productId from ', self.pid, ' to ', packet.pid
      self.pid = packet.pid
      modified = True

    if modified:
      self.device = get_usb_device(vid, pid)

    if (packet.epnum != self.ep_address):
      print 'Changing pcap packet endpoint address from ', self.ep_address, ' to ', packet.epnum
      self.ep_address = packet.epnum

    #res = self.device.iskernel_driver_active(self.iface_num)
    #if res:
    #  self.device.detach_kernel_driver()

    set_configuration(self.logical_cfg):
    set_interface(self.iface_num, self.alt_setting_num):
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
    dev.reset()
    dev.attach_kernel_driver(iface_num)


  def print_descriptor_info():
    """ 
    Utility function to print out some basic device hierarcy numbers, ids, 
    and endpoint address.
    """
    print 'vid = ', self.vid
    print 'pid = ', self.pid
    print 'cfg_logical_idx = ', self.cfg_num
    print 'iface_logical_idx = ', self.iface_num
    print 'alt_setting_logical_idx = ', self.alt_setting
    print 'ep_logical_idx = ', self.ep_address
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
    


  # Got this from USB in a NutShell, chp 5.
  def print_device_descriptor_fields(self, dev=self.device):
    """ 
    Utility function to print out all device descriptor fields.
    """
    # bLength = Size of device descriptor in bytes (18 bytes) (number).
    print 'bLength = ' % dev.bLength
    # bDescriptorType = Device descriptor (0x01) in bytes (constant).
    print 'bDescriptorType = ' % dev.DescriptorType
    # bDescriptorType = USB spec number which device complies to (bcd). 
    print 'bcdUSB = ' % dev.bcdUSB
    # bDeviceClass = Class code assigned by USB org (0 or 0xff) (class).
    print 'bDeviceClass = ' % dev.bDeviceClass
    # bDeviceSubClass = Sublass code assigned by USB org (subClass).
    print 'bDeviceSubClass = ' % dev.bDeviceSubClass
    # bDeviceProtocol = Protocol code assigned by USB org (protocol).
    print 'bDeviceProtocol = ' % dev.bDeviceProtocol
    #bMaxPacketSize = Max packet size for zero endpoint (8, 16, 32, 64).
    print 'bMaxPacketSize = ' % dev.bMaxPacketSize
    # idVendor = Vendor ID assigned by USB org (ID).
    print 'idVendor = ' % dev.idVendor
    # idProduct = Product ID assigned by USB org (ID).
    print 'idProduct = ' % dev.idProduct
    # bcdDevice = Device release number (bcd).
    print 'bcdDevice = ' % dev.bcdDevice
    # iManufacturer = Index of manufacturer string descriptor (index).
    if dev.iManufacturer is not None:
      print 'iManufacturer = ' % dev.iManufacturer
    # iProduct = Index of product string descriptor (index).
    if dev.iProduct is not None:
      print 'iProduct = ' % dev.iProduct
    # iSerialNumber = Index of serial number string descriptor (index).
    if dev.iSerialNumber is not None:
      print 'iSerialNumber = ' % dev.iSerialNumber
    # iNumConfigurations = Number of possible configurations (integer).
    print 'bNumConfigurations = ' % dev.bNumConfigurations


  # Got this from USB in a NutShell, chp 5.
  def print_cfg_descriptor_fields(self, cfg):
    """ 
    Utility function to print out all configuration descriptor fields.
    """
    # bLength = Size of configuration descriptor in bytes (number).
    print 'bLength = ' % cfg.bLength
    # bDescriptorType = Configuration descriptor (0x02) in bytes (constant).
    print 'bDescriptorType = ' % cfg.bDescriptorType
    # bTotalLength = Total length in bytes of data returned (number). 
    # This indicates the number of bytes in the configuration hierarchy.
    print 'wTotalLength = ' % cfg.wTotalLength
    # bNumInterfaces = Total length in bytes of data returned (number). 
    print 'bNumInterfaces = ' % cfg.bNumInterfaces
    # bConfigurationValue = Value to use as an arg to select this cfg (number).
    print 'bConfigurationValue = ' % cfg.bConfigurationValue
    # iConfiguration = Index of string descriptor describing this cfg (index).
    # This string is in human readable form.
    print 'iConfiguration = ' % cfg.iConfiguration
    # bmAttributes = Bus or self powered, remote wakeup or reserved (bitmap). 
    # Remote wakeup allows device to wake up the host when the host is in suspend.
    print 'bmAttributes = ' % cfg.bmAttributes
    # bMaxPower = Maximum power consumption in 2mA units (mA).
    print 'bMaxPower = ' % cfg.bMaxPower


  # Got this from USB in a NutShell, chp 5.
  # Interface descriptor is a grouping of endpoints into a functional 
  # group performing a single feature of the device.
  def print_iface_descriptor_fields(self, iface=self.iface):
    """ 
    Utility function to print out all interface descriptor fields.
    """
    # bLength = Size of interface descriptor in bytes (number).
    print 'bLength = ' % iface.bLength
    # bDescriptorType = Interface descriptor (0x04) in bytes (constant).
    print 'bDescriptorType = ' % iface.bDescriptorType
    # bInterfaceNumber = Number of interface (number).
    print 'bInterfaceNumber = ' % iface.bInterfaceNumber
    # bAlternateSetting = Value used to select alternate setting (number).
    print 'bAlternateSetting = ' % iface.bAlternateSetting
    # bNumEndpoints = Number of endpoints used for this interface (number).
    # This excludes endpoint 0.
    print 'bNumEndpoints = ' % iface.bNumEndpoints
    # bInterfaceClass = Class code assigned by USB org (class).
    # Class could be HID, communicatins, mass storage, etc.
    print 'bInterfaceClass = ' % iface.bInterfaceClass
    # bInterfaceSubClass = SubClass code assigned by USB org (subClass).
    print 'bInterfaceSubClass = ' % iface.bInterfaceSubClass
    # bInterfaceProtocol = Protocol code assigned by USB org (protocol).
    print 'bInterfaceProtocol = ' % iface.bInterfaceProtocol
    # iInterface = Index of string descriptor describing this interface (index).
    print 'iInterface = ' % iface.iInterface



  # Got this from USB in a NutShell, chp 5.
  def print_endpoint_descriptor_fields(self, ep=self.ep):
    """ 
    Utility function to print out all endpoint descriptor fields.
    """
    # bLength = Size of endpoint descriptor in bytes (number).
    print 'bLength = ' % ep.bLength
    # bDescriptorType = Endpoint descriptor (0x05) in bytes (constant).
    print 'bDescriptorType = ' % ep.bDescriptorType
    # bEndpointAddress = Endpoint descriptor (0x05) in bytes (constant).
    # Bits 0-3=endpoint number, Bits 4-6=0, Bit 7=0(out) or 1(in).
    print 'bEndpointAddress = ' % ep.bEndpointAddress
    # Endpoint logical index is derived from Bits 0-3=endpoint number of
    # the bEndpointAddress.
    print 'endpoint logical index = ' % ep.bEndpointAddress[0:3]
    # bmAttributes = Bits 0-1=Transfer type, other bits refer to 
    # synchronization type, usage type (iso mode) (bitmap).
    # Transfer types: 00=Control, 01=Isochronous, 10=Bulk, 11=Interrupt.
    print 'bmAttributes = ' % ep.bmAttributes
    # wMaxPacketSize = Max packet size this endpoint is capable of 
    # sending or receiving (number).
    # This is the maximum payload size for this endpoint.
    print 'wMaxPacketSize = ' % ep.wMaxPacketSize
    # bInterval = Interval for polling endpoint data transfers.  
    # Value in frame counts (?).  Ignored for bulk and control endpoints.
    # Isochronous must equal 1.  This field for interrupt endpoints may 
    # range from 1 to 255 (number).
    # bInterval is used to specify the polling interval of certain transfers.
    # The units are expressed in frames.  This equates to 1ms for low/full
    # speed devices, and 125us for high speed devices.
    print 'bInterval = ' % ep.bInterval


  def print_device_enumeration_tree(self, dev):
    """ 
    Utility function to print out the device enumeration, which includes
    device configuration, interface and endpoint descriptors.
    """
    for cfg in dev:
      print 'configuration value = %s ' % (cfg.bConfigurationValue)
      for iface in cfg:
        print '  interface number = %s ' % (iface.bInterfaceNumber)
        print '  alternate setting = %s ' % (iface.bAlternateSetting)
        for ep in iface:
          print '    endpoint address = %s ' % (ep.bEndpointAddress)

  
  def set_configuration(self, cfg_num=0):
    """ 
    Set configuration descriptor based on the cfg_logical_idx for desired 
    configuration in the hierarchy. 
    Example to set the second configuration:  
      config = dev[1]
    """
    self.cfg = self.dev[cfg_num]
    #self.device.set_configuration(self.cfg_num)


  def set_interface(self, iface_num=0, alt_setting_num=0):
    """ 
    Set interface descriptor based on interface and alternate setting numbers
    Example to access the first interface and first alternate setting:  
      iface = cfg[(0,0)]
    """
    self.iface = self.cfg[(iface_num, alt_setting_num)]



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

      packet = Packet(hdr, pack)
      print "Dumping pcap packet data ..."
      out.dump(hdr, packet.repack())

      print "Printing pcap field information ..."
      packet.print_pcap_fields()

      print "Printing pcap summary information ..."
      packet.print_pcap_summary()

      if not initialized:
        initialize_descriptors(packet)
        initialized = True

      send_usb_packet(packet)
      sys.exit("Early exit for debug purposes")



  def send_usb_packet(self, packet):
    ret_array = []
    send_array = []
    ep = usb.util.find_descriptor(self.iface, custom_match=lambda e: e.bEndpointAddress==self.ep_address)

    # Check to see if this is a setup packet.
    # It is safe to decode setup packet if setup flag is 's'
    #if packet.flag_setup == 's':
    if packet.flag_setup == 's':
      #
      bmRequestType, bmRequest, wValue, wIndex = packet.data[0:3]
      #if bmRequestType == IN_DIRECTION:  # IN means get bytes to read

      # IN means read bytes from device to host.
      if bmRequestType == usb.util.ENDPOINT_IN: 
        # If no data payload then numbytes should be 0
        numbytes = packet.data[4]
        ret_array = self.device.ctrl_transfer(bmRequestType, bmRequest, wValue, wIndex, numbytes)
        print 'Return array before join =', ret_array
        if len(ret_array) != numbytes:
          print 'Error: %d bytes read in IN control transfer out of %d bytes we attempted to send' % (len(ret_array), numbytes)
        ret_array = ''.join([chr(x) for x in ret])
        print 'Return array after join =', ret_array

      # OUT means write bytes from host to device.
      else if bmRequestType == usb.util.ENDPOINT_OUT:
        # If no data payload then send_array should be None
        send_array = packet.data[4:] 
        numbytes = self.device.ctrl_transfer(bmRequestType, bmRequest, wValue, wIndex, send_array)
        if numbytes != len(send_array):
          print 'Error: %d bytes sent in OUT control transfer out of %d bytes we attempted to send' % (numbytes, len(send_array))

    # Otherwise check to see if it is a submission packet.
    # Submission means xfer from host to USB device.
    else if packet.type == 'S':       
      send_array = packet.data[5:]
      #numbytes = ep.write(self.ep_address, array, self.iface_num, TIMEOUT)

      # Can also do:
      #   dev.write(ep_address, send_array, interface_number, TIMEOUT)
      numbytes = ep.write(send_array)
      print 'Wrote %d bytes to USB device', numbytes, ', expected to write %d bytes ', len(send_array)
      if numbytes != len(send_array):
        print 'Error: %d bytes sent in submission (transfer to USB device) out of %d bytes we attempted to send' % (numbytes, len(send_array))

    # Otherwise check to see it it is a callback packet.
    # Callback means xfer from USB to host.
    else if packet.type == 'C':   
      #array = ep.read(self.ep_address, pack.datalen, self.iface_num, TIMEOUT)
      ret_array = ep.read(packet.datalen)
      print '%d data items read.  Data = ' % (len(ret_array), ret_array)
      if numbytes != len(ret_array):
        print 'Error: %d bytes sent in submission (transfer to USB device) out of %d bytes we attempted to send' % (numbytes, len(ret_array))



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
      default=PRODUCT_ID, help="The product id for the USB device")

    # Get the configuration index (defaults to 0)
    parser.add_option("-c", "--cfg", type="int", dest="logical_cfg", 
      default=LOGICAL_CONFIG_IDX, help="The logical configuration index of the device (starting at 0) in the device hierarchy")

    # Get the interface index (defaults to 3)
    parser.add_option("-i", "--iface", type="int", dest="logical_iface", 
      default=LOGICAL_IFACE_IDX, help="The logical interface index in the configuration (starting at 0) in the device hierarchy")

    # Get the alternate setting index (defaults to 0)
    parser.add_option("-a", "--altsetting", type="int", dest="logical_alt_setting", 
      default=LOGICAL_ALT_SETTING_IDX, help="The logical alternate setting index in the interface (starting at 0) in the device hierarchy")

    # Get the endpoint index (defaults to 0)
    parser.add_option("-e", "--epaddress", type="int", dest="ep_address", 
      default=EP_ADDRESS, help="The endpoint address for the USB device in the device hierarchy")

    # Set the debug mode to quiet or verbose
    parser.add_option("-q", "--quiet", action="store_false", 
      dest="debug", default=True,
      help="Don't print debug messages to stdout")

    args_dict = {}
    args_dict{"vid"} = vid
    args_dict{"pid"} = pid
    args_dict{"logical_cfg"} = logical_cfg_idx
    args_dict{"logical_iface"} = logical_iface_idx
    args_dict{"logical_alt_setting"} = logical_alt_setting_idx
    args_dict{"ep_address"} = ep_address
    return args_dict


if __name__ == '__main__':
  # read a pcap stream from a file or from stdin, write the contents back
  # to stdout (for debug info), convert input stream to USB packets, and 
  # send USB packets to the device or stdout.
  args_dict = {}
  args_dict = get_arguments(sys.argv)
  pcap = pcapy.open_offline('-')
  out = pcap.dump_open('-')
  replayer = Replayer(args_dict)
  replayer.run(pcap, out)

