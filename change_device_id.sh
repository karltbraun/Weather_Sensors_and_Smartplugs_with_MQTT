#!/usr/bin/env bash

################################################################################
# Device ID Change Script for Weather Sensors
################################################################################
# Purpose: Updates device IDs in local_sensors.json within running container
#          without requiring image rebuild or manual file editing
#
# Usage: ./change_device_id.sh <old_device_id> <new_device_id> [container_name]
#
# Arguments:
#   old_device_id  - The current device ID to replace
#   new_device_id  - The new device ID to use
#   container_name - Optional: container name (default: sensor-republisher)
#
# Examples:
#   ./change_device_id.sh 12345 67890
#   ./change_device_id.sh old-sensor-01 new-sensor-01 sensor-republisher
#
# Notes:
#   - Creates backup before making changes
#   - Validates container is running
#   - Restarts container to apply changes
#   - Works with local_sensors.json in /app/config/ directory
################################################################################

set -e  # Exit on error

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
NC='\033[0m' # No Color

# Configuration
CONFIG_FILE="/app/config/local_sensors.json"
DEFAULT_CONTAINER="weather-sensors-republisher"

################################################################################
# Logging Functions
################################################################################
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

################################################################################
# Function: usage
################################################################################
usage() {
    cat << EOF
Usage: $0 <old_device_id> <new_device_id> [container_name]

Changes device IDs in local_sensors.json within a running Docker container.

ARGUMENTS:
    old_device_id    The current device ID to find and replace
    new_device_id    The new device ID to use as replacement
    container_name   Optional: Docker container name (default: $DEFAULT_CONTAINER)

EXAMPLES:
    $0 12345 67890
    $0 old-sensor-01 new-sensor-01
    $0 device-abc device-xyz weather-sensors-republisher

NOTES:
    - Script creates a timestamped backup before making changes
    - Validates that the old device ID exists in the file
    - Automatically restarts the container to apply changes
    - Requires Docker to be installed and container to be running

EOF
}

################################################################################
# Function: validate_container
################################################################################
# Purpose: Checks if the specified container exists and is running
#
# Parameters:
#   $1 - Container name
#
# Exit Codes:
#   0 - Container is running
#   1 - Container not found or not running
################################################################################
validate_container() {
    local CONTAINER=$1
    
    log_info "Checking if container '$CONTAINER' is running..."
    
    if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
        log_error "Container '$CONTAINER' is not running"
        log_info "Available containers:"
        docker ps --format "  - {{.Names}}" | grep -i sensor || echo "  (no sensor containers found)"
        return 1
    fi
    
    log_success "Container '$CONTAINER' is running"
    return 0
}

################################################################################
# Function: backup_config
################################################################################
# Purpose: Creates a timestamped backup of the config file in the container
#
# Parameters:
#   $1 - Container name
#
# Notes:
#   - Backup stored in same directory as original file
#   - Format: local_sensors.json.backup.YYYYMMDD-HHMMSS
################################################################################
backup_config() {
    local CONTAINER=$1
    local TIMESTAMP=$(date +%Y%m%d-%H%M%S)
    local BACKUP_FILE="${CONFIG_FILE}.backup.${TIMESTAMP}"
    
    log_info "Creating backup: $BACKUP_FILE"
    
    if docker exec "$CONTAINER" cp "$CONFIG_FILE" "$BACKUP_FILE" 2>/dev/null; then
        log_success "Backup created successfully"
        return 0
    else
        log_error "Failed to create backup"
        return 1
    fi
}

################################################################################
# Function: verify_old_id_exists
################################################################################
# Purpose: Checks if the old device ID exists in the config file
#
# Parameters:
#   $1 - Container name
#   $2 - Old device ID to search for
#
# Return:
#   0 - Old ID found
#   1 - Old ID not found
################################################################################
verify_old_id_exists() {
    local CONTAINER=$1
    local OLD_ID=$2
    
    log_info "Verifying old device ID '$OLD_ID' exists in config..."
    
    if docker exec "$CONTAINER" grep -q "\"$OLD_ID\"" "$CONFIG_FILE" 2>/dev/null; then
        log_success "Found old device ID in config"
        
        # Show occurrences
        local COUNT=$(docker exec "$CONTAINER" grep -c "\"$OLD_ID\"" "$CONFIG_FILE" 2>/dev/null || echo "0")
        log_info "Found $COUNT occurrence(s) of '$OLD_ID'"
        return 0
    else
        log_warning "Old device ID '$OLD_ID' not found in config file"
        log_warning "This might not be an error if the ID format in the file is different"
        return 1
    fi
}

################################################################################
# Function: change_device_id
################################################################################
# Purpose: Performs the actual device ID replacement in the config file
#
# Parameters:
#   $1 - Container name
#   $2 - Old device ID
#   $3 - New device ID
#
# Process:
#   - Uses sed to perform in-place replacement
#   - Replaces all occurrences of old ID with new ID
#   - Only replaces exact matches (within quotes for JSON safety)
################################################################################
change_device_id() {
    local CONTAINER=$1
    local OLD_ID=$2
    local NEW_ID=$3
    
    log_info "Replacing '$OLD_ID' with '$NEW_ID'..."
    
    # Use sed to replace all occurrences
    # The sed command replaces "old_id" with "new_id" (preserving quotes)
    if docker exec "$CONTAINER" sed -i "s/\"${OLD_ID}\"/\"${NEW_ID}\"/g" "$CONFIG_FILE" 2>/dev/null; then
        log_success "Device ID replacement completed"
        return 0
    else
        log_error "Failed to replace device ID"
        return 1
    fi
}

################################################################################
# Function: verify_change
################################################################################
# Purpose: Verifies that the change was successful
#
# Parameters:
#   $1 - Container name
#   $2 - Old device ID (should not exist)
#   $3 - New device ID (should exist)
################################################################################
verify_change() {
    local CONTAINER=$1
    local OLD_ID=$2
    local NEW_ID=$3
    
    log_info "Verifying changes..."
    
    local OLD_COUNT=$(docker exec "$CONTAINER" grep -c "\"$OLD_ID\"" "$CONFIG_FILE" 2>/dev/null || echo "0")
    local NEW_COUNT=$(docker exec "$CONTAINER" grep -c "\"$NEW_ID\"" "$CONFIG_FILE" 2>/dev/null || echo "0")
    
    echo
    log_info "Occurrences of old ID '$OLD_ID': $OLD_COUNT"
    log_info "Occurrences of new ID '$NEW_ID': $NEW_COUNT"
    echo
    
    if [ "$NEW_COUNT" -gt 0 ]; then
        log_success "New device ID is present in config"
    else
        log_warning "New device ID not found in config - this may indicate an issue"
    fi
}

################################################################################
# Function: restart_container
################################################################################
# Purpose: Restarts the container to apply configuration changes
#
# Parameters:
#   $1 - Container name
################################################################################
restart_container() {
    local CONTAINER=$1
    
    log_info "Restarting container to apply changes..."
    
    if docker restart "$CONTAINER" > /dev/null 2>&1; then
        log_success "Container restarted successfully"
        log_info "Waiting for container to be ready..."
        sleep 3
        return 0
    else
        log_error "Failed to restart container"
        return 1
    fi
}

################################################################################
# Function: show_recent_backups
################################################################################
# Purpose: Lists recent backup files in the container
#
# Parameters:
#   $1 - Container name
################################################################################
show_recent_backups() {
    local CONTAINER=$1
    
    log_info "Recent backups in container:"
    docker exec "$CONTAINER" ls -lht /app/config/local_sensors.json.backup.* 2>/dev/null | head -5 || log_info "  (no backups found)"
}

################################################################################
# Main Execution
################################################################################
main() {
    # Parse arguments
    if [ $# -lt 2 ]; then
        log_error "Insufficient arguments"
        echo
        usage
        exit 1
    fi
    
    if [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
        usage
        exit 0
    fi
    
    OLD_DEVICE_ID="$1"
    NEW_DEVICE_ID="$2"
    CONTAINER="${3:-$DEFAULT_CONTAINER}"
    
    # Display operation summary
    echo
    log_info "Device ID Change Operation"
    log_info "=========================="
    log_info "Container:      $CONTAINER"
    log_info "Old Device ID:  $OLD_DEVICE_ID"
    log_info "New Device ID:  $NEW_DEVICE_ID"
    log_info "Config File:    $CONFIG_FILE"
    echo
    
    # Validate inputs
    if [ "$OLD_DEVICE_ID" == "$NEW_DEVICE_ID" ]; then
        log_error "Old and new device IDs are the same"
        exit 1
    fi
    
    # Execute change workflow
    validate_container "$CONTAINER" || exit 1
    echo
    
    backup_config "$CONTAINER" || exit 1
    echo
    
    verify_old_id_exists "$CONTAINER" "$OLD_DEVICE_ID"
    echo
    
    change_device_id "$CONTAINER" "$OLD_DEVICE_ID" "$NEW_DEVICE_ID" || exit 1
    echo
    
    verify_change "$CONTAINER" "$OLD_DEVICE_ID" "$NEW_DEVICE_ID"
    echo
    
    restart_container "$CONTAINER" || exit 1
    echo
    
    show_recent_backups "$CONTAINER"
    echo
    
    log_success "Device ID change completed successfully!"
    echo
    log_info "To restore from backup if needed:"
    log_info "  docker exec $CONTAINER cp /app/config/local_sensors.json.backup.TIMESTAMP $CONFIG_FILE"
    log_info "  docker restart $CONTAINER"
    echo
}

# Run main function
main "$@"
