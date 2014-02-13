#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    Run it:

    python sensor.py

    After a little dialogue it will watch the luminosity readings
    from the serial port and decide if we have a black cat or a resident cat

"""
from __future__ import print_function
from os import system, listdir
from os.path import isfile, join
from random import shuffle
import getpass
import serial
# from random import shuffle
from time import strftime, mktime, sleep
from datetime import datetime

from confirm import confirm  # ux baby
from send_sms import send_sms
from calibrate import calibrate
from update_status import update_status
from secrets import secrets

from settings import serial_port,log_level

# the arduino needs longer to start than this does
print("sleeping for 30 seconds")
sleep(30)

resident_cat_variance_ratio = 1.5
recalibrate_freq = 15  # minutes
scary_msg = "Pssssst see see see see GET OUT OF HERE CAT!! Pssssst Pssssst Pssssst"

gmail_addy = secrets['gmail_addy']  # used for sending the text to sms_recipients
sms_recipients = secrets['sms_recipients']
# gmail_pw = getpass.getpass("if you want a text of each reading, enter your gmail password (or enter to skip): ")
gmail_pw = secrets['gmail_pw']

# send an initial sms
if gmail_pw:
    print("sending test sms...")
    send_sms('black cat sms alerts have begun', gmail_addy, gmail_pw, sms_recipients)
    last_sms = mktime(datetime.now().timetuple())
    print("ok that worked!")


# if you want sms control...
sms_msg = "if you want sms control, run this in another shell: \n python fetch_status.py"
print(sms_msg)

# connect to the Arduino's serial port
try:
    ser = serial.Serial(serial_port, 9600)
except serial.serialutil.SerialException:
    if confirm("Please plug in the Arduino, say Y when that's done: "):
        ser = serial.Serial(serial_port, 9600)


# upload your script to the arduino
"""
if confirm("Now upload your sketch to the arduino, say Y ®: "):
    print('ok!')
"""

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

consecutive_triggers = 0  # count of number of consecutive trigger alarms
consecutive_trigger_break = 0.
while True:

    # connect to our log file
    f = open("/home/pi/blackcat/logs/black_cat_sightings.log",'a')

    ser.flushInput()  # attempt to keep commands from stacking up, always get latest reading
    reading = ser.readline()

    # debugging
    # print(str(base) + ' ' + str(variance) + ' reading: ' + str(reading))

    t = mktime(datetime.now().timetuple())
    try:
        status = open('status.txt').readlines()[0].strip()
    except IndexError:
        status = 'ON'

    if status != 'ON':

        if status[0:2] == 'CA':
            # this means recalibrate now:
            base, variance, time_last_calib = calibrate(ser, f)
            update_status('ON')

        elif status == 'OFF':
            print(strftime("%X").strip() + " going off for 5 minutes")
            turned_off = True
            sleep(5*60)  # sleep n minutes then continue
            continue

    if turned_off == True:
        print("ok back on")
        turned_off = False


    if first_reading:
        first_reading = False
        time_str = datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S').strip()
        print("hello, first reading: " + reading + ' - ' + time_str)
        print("hello, first reading: " + reading + ' - ' + time_str, file=f)
        f.flush()
        sleep(1)
        continue

    # tiny movement logging
    if log_level == 'ALL':
        if abs(int(reading) - int(base)) > 25:
            # if it moves just a little log to json api
            msg = "time: %s reading: %s, base: %s, variance: %s, threshhold: %s" % (str(datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S').strip()), str(reading.strip()), str(base), str(variance), str(base-variance))
            print(msg, file=f)
            f.flush()

    try:

        if int(reading) < (base-variance): # black cats always score lower than base
            # we haz a black cat!

            consecutive_triggers += 1

            # there is a problem that around noon-ish it would continuously trigger until
            # remotely recalibrated
            if consecutive_triggers > 5:
                # alarm has gone off 5 times in a row
                timenow = mktime(datetime.now().timetuple())
                if not consecutive_trigger_break:
                    # so far we have not stopped alarms with the consecutive_trigger_break flag
                    # let's recalibrate and do that now
                    base, variance, time_last_calib = calibrate(ser, f)
                    consecutive_trigger_break = timenow
                    print(strftime("%X").strip() + " setting consecutive_trigger_break", file=f)
                    continue
                else:
                    # if timenow > consecutive_trigger_break + 60 * 15:
                    if timenow > consecutive_trigger_break + 15:
                        # 15 minutes have gone by since consecutive_trigger_break was set, let's turn it off
                        consecutive_trigger_break = 0
                        print(strftime("%X").strip() + " turning off consecutive_trigger_break", file=f)
                        base, variance, time_last_calib = calibrate(ser, f)  # just in case
                    else:
                        sleep(10)
                        continue  # continue the outer while


            # play a mac creepy mac voice
            """
            # pick a creepy voice at random and scare a cat with it
            shuffle(voices)
            voice, phrase = [v.strip() for v in voices[0].split('en_US    #')]
            msg = "say -r 340 -v %s %s " % (voice, scary_msg)
            system(msg)
            print(msg, file=f)
	       f.flush()
            """


            # log
            msg = "%s Black cat detected! - reading: %s base: %s signma: %s - %s" % (strftime("%X").strip(), str(reading).strip(), str(base).strip(), str(variance).strip(), strftime("%a, %d %b %Y").strip())
            print(msg, file=f)
            f.flush()


            # play a wav file
            shuffle(wav_files)
            system('aplay audio/' + wav_files[0])


            # send sms
            if gmail_pw and (t-last_sms > 30):  # minimum seconds between sms alerts please!
                last_sms = t
                send_sms(u'hello black cat %s' % str(strftime("%X").strip()), gmail_addy, gmail_pw, sms_recipients)

        else:
            consecutive_triggers = 0
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
