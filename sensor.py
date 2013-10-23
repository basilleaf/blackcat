#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
from os import system
import random
import getpass
import serial
import urllib2
from time import strftime, mktime, sleep
from datetime import datetime
from fabric.contrib.console import confirm  # ux baby
from send_sms import send_sms
from calibrate import calibrate
from update_status import update_status
from secrets import secrets

resident_cat_variance_ratio = 1.5
recalibrate_freq = 20  # minutes
scary_msg = "Pssssst see see see see GET OUT OF HERE CAT!! Pssssst Pssssst Pssssst"

log_file = "black_cat_sightings.log"

gmail_addy = secrets['gmail_addy']  # used for sending the text to sms_recipients
sms_recipients = secrets['sms_recipients']
gmail_pw = getpass.getpass("if you want a text of each reading, enter your gmail password (or enter to skip): ")

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
status = 'ON'
last_checked_status = mktime(datetime.now().timetuple())
while True:
    reading = ser.readline()

    # debugging
    # print(str(base) + ' ' + str(variance) + ' reading: ' + str(reading))

    t = mktime(datetime.now().timetuple())

    # check the remote server for status commands
    if t-last_checked_status > 60:  # check status every minute
        last_checked_status = mktime(datetime.now().timetuple())
        status =  urllib2.urlopen('https://s3.amazonaws.com/blackcatsensor/status').readlines()[0]
        if status != 'ON':
            if status[0:2] == 'CA':
                # this means recalibrate now:
                base, variance, time_last_calib = calibrate(ser, f)
                update_status('ON')
            elif status == 'OFF':
                print(strftime("%X").strip() + " going off for 15 minutes")
                sleep(15*60)  # sleep 15 minutes then continue
                continue


    if first_reading:
        first_reading = False
        time_str = datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S').strip()
        print("hello, first reading: - " + reading + ' - ' + time_str)
        print("hello, first reading: " + reading + ' - ' + time_str, file=f)
        f.flush()
        sleep(1)
        continue;

    try:

        if int(reading) < (base-variance): # black cats always score lower than base
            # we haz a black cat!

            # pick a creepy voice at random and scare a cat with it
            random.shuffle(voices)

            # play a mac creepy mac voice
            """
            voice, phrase = [v.strip() for v in voices[0].split('en_US    #')]
            msg = "say -r 340 -v %s %s " % (voice, scary_msg)
            system(msg)
            print(msg, file=f)
            """

            # play a wav file
            system('afplay ~/GET_OUT_OF_HERE_CAT.wav')

            # log
            msg = "%s Black cat detected! - %s - %s" % (strftime("%X").strip(), str(reading).strip(), strftime("%a, %d %b %Y").strip())
            print(msg, file=f)
            f.flush()

            # send sms
            if gmail_pw and (t-last_sms > 30):  # minimum seconds between sms alerts please!
                last_sms = t
                send_sms(u'hello black cat %s' % str(strftime("%X").strip()), gmail_addy, gmail_pw, sms_recipients)

        else:
            # no cats, do we need to calibrate?
            if t-time_last_calib > 60*recalibrate_freq:
                base, variance, time_last_calib = calibrate(ser, f)

            """
            this is fail
            if int(reading) > (resident_cat_variance_ratio*base+variance):
                time_str = datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S').strip()
                print("resident cat? - " + str(reading) + ' - ' + time_str, file=f)
            """

    except ValueError:
        print(reading, file=f)
