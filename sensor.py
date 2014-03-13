#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    Watches serial port for luminosity readings, decides if we have a black cat detection,
    if so does the following:
        - plays audio wav files
        - turn on Wemo switches (for lights and robotics)
        - sends sms

"""
from __future__ import print_function
import sys
from os import system, listdir
from os.path import isfile, join

import serial
from random import choice
from time import strftime, mktime, sleep, localtime, time
from datetime import datetime

from send_email import send_sms, send_email
from update_status import update_status
from secrets import secrets

import logging
import threading

# define some things
roomba_off_hours = [12, 13, 14]  # daylight hours high in false alarms, at night we unplug arduino
status = 'ON'
turned_off = False  # wtf?
last_consecutive_trigger_break = 0.
last_roomba_trigger = 0.
resident_cat_variance_ratio = 1.5
recalibrate_freq = 15  # minutes

# set up logging
LOG_LEVEL = logging.DEBUG
logging.basicConfig(filename='/home/pi/blackcat/logs/black_cat_sightings.log',level=LOG_LEVEL, format='%(asctime)s %(message)s')

# set up email
gmail_addy = secrets['gmail_addy']  # used for sending the text to sms_recipients
sms_recipients = secrets['sms_recipients']
gmail_pw = secrets['gmail_pw']  # gmail_pw = getpass.getpass("if you want a text of each reading, enter your gmail password (or enter to skip): ")
consecutive_triggers = 0  # count of number of consecutive trigger alarms

# connect to the Arduino's serial port (see settings.py)
logging.info("sleeping for 15 seconds to give Arduino time to boot up.")
sleep(15)

try:
    serial_port = '/dev/ttyACM1'
    ser = serial.Serial(serial_port, 9600)
except serial.SerialException:
    try:
        # somethings she moves it.
        serial_port = '/dev/ttyACM0'
        ser = serial.Serial(serial_port, 9600)
    except serial.SerialException:
        msg = 'could not connect to either serial port'
        logging.error(msg)
        print(msg)
        sys.exit()


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
            print('value error')
            # how many time will we let this trip?
            error_count += 1
            if error_count > 5:
                logging.error("could not calibrate, errors in reading serial line as int")
                sys.exit()

        if int(reading) > 3000:
            print('reading is huge!')
            logging.info('got large calib reading ' + str(reading.strip()) + ' throwing it away ')
            continue  # there is an initial spike that is really 2 numbers coming accross as 1

        latest_readings.append(int(reading))


    # and recalculate base and variance
    base = int(sum(latest_readings)/len(latest_readings))

    # the sensor becomes less sensitive in brighter ambient lighting
    if base > 100:
        variance = base/2
    else:
       variance  = base/4

    time_last_calib = mktime(datetime.now().timetuple())

    logging.info('recalibrated base: ' + str(base) + ' ' + 'variance: ' + str(variance))
    logging.debug(latest_readings)

    return (base, variance, time_last_calib)


def play_random_local_wave_file():
    """ plays random wave file from 'audio' directory"""
    wav_files = [f for f in listdir('audio') if isfile(join('audio',f)) ]
    # because random works better on a larger list of items:
    for i in range(0,3):
        wav_files = wav_files + wav_files
    system('aplay audio/' + choice(wav_files))


def get_serial_reading():
    """ gets latest reading from the serial buffer (flushes buffer before reading"""
    global ser
    ser.flushInput()  # attempt to keep commands from stacking up, always get latest reading
    reading = ser.readline()
    return (reading)


def status_check():
    """
       returns True or False: 'should we use this reading?'
       applies to an individual sensor reading
       checks status by reading local text file status.txt. (which gets update via fetch_status.py)
       """

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
            logging.debug('status = CA, recalibrating')
            return True

        elif status == 'OFF':
            logging.info("status = OFF - going off for 5 minutes")
            turned_off = True
            sleep(5*60)  # sleep n minutes then continue
            return True

    if turned_off == True:
        # status is on, but this was turned off before, so post a log msga
        logging.info("back on")
        turned_off = False
        return False  # we are back on


def consecutive_trigger_break():
    """ returns true if this sensor reading should be discarded because we are in a hold
        caused by excessivng alarm triggering (more than 5 in a row)
        this makes it so only 5 triggers can ever be called at a time, 15 min cooling off period ensues.
    """

    global base, variance, time_last_calib, last_consecutive_trigger_break, consecutive_triggers

    if consecutive_triggers < 5:
        return False

    # alarm has gone off 5 times in a row, should we stop this thing or what?
    timenow = mktime(datetime.now().timetuple())
    if not last_consecutive_trigger_break:
        # the last_consecutive_trigger_break is not set, let's set it now
        last_consecutive_trigger_break = timenow
        logging.info(" setting consecutive_trigger_break")
    else:
        if timenow > last_consecutive_trigger_break + 60 * 15:
            # 15 minutes have gone by since consecutive_trigger_break was set, turn it off and recalibrate
            base, variance, time_last_calib = calibrate()
            last_consecutive_trigger_break = 0
            logging.info("turning off consecutive_trigger_break")
            return False

    sleep(recalibrate_freq*2)  # sleep for n X the regular recalibration length, it needs extra time
    return True


class TriggerWemo(threading.Thread):
    """ turns on 2 Wemo switches (via gmail and IFTTT) and turns them off 5 minutes later.
        One wemo turns on a light and the other turns on an Arduino that emulates a wemo remote """

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        global last_roomba_trigger

        # trigger light switch wemo and turn off after a few minutes
        send_email('#ON', gmail_addy, gmail_pw, 'trigger@ifttt.com')
        logging.info("turning on Wemo light switch and roomba remote switch")

        # trigger the roomba?
        roomba_on = False  # if this becomes true then after sleeping we turn it back off
        timenow = mktime(datetime.now().timetuple())
        # to launch the roomba it must have been recharging at least 6 hours (WAG)
        # and refrain from launching roomba bt 11 am and 1pm because there are
        # too many false alarms during those hours
        if  timenow-last_roomba_trigger > 60*60*6 and localtime(time()).tm_hour not in roomba_off_hours:
                # launch!
                send_email('#ON_ROOMBA', gmail_addy, gmail_pw, 'trigger@ifttt.com')
                send_sms('Roomba launched at ' + str(strftime("%X").strip()), gmail_addy, gmail_pw, sms_recipients)
                last_roomba_trigger = timenow
                roomba_on = True

                logging.debug('last_roomba_trigger: ' + str(last_roomba_trigger))
                logging.info('roomba launched')
        else:
            logging.info('skipping roomba launch - ' + str(60*60*6 - (timenow-last_roomba_trigger)/60/60) + ' hours left to charge' )

        # this is how long the switch stays on:
        sleep(60)

        # now turn them off
        for i in range(0,2):  # twice just to be extra cautious and make sure it gets turned off for realzies
            send_email('#OFF', gmail_addy, gmail_pw, 'trigger@ifttt.com')
            if roomba_on:
                send_email('#OFF_ROOMBA', gmail_addy, gmail_pw, 'trigger@ifttt.com')
            logging.info("turned off Wemo light switch and roomba")
            sleep(15)


def main():
    """ this runs the loop that reads sensor readings, and does some initial setup, logging, things to keep track of"""

    global consecutive_triggers

    logging.error('hello main')

    # some vars to keep track of things
    first_reading = True

    # send an initial test sms
    if gmail_pw:
        logging.info("sending test sms...")
        send_sms('black cat sms alerts have begun', gmail_addy, gmail_pw, sms_recipients)
        last_sms = mktime(datetime.now().timetuple())
        logging.info("ok test sms worked!")

    # if you want sms control msg to command line user...
    sms_msg = "if you want sms control, run this in another shell: \n python fetch_status.py"
    print(sms_msg)

    # doing initial calibration..
    logging.info("doing initial calibration..")
    base, variance, time_last_calib = calibrate()

    while True:

        sleep(.5)  # check the serial reading every x time okay?
        timenow = mktime(datetime.now().timetuple())

        reading = get_serial_reading()

        # first check if we are even in status = ON here
        if status_check():
            logging.debug('taking status break')
            continue

        if first_reading:
            first_reading = False
            logging.info("hello first reading: " + reading)
            continue

        # tiny movement logging (for debugging)
        # todo: how to check status of logging level?
        if abs(int(reading) - int(base)) > 25:
            msg = "tiny movement reading: %s, base: %s, variance: %s, threshhold: %s" % (str(reading.strip()), str(base), str(variance), str(base-variance))
            logging.debug(msg)

        try:

            if int(reading) < (base-variance): # black cats always score lower than base
                # we haz a black cat!

                consecutive_triggers += 1

                if consecutive_trigger_break():
                    logging.info('hit consecutive trigger break, time out for a while...')
                    sleep(3)
                    continue

                # we are go. play a wav file
                play_random_local_wave_file()

                # trigger Wemo
                wemo = TriggerWemo()
                wemo.start()

                # log this event
                msg = "Black cat detected! - reading: %s base: %s signma: %s - %s" % (str(reading).strip(), str(base).strip(), str(variance).strip(), strftime("%a, %d %b %Y").strip())
                logging.info(msg)

                # send sms
                # todo: move this to it's own thread and do a sleep(30) init
                if gmail_pw and (timenow-last_sms > 30):  # minimum seconds between sms alerts please!
                    last_sms = timenow
                    send_sms(u'hello black cat %s' % str(strftime("%X").strip()), gmail_addy, gmail_pw, sms_recipients)

                """
                # play a mac creepy mac OSX voice - we have wav files so this is removed..
                # pick a creepy voice at random and scare a cat with it
                scary_msg = "Pssssst see see see see GET OUT OF HERE CAT!! Pssssst Pssssst Pssssst"
                shuffle(voices)
                voice, phrase = [v.strip() for v in voices[0].split('en_US    #')]
                msg = "say -r 340 -v %s %s " % (voice, scary_msg)
                system(msg)
                logging.info(msg)
                """

            else:
                # no black cat, nothing to see here
                consecutive_triggers = 0

                # do we need to calibrate?
                if timenow-time_last_calib > 60*recalibrate_freq:
                    base, variance, time_last_calib = calibrate()


        except ValueError:
            logging.info('ValueError: ' + str(reading))


if __name__ == "__main__":

    main()
