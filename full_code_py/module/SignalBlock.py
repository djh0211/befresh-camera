import time
import numpy as np
import json
import asyncio
import os

# signal
class SignalBlock:
	def __init__(self, initial_value=0):
		self.lock = asyncio.Lock()
		self.flag = initial_value
		self.power = False
		self.data = None
	
	async def signal_on(self):
		async with self.lock:
			self.flag = 1
	async def signal_off(self):
		async with self.lock:
			self.flag = 0
			self.data = None
	async def get_flag(self):
		async with self.lock:
			return self.flag
			
	async def power_on(self):
		async with self.lock:
			self.power = True
	async def power_off(self):
		async with self.lock:
			self.power = False
	async def get_power(self):
		async with self.lock:
			return self.power
			
	async def set_data(self, data):
		async with self.lock:
			self.data = data
	async def get_data(self):
		async with self.lock:
			data = self.data
			self.data = None
			return data
