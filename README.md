# EvoBot

A recursive self-evolving robot built on Raspberry Pi 3. The AI writes the code. The human builds the body.

## What Is This?

EvoBot is an open-source robotics project where Claude (an AI) designs and iterates on the robot's software while a human operator handles wiring, mechanical assembly, and hardware integration. The goal is a small, mobile robot whose software can evaluate its own performance and evolve its own capabilities over time.

## Hardware

- **Brain:** Raspberry Pi 3 Model B Rev 1.2
- **OS:** Raspbian Bookworm 12
- **Peripherals:** Motors, sensors, and modules — added incrementally as capabilities evolve

## Project Structure

```
EvoBot/
├── README.md            ← you are here
├── LICENSE              ← MIT License
├── PROJECT_STATUS.md    ← current state and setup log
├── docs/                ← setup guides, architecture notes
├── code/                ← robot software (deployed to Pi)
├── configs/             ← config files, systemd units
├── logs/                ← session logs, debug output
└── hardware/            ← wiring diagrams, parts inventory
```

On the Pi itself:
```
/home/scott/evobot/
├── README.md            ← on-device documentation
├── src/                 ← running robot source code
├── configs/             ← local configuration
└── logs/                ← runtime logs
```

## Getting Started

### Prerequisites
- Raspberry Pi 3 Model B (or compatible)
- Raspbian Bookworm 12
- Python 3.11+
- NetworkManager (default on Bookworm)

### Clone and Deploy
```bash
git clone https://github.com/WhitneyDesignLabs/EvoBot.git
# Copy code to your Pi:
scp -r EvoBot/code/ scott@<your-pi-ip>:~/evobot/src/
```

## Design Philosophy

### Local-First

EvoBot defaults to local computation. Cloud services are a bridge, not a destination.

- If it can run on the Pi or LAN — it runs local
- If local delivers 90-95% of cloud quality — it runs local
- If cloud is needed — the interface is abstracted so it can transition back to local later
- Core behavior (motor control, sensors, safety) is always local — no internet dependency

Local LLM inference via Ollama on LAN. Cloud APIs (Claude, TTS, STT) only where local quality isn't sufficient yet. Every cloud component has a documented path back to local.

Full details: [docs/DESIGN_PHILOSOPHY.md](docs/DESIGN_PHILOSOPHY.md)

### Constitutional Governance

EvoBot is governed by the [Project Opengates Constitution](docs/SOUL.md) — a universal ethical framework for AI agents approaching physical embodiment. This isn't bolted on; it's baked in.

Key principles: safety hierarchy (human life > property > task), irreversibility doctrine (pause and verify > proceed and hope), fail-safe defaults (when in doubt, stop), and authorization levels for physical actions.

### The Human-AI Loop

The human provides the hands. The AI provides the logic. The robot provides the feedback loop.

No simulation — real hardware, real physics, real iteration. Self-evolution means the robot proposes improvements to its own code based on real-world performance. Constitutional principles ensure it evolves responsibly.

## Contributing

Contributions welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

[MIT License](LICENSE) — use it, fork it, build on it.

## Author

Scott Whitney — [WhitneyDesignLabs.com](https://whitneydesignlabs.com)
