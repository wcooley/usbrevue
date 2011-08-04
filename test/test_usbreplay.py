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


import logging
import os
import os.path
import struct
import sys
import unittest

import pcapy

#from utils import *
from tutil import *
from usbreplay import *
import usbreplay as usbreplay
from usbrevue import *
import usb.core
import usb.util

DEBUG=False


class TestDevice(unittest.TestCase, TestUtil):

    def setUp(self):
        global replayer
        if replayer.debug:
            sys.stderr.write( '\nIn TestDevice.setup for vid=0x%x, pid=0x%x' % (replayer.device.idVendor, replayer.device.idProduct))
        try:
            replayer.reset_device()
        except usb.core.USBError as e:
            sys.stderr.write( '\nException in setup: %s' % e)
            pass


    def tearDown(self):
        global replayer
        if replayer.debug:
            sys.stderr.write( '\nIn TestDevice.teardown for vid=0x%x, pid=0x%x\n' % (replayer.device.idVendor, replayer.device.idProduct))
        try:
            replayer.reset_device()
        except usb.core.USBError as e:
            sys.stderr.write( '\nException in teardown: %s' % e)
            pass


    def print_device(self):
        """ Print the vendor and product id's for this device """
        sys.stderr.write( '\nTesting device with vid=0x%x, pid=0x%x\n' % (replayer.device.idVendor, replayer.device.idProduct))


    def test_device(self):
        """ Test that this usb device really exists """
        global replayer
        if replayer.debug:
            sys.stderr.write( '\nIn TestDevice.test_device for vid=0x%x, pid=0x%x' % (replayer.device.idVendor, replayer.device.idProduct))
        # find our device
        dev = usb.core.find(idVendor=replayer.device.idVendor, idProduct=replayer.device.idProduct)
        # Was device found?
        self.assertNotEqual(dev, None, 'No device available with vid=%s, pid=%s' % (replayer.device.idVendor, replayer.device.idProduct))


    def test_eps(self):
        """ Test all used endpoints for this usb device """
        global replayer
        if replayer.debug:
            sys.stderr.write( '\nIn TestDevice.test_eps for vid=0x%x, pid=0x%x' % (replayer.device.idVendor, replayer.device.idProduct))
        dev = usb.core.find(idVendor=replayer.device.idVendor, idProduct=replayer.device.idProduct)
        for cfg in dev:
            self.assertEqual(cfg.bConfigurationValue, replayer.cfg.bConfigurationValue)
            for iface in cfg:
                self.assertEqual(iface.bInterfaceNumber, replayer.iface.bInterfaceNumber)
                ep_found = False
                for ep in iface:
                    for i in range(len(replayer.eps)):
                        if replayer.debug:
                            sys.stderr.write( '\n%d: ep address is 0x%x\n' % (i, ep.bEndpointAddress))
                            sys.stderr.write( '\n%d: replayer eps = %s' % (i, replayer.eps))
                            sys.stderr.write( '\n%d: ep.bEndpointAddress = 0x%x' % (i, ep.bEndpointAddress))
                            sys.stderr.write( '\nreplayer.eps = %s' % replayer.eps )
                        if ep.bEndpointAddress in replayer.eps:
                            if replayer.debug:
                                sys.stderr.write( '\nGot an ep')
                            ep_found = True
                            if replayer.debug:
                                sys.stderr.write( '\nEndpoint %d found' % ep.epnum)

                    for j in range(len(replayer.poll_eps)):
                        if replayer.debug:
                            sys.stderr.write( '\n%d: replayer.poll_eps = %s' % (j, replayer.poll_eps))
                            sys.stderr.write( '\n%d: replayer.poll_eps[j].bEndpointAddress = %s' % (j, replayer.poll_eps[j].bEndpointAddress))
                        if ep.bEndpointAddress == replayer.poll_eps[j].bEndpointAddress:
                            if replayer.debug:
                                sys.stderr.write( '\nGot a poll ep')
                            ep_found = True
                            if replayer.debug:
                                sys.stderr.write( '\nEndpoint at address 0x%x found' % (ep.bEndpointAddress))

                    self.assertTrue(ep_found, 'No endpoint could be found')



    def test_replayer(self):
        """ Test for a valid replayer instance """
        global replayer
        if replayer.debug:
            sys.stderr.write( '\nIn TestDevice.test_replayer for vid=0x%x, pid=0x%x' % (replayer.device.idVendor, replayer.device.idProduct))
        self.assertNotEqual(replayer, None, 'Replayer not instantiated')
          

    def atest_print_descriptors(self):
        """ Print all usb descriptors """
        global replayer
        replayer.print_all()


    def test_device_descriptor(self):
        """ Verify some device descriptor fields.  """
        global replayer
        if replayer.debug:
            sys.stderr.write( '\nIn TestDevice.test_device_descriptor for vid=0x%x, pid=0x%x' % (replayer.device.idVendor, replayer.device.idProduct))
        devdesc = replayer.device
        #dsc = self.backend.get_device_descriptor(self.device)
        self.assertEqual(devdesc.bLength, 18, 'Incorrect device descriptor length')
        self.assertEqual(devdesc.bDescriptorType, usb.util.DESC_TYPE_DEVICE, 'Incorrect bDescriptorType')
        bcdUSBs = [0x0110, 0x0200, 0x300]
        self.assertIn(devdesc.bcdUSB, bcdUSBs, 'Incorrect device descriptor bcdUSB')
        #self.assertEqual(devdesc.idVendor, devinfo.ID_VENDOR, 'Incorrect device descriptor idVendor')
        self.assertNotEqual(devdesc.idVendor, 0, 'Incorrect device descriptor idVendor')
        #self.assertEqual(devdesc.idProduct, devinfo.ID_PRODUCT, 'Incorrect device descriptor idProduct')
        self.assertNotEqual(devdesc.idProduct, 0, 'Incorrect device descriptor idProduct')
        #self.assertEqual(devdesc.bcdDevice, 0x0001, 'Incorrect device descriptor bcdDevice')
        self.assertNotEqual(devdesc.bcdDevice, 0, 'Incorrect device descriptor bcdDevice')
        #self.assertEqual(devdesc.iManufacturer, 0x01, 'Incorrect device descriptor iManufacturer')
        #self.assertEqual(devdesc.iProduct, 0x02, 'Incorrect device descriptor iProduct')
        #self.assertEqual(devdesc.iSerialNumber, 0x00, 'Incorrect device descriptor iSerialNumber')
        #self.assertEqual(devdesc.bNumConfigurations, 0x01, 'Incorrect device descriptor bNumConfigurations')
        self.assertNotEqual(devdesc.bNumConfigurations, 0, 'Incorrect device descriptor bNumConfigurations')
        #self.assertEqual(devdesc.bMaxPacketSize, 64, 'Incorrect device descriptor bMaxPacketSize')
        self.assertEqual(devdesc.bDeviceClass, 0x00, 'Incorrect device descriptor bDeviceClass')
        self.assertEqual(devdesc.bDeviceSubClass, 0x00, 'Incorrect device descriptor bDeviceSubClass')
        self.assertEqual(devdesc.bDeviceProtocol, 0x00, 'Incorrect device descriptor bDeviceProtocol')
        if replayer.debug:
            sys.stderr.write( '\nActual device descriptor fields are ...')
            replayer.print_device_descriptor_fields()


    def test_cfg_descriptor(self):
        """ Verify some configuration descriptor fields.  """
        global replayer
        self.print_device()
        if replayer.debug:
            sys.stderr.write( '\nIn TestDevice.sys.stderr.write(_cfg_descriptor_fields for vid=0x%x, pid=0x%x' % (replayer.device.idVendor, replayer.device.idProduct))
        cfgdesc = replayer.cfg
        # bLength = Size of configuration descriptor in bytes (number).
        self.assertEqual(cfgdesc.bLength, 9, 'Incorrect configuration descriptor bLength')
        # bDescriptorType = Configuration descriptor (0x02) in bytes (constant).
        self.assertEqual(cfgdesc.bDescriptorType, 0x2, 'Incorrect configuration descriptor bDescriptorType')
        # bTotalLength = Total length in bytes of data returned (number).
        self.assertNotEqual(cfgdesc.wTotalLength, 0, 'Incorrect configuration descriptor wTotalLength')
        # This indicates the number of bytes in the configuration hierarchy.
        self.assertNotEqual(cfgdesc.bNumInterfaces, 0, 'Incorrect configuration descriptor bNumInterfaces')
        # bNumInterfaces = Total length in bytes of data returned (number).
        # bConfigurationValue = Value to use as an arg to select this cfg (number).
        self.assertNotEqual(cfgdesc.bConfigurationValue, 0, 'Incorrect configuration descriptor bConfigurationValue')
        # iConfiguration = Index of string descriptor describing this cfg (index).
        # This string is in human readable form.
        #self.assertEqual(cfgdesc.iConfiguration, 0, 'Incorrect configuration descriptor iConfiguration')
        # bmAttributes = Bus or self powered, remote wakeup or reserved (bitmap).
        self.assertNotEqual(cfgdesc.bmAttributes, 0, 'Incorrect configuration descriptor bmAttributes')
        # bMaxPower = Maximum power consumption in 2mA units (mA).
        self.assertNotEqual(cfgdesc.bMaxPower, 0, 'Incorrect configuration descriptor bMaxPower')
        if replayer.debug:
            sys.stderr.write( '\nActual configuration descriptor fields are ...')
            replayer.print_cfg_descriptor_fields()


    def test_iface_descriptor(self):
        """ Verify some interface descriptor fields.  """
        global replayer
        if replayer.debug:
            sys.stderr.write( '\nIn TestDevice.test_iface_descriptor for vid=0x%x, pid=0x%x' % (replayer.device.idVendor, replayer.device.idProduct))
        ifacedesc = replayer.iface

        # bLength = Size of interface descriptor in bytes (number).
        self.assertEqual(ifacedesc.bLength, 9, 'Incorrect interface descriptor bLength')

        # bDescriptorType = Interface descriptor (0x04) in bytes (constant).
        self.assertEqual(ifacedesc.bDescriptorType, 0x04, 'Incorrect interface descriptor bDescriptorType')

        # bInterfaceNumber = Number of interface (number).
        #sys.stderr.write( 'bInterfaceNumber = ', iface.bInterfaceNumber)

        # bAlternateSetting = Value used to select alternate setting (number).
        #sys.stderr.write( 'bAlternateSetting = ', iface.bAlternateSetting)

        # bNumEndpoints = Number of endpoints used for this interface (number).
        # This excludes endpoint 0.
        #sys.stderr.write( 'bNumEndpoints = ', iface.bNumEndpoints)
        self.assertNotEqual(ifacedesc.bNumEndpoints, 0, 'Incorrect interface descriptor bNumEndpoints')

        # bInterfaceClass = Class code assigned by USB org (class).
        # Class could be HID, communicatins, mass storage, etc.
        #sys.stderr.write( 'bInterfaceClass = ', iface.bInterfaceClass)

        # bInterfaceSubClass = SubClass code assigned by USB org (subClass).
        #sys.stderr.write( 'bInterfaceSubClass = ', iface.bInterfaceSubClass)

        # bInterfaceProtocol = Protocol code assigned by USB org (protocol).
        #sys.stderr.write( 'bInterfaceProtocol = ', iface.bInterfaceProtocol)

        # iInterface = Index of string descriptor describing this interface (index).
        #sys.stderr.write( 'iInterface = ', ifacedesc.iInterface)

        if replayer.debug:
            sys.stderr.write( '\nActual interface descriptor fields are ...')
            replayer.print_iface_descriptor_fields()


    def test_ep_descriptor(self):
        """ Print out selected poll endpoint descriptor fields.  """
        global replayer
        if replayer.debug:
            sys.stderr.write( '\nIn TestDevice.test_ep_descriptor for vid=0x%x, pid=0x%x' % (replayer.device.idVendor, replayer.device.idProduct))
        for i in range(len(replayer.poll_eps)):
            poll_ep = replayer.poll_eps[i]
            self.print_ep_info(poll_ep)


    def print_ep_info(self, ep):
        """ Print out some poll endpoint information """
        if replayer.debug:
            sys.stderr.write( '\nIn TestDevice.print_ep_info for vid=0x%x, pid=0x%x' % (replayer.device.idVendor, replayer.device.idProduct))
        if not ep.bEndpointAddress:
            sys.stderr.write( '\nThis endpoint does not have a valid address')
            return

        if replayer.debug:
            sys.stderr.write( '\nPoll endpoints are: %s' % ep.bEndpointAddress)
            sys.stderr.write( '\nActual poll endpoint descriptor fields are ...')
            replayer.print_ep_descriptor_fields(ep)

        # bLength = Size of endpoint descriptor in bytes (number).
        if ep.bLength:
            self.assertEqual(ep.bLength, 7, 'Incorrect endpoint descriptor bLength')

        # bDescriptorType = Endpoint descriptor (0x05) in bytes (constant).
        self.assertEqual(ep.bDescriptorType, 0x5, 'Incorrect endpoint descriptor bDescriptorType')

        # bEndpointAddress = Endpoint descriptor (0x05) in bytes (constant).
        # Bits 0-3=endpoint number, Bits 4-6=0, Bit 7=0(out) or 1(in).
        #sys.stderr.write( 'bEndpointAddress = 0x%x' % ep.bEndpointAddress)
        # bmAttributes = Bits 0-1=Transfer type, other bits refer to
        # synchronization type, usage type (iso mode) (bitmap).
        # Transfer types: 00=Control, 01=Isochronous, 10=Bulk, 11=Interrupt.
        #sys.stderr.write( 'bmAttributes = ', ep.bmAttributes)

        # wMaxPacketSize = Max packet size this endpoint is capable of
        # sending or receiving (number).
        # This is the maximum payload size for this endpoint.
        #sys.stderr.write( 'wMaxPacketSize = ', ep.wMaxPacketSize)
        self.assertNotEqual(ep.wMaxPacketSize, 0, 'Incorrect endpoint descriptor wMaxPacketSize')

        # bInterval = Interval for polling endpoint data transfers.
        # Value in frame counts (?).  Ignored for bulk and control endpoints.
        # Isochronous must equal 1.  This field for interrupt endpoints may
        # range from 1 to 255 (number).
        # bInterval is used to specify the polling interval of certain transfers.
        # The units are expressed in frames.  This equates to 1ms for low/full
        # speed devices, and 125us for high speed devices.
        self.assertNotEqual(ep.bInterval, 0, 'Incorrect endpoint descriptor bInterval')

        
def get_usb_devices():
    """ Get all non-hub usb devices on this computer """
    devices = []
    devices = usb.core.find(find_all=True)
    # Remove all hub devices from the list
    for i in range(len(devices)):
        for dev in devices:
            if dev.bDeviceClass == 0x9:
                devices.remove(dev)
            for cfg in dev:
                for iface in cfg:
                    if iface.bInterfaceClass == 0x9:
                        if dev in devices:
                            devices.remove(dev)
    return devices

                                                                            
def print_devices(devices):
    """ 
    Print the vendor and product ids of this usb device.
    """
    sys.stderr.write( '\nDevices being tested are ...')
    for dev in devices:
       sys.stderr.write( '\nvid = 0x%x,  pid = 0x%x' % (dev.idVendor, dev.idProduct)  )
    sys.stderr.write( '\n')


if __name__ == '__main__':
    global replayer
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    devices = []
    devices = get_usb_devices()
    #sys.stderr.write('\n%s' % devices)
    try:
        for dev in devices:
            replayer = usbreplay.Replayer(vid=dev.idVendor, pid=dev.idProduct, debug=DEBUG)
            suite.addTest(loader.loadTestsFromTestCase(TestDevice))
            unittest.TextTestRunner(verbosity=2).run(suite)
            suite = unittest.TestSuite()
    except usb.core.USBError as e:
        if str(e) == "Unknown Error":
            pass
        sys.stderr.write('\n%s' % e)

