from __future__ import print_function
from calibrate import calibrate
from time import sleep
import urllib2

while True:
    try:
        status =  urllib2.urlopen('https://s3.amazonaws.com/blackcatsensor/status').readlines()[0]
        f = open('status','w')
        print(status, file=f),
        f.close()
    except urllib2.URLError:
        pass
    sleep(60)  # check every minute
