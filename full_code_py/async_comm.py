import time
import logging
import numpy as np
import json
from operator import eq
import asyncio
from concurrent.futures import ThreadPoolExecutor
import random
from collections import deque
from dotenv import load_dotenv
import os
from multiprocessing import Process, Queue, Value
import queue

# IoT
import RPi.GPIO as gpio

# Camera
import cv2
from pyzbar.pyzbar import decode
from picamera2 import Picamera2, Preview
from libcamera import controls

# Audio
import struct
import pyaudio
import pvporcupine



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

def wakeword_detection(multiprocessing_queue, exit_flag):
	# audio_init
	porcupine = pvporcupine.create(
		access_key=PORCUPINE_KEY,
		keyword_paths=[KEYWORD_PATH],
		model_path=MODEL_PATH
	)
	pa = pyaudio.PyAudio()
	audio_stream = pa.open(
						rate=porcupine.sample_rate,
						channels=1,
						format=pyaudio.paInt16,
						input=True,
						frames_per_buffer=porcupine.frame_length)
	
	prev_timestamp = None
	while True:
		if exit_flag == 1:
			return
		pcm = audio_stream.read(porcupine.frame_length)
		pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
		keyword_index = porcupine.process(pcm)
		
		if keyword_index == 0:
			now = time.time()
			if prev_timestamp is None or now - prev_timestamp >= 2:
				print(111)
				# to avoid redundant call
				data = {}
				data['type'] = 'wakeword'
				data['payload'] = 'general_register'
				data['time'] = time.time()
				multiprocessing_queue.put(data)

			
def general_mode():
	# STT
	# there is no cancel, if timeout -> cancel
	#########################
	print("its general mode")
	time.sleep(2)
	print("general mode done.")
	
	

# QR/Valid Date mode
async def camera_mode(async_queue):
	picam2.start_preview(Preview.QTGL)
	picam2.start()
	qr_history_set = set()
	futures_dic = {}
	distance_threshold = 15
	start = time.time()
	
	while True:
		
		try:
			if async_queue.qsize() > 0:
				data_recv = await async_queue.get()
				if data_recv['type'] == 'wakeword' and data_recv['payload'] == 'general_register':
					# turn to general mode
					queue_in_time = data_recv['time']
					print('its general mode!!!!!')
					# general_mode()	
		except queue.Empty:
			# no data in queue now
			pass

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
			# distance error ignore once
			continue
		# print(f'distance: {distance} cm')
		if distance < distance_threshold:
		 	start = time.time()
		 	continue
		# have to change time threshold
		elif time.time() - start >= 10:
			# no action now -> register all
			picam2.stop_preview()
			picam2.stop()
			break
			
	# register mode exit. if you want to power register mode again, press the button1
	return futures_dic

async def queue_reader(multiprocessing_queue, async_queue):
	while True:
		if not multiprocessing_queue.empty():
			msg = multiprocessing_queue.get()
			########################################
			# for multiprocessing <-> asyncio compatible
			# wakeword process publish message
			# so we have to publish message to async_queue
			await async_queue.put(msg)
		else:
			await asyncio.sleep(0.1)  
# need to fix            
async def queue_consumer(async_queue):
	while True:
		
		try:
			data_recv = multiprocessing_queue.get(block=False)
			if data_recv['type'] == 'wakeword' and data_recv['payload'] == 'general_register':
				# turn to general mode
				queue_in_time = data_recv['time']
				general_mode()	
		except queue.Empty:
			# no data in queue now
			pass
    
async def program():

	while True:
		selected_mode = int(input("please select mode"))
		# QR/Valid Date mode : 1
		if selected_mode == 1:
			# multiprocessing
			multiprocessing_queue = Queue()
			print(1)
			exit_flag = Value('i', 0) # int type
			# wakeword_process = Process(target=wakeword_detection, args=(multiprocessing_queue, exit_flag,))
			# camera_process = Process(target=camera_process_wrapper, args=(multiprocessing_queue,))
						
			async_queue = asyncio.Queue()
			print(2)
			# wakeword_process.start()
			# queue_reader = asyncio.create_task(queue_reader(multiprocessing_queue, async_queue))
			
			camera_futures_dic = await camera_mode(async_queue)
			if camera_futures_dic == -1:
				continue
			results = await asyncio.gather(*camera_futures_dic.values())
			print('**********************')
			for name, result in zip(camera_futures_dic.keys(), results):
				print(f'{name}: {result}')
			
			# queue_reader.cancel()
			# try:
			# 	await queue_reader
			# except asyncio.CancelledError:
			# 	print('queue_reader canceled well :)')
				
			exit_flag = 1
			# wakeword_process.join()

			
			
	
		# General mode : 2
		else:
			continue
				
                
    




if __name__ == "__main__":
	# load .env
	load_dotenv()
	PORCUPINE_KEY = os.getenv('porcupine_key')
	KEYWORD_PATH = os.getenv('porcupine_keyword_path')
	MODEL_PATH = os.getenv('porcupine_model_path')
	
	
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
