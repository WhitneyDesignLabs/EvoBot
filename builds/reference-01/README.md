# Build: reference-01

## Summary

The first EvoBot build. A mid-size 2WD differential-drive robot built entirely from parts on hand ($0 initial cost), using a Raspberry Pi 3B as the brain, an ESP32 for real-time motor control, and a hybrid local/cloud inference stack.

**This is ONE way to build an EvoBot.** See [builds/README.md](../README.md) for other configurations.

## Key Choices (and Alternatives)

| Decision | This Build Chose | Why | Alternatives |
|---|---|---|---|
| **Drive** | 2WD + caster | Simple, cheap, sufficient for v1 | 4WD skid steer, mecanum, tracked |
| **Motors** | TT yellow geared DC | Free (in stock), ubiquitous, encoder-equipped | NEMA 17 stepper, geared 12V DC, BLDC |
| **Brain** | Pi 3B (1GB, armv7l) | Available, proven, WiFi built-in | Pi 4/5, Orange Pi, Jetson Nano |
| **Co-processor** | ESP32 | WiFi+BT, dual-core, cheap, real-time | Pi Pico, Arduino Mega, Teensy |
| **Inference** | Ollama (LAN, 8GB VRAM) + Claude API fallback | Local-first, degrades gracefully offline | Cloud-only, edge TPU, all-local small model |
| **Battery** | 2S Li-Ion (7.4V) | Available, safe, sufficient for TT motors | 3S (12V), USB power bank, 36V pack |
| **Chassis** | Laser-cut wood (parametric) | Free (scrap wood), fast iteration | 3D printed, acrylic, hand-cut, aluminum |
| **Camera** | USB webcam | Available, plug-and-play | Pi Camera CSI, ESP32-CAM, stereo |

## What You Need to Reproduce This Build

### Minimum Hardware
- 1x Raspberry Pi 3B (or any Pi with WiFi)
- 1x ESP32 dev board
- 2x TT geared DC motor with encoder
- 2x TT motor wheels
- 1x Caster wheel (or 3D print one)
- 1x L293D motor driver (shield or breakout)
- 2x HC-SR04 ultrasonic sensor
- 1x MPU6050 IMU
- 1x USB webcam
- 1x 2S battery pack + buck converter to 5V
- 1x Level shifter (3.3V↔5V)
- Wood or similar for chassis (~3-5mm, 250x200mm minimum)
- Assorted jumper wires, standoffs, screws

### Inference Stack Options

This build uses a local Ollama server with 8GB VRAM GPU. **You do NOT need this.** The inference interface is abstracted — configure whichever backend you have:

| If You Have... | Configure As | Performance |
|---|---|---|
| GPU + Ollama on LAN | `inference.local.url = "http://<ollama-ip>:11434"` | Best: fast, free, private, works offline |
| CPU-only Ollama on LAN | Same as above | Good: slower but still local and free |
| Ollama on the Pi itself | `inference.local.url = "http://localhost:11434"` | Slow: Pi 3 is underpowered for LLMs, but works for tiny models |
| No local LLM, cloud only | `inference.cloud.provider = "anthropic"` | Fine: requires internet, costs per call, but works great |
| Both (this build) | Local primary, cloud fallback | Recommended: best of both worlds |

### Network Layout

See [docs/TOPOLOGY.md](docs/TOPOLOGY.md) for the full connection map.

```
[Workstation/WSL] ──SSH──→ [Pi 3B @ 192.168.1.51]
                                │
                           [UART Serial]
                                │
                           [ESP32: motors + encoders + safety]
```

## Build-Specific Files

```
builds/reference-01/
├── README.md              ← you are here
├── hardware/
│   ├── BOM.md             ← full bill of materials
│   ├── BUDGET.md          ← spending tracker + reward program
│   └── SHOPPING_LIST.md   ← what to buy and when
├── configs/               ← build-specific configuration files
│   └── (inference.yaml, pin_map.yaml — TBD)
└── docs/
    ├── TOPOLOGY.md        ← network + compute layout
    └── (WIRING.md, CHASSIS.md — coming)
```

## Status

**Phase 1: Foundation** — Pi configured, SSH working, project structured. Next: chassis design, wiring, software scaffold.
