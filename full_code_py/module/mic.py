# stt
from gtts import gTTS
from io import BytesIO
import pyaudio
import wave
import speech_recognition as sr
import pygame

REGIST_SOUND = './correct.wav'
START_SOUND = './start.wav'

def speak(text):
	tts = gTTS(text=text, lang='ko')
	
	tts_bytes = BytesIO()
	tts.write_to_fp(tts_bytes)
	tts_bytes.seek(0)
	
	# pygame.mixer.pre_init(24000)
	# pygame.mixer.init()
	pygame.mixer.music.load(tts_bytes)
	# pygame.mixer.music.set_volume(0.5)
	# pygame.mixer.music.play()
	while pygame.mixer.music.get_busy():
		pygame.time.Clock().tick(10)
def play_sound(sound):
	pygame.mixer.music.load(sound)
	pygame.mixer.music.play()
	# while pygame.mixer.music.get_busy():
	#	pygame.time.Clock().tick(10)
def STT(mic, recognizer):
	while True:
		play_sound(START_SOUND)

		with mic as source:
			audio = recognizer.listen(source, timeout=4, phrase_time_limit=4)		
		try:
			result = recognizer.recognize_google(audio, language='ko-KR')
			play_sound(REGIST_SOUND)
			# speak('the food is '+result)
			print(result)
			return result
		except:
			print('repeat once')
			pass
def init_mic():
	# STT
	pygame.mixer.pre_init(24000)
	pygame.mixer.init()
	pygame.mixer.music.set_volume(0.5)
	recognizer = sr.Recognizer()
	mic = sr.Microphone()
	return mic, recognizer

