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

import sys
import usb.core
import usb.util
import pcapy
from usbrevue import Packet
import optparse
import traceback
import time
import math
import signal
from threading import Thread

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
DEBUG = False



class Timing(object):
    def __init__(self, max_wait=5, debug=False):
        self.prev_ts = None
        self.max_wait = max_wait
        self.debug = debug

    def wait_relative(self, ts_sec, ts_usec):
        """
        On first call, returns instantly. On subsequent calls, waits for the
        difference between this call's timestamp and the previous call's
        timestamp.
        """
        ts = ts_sec + ts_usec/1e6
        if self.prev_ts is not None:
            self.sleep(ts - self.prev_ts)
        self.prev_ts = ts

    def sleep(self, dur):
        """
        Sleep for dur seconds. Returns instantly if dur < 0, and won't
        sleep for longer than self.max_wait. 
        """
        now = time.time()
        until = now + min(dur, self.max_wait)
        if self.debug:
            print "waiting for %s" % (until - now)
        while now < until:
            time.sleep(until-now)
            now = time.time()



class PollThread(Thread):
    def __init__(self, ep):
        Thread.__init__(self)
        self.ep = ep

    def run(self):
        while 1:
            try:
                r = self.ep.read(self.ep.wMaxPacketSize)
                print ' '.join(map(lambda b: "%02x" % b, r))
            except usb.core.USBError as e:
                if str(e) == "Operation timed out":
                    # there must be a better way
                    continue
                print e
                break



class Replayer(object):
    """
    Class that encapsulates functionality to replay pcap steam packets 
    to a USB device.
    """

    #def __init__(self, infile='-', vid=VENDOR_ID, pid=PRODUCT_ID, logical_cfg=LOGICAL_CFG, logical_iface=LOGICAL_IFACE, logical_alt_setting=LOGICAL_ALT_SETTING, ep_address=EP_ADDRESS, debug=True):
    def __init__(self, vid=VENDOR_ID, pid=PRODUCT_ID, logical_cfg=LOGICAL_CFG, logical_iface=LOGICAL_IFACE, logical_alt_setting=LOGICAL_ALT_SETTING, ep_address=EP_ADDRESS, infile='-', debug=DEBUG):
        """
        Constructor to initialize to the various usb fields, such as vendor
        id, product id, configuration, interface, alternate setting and 
        endpoint address.  Based on vendor and product id, it will get
        the USB device and set the appropriate parameters.  The options
        argument contains either defaults values for these fields or 
        user designated values.
        """
        self.debug = debug
        if self.debug:
            print '\nIn Replayer.__init__'
        self.init_handlers()
        self.urbs = []
        self.vid = vid
        self.pid = pid
        self.logical_cfg = logical_cfg
        self.logical_iface = logical_iface
        self.logical_alt_setting = logical_alt_setting

        self.device = self.get_usb_device(self.vid, self.pid)
        if self.device is None:
            raise ValueError('The device with vid=0x%x, pid=0x%x is not connected') % (self.vid, self.pid)

        if self.device.is_kernel_driver_active(self.logical_iface):
            if self.debug: print 'Detaching kernal driver'
            self.device.detach_kernel_driver(self.logical_iface)

        self.set_configuration(self.logical_cfg)
        self.set_interface(self.logical_iface, self.logical_alt_setting)
        if self.debug:
            self.print_descriptor_info()

        # sort all endpoints on our interface: incoming interrupts go into poll_eps, and
        # all others go into eps, indexed by epnum
        self.poll_eps = []
        self.eps = {0x00: None, 0x80: None}
        for ep in self.iface:
            if usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_IN and \
                usb.util.endpoint_type(ep.bmAttributes) == usb.util.ENDPOINT_TYPE_INTR:
                self.poll_eps.append(ep)
            else:
                self.eps[ep.bEndpointAddress] = ep

        self.timer = Timing(debug=self.debug)


    def reset_device(self):
        """ 
        Utility function to reset device. 
        and endpoint address.
        """
        if self.debug:
            print '\nIn Replayer.reset_device: resetting device'
        self.device.reset()
        res = self.device.is_kernel_driver_active(self.logical_iface)
        if not res:
            print 'Re-attaching kernal driver'
            self.device.attach_kernel_driver(self.logical_iface)


    def print_all(self):
        print '\n\nDevice enumeration tree ...'
        self.print_device_enumeration_tree()
        print '\nDevice descriptor fields ...'
        self.print_device_descriptor_fields()
        print '\nConfiguration descriptor fields ...'
        self.print_cfg_descriptor_fields()
        print '\nInterface descriptor fields ...'
        self.print_iface_descriptor_fields()
        print '\nEndpoint descriptor fields ...'
        self.print_ep_descriptor_fields(self.poll_eps[0])


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
    def get_usb_device(self, vid=VENDOR_ID, pid=PRODUCT_ID):
        """ 
        Get the usb.core.Device object based on vendorId and productId.  
        """
        if self.debug:
            print '\nIn Replayer.get_usb_device'
        device = usb.core.find(idVendor=vid, idProduct=pid)
        if device is None:
            raise ValueError('USB Device with vendorId', vid, ', and productId', pid, 'not found')
        return device
      

    # Configuration descriptor specifies values such as amount of power
    # this particular configuration uses, if device is self or bus 
    # powered and number of interfaces it has. Few devices have more
    # than 1 configuration, so cfg index will usually be empty and we will
    # simply select the only active configuration at index 0. Only 1 
    # configuration may be enabled at a time
    def set_configuration(self, logical_cfg=0):
        """ 
        Set configuration descriptor based on the cfg_logical_idx for desired 
        configuration in the hierarchy. 
        Example to set the second configuration:  
          config = dev[1]
        """
        if self.debug:
            print '\nIn Replayer.set_configuration'
        self.cfg = self.device[logical_cfg]


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
    def set_interface(self, logical_iface=0, logical_alt_setting=0):
        """ 
        Set interface descriptor based on interface and alternate setting numbers
        Example to access the first interface and first alternate setting:  
          iface = cfg[(0,0)]
        """
        if self.debug:
            print '\nIn Replayer.set_interface'
        self.iface = self.cfg[(logical_iface, logical_alt_setting)]
        try:
            self.device.set_interface_altsetting(self.iface)
        except usb.core.USBError as e:
            print '\nIn Replayer.set_interface ', e
            sys.stderr.write("Error trying to set interface alternate setting")
            pass


    def run(self, pcap, out):
        """
        Run the replayer loop.  The loop will get each consecutive pcap 
        packet and replay it as nearly as possible.
        """
        MAX_LOOPS = 10
        loops = 0
        if self.debug:
            self.print_device_enumeration_tree()
            self.print_device_descriptor_fields()
            self.print_cfg_descriptor_fields()
            self.print_iface_descriptor_fields()

        for ep in self.poll_eps:
            if self.debug: print 'Spawning poll thread for endpoint 0x%x' % ep.bEndpointAddress
            thread = PollThread(ep)
            thread.start()

        if self.debug:
            print 'Entering Replayer run loop'
        while True:
            try:
                if self.debug:
                    print '------------------------------------------'
                    print '\nIn Replayer.run: Starting loop ', loops
                loops += 1
                hdr, pack = pcap.next()
                if hdr is None:
                    break # EOF

                packet = Packet(hdr, pack)
                if self.debug:
                    #print '\nIn run: Dumping pcap packet data ...'
                    #out.dump(hdr, packet.repack())
                    print '\nIn Replayer.run: Printing pcap field information ...'
                    packet.print_pcap_fields()
                    print '\nIn Replayer.run: Printing pcap summary information ...'
                    packet.print_pcap_summary()

                # Wait for awhile before sending next usb packet
                self.timer.wait_relative(packet.ts_sec, packet.ts_usec)
                self.send_usb_packet(packet)
            except Exception:
                sys.stderr.write("An error occured in replayer run loop. Here's the traceback")
                traceback.print_exc()
                break
        #wait for keyboard interrupt, let poll threads continue
        while True:
            time.sleep(5)


    def send_usb_packet(self, packet):
        """ 
        Send the usb packet to the device.  It will be either a control packet
        with IN or OUT direction (with respect to the host), or a non-control
        packet (Bulk, Isochronous, or Interrupt) with IN or OUT direction.
        It can also be a submission from the host or a callback from the 
        device.  In any case, there may or may not be a data payload.
        """
        if self.debug:
            print '\nIn Replayer.send_usb_packet'

        # Check to see if this is a setup packet.
        if packet.is_setup_packet:
            self.send_setup_packet(packet)
        else:
            # Check that packet is on an endpoint we care about
            if packet.epnum not in self.eps:
                if self.debug: print "Ignoring endpoint %s" % hex(packet.epnum)
                return

            ep = self.eps[packet.epnum]

            # Otherwise check to see if it is a submission packet.
            # Submission means xfer from host to USB device.
            if packet.event_type == 'S':       
                self.send_submission_packet(packet, ep)

            # Otherwise check to see it it is a callback packet.
            # Callback means xfer from USB device to host.
            elif packet.event_type == 'C':   
                self.get_callback(packet)


    def send_setup_packet(self, packet):
        if self.debug:
            print '\nIn Replayer.send_usb_packet: this is a setup packet with urb id = ', packet.urb
        #if packet.urb not in self.urbs:
        if self.debug:
            print 'Appending 0x%x to urb list' % packet.urb
        self.urbs.append(packet.urb)
        if self.debug:
            print 'Current urbs = ', self.urbs

        # IN means read bytes from device to host.
        if (packet.epnum == 0x80):
            self.ctrl_transfer_from_device(packet)
        # OUT means write bytes from host to device.
        elif (packet.epnum == 0x00):
            self.ctrl_transfer_to_device(packet)


    def ctrl_transfer_to_device(self, packet):
        # If no data payload then send_array should be None
        if self.debug:
            print '\nIn Replayer.send_usb_packet: Setup packet direction is OUT - writing from host to device for packet urb id = ', packet.urb
        numbytes = self.device.ctrl_transfer(packet.setup.bmRequestType, packet.setup.bRequest, packet.setup.wValue, packet.setup.wIndex, packet.data)
        if numbytes != len(packet.data):
            print 'Error: %d bytes sent in OUT control transfer out of %d bytes we attempted to send' % (numbytes, len(packet.data))


    def ctrl_transfer_from_device(self, packet):
        # If no data payload then numbytes should be 0
        if self.debug:
            print 'IN direction (reading bytes from device to host for packet urb id = ', packet.urb
        ret_array = self.device.ctrl_transfer(packet.setup.bmRequestType, packet.setup.bRequest, packet.setup.wValue, packet.setup.wIndex, packet.setup.wLength)
        if len(ret_array) != packet.length:
            print 'Error: %d bytes read in IN control transfer out of %d bytes we attempted to read' % (len(ret_array), packet.length)


    def send_submission_packet(self, packet, ep):
        # Otherwise check to see if it is a submission packet.
        # A submission can be either a read or write so check direction.
        # Submission means xfer from host to USB device.
        # Every submission or setup packet should have a callback?
        if self.debug:
            print '\nIn Replayer.send_usb_packet: this is a submission packet for urb id = ', packet.urb
        #if packet.urb not in self.urbs:
        if self.debug:
            print 'Appending 0x%x to urb list' % packet.urb
        self.urbs.append(packet.urb)
        if self.debug:
            print 'Current urbs = ', self.urbs

        if usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_IN:
            self.read_from_device(packet, ep)
        else:
            self.write_to_device(packet, ep)


    def write_to_device(self, packet, ep):
        numbytes = 0  
        if packet.data:
            numbytes = ep.write(packet.data)
        else:
            if self.debug:
                print 'Packet data is empty.  No submission data to send.'
        if self.debug:
            print 'Wrote %d submission bytes to USB device, expected to write %d bytes ' %(numbytes, packet.len_cap)
        if numbytes != packet.len_cap:
            print 'Error: %d bytes sent in submission (transfer to USB device) out of %d bytes we attempted to send' % (numbytes, packet.len_cap)


    def read_from_device(self, packet, ep):
        TIMEOUT = 1000
        ret_array = []
        if self.debug:
            print 'Attempting to read %d bytes from device to host' % packet.length
        if packet.length:
#            ret_array = self.device.read(self.ep_address, len(packet.data), self.logical_iface, 1000)
            try:
                ret_array = ep.read(packet.length, TIMEOUT)
            except usb.core.USBError as e:
                print '\nIn Replayer.read_from_device ', e

            #ret_array = self.device.read(ep, packet.length,  self.logical_iface, TIMEOUT)
            if self.debug:
                print 'Finished attempting to read %d callback bytes from device to host' % packet.length
                print 'Actually read %d callback bytes from device to host' % len(ret_array)
            if ret_array:
                if self.debug:
                    print '%d data items read from callback packet.  Data = %s' % (len(ret_array), ret_array)
                if packet.length != len(ret_array):
                    print 'Error: %d bytes sent in submission (transfer to USB device) out of %d bytes we attempted to send' % (packet.length, len(ret_array))
            else:
                if self.debug:
                    print 'No data items were read from callback packet.  '
        else:
            if self.debug:
                print 'No callback bytes to read: length of packet.data is 0'
            

    def get_callback(self, packet):
        if self.debug:
            print '\nIn Replayer.send_usb_packet: this is a callback packet for urb id = ', packet.urb
        if packet.urb in self.urbs:
            if self.debug:
                print 'Removing 0x%x from urb list' % packet.urb
            self.urbs.remove(packet.urb)
        else:
            print 'Packet urb id=0x%x has a callback but not a submission' % packet.urb
        if self.debug:
            print 'Current urbs = ', self.urbs


    def keyboard_handler(self, signum, frame):
        print 'Signal handler called with signal ', signum
        self.reset_device()
        sys.exit(0)


    def init_handlers(self):
        signal.signal(signal.SIGINT, self.keyboard_handler)


    def print_descriptor_info(self):
        """ 
        Utility function to print out some basic device hierarcy numbers, ids, 
        and endpoint address.
        """
        print 'vid = 0x%x' % self.vid
        print 'pid = 0x%x' % self.pid
        print 'logical_cfg_idx = %d' % self.logical_cfg
        print 'logical_iface_idx = %d' % self.logical_iface
        print 'logical_alt_setting_idx = %d' % self.logical_alt_setting
      

    # Got this from USB in a NutShell, chp 5.
    def print_device_descriptor_fields(self):
        """ 
        Utility function to print out all device descriptor fields.
        """
        #print '--------------------------------'
        #print 'In Replayer.print_device_descriptor_fields'
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
    def print_ep_descriptor_fields (self, ep):
        """ 
        Utility function to print out all endpoint descriptor fields.
        """
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
        #print '--------------------------------'
        #print 'In Replayer.print_device_enumeration_tree'
        dev = self.device
        for cfg in dev:
            print 'configuration value = %s ' % (cfg.bConfigurationValue)
            for iface in cfg:
                print '  interface number = %s ' % (iface.bInterfaceNumber)
                print '  alternate setting = %s ' % (iface.bAlternateSetting)
                for ep in iface:
                    print '    endpoint address = 0x%x ' % (ep.bEndpointAddress)



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

    # Set the debug mode to quiet or verbose
    parser.add_option("-q", "--quiet", 
                      dest="debug", 
                      default=False,
                      action="store_false", 
                      help="Don't print debug messages to stdout"
                     )
    
    options, remaining_args = parser.parse_args()
    if options.debug:
        print 'Options:  %s' % options
        print 'Remaining_args:  %s' % remaining_args
    return options


def print_options(options):
    """ 
    Utility function to print out command line options or their defaults.
    """

    #if options.debug:
    print 'options.infile = %s' % options.infile
    print 'options.vid = 0x%x' % options.vid
    print 'options.pid = 0x%x ' % options.pid
    print 'options.cfg = %d' % options.logical_cfg
    print 'options.iface = %d' % options.logical_iface
    print 'options.altsetting = %d' % options.logical_alt_setting
    print 'options.debug = %d' % options.debug


if __name__ == '__main__':
    # read a pcap stream from a file or from stdin, write the contents back
    # to stdout (for debug info), convert input stream to USB packets, and 
    # send USB packets to the device or stdout.
    #print '1'
    options = get_arguments(sys.argv)
    #print '2'
    print_options(options)
    #print '3'
    pcap = pcapy.open_offline(options.infile)
    #print '4'
    out = None
    if not sys.stdout.isatty():
    	out = pcap.dump_open('-')
     #print '5'
    replayer = Replayer(options.vid, options.pid, options.logical_cfg, options.logical_iface, options.logical_alt_setting, options.ep_address, options.infile, options.debug)
    #print '6'
    replayer.run(pcap, out)
    #print '7'

