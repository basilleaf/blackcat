#!/usr/bin/python
# -*- coding: utf-8 -*-

# serial port setting depends on platform
try:
    import  RPi.GPIO  # try to import the raspberry pi GPIO lib
    serial_port = '/dev/ttyACM0' # this is a raspberry pi!
except ImportError:
    # this must be an aging macbook air
    serial_port = '/dev/tty.usbmodemfd121'

log_level = 'ALL'  # anything but all turns off tiny movement logging