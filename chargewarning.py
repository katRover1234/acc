import time
import gopigo

def time_warning():
    volt = 0
    while True:
        volt = gopigo.volt()
        if volt < 9:
            print "Warning: your voltage is at ",volt,"v and below safe levels."
            print "Stop and charge the device to prevent potential damage."
        time.sleep(120)
