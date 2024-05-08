# stt
from gtts import gTTS
from io import BytesIO
import pyaudio
import wave
import speech_recognition as sr
import pygame

recognizer = sr.Recognizer()

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = 'output.wav'

p = pyaudio.PyAudio()

stream = p.open(format=FORMAT,
				channels=CHANNELS,
				rate=RATE,
				input=True,
				frames_per_buffer=CHUNK
				)

frames = []

for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
	data = stream.read(CHUNK)
	frames.append(data)

print('Recording is finished')

stream.stop_stream()
stream.close()
p.terminate()

wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
wf.setnchannels(CHANNELS)
wf.setsampwidth(p.get_sample_size(FORMAT))
wf.setframerate(RATE)
wf.writeframes(b''.join(frames))
wf.close()

kr_audio = sr.AudioFile('./output.wav')
with kr_audio as source:
	audio = recognizer.record(source)

def speak(text):
	tts = gTTS(text=text, lang='ko')
	
	tts_bytes = BytesIO()
	tts.write_to_fp(tts_bytes)
	tts_bytes.seek(0)
	
	pygame.mixer.pre_init(24000)
	pygame.mixer.init()
	pygame.mixer.music.load(tts_bytes)
	pygame.mixer.music.set_volume(0.5)
	pygame.mixer.music.play()
	while pygame.mixer.music.get_busy():
		pygame.time.Clock().tick(10)
	
try:
	speak('the food is '+recognizer.recognize_google(audio, language='ko-KR'))
	print('text is '+ recognizer.recognize_google(audio, language='ko-KR'))
except sr.UnknownValueError:
	print('repeat once')
except sr.RequestError as e:
	print('server error')
