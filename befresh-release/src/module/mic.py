# stt
from gtts import gTTS
from io import BytesIO
import pyaudio
import wave
import speech_recognition as sr
import pygame

REGIST_SOUND = '/home/pi/dev/befresh-release/src/correct.wav'
START_SOUND = '/home/pi/dev/befresh-release/src/start.wav'
ON_SOUND = '/home/pi/dev/befresh-release/src/on.wav'
OFF_SOUND = '/home/pi/dev/befresh-release/src/off.wav'

def play_sound(sound):
	pygame.mixer.music.load(sound)
	pygame.mixer.music.play()

def STT(mic, recognizer):
	try_cnt = 0
	while True:
		play_sound(START_SOUND)
		if try_cnt>=3:
			return -1
		try:
			with mic as source:
				audio = recognizer.listen(source, timeout=3, phrase_time_limit=3)
			result = recognizer.recognize_google(audio, language='ko-KR')
			play_sound(REGIST_SOUND)
			# speak('the food is '+result)
			print(result)
			return result
		except:
			print('repeat once')
			try_cnt += 1
def init_mic():
	# STT
	pygame.mixer.pre_init(24000)
	pygame.mixer.init()
	pygame.mixer.music.set_volume(0.5)
	recognizer = sr.Recognizer()
	mic = sr.Microphone()
	return mic, recognizer

