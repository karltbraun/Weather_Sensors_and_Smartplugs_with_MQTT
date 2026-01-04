# Description of this project

I built this project to better understand the basic principles of a Unified Name Space (UNS) for IoT devices using MQTT as the messaging protocol.

I don't have access to PLCs and industrial type sensors and equipment, so I've used consumer grade weather sensors and smart plugs to simulate the data sources.  I'm assuming you already know the basics of UNS and the MQTT protocol.

## Namespace

The MQTT topics used in this project follow a hierarchical structure to organize data effectively, and it's based on the data structures specified by ISA-95 part 2. The ISA spec gives us a standard way to organize industrial data - basically a hierarchy from Enterprise down through Site, Area, Line, and Cell/Work Unit. Think of it like a file system for your factory data:

``` text
- Enterprise
  - Site
    - Area
      - Line
        - Cell or Work Unit
```

You can extend or tweak this depending on your specific use case, but this is the general model as I understand it.  This is usually represented in MQTT topics as follows:

``` text
<enterprise>/<site>/<area>/<line>/<cell>
```

and you can extend it with more granular data sources as needed.  Like, a PLC in a cell might control multiple sensors and actuators, each of which will have individual attributes, which can be represented as:

``` text
<enterprise>/<site>/<area>/<line>/<cell>/<plc>/<sensor_or_actuator>/<attribute>
```

So in my setup, the "enterprise" is just the root of my namespace (or topic root).  I use KTBMES as this root.  I'll get into the specifics of this namespace below.

## Data Flow

There are two sources of raw data:  Basic consumer-grade weather sensors that transmit data using the 433 MHz ISM band, and Shelly smart plugs that report their status and power usage over WiFi.

### Weather Sensors

To collect the weather sensor data, I use an RTL-SDR dongle connected to a Raspberry Pi running the `rtl_433` software. This software decodes the 433 MHz signals from various weather sensors and publishes the raw JSON payloads to an MQTT broker.  

#### Raw Sensor Data

The RTL_433 software knows how to decode a variety of devices, based on a common protocol and a database of device definitions based on a protocol ID.  It can be configured to transmit the decoded data via MQTT, so it sends out each attribute transmitted by the sensor as a separate MQTT message, with a separate topic.  The prefix of the topic string can be configured, so you can push this data to a specific name space.  The name space root for this data I've set up to be separate from my own name space mentioned above - I use the name of my raspberry pi device (Pi1) as the root of this data, so the topic structure looks like this:

``` text
Pi1/sensors/raw/<device_id>/<attribute>
```

where '<attribute>' is usually one of:

- battery_ok
- button
- channel
- humidity
- id (device_id)
- mic (check some type)
- protocol (protocol id)
- temperature (Celsius or Fahrenheit, depending on the model)
- time (timestamp of the reading)

#### Processing Raw Sensor Data

I wrote some Python scripts that subscribe to the raw sensor data topics (eg: Pi1/sensors/raw/#), aggregate the individual attributes into an object representing each device (by device_id), and periodically republish the aggregated device data to a new topic in my own name space, KTBMES.  The republished topic structure looks like this:

``` text
KTBMES/<host>/sensors/...
```

What this gives me is a topic per device in the name space.  The '<host>' is the name of the publishing host, as I have the republishing software running on 2 different laptops and a VM running on a Vultr host.  This sort of represents the 'site' level of the ISA-95 hierarchy.

#### Separating 'local' sensors vs others

The unfiltered collection of data from 433 MHz devices produces an interesting challenge: the RTL system picks up not only my own sensors, but also those of my neighbors.  In addition, it picks up *anything* transmitting on that frequency, which can include various non-weather related devices, such as: 

- Tire pressure sensors, 
- Security system equipment (eg: Simply Safe), 
- Automated gate keyfobs,
- etc.

and there's even a meat thermometer that transmits on that frequency.

> Side Note: I was surprised to learn that tire pressure sensors communicate via radio.  I had always assumed they were either wired or connected via Bluetooth, BLE, or some other near-field protocol.  I suppose this is done because the cost of a simple 433 MHz transmitter is very cheap.

To filter this out, I had to learn what the device_id was for my own sensors - complicated by the fact that, on many of these, the device_id changes every time the device is reset - like when you change the batteries.  I then created a list of local device IDs so I can organize the data based on my own devices (for which I wanted to build dashboards, etc.) and other devices (which I wanted to retain because I'm a nerd and curious).

The final result of the topic structure then looks like this:

``` text
KTBMES/<host>/sensors/house_weather_sensors/<device_name>
KTBMES/<host>/sensors/other_pressure_sensors/<device_name>
etc.
```

(The 'device_name' is created based upon a mapping of known device_ids to friendly names, and a generated name where I don't have a friendly name for a device_id.)

#### Containerizing the project

After everything was running properly on my development machine, I containerized the project using Docker, so I could easily deploy it to other machines.  My setup uses docker desktop with the portainer extension added.  The Dockerfile and portainer oriented yml files are included in the repository.  There are shell scripts to facilitate the building of the image and the setup of the yml files.

#### Maintaining Local Device Lists

After the project was containerized, I ran into a problem with maintaining the list of local device IDs and friendly names. This led to something I wanted to experiment with anyway: using a dynamic configuration.  Initially the python scripts would periodically re-read in the json file containing this information; after containerization, this was placed in a mounted volume.  But updates were still klunky.  

I then modified the system so that the local sensors were published to their own name space, and any updates to that would cause an update to the running config for local_sensors.  The topic for this is: 

``` text
KTBMES/sensors/config/local_sensors
```

(no <host>).  When each running system receives an update via this topic, it updates its own 'site' config:

``` text
KTBMES/<host>/sensors/config/local_sensors
```

The only purpose of this site-specific topic is to confirm the updates in a human-readable format.

### Shelly Smart Plugs

The Shelly Smart Plugs can be configured to publish data via MQTT.  Like with the RTL_433 software, the Shelly devices are configured to publish their raw data to their own name space.  The topic structure for this raw data looks like this:

``` text
Shelly/<shelly_device_name>/...
```

where '<shelly_device_name>' is the network name configured into the device.  The '...' represents various attributes of the device, such as:

``` text
Shelly/<shelly_device_name>/events
Shelly/<shelly_device_name>/status
Shelly/<shelly_device_name>/online
```

The Python scripts (shelly_main.py et. al.) subscribe to these raw topics, and republish the data into the KTBMES name space.  The republished topic structure looks like this:

``` text
KTBMES/<host>/<room>/smartplugs/<shelly_plug_name>/online
KTBMES/<host>/<room>/smartplugs/<shelly_plug_name>/rpc
KTBMES/<host>/<room>/smartplugs/<shelly_plug_name>/switch:0
```

(note that the plugs I'm using only have a single switch, so the attribute is 'switch:0')

The logic in the Shelly scripts is a lot simpler than the weather sensor scripts, as we are only seeing data from our own specific devices; so there is no need to filter out 'other' devices.

The <room> attribute is analogous to the 'area' level of the ISA-95 hierarchy.

## Visualization

At the moment I'm only using Node-RED dashboards to visualize this.  If the Node-RED flows aren't included in this repository yet, the plan is to include them soon.

---

That's the basic setup! This has been a fun project to learn about UNS architecture and MQTT patterns. Feel free to reach out if you have questions or want to chat about the design decisions I made.

## A Word about ...

Most of this was vibe-coded.  

The IDE was VS Code, with a Claude Sonnet backend.

It's not that I don't know Python - I just wasn't that experienced with object-oriented programming, and working with CoPilot allowed me to explore some different ways of doing this.  The project was refactored a number of times as I learned more about both the problem domain and Python itself.

While a functional style might have been more efficient and quicker to develop, the object-oriented approach allowed me to reuse a lot of the code between the two different data sources (weather sensors vs smart plugs), and made it easier to extend the project in the future.

Constructive comments are welcome!  My coding career started in the 70's, and I still have my initial pair of asbestos undies, so if you must flame, I think I can handle it.  :)

