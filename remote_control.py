from __future__ import print_function
import os
import urllib2
import boto
from flask import Flask, request, redirect
import twilio.twiml
from update_status import update_status

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def hello():

    text_command = request.values.get('Body', False)
    text_command = str(text_command).strip().upper() if text_command else False

    resp = twilio.twiml.Response()

    if text_command and text_command not in ['ON','OFF','CAL','CALIBRATE','CALIB','STATUS','STAT']:
        resp.message("invalid command: " + text_command)

    elif text_command:
        if text_command[0:3] == 'STA':
            status =  urllib2.urlopen('https://s3.amazonaws.com/blackcatsensor/status').readlines()[0]
            resp.message("Current Cat Detector status is: " + status)
        else:
            # write text command to s3
            update_status(text_command)
            resp.message("Cat Detector status changed to: " + text_command)

    else:
        # no text_command, just try to get current status
        status =  urllib2.urlopen('https://s3.amazonaws.com/blackcatsensor/status').readlines()[0]
        resp.message(status)

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)
