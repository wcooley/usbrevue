#!/usr/bin/env python

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


class TestDevice(unittest.TestCase, TestUtil):

    #def __init__(self, rep):
    #    global replayer
    #    replayer = rep
    #    #replayer.reset_device()

    def setup(self):
        global replayer
        print 'Resetting device with vid=0x%x, pid=0x%x' % (replayer.device.idVendor, replayer.device.idProduct)
        replayer.reset_device()


    def print_device(self):
        print '\nTesting device with vid=0x%x, pid=0x%x' % (replayer.device.idVendor, replayer.device.idProduct)


    def test_device(self):
        global replayer
        #if replayer.debug:
        if replayer.debug:
            print 'In TestDevice.test_device'
        # find our device
        dev = usb.core.find(idVendor=replayer.device.idVendor, idProduct=replayer.device.idProduct)
        # Was device found?
        self.assertNotEqual(dev, None, 'No device available with vid=%s, pid=%s' % (replayer.device.idVendor, replayer.device.idProduct))


    def test_kernel_driver(self):
        global replayer
        #if replayer.debug:
        if replayer.debug:
            print 'In TestDevice.test_kernel_driver'
        res = replayer.device.is_kernel_driver_active(replayer.logical_iface)
        if res == False:
            res = replayer.device.attach_kernel_driver(replayer.logical_iface)
        if replayer.debug:
            print '\nResult of is kernel driver active is', res
        if res is not None:
            self.assertEqual(res, True, 'Kernel driver for vendorId 0x%x, productId 0x%x is not active' % (replayer.device.idVendor, replayer.device.idProduct))
        if replayer.debug:
            print 'Detaching kernal driver'
        res = replayer.device.detach_kernel_driver(replayer.logical_iface)
        if replayer.debug:
            print 'Result of detach is', res
   
    def test_eps(self):
        global replayer
        if replayer.debug:
            print 'In TestDevice.test_eps'
        dev = usb.core.find(idVendor=replayer.device.idVendor, idProduct=replayer.device.idProduct)
        for cfg in dev:
            self.assertEqual(cfg.bConfigurationValue, replayer.cfg.bConfigurationValue)
            for iface in cfg:
                self.assertEqual(iface.bInterfaceNumber, replayer.iface.bInterfaceNumber)
                ep_found = False
                for ep in iface:
                    for i in range(len(replayer.eps)):
                        if replayer.debug:
                            print '\n%d: ep address is 0x%x\n' % (i, ep.bEndpointAddress)
                            print '%d: replayer eps = %s' % (i, replayer.eps)
                            print '%d: ep.bEndpointAddress = 0x%x' % (i, ep.bEndpointAddress)
                            print 'replayer.eps =', replayer.eps 
                        if ep.bEndpointAddress in replayer.eps:
                            if replayer.debug:
                                print 'Got an ep'
                            ep_found = True
                            if replayer.debug:
                                print 'Endpoint %d found' % ep.epnum

                    for j in range(len(replayer.poll_eps)):
                        if replayer.debug:
                            print '%d: replayer.poll_eps = %s' % (j, replayer.poll_eps)
                            print '%d: replayer.poll_eps[j].bEndpointAddress = %s' % (j, replayer.poll_eps[j].bEndpointAddress)
                        if ep.bEndpointAddress == replayer.poll_eps[j].bEndpointAddress:
                            if replayer.debug:
                                print 'Got a poll ep'
                            ep_found = True
                            if replayer.debug:
                                print 'Endpoint at address 0x%x found' % (ep.bEndpointAddress)

                    self.assertTrue(ep_found, 'No endpoint could be found')



    def test_replayer(self):
        global replayer
        if replayer.debug:
            print '\nIn TestDevice.test_replayer'
        self.assertNotEqual(replayer, None, 'Replayer not instantiated')
          

    def test_print_descriptors(self):
        global replayer
        replayer.print_all()


    def test_device_descriptor(self):
        global replayer
        if replayer.debug:
            print '\nIn TestDevice.test_device_descriptor'
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
            print 'Actual device descriptor fields are ...'
            replayer.print_device_descriptor_fields()


    def test_cfg_descriptor(self):
        """
        Utility function to print out all configuration descriptor fields.
        """
        global replayer
        self.print_device()
        if replayer.debug:
            print '\nIn TestDevice.print_cfg_descriptor_fields'
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
            print 'Actual configuration descriptor fields are ...'
            replayer.print_cfg_descriptor_fields()


    def test_iface_descriptor(self):
        """
        Utility function to print out all interface descriptor fields.
        """
        global replayer
        if replayer.debug:
            print '\nIn TestDevice.print_iface_descriptor_fields'
        ifacedesc = replayer.iface

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

        if replayer.debug:
            print 'Actual interface descriptor fields are ...'
            replayer.print_iface_descriptor_fields()


    def test_ep_descriptor(self):
        """
        Utility function to print out all endpoint descriptor fields.
        """
        global replayer
        ep = replayer.poll_eps[0]
        if replayer.debug:
            print '\nPoll endpoints are: ', ep.bEndpointAddress
            print 'Actual poll endpoint descriptor fields are ...'
            replayer.print_ep_descriptor_fields(ep)

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

        
def get_usb_devices():
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
    print 'Devices being tested are ...'
    for dev in devices:
       print 'vid = 0x%x,  pid = 0x%x' % (dev.idVendor, dev.idProduct)  
    print '\n'


if __name__ == '__main__':
    global replayer
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    devices = []
    devices = get_usb_devices()
    print_devices(devices)
    for dev in devices:
        replayer = usbreplay.Replayer(vid=dev.idVendor, pid=dev.idProduct, debug=False)
        suite.addTest(loader.loadTestsFromTestCase(TestDevice))
        unittest.TextTestRunner(verbosity=2).run(suite)
        suite = unittest.TestSuite()


