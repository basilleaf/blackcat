#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
from os import system, listdir
from os.path import isfile, join
from random import shuffle
import getpass
import serial
from random import shuffle
from time import strftime, mktime, sleep
from datetime import datetime
from confirm import confirm  # ux baby
from send_sms import send_sms
from calibrate import calibrate
from update_status import update_status
from secrets import secrets

resident_cat_variance_ratio = 1.5
recalibrate_freq = 20  # minutes
scary_msg = "Pssssst see see see see GET OUT OF HERE CAT!! Pssssst Pssssst Pssssst"
serial_port = '/dev/tty.usbmodemfd121'

gmail_addy = secrets['gmail_addy']  # used for sending the text to sms_recipients
sms_recipients = secrets['sms_recipients']
gmail_pw = getpass.getpass("if you want a text of each reading, enter your gmail password (or enter to skip): ")

# send an initial sms
if gmail_pw:
    print("sending test sms...")
    send_sms('black cat sms alerts have begun', gmail_addy, gmail_pw, sms_recipients)
    last_sms = mktime(datetime.now().timetuple())
    print("ok that worked!")


# if you want sms control...
sms_msg = "if you want sms control, run this in another shell: \n python fetch_status.py"
print(sms_msg)
sleep(2)

# connect to the Arduino's serial port
try:
    ser = serial.Serial(serial_port, 19200)
except serial.serialutil.SerialException:
    if confirm("Please plug in the Arduino, say Y when that's done: "):
        ser = serial.Serial(serial_port, 19200)

# upload your script to the arduino
if confirm("Now upload your sketch to the arduino, say Y ®: "):
    print('ok!')

"""
fetch the creepy voices
voices = open('creepy_voices.txt').readlines()
"""

# get collection of wav files
wav_files = [ f for f in listdir('audio') if isfile(join('audio',f)) ]
# because random works better on a larger list of items:
for i in range(0,3):
    wav_files = wav_files + wav_files

# doing initial calibration..
print("doing initial calibration..")
base, variance, time_last_calib = calibrate(ser, f)

# read the serial port for sensor readings:
first_reading = True
status = 'ON'
last_checked_status = mktime(datetime.now().timetuple())
turned_off = False

while True:

    # connect to our log file
    f = open("black_cat_sightings.log",'w')

    reading = ser.readline()

    # debugging
    # print(str(base) + ' ' + str(variance) + ' reading: ' + str(reading))

    t = mktime(datetime.now().timetuple())
    try:
        status = open('status').readlines()[0].strip()
    except IndexError:
        status = 'ON'

    if status != 'ON':

        if status[0:2] == 'CA':
            # this means recalibrate now:
            base, variance, time_last_calib = calibrate(ser, f)
            update_status('ON')

        elif status == 'OFF':
            print(strftime("%X").strip() + " going off for 15 minutes")
            turned_off = True
            sleep(15*60)  # sleep 15 minutes then continue
            continue

    if turned_off == True:
        print("ok back on")
        turned_off == False


    if first_reading:
        first_reading = False
        time_str = datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S').strip()
        print("hello, first reading: " + reading + ' - ' + time_str)
        print("hello, first reading: " + reading + ' - ' + time_str, file=f)
        f.flush()
        sleep(1)
        continue;

    try:

        if int(reading) < (base-variance): # black cats always score lower than base
            # we haz a black cat!


            # play a mac creepy mac voice
            """
            # pick a creepy voice at random and scare a cat with it
            shuffle(voices)
            voice, phrase = [v.strip() for v in voices[0].split('en_US    #')]
            msg = "say -r 340 -v %s %s " % (voice, scary_msg)
            system(msg)
            print(msg, file=f)
            """

            # play a wav file
            shuffle(wav_files)
            system('afplay audio/' + wav_files[0])

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

    f.close()
