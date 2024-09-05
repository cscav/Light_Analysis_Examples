from datetime import datetime
from ctypes import cdll,c_long, c_ulong, c_uint32,byref,create_string_buffer,c_bool,c_char_p,c_int,c_int16,c_double, sizeof, c_voidp
from TLPMX import TLPMX
import time

from TLPMX import TLPM_DEFAULT_CHANNEL

# additions to send to homeassistant
import os
from dotenv import load_dotenv
load_dotenv()
import json
import paho.mqtt.publish as publish 
mqtt_topic = "power meter"
mqtt_broker_address = os.getenv('ADDRESS')
credentials = {'username': os.getenv('MQTT_USERNAME'), 'password': os.getenv('PASSWORD')}

# Find connected power meter devices.
tlPM = TLPMX()
deviceCount = c_uint32()
tlPM.findRsrc(byref(deviceCount))

print("Number of found devices: " + str(deviceCount.value))
print("")

resourceName = create_string_buffer(1024)

for i in range(0, deviceCount.value):
    tlPM.getRsrcName(c_int(i), resourceName)
    print("Resource name of device", i, ":", c_char_p(resourceName.raw).value)
print("")
tlPM.close()

# Connect to last device.
tlPM = TLPMX()
tlPM.open(resourceName, c_bool(True), c_bool(True))

message = create_string_buffer(1024)
tlPM.getCalibrationMsg(message,TLPM_DEFAULT_CHANNEL)
print("Connected to device", i)
print("Last calibration date: ",c_char_p(message.raw).value)
print("")

time.sleep(2)

# Set wavelength in nm.
wavelength = c_double(852)
tlPM.setWavelength(wavelength,TLPM_DEFAULT_CHANNEL)

# Enable auto-range mode.
# 0 -> auto-range disabled
# 1 -> auto-range enabled
tlPM.setPowerAutoRange(c_int16(1),TLPM_DEFAULT_CHANNEL)

# Set power unit to Watt.
# 0 -> Watt
# 1 -> dBm
tlPM.setPowerUnit(c_int16(0),TLPM_DEFAULT_CHANNEL)

# Take power measurements and save results to arrays.
power_measurements = []
times = []
count = 0
while True:
    power =  c_double()
    tlPM.measPower(byref(power),TLPM_DEFAULT_CHANNEL)

    # send to HAOS
    payload = {
        "power": power.value
    }
    payload_json = json.dumps(payload)
    publish.single(mqtt_topic, payload_json, hostname = mqtt_broker_address, auth = credentials)

    power_measurements.append(power.value)
    times.append(datetime.now())
    print(times[count], ":", power_measurements[count], "W")
    count+=1
    time.sleep(1)
print("")

# Close power meter connection.
tlPM.close()
print('End program')
