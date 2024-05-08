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

async def bluetooth_connect(bluetooth_connect_task_queue, bt_address, sensor_data_buffer):
	temp = 0
	not_found = 0
	print(f'{bt_address} in')
	print(SensorDataKeys)
	while True:
		print(1)
		try:
			if temp>=5 or not_found>=3:
				# connect Fail -> have to schedule later
				raise BTMaxTryFailException()
		except BTMaxTryFailException:
			print('why')
			asyncio.create_task(bluetooth_job_re_queue_in(bluetooth_connect_task_queue, bt_address))
			return
		print(2)
		try:
			# Search devices list
			devices = await BleakScanner.discover(timeout=20)
			for d in devices:
				if d.address == bt_address:
					await asyncio.sleep(2)
					client = BleakClient(d, timeout=60)
					try:
						await client.connect()
						while client.is_connected:
							print(f'{bt_address} connect')

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
							print(f'{bt_address}: {tempData}')
							await sensor_data_buffer.append_data(bt_address, tempData)
							await sensor_data_buffer.update_file()
							await asyncio.sleep(30)
					except Exception as e:
						print(e)
						# disconnected
						try:
							print(f'{bt_address} disconnect')
							temp += 1
							await client.disconnect()
						except:
							pass
			else:
				# No matching device
				raise NoMatchingBTDeviceException('No matching BT Device')
		except NoMatchingBTDeviceException:
			not_found += 1
			continue
		except Exception as e:
			print(f'Exception caused in searching BT devices: {e}')
			not_found += 1
			continue



##########################################################
def load_bt_address_file():
	file_path = './bt_address_file.pickle'
	if Path(file_path).is_file():
		with open(file_path, 'rb') as fr:
			return pickle.load(fr)
	return set()

def update_bt_address_file(bt_address_dic, bt_address):
	file_path = './bt_address_file.pickle'
	
	bt_address_dic.add(bt_address)
	with open(file_path, 'wb') as fw:
		bt_address_dic = pickle.dump(bt_address_dic, fw)

async def bluetooth_job_re_queue_in(bluetooth_connect_task_queue, bt_address):
	await asyncio.sleep(10)
	bluetooth_connect_task_queue.put(bt_address)
	

async def bluetooth_connect_worker(bluetooth_connect_task_queue, sensor_data_buffer):
	while True:
		if bluetooth_connect_task_queue.empty():
			await asyncio.sleep(5)
			continue
		bt_address = bluetooth_connect_task_queue.get()
		asyncio.create_task(bluetooth_connect(bluetooth_connect_task_queue, bt_address, sensor_data_buffer))
		bluetooth_connect_task_queue.task_done()
		
		

