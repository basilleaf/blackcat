from __future__ import print_function
import os
from flask import Flask, request, redirect
import twilio.twiml

app = Flask(__name__)

f = open('status.txt')

@app.route("/", methods=['GET', 'POST'])
def hello():
    """Respond to incoming calls with a simple text message."""

    text_command = request.values.get('Body', False)
    text_command = str(text_command).strip().upper() if text_command else False

    resp = twilio.twiml.Response()

    if text_command and text_command not in ['ON','OFF','CAL','CALIBRATE']:
        resp.message("invalid command: " + text_command)

    elif text_command:
        # write text command to file
        print(text_command, file=f)
        resp.message("Cat Detector status changed to: " + text_command)

    else:
        # no text_command, just try to get current status
        try:
            status = open('status.txt').readlines()[0].strip()
            resp.message(status)
        except IOError:
            # default status is 'ON'
            status = 'ON'
            print(status, file=f)
            resp.message(status)

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)