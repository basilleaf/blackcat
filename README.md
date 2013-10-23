### Black Cat Detector

Detect if black cat is coming through the cat door, and scare eem! Also: keep a log, and if desired send an sms when black cat detected.

Added a Twilio/Heroku/Flask app remote_control.py to send control commands via SMS: on, off, calibrate.

### Background:

We have 2 black cats that enter our kitchen and sometimes roam around the house, have some tasty food, and take naps. They also freak the hell out of our 2 orange tabbys.

Turns out you can detect a black cat against a white wall pretty accurately with a photocell and some ambient light (accurate meaning near zero false alarms when reading the orange cats, near zero meaning we've never had a false alarm against an orange cat!). Our orange/buff cats always reflect back a number higher than the reading for ambient light, the dark cats always reflect back a lower number, voila!

This currently runs with Arduino tethered to a Mac. sensor.py reads serial port from Arduino, decides if it is seeing a black cat, uses Mac 'say' command to scare cat.

Update: Cat got wise to the Mac robo voices, so now we have it play .wav files, the sounds of us running down the hall and yelling.. this works so far!

Recalibrates occasionally. Commands can be sent via SMS to heroku app remote_control.py to turn on, off, or calibrate.

So far it problems when ambient light is rapidly changing at dawn + dusk, especially at dusk. When ambient light fades quickly it reacts as though it is seeing a black cat and sounds the alarm repeatedly! So far fix has been to either only use it after dark, or to recalibrate more often, can also send SMS to turn off/recalibrate on the fly.
