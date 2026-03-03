# EvoBot - Recursive Self-Evolving Robot

## Overview
A Raspberry Pi 3-based mobile robot that recursively self-evolves its own software. Claude is full architect (mechanics, electronics, software, safety, iteration); Scott handles physical assembly, wiring, and fabrication.

## Current Phase: PHYSICAL BUILD IN PROGRESS

### What's Done
- **Bottom deck:** Laser cut from plywood, all holes and features verified
- **Motor mounts:** STL generated, 3MF slicer project ready, printing
- **Sensor brackets:** Redesigned as L-bracket with channel rails (v2), STL clean
- **All STL parts:** motor_mount, caster_skid, standoff, sensor_bracket, webcam_mount
- **All DXF plates:** bottom_deck, top_deck (with bracket bolt holes), all_parts
- **Pi code:** Written (main.py, motors.py, sensors.py, inference.py, safety.py, evolution.py, logger.py) — NOT deployed to Pi yet
- **ESP32 firmware:** PlatformIO project written — NOT compiled/flashed yet
- **Pi 3 (Board #1):** Configured at 192.168.1.51, SSH key auth, project dirs ready

### What's Next
- Print remaining STL parts (caster skid, standoffs, sensor brackets, webcam mount)
- Laser cut top deck
- Assemble chassis: mount motors, caster, standoffs, wire Pi + ESP32
- Deploy Pi code, compile/flash ESP32
- First power-on test

## Hardware
- **Brain:** Raspberry Pi 3 Model B Rev 1.2 — Board #1, serial c28bf021
- **OS:** Raspbian Bookworm 12 (kernel 6.12.47, armv7l)
- **Static IP:** 192.168.1.51
- **Hostname:** evobot
- **SSH:** `ssh evobot` (key auth, ~/.ssh/evobot_ed25519)

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
├── hardware/            ← photos, wiring diagrams, parts inventory
└── builds/reference-01/ ← build-specific files
    └── hardware/cad/    ← generate_stl.py, generate_dxf.py, STLs, DXFs
```

## Project Structure (Pi - /home/scott/evobot/)
```
/home/scott/evobot/
├── README.md            ← on-device documentation
├── src/                 ← robot source code
├── configs/             ← local config copies
└── logs/                ← runtime logs
```

## CAD Status
- **generate_stl.py:** 5 parts — motor_mount, caster_skid, standoff, sensor_bracket, webcam_mount
- **generate_dxf.py:** bottom_deck, top_deck (with sensor bracket bolt holes), all_parts
- **Sensor bracket v2:** L-bracket with channel rails, real M3 bolt holes (box_with_holes_mesh), axis-aligned geometry, 0 non-manifold edges
- **Top deck DXF:** Updated with 4x M3 bracket bolt holes (2 per sensor, 35mm apart)

## Build Photos
- `hardware/bottom_deck_cut.jpg` — Laser-cut bottom deck (plywood, all features cut/engraved)

## Setup Log
- **2026-02-24:** Project created. Pi #1 configured at .51. SSH key auth. Project dirs on Pi.
- **2026-03-02:** Bottom deck laser cut. Motor mounts printing. Sensor bracket redesigned (L-bracket v2). Top deck DXF updated with bracket bolt holes. All STL/DXF files regenerated.

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
