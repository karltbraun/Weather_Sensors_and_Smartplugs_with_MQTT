# Quick Reference: Vultr VM + Firewall Deployment

## 🏠 **Home Lab Deployment** (Lab machines → Vultr VM MQTT)

### Configuration Summary
```bash
# Environment
DEPLOYMENT_SCENARIO=home-lab
MQTT_BROKER_ADDRESS=n-vultr2  # Public IP or hostname
MQTT_BROKER_PORT=1883

# Docker Networking
network_mode: bridge (default)
networks: weather-sensors
```

### Firewall Requirements
- **Vultr VM**: Allow TCP/1883 from your home ISP IP
- **Command**: `sudo ufw allow from YOUR.HOME.IP to any port 1883`

### Portainer Stack Changes
```yaml
# In portainer-stack.yml services:
environment:
  - MQTT_BROKER_ADDRESS=n-vultr2  # DNS name (preferred) or IP address
  - DEPLOYMENT_SCENARIO=home-lab
networks:
  - weather-sensors  # Keep this
# Leave network_mode commented out
```

---

## ☁️ **Vultr VM Deployment** (Same VM as MQTT broker)

### Configuration Summary
```bash
# Environment  
DEPLOYMENT_SCENARIO=vultr-vm
MQTT_BROKER_ADDRESS=localhost
MQTT_BROKER_PORT=1883

# Docker Networking
network_mode: host
# No networks section needed
```

### Firewall Requirements
- **None** (all localhost communication)

### Portainer Stack Changes
```yaml
# In portainer-stack.yml services:
network_mode: host  # UNCOMMENT THIS
environment:
  - MQTT_BROKER_ADDRESS=localhost
  - DEPLOYMENT_SCENARIO=vultr-vm
# REMOVE networks: section entirely
```

---

## 🔄 **Tailscale Alternative** (For Home Lab)

### If Using Tailscale Network
```bash
# Get Vultr VM Tailscale IP
tailscale ip -4

# Use in configuration
MQTT_BROKER_ADDRESS=100.x.x.x  # Tailscale IP

# Vultr firewall
sudo ufw allow from 100.64.0.0/10 to any port 1883
```

---

## 🚀 **Quick Deploy Commands**

### Home Lab
```bash
# Build image
docker build -t weather-sensors:latest .

# Copy appropriate environment
cp .env.home-lab .env
# Edit .env with your Vultr VM IP

# Deploy via Portainer:
# 1. Copy portainer-stack.yml to Portainer web editor
# 2. Update MQTT_BROKER_ADDRESS line
# 3. Keep bridge networking (default)
# 4. Deploy stack
```

### Vultr VM
```bash
# Build image (or copy from home)
docker build -t weather-sensors:latest .

# Copy appropriate environment  
cp .env.vultr-vm .env

# Deploy via Portainer:
# 1. Copy portainer-stack.yml to Portainer web editor
# 2. Uncomment "network_mode: host" in both services
# 3. Remove "networks:" sections
# 4. Set MQTT_BROKER_ADDRESS=localhost
# 5. Deploy stack
```

---

## 🔧 **Testing Connectivity**

### From Home Lab Machine
```bash
# Set your MQTT broker hostname (CHANGE THIS LINE ONLY if broker name changes)
MQTT_BROKER=n-vultr2

# Test MQTT broker reachability (DNS name)
telnet $MQTT_BROKER 1883

# Test MQTT broker reachability (IP address alternative)
telnet $(grep "$MQTT_BROKER" /etc/hosts | awk '{print $1}') 1883

# Test container connectivity
docker run --rm weather-sensors:latest test
```

### From Vultr VM
```bash
# Test local MQTT broker
telnet localhost 1883

# Test container with host networking
docker run --rm --network host weather-sensors:latest test
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
# Check firewall (Vultr VM)
sudo ufw status numbered

# Test from source
telnet MQTT_BROKER_IP 1883

# Check container networking
docker exec -it CONTAINER_NAME ip route
```

### Container Won't Start
```bash
# Check logs
docker logs CONTAINER_NAME

# Test configuration
docker run --rm -it weather-sensors:latest bash
```

### Permission Issues
```bash
# Check volume permissions
docker volume inspect weather-sensors-data

# Reset if needed
docker volume rm weather-sensors-data
```

---

## 🔧 **Dynamic Sensor Configuration via MQTT**

### Overview
The system supports dynamic updates to local sensor configurations through MQTT messages, allowing real-time changes without container restarts.

### Configuration
```bash
# Environment variable (required)
MQTT_TOPIC_LOCAL_SENSORS_UPDATES="KTBMES/ROSA/sensors/config/local_sensors/update"

# Backup retention settings (optional, defaults shown)
# MAX_BACKUPS=10
# BACKUP_RETENTION_DAYS=30
```

### MQTT Topic & Payload Format

**Topic**: Value from `MQTT_TOPIC_LOCAL_SENSORS_UPDATES` environment variable
**Default**: `KTBMES/ROSA/sensors/config/local_sensors`

**Payload Structure**:
```json
{
  "mode": "merge|replace",
  "sensors": {
    "device_id_1": {
      "name": "Sensor Name",
      "location": "Sensor Location"
    },
    "device_id_2": {
      "name": "Another Sensor",
      "location": "Different Location"
    }
  }
}
```

### Update Modes

#### **Merge Mode** (`"mode": "merge"`)
- Adds new sensors to existing configuration
- Updates existing sensors with new data
- Preserves sensors not mentioned in the payload

#### **Replace Mode** (`"mode": "replace"`)
- Completely replaces the entire sensor configuration
- Removes all existing sensors not in the payload
- Use with caution - this is destructive

### Example MQTT Messages

#### Add/Update Sensors (Merge)
```bash
# Using mosquitto_pub
mosquitto_pub -h your-mqtt-broker \
  -t "KTBMES/ROSA/sensors/config/local_sensors" \
  -m '{
    "mode": "merge",
    "sensors": {
      "12345": {
        "name": "Living Room Temp",
        "location": "Living Room"
      },
      "67890": {
        "name": "Outdoor Weather",
        "location": "Back Yard"
      }
    }
  }'
```

#### Replace All Sensors
```bash
mosquitto_pub -h your-mqtt-broker \
  -t "KTBMES/ROSA/sensors/config/local_sensors" \
  -m '{
    "mode": "replace",
    "sensors": {
      "11111": {
        "name": "Kitchen Sensor",
        "location": "Kitchen"
      }
    }
  }'
```

### Using MQTT Explorer
1. Connect to your MQTT broker
2. Navigate to the config topic: `KTBMES/ROSA/sensors/config/local_sensors`
3. Publish a JSON payload with the desired sensor configuration
4. Check container logs for confirmation

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
- JSON syntax must be valid
- Required fields: `mode`, `sensors`
- Mode must be either `"merge"` or `"replace"`
- Each sensor must have `name` and `location` fields

**Error Responses**:
- Configuration errors are logged in container logs
- Invalid payloads are rejected with descriptive error messages
- System continues operating with previous configuration on failure

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