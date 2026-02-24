# EvoBot Design Philosophy

## Local-First Principle

**Default to local. Use cloud only when local cannot deliver.**

This project follows a strict local-first design philosophy. Every capability should run on the robot itself or on local network infrastructure whenever possible. Cloud services are a bridge, not a destination.

### The Decision Framework

When implementing any capability, apply this test:

```
1. Can it run on the Pi itself?                    → DO IT LOCAL
2. Can it run on a local server (e.g., Ollama)?    → DO IT LOCAL
3. Can local deliver 90-95% of cloud quality?      → DO IT LOCAL
4. Does it require cloud for acceptable quality?    → USE CLOUD, BUT:
   a. Abstract the interface so the backend is swappable
   b. Document what would need to change for local
   c. Revisit when local models/hardware improve
```

### What This Means in Practice

| Capability | Current Approach | Local Path |
|---|---|---|
| **Low-level inference** | Local (Ollama on LAN) | Already there |
| **High-level reasoning** | Cloud API (Claude, etc.) | Future: larger local models as hardware allows |
| **Text-to-Speech (TTS)** | Cloud API (quality needed) | Piper TTS, Coqui — revisit as quality improves |
| **Speech-to-Text (STT)** | Cloud API or local Whisper | Whisper.cpp on Pi or LAN server |
| **Vision/Object Detection** | Local (Pi Camera + lightweight model) | Already local-capable |
| **Motor control** | Local (GPIO, always) | N/A — always local |
| **Sensor reading** | Local (GPIO/I2C/SPI, always) | N/A — always local |
| **Decision loops** | Local (always) | N/A — always local |
| **Self-evolution logic** | Local (Ollama) + Cloud (complex reasoning) | Hybrid, trending local |

### The Abstraction Rule

**Every cloud-dependent component must be wrapped in an interface that allows backend swapping without changing the robot's behavior code.**

```
Robot Code → Capability Interface → [Local Backend | Cloud Backend]
```

The robot's logic should never know or care whether inference is coming from Ollama on the LAN or Claude via API. It asks a question, it gets an answer. The routing is configuration, not code.

### Local Infrastructure Available

- **Ollama server** on LAN — for local LLM inference
- **Pi 3 onboard** — for lightweight models, sensor processing, motor control
- **6x additional Pi 3 boards** in stock — available for distributed local compute if needed

### Why This Matters

1. **Resilience**: A robot that requires internet to function is a robot that stops working when the network goes down. Core behavior must survive disconnection.
2. **Privacy**: Sensor data, camera feeds, and operational logs stay local by default.
3. **Latency**: Motor control and safety responses cannot wait for a round trip to the cloud. Physics doesn't buffer.
4. **Cost**: Cloud API calls add up. Local inference is free after hardware cost.
5. **Philosophy**: If you can't run it yourself, you don't own it. Dependency is fragility.

### The Transition Goal

Every cloud service used today should have a documented path back to local. When local models catch up — and they will — the migration should be a config change, not a rewrite.

---

## Constitutional Governance

EvoBot's software is governed by the **Project Opengates Constitution** (SOUL.md), a universal ethical framework for AI agents approaching physical embodiment.

The full constitution is included in this repository at [`docs/SOUL.md`](SOUL.md).

### Why a Constitution for a Robot?

EvoBot is not just software — it will control motors, actuators, and physical mechanisms. In the physical domain:

- Mistakes are not incorrect outputs — they are broken equipment and potential injury
- Actions cannot be ctrl-Z undone
- Safety margins exist for reasons
- Physics does not negotiate

The constitution provides the ethical bedrock that ensures capability grows responsibly.

### Key Constitutional Principles for EvoBot

These articles are especially relevant to a self-evolving physical robot:

| Article | Principle | EvoBot Application |
|---|---|---|
| **Art. 4** | Irreversibility Doctrine | Prefer reversible actions. Never send irreversible motor commands without human authorization. |
| **Art. 5** | Cascading Consequence Awareness | Consider what happens after what happens. A motor command affects position, affects balance, affects safety. |
| **Art. 12** | Safety Hierarchy | Human safety > living being safety > property > task completion. Always. |
| **Art. 13** | Physical Action Protocols | Pre-verify, monitor during, confirm after. Every physical action. |
| **Art. 14** | Fail-Safe Defaults | When in doubt, stop. When sensors disagree, trust the one indicating danger. |
| **Art. 15** | Authorization Levels | Sensor reads need no auth. Motor commands need confirmation. Irreversible actions need human verification. |
| **Art. 22** | Growth Within Principles | Self-evolution means better judgment, not fewer constraints. |

### Integration Plan

The constitution will be integrated into EvoBot's software as:

1. **Decision gate**: Before any physical action, the authorization level check runs
2. **Safety monitor**: Continuous evaluation against the safety hierarchy during operation
3. **Evolution constraint**: Self-modification proposals are evaluated against constitutional principles before execution
4. **Logging requirement**: All significant decisions and physical actions are logged with reasoning (Art. 17)

The constitution is not bolted on — it is baked in. The robot's identity includes its ethics.

---

## Self-Evolution Philosophy

### What "Self-Evolving" Means

The robot evaluates its own performance, identifies weaknesses, proposes improvements to its own code, and — with appropriate authorization — implements those improvements.

### What It Does NOT Mean

- The robot does not modify its own constitutional principles
- The robot does not bypass safety checks to "optimize"
- The robot does not evolve toward goals not aligned with its purpose
- The robot does not treat constraints as obstacles to route around

### The Evolution Loop

```
Sense → Act → Evaluate → Propose Change → [Human Review] → Implement → Repeat
```

Human stays in the loop for any change that affects:
- Safety behavior
- Authorization levels
- Physical action protocols
- Constitutional compliance

Autonomous evolution is permitted for:
- Sensor calibration tuning
- Movement efficiency optimization
- Non-safety behavioral parameters
- Logging and reporting improvements

---

*This document is a living guide. It evolves as the project evolves — but the core principles don't change.*
