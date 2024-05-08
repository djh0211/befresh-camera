import pvporcupine
import struct
import pyaudio


porcupine = pvporcupine.create(
  access_key='P5GdhwlBrorjoVFgVbptVktYQqqfT2s6QS6U2W4CR+AyhfeKk1sdGQ==',
  keyword_paths=['~/dev/hotword-detection/hotword-model.ppn'],
  model_path='./porcupine_params_ko.pv'
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
		# detected `porcupine`
		print('detected porcu')
	elif keyword_index == 1:
		# detected `bumblebee`
		print('bumblebee')

