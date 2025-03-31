import pygame
import os
from openai import OpenAI
import matplotlib.pyplot as plt
import sounddevice as sd
import numpy as np
import tempfile
from scipy.io.wavfile import write, read as read_wav
from datetime import datetime, timezone, timedelta
import time
import matplotlib.animation as animation
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
import warnings
import subprocess
import requests
import xml.etree.ElementTree as ET
import html
from bs4 import BeautifulSoup
import re
from icalendar import Calendar
import json
import random
import serial
import keyboard

warnings.filterwarnings("ignore")

# Seriële poort instellen
ser = serial.Serial('COM8', 9600)

bericht = "pftpftpftpftpft"
ser.write(bericht.encode()) 

messageEnded = True

# Initialiseer Pygame voor audio afspelen
pygame.mixer.init()
chatViaMic = True


def play_audio(file_path):
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

chunk_size = 1024


def get_weeks_start_and_end_dates(date):
    start = date - timedelta(days=date.weekday())
    end = start + timedelta(days=6)
    return start, end


def rms(frame):
    return np.sqrt(np.mean(np.square(frame), axis=0))

def record_until_silence(threshold=0.015, fs=44100, chunk_size=1024, max_silence=500):
    print("Begin met opnemen... Spreek nu.")
    recorded_frames = []
    silent_frames = 5
    silence_limit = int(max_silence * fs / chunk_size)
    recording_started = False

    def callback(indata, frames, time, status):
        nonlocal silent_frames, recording_started
        volume_norm = rms(indata)
        if volume_norm < threshold:
            silent_frames += 1
            if silent_frames > silence_limit:
                print("silence limit")
        else:
            silent_frames = 0
            recording_started = True
        recorded_frames.append(indata.copy())                                
        if not keyboard.is_pressed('space'):      
            print("ended by spacebar")
            raise sd.CallbackStop

    with sd.InputStream(callback=callback, device=1, dtype='float32', channels=1, samplerate=fs, blocksize=chunk_size):
        print("Opname gestart. Wacht op geluid...")
        bericht = "tttttttttttttttttttttttttttttttttttttttttttt"
        ser.write(bericht.encode()) 
        sd.sleep(5000)

    if not recording_started:
        print("\nGeen vraag waargenomen.")
        return 0
    else:
        print("Einde van de opname. Even geduld aub.")
        recording = np.concatenate(recorded_frames, axis=0)
        temp_file = tempfile.mktemp(prefix='opgenomen_audio_', suffix='.wav')
        write(temp_file, fs, recording)
        return temp_file

with open("openaikey.txt", "r") as f:
    api_key = f.read().strip()

client = OpenAI(api_key=api_key)

with open('basicContext.txt', 'r') as file:
    inhoud = file.read()

initial_messages = [
    {"role": "system", "content": inhoud},
]

messages = initial_messages.copy()
firstCall = True
start_time = time.perf_counter()
toWait = 0

while True:
    if not firstCall:
        if not chatViaMic:
            user_input = input("Your message: ")
        else:
            print("Druk op de spatiebalk om te beginnen met een vraag te stellen, laat deze opnieuw los wanneer je je vraag hebt gesteld.")
            while not keyboard.is_pressed('space'):
                pass
            audio_file_path = record_until_silence()
            if audio_file_path == 0:
                continue
            with open(audio_file_path, "rb") as audio_file:
                user_input = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file
                ).text
    else:
        firstCall = False
        user_input = "Hallo wie ben jij?"

    if user_input.lower() == 'exit':
        print("Exiting chat...")
        break

    keywords_responses = {
        "kenniscentra": "Erasmushogeschool heeft onderzoekscentra. Namelijk Kenniscentrum Artificial Intelligence,  Kenniscentrum BruChi, Kenniscentrum Open BioLab Brussels, Kenniscentrum OpenTime, Kenniscentrum PAKT, Kenniscentrum Urban Coaching & Education, Kenniscentrum Tuin+",
    }

    for word, response_text in keywords_responses.items():
        if word in user_input.lower():
            messages.append({"role": "assistant", "content": response_text})

    if "weerbericht" in user_input.lower():
        start_time = time.perf_counter()
        subprocess.Popen(['python', 'playmp3.py', 'waiting/weeropzoeken.mp3'])
        toWait = 5
        response = requests.get('https://www.meteo.be/nl/weer/verwachtingen/weer-voor-de-komende-dagen')
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'lxml')
            text = soup.get_text()
            gevonden_tekst = re.search(r'Laatste update:(.*?)Uitleg over onze voorspellingen', text, re.DOTALL)
            inhoud = gevonden_tekst.group(1).strip()
            messages.append({"role": "assistant", "content": inhoud})

    messages.append({"role": "assistant", "content": user_input})

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )

    end_time = time.perf_counter()
    total_time = end_time - start_time
    print(f"Totale uitvoeringstijd voor chat: {total_time} seconden.")

    string = datetime.now().strftime('%Y%m%d%H%M%S')
    speech_file_path = 'speech' + str(string) + ".mp3"

    start_time = time.perf_counter()
    response = client.audio.speech.create(
        model="tts-1",
        voice="nova",
        input=completion.choices[0].message.content
    )
    response.stream_to_file(speech_file_path)

    while (time.perf_counter() - start_time) < toWait:
        time.sleep(0.5)

    print(f"Totale uitvoeringstijd voor speech: {time.perf_counter() - start_time} seconden.")

    subprocess.Popen(['python', 'playmp3.py', speech_file_path])
    #play_audio(speech_file_path)
    print("ROBOT:", completion.choices[0].message.content)
    messages.append({"role": "assistant", "content": completion.choices[0].message.content})
