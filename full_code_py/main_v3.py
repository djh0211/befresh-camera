from module.distance_module import distance_logic
from module.SignalBlock import SignalBlock
from module.mic import init_mic, speak, STT, play_sound
from module.register_food import register_QR_food, register_OCR_food, register_GENERAL_food
from module.bluetooth_module_v2 import SensorDataFormat, typeMap, SensorDataKeys, load_bt_address_file, update_bt_address_file, bluetooth_job_re_queue_in, bluetooth_connect, bluetooth_process_worker, SensorDataBuffer, bluetooth_process_wrapper, bluetooth_process, set_sensor_data_message_signal, produce_sensor_data_message
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
    # 로그 레벨 설정
    logger = log_to_stderr()
    logger.setLevel(logging.INFO)
    # 로그 포맷 설정
    formatter = logging.Formatter('[%(levelname)s/%(processName)s] %(message)s')
    # 로그를 파일에 출력하기 위한 핸들러 설정
    file_handler = logging.FileHandler('multiprocessing_logs.log')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


signal_block = SignalBlock()
	
####################################################
# BT

"""

"""
#######################################################################
# camera/general


async def general_mode():
	global signal_block
	# STT
	# there is no cancel, if timeout -> cancel
	#########################
	print("its general mode")
	food_name = STT(mic, recognizer)
	print(food_name)
	if food_name == -1:
		await signal_block.signal_off()
		return -1, None
	general_register_task = asyncio.create_task(register_GENERAL_food(food_name))
	await signal_block.signal_off()
	return food_name, general_register_task

# QR/Valid Date mode
async def camera_mode(bluetooth_connect_task_queue, bt_address_dic, button_flag):
	global signal_block
	
	logger = get_logger()
	
	picam2.start_preview(Preview.QTGL)
	picam2.start()
	# qr_history_set = set()
	futures_dic = {}
	distance_threshold = 50
	start = time.time()
	
	# replace by button click
	register_off_task = Process(target=exit_button, args=(button_flag,))
	register_off_task.start()
	while True:
		
		"""
		# calculate distance
		distance_task = asyncio.create_task(distance_logic())
		"""
		# replace by button click

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
				if general_register_task is None:
					print('yeah its right')
					continue
				k = f'GENERAL_{food_name}'
				futures_dic[k] = general_register_task
	

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
							# qr_history_set.add(string_data)
							bt_address = data['bt_address']
							# async bluetooth connect
							### future_bluetooth = loop.run_in_executor(executor, bluetooth_connect, containerId)
							
							
							bluetooth_connect_task_queue.put(bt_address)
							update_bt_address_file(bt_address_dic, bt_address)
							

							### task_bluetooth_connect = asyncio.create_task(bluetooth_connect(containerId))
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
# kafka job

async def produce_register_message():
	pass


######################################################################
# program
async def program():
	global signal_block
	
	# socket init need to port env
	socket_future = asyncio.create_task(socket_task_wrapper())
	
	# bluetooth, sensor data
	with Manager() as manager:
		bluetooth_connect_task_queue = manager.Queue()
		sensor_flag = manager.Value('i', 0)
		button_flag = manager.Value('i', 0)
		bt_address_dic = manager.list()

		bluetooth_process_wrapper(bluetooth_connect_task_queue, sensor_flag, bt_address_dic)

		scheduler = AsyncIOScheduler()
		scheduler.add_job(set_sensor_data_message_signal, 'interval', minutes=30, args=[sensor_flag])

		scheduler.start()

		while True:
			# camera_mode on waiting...
			is_clicked = await start_button()
			if is_clicked == 1:
				# register mode on
				await signal_block.power_on()
				
				camera_futures_dic = await camera_mode(bluetooth_connect_task_queue, bt_address_dic, button_flag)
				if camera_futures_dic == -1:
					continue
				results = await asyncio.gather(*camera_futures_dic.values())
				print('**********************')
				for name, result in zip(camera_futures_dic.keys(), results):
					print(f'{name}: {result}')
				
				data_box = {
					'refrigeratorId': 100,
					'foodList': results
				}
			
				
				producer = KafkaProducer(
					bootstrap_servers=['k10a307.p.ssafy.io:9092'], # 전달하고자 하는 카프카 브로커의 주소 리스트
					value_serializer=lambda x:json.dumps(x).encode('utf-8'), # 메시지의 값 직렬화
					retries=3
				)
				producer.send('food-regist', value=data_box)
							
				# register mode off
				await signal_block.power_off()
				

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
