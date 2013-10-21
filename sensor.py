#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
from os import system
import random
import getpass
import serial
from time import strftime, mktime, sleep
from datetime import datetime
from fabric.contrib.console import confirm  # ux baby
from send_sms import send_sms
from calibrate import calibrate
from secrets import secrets

resident_cat_variance_ratio = 1.5
recalibrate_freq = 10  # minutes
scary_msg = "Pssssst see see see see GET OUT OF HERE CAT!! Pssssst Pssssst Pssssst"

log_file = "black_cat_sightings.log"

gmail_addy = secrets['gmail_addy']  # used for sending the text to sms_recipients
sms_recipients = secrets['sms_recipients']
gmail_pw = getpass.getpass("if you want a text of each reading, enter your gmail password: ")

# send an initial sms
if gmail_pw:
    print("sending test sms...")
    send_sms('black cat sms alerts have begun', gmail_addy, gmail_pw, sms_recipients)
    last_sms = mktime(datetime.now().timetuple())
    print("ok that worked!")

# connect to the Arduino's serial port
try:
    ser = serial.Serial('/dev/tty.usbmodemfd121', 19200)
except serial.serialutil.SerialException:
    if confirm("Please plug in the Arduino, say Y when that's done: "):
        ser = serial.Serial('/dev/tty.usbmodemfd121', 19200)

# upload your script to the arduino
if confirm("Now upload your sketch to the arduino, say Y ®: "):
    print('ok!')

# connect to our log file and fetch the creepy voices
f = open(log_file,'w')
voices = open('creepy_voices.txt').readlines()

# doing initial calibration..
print("doing initial calibration..")
base, variance, time_last_calib = calibrate(ser, f)

# read the serial port for sensor readings:
first_reading = True
while True:
    reading = ser.readline()

    # debugging
    # print(str(base) + ' ' + str(variance) + ' reading: ' + str(reading))

    if first_reading:
        first_reading = False
        t = mktime(datetime.now().timetuple())
        time_str = datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S').strip()
        print("hello, first reading: - " + reading + ' - ' + time_str)
        print("hello, first reading: " + reading + ' - ' + time_str, file=f)
        f.flush()
        sleep(1)
        continue;

    try:

        if int(reading) < (base-variance): # black cats always score lower than base
            # we haz a black cat!

            # this stuff gets repeated because I didn't want to hold up the base/variance check.. speed!
            t = mktime(datetime.now().timetuple())
            time_str = datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S').strip()

            # pick a creepy voice at random and scare a cat with it
            random.shuffle(voices)
            voice, phrase = [v.strip() for v in voices[0].split('en_US    #')]
            msg = "say -r 340 -v %s %s " % (voice, scary_msg)
            system(msg)
            print(msg, file=f)

            # log
            msg = "%s Black cat detected! - %s - %s" % (strftime("%X").strip(), str(reading).strip(), strftime("%a, %d %b %Y").strip())
            print(msg, file=f)
            f.flush()

            # send sms - this script dies here if you change your gmail password, janky way to kill the script remotely
            if gmail_pw and (t-last_sms > 60*recalibrate_freq):  # minimum 10 minutes between sms alerts please!
                last_sms = t
                send_sms(u'hello black cat %s' % str(strftime("%X").strip()), gmail_addy, gmail_pw, sms_recipients)

        else:
            # no cats, do we need to calibrate?
            if t-time_last_calib > 60*recalibrate_freq:
                base, variance, time_last_calib = calibrate(ser, f)

            if int(reading) > (resident_cat_variance_ratio*base+variance):
                print("resident cat? - " + str(reading) + ' - ' + time_str, file=f)

    except ValueError:
        print(reading, file=f)



