# IoT
import RPi.GPIO as gpio
import asyncio

import time


async def distance_logic():
	# distance sensor
	TRIGER = 24
	ECHO = 23
	
	gpio.setmode(gpio.BCM)
	gpio.setwarnings(False)

	gpio.setup(TRIGER, gpio.OUT)
	gpio.setup(ECHO, gpio.IN)
	
	try:
		gpio.output(TRIGER, gpio.LOW)
		await asyncio.sleep(0.2)
		gpio.output(TRIGER, gpio.HIGH)
		await asyncio.sleep(0.00002)
		gpio.output(TRIGER, gpio.LOW)
		
		while gpio.input(ECHO)==gpio.LOW:
			startTime = time.time()
			
		while gpio.input(ECHO) == gpio.HIGH:
			endTime = time.time()
		
		period = endTime - startTime
		dist1 = period * 1000000 / 58
		dist2 = period * 17241
		
		return min(dist1, dist2)
	except Exception as e:
		print(e)
		return -1
		
