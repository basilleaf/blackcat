from __future__ import print_function
import os
import boto
import urllib2
from flask import Flask, request, redirect
import twilio.twiml

app = Flask(__name__)

aws_access_key_id = os.environ['aws_access_key_id']
aws_secret_access_key = os.environ['aws_secret_access_key']
aws_bucket_name = os.environ['aws_bucket_name']
aws_url = os.environ['aws_url']

@app.route("/", methods=['GET', 'POST'])
def hello():

    text_command = request.values.get('Body', False)
    text_command = str(text_command).strip().upper() if text_command else False

    resp = twilio.twiml.Response()

    if text_command and text_command not in ['ON','OFF','CAL','CALIBRATE','CALIB']:
        resp.message("invalid command: " + text_command)

    elif text_command:
        # write text command to s3
        s3 = boto.connect_s3(aws_access_key_id,aws_secret_access_key)
        bucket = s3.create_bucket(aws_bucket_name)
        key_name = 'status'
        bucket.delete_key(key_name)
        key = bucket.new_key(key_name)
        key.set_contents_from_string(text_command)
        key.set_acl('public-read')
        resp.message("Cat Detector status changed to: " + text_command)

    else:
        # no text_command, just try to get current status
        status =  urllib2.urlopen('https://s3.amazonaws.com/blackcatsensor/status').readlines()[0]
        resp.message(status)

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)