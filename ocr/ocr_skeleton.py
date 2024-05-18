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
import asyncio
import json

# IoT
import RPi.GPIO as gpio

# Camera
import cv2
from pyzbar.pyzbar import decode
from picamera2 import Picamera2, Preview
from libcamera import controls

# ocr
import pytesseract
from PIL import Image
import cv2
import pandas as pd
import re


"""
path = './captured.jpg'
image = cv2.imread(path)
rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
text = pytesseract.image_to_string(rgb_image, lang="eng+kor")
print(text)
"""


"""
"""
# camera_init
picam2 = Picamera2()
preview_config = picam2.create_preview_configuration(buffer_count=3)
capture_config = picam2.create_still_configuration(buffer_count=3)

picam2.configure(preview_config)
picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})


picam2.start_preview(Preview.QTGL)
picam2.start()
print(preview_config['main'])


"""
"""
while True:
	# time.sleep(3)
	# MM.DD.YYYY.
	# YYYY.MM.DD
	# DEC.31.2022
	# DD.MM.YY.
	
	array = picam2.capture_array()
	array = cv2.cvtColor(array, cv2.COLOR_BGR2RGB)
	
	array = cv2.fastNlMeansDenoisingColored(array, None, 10, 10, 7, 21)
	
	custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789.'
	text = pytesseract.image_to_string(array, lang='kor', config=custom_config)
	date_pattern = r'\d{2,}\.\d{1,}\.\d{1,}'
	# dates = re.findall(date_pattern, text)
	print(text)
	
	# picam2.switch_mode_and_capture_file(preview_config, './captured.jpg')



	
picam2.stop_preview()
picam2.stop()



