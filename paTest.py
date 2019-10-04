"""
PyAudio Example: Make a wire between input and output (i.e., record a
few samples and play them back immediately).

This is the callback (non-blocking) version.
"""

import pyaudio
import time
import wave

WIDTH = 2
CHANNELS = 2
RATE = 44100
CHUNK = 1024

wf = wave.open('440Hz.wav', 'rb')
print("Sample width [bytes]", wf.getsampwidth())
print("Num of channels", wf.getnchannels())
print("Frame rate", wf.getframerate())

p = pyaudio.PyAudio()

def callback(in_data, frame_count, time_info, status):
    data = wf.readframes(frame_count)
    print(frame_count, time_info, status)
    if len(data) < frame_count*wf.getsampwidth():
        wf.rewind()
        data = wf.readframes(frame_count)
    return (data, pyaudio.paContinue)

stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                input=False,
                output=True,
                stream_callback=callback)

stream.start_stream()

while stream.is_active():
    time.sleep(0.1)

stream.stop_stream()
stream.close()

p.terminate()
