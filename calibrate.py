# calibrate
from __future__ import print_function
import sys

from datetime import datetime
from time import strftime, mktime, sleep


def calibrate(ser, f):

    print("recalibrating..")

    # take 10 readings
    latest_readings = []
    error_count = 0
    for c in range(0,5):
        reading = ser.readline()
        try:
            latest_readings.append(int(reading))
        except ValueError:
            # how many time will we let this trip?
            error_count += 1
            if error_count > 5:
                print("could not calibrate, errors in reading serial line as int")
                sys.exit()

    # and recalculate base and variance
    base = int(sum(latest_readings)/len(latest_readings))

    # the sensor becomes less sensitive in brighter ambient lighting
    if base > 100:
    	variance = base/2
    else:
	   variance  = base/4

    time_last_calib = mktime(datetime.now().timetuple())

    print("recalibrated " + datetime.fromtimestamp(mktime(datetime.now().timetuple())).strftime('%Y-%m-%d %H:%M:%S').strip())
    print('base: ' + str(base) + ' ' + 'variance: ' + str(variance))

    # debug
    # print('%s %s %s' % (str(base), str(variance), str(time_last_calib)))

    return (base, variance, time_last_calib)
