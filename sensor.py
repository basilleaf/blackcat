#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    Run it:

    python sensor.py

    After a little dialogue it will watch the luminosity readings
    from the serial port and decide if we have a black cat or a resident cat

"""
from __future__ import print_function
import sys
from os import system, listdir
from os.path import isfile, join

import serial
from random import choice
from time import strftime, mktime, sleep
from datetime import datetime

from confirm import confirm  # ux baby
from send_email import send_sms, send_email
from update_status import update_status
from secrets import secrets

from settings import serial_port
import logging
import threading


LOG_LEVEL = logging.DEBUG

resident_cat_variance_ratio = 1.5
recalibrate_freq = 15  # minutes

# set up email things
gmail_addy = secrets['gmail_addy']  # used for sending the text to sms_recipients
sms_recipients = secrets['sms_recipients']
gmail_pw = secrets['gmail_pw']  # gmail_pw = getpass.getpass("if you want a text of each reading, enter your gmail password (or enter to skip): ")
consecutive_triggers = 0  # count of number of consecutive trigger alarms

try:
    ser = serial.Serial(serial_port, 9600)
except serial.serialutil.SerialException:
    if confirm("Please plug in the Arduino, say Y when that's done: "):
        ser = serial.Serial(serial_port, 9600)

# some vars to keep track of things
status = 'ON'
turned_off = False
last_consecutive_trigger_break = 0.


def calibrate():
    """ takes 10 readings and averages them to get a base reading
        return base, variance, time_last_calib """

    print("recalibrating..")

    # take 10 readings
    latest_readings = []
    error_count = 0
    while len(latest_readings) < 11:
        reading = get_serial_reading()

        # can this reading be cast as int?
        try:
            int(reading)
        except ValueError:
            # how many time will we let this trip?
            error_count += 1
            if error_count > 5:
                logging.error("could not calibrate, errors in reading serial line as int")
                sys.exit()

        if int(reading) > 3000:
            logging.info('got large calib reading ' + str(reading.strip()) + ' throwing it away ')
            continue  # there is an initial spike that is really 2 numbers coming accross as 1

        latest_readings.append(int(reading))

    logging.info(latest_readings)
    # and recalculate base and variance
    base = int(sum(latest_readings)/len(latest_readings))

    # the sensor becomes less sensitive in brighter ambient lighting
    if base > 100:
        variance = base/2
    else:
       variance  = base/4

    time_last_calib = mktime(datetime.now().timetuple())

    logging.info("recalibrated " + datetime.fromtimestamp(mktime(datetime.now().timetuple())).strftime('%Y-%m-%d %H:%M:%S').strip())
    logging.info('base: ' + str(base) + ' ' + 'variance: ' + str(variance))

    return (base, variance, time_last_calib)


def play_random_local_wave_file():
    """ plays random wave file in audio dir"""
    wav_files = [f for f in listdir('audio') if isfile(join('audio',f)) ]
    # because random works better on a larger list of items:
    for i in range(0,3):
        wav_files = wav_files + wav_files
    system('aplay audio/' + choice(wav_files))


def get_serial_reading():
    global ser
    """ gets serial reading and flushes input first"""
    ser.flushInput()  # attempt to keep commands from stacking up, always get latest reading
    return (ser.readline())

def status_break():
    """ returns true if the status file says hold or recalibrate and thus this iteration should be skipped """
    global status, base, variance, time_last_calib, turned_off

    try:
        status = open('/home/pi/blackcat/status.txt').readlines()[0].strip()
    except IndexError:
        status = 'ON'

    if status != 'ON':

        if status[0:2] == 'CA':
            # this means recalibrate now:
            base, variance, time_last_calib = calibrate()
            update_status('ON')  # change the status back to on
            return True

        elif status == 'OFF':
            logging.info("going off for 5 minutes")
            turned_off = True
            sleep(5*60)  # sleep n minutes then continue
            return True

    if turned_off == True:
        # status is on, but this was turned off before, so post a log msga
        logging.info("ok back on")
        turned_off = False
        return False  # we are back on



def consecutive_trigger_break():
    """
        returns true if the loop should be skipped this time around
        many consecutive triggers happen around noon on a sunny day, there is no cat
        this just makes it so only 5 triggers can ever be called
    """
    global base, variance, time_last_calib, last_consecutive_trigger_break, consecutive_triggers

    if consecutive_triggers < 5:
        return False

    # alarm has gone off 5 times in a row
    timenow = mktime(datetime.now().timetuple())

    if not last_consecutive_trigger_break:
        # so far we have not stopped alarms with the consecutive_trigger_break flag
        # let's recalibrate and do that now
        base, variance, time_last_calib = calibrate()
        last_consecutive_trigger_break = timenow
        logging.info(" setting consecutive_trigger_break")
        return True
    else:
        # if timenow > consecutive_trigger_break + 15:  # debug
        if timenow > last_consecutive_trigger_break + 60 * 15:
            # 15 minutes have gone by since consecutive_trigger_break was set, let's turn it off
            last_consecutive_trigger_break = 0
            logging.info("turning off consecutive_trigger_break")
            base, variance, time_last_calib = calibrate()  # just in case
            return False
        else:
            sleep(10)
            return True


class TriggerWemo(threading.Thread):
    """ turns on the Wemo switch and turns it off 5 minutes later """

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        logging.info("turning on Wemo light switch")
        send_email('#ON', gmail_addy, gmail_pw, 'trigger@ifttt.com')
        sleep(60*3)
        logging.info("turning off Wemo light switch")
        send_email('#OFF', gmail_addy, gmail_pw, 'trigger@ifttt.com')
        sleep(15)
        send_email('#OFF', gmail_addy, gmail_pw, 'trigger@ifttt.com')  # just in case


def main():
    global consecutive_triggers

    # some vars to keep track of things
    first_reading = True

    # send an initial test sms
    # set up logging
    logging.basicConfig(filename='/home/pi/blackcat/logs/black_cat_sightings.log',level=LOG_LEVEL, format='%(asctime)s %(message)s')

    if gmail_pw:
        logging.info("sending test sms...")
        send_sms('black cat sms alerts have begun', gmail_addy, gmail_pw, sms_recipients)
        last_sms = mktime(datetime.now().timetuple())
        logging.info("ok test sms worked!")

    # if you want sms control...
    sms_msg = "if you want sms control, run this in another shell: \n python fetch_status.py"
    print(sms_msg)

    # connect to the Arduino's serial port
    # but first take a break: the arduino needs longer on startup than this does script does apparently
    logging.info("sleeping for 15 seconds")
    sleep(15)

    # doing initial calibration..
    logging.info("doing initial calibration..")
    base, variance, time_last_calib = calibrate()

    while True:


        sleep(.5)  # check the serial reading every x time
        timenow = mktime(datetime.now().timetuple())

        # always check the status.txt file before doing anything
        if status_break():
            logging.debug('taking status break')
            continue

        reading = get_serial_reading()

        if first_reading:
            first_reading = False
            logging.info("hello first reading: " + reading)
            continue

        # tiny movement logging (for debugging)
        if abs(int(reading) - int(base)) > 25:
            msg = "tiny movement reading: %s, base: %s, variance: %s, threshhold: %s" % (str(reading.strip()), str(base), str(variance), str(base-variance))
            logging.debug(msg)

        try:

            if int(reading) < (base-variance): # black cats always score lower than base
                # we haz a black cat!

                consecutive_triggers += 1

                if consecutive_trigger_break():
                    logging.info('hit consecutive trigger break')
                    continue

                # log
                msg = "Black cat detected! - reading: %s base: %s signma: %s - %s" % (str(reading).strip(), str(base).strip(), str(variance).strip(), strftime("%a, %d %b %Y").strip())
                logging.info(msg)

                # trigger wemo light switch
                wemo = TriggerWemo()
                wemo.start()

                # play a wav file
                play_random_local_wave_file()

                # send sms
                if gmail_pw and (timenow-last_sms > 30):  # minimum seconds between sms alerts please!
                    last_sms = timenow
                    send_sms(u'hello black cat %s' % str(strftime("%X").strip()), gmail_addy, gmail_pw, sms_recipients)

                # play a mac creepy mac OSX voice - we have wav files so this is removed..
                """
                # pick a creepy voice at random and scare a cat with it
                scary_msg = "Pssssst see see see see GET OUT OF HERE CAT!! Pssssst Pssssst Pssssst"
                shuffle(voices)
                voice, phrase = [v.strip() for v in voices[0].split('en_US    #')]
                msg = "say -r 340 -v %s %s " % (voice, scary_msg)
                system(msg)
                logging.info(msg)
                """

            else:

                consecutive_triggers = 0

                # no cats, do we need to calibrate?
                if timenow-time_last_calib > 60*recalibrate_freq:
                    base, variance, time_last_calib = calibrate()


        except ValueError:
            logging.info('ValueError: ' + str(reading))


if __name__ == "__main__":

    main()
