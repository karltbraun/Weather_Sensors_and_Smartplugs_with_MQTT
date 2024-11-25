# Weather_Sensors_and_Smartplugs_with_MQTT

## Overview

(Apologies for the rediculously long name - I'm terrible at naming things)

This project started out with a desire to learn how to (1) take flat MQTT data and transform it into packaged data in json format, and (2) take MQTT data in a packaged json format and transform it into a flat MQTT namespace.

It sources the data from two areas:

(1) We use the RTL-433 program and an SDR dongle tuned for 433 MHz to read data from consumer type weather sensors broadcasting on the 433 MHz band.  RTL_433 can be configured to publish to an MQTT broker, and when it does, it does in a flat MQTT fashion, with one attribute of each device per message.  The device is defined by the topic, with the device ID being the last part of the topic in the received message.

(2) I acquired a couple of Shelly US smartplugs - mainly for use on my level 1 EV charger to see how much energy it was using, but I also put one in my lab to monitor energy usage there.  The Shelly smartplugs are MQTT enabled, and deliver a json package for each device, with nested parts of the json being updated at different intervals.

There are two main routines (entry point routines): shelly_main.py which is for the Shelly smartplugs, and weather_republish.py which is for the weather sensors.

These routines do essentially the same thing:

1) setup logging and mqtt connections
2) setup the mqtt callbacks
3) start the main loop

The main loop is fairly common between the two as well:

1) The on_message callback just puts the incoming mqtt message in a queue
2) The main loop reads and processes the messages in the queue
3) For the Shelly routines, once a message is processed, it is put in the output queue.  The main loop then publishes the data in the output queue to the mqtt broker.
4) For the weather sensors, we are consuming flat data - one sensor attribute per mqtt message (eg: temperature, humidity, various radio information, etc).  We keep a dictionary of each device seen indexed by the device id.  We also keep track (in the dictionary entries) of (a) when the device data was last published and (b) when some information from that device was last seen (when something changed).
5) The Main loop cycles through the dictionary of devices and publishes the data if anything has changed since it was last published.

The current version assumes the same broker for subscribing and publishing; but there are some aspects of the code which were set up so that multiple brokers could be used.

## Installation

Nothing complex.  You will need the root directory of the repository, and the following folders defined in the root directory:

- config
- logs
- src
  - src/managers
  - src/models
  - src/utils

These are defined below

## Directory Structure

### Top level directory

#### README.md

This file

#### republish_processed_sensors_main.py

The main entry point for the routines which consume topics from the RTL_433 program publishing flat mqtt data, gathers the data into a dictionary of devices, and then republishes the data in a json package for each device.

#### shelly_main.py

The main entry point for the routines which consume the data published by the shelly smartplugs and republishes the data in flat MQTT fashion for easy analysis.

#### requirements.txt

Required packages for the code.  Should be:

- paho-mqtt==2.1.0
- python-dotenv==1.0.1

#### RTL_433_Protocols.txt

From the RTL_433 documentation - a list of the protocol_ids and their descriptions.  Used to create the rtl_433_protocols.json file (manually).

#### setup.sh

Apparently something uv (an environment manager) sets up.  First time using this so I'm not totally clear on this.

### logs

This directory is where the log files are written.  See utils/logger_setup.py for details.  Each of the '...main.py' routines will call the logger_setup with logging levels.

### config

#### config/broker_config.py

Setups up a dictionary with different broker configurations so that it is fairly easy to switch between brokers for testing.  Note that username and password information is kept in the .env file which is read by load_broker_config and then used to update the dictionary.

I'm not using a username and password in my current testing, so this logic hasn't been very well tested.

#### config/device_ids.json

This file is used to map devices (by teir device_id) into separate topics.  The 'ktb_weather_sensors' list are for the sensors I have at my house.  The "other_weather_sensors" are sensors I have seen (via the RTL_433 scanning) that are not mine, but that I have determined are weather sensors by their protocol_ids (see rtl_433_protocols.json).

Similarly for the 'other_security_sensors'.  You can add here as you see fit.

NOTE: RTL_433 will pick up a rediculous number of devices - tire pressure sensors, ring doorbell devices, simply safe security devices, automatic curtain controllers, etc.

NOTE: a lot of the devices will change their device_id to some random number when they reboot (like when you change the battery on them).  You will have to determine what the new IDs are and add them to the lists as needed.

#### config/logging_config.py

A simple logging configuration setup.

#### config/mqtt_config.py

Sets up default MQTT parameter values (Port, keepalive timer, etc) and default topics.  The latter is not used in the current scripts but was put in for future use.

#### config/protocol_categories.json

Refer to config/rtl_433_protocols.json, RTL_433_Protocols.txt, or to the RTL_433 documentation for more information on the protocols.

The scripts use the lists in protocol_categories.json to determine what type of device is being seen.  This is used to determine under which topic to publish the data.

The lists were formed by seeing what devices were being seen by RTL_433, looking up the protocols, and putting the protocol_id in the desired list.  This was a lazy way of avoiding having to categorize each protocol_id individually (over 200 at this writing).

#### rtl_433_protocols.json

A dictionary of protocols Ids indexing a short name and long description for each protocol.  Many still have "TBD" in the name as I haven't seen them in my testing yet and so didn't take the time to determine a short name.  The descriptions come from the RTL_433 documentation.

### src

This directory contains most of the code, divided up into separate subdirectories, except for the main entry point routines.

#### managers

Code and data which manage the more object-oriented aspects of the code.

##### message_manager_republish.py

Message manager for the republish_processed_sensors.py routine.  This is the code that takes the flat mqtt data and packages it up into json for each device.

##### message_manager_shelly.py

Message manager for the shelly_main.py routine.  This is the code that takes the json data from the Shelly smartplugs and republishes it in flat mqtt fashion.  

Creation of the publication topic strings is handled here; some comments will clarify
how the topics are created.

#### mqtt_manager.py

Contains the MQTT setup code and the call back functions.  

Also contains the MQTTManager class which has the input / output queues, publish and subscribe topics, etc.  This makes it a little easier to decouple the code without passing a ton of parameters around.

##### protocol_manager.py

Used by the republish_processed_sensors.py routine only.  Handles the periodic loading of the RTL_433 protocols and the categorization of the protocols into the categories in protocol_categories.json.

The file specifications for the RTL_433 protocols and the localized categories defintion files are defined here, as well as routines for checking for updates to these files and reloading them if they have changed.  This allows for updating the defintions files without having to restart the main routines.

#### models

Only contains the devices.py file which is used by the republish_processed_sensors.py routine.  This attempts to define subgroups of device attributes that are commonly seen in my use.  This may be overly complex, but it was the best I could do at the time.

#### utils

##### device_maps.py

Used to map known (to me) device_ids with the names I want to use for them.  There are the "ID-sensor_name" which is sort of the brand name of the sensor, and a "sensor_name" which is my personal name for the device indicating where the temperature sensor is located.

Note that the current version of this code is set up to use where there might be other sensors types and are grouped in to 'rooms' or areas of the property in common.  

For example, we will have a weather sensor in the garage along with one of the shelly smartplugs, and they will both be grouped into a topic that indicates they are in the garage (vs my office or other room).

##### flatten_json.py

Pretty useful routine cooked up by chatGPT to take a possibly-nested dictionary and turn it in to a series of topic-value pairs for publishing into a flat mqtt namespace.

##### logger_setup.py

A simple logger setup routine module

## Usage

## Contributing

## License

## Contact
