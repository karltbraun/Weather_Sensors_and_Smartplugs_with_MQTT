# Quick Reference: Multi-Host MQTT Deployment

## 🏗️ **Architecture Overview**

This system uses host-based networking by default for all deployments, providing optimal performance and simplified configuration. Bridge networking is available as an explicit option when needed.

### Default Configuration (All Hosts)
```bash
# Docker Networking (DEFAULT for all hosts)
network_mode: host    # Direct host network access

# Environment
PUB_SOURCE=<hostname>     # Mu, ROSA, TWIX, VULTR2, etc.
PUB_TOPIC_ROOT=KTBMES    # Root MQTT topic
MQTT_BROKER_PORT=1883
```

---

## 🏠 **Home Lab Hosts** (ROSA, TWIX, Mu)

### Configuration Summary
```bash
# Environment
DEPLOYMENT_SCENARIO=home-lab
MQTT_BROKER_ADDRESS=n-vultr2  # Remote broker hostname or IP
PUB_SOURCE=ROSA              # or TWIX, Mu, etc.

# Docker Networking
network_mode: host            # DEFAULT - uses host network directly
```

### Firewall Requirements
- **Vultr VM**: Allow TCP/1883 from your home ISP IP
- **Command**: `sudo ufw allow from YOUR.HOME.IP to any port 1883`

### Stack File Generation
```bash
# Generate all home lab stacks
./generate-portainer-stacks.sh --all

# Generate specific hosts
./generate-portainer-stacks.sh --ROSA --TWIX

# Default stack (Mu)
./generate-portainer-stacks.sh   # Creates portainer-stack.yml
```

### Portainer Deployment
```yaml
# In portainer-stack-rosa.yml (or twix.yml):
services:
  republish-sensors:
    network_mode: host          # Host networking (default)
    environment:
      - MQTT_BROKER_ADDRESS=n-vultr2
      - PUB_SOURCE=ROSA         # Host identifier
      - DEPLOYMENT_SCENARIO=home-lab
    # No networks: section needed with host mode
```

---

## ☁️ **Vultr VM Deployment** (Co-located with MQTT broker)

### Configuration Summary
```bash
# Environment  
DEPLOYMENT_SCENARIO=vultr-vm
MQTT_BROKER_ADDRESS=localhost    # Broker on same host
PUB_SOURCE=VULTR2

# Docker Networking
network_mode: host              # DEFAULT - localhost communication
```

### Firewall Requirements
- **None** (all localhost communication)
- External access only needed for remote clients connecting to broker

### Stack File Generation
```bash
# Generate Vultr VM stack
./generate-portainer-stacks.sh --VULTR2
```

### Portainer Deployment
```yaml
# In portainer-stack-vultr2.yml:
services:
  republish-sensors:
    network_mode: host          # Host networking (default)
    environment:
      - MQTT_BROKER_ADDRESS=localhost
      - PUB_SOURCE=VULTR2
      - DEPLOYMENT_SCENARIO=vultr-vm
```

---

## 🔧 **Custom Host Deployment**

### Generate Custom Stack
```bash
# Create stack for any hostname
./generate-portainer-stacks.sh --pub_source=MyHost

# This creates: portainer-stack-myhost.yml
# With: PUB_SOURCE=MyHost, host networking
```

### Bridge Networking (Optional)
```bash
# Explicitly request bridge networking if needed
./generate-portainer-stacks.sh --pub_source=MyHost --network_mode=bridge

# Note: Bridge mode requires additional network configuration
```

---

## 🔄 **Tailscale Alternative** (For Home Lab)

### Using Tailscale for Secure Remote Access
```bash
# 1. Install Tailscale on both home lab and Vultr VM
curl -fsSL https://tailscale.com/install.sh | sh

# 2. Get Vultr VM Tailscale IP
tailscale ip -4
# Example output: 100.x.x.x

# 3. Configure home lab to use Tailscale IP
MQTT_BROKER_ADDRESS=100.x.x.x  # Use in .env or stack file

# 4. Update Vultr firewall (allow Tailscale subnet)
sudo ufw allow from 100.64.0.0/10 to any port 1883

# 5. No changes to networking mode needed - host mode works with Tailscale
```

### Benefits
- Encrypted traffic without VPN configuration
- No public IP exposure required
- Works with host or bridge networking
- Automatic route management

---

## 📊 **Stack File Management**

### Understanding the Template System

The project uses a template-based approach to avoid configuration duplication:

```bash
# Template file (single source of truth)
portainer-stack.template.yml

# Generated files (deployment-specific)
portainer-stack.yml              # Default (Mu) with host networking
portainer-stack-rosa.yml         # ROSA host with host networking
portainer-stack-twix.yml         # TWIX host with host networking
portainer-stack-vultr2.yml       # VULTR2 VM with host networking
```

### Key Generation Options

```bash
# Standard hosts (creates all three)
./generate-portainer-stacks.sh --all

# Individual hosts
./generate-portainer-stacks.sh --ROSA
./generate-portainer-stacks.sh --TWIX
./generate-portainer-stacks.sh --VULTR2

# Custom host (auto-lowercases filename)
./generate-portainer-stacks.sh --pub_source=MyNewHost
# Creates: portainer-stack-mynewhost.yml

# Custom with bridge networking (not recommended)
./generate-portainer-stacks.sh --pub_source=Test --network_mode=bridge

# Multiple at once
./generate-portainer-stacks.sh --ROSA --TWIX --pub_source=NewHost
```

### Validation
```bash
# Test all generated files
./test-stack-generation.sh

# Expected output: 14/14 tests PASSED
# Validates:
#   - Correct PUB_SOURCE values
#   - Host networking configuration
#   - No commented PUB_SOURCE alternatives
#   - Proper file structure
```

---

## 🚀 **Quick Deploy Commands**

### Home Lab (ROSA, TWIX, Mu)
```bash
# 1. Generate stack file for your host
./generate-portainer-stacks.sh --ROSA    # or --TWIX for TWIX

# 2. Build Docker image (if not already built)
./build-and-push.sh -v latest

# 3. Deploy via Portainer Web UI:
#    - Stacks → Add Stack → Web Editor
#    - Copy content from portainer-stack-rosa.yml (or appropriate file)
#    - Verify MQTT_BROKER_ADDRESS is set correctly
#    - Deploy stack

# Stack uses host networking by default - no additional network config needed
```

### Vultr VM
```bash
# 1. Generate stack file
./generate-portainer-stacks.sh --VULTR2

# 2. Build or pull Docker image
./build-and-push.sh -v latest

# 3. Deploy via Portainer:
#    - Copy content from portainer-stack-vultr2.yml
#    - Verify MQTT_BROKER_ADDRESS=localhost
#    - Deploy stack

# All traffic stays on localhost with host networking
```

### Testing New Configuration
```bash
# Generate and test all stack files
./generate-portainer-stacks.sh --all
./test-stack-generation.sh

# All 14 tests should pass
```

---

## 🔧 **Testing Connectivity**

### Network Mode Verification
```bash
# Check container network mode
docker inspect <container_name> | grep NetworkMode

# Expected: "NetworkMode": "host"
```

### From Home Lab Machine
```bash
# Set your MQTT broker hostname
MQTT_BROKER=n-vultr2

# Test DNS resolution
nslookup $MQTT_BROKER
ping -c 3 $MQTT_BROKER

# Test MQTT port accessibility
telnet $MQTT_BROKER 1883
# or
nc -zv $MQTT_BROKER 1883

# Test from container (host networking)
docker run --rm --network host weather-sensors:latest \
  sh -c "nc -zv $MQTT_BROKER 1883"
```

### From Vultr VM
```bash
# Test local MQTT broker
telnet localhost 1883
nc -zv localhost 1883

# Check mosquitto is running
sudo systemctl status mosquitto

# Test from container (host networking)
docker run --rm --network host weather-sensors:latest \
  sh -c "nc -zv localhost 1883"
```

### Container Health Check
```bash
# View container logs
docker logs <container_name> --tail 50 --follow

# Check container status
docker ps --filter name=<container_name>

# Execute commands in running container
docker exec -it <container_name> bash

# Test MQTT connectivity from inside container
docker exec <container_name> nc -zv localhost 1883
```

---

## 📊 **Monitoring in Portainer**

### Health Checks
- **Green**: Service running, log files created
- **Yellow**: Starting up (30s grace period)
- **Red**: Failed health check

### Log Monitoring
1. **Containers** → Select container → **Logs** tab
2. Enable **Auto-refresh** for real-time monitoring
3. Look for MQTT connection messages

### Common Log Messages
```
✓ MQTT broker is reachable              # Good connection
⚠ Cannot reach MQTT broker              # Check firewall/config
Starting RTL-433 Sensor Data...         # Service starting
Main: Loop: Processing X messages       # Processing data
```

---

## 🚨 **Troubleshooting Quick Fixes**

### MQTT Connection Failed
```bash
# 1. Verify broker is running
sudo systemctl status mosquitto

# 2. Check firewall rules (on Vultr VM)
sudo ufw status numbered
sudo ufw allow from YOUR.HOME.IP to any port 1883

# 3. Test connectivity from source
telnet MQTT_BROKER_IP 1883

# 4. Check container network mode
docker inspect <container_name> | grep NetworkMode

# 5. Verify environment variables
docker exec <container_name> env | grep MQTT
```

### Container Won't Start
```bash
# Check container logs for errors
docker logs <container_name>

# Common issues:
# - MQTT_BROKER_ADDRESS not set or incorrect
# - PUB_TOPIC_ROOT not configured
# - Network connectivity issues

# Test configuration locally
python republish_processed_sensors_main.py
```

### Configuration Not Updating
```bash
# 1. Check MQTT topic is correct
echo $MQTT_TOPIC_LOCAL_SENSORS_UPDATES

# 2. Verify config file permissions
docker exec <container_name> ls -la config/

# 3. Check for backup files (confirms updates are being received)
docker exec <container_name> ls -la config/*.backup.*

# 4. Monitor logs during config update
docker logs -f <container_name>

# 5. Manually trigger config update
mosquitto_pub -h $MQTT_BROKER \
  -t "KTBMES/sensors/config/local_sensors/update" \
  -m '{"12345":{"sensor_name":"Test","id_sensor_name":"test","comment":"test"}}'
```

### Permission Issues
```bash
# Check volume permissions
docker volume inspect weather-sensors-data

# Fix permissions (from host)
sudo chown -R 1000:1000 /path/to/volume

# Reset volume if needed (WARNING: deletes data)
docker volume rm weather-sensors-data
```

### Host Networking Not Working
```bash
# Verify host networking is enabled
docker inspect <container_name> --format='{{.HostConfig.NetworkMode}}'
# Should show: host

# Check if port is available on host
sudo netstat -tlnp | grep 1883

# Test connectivity without Docker
telnet localhost 1883

# Regenerate stack file with correct settings
./generate-portainer-stacks.sh --ROSA  # or appropriate host
```

### DNS Resolution Issues
```bash
# Check DNS from container
docker exec <container_name> nslookup n-vultr2

# Check /etc/hosts
docker exec <container_name> cat /etc/hosts

# Test with IP address instead of hostname
MQTT_BROKER_ADDRESS=123.45.67.89  # Use actual IP
```

---

## 🔧 **Dynamic Sensor Configuration via MQTT**

### Overview
The system supports dynamic updates to local sensor configurations through MQTT messages, allowing real-time changes without container restarts.

### Configuration
```bash
# Environment variables (required)
MQTT_TOPIC_LOCAL_SENSORS_UPDATES="KTBMES/sensors/config/local_sensors/update"  # Note: singular 'update'
MQTT_TOPIC_LOCAL_SENSORS_CURRENT="KTBMES/sensors/config/local_sensors/current"  # Not directly set, derived from PUB_TOPIC_ROOT
CONFIG_SUBSCRIBE_TIMEOUT=10  # Timeout in seconds for startup config subscription

# Backup retention settings (optional, defaults shown)
MAX_BACKUPS=10
BACKUP_RETENTION_DAYS=30
```

### MQTT Topics

#### Topic Structure
- `<root>` = Value from `PUB_TOPIC_ROOT` environment variable (e.g., "KTBMES")
- `<host>` = Value from `PUB_SOURCE` environment variable (e.g., "ROSA", "TWIX", "Mu", "VULTR2")

**Update Topic** (Global - Subscribe):
```
<root>/sensors/config/local_sensors/update
```
- **Purpose**: Receive configuration updates from external sources
- **Direction**: Subscribe only
- **Default**: `KTBMES/sensors/config/local_sensors/update`
- **Usage**: Publish sensor configuration updates to this topic to update all listening services
- **Retained**: No (updates are processed once when received)

**Global Current Topic** (Subscribe at startup):
```
<root>/sensors/config/local_sensors/current
```
- **Purpose**: Retrieve last known configuration at service startup
- **Direction**: Subscribe (temporary, at startup only)
- **Default**: `KTBMES/sensors/config/local_sensors/current`
- **Usage**: Service subscribes briefly at startup, unsubscribes after receiving retained message or timeout
- **Retained**: Yes (last configuration persisted on broker)
- **Timeout**: Controlled by `CONFIG_SUBSCRIBE_TIMEOUT` (default: 10 seconds)

**Host-Specific Current Topic** (Publish):
```
<root>/<host>/sensors/config/local_sensors/current
```
- **Purpose**: Publish current configuration from this specific host
- **Direction**: Publish only (with retain=True)
- **Example**: `KTBMES/ROSA/sensors/config/local_sensors/current`
- **Usage**: Each host publishes its active config here after startup and after any updates
- **Retained**: Yes (persists on broker for monitoring and debugging)

**Topic Examples**:
```bash
# Update topic (all hosts subscribe)
KTBMES/sensors/config/local_sensors/update

# Global current (startup sync)
KTBMES/sensors/config/local_sensors/current

# Host-specific current (each host publishes)
KTBMES/ROSA/sensors/config/local_sensors/current
KTBMES/TWIX/sensors/config/local_sensors/current
KTBMES/VULTR2/sensors/config/local_sensors/current
```

### Configuration Flow

#### 1. Startup Sequence
```
1. Load initial config from config/local_sensors.json file
2. Connect to MQTT broker
3. Subscribe to <root>/sensors/config/local_sensors/current (global retained)
4. Wait CONFIG_SUBSCRIBE_TIMEOUT seconds for retained config message
5. If received and valid:
   - Update in-memory configuration
   - Write to config/local_sensors.json
   - Create backup of previous config
6. Publish current config to <root>/<host>/sensors/config/local_sensors/current (retained)
7. Unsubscribe from global current topic
8. Subscribe to <root>/sensors/config/local_sensors/update for runtime updates
9. Continue normal operation
```

#### 2. Runtime Updates (via /update topic)
```
1. Receive message on <root>/sensors/config/local_sensors/update
2. Validate JSON payload structure
3. Create timestamped backup of current config/local_sensors.json
4. Update in-memory configuration (complete replacement)
5. Write new config to config/local_sensors.json file
6. Publish updated config to <root>/<host>/sensors/config/local_sensors/current (retained)
7. Refresh device names in device registry
8. Continue processing with new configuration
```

#### 3. Configuration Validation
- JSON syntax must be valid
- Each sensor must have required fields: `sensor_name`, `id_sensor_name`
- Optional field: `comment`
- Invalid configs are rejected with error logging
- System continues with previous valid configuration on failure

**Payload Structure**:
```json
{
  "device_id_1": {
    "sensor_name": "Sensor Name",
    "id_sensor_name": "device_id_1_sensor_name",
    "comment": "Optional description"
  },
  "device_id_2": {
    "sensor_name": "Another Sensor",
    "id_sensor_name": "device_id_2_another_sensor",
    "comment": "Optional description"
  }
}
```

### Update Behavior

#### **Replace Mode** (Always Used)
The system always performs a complete replacement of the sensor configuration:

- **Replaces entire configuration**: All sensors not in the payload are removed
- **Validates before applying**: Checks all required fields exist
- **Creates automatic backup**: Timestamped backup before each update
- **Atomic operation**: Either all changes apply or none (rollback on error)
- **Device registry update**: Refreshes all device names after successful update

**Important**: This is a destructive operation. Always include all sensors you want to keep in the update payload.

#### Configuration Structure
```json
{
  "device_id_1": {
    "sensor_name": "Human-Readable Name",
    "id_sensor_name": "device_id_1_machine_name",
    "comment": "Optional description"
  },
  "device_id_2": {
    "sensor_name": "Another Sensor",
    "id_sensor_name": "device_id_2_machine_name",
    "comment": "Optional description"
  }
}
```

**Required Fields** (per sensor):
- `sensor_name`: Human-readable sensor name
- `id_sensor_name`: Machine-readable identifier (used in topics)

**Optional Fields**:
- `comment`: Description or notes about the sensor

### Example MQTT Messages

#### Complete Configuration Update
```bash
# Using mosquitto_pub to update all sensors
mosquitto_pub -h your-mqtt-broker -p 1883 \
  -t "KTBMES/sensors/config/local_sensors/update" \
  -m '{
    "12345": {
      "sensor_name": "Living Room Temp",
      "id_sensor_name": "living_room",
      "comment": "Living Room Temperature Sensor"
    },
    "67890": {
      "sensor_name": "Outdoor Weather",
      "id_sensor_name": "outdoor",
      "comment": "Back Yard Weather Station"
    },
    "11111": {
      "sensor_name": "Kitchen Sensor",
      "id_sensor_name": "kitchen",
      "comment": "Kitchen Temperature"
    }
  }'
```

#### Adding a Single Sensor (Must Include All Existing Sensors)
```bash
# WARNING: This replaces entire config, not just adding
# Include ALL existing sensors plus the new one
mosquitto_pub -h your-mqtt-broker -p 1883 \
  -t "KTBMES/sensors/config/local_sensors/update" \
  -m '{
    "12345": {"sensor_name": "Living Room", "id_sensor_name": "living_room", "comment": "Existing"},
    "67890": {"sensor_name": "Outdoor", "id_sensor_name": "outdoor", "comment": "Existing"},
    "99999": {"sensor_name": "New Sensor", "id_sensor_name": "new_sensor", "comment": "Newly Added"}
  }'
```

#### Minimal Configuration (Removing All But One)
```bash
# This will REMOVE all sensors except the one specified
mosquitto_pub -h your-mqtt-broker -p 1883 \
  -t "KTBMES/sensors/config/local_sensors/update" \
  -m '{
    "12345": {
      "sensor_name": "Only Sensor",
      "id_sensor_name": "only_sensor",
      "comment": "All others removed"
    }
  }'
```

#### Using Python Script
```python
#!/usr/bin/env python3
import json
import paho.mqtt.publish as publish

sensors = {
    "12345": {
        "sensor_name": "Living Room",
        "id_sensor_name": "living_room",
        "comment": "Main temperature sensor"
    },
    "67890": {
        "sensor_name": "Outdoor",
        "id_sensor_name": "outdoor",
        "comment": "Weather station"
    }
}

publish.single(
    topic="KTBMES/sensors/config/local_sensors/update",
    payload=json.dumps(sensors),
    hostname="your-mqtt-broker",
    port=1883
)
```

#### Check Current Configuration
```bash
# Subscribe to host-specific current topic to see active config
mosquitto_sub -h your-mqtt-broker -p 1883 \
  -t "KTBMES/ROSA/sensors/config/local_sensors/current" \
  -v

# Or subscribe to all host configurations
mosquitto_sub -h your-mqtt-broker -p 1883 \
  -t "KTBMES/+/sensors/config/local_sensors/current" \
  -v
```

### Using MQTT Explorer
1. Connect to your MQTT broker
2. Navigate to the updates topic: `KTBMES/sensors/config/local_sensors/updates`
3. Publish a JSON payload with the complete sensor configuration
4. The system will process the update and publish the new config to the 'current' topic
5. Check container logs for confirmation

### Backup & Recovery

**Automatic Backups**:
- Created before every configuration update
- Stored in `config/` directory with timestamp
- Format: `local_sensors.json.backup.YYYYMMDD_HHMMSS`

**Retention Policy**:
- Keeps last 10 backups (configurable)
- Removes backups older than 30 days (configurable)
- Automatic cleanup after each backup creation

**Manual Recovery**:
```bash
# List available backups
ls config/*.backup.*

# Restore from backup
cp config/local_sensors.json.backup.20251110_143022 config/local_sensors.json

# Restart container to reload
docker restart your-container-name
```

### Validation & Error Handling

**Payload Validation**:
- JSON syntax must be valid (proper structure, quotes, commas)
- Must be a dictionary/object with device IDs as keys
- Each sensor object must contain `sensor_name` and `id_sensor_name` fields
- `comment` field is optional
- Empty configurations are valid (removes all sensors)

**Error Responses**:
- Configuration errors are logged in container logs with detailed messages
- Invalid payloads are rejected with descriptive error messages
- System continues operating with previous configuration on failure
- Failed updates do not create backup files

**Common Validation Errors**:
```bash
# Invalid JSON
Error: Invalid JSON syntax in config payload

# Missing required field
Error: Sensor '12345' missing required field 'sensor_name'

# Wrong data type
Error: Sensor configuration must be a dictionary

# File write failure
Error: Failed to write config file: Permission denied
```

**Validation Success Indicators**:
```bash
# In logs
INFO: Config update successful: Updated 3 sensors
INFO: Created backup: config/local_sensors.json.backup.20241230_143022
INFO: Published current config to KTBMES/ROSA/sensors/config/local_sensors/current
```

### Testing the Configuration

1. **Check current sensors**:
   ```bash
   docker exec -it container-name cat config/local_sensors.json
   ```

2. **Monitor logs during update**:
   ```bash
   docker logs -f container-name
   ```

3. **Verify backup creation**:
   ```bash
   docker exec -it container-name ls -la config/*.backup.*
   ```

### Troubleshooting

**Common Issues**:
- **Topic not configured**: Ensure `MQTT_TOPIC_LOCAL_SENSORS_UPDATES` environment variable is set
- **Invalid JSON**: Validate payload syntax before publishing
- **Permission errors**: Check container file system permissions
- **Network issues**: Verify MQTT broker connectivity

**Debug Commands**:
```bash
# Check environment variables
docker exec container-name env | grep TOPIC

# Test MQTT connectivity
docker exec container-name mosquitto_pub -h mqtt-broker -t test -m "hello"

# Check file permissions
docker exec container-name ls -la config/
```