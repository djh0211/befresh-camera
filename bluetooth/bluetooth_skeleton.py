import asyncio
from bleak import BleakScanner, BleakClient
import struct
import time
import random

import pickle
import os
from pathlib import Path
import queue

bt_address_list = ['1','2','3','4','5']
bt_address_set = set()
bluetooth_connect_task_queue = queue.Queue()
	

def load_bt_address_file():
	file_path = './bt_address_file.pickle'
	if Path(file_path).is_file():
		with open(file_path, 'rb') as fr:
			return pickle.load(fr)
	return {}

def update_bt_address_file(bt_address):
	file_path = './bt_address_file.pickle'
	global bt_address_set
	
	bt_address_set.add(bt_address)
	with open(file_path, 'wb') as fw:
		bt_address_set = pickle.dump(bt_address_set, fw)

async def bluetooth_job_re_queue_in(bt_address):
	global bluetooth_connect_task_queue
	await asyncio.sleep(10)
	bluetooth_connect_task_queue.put(bt_address)
	

async def bluetooth_connect(bt_address):
	global bluetooth_connect_task_queue
	prev_status = None
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
		
			

async def program():
	global bt_address_set
	global bluetooth_connect_task_queue
	
	bt_address_set = load_bt_address_file()
	print(bt_address_dic)
	bt_worker_task = asyncio.create_task(bluetooth_connect_worker())

	for bt_address in bt_address_set:
		bluetooth_connect_task_queue.put(bt_address)
	while True:
		asyncio.sleep(1)
	


if __name__ == "__main__":
	
	# main program
	asyncio.run(program())
