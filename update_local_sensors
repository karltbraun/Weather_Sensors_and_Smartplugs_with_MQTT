#!/usr/bin/env bash
################################################################################
# update_local_sensors1.sh - Publish local sensor configuration via MQTT
################################################################################
# Purpose: Reads sensor configuration from JSON file and publishes to MQTT
#          This is a bash reimplementation of update_local_sensors.py
#
# Author: Karl T. Braun
# Created: 2026-01-01
#
# Usage: ./update_local_sensors1.sh [INPUT_FILE]
#
# Requirements:
#   - mosquitto_pub must be installed and available in PATH
#   - jq (for JSON validation, optional but recommended)
#   - .env file with MQTT configuration
################################################################################

set -e  # Exit on error

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT_FILE=""
USE_STDIN=false

# Function to display usage
usage() {
    cat << EOF
Publish Local Sensors Update to MQTT

Usage: $0 [INPUT_FILE]
       cat file.json | $0

Arguments:
  INPUT_FILE          Path to input JSON file
                      If omitted, reads from standard input

Environment Variables (from .env file):
  MQTT_BROKER         MQTT broker hostname (default: vultr2)
  MQTT_PORT           MQTT broker port (default: 1883)
  MQTT_TOPIC_LOCAL_SENSORS
                      MQTT topic to publish to
                      Default: KTBMES/sensors/config/local_sensors

Examples:
  # Read from file
  $0 ./config_update/local_sensors_update.json
  
  # Read from stdin
  cat ./config_update/local_sensors_update.json | $0
  
  # Pipe from another command
  echo '{"sensor1": {"name": "test"}}' | $0

Requirements:
  - mosquitto_pub command must be available
  - .env file must exist in current directory

EOF
}

# Function to load environment variables from .env file
load_env_file() {
    local env_file="${SCRIPT_DIR}/.env"
    
    if [[ ! -f "$env_file" ]]; then
        echo -e "${RED}ERROR: .env file not found: $env_file${NC}" >&2
        exit 1
    fi
    
    # Load environment variables from .env file
    # This handles quoted values and comments
    while IFS='=' read -r key value; do
        # Skip empty lines and comments
        [[ -z "$key" || "$key" =~ ^[[:space:]]*# ]] && continue
        
        # Remove leading/trailing whitespace and quotes
        key=$(echo "$key" | xargs)
        value=$(echo "$value" | sed 's/^["'\'']*//;s/["'\'']*$//' | sed 's/#.*//' | xargs)
        
        # Export variable
        export "$key=$value"
    done < <(grep -v '^[[:space:]]*$' "$env_file")
}

# Function to get MQTT broker from environment
get_mqtt_config() {
    # Set defaults
    MQTT_BROKER="${MQTT_BROKER:-vultr2}"
    MQTT_PORT="${MQTT_PORT:-1883}"
    MQTT_TOPIC="${MQTT_TOPIC_LOCAL_SENSORS:-KTBMES/sensors/config/local_sensors}"
}

# Function to validate JSON
validate_json() {
    local source="$1"
    local data="$2"
    
    # Validate JSON syntax if jq is available
    if command -v jq &> /dev/null; then
        if ! echo "$data" | jq empty 2>/dev/null; then
            echo -e "${RED}ERROR: Invalid JSON from $source${NC}" >&2
            return 1
        fi
    else
        echo -e "${YELLOW}WARNING: jq not found, skipping JSON validation${NC}" >&2
    fi
    
    return 0
}

# Function to publish to MQTT
publish_to_mqtt() {
    local payload="$1"
    local broker="$2"
    local port="$3"
    local topic="$4"
    
    # Check if mosquitto_pub is available
    if ! command -v mosquitto_pub &> /dev/null; then
        echo -e "${RED}ERROR: mosquitto_pub command not found${NC}" >&2
        echo "Please install mosquitto-clients package" >&2
        exit 1
    fi
    
    # Publish to MQTT
    echo "Publishing to MQTT broker ${broker}:${port} on topic '${topic}'..."
    
    if echo "$payload" | mosquitto_pub -h "$broker" -p "$port" -t "$topic" -s; then
        echo -e "${GREEN}✓ Successfully published update to topic '${topic}'${NC}"
        return 0
    else
        echo -e "${RED}ERROR: Failed to publish to MQTT${NC}" >&2
        return 1
    fi
}

# Main script logic
main() {
    # Parse arguments
    if [[ "$1" == "--help" || "$1" == "-h" ]]; then
        usage
        exit 0
    fi
    
    # Determine input source
    if [[ -n "$1" ]]; then
        # File specified as argument
        INPUT_FILE="$1"
        USE_STDIN=false
    else
        # No argument - use stdin
        USE_STDIN=true
    fi
    
    # Load environment variables
    echo "Loading environment variables from .env..."
    load_env_file
    
    # Get MQTT configuration
    get_mqtt_config
    
    # Display configuration
    echo -e "${GREEN}Configuration:${NC}"
    if [[ "$USE_STDIN" == true ]]; then
        echo "  Input Source: stdin"
    else
        echo "  Input File: $INPUT_FILE"
    fi
    echo "  MQTT Broker: ${MQTT_BROKER}:${MQTT_PORT}"
    echo "  MQTT Topic: $MQTT_TOPIC"
    echo ""
    
    # Read input
    local payload
    local source_desc
    
    if [[ "$USE_STDIN" == true ]]; then
        echo "Reading sensor configuration from stdin..."
        source_desc="stdin"
        if ! payload=$(cat); then
            echo -e "${RED}ERROR: Failed to read from stdin${NC}" >&2
            exit 1
        fi
        
        # Check if stdin was empty
        if [[ -z "$payload" ]]; then
            echo -e "${RED}ERROR: No data received from stdin${NC}" >&2
            exit 1
        fi
    else
        # Check if file exists
        if [[ ! -f "$INPUT_FILE" ]]; then
            echo -e "${RED}ERROR: File not found: $INPUT_FILE${NC}" >&2
            exit 1
        fi
        
        echo "Reading sensor configuration from $INPUT_FILE..."
        source_desc="file: $INPUT_FILE"
        if ! payload=$(cat "$INPUT_FILE"); then
            echo -e "${RED}ERROR: Failed to read file: $INPUT_FILE${NC}" >&2
            exit 1
        fi
    fi
    
    # Validate JSON
    if ! validate_json "$source_desc" "$payload"; then
        exit 1
    fi
    
    # Display JSON payload
    echo ""
    echo -e "${GREEN}JSON Payload to be published:${NC}"
    echo "=============================================="
    if command -v jq &> /dev/null; then
        echo "$payload" | jq -C '.'
    else
        echo "$payload"
    fi
    echo "=============================================="
    echo ""
    
    # Publish to MQTT
    if ! publish_to_mqtt "$payload" "$MQTT_BROKER" "$MQTT_PORT" "$MQTT_TOPIC"; then
        exit 1
    fi
    
    echo -e "${GREEN}✓ Update complete${NC}"
}

# Run main function
main "$@"
