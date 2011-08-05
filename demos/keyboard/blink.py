#!/usr/bin/env python
import usb.core
import usb.util
import sys
import time
 
# Set the interface number
IFACE = 0
VID = 0x413c
PID = 0x2003

# Find the keyboard device
device = usb.core.find(idVendor=VID, idProduct=PID)
 
# Ensure keyboard was found
if device is None:
    raise ValueError('Device not found')
 
# Detach kernel driver so my ctrl_transfer can be sent
if device.is_kernel_driver_active(IFACE):
    device.detach_kernel_driver(IFACE)

# Set the active configuration
device.set_configuration()
 
# Turn numlock on
# ctrl_transfer( bmRequestType, bmRequest, wValue, wIndex, nBytes) 
# Why does usbview have 0x21, 0x9 0x0002, 0x0000, 0x0100 and 01 for data?
result = device.ctrl_transfer(0x21, 0x9, 0x200, 0x100, [01])
time.sleep(2)
print 'Returned %d bytes' % result

# Turn numlock off
result = device.ctrl_transfer(0x21, 0x9, 0x200, 0x100, [00])
time.sleep(1)
print 'Returned %d bytes' % result

# Re-attach kernel driver 
if not device.is_kernel_driver_active(IFACE):
    device.attach_kernel_driver(IFACE)

