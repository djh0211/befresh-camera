import asyncio
import time
import logging
from operator import eq
from dotenv import load_dotenv
import os
import json

# IPC
import socket
import threading

# Audio
import struct
import pyaudio
import pvporcupine

# have to change logic trycount -> forever
async def send_data(data, attempt=1, max_attempts=3):
	try:
		reader, writer = await asyncio.open_connection('127.0.0.1', 56000)

		data = json.dumps(data)
		writer.write(data.encode())
		await writer.drain()
		writer.close()
		await writer.wait_closed()
	except (ConnectionError, OSError) as e:
		print(e)
		if attempt <= max_attempts:
			print(f"Attempt {attempt} failed, retrying...")
			await asyncio.sleep(1)
			await send_data(data, attempt + 1, max_attempts)
		else:
			print("Max attempts reached, giving up.")

async def main():
	# audio_init
	porcupine = pvporcupine.create(
		access_key=PORCUPINE_KEY,
		keyword_paths=[KEYWORD_PATH],
		model_path=MODEL_PATH
	)
	pa = pyaudio.PyAudio()
	audio_stream = pa.open(
						rate=porcupine.sample_rate,
						channels=1,
						format=pyaudio.paInt16,
						input=True,
						frames_per_buffer=porcupine.frame_length)
						
	prev_timestamp = None
	# reader, writer = await asyncio.open_connection(
	# 	'127.0.0.1', 56000)
	while True:
		pcm = audio_stream.read(porcupine.frame_length)
		pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
		keyword_index = porcupine.process(pcm)
		
		if keyword_index == 0:
			now = time.time()
			if prev_timestamp is None or now - prev_timestamp >= 3:
				# to avoid redundant call
				prev_timestamp = now
				data = {}
				data['type'] = 'wakeword'
				data['payload'] = 'general_register'
				data['time'] = time.time()
				print(f'Send: {data!r}')
				await send_data(data)
				# writer.write(json.dumps(data).encode('utf-8'))
				# await writer.drain()

		"""
		print('Close the connection')
		writer.close()
		await writer.wait_closed()
		"""


if __name__ == "__main__":
	# load .env
	load_dotenv()
	PORCUPINE_KEY = os.getenv('porcupine_key')
	KEYWORD_PATH = os.getenv('porcupine_keyword_path')
	MODEL_PATH = os.getenv('porcupine_model_path')

	asyncio.run(main())


	
