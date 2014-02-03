# calibrate
from __future__ import print_function
from datetime import datetime
from time import strftime, mktime, sleep

def get_trigger_limit(base):
    # ambient lighting effects rate of false alarms
    # tweek this method according to observation
    # right now we have false alarm around noon on sunny days without any cat
    # zero false positives woot!

    # the sensor deamon runs this:
    # if int(reading) < (base-trigger_limit):
    #   trigger alarm
    #
    # (note that 'trigger_limit' may still be referred to as 'variance' elsewhere)
    if base > 350:
       trigger_limit = int(base/4)  # based on observation, something about noontime sun
    if base > 125:
        trigger_limit = int(base/2)
    else:
        trigger_limit = int(base/4)

    return trigger_limit


def calibrate(ser, f):

    print("recalibrating..")

    # take 10 readings
    latest_readings = []
    for c in range(0,10):
        reading = ser.readline()
        latest_readings.append(int(reading))
        sleep(.3)

    # and recalculate base and trigger_limit/trigger_limit

    base = int(sum(latest_readings)/len(latest_readings))

    trigger_limit = get_trigger_limit(base)

    time_last_calib = mktime(datetime.now().timetuple())

    print("recalibrated " + datetime.fromtimestamp(mktime(datetime.now().timetuple())).strftime('%Y-%m-%d %H:%M:%S').strip())
    print('base: ' + str(base) + ' ' + 'trigger_limit: ' + str(trigger_limit))

    # debug
    # print('%s %s %s' % (str(base), str(trigger_limit), str(time_last_calib)))

    return (base, trigger_limit, time_last_calib)
