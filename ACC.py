from gopigo import *
import time
import signal
import sys
import multiprocessing


#The following variables are used to compensate for asymetries in the robot wheels.
#Use negative values to reduce the wheel speed.
RIGHTMORE_LEFT = 2 #4
RIGHTMORE_RIGHT = -2 #-2
LEFTMORE_LEFT = -2  #-2
LEFTMORE_RIGHT = 2 #2
BALANCE_LEFT = 0
BALANCE_RIGHT = 0


#get encoder values
time.sleep(0.1)
left_enc_init = enc_read(0)
time.sleep(0.1)
right_enc_init = enc_read(1)
    
####Really really scary pin functions, don't touch
###PS TY chris wells
###honorable mention: gopigo and dexter industries
ADDRESS = 0x08
ENC_READ_CMD = [53]

import smbus
bus = smbus.SMBus(1)

def write_i2c_block(address, block):
    try:
        op = bus.write_i2c_block_data(address, 1, block)
        time.sleep(0.005)
        return op
    except IOError:
        return -1
    return 1

def enc_read(motor):
    write_i2c_block(ADDRESS, ENC_READ_CMD+[motor,0,0])
    #time.sleep(0.01)
    #time.sleep(0.08)
    try:
        b1 = bus.read_byte(ADDRESS)
        b2 = bus.read_byte(ADDRESS)
    except IOError:
        return -1
    if b1 != -1 and b2 != -1:
        v = b1 * 256 + b2
        return v
    else:
        return -1

US_CMD = [117]

def us_dist(pin):
    write_i2c_block(ADDRESS, US_CMD+[pin,0,0])
    time.sleep(0.01)
    #time.sleep(0.08)
    try:
        b1 = bus.read_byte(ADDRESS)
        b2 = bus.read_byte(ADDRESS)
    except IOError:
        return -1
    if b1 != -1 and b2 != -1:
        v = b1 * 256 + b2
        return v
    else:
        return -1

def check_encoders():
    
    #print "left: ",encl1," ",encl2," ",encl3
    #print "right: ",encr1," ",encr2," ",encr3
    count = 0
    while count < 10:
    #while True:
        encr = enc_read(1)
        encl = enc_read(0)
    
        left_enc_diff = encl - left_enc_init
        right_enc_diff = encr - right_enc_init

        diff = left_enc_diff - right_enc_diff
        encoders_similar = diff > 50 or diff < 50
        if encl > 0 and encr > 0 and not encoders_similar:
            break
        count +=1
    return (abs(left_enc_diff), abs(right_enc_diff))

def compensate(speed):
    if speed < 60:
        return 0
    else:
        if speed > 40:
            return int((9.0/(speed/100.0)) /1.5) + 10
        else:        
            return (int(speed/100) * 10) + 5



class ACC:
    def __init__(self):

        #set encoders
        self.left_enc_diff = 0
        self.right_enc_diff = 0
        
        #set initial speed
        self.minimum_start = 50
        self.max_speed = 150
        self.accel = 10
        self.speed = self.minimum_start
        #set distances
        self.min_safe_dist = 30
        self.max_safe_dist = 50

    def main_loop(self,q):
        #initalize detected object to 
        detected_object = True
        should_move = False
        old_dist = 0
        set_speed(self.speed)
        command = ""
        queue = q
        run_acc = False
        print "left init: ",left_enc_init
        print "right init: ",right_enc_init
        
        try:
            while command != "exit":
                if not queue.empty():
                    command = queue.get_nowait()
                    #print command
                    if command == "go":
                        run_acc = True
                        set_right_speed(self.minimum_start)
                        set_left_speed(self.minimum_start)
                        fwd()
                    elif command == "stop":
                        run_acc = False
                        stop()
                    elif command != "exit":
                        self.max_speed = command
                if run_acc:
                    balance = True
                    can_accel = True
                    distance = us_dist(15)
                    print "dist: ",distance," cm"
                    if(distance > 0):
                        self.max_safe_dist = (1*self.speed) + self.min_safe_dist
                        if distance < self.min_safe_dist:
                            stop()
                            self.speed = self.minimum_start
                            set_speed(self.speed)
                            should_move = False
                            #print "Hazard!  Emergency stop!"
                        elif distance >= self.min_safe_dist and distance <= self.max_safe_dist:
                            #print "Object ahead!"
                            can_accel = False
                            if old_dist > distance:
                                #print "Approching, decelerating."
                                self.speed = self.speed - (self.accel)
                                if self.speed < self.minimum_start:
                                    self.speed = self.minimum_start
                                #set_speed(speed)
                                set_left_speed(self.speed) #(comp - 25))
                                set_right_speed(self.speed + compensate(self.speed))  #(comp + 100))    
                                balance = False
                        else:
                            fwd()
                            should_move = True
                        old_dist = distance
                    elif distance == -1:#distance == 0 or distance == -1:
                        print "The Distance sensor has malfunctioned"
                        time.sleep(.01)
                        
                    if should_move:
                        #calculate the difference since last tick
                        left_enc_diff,right_enc_diff = check_encoders()
                        print "left enc:", left_enc_diff
                        print "right enc:", right_enc_diff
                        
                        #update the previous tick values
                        if balance:
                            #if the left wheel has moved farther than right
                            #(it leans to the right)
                            if left_enc_diff > right_enc_diff:
                                print "left more"
                                set_left_speed(self.speed + compensate(self.speed)*LEFTMORE_LEFT) #(comp - 25))
                                set_right_speed(self.speed + compensate(self.speed)*LEFTMORE_RIGHT)#(comp + 100))
                                #print "left speed", speed - comp
                                #print "right speed",speed + comp
                            #if the right wheel has moved farther than left
                            #(it leans to the left)
                            elif left_enc_diff < right_enc_diff:
                                print "right more"
                                set_left_speed(self.speed + compensate(self.speed)*RIGHTMORE_LEFT)
                                set_right_speed(self.speed + compensate(self.speed)*RIGHTMORE_RIGHT)
                                #print "left speed", speed + comp
                                #print "right speed",speed - comp
                            else:
                                print "Balanced"
                                #keep the speeds equal
                                set_left_speed(self.speed + compensate(self.speed)*BALANCE_LEFT)
                                set_right_speed(self.speed + compensate(self.speed)*BALANCE_RIGHT)
                                #print "left speed", speed
                                #print "right speed",speed
                        else:
                            print "Balanced"
                            #keep the speeds equal
                            set_left_speed(self.speed)
                            set_right_speed(self.speed)
                            #print "left speed", speed
                            #print "right speed",speed
                    #print "speeds: " , read_motor_speed_cmd()
                    if can_accel:
                        if self.speed < self.max_speed:
                            self.speed = self.speed + self.accel
                        else:
                            self.speed = self.max_speed
                        set_speed(self.speed)
                    time.sleep(.05)
                    #print "******************"
            #print "done"
        except KeyboardInterrupt:
                stop()
