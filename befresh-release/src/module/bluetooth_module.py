# Bluetooth
from bleak import BleakScanner, BleakClient
from bleak.exc import BleakError
import struct

import copy
import pickle
import time
from pathlib import Path
import asyncio
import random
from datetime import datetime
from dotenv import load_dotenv
import os
from multiprocessing import Process, Manager, log_to_stderr, get_logger
from pytz import timezone
import json

from kafka import KafkaProducer


##########################################################
SensorDataFormat = {
    'temperature':
    {
      'uuid': '19b10000-2001-537e-4f6c-d104768a1214',
      'structure': ['Float32']
    },
    'humidity':
    {
      'uuid': '19b10000-3001-537e-4f6c-d104768a1214',
      'structure': ['Uint8']
    },
    'pressure':
    {
      'uuid': '19b10000-4001-537e-4f6c-d104768a1214',
      'structure': ['Float32']
	},
    'co2':
    {
      'uuid': '19b10000-9002-537e-4f6c-d104768a1214',
      'structure': ['Uint32']
    },
    'gas':
    {
      'uuid': '19b10000-9003-537e-4f6c-d104768a1214',
      'structure': ['Uint32']
    },
    'nh3':
    {
      'uuid': '19b10000-9004-537e-4f6c-d104768a1214',
      'structure': ['Uint32']
    },
}

typeMap = {
    "Uint8": {'type' : 'B', 'size': 1},
    "Uint16": {'type' : 'H', 'size': 2},
    "Uint32": {'type' : 'I', 'size': 4},
    "Int16": {'type' : 'h', 'size': 2},
    "Float32": {'type' : 'f', 'size': 4}
}

SensorDataKeys = SensorDataFormat.keys()
##########################################################

class NoMatchingBTDeviceException(Exception):
	pass
	
class BTDisconnectException(Exception):
	pass

class BTMaxTryFailException(Exception):
	pass
	
class SensorDataBuffer:
	def __init__(self,):
		self.lock = asyncio.Lock()
		self.data = {}
	
	async def append_data(self, bt_address, data):
		async with self.lock:
			if bt_address not in self.data:
				self.data[bt_address] = []
			self.data[bt_address].append(data)
	async def update_file(self, ):
		async with self.lock:
			file_path = '/home/pi/dev/befresh-release/src/sensor_data_buffer.pickle'
			with open(file_path, 'wb') as fw:
				pickle.dump(self.data, fw)
	async def load_file(self, ):
		async with self.lock:
			file_path = '/home/pi/dev/befresh-release/src/sensor_data_buffer.pickle'
			if Path(file_path).is_file():
				with open(file_path, 'rb') as fr:
					self.data = pickle.load(fr)
	async def copy_and_delete(self, ):
		async with self.lock:
			copied = copy.deepcopy(self.data)
			self.data = {}
			return copied


async def bluetooth_connect_over_10(bt_address, sensor_data_buffer, bt_address_lookup_dic):
	logger = get_logger()
	logger.info(f"{bt_address} function in")

	while True:
		try:
			async with BleakClient(bt_address) as client:
				if await client.is_connected():
					print(f"Connected to {bt_address}")
					services = client.services
					tempData = {
						'time': time.strftime('%Y-%m-%d %H:%M'),
						'data': {}
					}
					for service in services:
						for characteristic in service.characteristics:
							for sense in SensorDataKeys:
								if characteristic.uuid == SensorDataFormat[sense]['uuid']:
									if 'read' in characteristic.properties:
										read_data = await client.read_gatt_char(characteristic)
										data_types = SensorDataFormat[sense]['structure']
										values = []
										offset = 0
										for data_type in data_types:
											value, = struct.unpack_from(typeMap[data_type]['type'], read_data)
											values.append(value)
											offset += typeMap[data_type]['size']
										tempData['data'][sense] = values[0]
					logger.info(f'{bt_address}: {tempData}')

					await sensor_data_buffer.append_data(bt_address, tempData)
					await sensor_data_buffer.update_file()
					return 1
		except BleakError as e:
			if 'was not found' in str(e):
				print('failed to find device')
				bt_address_lookup_dic[bt_address] = False
			else:
				print('connect fail')
		except Exception as e:
			logger.info(f'{bt_address} : failed by other reason')

async def bluetooth_connect_under_10(bt_address, sensor_data_buffer, bt_address_lookup_dic):
	logger = get_logger()
	failed_to_find = 0
	while True:
		logger.info(f"{bt_address} function in")
		keys = list(bt_address_lookup_dic.keys())
		n = len(keys)
		if n >= 10:
			# change mode to over_10
			return -1
		if failed_to_find >= 3:
			bt_address_lookup_dic[bt_address] = False
		try:
			async with BleakClient(bt_address) as client:
				if await client.is_connected():
					print(f"Connected to {bt_address}")
					services = client.services
					tempData = {
						'time': time.strftime('%Y-%m-%d %H:%M'),
						'data': {}
					}
					for service in services:
						for characteristic in service.characteristics:
							for sense in SensorDataKeys:
								if characteristic.uuid == SensorDataFormat[sense]['uuid']:
									if 'read' in characteristic.properties:
										read_data = await client.read_gatt_char(characteristic)
										data_types = SensorDataFormat[sense]['structure']
										values = []
										offset = 0
										for data_type in data_types:
											value, = struct.unpack_from(typeMap[data_type]['type'], read_data)
											values.append(value)
											offset += typeMap[data_type]['size']
										tempData['data'][sense] = values[0]
					logger.info(f'{bt_address}: {tempData}')

					await sensor_data_buffer.append_data(bt_address, tempData)
					await sensor_data_buffer.update_file()
					return 1
		except BleakError as e:
			if 'was not found' in str(e):
				print('failed to find device')
				failed_to_find += 1
			else:
				print('connect fail')
		except Exception as e:
			logger.info(f'{bt_address} : failed by other reason')

					


async def bluetooth_process_worker(sensor_flag, bt_address_dic, bt_address_lookup_dic):
	logger = get_logger()
	logger.info("worker in")

	# connect, data transfer time check
	time_list = []

	# load sensor data
	sensor_data_buffer = SensorDataBuffer()
	await sensor_data_buffer.load_file()
	# load bt file
	load_bt_address_file(bt_address_dic)
	for bt_address in bt_address_dic:
		bt_address_lookup_dic[bt_address] = True # if True -> in latest job it connected. so it should be go on

	asyncio.create_task(produce_sensor_data_message(sensor_data_buffer, sensor_flag))

	idx_cursor = 0
	while True:		
		# default transfer schedule is 10min, and max-data-transfer time is 60sec
		# so, if n<10 then it could be over request -> so we have to divide by time
		# if n>=10 then it have to be timed out
		keys = list(bt_address_lookup_dic.keys())
		n = len(keys)
		timeout = 600
		try:
			timeout = int(600/n)
		except:
			pass
		if n == 0:
			await asyncio.sleep(10)
			continue
		try:
			idx_cursor %= n
		except:
			pass
		bt_address = keys[idx_cursor]
		if bt_address_lookup_dic[bt_address] == False:
			# latest -> failed to find -> pass once
			bt_address_lookup_dic[bt_address] = True
			idx_cursor += 1
			continue
		
		if n<10:
			# 10/n min timeout
			try:
				start = time.time()
				result = await asyncio.wait_for(bluetooth_connect_under_10(bt_address, sensor_data_buffer, bt_address_lookup_dic), timeout=timeout)
				if result == 1:
					# successed
					print('sleep...')
					while True:
						now = time.time()
						if now - start >= timeout:
							# go to next
							idx_cursor += 1
							break
						await asyncio.sleep(2)
				elif result == -1:
					# have to change mode
					continue			
			except asyncio.TimeoutError:
				idx_cursor += 1
				pass
			print('wake up!!')
		else:
			# 60sec timeout
			try:
				start = time.time()
				result = await asyncio.wait_for(bluetooth_connect_over_10(bt_address, sensor_data_buffer, bt_address_lookup_dic), timeout=60)
				if result == 1:
					# successed
					while True:
						now = time.time()
						if now - start >= int(10/n):
							# go to next
							idx_cursor += 1
							break
						await asyncio.sleep(2)
			except asyncio.TimeoutError:
				idx_cursor += 1
				pass

		
    


def bluetooth_process(sensor_flag, bt_address_dic, bt_address_lookup_dic):
    logger = get_logger()
    logger.info("process in")
    asyncio.run(bluetooth_process_worker(sensor_flag, bt_address_dic, bt_address_lookup_dic))
       

def bluetooth_process_wrapper(sensor_flag, bt_address_dic, bt_address_lookup_dic):
    logger = get_logger()
    logger.info("wrapper in")
    p = Process(target=bluetooth_process, args=(sensor_flag, bt_address_dic, bt_address_lookup_dic, ))
    p.start()
    # p.join()	



##########################################################
def load_bt_address_file(bt_address_dic):
	file_path = '/home/pi/dev/befresh-release/src/bt_address_file.pickle'
	if Path(file_path).is_file():
		with open(file_path, 'rb') as fr:
			temp = pickle.load(fr)
			for k in temp:
			      bt_address_dic.append(k)
	else:
		bt_address_dic[:] = []

def update_bt_address_file(bt_address_dic, bt_address):
	file_path = '/home/pi/dev/befresh-release/src/bt_address_file.pickle'
	if bt_address not in bt_address_dic:
	  bt_address_dic.append(bt_address)
	with open(file_path, 'wb') as fw:
		pickle.dump(list(bt_address_dic), fw)
		
############################################################
async def set_sensor_data_message_signal(sensor_flag):
	logger = get_logger()	

	sensor_flag.value = 1
	logger.info(sensor_flag.value)
async def produce_sensor_data_message(sensor_data_buffer, sensor_flag):
	load_dotenv()
	KAFKA_SERVER = os.getenv('KAFKA_SERVER')
	REFRIGERATOR_ID = int(os.getenv('REFRIGERATOR_ID'))

	logger = get_logger()
	producer = KafkaProducer(
		bootstrap_servers=[KAFKA_SERVER],
		value_serializer=lambda x:json.dumps(x).encode('utf-8'), 
		retries=3
	)
	
	while True:
		# logger.info(f'im here 2 {sensor_flag.value}')	

		if sensor_flag.value == 1:	
			dt = datetime.now(timezone('Asia/Seoul')).strftime('%Y-%m-%d')
			data = await sensor_data_buffer.copy_and_delete()
			# logger.info(f'im here 3 {data}')	

			await sensor_data_buffer.update_file()
			if len(data.keys()) > 0:
				payload = {
					'execute_time' : dt,
					'refrigeratorId' : REFRIGERATOR_ID,
					'data' : data
				}
				try:
					logger.info(f'run task!!! {payload}')
					producer.send('sensor-data-topic', value=payload)

				except Exception as e:
					logger.info(f'failed run task {e}')
			sensor_flag.value = 0
		await asyncio.sleep(5)

