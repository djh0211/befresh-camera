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
	
	async def signal_on(self):
		async with self.lock:
			self.flag = 1
	async def signal_off(self):
		async with self.lock:
			self.flag = 0
	def get_flag(self):
		return self.flag

