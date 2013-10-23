# calibrate
from __future__ import print_function
from datetime import datetime
from time import strftime, mktime, sleep

def calibrate(ser, f):
    """
    this fails around sunset and sunrise, is good at stable ambient lighting
    """

    print("recalibrating..", file=f)
    f.flush()

    # take 10 readings
    latest_readings = []
    for c in range(0,10):
        reading = ser.readline()
        latest_readings.append(int(reading))
        sleep(1)

    # and recalculate base and variance
    base = int(sum(latest_readings)/len(latest_readings))

    # the sensor becomes more sensitive in brighter ambient lighting
    if base < 15:
        variance = int(base/2)
    elif base < 25:
        variance = int(base/3)
    else:
        variance = int(base/4)

    time_last_calib = mktime(datetime.now().timetuple())

    print("recalibrated " + datetime.fromtimestamp(mktime(datetime.now().timetuple())).strftime('%Y-%m-%d %H:%M:%S').strip(), file=f)
    print('base: ' + str(base) + ' ' + 'variance: ' + str(variance), file=f)

    # debug
    # print('%s %s %s' % (str(base), str(variance), str(time_last_calib)))

    return (base, variance, time_last_calib)
