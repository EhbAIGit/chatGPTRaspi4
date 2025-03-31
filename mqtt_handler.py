import threading
import paho.mqtt.client as mqtt

# Lock for thread-safe handling of conn
conn_lock = threading.Lock()
_conn = None  # Global variable for the socket connection (accessed via a setter)

# Placeholder for the callback function to handle MQTT messages in the main file
mqtt_message_callback = None

# Set the socket connection (setter function)
def set_socket_conn(conn):
    global _conn
    with conn_lock:
        _conn = conn

# Set the callback function for MQTT messages
def set_mqtt_message_callback(callback):
    global mqtt_message_callback
    mqtt_message_callback = callback

# MQTT functions
def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT broker with result code {rc}")
    client.subscribe("brainTalk") 
    client.subscribe("brainTalk/status")   # xArm topic
    
def on_message(client, userdata, msg):
    message = msg.payload.decode()
    print(f"Received MQTT message on {msg.topic}: {message}")
    
    # Format the message to include "MQTT MESSAGE: " at the beginning
    formatted_message = f"MQTT MESSAGE from {msg.topic}: {message}"
    
    # Pass the formatted message to the main file via the callback
    if mqtt_message_callback:
        mqtt_message_callback(formatted_message)

def mqtt_listener():
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect("broker.emqx.io", 1883, 60)  # Connect to the MQTT broker
    mqtt_client.loop_forever()  # Start the MQTT loop

# Start the MQTT listener in a separate thread
def start_mqtt_listener():
    mqtt_thread = threading.Thread(target=mqtt_listener)
    mqtt_thread.start()
