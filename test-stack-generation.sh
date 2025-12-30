#!/usr/bin/env bash
################################################################################
# Test Script for Portainer Stack Generation
################################################################################
# Purpose: Validate that generated stack files have correct PUB_SOURCE values
#          and network configurations based on new requirements:
#          - Default: PUB_SOURCE=Mu, network_mode=host, NO commented alternatives
#          - All hosts (ROSA, TWIX, VULTR2): network_mode=host by default
#          - NO commented PUB_SOURCE alternatives in any file
#          - Bridge networking only when explicitly specified
################################################################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0

echo "================================"
echo "Stack Generation Test Suite"
echo "================================"
echo ""

# Test function for PUB_SOURCE
test_pub_source() {
    local file="$1"
    local expected_value="$2"
    
    echo -n "Testing $file for PUB_SOURCE=$expected_value... "
    
    # Count active PUB_SOURCE lines with expected value
    local active_count=$(grep "PUB_SOURCE=$expected_value" "$file" | grep -c "^      - PUB_SOURCE=" || echo "0")
    
    # Check for any commented PUB_SOURCE alternatives (should be NONE per new requirements)
    local comment_count=$(grep "^      # - PUB_SOURCE=" "$file" 2>/dev/null | wc -l | tr -d ' ')
    
    if [[ "$active_count" -eq 2 ]]; then
        if [[ "$comment_count" -eq 0 ]]; then
            echo -e "${GREEN}PASS${NC} (2 active, 0 commented)"
            ((PASS++))
            return 0
        else
            echo -e "${RED}FAIL${NC} (Found $comment_count commented PUB_SOURCE lines, expected 0)"
            ((FAIL++))
            return 1
        fi
    else
        echo -e "${RED}FAIL${NC} (Expected 2 active PUB_SOURCE=$expected_value, found $active_count)"
        ((FAIL++))
        return 1
    fi
}

# Test function for network configuration
test_network_config() {
    local file="$1"
    local expected_mode="$2"  # "host" or "bridge"
    
    echo -n "Testing $file for network_mode=$expected_mode... "
    
    if [[ "$expected_mode" == "host" ]]; then
        # Should have active network_mode: host (not commented)
        local active_mode=$(grep "^    network_mode: host" "$file" 2>/dev/null | wc -l | tr -d ' ')
        local commented_networks=$(grep "^    # networks:" "$file" 2>/dev/null | wc -l | tr -d ' ')
        
        if [[ "$active_mode" -ge 2 ]]; then
            echo -e "${GREEN}PASS${NC} (host networking: $active_mode active network_mode lines)"
            ((PASS++))
            return 0
        else
            echo -e "${RED}FAIL${NC} (Expected active network_mode: host, found $active_mode lines)"
            ((FAIL++))
            return 1
        fi
    else
        # Bridge mode: should have commented network_mode and active networks
        local commented_mode=$(grep "^    # network_mode: host" "$file" 2>/dev/null | wc -l | tr -d ' ')
        local active_networks=$(grep "^    networks:" "$file" 2>/dev/null | wc -l | tr -d ' ')
        
        if [[ "$commented_mode" -ge 2 && "$active_networks" -ge 2 ]]; then
            echo -e "${GREEN}PASS${NC} (bridge networking configured)"
            ((PASS++))
            return 0
        else
            echo -e "${RED}FAIL${NC} (Expected bridge mode, found commented_mode=$commented_mode, active_networks=$active_networks)"
            ((FAIL++))
            return 1
        fi
    fi
}

echo "--- Generating Files for Testing ---"
echo "Generating default..."
./generate-portainer-stacks.sh > /dev/null 2>&1
echo "Generating all standard hosts..."
./generate-portainer-stacks.sh --all > /dev/null 2>&1
echo ""

echo "--- Test 1: Default (no options) ---"
echo "Requirement: PUB_SOURCE=Mu, network_mode=host, NO commented alternatives"
test_pub_source "portainer-stack.yml" "Mu"
test_network_config "portainer-stack.yml" "host"
echo ""

echo "--- Test 2: ROSA Host ---"
echo "Requirement: PUB_SOURCE=ROSA, network_mode=host, NO commented alternatives"
test_pub_source "portainer-stack-rosa.yml" "ROSA"
test_network_config "portainer-stack-rosa.yml" "host"
echo ""

echo "--- Test 3: TWIX Host ---"
echo "Requirement: PUB_SOURCE=TWIX, network_mode=host, NO commented alternatives"
test_pub_source "portainer-stack-twix.yml" "TWIX"
test_network_config "portainer-stack-twix.yml" "host"
echo ""

echo "--- Test 4: VULTR2 VM ---"
echo "Requirement: PUB_SOURCE=VULTR2, network_mode=host, NO commented alternatives"
test_pub_source "portainer-stack-vultr2.yml" "VULTR2"
test_network_config "portainer-stack-vultr2.yml" "host"
echo ""

echo "--- Test 5: Custom PUB_SOURCE with default (host) networking ---"
./generate-portainer-stacks.sh --pub_source=TestHost > /dev/null 2>&1
test_pub_source "portainer-stack-testhost.yml" "TestHost"
test_network_config "portainer-stack-testhost.yml" "host"
rm -f portainer-stack-testhost.yml
echo ""

echo "--- Test 6: Custom PUB_SOURCE with bridge networking ---"
./generate-portainer-stacks.sh --pub_source=TestBridge --network_mode=bridge > /dev/null 2>&1
test_pub_source "portainer-stack-testbridge.yml" "TestBridge"
test_network_config "portainer-stack-testbridge.yml" "bridge"
rm -f portainer-stack-testbridge.yml
echo ""

echo "--- Test 7: Only network_mode specified (should use Mu) ---"
./generate-portainer-stacks.sh --network_mode=bridge > /dev/null 2>&1
test_pub_source "portainer-stack-mu.yml" "Mu"
test_network_config "portainer-stack-mu.yml" "bridge"
rm -f portainer-stack-mu.yml
echo ""

echo "================================"
echo "Test Results"
echo "================================"
echo -e "${GREEN}PASSED: $PASS${NC}"
echo -e "${RED}FAILED: $FAIL${NC}"
echo ""

if [[ $FAIL -eq 0 ]]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
