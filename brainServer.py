import pygame
import os
from openai import OpenAI
import numpy as np
import tempfile
from datetime import datetime, timezone, timedelta
import time
import warnings
warnings.filterwarnings("ignore")
import random
import re
import random
import pandas as pd
import nltk
from nltk.tokenize import sent_tokenize
import os
import yaml
#  speech to text
import sounddevice as sd
import tempfile
from scipy.io import wavfile
from scipy.io.wavfile import write
import usb.core
import usb.util
import threading
import sys
import socket
import json
from mqtt_handler import start_mqtt_listener, set_socket_conn, set_mqtt_message_callback
from pydub import AudioSegment
import serial

brainActive = True
handle_mqtt = True

# Initialize Pygame for conversation logging
pygame.init()

# Set up the screen
display_width, display_height = 800, 300
screen = pygame.display.set_mode((display_width, display_height))
pygame.display.set_caption('Brainy Conversation Log')
font = pygame.font.Font(None, 48)

# Conversation Log
conversation_log = []

# Scrolloffset als globale variabele om de waarde te behouden
scroll_offset = 0 


def wrap_textline(text, font, max_width):
    words = text.split(' ')
    wrapped_lines = []
    current_line = ""

    print (text)
    
    for word in words:
        # Probeer de huidige regel plus het nieuwe woord
        test_line = current_line + word + " "
        # Meet de breedte van de lijn met het nieuwe woord erbij
        text_width, _ = font.size(test_line)
        
        if text_width <= max_width:
            current_line = test_line  # Voeg het woord toe aan de huidige regel
        else:
            wrapped_lines.append(current_line)  # Voeg de huidige regel toe aan de lijst
            current_line = word + " "  # Begin een nieuwe regel met het woord

    wrapped_lines.append(current_line)  # Voeg de laatste regel toe
    
    return wrapped_lines

# Function to add messages to the conversation log
def add_to_pygame_log(role, text):
    global scroll_offset  # Om scroll_offset te kunnen wijzigen in deze functie
    conversation_log.append(f"{role}: {text}")
    if len(conversation_log) > 20:
        conversation_log.pop(0)
    
    # Parameters voor schermhoogte
    screen_height = 300  # Hoogte van het scherm

    # Clear the screen and redraw
    screen.fill((0, 0, 0))  # Zwart als achtergrond
    y_offset = 10  # Begin bovenaan het scherm met eventuele scroll

    line = conversation_log[-1]
    #wrapped_lines = wrap_textline(line, 40, 600)
    #print (wrapped_lines)


    words = text.split(' ')
    current_line = ""
    lines = []
    line_spacing = 10

    for word in words:
        test_line = current_line + word + " "
        text_width, _ = font.size(test_line)
        if text_width <= display_width:
            current_line = test_line  # Voeg het woord toe aan de huidige regel
        else:
            # Voeg de huidige regel toe aan de lijst met regels
            lines.append(current_line)
            current_line = word + " "  # Begin een nieuwe regel met het huidige woord

    # Voeg de laatste regel toe aan de lijst als er nog tekst over is
    if current_line:
        lines.append(current_line)


    lineNumber = 0
    y = 0
    for lineContent in lines:
        lineNumber+=1
        print (f"{lineNumber} - {lineContent}")
        rendered_text = font.render(lineContent, True, (255, 255, 255))
        screen.blit(rendered_text, (10, y))
        y += font.get_height() + line_spacing

    pygame.display.flip()

# Seriële poort instellen
if (brainActive == True) :
    ser = serial.Serial('COM9', 9600)  # Vervang 'COM1' door de juiste poort en 9600 door de juiste baudrate
    bericht = "pftpftpftpftpft"
    ser.write(bericht.encode()) 

audio_file_path = 0 
last_mqtt_processed_time = 0 

start_listening_event = threading.Event()
stop_listening_event = threading.Event()
start_speaking_event = threading.Event()

# Function to handle incoming MQTT messages
def handle_mqtt_message(mqtt_message):
    global audio_file_path
    global last_mqtt_processed_time

    current_time = time.time()
    if current_time - last_mqtt_processed_time < 10:
        print("Ignoring MQTT message due to rapid fire")
        return
    
    last_mqtt_processed_time = current_time
   
    print(f"Processing MQTT message: {mqtt_message}")
    
    audio_file_path = 0
    print ("Prompting ChatGPT for MQTT messages...")
    # Add the MQTT message to the list of messages for context
    messages.append({"role": "user", "content": mqtt_message})

    start_time_llm = time.perf_counter() 
    # ChatGPT pipeline repeated here; to be modularized later
    completion = client.chat.completions.create(
        model="gpt-4o",  #"gpt-3.5-turbo",
        messages=messages
        # max_tokens=70
        # temperature=0.7
    )
    end_time_llm = time.perf_counter()  # Precieze eindtijd
    total_time_llm = end_time_llm - start_time_llm
    print(f"Total LLM time: {total_time_llm} seconds.")

    # Extract and print the response from GPT-4
    print("GPT-4 response to MQTT message:")
    print(completion.choices[0].message.content)

    # Log to Pygame window
    add_to_pygame_log("Brainy", completion.choices[0].message.content)
    add_to_pygame_log("User", mqtt_message)

    start_speaking_event.set()
    print("SPEAKING PARSED MESSAGE TRIGGERED BY MQTT")

    parsed_text = completion.choices[0].message.content
    print ('SPEAKING PARSED TEXT AFTER LISTENING')
    print (parsed_text)

    ascii_text = parsed_text.encode('ascii', 'ignore').decode()

    playText(ascii_text)
        
    add_to_conversation_log(mqtt_message, completion.choices[0].message.content, ascii_text)

    # Add model's response to the messages list to maintain context
    messages.append({"role": "assistant", "content": completion.choices[0].message.content}) 

    start_speaking_event.clear()

def add_to_conversation_log(user_input, machine_response, parsed_response, file_name="conversation_log.json"):
    entry = {"user_input": user_input, "machine_response": machine_response, "parsed_response": parsed_response}

    with open(file_name, 'a') as file:
        file.write(json.dumps(entry) + '\n')

def pointer_listener(device):
    """Thread to listen to pointer events."""
    bs_pressed_time = 0
    bs_pressed = False

    global reset_conversation
    reset_conversation = False
    while True:
        data = device.read(endpoint.bEndpointAddress, endpoint.wMaxPacketSize, timeout=50000000)
        button_code = data[0]
        if data:
            if button_code == 8:  # Previous Slide button code
                start_listening_event.set()
            elif button_code == 0 and start_listening_event.is_set():  # Button released
                # time.sleep(0.1)
                stop_listening_event.set()
            elif button_code == 16:  # Next Slide button code
                # time.sleep(0.1)
                start_speaking_event.set()
            elif button_code ==  2: # Black screen button 
                # if bs_pressed == False: 
                # bs_pressed_time = time.time()
                reset_conversation = True
            elif button_code == 4 or button_code == 1:
                start_listening_event.set()

def record_audio(fs=44100, chunk_size=1024, min_duration=0.5):
    """Function to record audio until stopped."""
    start_listening_event.wait()
    print("Listening started...")
    recorded_frames = []

    def callback(indata, frames, time, status):
        recorded_frames.append(indata.copy())

    with sd.InputStream(callback=callback, device=1, dtype='float32', channels=1, samplerate=fs, blocksize=chunk_size):
        while not stop_listening_event.is_set():
            time.sleep(0.1)
    stop_listening_event.clear()
    start_listening_event.clear()

    print("Listening stopped.")

    if recorded_frames:
        recording = np.concatenate(recorded_frames, axis=0)
        duration = len(recording) / fs

        if duration < min_duration:
            print("Recording dumped due to being too short.")
            return 0
        else: 
            temp_file = tempfile.mktemp(prefix='recorded_audio_', suffix='.wav')
            write(temp_file, fs, recording)
    else:
        temp_file = 0

    return temp_file

def playText(text):
    start = time.time()

    # current date and time
    date_time = datetime.now()

    # format specification
    format = '%Y%m%d%H%M%S'

    # applying strftime() to format the datetime
    string = date_time.strftime(format)

    start_time = time.perf_counter()  # Precieze starttijd
    # Plaats hier de code waarvan je de uitvoeringstijd wilt meten

    speech_file_path = 'speech' + str(string) + ".mp3"
    response = client.audio.speech.create(
        model="tts-1",
        voice="onyx",
        input=text
    )

    end_time = time.perf_counter()  # Precieze eindtijd
    total_time = end_time - start_time
    while total_time < toWait:
        time.sleep(0.5)
        end_time = time.perf_counter()  # Precieze eindtijd
        total_time = end_time - start_time
    
    print(f"Totale uitvoeringstijd voor speech: {total_time} seconden.")

    response.stream_to_file(speech_file_path)
    end = time.time()

    # Laden van het MP3-bestand
    mp3File = speech_file_path
    audio = AudioSegment.from_mp3(mp3File)
    # Exporteren naar WAV
    pygame.mixer.quit()
    audio.export('vumeter.wav', format="wav")
    pygame.mixer.init()

    audio_file_path = 'vumeter.wav'  # Vervang dit door het pad naar je WAV-bestand
    if brainActive:
        bericht = "pfpfpf"
        ser.write(bericht.encode()) 

    # Start audio playback
    play_audio(audio_file_path)

def play_audio(file_path):
    if brainActive:
        length_seconds = get_audio_length(file_path) / 200
        command = "pf" * int(length_seconds)
        ser.write(command.encode())
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()

def get_audio_length(file_path):
    audio = AudioSegment.from_mp3(file_path)
    return len(audio)  # De lengte van het audiobestand in seconden

if handle_mqtt:
    # Set the callback to handle incoming MQTT messages
    set_mqtt_message_callback(handle_mqtt_message)

    # Start the MQTT listener in a separate thread
    start_mqtt_listener()

# Constants for the Logitech R400
VENDOR_ID = 0x046d
PRODUCT_ID = 0xc538 # 0xc52d

# Find the R400 device
device = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)

if device is None:
    sys.exit("Logitech Pointer not found")
else:
    print("Logitech Pointer found!")

# Set the active configuration. With no arguments, the first configuration will be the active one
device.set_configuration()

# Get the endpoint instance
cfg = device.get_active_configuration()
interface_number = cfg[(0,0)].bInterfaceNumber
alternate_setting = usb.control.get_interface(device, interface_number)
intf = usb.util.find_descriptor(
    cfg, bInterfaceNumber=interface_number,
    bAlternateSetting=alternate_setting
)

endpoint = usb.util.find_descriptor(
    intf,
    # match the first OUT endpoint
    custom_match=
    lambda e:
        usb.util.endpoint_direction(e.bEndpointAddress) ==
        usb.util.ENDPOINT_IN
)

assert endpoint is not None

messageEnded = True

keyfile = open("openaikey.txt", 'r')
OPENAI_KEY = keyfile.read()

client = OpenAI(api_key=OPENAI_KEY)

# Open het tekstbestand in leesmodus ('r')
with open('basicContext.txt', 'r', encoding='utf-8') as file:
    # Lees de inhoud van het bestand en sla het op in een string
    inhoud = file.read()

initial_messages = [
    {"role": "system", "content": inhoud},
]

# Initialize messages list with the initial system message
messages = initial_messages.copy()

firstCall = True
start_time = time.perf_counter()  # Precieze starttijd
toWait = 0
audio_thread_running = False
pointer_thread = threading.Thread(target=pointer_listener, args=(device,))
pointer_thread.start()

while True:
    # Handle Pygame events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f:
                pygame.display.toggle_fullscreen()

    if reset_conversation:
        messages = []
        messages = initial_messages.copy()
        print ("Conversation is reset")
        reset_conversation = False

    if start_listening_event.is_set() and not stop_listening_event.is_set():
        bericht = "tttt"
        ser.write(bericht.encode())

        audio_file_path = record_audio()
        if audio_file_path != 0:
            try:
                start_time_transcription = time.perf_counter()
                with open(audio_file_path, "rb") as audio_file:
                    user_input = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file
                    )

                user_input = user_input.text
                end_time_transcription = time.perf_counter()  # Precieze eindtijd
                total_time_transcription = end_time_transcription - start_time_transcription
                
                print(f"Total transcription time:  {total_time_transcription}, transcription: {user_input}")
                
                # Log user input to Pygame window
                add_to_pygame_log("Persoon", user_input)
            except:
                print("Whisper connection Error")

            try:
                print("Prompting ChatGPT...")
                messages.append({"role": "user", "content": user_input})

                start_time_llm = time.perf_counter()
                # Generate a response from the model
                completion = client.chat.completions.create(
                    model="gpt-4o",  #"gpt-3.5-turbo",
                    messages=messages
                )
                end_time_llm = time.perf_counter()  # Precieze eindtijd
                total_time_llm = end_time_llm - start_time_llm

                print(f"Answer is ready -  Total LLM time: {total_time_llm} seconds.")
            except:
                print("LLM connection error")

        start_listening_event.clear()  #
        # wait to launch speaking.
        if brainActive:
            bericht = "pftpftp"
            ser.write(bericht.encode())

    elif start_speaking_event.is_set() and audio_file_path:
        start_speaking_event.wait(timeout=10)
        print("Speaking triggered")
        print(completion.choices[0].message.content)

        parsed_text = completion.choices[0].message.content
        print('SPEAKING PARSED TEXT AFTER LISTENING')
        print(parsed_text)
        # Log response to Pygame window
        add_to_pygame_log("Brainy", parsed_text)

        ascii_text = parsed_text.encode('ascii', 'ignore').decode()

        playText(ascii_text)
        
        add_to_conversation_log(user_input, completion.choices[0].message.content, ascii_text)


        # Add model's response to the messages list to maintain context
        messages.append({"role": "assistant", "content": completion.choices[0].message.content})

        audio_thread_running = True
        start_speaking_event.clear()

        audio_thread_running = True
        start_speaking_event.clear()
