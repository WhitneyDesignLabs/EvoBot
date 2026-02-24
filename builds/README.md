# EvoBot Builds

## What Is a Build?

A "build" is one specific way to assemble an EvoBot. The EvoBot platform defines the software architecture, design philosophy, and constitutional governance. A build defines the specific hardware, wiring, configuration, and trade-offs for one particular robot.

**There is no single "correct" build.** The platform is designed to support many configurations depending on what parts you have, what you can afford, and what capabilities you want.

## Available Builds

| Build | Description | Cost | Status |
|---|---|---|---|
| [reference-01](reference-01/) | Mid-size 2WD, Pi 3B + ESP32, TT motors, local Ollama + Claude API | $0 (from parts on hand) | In progress |

## How Builds Differ

Builds can vary in any or all of these dimensions:

| Dimension | Example Variations |
|---|---|
| **Size** | Desktop (20cm), mid-size (40-60cm), large (60cm+) |
| **Drive** | 2WD differential, 4WD skid steer, mecanum, tracked |
| **Motors** | TT geared DC, NEMA 17 stepper, BLDC hoverboard, hobby servo |
| **Brain** | Pi 3B, Pi 4, Pi 5, Orange Pi, Jetson Nano |
| **Co-processor** | ESP32, Pi Pico, Arduino Mega, Teensy, none |
| **Inference** | Local Ollama, cloud-only (Claude/GPT), hybrid, edge TPU |
| **Power** | 2S LiPo (7.4V), 3S (12V), USB power bank, 36V hoverboard pack |
| **Sensors** | Ultrasonic only, ultrasonic + IMU, LiDAR, stereo camera |
| **Chassis** | Laser-cut wood, 3D printed, acrylic, aluminum, cardboard |
| **Arms** | None, SO-101, custom servo arm, gripper only |

## Creating a New Build

1. Copy `reference-01/` as a starting point (or start from scratch)
2. Create your directory: `builds/your-build-name/`
3. Include at minimum:
   - `README.md` — what makes this build different and why
   - `hardware/BOM.md` — bill of materials
   - `docs/TOPOLOGY.md` — your specific network/compute layout
   - `configs/` — any configuration files specific to this build
4. Submit a PR if you want it included in the repo

## What Stays at Platform Level

These files apply to ALL builds and live in the repo root or `docs/`:

| File | Scope |
|---|---|
| `docs/DESIGN_PHILOSOPHY.md` | Local-first principle, constitutional governance, self-evolution philosophy |
| `docs/SOUL.md` | Opengates Constitution — governs ALL builds |
| `docs/ARCHITECTURE_VISION.md` | Evolution roadmap, compute architecture concepts |
| `code/` | Core robot software (configurable per build) |
| `hardware/INVENTORY.md` | Reference-01's specific parts (other builds have their own) |

## The Goal

A community of builds, each learning from the others. Your build's self-evolution insights feed back into the platform. The platform gets smarter. Every build benefits.
