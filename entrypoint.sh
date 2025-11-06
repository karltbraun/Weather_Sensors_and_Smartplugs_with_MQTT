#!/bin/bash
set -e

# Entrypoint script for Weather Sensors MQTT Services
# Supports both sensor republisher and shelly processor services

# Default service if not specified
SERVICE=${SERVICE:-republish}

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
    echo "  CONSOLE_LOG_LEVEL      - Console logging level (DEBUG|INFO|WARNING|ERROR)"
    echo "  FILE_LOG_LEVEL         - File logging level (DEBUG|INFO|WARNING|ERROR)"
    echo "  CLEAR_LOG_FILE         - Clear log file on startup (true|false)"
    echo "  MQTT_BROKER_ADDRESS    - MQTT broker hostname/IP"
    echo "  MQTT_BROKER_PORT       - MQTT broker port (default: 1883)"
    echo "  MQTT_USERNAME          - MQTT username (optional)"
    echo "  MQTT_PASSWORD          - MQTT password (optional)"
    echo ""
}

# Function to validate environment
validate_environment() {
    local errors=0
    
    # Check for required MQTT configuration
    if [[ -z "${MQTT_BROKER_ADDRESS}" ]]; then
        echo "ERROR: MQTT_BROKER_ADDRESS environment variable is required"
        errors=$((errors + 1))
    fi
    
    # Test MQTT connectivity
    echo "Testing MQTT broker connectivity..."
    if command -v nc >/dev/null 2>&1; then
        if timeout 5 nc -z "${MQTT_BROKER_ADDRESS}" "${MQTT_BROKER_PORT:-1883}" 2>/dev/null; then
            echo "✓ MQTT broker ${MQTT_BROKER_ADDRESS}:${MQTT_BROKER_PORT:-1883} is reachable"
        else
            echo "⚠ WARNING: Cannot reach MQTT broker ${MQTT_BROKER_ADDRESS}:${MQTT_BROKER_PORT:-1883}"
            echo "  This may be due to:"
            echo "  - MQTT broker not running"
            echo "  - Firewall blocking connection"
            echo "  - Incorrect broker address"
            echo "  - Network configuration issues"
        fi
    else
        echo "⚠ Cannot test MQTT connectivity (nc command not available)"
    fi
    
    # Check if config directory is accessible
    if [[ ! -d "/app/config" ]]; then
        echo "WARNING: /app/config directory not found, creating it..."
        mkdir -p /app/config
    fi
    
    # Check if data directory is accessible
    if [[ ! -d "/app/data" ]]; then
        echo "INFO: Creating /app/data directory..."
        mkdir -p /app/data
    fi
    
    # Check if logs directory is accessible
    if [[ ! -d "/app/logs" ]]; then
        echo "INFO: Creating /app/logs directory..."
        mkdir -p /app/logs
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

# Function to display service info
display_service_info() {
    echo "=================================================="
    echo "Weather Sensors MQTT Service Container"
    echo "=================================================="
    echo "Service: $SERVICE"
    echo "Timestamp: $(date -Iseconds)"
    echo "Python Version: $(python --version)"
    echo "Working Directory: $(pwd)"
    echo "User: $(whoami)"
    echo "MQTT Broker: ${MQTT_BROKER_ADDRESS}:${MQTT_BROKER_PORT:-1883}"
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

# Display service information
display_service_info

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
            echo "Testing connection to ${MQTT_BROKER_ADDRESS:-localhost}:${MQTT_BROKER_PORT:-1883}..."
            if timeout 10 nc -z "${MQTT_BROKER_ADDRESS:-localhost}" "${MQTT_BROKER_PORT:-1883}"; then
                echo "✓ MQTT broker is reachable"
            else
                echo "✗ MQTT broker is not reachable"
                echo "  Check:"
                echo "  - MQTT broker is running"
                echo "  - Firewall allows connection"
                echo "  - Network configuration"
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
    
    # Test environment variables
    import os
    broker_addr = os.getenv('MQTT_BROKER_ADDRESS', 'not-set')
    deployment = os.getenv('DEPLOYMENT_SCENARIO', 'not-set')
    print(f'✓ MQTT Broker: {broker_addr}')
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