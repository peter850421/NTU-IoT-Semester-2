'''
/*
 * Copyright 2010-2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License.
 * A copy of the License is located at
 *
 *  http://aws.amazon.com/apache2.0
 *
 * or in the "license" file accompanying this file. This file is distributed
 * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 * express or implied. See the License for the specific language governing
 * permissions and limitations under the License.
 */
 '''

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import logging
import time
import argparse
import json
from serial import Serial
from PIL import Image, ImageDraw, ImageFont
import picamera

AllowedActions = ['both', 'publish', 'subscribe']

def draw_img(value, outputfile):
    img = Image.new('RGB', (100, 100), (225, 225, 225))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype('/var/www/html/number.ttf', 40)
    draw.text((30,30),str(value),font=font, fill=(10,10,10,128))
    img.save(outputfile)

# Custom MQTT message callback
def customCallback(client, userdata, message):
    print("Received a new message: ")
    print(message.payload)
    print("from topic: ")
    print(message.topic)
    print("--------------\n\n")

def publish_sensor(value, sensor_type, loopCount):
    if mode =='both' or mode =='publish':
        message = {}
        message['type'] = sensor_type
        message['value'] = value
        message['sequence'] = loopCount
        messageJson = json.dumps(message)
        myAWSIoTMQTTClient.publish("rpi/sensor_wet", messageJson, 1)
        if mode =='publish':
            print('Publish topic %s: %s\n' %("rpi/sensor_wet", messageJson))

def publish_watering_times(value, loopCount):
    if mode =='both' or mode =='publish':
        message = {}
        message['type'] = 'WATER'
        message['value'] = value
        message['sequence'] = loopCount
        messageJson = json.dumps(message)
        myAWSIoTMQTTClient.publish("rpi/sensor_water", messageJson, 1)
        if mode =='publish':
            print('Publish topic %s: %s\n' %("rpi/sensor_water", messageJson))

# Read in command-line parameters
host = "a1rlohdm5vkx2f-ats.iot.us-east-1.amazonaws.com"
rootCAPath = ".aws/root-CA.crt"
certificatePath = ".aws/rpi.cert.pem"
privateKeyPath = ".aws/rpi.private.key"
port = 8883
useWebsocket = False
clientId = "rpi"
topic = "rpi/sensor"
mode = "publish"

if mode not in AllowedActions:
    parser.error("Unknown --mode option %s. Must be one of %s" % (args.mode, str(AllowedActions)))
    exit(2)
if useWebsocket and not port:  # When no port override for WebSocket, default to 443
    port = 443
if not useWebsocket and not port:  # When no port override for non-WebSocket, default to 8883
    port = 8883

# Configure logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# Init AWSIoTMQTTClient
myAWSIoTMQTTClient = None
if useWebsocket:
    myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId, useWebsocket=True)
    myAWSIoTMQTTClient.configureEndpoint(host, port)
    myAWSIoTMQTTClient.configureCredentials(rootCAPath)
else:
    myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
    myAWSIoTMQTTClient.configureEndpoint(host, port)
    myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTClient connection configuration
myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connect and subscribe to AWS IoT
myAWSIoTMQTTClient.connect()
if mode == 'both' or mode == 'subscribe':
    myAWSIoTMQTTClient.subscribe(topic, 1, customCallback)
time.sleep(2)

# Publish to the same topic in a loop forever
loopCount = 0
ser = Serial('/dev/ttyACM0', 9600, timeout=.5)
while True:
    if ser.inWaiting():
        res = ser.readline().decode('utf8')[:-2]
        cam = picamera.PiCamera()
        cam.vflip = True
        cam.hflip = True
        cam.capture('images/lab.jpg')
        cam.close()

        if "water" in res:
            end = res.find("|")
            cnt  = int(res[15:end])
            draw_img(cnt, "images/water.jpg")
            publish_watering_times(cnt, loopCount)
        elif "Light" in res:
            end = res.find("l")
            light = float(res[6:end])
            draw_img(light, "images/light.jpg")
            publish_sensor(light, "Light", loopCount)
        elif "Soil" in res:
        	#end = res.find("")
            soil = int(res[5:])
            draw_img(soil, "images/soil.jpg")
            publish_sensor(soil, "Soil", loopCount)
        elif "Humid" in res:
            end = res.find("%")
            humid = float(res[9:end])
            draw_img(humid, "images/humidity.jpg")
            publish_sensor(humid, "Humid", loopCount)
        elif "Temper" in res:
            end = res.find("*C")
            temper = float(res[12:end])
            draw_img(temper, "images/temperature.jpg")
            publish_sensor(temper, "Temperature", loopCount)
        else:
            pass
        loopCount += 1











