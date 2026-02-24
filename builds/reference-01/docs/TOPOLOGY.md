# EvoBot System Topology

## Overview

Three distinct layers with clear separation of responsibilities.

```
┌──────────────────────────────────────────────────────────────────┐
│  LAYER 1: DEVELOPMENT (Windows 10 Workstation / WSL)            │
│                                                                  │
│  Scott (human) ←→ Claude Code (WSL/bash)                        │
│                      │                                           │
│                      ├── SSH to Pi (deploy, debug, configure)    │
│                      ├── Git ←→ GitHub (version control)         │
│                      └── Internet (Anthropic API for Claude Code)│
│                                                                  │
│  Role: Architecture, code writing, design, review, iteration     │
│  Claude Code is the DEVELOPMENT TOOL — not the robot's brain    │
├──────────────────────────────────────────────────────────────────┤
│  LAYER 2: ROBOT BRAIN (Pi 3B @ 192.168.1.51)                    │
│                                                                  │
│  Robot Python Code (main loop)                                   │
│      │                                                           │
│      ├── Ollama (LAN server) ── routine inference, local-first  │
│      ├── Claude API (HTTP) ──── complex reasoning, self-evolution│
│      ├── ESP32 (UART serial) ── motor commands, encoder reads   │
│      ├── Sensors (I2C/GPIO) ── IMU, ultrasonic, camera          │
│      └── Logging / self-evaluation                               │
│                                                                  │
│  Role: Autonomous operation, decision-making, perception, action │
│  Pi stays LEAN — no Node.js, no Claude Code CLI, no IDE         │
├──────────────────────────────────────────────────────────────────┤
│  LAYER 3: REAL-TIME (ESP32 / Pico / Arduino)                     │
│                                                                  │
│  Motor PWM generation                                            │
│  Encoder pulse counting                                          │
│  PID loop (constant-rate, microsecond precision)                 │
│  Safety watchdog (independent of Pi)                             │
│                                                                  │
│  Role: Physics-layer control that Linux can't reliably do       │
└──────────────────────────────────────────────────────────────────┘
```

## Connection Map

```
[Workstation WSL] ──SSH──→ [Pi 3B eth0 192.168.1.51]
                                │
                    ┌───────────┼───────────────┐
                    │           │               │
              [UART/Serial] [I2C Bus]     [USB Port]
                    │           │               │
               [ESP32]    [IMU, ADC,       [Webcam]
              Motor Ctrl   RTC, etc.]
              + Encoders
              + Safety
                    │
              [Motor Driver]
                    │
              [TT Motors]
```

## Network

| Device | IP | Access | Purpose |
|---|---|---|---|
| Workstation (WSL) | 192.168.1.x (DHCP) | — | Development hub |
| EvoBot Pi 3B | 192.168.1.51 (static) | `ssh evobot` | Robot brain |
| Sensor Pi (DO NOT TOUCH) | 192.168.1.48 (static) | — | Heat pump monitoring |
| Home Assistant | 192.168.1.151 | — | Home automation (future integration) |
| Ollama server | TBD | HTTP API | Local LLM inference |
| Internet | — | Pi WiFi | Claude API, updates |

## Why Not Claude Code on the Pi?

Tested and verified: Claude Code runs on Pi 3 (64-bit OS) but is very slow and resource-hungry.

| Factor | Impact |
|---|---|
| Node.js on ARM | 200-400MB RAM of 921MB total |
| Response latency | Painful on 1.2GHz Cortex-A53 |
| Resource competition | Starves robot code of CPU/RAM |
| Unnecessary overhead | Robot needs HTTP API calls, not a full CLI with file editing + git |
| Internet dependency | Claude Code always needs internet; robot should survive disconnection |

**The robot calls the Claude API directly via Python `requests` (~20 lines of code).** Same inference capability, 1% of the overhead.

## Inference Routing (Local-First)

```python
# Pseudocode for robot's inference decision
def get_inference(prompt, complexity="routine"):
    if complexity == "routine":
        return call_ollama(prompt)        # LAN, no internet needed
    elif complexity == "complex":
        try:
            return call_claude_api(prompt) # Cloud, for self-evolution reasoning
        except ConnectionError:
            return call_ollama(prompt)     # Fallback to local if offline
```

The robot's thinking degrades gracefully — if internet drops, it falls back to Ollama. If Ollama is down, it falls back to cached heuristics. Core motor control and safety never depend on any inference service.

## Deployment Flow

```
1. Claude Code (WSL) writes/edits code in Documents/EvoBot/code/
2. Git commit + push to GitHub
3. SCP deploy to Pi:
   scp -r code/ evobot:~/evobot/src/
4. SSH to Pi, restart services:
   ssh evobot 'systemctl --user restart evobot'
```

Future: automated deploy via git hooks or CI.

---

*This topology is designed for the Pi 3 resource constraints. If the brain upgrades to Pi 4/5 or Orange Pi 5, the layers remain the same but capabilities expand.*
