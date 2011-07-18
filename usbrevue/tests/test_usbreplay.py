#!/usr/bin/env python

import logging
import os
import os.path
import struct
import sys
import unittest
#import utils
from array import array
from functools import partial
from logging import debug
from pprint import pformat
import usb.backend.libusb01 as libusb01
import usb.backend.libusb10 as libusb10
import usb.backend.openusb as openusb
import usb.backend


import pcapy

from tutil import *
from usbreplay import *
import usbreplay as usbreplay
from usbrevue import *
from util import apply_mask
import usb.core
import usb.util

#logging.basicConfig(level=logging.DEBUG)

#class TestPackedFields(unittest.TestCase,TestUtil):
#class TestReplayer(unittest.TestCase, TestUtil):
class MyBackend(usb.backend.IBackend):
    pass

class TestDevice(unittest.TestCase, TestUtil, usb.backend.IBackend):

    replayer = usbreplay.Replayer()
    #backend = MyBackend()

    #def __init__(self, backend):
        #unittest.TestCase.__init__(self)
        #self.backend = backend

    def setup(self):
        if self.replayer.debug:
            print 'In TestDevice.setup'

        self.replayer = usbreplay.Replayer()
        #self.replayer = usbreplay.Replayer(self.device.idVendor, self.device.idProduct)
        self.assertNotEqual(self.replayer, None, 'Replayer not instantiated')
        if self.replayer.debug:
            print 'replayer = ', self.replayer.__name__
    
        #self.assertNotEqual(self.backend, None, 'In setup, backend not defined')
        self.replayer.reset_device()

        # find device from ep?



    #def test_backend(self):
    #   for m in (libusb10, libusb01, openusb):
    #       print '\nGetting a backend?'
    #       b = m.get_backend()
    #       if b is not None:
    #           #sys.stderr.write('Found b backend', b.__name__)
    #           sys.stderr.write('Found m backend %s \n' % m.__name__)
    #           self.backend = b
    #           return
    #           #suite.addTest(TestDevice(b))
    #       else:
    #           sys.stderr.write('Backend %s is not available \n' % m.__name__)


    
    def test_for_device(self):
        # Send the 'test' string to the first OUT endpoint found:
        # find our device
        dev = usb.core.find(idVendor=self.replayer.device.idVendor, idProduct=self.replayer.device.idProduct)
        # Was device found?
        self.assertNotEqual(dev, None, 'No device available with vid=%s, pid=%s' % (self.replayer.device.idVendor, self.replayer.device.idProduct))


    def test_kernel_driver(self):
        res = self.replayer.device.is_kernel_driver_active(self.replayer.logical_iface)
        if self.replayer.debug:
            print '\nResult of is kernel driver active is', res
        self.assertEqual(res, True)
        if self.replayer.debug:
            print 'Detaching kernal driver'
        res = self.replayer.device.detach_kernel_driver(self.replayer.logical_iface)
        if self.replayer.debug:
            print 'Result of detach is', res
   
    
    #def test_for_ep_doesnt_work(self):
        # set the active configuration. With no arguments, the first
        # configuration will be the active one
        #dev.set_configuration()
        #self.alt_setting = dev.get_interface_altsetting()  # first interface
        # get an endpoint instance
        #self.ep = usb.util.find_descriptor(
        #     #dev.get_interface_altsetting(),   # first interface
        #     self.replayer.logical_alt_setting, # first interface?
        #     # match the first OUT endpoint
        #     custom_match = \
        #        lambda e: \
        #            usb.util.endpoint_direction(e.bEndpointAddress) == \
        #            usb.util.ENDPOINT_OUT
        #)
        # write the data
        #res = ep.write('test')
        #print 'Result of ep.write is', res


    def test_for_eps(self):
        dev = usb.core.find(idVendor=self.replayer.device.idVendor, idProduct=self.replayer.device.idProduct)
        for cfg in dev:
            self.assertEqual(cfg.bConfigurationValue, self.replayer.cfg.bConfigurationValue)
            for iface in cfg:
                self.assertEqual(iface.bInterfaceNumber, self.replayer.iface.bInterfaceNumber)
                ep_found = False
                for ep in iface:
                    for i in range(len(self.replayer.eps)):
                        if self.replayer.debug:
                            print '\n%d: ep address is 0x%x\n' % (i, ep.bEndpointAddress)
                            print '%d: replayer eps = %s' % (i, self.replayer.eps)
                            print '%d: ep.bEndpointAddress = 0x%x' % (i, ep.bEndpointAddress)
                            print 'self.replayer.eps =', self.replayer.eps 
                        if ep.bEndpointAddress in self.replayer.eps:
                            if self.replayer.debug:
                                print 'Got an ep'
                            ep_found = True
                            if self.replayer.debug:
                                print 'Endpoint %d found' % ep.epnum

                    for j in range(len(self.replayer.poll_eps)):
                        if self.replayer.debug:
                            print '%d: self.replayer.poll_eps = %s' % (j, self.replayer.poll_eps)
                            print '%d: self.replayer.poll_eps[j].bEndpointAddress = %s' % (j, self.replayer.poll_eps[j].bEndpointAddress)
                        if ep.bEndpointAddress == self.replayer.poll_eps[j].bEndpointAddress:
                            if self.replayer.debug:
                                print 'Got a poll ep'
                            ep_found = True
                            if self.replayer.debug:
                                print 'Endpoint at address 0x%x found' % (ep.bEndpointAddress)

                    self.assertTrue(ep_found, 'No endpoint could be found')


    #def test_enumeration(self):
    #    print '\nIn TestDevice.test_enumeration'
    #    self.assertNotEqual(self.backend, None, 'Backend not defined')
    #    for d in self.backend.enumerate_devices():
    #        print 'Get backend device with vid=%s, pid=%s' % (d.idVendor, d.idProduct)
    #        desc = self.backend.get_device_descriptor(d)
    #        if desc.idVendor == devinfo.ID_VENDOR and desc.idProduct == devinfo.ID_PRODUCT:
    #            self.device = d
    #            print 'Found a device'
    #            return
    #    self.fail('PyUSB test device not found')


    def test_for_replayer(self):
        if self.replayer.debug:
            print '\nIn TestDevice.test_for_device'
        self.assertNotEqual(self.replayer, None, 'Replayer not instantiated')
        # Make sure the device has been enumerated
        #self.assertEqual(devdesc.idVendor, devinfo.ID_VENDOR, 'idVendor incorrect')
        #self.assertEqual(devdesc.idProduct, devinfo.ID_PRODUCT, 'idProduct incorrect')
          

    def test_print_descriptors(self):
        self.replayer.print_all()


    def test_device_descriptor(self):
        if self.replayer.debug:
            print '\nIn TestDevice.test_device_descriptor'
        devdesc = self.replayer.device
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
        if self.replayer.debug:
            print 'Actual device descriptor fields are ...'
            self.replayer.print_device_descriptor_fields()


    def test_cfg_descriptor(self):
        """
        Utility function to print out all configuration descriptor fields.
        """
        if self.replayer.debug:
            print '\nIn TestDevice.print_cfg_descriptor_fields'
        cfgdesc = self.replayer.cfg
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
        if self.replayer.debug:
            print 'Actual configuration descriptor fields are ...'
            self.replayer.print_cfg_descriptor_fields()


    def test_iface_descriptor(self):
        """
        Utility function to print out all interface descriptor fields.
        """
        if self.replayer.debug:
            print '\nIn TestDevice.print_iface_descriptor_fields'
        ifacedesc = self.replayer.iface

        # bLength = Size of interface descriptor in bytes (number).
        self.assertEqual(ifacedesc.bLength, 9, 'Incorrect interface descriptor bLength')

        # bDescriptorType = Interface descriptor (0x04) in bytes (constant).
        self.assertEqual(ifacedesc.bDescriptorType, 0x04, 'Incorrect interface descriptor bDescriptorType')

        # bInterfaceNumber = Number of interface (number).
        #print 'bInterfaceNumber = ', iface.bInterfaceNumber

        # bAlternateSetting = Value used to select alternate setting (number).
        #print 'bAlternateSetting = ', iface.bAlternateSetting

        # bNumEndpoints = Number of endpoints used for this interface (number).
        # This excludes endpoint 0.
        #print 'bNumEndpoints = ', iface.bNumEndpoints
        self.assertNotEqual(ifacedesc.bNumEndpoints, 0, 'Incorrect interface descriptor bNumEndpoints')

        # bInterfaceClass = Class code assigned by USB org (class).
        # Class could be HID, communicatins, mass storage, etc.
        #print 'bInterfaceClass = ', iface.bInterfaceClass

        # bInterfaceSubClass = SubClass code assigned by USB org (subClass).
        #print 'bInterfaceSubClass = ', iface.bInterfaceSubClass

        # bInterfaceProtocol = Protocol code assigned by USB org (protocol).
        #print 'bInterfaceProtocol = ', iface.bInterfaceProtocol

        # iInterface = Index of string descriptor describing this interface (index).
        #print 'iInterface = ', ifacedesc.iInterface

        if self.replayer.debug:
            print 'Actual interface descriptor fields are ...'
            self.replayer.print_iface_descriptor_fields()


    def test_ep_descriptor(self):
        """
        Utility function to print out all endpoint descriptor fields.
        """
        #ep = self.replayer.eps[0]
        #print 'Endpoints are: ', ep.bEndpointAddress
        #print 'Actual endpoint descriptor fields are ...'
        #self.replayer.print_ep_descriptor_fields(ep)
        ep = self.replayer.poll_eps[0]
        if self.replayer.debug:
            print '\nPoll endpoints are: ', ep.bEndpointAddress
            print 'Actual poll endpoint descriptor fields are ...'
            self.replayer.print_ep_descriptor_fields(ep)

        # bLength = Size of endpoint descriptor in bytes (number).
        self.assertEqual(ep.bLength, 7, 'Incorrect endpoint descriptor bLength')

        # bDescriptorType = Endpoint descriptor (0x05) in bytes (constant).
        self.assertEqual(ep.bDescriptorType, 0x5, 'Incorrect endpoint descriptor bDescriptorType')

        # bEndpointAddress = Endpoint descriptor (0x05) in bytes (constant).
        # Bits 0-3=endpoint number, Bits 4-6=0, Bit 7=0(out) or 1(in).
        #print 'bEndpointAddress = 0x%x' % ep.bEndpointAddress

        # bmAttributes = Bits 0-1=Transfer type, other bits refer to
        # synchronization type, usage type (iso mode) (bitmap).
        # Transfer types: 00=Control, 01=Isochronous, 10=Bulk, 11=Interrupt.
        #print 'bmAttributes = ', ep.bmAttributes

        # wMaxPacketSize = Max packet size this endpoint is capable of
        # sending or receiving (number).
        # This is the maximum payload size for this endpoint.
        #print 'wMaxPacketSize = ', ep.wMaxPacketSize
        self.assertNotEqual(ep.wMaxPacketSize, 0, 'Incorrect endpoint descriptor wMaxPacketSize')

        # bInterval = Interval for polling endpoint data transfers.
        # Value in frame counts (?).  Ignored for bulk and control endpoints.
        # Isochronous must equal 1.  This field for interrupt endpoints may
        # range from 1 to 255 (number).
        # bInterval is used to specify the polling interval of certain transfers.
        # The units are expressed in frames.  This equates to 1ms for low/full
        # speed devices, and 125us for high speed devices.
        self.assertNotEqual(ep.bInterval, 0, 'Incorrect endpoint descriptor bInterval')
        
                                                                             

        ##if __name__ == '__main__':
        ##    loader = unittest.defaultTestLoader
        ##    suite = unittest.TestSuite()
        ##    suite.addTest(loader.loadTestsFromTestCase(TestPackedFields))
        ##    suite.addTest(loader.loadTestsFromTestCase(TestPacket))
        ##    suite.addTest(loader.loadTestsFromTestCase(TestPacketData))
        ##    suite.addTest(loader.loadTestsFromTestCase(TestSetupField))
        ##    suite.addTest(loader.loadTestsFromTestCase(TestSetupFieldPropagation))
        ##    unittest.TextTestRunner(verbosity=2).run(suite)



if __name__ == '__main__':
    # Use the keyboard as the device upon which to perform unit tests
    loader = unittest.defaultTestLoader
    #suite = get_suite()
    suite = unittest.TestSuite()
    # Test that device is connected
    suite.addTest(loader.loadTestsFromTestCase(TestDevice))
    
    #suite.addTest(loader.loadTestsFromTestCase(TestDeviceDescriptor)
    # Test that device has correct endpoint address
    #    suite.addTest(loader.loadTestsFromTestCase(TestForEndpoint))
    # Test that kernel driver can be detached and re-attached
    #    suite.addTest(loader.loadTestsFromTestCase(TestKernelDriver))
    # Test that host can send a setup packet
    #    suite.addTest(loader.loadTestsFromTestCase(TestSetupField))
    # Do a loopback test here: write and readback what you wrote
    # Test that host can perform a write to device
    #    suite.addTest(loader.loadTestsFromTestCase(TestSetupFieldPropagation))
    # Test that host can perform a read from device
    unittest.TextTestRunner(verbosity=2).run(suite)

