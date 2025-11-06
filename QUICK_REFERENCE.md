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