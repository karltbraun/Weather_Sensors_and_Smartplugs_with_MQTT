# Handoff

Updated: 2026-06-10T00:00:00
Project: /Users/karl/Development/KTB/Weather_Sensors_and_Smartplugs_with_MQTT
Branch: main
Commit: e9e47fc Fix protocol lookup: remove config volume mounts and handle unknown protocols gracefully
Uncommitted: no

## Now
Project is stable; last session fixed protocol lookup by removing config volume mounts and handling unknown protocols gracefully.

## Done
- Migrated all stacks from VULTR2 to VULTR3 (broker: n-vultr3)
- Added PI2 deployment support in `generate-portainer-stacks.sh`
- Fixed startup log format error; added netcat to container image
- Fixed protocol lookup: removed config volume mounts, added graceful handling for unknown protocols
- Updated `local_sensors.json` with current sensor config

## Next
- Consider moving `DEVICE_ROOM_MAP` from `message_manager_shelly.py` to a JSON config file (existing TODO)
- Align weather sensor namespace (`<ROOT>/<host>/sensors/...`) with smart plug namespace (`<ROOT>/<host>/<room>/smartplugs/...`) for room-level consistency

## Blockers
- none

## Touched
- `generate-portainer-stacks.sh` — PI2 support, VULTR3 migration
- `portainer-stack-pi2.yml`, `portainer-stack-vultr3.yml` — generated stacks
- `config/broker_config.py` — broker config indirection (active: n-vultr3)
- `src/managers/message_manager_shelly.py` — DEVICE_ROOM_MAP
- Docker image / container config — netcat added, config volume mounts removed

## Verify
- not run
