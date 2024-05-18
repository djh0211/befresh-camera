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

async def send_data(data, attempt=1, max_attempts=3):
	try:
		reader, writer = await asyncio.open_connection('127.0.0.1', 56000)
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
						
	while True:
		pcm = audio_stream.read(porcupine.frame_length)
		pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
		keyword_index = porcupine.process(pcm)
		
		if keyword_index == 0:
			data = '1'
			print(f'Send: {data!r}')
			await send_data(data)





if __name__ == "__main__":
	# load .env
	load_dotenv()
	PORCUPINE_KEY = os.getenv('PORCUPINE_KEY')
	KEYWORD_PATH = os.getenv('PORCUPINE_KEYWORD_PATH')
	MODEL_PATH = os.getenv('PORCUPINE_MODEL_PATH')
	

	asyncio.run(main())


	
