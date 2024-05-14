import time
import logging

# IoT
from pyfirmata import Arduino, util
import RPi.GPIO as gpio

mode_var = "light"

    
def light_sensor_logic():
    global mode_var
    bright_cnt = 0
    dark_cnt = 0
    threshold = 3
    print("light sensor start")
    try:
        while True:
            time.sleep(0.5)
            light_rate = board.analog[0].read()
            # print(light_rate, bright_cnt, dark_cnt)
            if (0.3 < light_rate):
                dark_cnt += 1
                if threshold <= dark_cnt:
                    # init bright_cnt because it's not open signal
                    bright_cnt = 0
            # bright
            else:
                bright_cnt += 1
                if threshold <= bright_cnt:
                    # user opened the refrigerator -> distance sensor run
                    mode_var = "distance"
                    break
    except Exception as e:
        logging.warning(f"Exception raise : light sensor : {e}")
        
def distance_logic():
    global mode_var
    threshold = 3
    cnt_detect = 0
    cnt_not_detect = 0
    print("distance sensor start")
    try:
        while True:
            gpio.output(TRIGER, gpio.LOW)
            time.sleep(0.1)
            gpio.output(TRIGER, gpio.HIGH)
            time.sleep(0.00002)
            gpio.output(TRIGER, gpio.LOW)
            
            while gpio.input(ECHO)==gpio.LOW:
                startTime = time.time()
                
            while gpio.input(ECHO) == gpio.HIGH:
                endTime = time.time()
            
            period = endTime - startTime
            dist = period * 34300 / 2
            
            if 10 <= dist < 25:
                cnt_detect += 1
                
            else:
                cnt_not_detect += 1
                if 2 <= cnt_not_detect:
                    cnt_not_detect = 0
                    cnt_detect = 0
                    
            
            print("Distance: %.1f cm" % dist)
            time.sleep(0.2)
    except:
        gpio.cleanup()
        
# light sensor async -> stop distance sensor
        
    
def program():
    global mode_var
    mode_var = "light"
    
    while True:
        print(mode_var)
        # light sensor logic
        if mode_var == "light":
            light_sensor_logic()
        # microwave distance logic
        elif mode_var == "distance":
            # distance_logic()
            continue

            
                
    




if __name__ == "__main__":
    # light sensor
    board = Arduino('/dev/ttyACM0')
    it = util.Iterator(board)
    it.start()
    board.analog[0].enable_reporting()
    
    # distance sensor
    TRIGER = 24
    ECHO = 23

    gpio.setmode(gpio.BCM)
    gpio.setwarnings(False)

    gpio.setup(TRIGER, gpio.OUT)
    gpio.setup(ECHO, gpio.IN)
    
    # main program
    program()