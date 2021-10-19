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
import serial

AllowedActions = ['both', 'publish', 'subscribe']

# Custom MQTT message callback
def customCallback(client, userdata, message):
    print("Received a new message: ")
    print(message.payload)
    print("from topic: ")
    print(message.topic)
    print("--------------\n\n")


host = "a1ym84qrgn7buq-ats.iot.us-east-1.amazonaws.com"
rootCAPath = "/home/pi/.aws/root-CA.crt"
certificatePath = "/home/pi/.aws/RPi.cert.pem"
privateKeyPath = "/home/pi/.aws/RPi.private.key"
useWebsocket = False
clientId = "RPi"
topic1 = "RPi/distance"
topic2 = "RPi/light"
mode = "publish"

# Port defaults
if useWebsocket:  # When no port override for WebSocket, default to 443
    port = 443
if not useWebsocket:  # When no port override for non-WebSocket, default to 8883
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
loopCount_d = 0
loopCount_l = 0

ser = serial.Serial('/dev/ttyACM0', 9600, timeout= 0.5)
while True:
    if ser.in_waiting:          # 若收到序列資料…
        data_raw = ser.readline().decode()
        end1 = data_raw.find(': ')
        end2 = data_raw.find('\r\n')
        ty = data_raw[:end1]
        data = data_raw[end1+2:end2]
        #struct_time = time.localtime(time.time())
        #localtime = time.strftime("%Y-%m-%d %H:%M:%S", struct_time)
        localtime = time.time()

        if mode == 'both' or mode == 'publish':
            topic  = ''
            if ty =='Distance':
                topic = topic1
            else:
                topic = topic2
            message = {}
            message['type'] = topic
            message['value'] = data
            message['time'] = localtime
            messageJson = json.dumps(message)
            myAWSIoTMQTTClient.publish(topic, messageJson, 1)
            if mode == 'publish':
                print('Published topic %s: %s\n' % (topic, messageJson))
