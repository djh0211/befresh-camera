from module.distance_module import distance_logic
from module.SignalBlock import SignalBlock

import asyncio
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
import json
import re
from datetime import datetime, date


# Camera
import cv2
from pyzbar.pyzbar import decode
from picamera2 import Picamera2, Preview
from libcamera import controls
import pytesseract

# stt
from gtts import gTTS
from io import BytesIO
import pyaudio
import wave
import speech_recognition as sr
import pygame



signal_block = SignalBlock()

#######################################################################
# camera/general
async def bluetooth_connect(containerId):
	# print('hihi')
	while True:
		await asyncio.sleep(5)
		rand = random.random()
		if rand >= 0.5:
			print(f'{containerId} container bluetooth connected!!')
			return containerId 
		print(f'{containerId} retry again....')
async def register_QR_food(containerId, food_name):
	await asyncio.sleep(10)
	data = {}
	data['food_type'] = 'QR'
	data['container_id'] = containerId
	data['food_name'] = food_name
	print(f'QR {containerId} registered!!.... {data}')
	return data
async def register_OCR_food(validate_time, food_name):
	await asyncio.sleep(10)
	data = {}
	data['food_type'] = 'OCR'
	data['validate_time'] = validate_time
	data['food_name'] = food_name
	print(f'OCR registered!!.... {data}')
	return data
async def register_general_food(food_name):
	await asyncio.sleep(10)
	data = {}
	data['food_type'] = 'GENERAL'
	data['food_name'] = food_name
	print(f'GENERAL registered!!.... {data}')
	return data
async def general_mode():
	global signal_block
	# STT
	# there is no cancel, if timeout -> cancel
	#########################
	print("its general mode")
	# await asyncio.sleep(2)
	food_name = STT(mic, recognizer)
	general_register_task = asyncio.create_task(register_general_food(food_name))
	await signal_block.signal_off()
	return food_name, general_register_task
# QR/Valid Date mode
async def camera_mode():
	# global async_queue
	global signal_block

	picam2.start_preview(Preview.QTGL)
	picam2.start()
	qr_history_set = set()
	futures_dic = {}
	distance_threshold = 20
	start = time.time()
	
	while True:
		
		try:
			signal_flag = await signal_block.get_flag()
			if signal_flag == 1:
				data_recv = await signal_block.get_data()
				print(data_recv)
				if data_recv['type'] == 'wakeword' and data_recv['payload'] == 'general_register':
					# turn to general mode
					queue_in_time = data_recv['time']
					print('its general mode!!!!!')
					print(data_recv)
					food_name, general_register_task = await general_mode()
					futures_dic[f'register_GENERAL_{food_name}'] = general_register_task
	
		except queue.Empty:
			# no data in queue now
			pass
		

		array = picam2.capture_array()
		
		qr_list = decode(array)
		# calculate distance
		distance_task = asyncio.create_task(distance_logic())
		
		# qr_logic
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
							food_name = STT(mic, recognizer)

							# async food register
							task_register_food = asyncio.create_task(register_QR_food(containerId, food_name))
							futures_dic[f'register_QR_{containerId}'] = task_register_food
							
				except Exception as e:
					print(e)
		# ocr logic
		rgb_image = cv2.cvtColor(array, cv2.COLOR_BGR2RGB)
		custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789.'
		text = pytesseract.image_to_string(rgb_image, config=custom_config)
		date_pattern = r'\d{2,}\.\d{1,}\.\d{1,}'
		dates = re.findall(date_pattern, text)
		if dates:
			date_splitted = dates[0].split('.')
			
			year = int(str(datetime.today().year)[:-2] + date_splitted[0][:-2])
			month = int(date_splitted[1])
			day = int(date_splitted[2][:2])
			
			validate_time = date(year, month, day)
			print(validate_time)
			food_name = STT(mic, recognizer)
			task_register_OCR_food = asyncio.create_task(register_OCR_food(validate_time, food_name))
			futures_dic[f'register_OCR_{food_name}'] = task_register_OCR_food
			# register_OCR_food(validate_time, food_name)
					
		
					
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

#######################################################################
# socket
async def handle_echo(reader, writer):
	# global async_queue
	global signal_block
	while True:
		data = await reader.read(100)
		message = json.loads(data.decode())
		print(message['type'])
		addr = writer.get_extra_info('peername')
		
		
		power = await signal_block.get_power()
		if power==True:
			signal_flag = await signal_block.get_flag()
			if signal_flag == 0:
				await signal_block.signal_on()
				await signal_block.set_data(message)

		print(f"Received {message} from {addr}")

		"""
			print("Send: %s" % message)
			writer.write(data)
			await writer.drain()

			print("Close the connection")
			writer.close()
		"""
async def socket_task():
	server = await asyncio.start_server(
			handle_echo, '127.0.0.1', 56000)
	async with server:
		await server.serve_forever()
async def socket_task_wrapper():
	while True:
		try:
			await socket_task()
		except Exception as e:
			await asyncio.sleep(1)
######################################################################

######################################################################
# STT
def speak(text):
	tts = gTTS(text=text, lang='ko')
	
	tts_bytes = BytesIO()
	tts.write_to_fp(tts_bytes)
	tts_bytes.seek(0)
	
	# pygame.mixer.pre_init(24000)
	# pygame.mixer.init()
	pygame.mixer.music.load(tts_bytes)
	# pygame.mixer.music.set_volume(0.5)
	# pygame.mixer.music.play()
	while pygame.mixer.music.get_busy():
		pygame.time.Clock().tick(10)
def play_sound(sound):
	pygame.mixer.music.load(sound)
	pygame.mixer.music.play()
	# while pygame.mixer.music.get_busy():
	#	pygame.time.Clock().tick(10)
def STT(mic, recognizer):
	while True:
		play_sound(START_SOUND)

		with mic as source:
			audio = recognizer.listen(source, timeout=4, phrase_time_limit=4)		
		try:
			result = recognizer.recognize_google(audio, language='ko-KR')
			play_sound(REGISTER_SOUND)
			# speak('the food is '+result)
			print(result)
			return result
		except (sr.UnknownValueError, sr.WaitTimeoutError):
			print('repeat once')
		except sr.RequestError as e:
			print('server error')

######################################################################

######################################################################
# program
async def program():
	global signal_block

	# socket init need to port env
	socket_future = asyncio.create_task(socket_task_wrapper())
	await asyncio.sleep(1)

	while True:
		selected_mode = int(input("please select mode"))
		# QR/Valid Date mode : 1
		if selected_mode == 1:
			
			# register mode on
			await signal_block.power_on()
			
			camera_futures_dic = await camera_mode()
			if camera_futures_dic == -1:
				continue
			results = await asyncio.gather(*camera_futures_dic.values())
			print('**********************')
			for name, result in zip(camera_futures_dic.keys(), results):
				print(f'{name}: {result}')
			
			# register mode off
			await signal_block.power_off()
			
	
		# General mode : 2
		else:
			continue
	await socket_future		
if __name__ == "__main__":
	# load .env
	load_dotenv()	
	
	# camera_init
	picam2 = Picamera2()
	preview_config = picam2.create_preview_configuration(buffer_count=3)
	# capture_config = picam2.create_still_configuration(buffer_count=3)
	picam2.configure(preview_config)
	picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})
	
	# STT
	REGISTER_SOUND = './registered.wav'
	START_SOUND = './start.wav'
	pygame.mixer.pre_init(24000)
	pygame.mixer.init()
	pygame.mixer.music.set_volume(0.5)
	recognizer = sr.Recognizer()
	mic = sr.Microphone()

	# main program
	asyncio.run(program())
