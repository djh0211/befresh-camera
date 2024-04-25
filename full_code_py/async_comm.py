import time
import logging
import numpy as np
import json
from operator import eq
import asyncio
from concurrent.futures import ThreadPoolExecutor
import random
from collections import deque

# IoT
import RPi.GPIO as gpio

# Camera
import cv2
from pyzbar.pyzbar import decode
from picamera2 import Picamera2, Preview
from libcamera import controls



async def distance_logic():
	try:
		gpio.output(TRIGER, gpio.LOW)
		await asyncio.sleep(0.1)
		gpio.output(TRIGER, gpio.HIGH)
		await asyncio.sleep(0.00002)
		gpio.output(TRIGER, gpio.LOW)
		
		while gpio.input(ECHO)==gpio.LOW:
			startTime = time.time()
			
		while gpio.input(ECHO) == gpio.HIGH:
			endTime = time.time()
		
		period = endTime - startTime
		dist = period * 34300 / 2
		return dist
	except Exception as e:
		print(e)
		return -1
    
        
async def bluetooth_connect(containerId):
	# print('hihi')
	while True:
		await asyncio.sleep(5)
		rand = random.random()
		if rand >= 0.5:
			print(f'{containerId} container bluetooth connected!!')
			return 1 
		print(f'{containerId} retry again....')

async def register_food(containerId):
	await asyncio.sleep(10)
	print(f'{containerId} registered!!....')
	return 1

			
	
	

# QR/Valid Date mode
async def camera_mode():
	picam2.start_preview(Preview.QTGL)
	picam2.start()
	qr_history_set = set()
	futures_dic = {}
	distance_threshold = 15
	start = time.time()
	
	while True:
		array = picam2.capture_array()
		qr_list = decode(array)
		# calculate distance
		distance_task = asyncio.create_task(distance_logic())
		
		if qr_list:
			for qr in qr_list:
				try:
					if eq(qr.type,'QRCODE'):
						string_data = qr.data.decode('utf-8')
						data = json.loads(string_data)
						if 'containerId' in data and string_data not in qr_history_set:
							print(f'containerId: {data}')
							qr_history_set.add(string_data)
							containerId = data['containerId']
							# async bluetooth connect
							### future_bluetooth = loop.run_in_executor(executor, bluetooth_connect, containerId)
							future_bluetooth = asyncio.create_task(bluetooth_connect(containerId))
							futures_dic[f'bluetooth_{containerId}'] = future_bluetooth
							### task_bluetooth_connect = asyncio.create_task(bluetooth_connect(containerId))
							# food name STT
							# async food register
							task_register_food = asyncio.create_task(register_food(containerId))
							futures_dic[f'register_{containerId}'] = task_register_food
							
				except Exception as e:
					print(e)
					
		# calculated distance gather -> logic		
		distance = await distance_task
		if distance == -1:
			# distance error
			return -1
		# print(f'distance: {distance} cm')
		if distance < distance_threshold:
		 	start = time.time()
		 	continue
		# have to change time threshold
		elif time.time() - start >= 10:
			# no action now
			break
			
	return futures_dic

        
    
async def program():
	# loop = asyncio.get_running_loop()
	# executor = ThreadPoolExecutor()		
	while True:
		selected_mode = int(input("please select mode"))
		# QR/Valid Date mode : 1
		if selected_mode == 1:
			camera_futures_dic = await camera_mode()
			if camera_futures_dic == -1:
				continue
			results = await asyncio.gather(*camera_futures_dic.values())
			print('**********************')
			for name, result in zip(camera_futures_dic.keys(), results):
				print(f'{name}: {result}')
		# General mode : 2
		elif selected_mode == 1:
			continue
		else:
			continue
				
                
    




if __name__ == "__main__":
	# distance sensor
	TRIGER = 24
	ECHO = 23

	gpio.setmode(gpio.BCM)
	gpio.setwarnings(False)

	gpio.setup(TRIGER, gpio.OUT)
	gpio.setup(ECHO, gpio.IN)
	
	# camera_init
	picam2 = Picamera2()
	preview_config = picam2.create_preview_configuration(buffer_count=3)
	# capture_config = picam2.create_still_configuration(buffer_count=3)
	picam2.configure(preview_config)
	picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})

	# main program
	asyncio.run(program())
