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
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

device_info = sd.query_devices(3)
print(f"Device info: {device_info}")

def play_mp3(file_path):
    pygame.init()
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()

def rms(frame):
    return np.sqrt(np.mean(np.square(frame), axis=0))

def record_until_silence(threshold=0.03, fs=44100, chunk_size=2048, max_silence=2):
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

    print("\nEinde van de opname.")
    recording = np.concatenate(recorded_frames, axis=0)
    temp_file = tempfile.mktemp(prefix='opgenomen_audio_', suffix='.wav')
    write(temp_file, fs, recording)
    print(f"Audio opgenomen en opgeslagen in: {temp_file}")
    return temp_file

client = OpenAI()

with open('contextHistory.txt', 'r') as file:
    inhoud = file.read()

initial_messages = [
    {"role": "system", "content": inhoud},
]

messages = initial_messages.copy()

try:
    while True:
        print("Wacht op knopdruk om verder te gaan...")
        while GPIO.input(BUTTON_PIN) == GPIO.HIGH:
            time.sleep(0.1)

        audio_file_path = record_until_silence()
        with open(audio_file_path, "rb") as audio_file:
            user_input = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        
        user_input = user_input.text

        if user_input.lower() == 'exit':
            print("Exiting chat...")
            with open("contextHistory.txt", 'w') as naofile:
                naofile.write(str(messages))
            break

        words_to_test = ['kenniscentra', 'onderzoek']
        for word in words_to_test:
            if word.lower() in user_input.lower():
                messages.append({"role": "assistant", "content": "Erasmushogeschool heeft onderzoekscentra. Namelijk Kenniscentrum Artificial Intelligence, Kenniscentrum BruChi, Kenniscentrum Open BioLab Brussels, Kenniscentrum OpenTime, Kenniscentrum PAKT, Kenniscentrum Urban Coaching & Education, Kenniscentrum Tuin+"})
        
        words_to_test = ['weerbericht']
        for word in words_to_test:
            if word.lower() in user_input.lower():
                messages.append({"role": "assistant", "content": "Zeg dat je het weerbericht via een API kan ophalen en vraag naar de locatie. Eens je de locatie weet maak je een json string van de vorm {\"actionname\": \"weather\",\"location\": \"gevraagde\"}"})

        messages.append({"role": "user", "content": user_input})

        completion = client.chat.completions.create(
            model="gpt-4-turbo",
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

        print(end - start)

        play_mp3(speech_file_path)
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        print("Assistant:", completion.choices[0].message.content)
        messages.append({"role": "assistant", "content": completion.choices[0].message.content})
finally:
    GPIO.cleanup()
