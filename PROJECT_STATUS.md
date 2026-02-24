# EvoBot - Recursive Self-Evolving Robot

## Overview
A Raspberry Pi 3-based mobile robot that recursively self-evolves its own software. Claude builds the code and logic; Scott handles wiring and mechanical assembly. Hardware inventory includes assorted motors, sensors, and modules.

## Hardware
- **Brain:** Raspberry Pi 3 Model B Rev 1.2 — Board #1, serial c28bf021
- **OS:** Raspbian Bookworm 12 (kernel 6.12.47, armv7l)
- **Static IP:** 192.168.1.51
- **Hostname:** evobot
- **SSH:** Key-based auth (evobot_ed25519)

## Network
- **LAN:** 192.168.1.0/24
- **Gateway:** 192.168.1.1 (confirmed)
- **DNS:** 192.168.1.1
- **Other devices:** Sensor Pi at .48, Home Assistant at .151

## Project Structure (Workstation)
```
Documents/EvoBot/
├── PROJECT_STATUS.md    ← this file
├── docs/                ← setup guides, architecture notes
├── code/                ← robot software (mirrored to Pi)
├── configs/             ← config files, systemd units
├── logs/                ← session logs, debug output
└── hardware/            ← wiring diagrams, parts inventory
```

## Project Structure (Pi - /home/scott/evobot/)
```
/home/scott/evobot/
├── README.md            ← on-device documentation
├── src/                 ← robot source code
├── configs/             ← local config copies
└── logs/                ← runtime logs
```

## Setup Log
- **2026-02-24:** Project created. Found Pi #1 at .17 (DHCP). Set static IP .51 via nmcli. Hostname set to evobot. SSH key auth configured (evobot_ed25519). WiFi also active on wlan0 (.43 DHCP). Project dirs created on Pi at ~/evobot/.

## SSH Access
```bash
# From WSL (alias configured in ~/.ssh/config):
ssh evobot

# Or explicitly:
ssh -i ~/.ssh/evobot_ed25519 scott@192.168.1.51
```

## MAC Addresses
- **eth0:** B8:27:EB:8B:F0:21
- **wlan0:** B8:27:EB:DE:A5:74

## Status: READY FOR DEVELOPMENT
