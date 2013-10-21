### Black Cat Detector

Detect if black cat is coming through the cat door, and scare eem! Also: keep a log, and send an sms text when black cat detected.

We have 2 black cats that enter our kitchen and sometimes roam around the house, have some tasty food, and take naps. They also freak the hell out of our 2 orange tabbys.

Turns out you can detect a black cat against a white wall pretty accurately with a photocell and some ambient light (accurate meaning near zero false alarms when reading the orange cats).

This currently runs with Arduino tethered to a Mac. sensor.py reads serial port from Arduino, decides if it is seeing a black cat, uses Mac 'say' command to scare cat. Recalibrates occasionally.

So far has problems when ambient light is rapidly changing at dawn + dusk.
