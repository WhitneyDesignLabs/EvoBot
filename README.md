# EvoBot

A recursive self-evolving robot platform. The AI architects everything. The human builds the body.

## What Is This?

EvoBot is an open-source robotics **platform** — not a single robot design, but a framework for building AI-driven robots that evaluate their own performance and evolve their own software. Claude (AI) is the full architect: mechanics, electronics, software, testing, and safety. The human operator handles physical assembly.

The platform defines the philosophy, the software architecture, and the constitutional governance. **Builds** define the specific hardware for a particular robot.

## Platform vs. Builds

| Layer | What it defines | Where |
|---|---|---|
| **Platform** | Software, design philosophy, constitution, evolution framework | `code/`, `docs/`, repo root |
| **Builds** | Specific hardware, wiring, BOM, config for one robot | `builds/<build-name>/` |

Your robot is a **build**. The platform supports many builds.

See [builds/README.md](builds/README.md) for available configurations and how to create your own.

### Current Builds

| Build | Description | Status |
|---|---|---|
| [reference-01](builds/reference-01/) | Mid-size 2WD, Pi 3B + ESP32, TT motors, Ollama + Claude API | In progress |

## Project Structure

```
EvoBot/
├── README.md                ← you are here (platform overview)
├── LICENSE                  ← MIT License
├── CONTRIBUTING.md          ← how to contribute
├── docs/
│   ├── DESIGN_PHILOSOPHY.md ← local-first, constitutional governance
│   ├── ARCHITECTURE_VISION.md ← compute model, evolution roadmap
│   └── SOUL.md              ← Opengates Constitution (governs all builds)
├── code/                    ← platform software (configurable per build)
├── builds/
│   ├── README.md            ← how builds work, how to add yours
│   └── reference-01/        ← first reference build
│       ├── hardware/        ← BOM, budget, shopping list
│       ├── configs/         ← build-specific configuration
│       └── docs/            ← topology, wiring, chassis design
├── hardware/                ← shared reference (inventory template)
└── configs/                 ← shared/default configuration
```

## Getting Started

### 1. Choose or Create a Build

Start with [reference-01](builds/reference-01/) or create your own based on what parts you have.

### 2. Prerequisites (minimum)

- Any Raspberry Pi with WiFi (Pi 3B+, Pi 4, Pi 5, Pi Zero 2W)
- Python 3.11+
- At least one motor + driver
- Some way to sense the world (ultrasonic, camera, anything)
- **Inference backend** — pick one:

| Option | Requirements | Cost | Offline? |
|---|---|---|---|
| **Ollama on LAN** | Any PC/server with Ollama installed | Free | Yes |
| **Ollama on Pi** | Pi 4+ recommended (Pi 3 is very slow) | Free | Yes |
| **Claude API** | Anthropic API key, internet access | Per-token | No |
| **Other cloud LLM** | API key for your provider | Per-token | No |
| **Hybrid (recommended)** | Ollama local + cloud fallback | Minimal | Degrades gracefully |

### 3. Clone and Deploy

```bash
git clone https://github.com/WhitneyDesignLabs/EvoBot.git
# Copy code to your Pi:
scp -r EvoBot/code/ user@<your-pi-ip>:~/evobot/src/
```

## Design Philosophy

### Local-First

Default to local computation. Cloud services are a bridge, not a destination.

- If it can run on the Pi or LAN — it runs local
- If local delivers 90-95% of cloud quality — it runs local
- If cloud is needed — the interface is abstracted so it can swap back to local later
- Core behavior (motor control, sensors, safety) is **always** local

Full details: [docs/DESIGN_PHILOSOPHY.md](docs/DESIGN_PHILOSOPHY.md)

### Constitutional Governance

All EvoBot builds are governed by the [Project Opengates Constitution](docs/SOUL.md) — a universal ethical framework for AI agents approaching physical embodiment.

Key principles: safety hierarchy (human life > property > task), irreversibility doctrine, fail-safe defaults, and authorization levels for physical actions. This isn't optional — it's the foundation.

### The Human-AI Loop

The human provides the hands. The AI provides the logic. The robot provides the feedback loop.

No simulation — real hardware, real physics, real iteration. Self-evolution means the robot proposes improvements to its own code based on real-world performance. Constitutional principles ensure it evolves responsibly.

## Contributing

Contributions welcome — especially new builds. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT License](LICENSE) — use it, fork it, build on it.

## Author

Scott Whitney — [WhitneyDesignLabs.com](https://whitneydesignlabs.com)
