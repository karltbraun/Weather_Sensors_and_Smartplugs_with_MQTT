#!/usr/bin/env bash
################################################################################
# Generate Portainer Stack Files from Template
################################################################################
# Purpose: Creates deployment-specific portainer stack YAML files from a 
#          single template to avoid duplication and sync errors.
#
# Author: Karl T. Braun
# Last Modified: 2025-12-30
#
# Usage: ./generate-portainer-stacks.sh [OPTIONS]
#        ./generate-portainer-stacks.sh --ROSA --TWIX
#        ./generate-portainer-stacks.sh --all
#        ./generate-portainer-stacks.sh --pub_source=MyHost --network_mode=bridge
################################################################################

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_FILE="${SCRIPT_DIR}/portainer-stack.template.yml"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to display usage
usage() {
    echo "Generate Portainer Stack Files from Template"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --pub_source=VALUE      Generate stack with custom PUB_SOURCE value"
    echo "  --network_mode=MODE     Specify network mode (host or bridge), default: host"
    echo "  --ROSA                  Generate stack for ROSA host"
    echo "  --TWIX                  Generate stack for TWIX host"
    echo "  --VULTR2                Generate stack for VULTR2 VM"
    echo "  --all                   Generate all standard stacks (ROSA, TWIX, VULTR2)"
    echo "  --help, -h              Display this help message"
    echo ""
    echo "Examples:"
    echo "  $0                              # Generate default (PUB_SOURCE=Mu, host networking)"
    echo "  $0 --ROSA --TWIX                # Generate ROSA and TWIX stacks"
    echo "  $0 --all                        # Generate all standard stacks"
    echo "  $0 --pub_source=MyHost          # Generate stack with PUB_SOURCE=MyHost"
    echo "  $0 --pub_source=Test --network_mode=bridge  # Custom with bridge networking"
    echo ""
    echo "Output Files:"
    echo "  default                 → portainer-stack.yml"
    echo "  --pub_source=VALUE      → portainer-stack-<value>.yml (lowercase)"
    echo "  --ROSA                  → portainer-stack-rosa.yml"
    echo "  --TWIX                  → portainer-stack-twix.yml"
    echo "  --VULTR2                → portainer-stack-vultr2.yml"
    echo ""
    echo "Network Modes:"
    echo "  host   - Use host networking (default for all deployments)"
    echo "  bridge - Use Docker bridge networking"
}

# Function to generate a stack file
# Args: pub_source, network_mode, output_file
generate_stack() {
    local pub_source="$1"
    local network_mode="$2"  # "bridge" or "host"
    local output_file="$3"
    
    echo -e "${YELLOW}Generating: ${output_file}${NC}"
    
    # Validate network mode
    if [[ "$network_mode" != "host" && "$network_mode" != "bridge" ]]; then
        echo -e "${RED}Error: Invalid network_mode '$network_mode'. Must be 'host' or 'bridge'${NC}"
        exit 1
    fi
    
    # Determine network configuration based on mode
    local deployment_scenario
    local top_level_network_section
    if [[ "$network_mode" == "host" ]]; then
        local network_config="    network_mode: host\n    # networks:\n      # - weather-sensors"
        local network_comment="Host networking enabled\n    #   - 'network_mode: host' is active\n    #   - 'networks:' is commented out\n    # To use bridge networking instead:\n    #   - Comment 'network_mode: host'\n    #   - Uncomment 'networks: - weather-sensors'"
        deployment_scenario="host-networking"
        # For host networking, comment out the top-level networks section
        top_level_network_section="# Using host networking mode - no bridge network needed\n# Services connect to localhost to reach MQTT broker on same VM\n\n# networks:\n#   weather-sensors:\n#     driver: bridge\n#     name: weather-sensors-network"
    else
        local network_config="    # network_mode: host\n    networks:\n      - weather-sensors"
        local network_comment="Bridge networking enabled\n    #   - 'networks:' assignment is active\n    #   - 'network_mode: host' is commented out\n    # To use host networking instead:\n    #   - Uncomment 'network_mode: host'\n    #   - Comment 'networks:' assignment"
        deployment_scenario="bridge-networking"
        # For bridge networking, keep the networks section active
        top_level_network_section="networks:\n  weather-sensors:\n    driver: bridge\n    name: weather-sensors-network"
    fi
    
    # Deployment comment - no PUB_SOURCE examples in any file
    local deployment_comment="Configuration for ${pub_source}\n    #  BROKER_NAME=n-vultr2\n    #  PUB_SOURCE=${pub_source}\n    #  network_mode=${network_mode}"
    local pub_source_examples="      # PUB_SOURCE is set to ${pub_source} for this deployment"
    
    # Read template and perform replacements using awk
    awk -v network_config="$network_config" \
        -v network_comment="$network_comment" \
        -v deployment_scenario="$deployment_scenario" \
        -v pub_source="$pub_source" \
        -v pub_source_examples="$pub_source_examples" \
        -v deployment_comment="$deployment_comment" \
        -v top_level_network="$top_level_network_section" \
        '{
            line = $0
            gsub(/\{\{TOP_LEVEL_NETWORK\}\}/, top_level_network, line)
            gsub(/\{\{NETWORK_CONFIG\}\}/, network_config, line)
            gsub(/\{\{NETWORK_CONFIG_SHELLY\}\}/, network_config, line)
            gsub(/\{\{NETWORK_CONFIG_COMMENT\}\}/, network_comment, line)
            gsub(/\{\{DEPLOYMENT_SCENARIO\}\}/, deployment_scenario, line)
            gsub(/\{\{PUB_SOURCE\}\}/, pub_source, line)
            gsub(/\{\{PUB_SOURCE_EXAMPLES\}\}/, pub_source_examples, line)
            gsub(/\{\{BROKER_NAME\}\}/, "n-vultr2", line)
            gsub(/\{\{DEPLOYMENT_COMMENT\}\}/, deployment_comment, line)
            print line
        }' "${TEMPLATE_FILE}" > "${output_file}.tmp"
    
    # Add header comment
    cat > "${output_file}" << EOF
# Weather Sensors MQTT Stack for Portainer
# Copy this entire file content into Portainer > Stacks > Add Stack > Web Editor
# This file is GENERATED from portainer-stack.template.yml - DO NOT EDIT DIRECTLY

# =============================================================================
# Configuration:
#   PUB_SOURCE: ${pub_source}
#   Network Mode: ${network_mode}
#   DEPLOYMENT_SCENARIO: ${deployment_scenario}
# =============================================================================

EOF
    cat "${output_file}.tmp" >> "${output_file}"
    rm "${output_file}.tmp"
    
    echo -e "${GREEN}✓ Generated: ${output_file}${NC}"
}

# Main script logic
main() {
    local custom_pub_source=""
    local custom_network_mode="host"  # Default to host
    local targets=()
    
    # Parse command line arguments
    if [[ $# -eq 0 ]]; then
        # No arguments - generate default with Mu and host networking
        targets=("default")
    else
        for arg in "$@"; do
            case "$arg" in
                --help|-h|help)
                    usage
                    exit 0
                    ;;
                --pub_source=*)
                    custom_pub_source="${arg#*=}"
                    ;;
                --network_mode=*)
                    custom_network_mode="${arg#*=}"
                    # Validate network mode
                    if [[ "$custom_network_mode" != "host" && "$custom_network_mode" != "bridge" ]]; then
                        echo -e "${RED}Error: Invalid network_mode '$custom_network_mode'. Must be 'host' or 'bridge'${NC}"
                        exit 1
                    fi
                    ;;
                --ROSA)
                    targets+=("ROSA")
                    ;;
                --TWIX)
                    targets+=("TWIX")
                    ;;
                --VULTR2)
                    targets+=("VULTR2")
                    ;;
                --all)
                    targets=("ROSA" "TWIX" "VULTR2")
                    ;;
                *)
                    echo -e "${RED}Error: Unknown option '$arg'${NC}"
                    echo ""
                    usage
                    exit 1
                    ;;
            esac
        done
    fi
    
    # If custom pub_source or network_mode specified but no targets, create custom target
    if [[ -n "$custom_pub_source" || "$custom_network_mode" != "host" ]] && [[ ${#targets[@]} -eq 0 ]]; then
        targets=("custom")
    fi
    
    # If no targets set, generate default
    if [[ ${#targets[@]} -eq 0 ]]; then
        targets=("default")
    fi
    
    # Generate requested stacks
    for target in "${targets[@]}"; do
        case "$target" in
            default)
                # Default: PUB_SOURCE=Mu, network_mode=host
                local pub_src="${custom_pub_source:-Mu}"
                generate_stack "$pub_src" "$custom_network_mode" "${SCRIPT_DIR}/portainer-stack.yml"
                ;;
            custom)
                # Custom pub_source and/or network_mode
                local pub_src="${custom_pub_source:-Mu}"
                local lowercase_source=$(echo "$pub_src" | tr '[:upper:]' '[:lower:]')
                generate_stack "$pub_src" "$custom_network_mode" "${SCRIPT_DIR}/portainer-stack-${lowercase_source}.yml"
                ;;
            ROSA)
                # ROSA uses host networking (MQTT broker is a host service)
                generate_stack "ROSA" "host" "${SCRIPT_DIR}/portainer-stack-rosa.yml"
                ;;
            TWIX)
                # TWIX uses host networking (MQTT broker is a host service)
                generate_stack "TWIX" "host" "${SCRIPT_DIR}/portainer-stack-twix.yml"
                ;;
            VULTR2)
                # VULTR2 uses bridge networking (MQTT broker is also a container on same VM)
                generate_stack "VULTR2" "bridge" "${SCRIPT_DIR}/portainer-stack-vultr2.yml"
                ;;
        esac
    done
    
    echo ""
    echo -e "${GREEN}✓ Stack generation complete${NC}"
    echo ""
    echo "Files generated. You can now:"
    echo "  1. Review the generated files"
    echo "  2. Copy the appropriate file content to Portainer"
    echo "  3. Deploy the stack in Portainer"
}

# Check if template exists
if [[ ! -f "$TEMPLATE_FILE" ]]; then
    echo -e "${RED}Error: Template file not found: $TEMPLATE_FILE${NC}"
    exit 1
fi

# Run main function
main "$@"