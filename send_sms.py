# send_sms.py
import smtplib
from time import sleep

def send_sms(msg, gmail_addy, gmail_pw, sms_recipients):
    if not gmail_pw: return

    server = smtplib.SMTP( "smtp.gmail.com", 587)
    server.starttls()
    server.login( gmail_addy, gmail_pw)

    for phone_no in sms_recipients:
        server.sendmail(gmail_addy, phone_no + '@vtext.com', "\n" + msg)
        sleep(1) # there's some buggy where it sends several texts in a row, this fixes
    server.quit()
