# Weather Sensors and Smart Plugs with MQTT

A Python-based MQTT processing system for aggregating RTL-433 sensor data and Shelly smart plug readings into structured JSON payloads. Supports dynamic configuration updates via MQTT and flexible deployment across multiple hosts.

These are really two separate projects, but they use a common set of python scripts (which I have yet to package into a library).

The first project processes RTL-433 sensor data published to MQTT as flat topics (one topic per attribute) and republishes them as JSON device records, aggregating multiple attributes per device. 

The second project processes Shelly smart plug data, flattening the JSON payloads and republishing individual attributes to flat MQTT topics with room associations.

See the [MQTT Topics](#mqtt-topics) section below for detailed information on topic structure and conventions. This will clarify some of the environment variables defined below.

## 🚀 Features

- **RTL-433 Sensor Processing**: Aggregates individual sensor attributes into unified device records
- **Shelly Smart Plug Integration**: Processes and republishes smart plug data with room associations
- **Dynamic Configuration**: Update sensor definitions via MQTT without restarts
- **Multi-Host Deployment**: Support for deployments via 
  - (1) hosts separate from the MQTT Broker host ("home-lab") and 
  - (2) deployments on the same cloud-hosted VM as the MQTT Broker ("vultr-vm")
- **Protocol Management**: Automatic RTL-433 device protocol identification and categorization
- **Flexible Networking**: Bridge and host network modes for different deployment scenarios
- **Comprehensive Logging**: Configurable logging levels for console and file output
- **Docker Ready**: Containerized deployment with Portainer stack support

## 📋 Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Architecture](#architecture)
- [Deployment](#deployment)
- [MQTT Topics](#mqtt-topics)
- [Development](#development)
- [Documentation](#documentation)
- [License](#license)

## 🔧 Requirements

- **Python**: 3.12 or higher
- **Docker**: For containerized deployment
- **MQTT Broker**: Mosquitto or compatible broker
- **RTL-433**: For receiving sensor data (separate installation)

### Python Dependencies

```
paho-mqtt>=2.1.0
python-dotenv>=1.0.1
```

See [requirements.txt](requirements.txt) for exact versions.

## 📦 Installation

### Local Development

#### Standard pip setup

```bash
# Clone the repository
git clone https://github.com/karltbraun/Weather_Sensors_and_Smartplugs_with_MQTT.git
cd Weather_Sensors_and_Smartplugs_with_MQTT

# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.template .env
# Edit .env with your configuration
```

#### uv environment management setup

[uv](https://docs.astral.sh/uv/) is a fast Python package installer and environment manager. It's recommended for faster dependency installation.

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/karltbraun/Weather_Sensors_and_Smartplugs_with_MQTT.git
cd Weather_Sensors_and_Smartplugs_with_MQTT

# Create virtual environment and install dependencies
uv venv --python 3.12
source .venv/bin/activate

# Install dependencies with uv
uv pip install -r requirements.txt

# Copy environment template
cp .env.template .env
# Edit .env with your configuration
```

### Docker Deployment

```bash
# Build image
docker build -t weather-sensors:latest .

# Or use provided script with version tagging
./build-and-push.sh -v 1.0.0
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file from the template:

```bash
# MQTT Broker Configuration
MQTT_BROKER_ADDRESS=localhost        # Broker hostname or IP
MQTT_BROKER_PORT=1883               # Default MQTT port
PUB_TOPIC_ROOT=KTBMES               # Root topic for all messages
PUB_SOURCE=Mu                        # Host identifier (Mu, ROSA, TWIX, VULTR2)

# Subscription Topics (comma-separated)
SUB_TOPICS_SENSORS=KTBMES/raw/#     # RTL-433 sensor topics
SUB_TOPICS_SHELLY=shellies/#        # Shelly device topics

# Logging Configuration
CONSOLE_LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR
FILE_LOG_LEVEL=DEBUG
CLEAR_LOG_FILE=True                 # Clear logs on startup

# Publishing Configuration
PUBLISH_INTERVAL_MAX=300            # Max seconds between republishing

# Configuration Update Topics
MQTT_TOPIC_LOCAL_SENSORS=KTBMES/sensors/config/local_sensors
CONFIG_SUBSCRIBE_TIMEOUT=10         # Timeout for startup config subscription

# Backup Settings
MAX_BACKUPS=10                      # Maximum config backup files
BACKUP_RETENTION_DAYS=30            # Days to retain backups

# Deployment
DEPLOYMENT_SCENARIO=home-lab        # home-lab or vultr-vm
```

### Sensor Configuration

Edit `config/local_sensors.json` to define known sensors:

```json
{
  "12345": {
    "sensor_name": "Living Room",
    "id_sensor_name": "living_room",
    "comment": "Temperature and humidity sensor"
  },
  "67890": {
    "sensor_name": "Outdoor",
    "id_sensor_name": "outdoor",
    "comment": "Weather station"
  }
}
```

## 🎯 Usage

### Running Locally

#### RTL-433 Sensor Processor
```bash
python republish_processed_sensors_main.py
```

#### Shelly Smart Plug Processor
```bash
python shelly_main.py
```

### Running in Docker

```bash
# Using docker-compose
docker-compose up -d

# Using Portainer
# 1. Generate appropriate stack file
./generate-portainer-stacks.sh --ROSA    # or --TWIX, --VULTR2

# 2. Deploy via Portainer Web UI
# Copy content from generated file to Portainer stack editor
```

### Updating Sensor Configuration via MQTT

```bash
# Using mosquitto_pub
mosquitto_pub -h your-broker \
  -t "KTBMES/sensors/config/local_sensors" \
  -m '{
    "12345": {
      "sensor_name": "Kitchen",
      "id_sensor_name": "kitchen",
      "comment": "Kitchen sensor"
    }
  }'
```

## 🏗️ Architecture

### Project Structure

```
.
├── republish_processed_sensors_main.py  # Main RTL-433 processor
├── shelly_main.py                       # Shelly device processor
├── src/
│   ├── managers/                        # Core management classes
│   │   ├── mqtt_manager.py             # MQTT client management
│   │   ├── device_manager.py           # Device state management
│   │   ├── local_sensor_manager.py     # Sensor configuration
│   │   ├── protocol_manager.py         # RTL-433 protocol handling
│   │   ├── message_manager_*.py        # Message processing
│   │   ├── config_file_manager.py      # Config file monitoring
│   │   └── data_repository_manager.py  # Data persistence
│   └── utils/                           # Utility functions
│       ├── misc_utils.py               # Configuration utilities
│       ├── logger_setup.py             # Logging configuration
│       ├── mqtt_broker_check.py        # Connectivity checking
│       └── flatten_json.py             # JSON flattening
├── config/                              # Configuration files
│   ├── local_sensors.json              # Sensor definitions
│   ├── rtl_433_protocols.json          # Protocol mappings
│   └── protocol_categories.json        # Protocol categorization
├── data/                                # Data persistence
└── logs/                                # Application logs
```

### Data Flow

#### RTL-433 Sensor Processing
```
RTL-433 → MQTT (flat topics)
  ↓
Message Manager
  ↓
Device Registry (aggregation)
  ↓
MQTT (JSON payloads) + File persistence
```

#### Shelly Device Processing
```
Shelly Devices → MQTT (JSON)
  ↓
Message Manager (flatten)
  ↓
MQTT (flat topics by attribute)
```

## 🚀 Deployment

### Deployment Scenarios

#### Home Lab (ROSA/TWIX hosts)
- **Network Mode**: Bridge
- **Broker**: Remote (Vultr VM or other)
- **Stack Files**: `portainer-stack-rosa.yml`, `portainer-stack-twix.yml`

```bash
# Generate stack
./generate-portainer-stacks.sh --ROSA

# Configuration
MQTT_BROKER_ADDRESS=n-vultr2
DEPLOYMENT_SCENARIO=home-lab
```

#### Vultr VM (Same host as broker)
- **Network Mode**: Host
- **Broker**: Localhost
- **Stack File**: `portainer-stack-vultr2.yml`

```bash
# Generate stack
./generate-portainer-stacks.sh --VULTR2

# Configuration
MQTT_BROKER_ADDRESS=localhost
DEPLOYMENT_SCENARIO=vultr-vm
```

### Generating Stack Files

The project uses a template-based system for Portainer stack generation:

```bash
# Generate all standard stacks
./generate-portainer-stacks.sh --all

# Generate specific hosts
./generate-portainer-stacks.sh --ROSA --TWIX --VULTR2

# Generate custom stack
./generate-portainer-stacks.sh --pub_source=MyHost
```

See [PORTAINER_STACKS.md](PORTAINER_STACKS.md) for detailed documentation.

## 📡 MQTT Topics

### Topic Structure and Conventions

#### RTL-433 Topic Structure Breakdown
- **Base Topic**: `KTBMES/raw/`
- **Device ID**: Unique identifier for each sensor (e.g., `12345`)
- **Attributes**: Sensor data attributes (e.g., `temperature_C`, `humidity`)

#### Shelly Topic Structure Breakdown
- **Base Topic**: `shellies/`
- **Device ID**: Unique identifier for each Shelly device
- **Attributes**: Flattened JSON attributes (e.g., `power`, `energy`)

#### PUB_TOPIC_ROOT Usage
- All published topics share a common root defined by `PUB_TOPIC_ROOT`
- Example: If `PUB_TOPIC_ROOT=KTBMES`, the full topic for a device would be `KTBMES/devices/12345`

#### PUB_SOURCE Identifier Usage
- `PUB_SOURCE` is used to distinguish messages from different hosts
- Appears in the topic hierarchy, e.g., `KTBMES/Mu/sensors/config/local_sensors`

#### Topic Hierarchy Explanation
- Topics are hierarchical, using slashes (`/`) to separate levels
- Example: `KTBMES/raw/12345/temperature_C` indicates the temperature_C attribute of the device with ID 12345

### RTL-433 Sensor Topics

**Subscribe** (input - flat attributes):
```
KTBMES/raw/12345/temperature_C
KTBMES/raw/12345/humidity
KTBMES/raw/12345/battery_ok
```

**Publish** (output - JSON device):
```
KTBMES/devices/12345
Payload: {
  "device_id": "12345",
  "device_name": "Living Room",
  "temperature_C": 23.5,
  "temperature_F": 74.3,
  "humidity": 45,
  "battery_ok": 1,
  "protocol_id": "40",
  "protocol_name": "Acurite-606TX",
  "time_last_seen_iso": "2024-12-30T10:30:00"
}
```

### Shelly Device Topics

**Subscribe** (input - JSON payloads):
```
shellies/1234567890
```

**Publish** (output - flat attributes):
```
KTBMES/shelly/1234567890/power
KTBMES/shelly/1234567890/energy
KTBMES/shelly/1234567890/temperature
```

### Configuration Topics

**Update Topic** (subscribe):
```
KTBMES/sensors/config/local_sensors
```

**Current Config Topic** (publish, retained):
```
KTBMES/Mu/sensors/config/local_sensors
KTBMES/ROSA/sensors/config/local_sensors
```

See [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for complete topic documentation.

## 👨‍💻 Development

### Running Tests

```bash
# Test stack generation
./test-stack-generation.sh

# Manual testing
python -m pytest tests/
```

### Code Style

The project follows PEP 8 with comprehensive docstrings:

```python
def function_name(param: str) -> bool:
    """Brief description.
    
    Detailed description if needed.
    
    Args:
        param: Parameter description.
    
    Returns:
        Return value description.
    
    Raises:
        ValueError: When error occurs.
    """
```

### Building Docker Images

```bash
# Build and tag
./build-and-push.sh -v 1.0.0

# Push to registry (if configured)
docker push your-registry/weather-sensors:1.0.0
```

## 📚 Documentation

- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)**: Quick start guide and common operations
- **[PORTAINER_STACKS.md](PORTAINER_STACKS.md)**: Stack file generation and deployment
- **[DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)**: Docker deployment details
- **[000 README.md](000%20README.md)**: Development notes and current status

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👤 Author

**Karl Braun**
- Email: karl@ktb.dev
- GitHub: [@karltbraun](https://github.com/karltbraun)

## 🙏 Acknowledgments

- RTL-433 project for sensor decoding
- Shelly for smart plug devices
- Paho MQTT for Python MQTT client
- The open-source community

## 📊 Project Status

**Status**: Active Development  
**Version**: 0.1.0  
**Python**: 3.12+  
**Last Updated**: December 30, 2024

---

For issues and feature requests, please use the [GitHub Issues](https://github.com/karltbraun/Weather_Sensors_and_Smartplugs_with_MQTT/issues) page.
