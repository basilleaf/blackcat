"""
    This watches the remote status file (on s3) and updates a local status file
    it runs separately if you want sms control you have to run it

"""
from __future__ import print_function
from sensor import calibrate
from time import sleep
import urllib2

print('ok watching https://s3.amazonaws.com/blackcatsensor/status')

while True:
    try:
        status =  urllib2.urlopen('https://s3.amazonaws.com/blackcatsensor/status').readlines()[0]
        f = open('/home/pi/blackcat/status.txt','w')
        print(status, file=f),
        f.close()
    except urllib2.URLError:
        pass
    sleep(60)  # check every minute
