import RPi.GPIO as gpio
import time

TRIGER = 24
ECHO = 23

gpio.setmode(gpio.BCM)
gpio.setwarnings(False)

gpio.setup(TRIGER, gpio.OUT)
gpio.setup(ECHO, gpio.IN)

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
        
        print("Distance: %.1f cm" % dist)
        time.sleep(0.4)
except:
    gpio.cleanup()
        