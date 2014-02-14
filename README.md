### Black Cat Detector

Detect if black cat is coming through the cat door, and scare eem! 
    - remote sms control (on, off, calibrate) via Twilio/Flask app running on Heroku (remote_control.py)
    - plays scary sounding .wav file (or can just play creepy Mac voice) 
    - Turns on a Wemo switch (and turns it off a few minutes later) 

run it: 
    
    python sensor.py

black_cat_detector.ino runs on the Arduino
sensor.py is the detection script
fetch_status.py watches a remote file on s3 for status updates

### Background:

We have 2 black cats that enter our kitchen and sometimes roam around the house, have some tasty food, and take naps. They also freak the hell out of our 2 orange tabbys.

Turns out you can detect a black cat against a white wall pretty accurately with a photocell and some ambient light (accurate meaning near zero false alarms when reading the orange cats). Our orange/buff cats often reflect back a number higher than the reading for ambient light, the dark cats always reflect back a lower number.

This currently runs via cron (@reboot) on a Raspberry pi with Arduino connected via usb cable.

Here is the most frequent offender "Big Steve" making a hasty retreat. The sensor is embedded inside a small black ring box to the left of the cat flap:

<img src = "https://dl.dropboxusercontent.com/u/22391580/big_steve_gets_yelled_at.jpg">


### install something like.. 

    git clone git@github.com:basilleaf/blackcat.git
    cd blackcat
    echo  "ON" > status
    touch black_cat_sightings.log
    cp secrets_template.py secrets.py  # edit this
    virtualenv venv --distribute
    source venv/bin/activate
    pip install -r requirements.txt
    

### run:
    python fetch_status.py  # start the deamon to check for SMS status updates
    python sensor.py  
    tail -f black_cat_sightings.log


<3
<img src = "http://24.media.tumblr.com/e724ec40de93e65324ed1828df68da07/tumblr_mzyynrWrjc1qzaxi1o1_1280.jpg">
