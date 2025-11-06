# Docker Deployment Guide for Portainer + Docker Desktop

This guide provides step-by-step instructions for deploying the Weather Sensors MQTT services using Portainer on Docker Desktop. **Updated for Vultr VM MQTT broker with firewall restrictions.**

## 🏗️ **Deployment Scenarios**

You have **two deployment options** based on your MQTT broker setup:

### 🏠 **Home Lab Deployment**
- Deploy containers on your **local lab machines**
- Connect to **Vultr VM MQTT broker** via home ISP IP
- Requires **bridge networking** in containers

### ☁️ **Vultr VM Deployment** 
- Deploy containers on the **same Vultr VM** as MQTT broker
- Connect to **localhost MQTT broker**
- Can use **host networking** for optimal performance

---

## 🚀 Quick Deployment

### Step 1: Build the Docker Image

From your MacBook terminal in the project directory:

```bash
# Build the image
docker build -t weather-sensors:latest .

# Verify the image was created
docker images | grep weather-sensors
```

### Step 2: Choose Your Deployment Scenario

#### 🏠 **For Home Lab Deployment:**

1. **Configure Environment**:
   ```bash
   cp .env.home-lab .env
   # Edit .env and update MQTT_BROKER_ADDRESS with your Vultr VM IP
   ```

2. **Use Portainer Stack**: Copy `portainer-stack.yml` 
3. **Network Settings**: Keep bridge networking (default)
4. **MQTT Address**: Use your Vultr VM's IP or hostname

#### ☁️ **For Vultr VM Deployment:**

1. **Configure Environment**:
   ```bash
   cp .env.vultr-vm .env
   # MQTT_BROKER_ADDRESS should be "localhost"
   ```

2. **Use Portainer Stack**: Copy `portainer-stack.yml`
3. **Network Settings**: Uncomment `network_mode: host` in services
4. **MQTT Address**: Use "localhost" or "127.0.0.1"

### Step 3: Deploy via Portainer Stack

1. **Open Portainer** in your browser (usually http://localhost:9000)

2. **Navigate to Stacks**:
   - Click on "Stacks" in the left sidebar
   - Click "Add stack" button

3. **Create New Stack**:
   - **Name**: `weather-sensors`
   - **Build method**: Choose "Web editor"
   
4. **Copy Stack Configuration**:
   - Open `portainer-stack.yml` from this project
   - Copy the entire contents
   - Paste into Portainer's web editor

5. **Configure for Your Deployment Scenario**:

   **🏠 Home Lab Configuration:**
   ```yaml
   # Leave network_mode commented (use bridge networking)
   environment:
     - MQTT_BROKER_ADDRESS=your-vultr-vm-ip-or-hostname  # UPDATE THIS
     - DEPLOYMENT_SCENARIO=home-lab
   networks:
     - weather-sensors  # Keep this
   ```

   **☁️ Vultr VM Configuration:**
   ```yaml
   # Uncomment network_mode for both services
   network_mode: host
   environment:
     - MQTT_BROKER_ADDRESS=localhost
     - DEPLOYMENT_SCENARIO=vultr-vm
   # Remove networks: section
   ```

6. **Deploy the Stack**:
   - Click "Deploy the stack"
   - Portainer will create and start both services

---

## 🌐 **Network Configuration Details**

### 🏠 **Home Lab Networking**

**Requirements:**
- Lab machines must have your **home ISP's public IP**
- Vultr VM firewall allows your **home ISP IP range**
- **Alternative**: Use Tailscale network

**Configuration:**
```bash
# Standard bridge networking
MQTT_BROKER_ADDRESS=your-vultr-vm-public-ip
# OR if using Tailscale:
MQTT_BROKER_ADDRESS=100.x.x.x  # Vultr VM's Tailscale IP
```

**Firewall Requirements:**
- Vultr VM allows TCP/1883 from your home ISP IP
- OR Vultr VM allows Tailscale network range

### ☁️ **Vultr VM Networking**

**Requirements:**
- Containers run on **same VM** as MQTT broker
- Use **localhost** connectivity
- **Host networking** for optimal performance

**Configuration:**
```bash
# Host networking (no Docker network isolation)
network_mode: host
MQTT_BROKER_ADDRESS=localhost
```

**Advantages:**
- No firewall concerns (all local)
- Best performance (no network translation)
- Direct localhost access

In Portainer:
1. Go to **Containers** to see running services
2. Click on container names to view:
   - **Logs**: Real-time service output
   - **Stats**: Resource usage
   - **Console**: Interactive access if needed

## 🔧 Alternative: Docker Compose (Command Line)

### 🏠 **Home Lab Deployment**
```bash
# Use home lab environment
cp .env.home-lab .env
# Edit .env and update MQTT_BROKER_ADDRESS

# Deploy with bridge networking
docker compose up -d

# Monitor logs
docker compose logs -f sensor-republisher
```

### ☁️ **Vultr VM Deployment**
```bash
# Use Vultr VM environment  
cp .env.vultr-vm .env

# Edit docker-compose.yml:
# 1. Uncomment "network_mode: host" in both services
# 2. Remove "networks:" and "depends_on:" sections
# 3. Remove mqtt-broker service entirely

# Deploy with host networking
docker compose up -d

# Monitor logs
docker compose logs -f sensor-republisher
```

---

## 🔍 **Troubleshooting Network Issues**

### **MQTT Connection Failed**

**🏠 Home Lab Issues:**
```bash
# Test connectivity from lab machine to Vultr VM
telnet your-vultr-vm-ip 1883

# Check if your IP is allowed
curl -4 ifconfig.me  # Get your public IP
# Verify this IP is in Vultr VM firewall rules
```

**☁️ Vultr VM Issues:**
```bash
# Test local MQTT broker
telnet localhost 1883

# Check if MQTT broker is running
sudo systemctl status mosquitto
# OR
sudo netstat -tlnp | grep 1883
```

### **Firewall Configuration**

**Vultr VM Firewall Rules:**
```bash
# Allow your home ISP IP (replace with your actual IP)
sudo ufw allow from YOUR.HOME.ISP.IP to any port 1883

# OR allow Tailscale network range
sudo ufw allow from 100.64.0.0/10 to any port 1883

# Check rules
sudo ufw status numbered
```

### **Tailscale Setup**

If using Tailscale network:

**On Vultr VM:**
```bash
# Install and connect to Tailscale
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# Get Tailscale IP
tailscale ip -4
```

**On Lab Machines:**
```bash
# Ensure lab machines are on Tailscale
tailscale status

# Test connectivity via Tailscale
telnet VULTR-TAILSCALE-IP 1883
```

---

## 📊 Service Overview

### Sensor Republisher Service
- **Container**: `weather-sensors-republisher`
- **Purpose**: Processes RTL-433 raw sensor data
- **Subscribes to**: `"+/sensors/raw/#"` (configurable)
- **Log file**: `/app/logs/republish_processed_sensors.log`

### Shelly Processor Service
- **Container**: `weather-sensors-shelly`
- **Purpose**: Processes Shelly smart device messages
- **Subscribes to**: `"Shelly/#"` (configurable)
- **Log file**: `/app/logs/shelly.log`

## 🗂️ Volume Management in Portainer

The stack creates three persistent volumes accessible in Portainer:

1. **weather-sensors-data**: Device data and JSON files
2. **weather-sensors-logs**: Service log files
3. **weather-sensors-config**: Configuration files

To access volumes in Portainer:
- Go to **Volumes** → Select volume → **Browse**

## 🔍 Troubleshooting

### Container Won't Start
1. Check container logs in Portainer
2. Verify MQTT broker configuration
3. Ensure MQTT broker is accessible from Docker

### Test Container Configuration
```bash
# Run container in test mode
docker run --rm weather-sensors:latest test

# Interactive shell for debugging
docker run --rm -it weather-sensors:latest bash
```

### Common Issues

**MQTT Connection Failed**:
- Verify `MQTT_BROKER_ADDRESS` is correct
- Check if MQTT broker is running and accessible
- Verify authentication credentials if required

**Permission Errors**:
- Containers run as non-root user for security
- Volume permissions are automatically handled

**Out of Memory**:
- Containers are limited to 256MB by default
- Increase limits in stack configuration if needed

## 🔄 Updates and Maintenance

### Update Container Image
```bash
# Rebuild image with changes
docker build -t weather-sensors:latest .

# In Portainer: Stacks → Select stack → "Update the stack"
# Or restart containers to use new image
```

### View Real-time Logs
In Portainer:
1. Go to **Containers**
2. Click on container name
3. Select **Logs** tab
4. Enable "Auto-refresh" for real-time monitoring

### Backup Configuration
Export your stack configuration from Portainer:
1. **Stacks** → Select your stack
2. Click **Download** to save the configuration

## 🏷️ Portainer Labels

The containers include Portainer-specific labels for organization:
- **Group**: `weather-sensors`
- **Service**: `republisher` or `shelly-processor`
- **Description**: Service-specific descriptions

These help organize containers in the Portainer UI.

## 📈 Monitoring and Alerts

### Health Checks
Both services include health checks that monitor:
- Service startup success
- Log file creation
- Basic functionality

### Resource Monitoring
- **CPU Limit**: 0.5 cores per service
- **Memory Limit**: 256MB per service
- **Disk Usage**: Monitored via volume usage

### Log Rotation
Consider setting up log rotation for production:
- Logs are written to persistent volumes
- Can grow over time without rotation
- Portainer can help monitor disk usage

## 🔐 Security Considerations

- Containers run as non-root user (`appuser`)
- No exposed ports (except for optional MQTT broker)
- Environment variables for sensitive data
- Read-only config volume mounting option available

## 🌐 Network Configuration

- **Network**: `weather-sensors-network` (bridge)
- **DNS**: Automatic service discovery between containers
- **External Access**: Only MQTT broker (if enabled) exposes ports

This setup is optimized for your Docker Desktop + Portainer workflow and provides easy management through the Portainer UI.