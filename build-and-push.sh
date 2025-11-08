#!/bin/bash

################################################################################
# Multi-platform Docker Build and Push Script
################################################################################
# Purpose: Automates building and publishing weather-republish and shelly 
#          device monitoring Docker images to Docker Hub for multiple CPU 
#          architectures (amd64, arm64, arm/v7).
#
# Author: Karl T. Braun
# Last Modified: 2025-11-08
# 
# Requirements:
#   - Docker Engine with buildx plugin (Docker Desktop includes this)
#   - Docker Hub account credentials
#   - Git (optional, for version detection)
#
# Usage: ./build-and-push.sh [OPTIONS]
#        See usage() function or run with -h for detailed help
################################################################################

set -e  # Exit immediately if any command returns non-zero status

################################################################################
# Configuration Variables
################################################################################
# Docker Hub username - change this if forking/adapting this script
DOCKER_USERNAME="karltbraun"

# Docker image name - must match the image referenced in docker-compose.yml
# and portainer-stack.yml
IMAGE_NAME="weather-sensors"

# Target platforms for multi-architecture builds
# Format: comma-separated list of "os/arch" or "os/arch/variant"
# Common platforms:
#   - linux/amd64: Intel/AMD 64-bit (most servers, desktops)
#   - linux/arm64: 64-bit ARM (Apple Silicon, newer Raspberry Pi OS 64-bit)
#   - linux/arm/v7: 32-bit ARM v7 (Raspberry Pi 3/4 with 32-bit OS)
#   - linux/arm/v6: 32-bit ARM v6 (Raspberry Pi Zero, Pi 1)
PLATFORMS="linux/amd64,linux/arm64,linux/arm/v7"

################################################################################
# ANSI Color Codes for Terminal Output
################################################################################
# These codes provide colored output for better readability in terminal logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color - resets to default terminal color

################################################################################
# Logging Helper Functions
################################################################################
# These functions provide consistent, color-coded logging output throughout
# the script. All log messages are written to stdout.

# Log informational messages (blue)
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Log success messages (green)
log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Log warning messages (yellow) - for non-fatal issues
log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Log error messages (red) - typically followed by exit
log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

################################################################################
# Function: check_requirements
################################################################################
# Purpose: Validates that all required tools are installed and accessible
#
# Checks:
#   1. Docker CLI is installed and in PATH
#   2. Docker Engine is running and accessible
#   3. Docker buildx plugin is available (required for multi-platform builds)
#
# Exit Codes:
#   0 - All requirements met
#   1 - Missing Docker or buildx
#
# Dependencies: docker, docker buildx
################################################################################
check_requirements() {
    log_info "Checking requirements..."
    
    # Verify Docker CLI is available
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Display Docker version for debugging purposes
    # Note: Requires Docker Engine to be running
    DOCKER_VERSION=$(docker version --format '{{.Server.Version}}' 2>/dev/null || echo "unknown")
    log_info "Docker version: $DOCKER_VERSION"
    
    # Verify buildx plugin is available
    # buildx is required for cross-platform builds and comes with Docker Desktop
    # For Docker Engine, install with: apt-get install docker-buildx-plugin
    if ! docker buildx version &> /dev/null; then
        log_error "Docker buildx is not available. Please update Docker to a version that supports buildx."
        exit 1
    fi
    
    log_success "All requirements met"
}

################################################################################
# Function: check_docker_login
################################################################################
# Purpose: Verifies authentication to Docker Hub and prompts for login if needed
#
# Behavior:
#   - If already logged in as DOCKER_USERNAME: continues silently
#   - If not logged in: prompts for Docker Hub credentials interactively
#
# Notes:
#   - Docker credentials are stored in ~/.docker/config.json
#   - For CI/CD: use 'docker login -u user -p password' or access tokens
#   - This function does not handle authentication errors; docker login will
#     exit with non-zero status if credentials are invalid
#
# Dependencies: docker
################################################################################
check_docker_login() {
    log_info "Checking Docker Hub authentication..."
    
    # Check if currently logged in with the correct username
    # 'docker info' shows current authentication state
    if ! docker info 2>&1 | grep -q "Username: $DOCKER_USERNAME"; then
        log_warning "Not logged in to Docker Hub as $DOCKER_USERNAME"
        log_info "Attempting to log in..."
        # Interactive login - will prompt for username and password/token
        docker login
    else
        log_success "Already logged in to Docker Hub as $DOCKER_USERNAME"
    fi
}

################################################################################
# Function: setup_buildx
################################################################################
# Purpose: Creates or activates a buildx builder instance for multi-platform builds
#
# Behavior:
#   - If builder "multiarch-builder" exists: activates it
#   - If builder doesn't exist: creates new docker-container builder
#
# Builder Details:
#   - Name: multiarch-builder (reusable across builds)
#   - Driver: docker-container (isolated build environment)
#   - Bootstrap: pre-starts the builder container for faster builds
#
# Why docker-container driver?
#   - Default 'docker' driver can't build for multiple platforms simultaneously
#   - docker-container driver uses QEMU for cross-platform emulation
#   - Allows building arm64 images on amd64 hosts and vice versa
#
# Notes:
#   - Builder persists between script runs for efficiency
#   - To remove: docker buildx rm multiarch-builder
#   - To inspect: docker buildx inspect multiarch-builder
#
# Dependencies: docker buildx
################################################################################
setup_buildx() {
    log_info "Setting up Docker buildx builder..."
    
    BUILDER_NAME="multiarch-builder"
    
    # Check if the builder instance already exists
    # If it exists, just activate it instead of creating a new one
    if docker buildx inspect "$BUILDER_NAME" &> /dev/null; then
        log_info "Builder '$BUILDER_NAME' already exists"
        docker buildx use "$BUILDER_NAME"
    else
        log_info "Creating new builder '$BUILDER_NAME'..."
        # Create new builder with docker-container driver
        # --bootstrap: start builder immediately to verify it works
        # --use: make this the active builder
        docker buildx create --name "$BUILDER_NAME" --driver docker-container --bootstrap --use
    fi
    
    log_success "Buildx builder configured"
}

################################################################################
# Function: get_version
################################################################################
# Purpose: Auto-detects an appropriate version tag for the Docker image
#
# Version Detection Strategy (in order of precedence):
#   1. Git Tag: If HEAD has an exact tag (e.g., v1.2.3), use that
#   2. Git Commit: If in a git repo, use short commit SHA (e.g., git-a1b2c3d)
#   3. Timestamp: Fallback to current datetime (e.g., 20251108-143022)
#
# Return Value:
#   Outputs version string to stdout for capture by caller
#   (Log messages go to stderr to avoid contaminating the version string)
#
# Examples:
#   - Tagged release:     "v1.2.3"
#   - Development build:  "git-a1b2c3d"
#   - No git repo:        "20251108-143022"
#
# Notes:
#   - Requires git to be installed for git-based detection
#   - Timestamp format: YYYYMMDD-HHMMSS (sortable, no special chars)
#   - Used to tag Docker images for traceability
#   - CRITICAL: Only echo the VERSION to stdout; all other output to stderr
#
# Dependencies: git (optional), date
################################################################################
get_version() {
    local VERSION=""
    
    # Strategy 1: Try to get version from git tag on current commit
    # Only succeeds if HEAD is exactly at a tagged commit
    if VERSION=$(git describe --tags --exact-match 2>/dev/null); then
        log_info "Using git tag: $VERSION" >&2
    # Strategy 2: Try to get short commit hash
    # Format as "git-<short-sha>" to distinguish from tagged releases
    elif git rev-parse --short HEAD &>/dev/null; then
        VERSION="git-$(git rev-parse --short HEAD)"
        log_info "Using git commit: $VERSION" >&2
    # Strategy 3: Fallback to timestamp if not in git repo
    else
        VERSION=$(date +%Y%m%d-%H%M%S)
        log_info "Using timestamp: $VERSION" >&2
    fi
    
    # Return version string to caller (stdout only - no contamination)
    echo "$VERSION"
}

################################################################################
# Function: build_and_push
################################################################################
# Purpose: Builds Docker image for multiple platforms and pushes to Docker Hub
#
# Parameters:
#   $1 - VERSION: Docker image version tag (e.g., "v1.2.3", "git-abc123")
#   $2 - TAG_LATEST: Boolean ("true"/"false") whether to also tag as "latest"
#
# Process:
#   1. Constructs buildx arguments array with platform and tag specifications
#   2. Optionally adds "latest" tag if TAG_LATEST=true
#   3. Executes multi-platform build using docker buildx
#   4. Automatically pushes to Docker Hub (--push flag)
#
# Build Process:
#   - Uses Dockerfile in current directory (build context: .)
#   - Builds for all platforms specified in $PLATFORMS simultaneously
#   - Each platform uses appropriate base image and emulation if needed
#   - Creates multi-architecture manifest that Docker can pull from
#
# Time Considerations:
#   - Multi-platform builds can take 10-30+ minutes depending on:
#     * Number of platforms (3 platforms = 3x build time)
#     * Image complexity and dependencies
#     * Network speed for base image pulls and push to registry
#     * Build cache availability
#
# Error Handling:
#   - Exits on any build error due to 'set -e' at script start
#   - No cleanup needed; buildx handles temporary build containers
#
# Dependencies: docker buildx, active builder, Docker Hub authentication
################################################################################
build_and_push() {
    local VERSION=$1
    local TAG_LATEST=$2
    
    log_info "Building multi-platform image..."
    log_info "Platforms: $PLATFORMS"
    log_info "Image: $DOCKER_USERNAME/$IMAGE_NAME"
    log_info "Version tag: $VERSION"
    
    # Initialize build arguments array
    # Using array ensures proper handling of arguments with spaces
    BUILD_ARGS=(
        --platform "$PLATFORMS"
        --tag "$DOCKER_USERNAME/$IMAGE_NAME:$VERSION"
    )
    
    # Conditionally add 'latest' tag
    # This creates a second tag pointing to the same image manifest
    if [ "$TAG_LATEST" = true ]; then
        BUILD_ARGS+=(--tag "$DOCKER_USERNAME/$IMAGE_NAME:latest")
        log_info "Also tagging as: latest"
    fi
    
    # Add push flag to automatically push to registry after build
    # Without this, image only stays in local build cache
    BUILD_ARGS+=(--push)
    
    # Add build context (current directory)
    # This is where Docker looks for Dockerfile and files to COPY
    BUILD_ARGS+=(.)
    
    log_info "Running docker buildx build..."
    log_info "Note: This may take 10-30+ minutes for multi-platform build"
    
    # Execute the build
    # "${BUILD_ARGS[@]}" expands array elements as separate arguments
    docker buildx build "${BUILD_ARGS[@]}"
    
    log_success "Build and push completed!"
    log_success "Image: $DOCKER_USERNAME/$IMAGE_NAME:$VERSION"
    if [ "$TAG_LATEST" = true ]; then
        log_success "Image: $DOCKER_USERNAME/$IMAGE_NAME:latest"
    fi
}

################################################################################
# Function: usage
################################################################################
# Purpose: Displays help text with script usage, options, and examples
#
# Called when: User runs script with -h or --help, or provides invalid arguments
################################################################################
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Multi-platform Docker build and push script for $IMAGE_NAME

OPTIONS:
    -v, --version VERSION    Specify version tag (default: auto-detect from git or timestamp)
    -l, --latest             Also tag as 'latest' (default: false)
    -p, --platforms PLATFORMS Comma-separated list of platforms (default: $PLATFORMS)
    -h, --help               Display this help message

EXAMPLES:
    $0                       # Build with auto-detected version
    $0 -v v1.2.3 -l          # Build version v1.2.3 and tag as latest
    $0 --version v1.2.3      # Build only version v1.2.3
    $0 -l                    # Build with auto-detected version and tag as latest

PLATFORMS:
    Default platforms: $PLATFORMS
    Common options:
        - linux/amd64        (x86_64, Intel/AMD 64-bit)
        - linux/arm64        (ARM 64-bit, Apple Silicon, Raspberry Pi 4 64-bit)
        - linux/arm/v7       (ARM 32-bit, Raspberry Pi 3/4 32-bit)
        - linux/arm/v6       (ARM 32-bit, Raspberry Pi Zero/1)

EOF
}

################################################################################
# Function: parse_args
################################################################################
# Purpose: Parses command-line arguments and sets build configuration
#
# Parameters: All command-line arguments passed to script ($@)
#
# Supported Arguments:
#   -v, --version VERSION     Explicit version tag (overrides auto-detection)
#   -l, --latest              Also tag image as "latest"
#   -p, --platforms PLATFORMS Override default platform list
#   -h, --help                Display usage and exit
#
# Return Value:
#   Outputs "VERSION|TAG_LATEST" string to stdout for parsing by caller
#   Format: "v1.2.3|true" or "git-abc123|false"
#
# Notes:
#   - Unknown arguments cause error and display usage
#   - Version auto-detection runs if -v not specified
#   - PLATFORMS is a module-level variable, modified in place if -p used
#
# Dependencies: get_version(), usage()
################################################################################
parse_args() {
    VERSION=""
    TAG_LATEST=false
    
    # Process all arguments using shift-based parsing
    while [[ $# -gt 0 ]]; do
        case $1 in
            -v|--version)
                # User-specified version tag
                VERSION="$2"
                shift 2  # Skip flag and value
                ;;
            -l|--latest)
                # Flag to also tag as 'latest'
                TAG_LATEST=true
                shift  # Skip flag only
                ;;
            -p|--platforms)
                # Override default platform list
                # Modifies global PLATFORMS variable
                PLATFORMS="$2"
                shift 2  # Skip flag and value
                ;;
            -h|--help)
                # Display help and exit successfully
                usage
                exit 0
                ;;
            *)
                # Unrecognized argument - show error and usage
                log_error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
    
    # Auto-detect version if user didn't provide one
    if [ -z "$VERSION" ]; then
        VERSION=$(get_version)
    fi
    
    # Return version and latest flag as pipe-delimited string
    # Caller will split this using cut or IFS
    echo "$VERSION|$TAG_LATEST"
}

################################################################################
# Function: main
################################################################################
# Purpose: Main script orchestration - coordinates all build steps
#
# Parameters: All command-line arguments ($@)
#
# Execution Flow:
#   1. Parse command-line arguments
#   2. Run pre-flight checks (Docker, buildx, authentication)
#   3. Setup buildx builder for multi-platform builds
#   4. Display build summary and request user confirmation
#   5. Execute build and push
#   6. Display pull commands for convenience
#
# Exit Codes:
#   0 - Success (build completed and pushed)
#   0 - User cancelled at confirmation prompt
#   1 - Any error (Docker missing, auth failed, build failed, etc.)
#
# Interactive Elements:
#   - May prompt for Docker Hub login if not authenticated
#   - Always prompts for confirmation before starting build
#   - Confirmation can be bypassed by piping 'y' to stdin:
#     echo 'y' | ./build-and-push.sh -v v1.2.3 -l
#
# Notes:
#   - This is the entry point when script is executed
#   - All output goes to stdout/stderr for easy redirection
#   - Build times vary: expect 10-30+ minutes for multi-platform builds
################################################################################
main() {
    log_info "Weather Sensors Multi-Platform Docker Build"
    log_info "============================================="
    echo
    
    # Parse and extract command-line arguments
    # Returns pipe-delimited string: "version|tag_latest_bool"
    RESULT=$(parse_args "$@")
    VERSION=$(echo "$RESULT" | cut -d'|' -f1)
    TAG_LATEST=$(echo "$RESULT" | cut -d'|' -f2)
    
    # Pre-flight checks - ensure all requirements are met
    check_requirements
    echo
    check_docker_login
    echo
    setup_buildx
    echo
    
    # Display build configuration summary for user review
    log_info "Ready to build and push:"
    log_info "  Image: $DOCKER_USERNAME/$IMAGE_NAME"
    log_info "  Version: $VERSION"
    log_info "  Tag as latest: $TAG_LATEST"
    log_info "  Platforms: $PLATFORMS"
    echo
    
    # Interactive confirmation before starting lengthy build process
    # Accepts 'y' or 'Y', rejects anything else (including just Enter)
    read -p "Continue? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_warning "Build cancelled by user"
        exit 0
    fi
    
    echo
    # Execute the actual build and push operation
    build_and_push "$VERSION" "$TAG_LATEST"
    echo
    
    # Success message and helpful next steps
    log_success "All done! 🎉"
    echo
    log_info "To pull the image:"
    log_info "  docker pull $DOCKER_USERNAME/$IMAGE_NAME:$VERSION"
    if [ "$TAG_LATEST" = true ]; then
        log_info "  docker pull $DOCKER_USERNAME/$IMAGE_NAME:latest"
    fi
}

################################################################################
# Script Entry Point
################################################################################
# Execute main function with all command-line arguments
# This allows the script to be sourced without auto-executing (for testing)
main "$@"
