from module.distance_module import distance_logic
from module.SignalBlock import SignalBlock
from module.mic import init_mic, speak, STT, play_sound
from module.register_food import register_QR_food, register_OCR_food, register_GENERAL_food
from module.bluetooth_module_v2 import SensorDataFormat, typeMap, SensorDataKeys, load_bt_address_file, update_bt_address_file, bluetooth_job_re_queue_in, bluetooth_connect, bluetooth_process_worker, SensorDataBuffer, bluetooth_process_wrapper, bluetooth_process, set_sensor_data_message_signal, produce_sensor_data_message
# from module.bluetooth_module_v2 import SensorDataFormat, typeMap, SensorDataKeys, load_bt_address_file, update_bt_address_file, SensorDataBuffer

# GPIO
import RPi.GPIO as GPIO

import asyncio
import time
import logging
import numpy as np
import json
from operator import eq
import asyncio
from concurrent.futures import ThreadPoolExecutor
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



async def button():
	button_pin = 15

	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
	
	while 1:
		try:
			if GPIO.input(button_pin) == GPIO.HIGH:
				print('button pushed')
				return 1
			await asyncio.sleep(0.1)
		except Exception as e:
			print(f'button: {e}')
			return 0

async def camera_mode():
	print('camera on')
	await asyncio.sleep(10)
	print('camera off')

async def program():
	while True:
		
		# button wait
		is_clicked = await button()
		if is_clicked == 1:
			camera_futures_dic = await camera_mode()
		


if __name__ == "__main__":
	# load .env
	load_dotenv()
	
	# camera_init
	picam2 = Picamera2()
	preview_config = picam2.create_preview_configuration(buffer_count=3)
	picam2.configure(preview_config)
	picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})
	
	# STT
	mic, recognizer = init_mic()
	
	# main program
	asyncio.run(program())
