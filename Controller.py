from gopigo import *
import time
import multiprocessing
import ACC
import chargewarning
def commandList():
    print "*****************************************************"
    print "*  Commands:                                        *"
    print "*  go                                               *"
    print "*  stop                                             *"
    print "*  speed                                            *"
    print "*  exit                                             *"
    print "*****************************************************"
command = ""
speed = 100
min_speed = 50
max_speed = 150
queue = multiprocessing.Queue()
acc = ACC.ACC()
acc_process = multiprocessing.Process(target = acc.main_loop, args=(queue,))
acc_process.start()
volt_process = multiprocessing.Process(target = chargewarning.time_warning)
volt_process.start()

while command != "exit":
    commandList()
    command = raw_input()
    if "go" == command:
        queue.put(command)    
    elif "stop" == command:
        queue.put(command)
        stop()
    elif "speed" == command:
        print "Enter speed (",min_speed,"-",max_speed,"):"
        try:
            speed = int(raw_input())
            if(speed < min_speed or speed > max_speed):
                print "Invalid speed!"
            else:
                queue.put(speed)
        except ValueError:
            print "Use numbers only!"
    elif "exit" == command:
        queue.put(command)
volt_process.terminate()
acc_process.join()
stop()
print "Goodbye!"
