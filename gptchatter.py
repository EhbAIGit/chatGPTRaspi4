import pygame
from openai import OpenAI
import sounddevice as sd
import numpy as np
import tempfile
from scipy.io.wavfile import write
from datetime import datetime
import time
import RPi.GPIO as GPIO

# Initialiseer GPIO
GPIO.setmode(GPIO.BCM)
BUTTON_PIN = 4
LED_PIN = 18
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(LED_PIN, GPIO.OUT)


def blink_led(pin, duration, interval):
    end_time = time.time() + duration
    while time.time() < end_time:
        GPIO.output(pin, GPIO.HIGH)  # LED aan
        time.sleep(interval)  # Pauzeer voor het interval
        GPIO.output(pin, GPIO.LOW)   # LED uit
        time.sleep(interval)  # Pauzeer opnieuw




#device_info = sd.query_devices(3)
#print(f"Device info: {device_info}")

def play_mp3(file_path):
    pygame.init()
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()

def rms(frame):
    return np.sqrt(np.mean(np.square(frame), axis=0))

def record_until_silence(threshold=0.01, fs=44100, chunk_size=1048, max_silence=5):
    print("Begin met opnemen... Spreek nu.")
    recorded_frames = []
    silent_frames = 0
    silence_limit = int(max_silence * fs / chunk_size)

    def callback(indata, frames, time, status):
        nonlocal silent_frames
        volume_norm = rms(indata)
        if volume_norm < threshold:
            silent_frames += 1
            if silent_frames > silence_limit:
                raise sd.CallbackStop
        else:
            silent_frames = 0
        recorded_frames.append(indata.copy())

    with sd.InputStream(callback=callback, dtype='float32', channels=1, samplerate=fs, blocksize=chunk_size):
        print("Opname gestart. Wacht op geluid...")
        while True:
            # Check op knopdruk
            if GPIO.input(BUTTON_PIN) == GPIO.LOW:
                break
            time.sleep(0.01)
            
    time.sleep(0.5)
    print("\nEinde van de opname.")
    recording = np.concatenate(recorded_frames, axis=0)
    temp_file = tempfile.mktemp(prefix='opgenomen_audio_', suffix='.wav')
    write(temp_file, fs, recording)
    print(f"Audio opgenomen en opgeslagen in: {temp_file}")
    return temp_file

api_key="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"
client = OpenAI(api_key=api_key)


with open('/home/pi/Documents/chatGPTRaspi4/basicContext.txt', 'r') as file:
    inhoud = file.read()

initial_messages = [
    {"role": "system", "content": inhoud},
]

messages = initial_messages.copy()

counter = 0

user_input = ""

try:

    blink_led(LED_PIN, 1, 0.1)
    play_mp3("/home/pi/Documents/chatGPTRaspi4/audioTemplates/werkingUitleg.mp3")
    blink_led(LED_PIN, 21, 0.1)
    

    while True:
        print("Wacht op knopdruk om verder te gaan...")
        if (counter >=1):
          while GPIO.input(BUTTON_PIN) == GPIO.HIGH:
            blink_led(LED_PIN, 0.2, 0.1)
            
          time.sleep(0.2)
          GPIO.output(LED_PIN, GPIO.HIGH)
          audio_file_path = record_until_silence()
          GPIO.output(LED_PIN, GPIO.LOW)
          with open(audio_file_path, "rb") as audio_file:
            user_input = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
          )
          user_input = user_input.text
        
        counter+=1
        if user_input.lower() == 'exit':
            print("Exiting chat...")
            with open("/home/pi/Documents/chatGPTRaspi4/contextHistory.txt", 'w') as naofile:
                naofile.write(str(messages))
            break

        words_to_test = ['kenniscentra', 'onderzoek']
        for word in words_to_test:
            if word.lower() in user_input.lower():
                messages.append({"role": "assistant", "content": "Erasmushogeschool heeft onderzoekscentra. Namelijk Kenniscentrum Artificial Intelligence, Kenniscentrum BruChi, Kenniscentrum Open BioLab Brussels, Kenniscentrum OpenTime, Kenniscentrum PAKT, Kenniscentrum Urban Coaching & Education, Kenniscentrum Tuin+"})
        

        messages.append({"role": "user", "content": user_input})

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )

        start = time.time()
        date_time = datetime.now()
        format = '%Y%m%d%H%M%S'
        string = date_time.strftime(format)
        speech_file_path = 'speech' + str(string)+ ".mp3"
        response = client.audio.speech.create(
            model="tts-1",
            voice="onyx",
            input=completion.choices[0].message.content
        )
        response.stream_to_file(speech_file_path)
        end = time.time()

        play_mp3(speech_file_path)
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        print("Assistant:", completion.choices[0].message.content)
        messages.append({"role": "assistant", "content": completion.choices[0].message.content})
finally:
    GPIO.cleanup()
