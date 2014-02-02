# calibrate
from __future__ import print_function
from datetime import datetime
from time import strftime, mktime, sleep

def calibrate(ser, f):

    print("recalibrating..")

    # take 10 readings
    latest_readings = []
    for c in range(0,10):
        reading = ser.readline()
        latest_readings.append(int(reading))
        sleep(.3)

    # and recalculate base and variance
    base = int(sum(latest_readings)/len(latest_readings))

    # the sensor becomes more sensitive in brighter ambient lighting
    if base > 350:
	   variance = int(base/4)  # based on observations
    if base > 125:
        variance = int(base/2)
    else:
        variance = int(base/4)

    time_last_calib = mktime(datetime.now().timetuple())

    print("recalibrated " + datetime.fromtimestamp(mktime(datetime.now().timetuple())).strftime('%Y-%m-%d %H:%M:%S').strip())
    print('base: ' + str(base) + ' ' + 'variance: ' + str(variance))

    # debug
    # print('%s %s %s' % (str(base), str(variance), str(time_last_calib)))

    return (base, variance, time_last_calib)
