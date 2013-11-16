try:
    import  RPi.GPIO

    # this is a raspberry pi!
    serial_port = '/dev/ttyACM0'

except ImportError:

    # this is an aging macbook air
    serial_port = '/dev/tty.usbmodemfd121'
