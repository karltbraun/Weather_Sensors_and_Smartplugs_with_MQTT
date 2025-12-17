#!/bin/bash
set -e

# Entrypoint script for Weather Sensors MQTT Services
# Supports both sensor republisher and shelly processor services

# Default service if not specified
SERVICE=${SERVICE:-weather-republish}

# Function to display usage
usage() {
    echo "Weather Sensors MQTT Service Container"
    echo "Usage: docker run [options] weather-sensors:latest [SERVICE]"
    echo ""
    echo "Services:"
    echo "  republish  - RTL-433 sensor data republisher (default)"
    echo "  shelly     - Shelly smart device processor"
    echo "  bash       - Interactive bash shell"
    echo ""
    echo "Environment Variables:"
    echo "  SERVICE                 - Service to run (republish|shelly|bash)"
    echo "  BROKER_NAME            - MQTT broker configuration name (n-vultr2, PI2, etc.)"
    echo "  CONSOLE_LOG_LEVEL      - Console logging level (DEBUG|INFO|WARNING|ERROR)"
    echo "  FILE_LOG_LEVEL         - File logging level (DEBUG|INFO|WARNING|ERROR)"
    echo "  CLEAR_LOG_FILE         - Clear log file on startup (true|false)"
    echo "  DEPLOYMENT_SCENARIO    - Deployment type (home-lab|vultr-vm)"
    echo "  PUB_TOPIC_ROOT         - Root MQTT topic for publishing"
    echo "  PUB_SOURCE             - Source identifier (hostname)"
    echo ""
}

# Function to get broker configuration from BROKER_NAME
get_broker_config() {
    python3 -c "
import sys
import os
sys.path.insert(0, '/app')

try:
    from config.broker_config import load_broker_config
    broker_config = load_broker_config()
    if broker_config:
        address = broker_config['MQTT_BROKER_ADDRESS']
        port = broker_config['MQTT_BROKER_PORT']
        print(f'{address}:{port}')
    else:
        print('ERROR: Unable to load broker configuration', file=sys.stderr)
        sys.exit(1)
except Exception as e:
    print(f'ERROR: {e}', file=sys.stderr)
    sys.exit(1)
"
}

# Function to validate environment
validate_environment() {
    local errors=0
    
    # Check for BROKER_NAME instead of individual MQTT variables
    if [[ -z "${BROKER_NAME}" ]]; then
        echo "ERROR: BROKER_NAME environment variable is required"
        echo "  Available broker names: n-vultr2, ts-vultr2, PI2, TS-PI2, mqtt.eclipse.org"
        errors=$((errors + 1))
        return $errors
    fi
    
    # Get actual broker address from configuration
    local broker_info
    broker_info=$(get_broker_config)
    if [[ $? -ne 0 ]]; then
        echo "ERROR: Failed to load broker configuration for BROKER_NAME=${BROKER_NAME}"
        errors=$((errors + 1))
        return $errors
    fi
    
    # Extract address and port from broker info
    local broker_address=${broker_info%:*}
    local broker_port=${broker_info#*:}
    
    # Test MQTT connectivity using resolved broker information
    echo "Testing MQTT broker connectivity..."
    echo "  Broker Name: ${BROKER_NAME}"
    echo "  Resolved Address: ${broker_address}:${broker_port}"
    
    if command -v nc >/dev/null 2>&1; then
        if timeout 5 nc -z "${broker_address}" "${broker_port}" 2>/dev/null; then
            echo "✓ MQTT broker ${broker_address}:${broker_port} is reachable"
        else
            echo "⚠ WARNING: Cannot reach MQTT broker ${broker_address}:${broker_port}"
            echo "  This may be due to:"
            echo "  - MQTT broker not running"
            echo "  - Firewall blocking connection"
            echo "  - Incorrect broker address"
            echo "  - Network configuration issues"
        fi
    else
        echo "⚠ Cannot test MQTT connectivity (nc command not available)"
    fi
    
    # Display network information for debugging
    echo "Network Information:"
    echo "  Container IP: $(hostname -i 2>/dev/null || echo 'N/A')"
    echo "  Hostname: $(hostname)"
    echo "  Deployment Scenario: ${DEPLOYMENT_SCENARIO:-not-set}"
    
    if [[ $errors -gt 0 ]]; then
        echo "Environment validation failed with $errors error(s)"
        return 1
    fi
    
    return 0
}

# Function to setup logging
setup_logging() {
    # Ensure log directory exists and is writable
    mkdir -p /app/logs
    
    # Set default log levels if not specified
    export CONSOLE_LOG_LEVEL=${CONSOLE_LOG_LEVEL:-INFO}
    export FILE_LOG_LEVEL=${FILE_LOG_LEVEL:-DEBUG}
    export CLEAR_LOG_FILE=${CLEAR_LOG_FILE:-true}
    
    echo "Logging configuration:"
    echo "  Console Level: $CONSOLE_LOG_LEVEL"
    echo "  File Level: $FILE_LOG_LEVEL"
    echo "  Clear Log File: $CLEAR_LOG_FILE"
}

# Function to display startup banner
display_banner() {
    # Get resolved broker information
    local broker_info
    broker_info=$(get_broker_config 2>/dev/null) || broker_info="unknown:1883"
    
    echo "=================================================="
    echo "Weather Sensors MQTT Service Container"
    echo "=================================================="
    echo "Service: $SERVICE"
    echo "Timestamp: $(date -Iseconds)"
    echo "Python Version: $(python --version)"
    echo "Working Directory: $(pwd)"
    echo "User: $(whoami)"
    echo "MQTT Broker Name: ${BROKER_NAME:-not-set}"
    echo "MQTT Broker: ${broker_info}"
    echo "=================================================="
}

# Handle command line arguments
if [[ $# -gt 0 ]]; then
    SERVICE=$1
fi

# Handle help requests
case "$SERVICE" in
    -h|--help|help)
        usage
        exit 0
        ;;
esac

# Setup logging first
setup_logging

# Display startup banner
display_banner

# Validate environment (but don't exit for bash service)
if [[ "$SERVICE" != "bash" ]]; then
    if ! validate_environment; then
        echo "Environment validation failed. Exiting..."
        exit 1
    fi
fi

# Execute the appropriate service
case "$SERVICE" in
    republish|republish_processed_sensors)
        echo "Starting RTL-433 Sensor Data Republisher Service..."
        echo "Subscription topics: ${SUB_TOPICS_REPUBLISH:-KTBMES/raw/#}"
        exec python republish_processed_sensors_main.py
        ;;
    
    shelly|shelly_processor)
        echo "Starting Shelly Smart Device Processor Service..."
        echo "Subscription topics: ${SUB_TOPICS_SHELLY:-shellies/+/+}"
        exec python shelly_main.py
        ;;
    
    bash|shell|sh)
        echo "Starting interactive bash shell..."
        exec /bin/bash
        ;;
    
    test)
        echo "Running service tests..."
        echo "Testing network connectivity and configuration..."
        
        # Test MQTT connectivity
        echo "=== MQTT Connectivity Test ==="
        if command -v nc >/dev/null 2>&1; then
            # Get broker config using Python
            BROKER_INFO=$(python3 -c "
import sys
sys.path.append('/app')
from config.broker_config import load_broker_config
broker_config = load_broker_config()
print(f'{broker_config[\"MQTT_BROKER_ADDRESS\"]}:{broker_config[\"MQTT_BROKER_PORT\"]}')
            ")
            BROKER_HOST=$(echo $BROKER_INFO | cut -d: -f1)
            BROKER_PORT=$(echo $BROKER_INFO | cut -d: -f2)
            
            echo "Testing connection to $BROKER_INFO..."
            if timeout 10 nc -z "$BROKER_HOST" "$BROKER_PORT"; then
                echo "✓ MQTT broker is reachable"
            else
                echo "✗ MQTT broker is not reachable"
                echo "  Check:"
                echo "  - MQTT broker is running"
                echo "  - Firewall allows connection"
                echo "  - Network configuration"
                echo "  - BROKER_NAME ($BROKER_NAME) configuration"
            fi
        fi
        
        # Test Python modules
        echo "=== Python Module Test ==="
        python -c "
import sys
sys.path.insert(0, '/app')
try:
    from src.utils.misc_utils import get_logging_levels
    from config.broker_config import load_broker_config
    print('✓ Configuration modules loaded successfully')
    
    # Test environment variables and broker configuration
    import os
    broker_name = os.getenv('BROKER_NAME', 'not-set')
    deployment = os.getenv('DEPLOYMENT_SCENARIO', 'not-set')
    
    # Test broker configuration loading
    try:
        broker_config = load_broker_config()
        broker_addr = f\"{broker_config['MQTT_BROKER_ADDRESS']}:{broker_config['MQTT_BROKER_PORT']}\"
        print(f'✓ Broker Name: {broker_name}')
        print(f'✓ MQTT Broker: {broker_addr}')
    except Exception as e:
        print(f'⚠ Broker config error: {e}')
        print(f'✓ Broker Name: {broker_name} (config not loaded)')
    
    print(f'✓ Deployment: {deployment}')
    print('✓ Container is ready for service execution')
    sys.exit(0)
except Exception as e:
    print(f'✗ Test failed: {e}')
    sys.exit(1)
"
        
        # Network diagnostic information
        echo "=== Network Diagnostic ==="
        echo "Container networking mode: $(cat /proc/1/cgroup | grep -o 'docker.*' | head -1 || echo 'unknown')"
        echo "Container IP: $(hostname -i 2>/dev/null || echo 'host networking or unknown')"
        echo "Gateway: $(ip route | grep default | awk '{print $3}' 2>/dev/null || echo 'host networking or unknown')"
        ;;
    
    *)
        echo "ERROR: Unknown service '$SERVICE'"
        echo ""
        usage
        exit 1
        ;;
esac