#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import boto
import urllib2

"""
    updates status in local status.txt and on remote s3 bucket

    you can update the remote status with the heroku app
    but the local deployment also needs to update the status
    (ie like turning it to ON after it finishes calibrating)

"""

# get config vars, where are we?
try:
    # this works if we are on heroku
    test = os.environ['aws_access_key_id']
    config = os.environ
except KeyError:
    # we must be local
    from secrets import secrets
    config = secrets

aws_access_key_id = config['aws_access_key_id']
aws_secret_access_key = config['aws_secret_access_key']
aws_bucket_name = config['aws_bucket_name']

def update_status(status):

    print("updating status to " + status)
    # update local status
    f = open('/home/pi/blackcat/status.txt','w')
    print(status, file=f),
    f.close()

    # update status on s3
    s3 = boto.connect_s3(aws_access_key_id,aws_secret_access_key)
    bucket = s3.create_bucket(aws_bucket_name)
    key_name = 'status'
    bucket.delete_key(key_name)
    key = bucket.new_key(key_name)
    key.set_contents_from_string(status)
    if key.set_acl('public-read'):
        return True
