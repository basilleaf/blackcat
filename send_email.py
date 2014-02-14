#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
this sends an sms using gmail, this is not ideal and should
really use the Twilio instead, so you are conversing with
the same sender on your phone.

"""
# send_sms.py
import smtplib
from time import sleep

def send_email(msg, gmail_addy, gmail_pw, to_address):
    """ send an email, mostly for triggering the wemo """
    server = smtplib.SMTP( "smtp.gmail.com", 587)
    server.starttls()
    server.login( gmail_addy, gmail_pw)
    email_body = "Subject: %s\nTo:trigger@ifttt.com\n\n%s" % (msg, 'test')  # same subject as body
    server.sendmail(gmail_addy, to_address, email_body)
    server.quit()


def send_sms(msg, gmail_addy, gmail_pw, sms_recipients):
    if not gmail_pw: return

    server = smtplib.SMTP( "smtp.gmail.com", 587)
    server.starttls()
    server.login( gmail_addy, gmail_pw)

    for phone_no in sms_recipients:
        server.sendmail(gmail_addy, phone_no + '@vtext.com', "\n" + msg)
        sleep(1) # there's some buggy where it sends several texts in a row, this fixes
    server.quit()

