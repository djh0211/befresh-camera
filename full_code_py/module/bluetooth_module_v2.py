# Bluetooth
from bleak import BleakScanner, BleakClient
import struct

import copy
import pickle
import time
from pathlib import Path
import asyncio
import random
from datetime import datetime

from multiprocessing import Process, Manager, log_to_stderr, get_logger

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
			file_path = './sensor_data_buffer.pickle'
			with open(file_path, 'wb') as fw:
				pickle.dump(self.data, fw)
	async def load_file(self, ):
		async with self.lock:
			file_path = './sensor_data_buffer.pickle'
			if Path(file_path).is_file():
				with open(file_path, 'rb') as fr:
					self.data = pickle.load(fr)
	async def copy_and_delete(self, ):
		async with self.lock:
			copied = copy.deepcopy(self.data)
			self.data = {}
			return copied


async def bluetooth_job_re_queue_in(bluetooth_connect_task_queue, bt_address, time):
	await asyncio.sleep(time)
	bluetooth_connect_task_queue.put(bt_address)



async def bluetooth_connect(bt_address, sensor_data_buffer):
	logger = get_logger()
	logger.info(f"{bt_address} function in")

	failed = 0
	while True:
		if failed>3:
			return False
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
					return True
		except Exception as e:
			logger.info(f'{bt_address} : failed : {e}')
			failed += 1




async def bluetooth_process_worker(bluetooth_connect_task_queue, sensor_flag, bt_address_dic):
	logger = get_logger()
	logger.info("worker in")
	
	# connect, data transfer time check
	time_list = []

	# load sensor data
	sensor_data_buffer = SensorDataBuffer()
	await sensor_data_buffer.load_file()
	# load bt file
	load_bt_address_file(bt_address_dic)
	logger.info(bt_address_dic)
	for bt_address in bt_address_dic:
		bluetooth_connect_task_queue.put(bt_address)
	# worker start
	# bt_worker_task = asyncio.create_task(bluetooth_connect_worker(bluetooth_connect_task_queue, sensor_data_buffer, ble_lock))

	asyncio.create_task(produce_sensor_data_message(sensor_data_buffer, sensor_flag))

	while True:
		if bluetooth_connect_task_queue.empty():
			await asyncio.sleep(10)
		# not empty
		bt_address = bluetooth_connect_task_queue.get()
		start = time.time()
		result = await bluetooth_connect(bt_address, sensor_data_buffer)
		end = time.time()
		
		# append and out
		time_list.append([result ,end-start])
		p = './time_history.pickle'
		with open(p, 'wb') as fw:
		  pickle.dump(time_list, fw)
		
		logger.info(f'bt --> {result}, {end-start}')
		if result:
			asyncio.create_task(bluetooth_job_re_queue_in(bluetooth_connect_task_queue, bt_address, 3))
		else:
			asyncio.create_task(bluetooth_job_re_queue_in(bluetooth_connect_task_queue, bt_address, 3))
    


def bluetooth_process(bluetooth_connect_task_queue, sensor_flag, bt_address_dic):
    logger = get_logger()
    logger.info("process in")
    asyncio.run(bluetooth_process_worker(bluetooth_connect_task_queue, sensor_flag, bt_address_dic))
       

def bluetooth_process_wrapper(bluetooth_connect_task_queue, sensor_flag, bt_address_dic):
    logger = get_logger()
    logger.info("wrapper in")
    p = Process(target=bluetooth_process, args=(bluetooth_connect_task_queue, sensor_flag, bt_address_dic,))
    p.start()
    # p.join()	



##########################################################
def load_bt_address_file(bt_address_dic):
	file_path = './bt_address_file.pickle'
	if Path(file_path).is_file():
		with open(file_path, 'rb') as fr:
			temp = pickle.load(fr)
			for k in temp:
			      bt_address_dic.append(k)
	else:
		bt_address_dic[:] = []

def update_bt_address_file(bt_address_dic, bt_address):
	file_path = './bt_address_file.pickle'
	if bt_address not in bt_address_dic:
	  bt_address_dic.append(bt_address)
	with open(file_path, 'wb') as fw:
		pickle.dump(list(bt_address_dic), fw)
		
############################################################
async def set_sensor_data_message_signal(sensor_flag):
	logger = get_logger()	
	logger.info('hihi')

	sensor_flag.value = 1
	logger.info(sensor_flag.value)
async def produce_sensor_data_message(sensor_data_buffer, sensor_flag):
	# global producer
	logger = get_logger()
	# logger.info('im here 1')	
	producer = KafkaProducer(
		bootstrap_servers=['k10a307.p.ssafy.io:9092'], # 전달하고자 하는 카프카 브로커의 주소 리스트
		value_serializer=lambda x:json.dumps(x).encode('utf-8'), # 메시지의 값 직렬화
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
					'refrigeratorId' : 100,
					'data' : data
				}
				try:
					logger.info(f'run task!!! {payload}')
					producer.send('sensor-data-topic', value=payload)

				except:
					print('failed run task')
					logger.info('failed run task')
			sensor_flag.value = 0
		await asyncio.sleep(5)

