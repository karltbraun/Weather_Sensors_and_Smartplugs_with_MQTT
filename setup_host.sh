#!/bin/bash

# Check if .env exists
if [ -f .env ]; then
    echo ".env file already exists!"
    exit 1
fi

# Get hostname
HOST_ID=$(hostname)

# Copy template
cp .env.template .env

# Prompt for values
read -p "MQTT Broker Address: " broker

username=""
password=""
read -p "Does your MQTT Broker require a username and password? (y/N): " require_auth
if [[ "$require_auth" =~ ^[Yy]$ ]]; then
    read -p "MQTT Username: " username
    read -s -p "MQTT Password: " password
    echo
fi

# Update .env file
sed -i '' "s/broker_address_here/$broker/" .env
sed -i '' "s/username_here/$username/" .env
sed -i '' "s/password_here/$password/" .env
sed -i '' "s/host_identifier_here/$HOST_ID/" .env

echo ".env file created successfully!"
