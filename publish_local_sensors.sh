#!/usr/bin/env bash
################################################################################
# publish_local_sensors.sh - Publish local sensor configuration via MQTT
################################################################################
# Purpose: Publishes local_sensors JSON configuration to MQTT topic
#
# Author: Karl T. Braun
# Created: 2025-12-31
#
# Usage: ./publish_local_sensors.sh [OPTIONS]
#
# Requirements:
#   - mosquitto_pub must be installed and available in PATH
#   - jq (for JSON validation, optional but recommended)
################################################################################

set -e  # Exit on error

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
TOPIC_ROOT="KTBMES"
DEFAULT_TOPIC="${TOPIC_ROOT}/sensors/config/local_sensors"
TOPIC=""
BROKER=""
INPUT_FILE=""
RETAIN_FLAG="-r"  # Retain by default
TEST_MODE=""       # Test mode - print config without publishing

# Function to display usage
usage() {
    cat << EOF
Publish Local Sensors Configuration to MQTT

Usage: $0 [OPTIONS]

Options:
  --topic=TOPIC       MQTT topic to publish to
                      Default: ${DEFAULT_TOPIC}
  
  --broker=BROKER     MQTT broker hostname or IP address
                      Default: Value of BROKER_NAME from .env file
  
  --file=FILE         Path to JSON file containing sensor data
                      Default: Read from standard input
  
  --no-retain         Publish without retain flag (default: retained)
  
  --test              Test mode - display configuration without publishing
  
  --help, -h          Display this help message

Examples:
  # Publish from file with defaults
  $0 --file=config/local_sensors.json
  
  # Publish to custom topic
  $0 --topic=KTBMES/sensors/config/test --file=config/local_sensors.json
  
  # Publish to specific broker
  $0 --broker=mqtt.example.com --file=config/local_sensors.json
  
  # Publish from stdin
  cat config/local_sensors.json | $0
  
  # Publish without retain flag
  $0 --file=config/local_sensors.json --no-retain
  
  # Test mode - show what would be published
  $0 --file=config/local_sensors.json --test

Environment:
  Reads BROKER_NAME from .env file if --broker not specified

Requirements:
  - mosquitto_pub command must be available
  - jq command recommended for JSON validation

EOF
}

# Function to get BROKER_NAME from .env file
get_broker_from_env() {
    local env_file="${1:-.env}"
    
    if [[ ! -f "$env_file" ]]; then
        echo -e "${RED}ERROR: .env file not found: $env_file${NC}" >&2
        return 1
    fi
    
    # Read BROKER_NAME from .env, handling quotes and comments
    local broker_name=$(grep "^BROKER_NAME=" "$env_file" | head -1 | cut -d'=' -f2 | sed 's/^["'\'']*//;s/["'\'']*$//' | sed 's/#.*//' | xargs)
    
    if [[ -z "$broker_name" ]]; then
        echo -e "${RED}ERROR: BROKER_NAME not found in $env_file${NC}" >&2
        return 1
    fi
    
    echo "$broker_name"
}

# Function to validate JSON
validate_json() {
    local payload="$1"
    
    if command -v jq >/dev/null 2>&1; then
        if ! echo "$payload" | jq empty 2>/dev/null; then
            echo -e "${RED}ERROR: Invalid JSON payload${NC}" >&2
            return 1
        fi
    else
        # Basic JSON validation without jq
        if ! echo "$payload" | grep -q '^{.*}$\|^\[.*\]$'; then
            echo -e "${YELLOW}WARNING: jq not available for JSON validation${NC}" >&2
        fi
    fi
    return 0
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --topic=*)
            TOPIC="${1#*=}"
            shift
            ;;
        --broker=*)
            BROKER="${1#*=}"
            shift
            ;;
        --file=*)
            INPUT_FILE="${1#*=}"
            shift
            ;;
        --no-retain)
            RETAIN_FLAG=""
            shift
            ;;
        --test)
            TEST_MODE="true"
            shift
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            echo -e "${RED}ERROR: Unknown option: $1${NC}" >&2
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Set defaults if not provided
if [[ -z "$TOPIC" ]]; then
    TOPIC="$DEFAULT_TOPIC"
fi

# Get broker from .env if not specified
if [[ -z "$BROKER" ]]; then
    BROKER=$(get_broker_from_env)
    if [[ $? -ne 0 ]]; then
        echo -e "${RED}ERROR: Could not determine MQTT broker${NC}" >&2
        echo "Specify --broker=HOSTNAME or ensure BROKER_NAME is set in .env file" >&2
        exit 1
    fi
fi

# Check if mosquitto_pub is available
if ! command -v mosquitto_pub >/dev/null 2>&1; then
    echo -e "${RED}ERROR: mosquitto_pub command not found${NC}" >&2
    echo "Please install mosquitto-clients package" >&2
    exit 1
fi

# Read input payload
if [[ -n "$INPUT_FILE" ]]; then
    if [[ ! -f "$INPUT_FILE" ]]; then
        echo -e "${RED}ERROR: File not found: $INPUT_FILE${NC}" >&2
        exit 1
    fi
    echo -e "${YELLOW}Reading from file: $INPUT_FILE${NC}"
    PAYLOAD=$(cat "$INPUT_FILE")
else
    echo -e "${YELLOW}Reading from standard input...${NC}" >&2
    PAYLOAD=$(cat)
fi

# Validate payload is not empty
if [[ -z "$PAYLOAD" ]]; then
    echo -e "${RED}ERROR: Empty payload${NC}" >&2
    exit 1
fi

# Validate JSON format
if ! validate_json "$PAYLOAD"; then
    exit 1
fi

# Test mode - display configuration and exit
if [[ -n "$TEST_MODE" ]]; then
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}                    TEST MODE - NO PUBLISH                      ${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${YELLOW}Configuration:${NC}"
    echo -e "  Topic:        ${GREEN}$TOPIC${NC}"
    echo -e "  Broker:       ${GREEN}$BROKER${NC}"
    echo -e "  Retain Flag:  ${GREEN}$([ -n "$RETAIN_FLAG" ] && echo 'Yes' || echo 'No')${NC}"
    echo -e "  Payload Size: ${GREEN}$(echo "$PAYLOAD" | wc -c) bytes${NC}"
    echo ""
    echo -e "${YELLOW}JSON Payload:${NC}"
    echo -e "${GREEN}───────────────────────────────────────────────────────────────${NC}"
    if command -v jq >/dev/null 2>&1; then
        echo "$PAYLOAD" | jq -C .
    else
        echo "$PAYLOAD" | python3 -m json.tool 2>/dev/null || echo "$PAYLOAD"
    fi
    echo -e "${GREEN}───────────────────────────────────────────────────────────────${NC}"
    echo ""
    echo -e "${YELLOW}Note: Run without --test flag to actually publish to MQTT${NC}"
    exit 0
fi

# Display configuration
echo -e "${GREEN}Publishing Configuration:${NC}"
echo "  Broker: $BROKER"
echo "  Topic: $TOPIC"
echo "  Retain: $([ -n "$RETAIN_FLAG" ] && echo 'Yes' || echo 'No')"
echo "  Payload size: $(echo "$PAYLOAD" | wc -c) bytes"
echo ""
echo -e "${YELLOW}JSON Payload:${NC}"
echo -e "${GREEN}───────────────────────────────────────────────────────────────${NC}"
if command -v jq >/dev/null 2>&1; then
    echo "$PAYLOAD" | jq -C .
else
    echo "$PAYLOAD" | python3 -m json.tool 2>/dev/null || echo "$PAYLOAD"
fi
echo -e "${GREEN}───────────────────────────────────────────────────────────────${NC}"
echo ""

# Publish to MQTT
echo -e "${YELLOW}Publishing to MQTT...${NC}"
if mosquitto_pub -h "$BROKER" -t "$TOPIC" -m "$PAYLOAD" $RETAIN_FLAG; then
    echo -e "${GREEN}✓ Successfully published to $TOPIC${NC}"
    exit 0
else
    echo -e "${RED}✗ Failed to publish to MQTT broker${NC}" >&2
    exit 1
fi
