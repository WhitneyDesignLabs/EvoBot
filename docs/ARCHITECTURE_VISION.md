# EvoBot Architecture Vision

## The Big Picture

EvoBot is a mid-size (~40-60cm) mobile robot platform designed to be:

- **Fully AI-architected** — Claude designs the mechanics, electronics, software, testing, and safety. Human handles physical assembly and wiring.
- **Open and reproducible** — Laser-cut wood chassis with parametric sizing, so anyone with a laser cutter (or a jigsaw and patience) can build one.
- **Self-evolving** — The robot evaluates its own performance and proposes improvements to its own code.
- **Constitutionally governed** — All behavior constrained by the Project Opengates Constitution (SOUL.md).
- **Local-first** — Core operation independent of internet. Cloud used only where local can't deliver.

## Platform Specifications (v1 Target)

| Parameter | Target | Notes |
|---|---|---|
| **Size** | ~40-60cm footprint | Mid-size floor rover |
| **Chassis** | Laser-cut wood (parametric) | Hand-cuttable fallback for accessibility |
| **Drive** | Differential drive (2 powered + 1 caster) | Simple, proven, maneuverable |
| **Motors (v1)** | Geared DC or NEMA 17 steppers | 12-24V, with encoder feedback |
| **Brain** | Raspberry Pi 3B | Primary compute — runs main logic |
| **Co-processors** | ESP32 / Pico / Arduino | Real-time motor control, sensor polling |
| **Battery** | 12V (v1), upgradeable to 24V | Custom pack or off-the-shelf |
| **Sensors (v1)** | Ultrasonic, IMU, encoders, camera | Minimum viable perception |
| **Communication** | WiFi (Pi built-in) | SSH for dev, API for cloud services |

## Design File Strategy

All mechanical designs will be provided as:

| Format | Purpose | Tool |
|---|---|---|
| **SVG/DXF** | Laser cutter / CNC router input | Any laser software |
| **STEP** | 3D printable parts, full assembly visualization | FreeCAD, Fusion 360, any CAD |
| **PDF** | Printable templates for hand-cutting | Paper, scissors, trace to wood |
| **Parametric source** | OpenSCAD or FreeCAD files with variables | Scale the whole robot by changing parameters |

### Parametric Design Principle

All dimensions derive from a small set of base parameters:

```
CHASSIS_WIDTH = 300mm    # Change this, everything scales
CHASSIS_LENGTH = 400mm
WHEEL_DIAMETER = 80mm
MOTOR_MOUNT_PATTERN = "NEMA17"  # or "geared_dc_37mm" etc.
```

Someone with a smaller laser bed can scale down. Someone wanting a bigger platform can scale up. The relationships between parts are maintained.

## Compute Architecture

### Distributed Processing Model

```
┌─────────────────────────────────────────────┐
│                   Pi 3B (Brain)             │
│  - Main logic loop                          │
│  - Decision making                          │
│  - Self-evolution engine                    │
│  - WiFi/SSH/API communication               │
│  - Camera processing (USB webcam)           │
├─────────────────────────────────────────────┤
│          Serial/I2C/SPI Bus                 │
├──────────────┬──────────────┬───────────────┤
│   ESP32/Pico │  ESP32/Pico  │  Arduino/Pico │
│  Motor Ctrl  │  Sensor Hub  │   Safety Mon  │
│  - PWM       │  - Ultrasonic│  - E-stop     │
│  - Encoders  │  - IMU       │  - Voltage    │
│  - PID loop  │  - Temp      │  - Current    │
│              │  - Light     │  - Watchdog   │
└──────────────┴──────────────┴───────────────┘
```

**Why distributed?**
- Pi 3 is not a real-time system (Linux scheduler jitter)
- Motor control PID loops need consistent microsecond timing → ESP32/Pico
- Safety monitoring must be independent of main brain → separate MCU
- Sensor polling at consistent rates → dedicated MCU
- If the Pi crashes, the safety MCU kills the motors (fail-safe per Constitution Art. 14)

### Inference Stack

```
┌──────────────────────────────────────────┐
│          EvoBot Software Stack           │
│                                          │
│  Robot Logic (Python on Pi)              │
│       │                                  │
│       ▼                                  │
│  Inference Interface (abstracted)        │
│       │                                  │
│       ├── Local: Ollama on LAN server    │
│       ├── Local: Small model on Pi       │
│       └── Cloud: Claude API (fallback)   │
│                                          │
│  TTS Interface (abstracted)              │
│       ├── Local: Piper TTS              │
│       └── Cloud: TTS API (fallback)     │
│                                          │
│  STT Interface (abstracted)              │
│       ├── Local: Whisper.cpp            │
│       └── Cloud: STT API (fallback)     │
└──────────────────────────────────────────┘
```

## Evolution Roadmap

### Phase 1: Foundation (current)
- Chassis design and build
- Basic drive system (move forward, back, turn)
- Encoder feedback (know where you are)
- Ultrasonic obstacle avoidance
- Camera feed to Pi
- SSH-based remote operation

### Phase 2: Perception
- IMU integration (balance, orientation)
- Multi-sensor fusion
- Basic object recognition (local model)
- Mapping / localization (SLAM lite)

### Phase 3: Intelligence
- Local LLM integration (Ollama)
- Self-evaluation framework (score own performance)
- Behavior logging and analysis
- First self-proposed code modifications

### Phase 4: Voice
- TTS output (speak status, decisions)
- STT input (voice commands)
- Conversational interaction

### Phase 5: Manipulation
- SO-101 arm integration (6-DOF open source arms)
- Gripper capability
- Pick and place tasks
- Potential for self-assembly / self-repair of modular components

### Phase 6: Full Autonomy
- Untethered battery operation
- Self-charging (dock)
- Continuous self-evolution with constitutional oversight
- Multi-robot coordination (using spare Pi 3 / Orange Pi fleet)

## Available Compute Fleet

For distributed tasks, swarm experiments, or dedicated subsystem nodes:

| Board | Qty | Best Use |
|---|---|---|
| Pi 3B | 6 spare | Additional robot brains, sensor hubs, camera nodes |
| Pi Zero | Multiple | Ultra-compact sensor nodes, lightweight tasks |
| Pi Pico | Multiple | Real-time motor control, sensor polling (no OS overhead) |
| Orange Pi v1 | ~6-7 | Dedicated task nodes: camera processing, motor control, sensor fusion |
| ESP32 | Multiple | WiFi sensor nodes, motor control, real-time I/O |
| ESP32-CAM | 1+ | Standalone camera node with WiFi |
| Arduino Uno/Mega | Multiple | Simple I/O, legacy sensor interfaces |
| Arduino Micro | Multiple | Compact I/O nodes |
| Teensy | 1+ | High-speed USB, audio processing |
| Adafruit RP2040 | Multiple | CircuitPython ecosystem |
| Seeeduino XIAO | Multiple | Tiny form factor nodes |

## Fabrication Capabilities

| Method | Materials | Precision | Use Case |
|---|---|---|---|
| **Laser CNC** | Wood, acrylic, soft materials | High | Chassis plates, mounts — primary build method |
| **3D Printer (PETG)** | PETG filament | Medium-high | Brackets, motor mounts, sensor housings, wheels |
| **3D Printer (TPU/Flex)** | Flexible filament | Medium | Wheel tread, bumpers, vibration dampening |
| **Plasma CNC** | Metal (steel, aluminum) | Medium | Heavy structural, future arm mounts |
| **CNC Router** | Wood | High | Larger structural panels (outsourced for now) |

## Procurement

Parts can be purchased to fill gaps. Priorities:
1. Items not in current inventory that block v1 build
2. Quality-of-life improvements (connectors, wire management)
3. Future phase components (arms, grippers)

*See hardware/SHOPPING_LIST.md for current needs.*

---

*This vision document evolves as the robot evolves. Updated by Claude (architect) with human approval.*
