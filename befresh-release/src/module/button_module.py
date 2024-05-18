import RPi.GPIO as GPIO
import time
import asyncio


def exit_button(button_flag):	
	button_pin = 15

	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
	
	while 1:
		try:
			if GPIO.input(button_pin) == GPIO.HIGH:
				print('button pushed')
				button_flag.value = 1
				return
			time.sleep(0.05)
		except Exception as e:
			print(f'button: {e}')


async def start_button():
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
