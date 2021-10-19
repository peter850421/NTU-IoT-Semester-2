Source: https://github.com/lucileee5657/IoT_smart_water_plant
# IoT_smart_water_plant
## Smart Plant Watering System with Cloud and Real-time Monitoring

* Retrieve values from various sensors.
* Record those sensor data on the cloud.
* Take pictures of the plant and send it to the owner through Line notify (TBD).
* Real-time publish sensor values and the photo of plants on local website in the same domain.
* Automated watering and cooling down according to the moisture and temperature values.

### Requirements
* An AWS account
* Arduino Uno
* Raspberry Pi
* sensors: soil moisture, light, temperature and humidity sensor
* battery case with batteries
* water pump and pipes
* small fan

### Hardware
Connect those ingredients with Arduino
![alt text](https://github.com/105061210/IoT_smart_water_plant/blob/main/assets/iot_wire.jpeg)

### Software
#### upload sensor data to AWS
Configure Raspberry Pi and get **connect_device_package.zip**, then put it on RPi and unzip it
```
mkdir .aws
cd .aws
sudo unzip connect_device_package.zip
sudo chmod +x start.sh
sudo ./start.sh
```
Based on  aws-iot-device-sdk-python/samples/basicPubSub/basicPubSub.py, we modify it and get **src/basicPubSub_sensor.py**
 --> Then add the **topic** and **clientId** in **IoT Core -> Secure -> Policies**
 --> And go to **Act -> Rules**, create new rules that 
 ```
 SELECT * FROM 'rpi/sensor_wet'
 ```
 that will insert a message into DynamoDB table (need to create a table or use an old one here)
 --> add another rule
 ```
 SELECT * FROM 'rpi/sensor_water'
 ```
When run src/basicPubSub_sensor.py, it will automatically publish those sensor data and watering times to AWS DynamoDB.

#### Monitoring (by Apache)
Install Apache2 on Raspberry Pi
```
sudo apt-get update
sudo apt-get -y install apache2
```
Then replace the original **index.html** under **/var/www/html** by **src/index.html**
and also copy **sensor.css** and **basicPubSub_sensor.py** to **/var/www/html/**
Finally, connect to the IP of Raspberry Pi, we can monitor our plants!

### Result
#### Demo video:
* For automatically watering and cooling https://drive.google.com/file/d/1psmXBsLfBjDCurmze0sd-OAoLO7ka-0R/view?usp=sharing
* For recording data on DynamoDB and real-time monitoring on web in the same domain https://drive.google.com/file/d/1SW2s0SwKdsn4POhasLO0j1nv2VJmc11I/view?usp=sharing
* For sending the photo of the plant through Line notify https://drive.google.com/file/d/1-J7Asu7q0_Cxp1w3vhEoD8UVgFxaumYM/view?usp=sharing
#### Picture

![alt text](https://github.com/105061210/IoT_smart_water_plant/blob/main/assets/iot_result.jpg)



