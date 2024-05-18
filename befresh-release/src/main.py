from module.distance_module import distance_logic
from module.SignalBlock import SignalBlock
from module.mic import init_mic, STT, play_sound, ON_SOUND, OFF_SOUND
from module.register_food import register_QR_food, register_OCR_food, register_GENERAL_food
from module.bluetooth_module import update_bt_address_file, bluetooth_process_wrapper, bluetooth_process, set_sensor_data_message_signal
from module.button_module import start_button, exit_button

import asyncio
import time
import logging
import numpy as np
import json
from operator import eq
import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
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
from multiprocessing import Process, Manager, log_to_stderr, get_logger

# Scheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Camera
import cv2
from pyzbar.pyzbar import decode
from picamera2 import Picamera2, Preview
from libcamera import controls
import pytesseract

# Bluetooth
from bleak import BleakScanner, BleakClient
import struct

# Kafka
from kafka import KafkaProducer

def setup_logger():
    logger = log_to_stderr()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(levelname)s/%(processName)s] %(message)s')
    file_handler = logging.FileHandler('multiprocessing_logs.log')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


signal_block = SignalBlock()
	

#######################################################################
# camera/general


async def general_mode():
	global signal_block
	# STT
	# there is no cancel, if timeout -> cancel
	#########################
	print("its general mode")
	food_name = STT(mic, recognizer)
	if food_name == -1:
		return -1, None
	general_register_task = asyncio.create_task(register_GENERAL_food(food_name))
	return food_name, general_register_task

# QR/Valid Date mode
async def camera_mode(bt_address_dic, button_flag, bt_address_lookup_dic):
	global signal_block
	
	logger = get_logger()
	
	picam2.start_preview(Preview.QTGL)
	picam2.start()
	
	play_sound(ON_SOUND)
		
	# qr_history_set = set()
	futures_dic = {}
	distance_threshold = 50
	start = time.time()
	
	# replace by button click
	register_off_task = Process(target=exit_button, args=(button_flag,))
	register_off_task.start()
	
	await signal_block.signal_off()

	while True:
		
		"""
		# calculate distance
		distance_task = asyncio.create_task(distance_logic())
		"""
		# replaced by button click

		signal_flag = signal_block.get_flag()
		if signal_flag == 1:
				print('its general mode!!!!!')
				food_name, general_register_task = await general_mode()
				if food_name!=-1 and general_register_task is not None:	
					k = f'GENERAL_{food_name}'
					futures_dic[k] = general_register_task
		await signal_block.signal_off()

		array = picam2.capture_array()

		qr_list = decode(array)
		
		
		# qr_logic
		if qr_list:
			for qr in qr_list:
				try:
					if eq(qr.type,'QRCODE'):
						string_data = qr.data.decode('utf-8')
						data = json.loads(string_data)
						if 'bt_address' in data:
							print(f'bt_address: {data}')
							bt_address = data['bt_address']
							
							bt_address_lookup_dic[bt_address] = True
							update_bt_address_file(bt_address_dic, bt_address)

							# food name STT
							food_name = STT(mic, recognizer)

							# async food register
							task_register_food = asyncio.create_task(register_QR_food(bt_address, food_name))
							futures_dic[f'QR_{food_name}_{bt_address}'] = task_register_food
							
				except Exception as e:
					print(e)
		# ocr logic
		rgb_image = cv2.cvtColor(array, cv2.COLOR_BGR2RGB)
		custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789.'
		text = pytesseract.image_to_string(rgb_image, config=custom_config)
		date_pattern = r'\d{2,}\.\d{1,}\.\d{1,}'
		dates = re.findall(date_pattern, text)
		
		if dates:
			delimeter = '.'
			status = True
			try:
				date_splitted = dates[0].split(delimeter)
				print(date_splitted)
				year = int(str(datetime.today().year)[:2] + date_splitted[0][-2:])
				month = int(date_splitted[1])
				temp_day = re.findall(r'\d+', date_splitted[2])[0]
				day = int(temp_day[:2])
			except Exception as e:
				print(e)
				status = False
			if status:
				try:
					validate_time = date(year, month, day).strftime('%Y-%m-%d')
					print(validate_time)
					food_name = STT(mic, recognizer)
					task_register_OCR_food = asyncio.create_task(register_OCR_food(validate_time, food_name))
					futures_dic[f'OCR_{food_name}_{validate_time}'] = task_register_OCR_food
				except:
					pass
		
		
		"""
		# calculated distance gather -> logic		
		distance = await distance_task
		print(distance)

		if distance == -1:
			# distance error ignore once
			continue
		# print(f'distance: {distance} cm')
		if distance < distance_threshold:
			start = time.time()
			continue
		# have to change time threshold
		elif time.time() - start >= 15:
			# no action now -> register all
			picam2.stop_preview()
			picam2.stop()
			break
		"""
		# replaced by button click
		# is_clicked = await register_off_task
		if button_flag.value == 1:
			picam2.stop_preview()
			picam2.stop()
			button_flag.value = 0

			break
		
		await asyncio.sleep(0.5)

	play_sound(OFF_SOUND)
	return futures_dic

#######################################################################
# socket
async def handle_echo(reader, writer):
	global signal_block
	data = await reader.read(100)
	message = data.decode()
	addr = writer.get_extra_info('peername')
	
	
	if data:
		print(f"Received {message} from {addr}")
		await signal_block.signal_on()

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
# kafka job



######################################################################
# program
async def program():
	global signal_block
	
	load_dotenv()
	REFRIGERATOR_ID = int(os.getenv('REFRIGERATOR_ID'))
	KAFKA_SERVER = os.getenv('KAFKA_SERVER')
	
	# socket init need to port env
	socket_future = asyncio.create_task(socket_task_wrapper())
	
	# bluetooth, sensor data
	with Manager() as manager:
		sensor_flag = manager.Value('i', 0)
		button_flag = manager.Value('i', 0)
		bt_address_dic = manager.list()
		bt_address_lookup_dic = manager.dict()

		bluetooth_process_wrapper(sensor_flag, bt_address_dic, bt_address_lookup_dic)


		scheduler = AsyncIOScheduler()
		scheduler.add_job(set_sensor_data_message_signal, 'interval', minutes=30, args=[sensor_flag])

		scheduler.start()

		while True:
			# camera_mode on waiting...
			is_clicked = await start_button()
			if is_clicked == 1:
				# register mode on
				
				camera_futures_dic = await camera_mode(bt_address_dic, button_flag, bt_address_lookup_dic)
				if camera_futures_dic == -1:
					continue
				results = await asyncio.gather(*camera_futures_dic.values())
				print('**********************')
				for name, result in zip(camera_futures_dic.keys(), results):
					print(f'{name}: {result}')
				
				data_box = {
					'refrigeratorId': REFRIGERATOR_ID,
					'foodList': results
				}
			
				
				producer = KafkaProducer(
					bootstrap_servers=[KAFKA_SERVER],
					value_serializer=lambda x:json.dumps(x).encode('utf-8'),
					retries=3
				)
				producer.send('food-regist', value=data_box)
											

			# General mode : 2
			else:
				while True:
					await asyncio.sleep(20)
		await socket_future		
if __name__ == "__main__":
	# load .env
	load_dotenv()
	setup_logger()	
	
	# camera_init
	picam2 = Picamera2()
	preview_config = picam2.create_preview_configuration(buffer_count=3)
	picam2.configure(preview_config)
	picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})
	
	# STT
	mic, recognizer = init_mic()
	
	# main program
	asyncio.run(program())
