import time
import board
from adafruit_seesaw.seesaw import Seesaw
import os
import requests # NEW: Import requests library
import json     # NEW: Import json library

# --- Configuration ---
# NEW: The Raspberry Pi now sends data to the Node.js server
SERVER_URL = "http://<YOUR_SERVER_IP_ADDRESS>:5002/api/sensor-data"

# This threshold is now managed by the server, but we keep it here for local alerts
ALERT_THRESHOLD_F = 80.0 
SIMULATION_INTERVAL_SEC = 10

# Initialize I2C connection
try:
    i2c_bus = board.I2C()
    ss = Seesaw(i2c_bus, addr=0x36)
    print("✅ Seesaw sensor initialized via I2C.")
    SENSOR_READY = True
except Exception as e:
    print(f"❌ I2C Initialization Error: {e}. Using mock data.")
    SENSOR_READY = False

def convert_c_to_f(celsius):
    return (celsius * 9/5) + 32

def send_local_alert(temperature_f):
    """Logs the critical alert locally on the Pi."""
    print("*******************************************")
    print(f"🚨 CRITICAL ALERT: TEMPERATURE IS {temperature_f:.2f}°F")
    print("   Action: Logged alert locally (80°F threshold exceeded).")
    print("*******************************************")

# --- NEW: Function to send data to the Node.js server ---
def send_data_to_server(temperature_f, moisture_value):
    """Sends sensor data to the Node.js server via a POST request."""
    payload = {
        "temperature": temperature_f,
        "moisture_value": moisture_value,
        "timestamp": time.time() * 1000 # Milliseconds
    }
    try:
        response = requests.post(SERVER_URL, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        if response.status_code == 200:
            print(f"✅ Data successfully sent to server.")
        else:
            print(f"🔴 Failed to send data. Server responded with status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending data to server: {e}")

# Main loop
while True:
    temperature_f = 0.0
    moisture_value = 0
    
    if SENSOR_READY:
        moisture_value = ss.moisture_read()
        temperature_c = ss.get_temp()
        temperature_f = convert_c_to_f(temperature_c)
    else:
        # Mock data for testing without a sensor
        moisture_value = 400
        temperature_f = (70 + (time.time() % 20)) # Simulate fluctuating temp

    # 1. Send data to the Node.js server
    send_data_to_server(temperature_f, moisture_value)

    # 2. Check for local alert condition (optional, but good for redundancy)
    if temperature_f >= ALERT_THRESHOLD_F:
        send_local_alert(temperature_f)

    # 3. Print status
    print(f"Temp: {temperature_f:.2f}°F | Moisture: {moisture_value}")

    time.sleep(SIMULATION_INTERVAL_SEC)
