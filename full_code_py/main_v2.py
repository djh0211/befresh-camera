from module.distance_module import distance_logic
from module.SignalBlock import SignalBlock
from module.mic import init_mic, speak, STT, play_sound, START_SOUND, REGISTER_SOUND
from module.register_food import register_QR_food, register_OCR_food, register_GENERAL_food

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
import pickle
from pathlib import Path
from pytz import timezone

# Camera
import cv2
from pyzbar.pyzbar import decode
from picamera2 import Picamera2, Preview
from libcamera import controls
import pytesseract

# Bluetooth
from bleak import BleakScanner, BleakClient
import struct



signal_block = SignalBlock()
bt_address_dic = set()
bluetooth_connect_task_queue = queue.Queue()
	
####################################################
# BT
def load_bt_address_file():
	file_path = './bt_address_file.pickle'
	if Path(file_path).is_file():
		with open(file_path, 'rb') as fr:
			return pickle.load(fr)
	return set()

def update_bt_address_file(bt_address):
	file_path = './bt_address_file.pickle'
	global bt_address_dic
	
	bt_address_dic.add(bt_address)
	with open(file_path, 'wb') as fw:
		bt_address_dic = pickle.dump(bt_address_dic, fw)

async def bluetooth_job_re_queue_in(bt_address):
	global bluetooth_connect_task_queue
	await asyncio.sleep(10)
	bluetooth_connect_task_queue.put(bt_address)
	

async def bluetooth_connect(bt_address):
	global bluetooth_connect_task_queue
	try:
		while True:
			p = random.random()
			if p<=0.5:
				raise Exception
			else:
				print(f'{bt_address} bluetooth connected')
			print(f'{bt_address} bluetooth data transfer')
			await asyncio.sleep(60)
			# data transfer
	except:
		print(f'{bt_address} bluetooth timeout')
		asyncio.create_task(bluetooth_job_re_queue_in(bt_address))
		return


async def bluetooth_connect_worker():
	global bluetooth_connect_task_queue
	while True:
		if bluetooth_connect_task_queue.empty():
			await asyncio.sleep(5)
			continue
		bt_address = bluetooth_connect_task_queue.get()
		asyncio.create_task(bluetooth_connect(bt_address))
		bluetooth_connect_task_queue.task_done()

#######################################################################
# camera/general
"""
async def bluetooth_connect(containerId):
	# print('hihi')
	while True:
		await asyncio.sleep(5)
		rand = random.random()
		if rand >= 0.5:
			print(f'{containerId} container bluetooth connected!!')
			return containerId 
		print(f'{containerId} retry again....')
"""

async def general_mode(dt):
	global signal_block
	# STT
	# there is no cancel, if timeout -> cancel
	#########################
	print("its general mode")
	food_name = STT(mic, recognizer)
	general_register_task = asyncio.create_task(register_GENERAL_food(food_name, dt))
	await signal_block.signal_off()
	return food_name, general_register_task

# QR/Valid Date mode
async def camera_mode():
	# global async_queue
	global signal_block
	global bluetooth_connect_task_queue 

	picam2.start_preview(Preview.QTGL)
	picam2.start()
	qr_history_set = set()
	futures_dic = {}
	distance_threshold = 20
	start = time.time()
	
	while True:
		signal_flag = await signal_block.get_flag()
		if signal_flag == 1:
			data_recv = await signal_block.get_data()
			print(data_recv)
			if data_recv['type'] == 'wakeword' and data_recv['payload'] == 'general_register':
				# turn to general mode
				queue_in_time = data_recv['time']
				print('its general mode!!!!!')
				print(data_recv)
				dt = datetime.now(timezone('Asia/Seoul'))
				food_name, general_register_task = await general_mode(dt)
				k = f'GENERAL_{dt}_{food_name}'
				futures_dic[k] = general_register_task
	

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
							bluetooth_connect_task_queue.put(containerId)
							update_bt_address_file(containerId)

							### task_bluetooth_connect = asyncio.create_task(bluetooth_connect(containerId))
							# food name STT
							food_name = STT(mic, recognizer)

							# async food register
							dt = datetime.now(timezone('Asia/Seoul'))
							task_register_food = asyncio.create_task(register_QR_food(containerId, food_name, dt))
							futures_dic[f'QR_{dt}_{food_name}_{containerId}'] = task_register_food
							
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
			
			year = int(str(datetime.today().year)[:2] + date_splitted[0][-2:])
			month = int(date_splitted[1])
			day = int(date_splitted[2][:2])
			
			validate_time = date(year, month, day)
			print(validate_time)
			food_name = STT(mic, recognizer)
			dt = datetime.now(timezone('Asia/Seoul'))
			task_register_OCR_food = asyncio.create_task(register_OCR_food(validate_time, food_name, dt))
			futures_dic[f'OCR_{dt}_{food_name}_{validate_time}'] = task_register_OCR_food
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
# program
async def program():
	global signal_block
	global bt_address_dic
	global bluetooth_connect_task_queue

	# socket init need to port env
	socket_future = asyncio.create_task(socket_task_wrapper())
	await asyncio.sleep(1)
	
	bt_address_dic = load_bt_address_file()
	print(bt_address_dic)
	bt_worker_task = asyncio.create_task(bluetooth_connect_worker())

	for bt_address in bt_address_dic:
		bluetooth_connect_task_queue.put(bt_address)

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
			while True:
				await asyncio.sleep(1)
	await socket_future		
if __name__ == "__main__":
	# load .env
	load_dotenv()	
	
	# camera_init
	picam2 = Picamera2()
	preview_config = picam2.create_preview_configuration(buffer_count=3)
	picam2.configure(preview_config)
	picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})
	
	# STT
	mic, recognizer = init_mic()
	# main program
	asyncio.run(program())
