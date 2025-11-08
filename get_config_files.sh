#!/bin/bash

################################################################################
# Config Files Export Script for Weather Sensors
################################################################################
# Purpose: Copies all configuration files from running container to local system
#          for inspection, editing, or backup purposes
#
# Usage: ./get_config_files.sh [destination_dir] [container_name]
#
# Arguments:
#   destination_dir - Optional: local directory to copy files to (default: ./config_backup)
#   container_name  - Optional: container name (default: sensor-republisher)
#
# Examples:
#   ./get_config_files.sh
#   ./get_config_files.sh ./my_configs
#   ./get_config_files.sh ./backup sensor-republisher
#
# Notes:
#   - Creates destination directory if it doesn't exist
#   - Preserves file permissions and timestamps where possible
#   - Creates timestamped subdirectory for each export
#   - Lists all copied files at completion
################################################################################

set -e  # Exit on error

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;36m'
NC='\033[0m' # No Color

# Configuration
CONFIG_DIR_IN_CONTAINER="/app/config"
DEFAULT_DEST="./config_backup"
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
Usage: $0 [destination_dir] [container_name]

Copies all configuration files from running Docker container to local system.

ARGUMENTS:
    destination_dir  Optional: local directory path (default: $DEFAULT_DEST)
    container_name   Optional: Docker container name (default: $DEFAULT_CONTAINER)

EXAMPLES:
    $0
        Copies to ./config_backup/YYYYMMDD-HHMMSS/

    $0 ./my_configs
        Copies to ./my_configs/YYYYMMDD-HHMMSS/

    $0 ./backup sensor-republisher
        Copies from specific container to ./backup/YYYYMMDD-HHMMSS/

    $0 . sensor-republisher
        Copies to current directory (no timestamp subdirectory)

NOTES:
    - Creates timestamped subdirectory to avoid overwriting previous exports
    - Use '.' as destination to copy directly to current directory
    - Preserves original file structure from /app/config/
    - Container must be running

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
# Function: verify_config_dir_exists
################################################################################
# Purpose: Verifies that the config directory exists in the container
#
# Parameters:
#   $1 - Container name
#
# Return:
#   0 - Directory exists
#   1 - Directory not found
################################################################################
verify_config_dir_exists() {
    local CONTAINER=$1
    
    log_info "Verifying config directory exists in container..."
    
    if docker exec "$CONTAINER" test -d "$CONFIG_DIR_IN_CONTAINER" 2>/dev/null; then
        log_success "Config directory found: $CONFIG_DIR_IN_CONTAINER"
        return 0
    else
        log_error "Config directory not found in container: $CONFIG_DIR_IN_CONTAINER"
        return 1
    fi
}

################################################################################
# Function: list_config_files
################################################################################
# Purpose: Lists all files in the container's config directory
#
# Parameters:
#   $1 - Container name
#
# Notes:
#   - Shows file count and names for user confirmation
################################################################################
list_config_files() {
    local CONTAINER=$1
    
    log_info "Files in $CONFIG_DIR_IN_CONTAINER:"
    
    # List files with details
    docker exec "$CONTAINER" ls -lh "$CONFIG_DIR_IN_CONTAINER" 2>/dev/null | tail -n +2 || {
        log_warning "Could not list files in config directory"
        return 1
    }
    
    # Count files (excluding directories)
    local FILE_COUNT=$(docker exec "$CONTAINER" find "$CONFIG_DIR_IN_CONTAINER" -maxdepth 1 -type f 2>/dev/null | wc -l)
    echo
    log_info "Total files to copy: $FILE_COUNT"
}

################################################################################
# Function: create_destination
################################################################################
# Purpose: Creates the destination directory if it doesn't exist
#
# Parameters:
#   $1 - Destination directory path
#
# Return:
#   0 - Directory created or already exists
#   1 - Failed to create directory
################################################################################
create_destination() {
    local DEST_DIR=$1
    
    if [ -d "$DEST_DIR" ]; then
        log_info "Destination directory already exists: $DEST_DIR"
        return 0
    fi
    
    log_info "Creating destination directory: $DEST_DIR"
    
    if mkdir -p "$DEST_DIR"; then
        log_success "Directory created successfully"
        return 0
    else
        log_error "Failed to create destination directory"
        return 1
    fi
}

################################################################################
# Function: copy_config_files
################################################################################
# Purpose: Copies all config files from container to local destination
#
# Parameters:
#   $1 - Container name
#   $2 - Destination directory
#
# Process:
#   - Uses docker cp to copy entire config directory
#   - Preserves file structure and permissions
#   - Reports success/failure for each operation
################################################################################
copy_config_files() {
    local CONTAINER=$1
    local DEST_DIR=$2
    
    log_info "Copying config files from container..."
    echo
    
    # Get list of files to copy (excluding __pycache__ and .pyc files)
    local FILES=$(docker exec "$CONTAINER" find "$CONFIG_DIR_IN_CONTAINER" -maxdepth 1 -type f ! -name "*.pyc" 2>/dev/null)
    
    if [ -z "$FILES" ]; then
        log_warning "No files found to copy"
        return 1
    fi
    
    local SUCCESS_COUNT=0
    local FAIL_COUNT=0
    
    # Copy each file individually for better error handling and reporting
    while IFS= read -r file; do
        local filename=$(basename "$file")
        local dest_path="$DEST_DIR/$filename"
        
        if docker cp "$CONTAINER:$file" "$dest_path" 2>/dev/null; then
            log_success "Copied: $filename"
            ((SUCCESS_COUNT++))
        else
            log_error "Failed to copy: $filename"
            ((FAIL_COUNT++))
        fi
    done <<< "$FILES"
    
    echo
    log_info "Copy summary: $SUCCESS_COUNT succeeded, $FAIL_COUNT failed"
    
    if [ $FAIL_COUNT -gt 0 ]; then
        return 1
    fi
    
    return 0
}

################################################################################
# Function: show_copied_files
################################################################################
# Purpose: Displays the contents of the destination directory
#
# Parameters:
#   $1 - Destination directory
################################################################################
show_copied_files() {
    local DEST_DIR=$1
    
    log_info "Files in destination directory:"
    echo
    ls -lh "$DEST_DIR" 2>/dev/null | grep -v "^total" || log_warning "Could not list destination files"
    echo
    
    # Show full path
    local FULL_PATH=$(cd "$DEST_DIR" && pwd)
    log_info "Full path: $FULL_PATH"
}

################################################################################
# Function: show_edit_instructions
################################################################################
# Purpose: Displays helpful instructions for editing and restoring files
#
# Parameters:
#   $1 - Destination directory
#   $2 - Container name
################################################################################
show_edit_instructions() {
    local DEST_DIR=$1
    local CONTAINER=$2
    
    echo
    log_info "Next steps:"
    echo
    echo "  1. Edit files in: $DEST_DIR"
    echo "  2. Copy modified file back to container:"
    echo "     docker cp $DEST_DIR/filename $CONTAINER:$CONFIG_DIR_IN_CONTAINER/filename"
    echo "  3. Restart container to apply changes:"
    echo "     docker restart $CONTAINER"
    echo
    log_info "Or use the change_device_id.sh script for device ID changes"
}

################################################################################
# Main Execution
################################################################################
main() {
    # Parse arguments
    if [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
        usage
        exit 0
    fi
    
    # Set defaults and parse arguments
    local BASE_DEST="${1:-$DEFAULT_DEST}"
    local CONTAINER="${2:-$DEFAULT_CONTAINER}"
    
    # Create timestamped subdirectory unless destination is current directory
    local TIMESTAMP=$(date +%Y%m%d-%H%M%S)
    local DEST_DIR
    
    if [ "$BASE_DEST" == "." ]; then
        # Copy directly to current directory (no timestamp subdirectory)
        DEST_DIR="."
        log_warning "Copying directly to current directory (no timestamp subdirectory)"
    else
        # Create timestamped subdirectory
        DEST_DIR="${BASE_DEST}/${TIMESTAMP}"
    fi
    
    # Display operation summary
    echo
    log_info "Config Files Export Operation"
    log_info "=============================="
    log_info "Container:    $CONTAINER"
    log_info "Source:       $CONFIG_DIR_IN_CONTAINER"
    log_info "Destination:  $DEST_DIR"
    echo
    
    # Execute export workflow
    validate_container "$CONTAINER" || exit 1
    echo
    
    verify_config_dir_exists "$CONTAINER" || exit 1
    echo
    
    list_config_files "$CONTAINER" || exit 1
    echo
    
    # Confirm before copying
    read -p "Continue with copy? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_warning "Copy cancelled by user"
        exit 0
    fi
    echo
    
    create_destination "$DEST_DIR" || exit 1
    echo
    
    copy_config_files "$CONTAINER" "$DEST_DIR" || {
        log_warning "Some files failed to copy, but continuing..."
    }
    echo
    
    show_copied_files "$DEST_DIR"
    
    show_edit_instructions "$DEST_DIR" "$CONTAINER"
    
    log_success "Config files export completed!"
    echo
}

# Run main function
main "$@"
