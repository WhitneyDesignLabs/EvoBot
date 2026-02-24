# Software Architecture: reference-01

## Overview

This document defines the complete software architecture for the reference-01 EvoBot build. It covers the Pi-side Python application, ESP32 motor firmware, the serial protocol between them, and the inference routing system. All behavior is governed by the Opengates Constitution (SOUL.md).

**This is an architecture document, not code.** Implementation follows separately.

---

## System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  Pi 3B (192.168.1.51) — Python 3.11+                       │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  main.py — Main Loop                                │    │
│  │                                                      │    │
│  │  ┌──────┐ ┌──────┐ ┌──────────┐ ┌──────┐ ┌──────┐ │    │
│  │  │sense │→│think │→│   act    │→│eval  │→│ log  │ │    │
│  │  └──┬───┘ └──┬───┘ └────┬─────┘ └──┬───┘ └──┬───┘ │    │
│  │     │        │          │           │        │      │    │
│  └─────┼────────┼──────────┼───────────┼────────┼──────┘    │
│         │        │          │           │        │           │
│  ┌──────┴───┐ ┌──┴──────┐ ┌┴────────┐ ┌┴──────┐ ┌┴──────┐ │
│  │sensors.py│ │inference│ │motors.py│ │evolve │ │logger │ │
│  │          │ │  .py    │ │(serial) │ │ .py   │ │  .py  │ │
│  └──────────┘ └────┬────┘ └─────────┘ └───────┘ └───────┘ │
│                     │                                       │
│         ┌───────────┼───────────┐                          │
│         │           │           │                          │
│    ┌────┴────┐ ┌────┴────┐ ┌───┴──────┐                   │
│    │ Ollama  │ │ Claude  │ │ Cached   │                   │
│    │  (LAN)  │ │  (API)  │ │Heuristic │                   │
│    └─────────┘ └─────────┘ └──────────┘                   │
│                                                              │
│  ┌──────────────────────────────────────────────────┐       │
│  │  safety.py — Constitutional Compliance Engine    │       │
│  │  (runs BEFORE every act, monitors DURING)        │       │
│  └──────────────────────────────────────────────────┘       │
│                                                              │
│         [UART Serial — /dev/ttyS0 or /dev/ttyAMA0]         │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────┐
│  ESP32 — C++ (Arduino framework) or MicroPython             │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌───────────┐ │
│  │ Serial   │  │ PID Loop │  │  Motor    │  │ Safety    │ │
│  │ Parser   │→ │ (per     │→ │  Driver   │  │ Watchdog  │ │
│  │          │  │  motor)  │  │  (PWM)    │  │ (indep.)  │ │
│  └──────────┘  └──────────┘  └───────────┘  └───────────┘ │
│                      ↑                                      │
│               ┌──────┴──────┐                               │
│               │  Encoder    │                               │
│               │  ISR        │                               │
│               └─────────────┘                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. Pi-Side Python Architecture

### 1.1 Main Loop (main.py)

The core execution follows a five-phase loop that runs continuously at a configurable target rate (default: 10 Hz for the main decision loop; sensor polling and motor commands can run faster in sub-loops).

```
SENSE → THINK → ACT → EVALUATE → LOG
  │        │       │       │         │
  │        │       │       │         └─ Write structured log entry
  │        │       │       └─ Score this cycle's performance
  │        │       └─ Send motor commands via serial, trigger actuators
  │        └─ Run inference if needed, make decisions
  └─ Read all sensors, get encoder data from ESP32, capture camera frame
```

**Phase details:**

| Phase | Module(s) | What Happens | Timing |
|---|---|---|---|
| **SENSE** | `sensors.py`, `motors.py` | Read ultrasonic distances, IMU orientation, camera frame, request encoder data from ESP32 | Every cycle |
| **THINK** | `inference.py`, `safety.py` | Evaluate sensor data, decide next action. For simple decisions (obstacle ahead, turn right), use local heuristics. For complex situations, call inference backend. Safety pre-check runs here. | Every cycle (inference call only when needed) |
| **ACT** | `motors.py`, `safety.py` | Send velocity commands to ESP32 over serial. Safety module validates commands before transmission — any command violating safety constraints is blocked before it reaches the wire. | Every cycle |
| **EVALUATE** | `evolution.py` | Score this cycle: Did I avoid obstacles? Did I make progress toward goal? Did I waste energy? Did I trigger any safety events? | Every cycle (lightweight), detailed evaluation every N cycles |
| **LOG** | `logger.py` | Write structured log: timestamp, sensor readings, decision made, action taken, evaluation score, any safety events. Append to rolling log file. | Every cycle |

**Startup sequence:**

1. Load configuration from `configs/robot.yaml` and `configs/inference.yaml`
2. Initialize logger (create log session file)
3. Load SOUL.md and parse constitutional references (safety.py uses these at runtime)
4. Initialize serial connection to ESP32 (wait for handshake)
5. Initialize sensors (ultrasonic, IMU, camera)
6. Run self-test: send `HEARTBEAT` to ESP32, read encoders, verify sensor readings are sane
7. Log startup complete, enter main loop
8. On shutdown (SIGTERM, SIGINT, or keyboard): send `STOP` to ESP32, close serial, flush logs

**Error handling in the main loop:**

- If a single sensor read fails: log warning, use last known good value, continue
- If serial to ESP32 fails: send `E_STOP` (retry once), log critical, halt main loop, wait for reconnection
- If inference call fails: fall back to next backend (see Section 4), continue with degraded reasoning
- If multiple consecutive failures accumulate: halt robot, log diagnostic dump, await human intervention
- The loop never crashes silently. Every exception is caught, logged, and escalated appropriately.

### 1.2 Module Layout

#### sensors.py — Perception Interface

Responsible for all sensor reading. Abstracts the hardware so the main loop gets clean data regardless of sensor type.

**Public interface:**

- `init(config)` — Initialize all sensors based on config (which pins, which types, which bus)
- `read_all()` — Returns a `SensorState` data object with all current readings
- `read_ultrasonic(sensor_id)` — Single ultrasonic reading (cm)
- `read_imu()` — Returns orientation (roll, pitch, yaw) and acceleration
- `read_camera()` — Returns current frame (numpy array or None if unavailable)
- `self_test()` — Verify all configured sensors respond with sane values

**Sensor abstraction principle:** The main loop never talks to GPIO directly. It calls `sensors.read_all()` and gets a data object. If a sensor is swapped (e.g., HC-SR04 replaced with VL53L0X lidar), only `sensors.py` changes. The main loop, inference, and safety modules are unaffected.

**SensorState data object:**

```
SensorState:
    timestamp: float
    ultrasonics: dict[str, float]     # {"front": 42.3, "rear": 180.0} — cm
    imu:
        roll: float                    # degrees
        pitch: float
        yaw: float
        accel_x: float                 # m/s^2
        accel_y: float
        accel_z: float
    encoders:                          # populated from ESP32 response
        left_ticks: int
        right_ticks: int
        left_speed: float             # ticks/sec
        right_speed: float
    camera_frame: numpy.ndarray | None
    battery_voltage: float | None      # if ADC available
```

#### motors.py — Motion Interface (Serial to ESP32)

This module does NOT drive motors directly. It sends serial commands to the ESP32 and parses responses. The Pi never touches PWM pins — that is the ESP32's job.

**Public interface:**

- `init(config)` — Open serial port, perform handshake with ESP32, set communication parameters
- `set_speed(left, right)` — Send velocity command (values in range -100 to +100, mapped to PWM by ESP32)
- `stop()` — Send `STOP` command (controlled deceleration to zero)
- `e_stop()` — Send `E_STOP` command (immediate zero, no ramp)
- `get_encoders()` — Request and return current encoder data from ESP32
- `heartbeat()` — Send heartbeat to reset ESP32 watchdog timer
- `get_status()` — Request ESP32 system status (uptime, watchdog state, error count)
- `close()` — Clean shutdown of serial connection

**Design notes:**

- All motor commands pass through `safety.py` validation before `motors.py` sends them over serial. The `motors.py` module itself is a dumb pipe — it formats and sends, it does not decide.
- Serial communication uses a simple text protocol (see Section 3).
- `motors.py` maintains a heartbeat timer. If the main loop fails to call `heartbeat()` within the configured interval, `motors.py` logs a warning. The ESP32 watchdog is the hard safety net — if heartbeats stop arriving, the ESP32 kills the motors regardless of what the Pi is doing.

#### inference.py — Inference Interface (Abstracted Backend)

Provides a single API for all inference calls. The caller never knows or cares whether the response came from Ollama, Claude, or a cached heuristic. Backend selection is driven by configuration and runtime availability.

**Public interface:**

- `init(config)` — Load inference configuration, test backend availability, establish priority order
- `query(prompt, complexity="routine", context=None)` — Send a prompt, get a text response. Complexity hint guides backend selection.
- `query_structured(prompt, schema, complexity="routine")` — Same as `query()` but expects a JSON response conforming to the given schema. Retries with format correction if response is malformed.
- `get_available_backends()` — Returns list of currently reachable backends
- `get_backend_stats()` — Returns call counts, latencies, error rates per backend

**Complexity levels:**

| Level | Typical Use | Preferred Backend |
|---|---|---|
| `"routine"` | Obstacle avoidance decisions, simple navigation | Ollama (local) |
| `"analytical"` | Sensor data interpretation, pattern recognition | Ollama (local), larger model |
| `"complex"` | Self-evaluation reasoning, evolution proposals, novel situations | Claude API (cloud) |

**Backend selection logic (see Section 4 for full detail):**

1. Check complexity level against config priority map
2. Try preferred backend
3. If preferred backend fails or times out, try next in priority order
4. If all backends fail, fall back to cached heuristics (hard-coded conservative behaviors)
5. Log every fallback event

#### safety.py — Constitutional Compliance Engine

The most critical module. It enforces the Opengates Constitution at runtime. Every physical action passes through this module before execution. It is not advisory — it has veto power.

**Public interface:**

- `init(config, constitution_path)` — Load safety thresholds from config, parse SOUL.md article references for logging
- `validate_command(command, sensor_state)` — Returns `(approved: bool, reason: str)`. Checks the proposed command against current sensor state and constitutional rules. If rejected, `reason` explains which rule was violated.
- `check_continuous(sensor_state)` — Called every cycle during execution. Returns list of active safety conditions (e.g., "obstacle within emergency distance", "battery critically low"). Can trigger automatic `E_STOP` for immediate dangers.
- `get_authorization_level(action)` — Returns the authorization level (0-4 per SOUL.md Article 15) required for an action. Levels 3-4 require human confirmation.
- `log_safety_event(event_type, details)` — Record safety events in a separate safety log (per SOUL.md Article 17)

**Constitutional article mapping:**

| SOUL.md Article | Safety Module Implementation |
|---|---|
| **Art. 4 — Irreversibility** | `validate_command()` checks if action is reversible. Irreversible actions (e.g., full-speed command from standstill) require explicit confirmation. |
| **Art. 5 — Cascading Consequences** | `validate_command()` evaluates second-order effects: "If I accelerate now and the front sensor reads 30cm, will I be able to stop in time at this speed?" |
| **Art. 12 — Safety Hierarchy** | Hard-coded priority: human safety > living being > property > task. If ultrasonic reads <20cm and camera detects a person, behavior differs from detecting a wall. |
| **Art. 13 — Physical Action Protocols** | Pre-action: `validate_command()`. During-action: `check_continuous()`. Post-action: called by main loop after ACT phase to confirm expected outcome matches actual. |
| **Art. 14 — Fail-Safe Defaults** | If `check_continuous()` detects conflicting sensor readings, it trusts the one indicating danger. If sensor state is unknown, it commands stop. |
| **Art. 15 — Authorization Levels** | `get_authorization_level()` classifies every action. Level 0 (read sensors) needs no auth. Level 1 (slow movement) is auto-approved. Level 2+ (fast movement, sustained operation) requires escalation path. |
| **Art. 17 — Logging** | `log_safety_event()` writes a tamper-evident, append-only safety log separate from the general operational log. |

**Safety thresholds (configurable in robot.yaml):**

```
safety:
  emergency_stop_distance_cm: 15     # E_STOP if any obstacle closer than this
  warning_distance_cm: 40            # Slow down, start looking for alternatives
  max_speed_near_obstacle: 30        # Cap speed (% of max) when within warning distance
  heartbeat_interval_ms: 200         # How often Pi sends heartbeat to ESP32
  max_tilt_degrees: 30               # E_STOP if IMU shows excessive tilt (falling over)
  min_battery_voltage: 6.0           # Halt if battery drops below safe threshold
  watchdog_timeout_ms: 500           # ESP32 kills motors if no heartbeat for this long
```

#### evolution.py — Self-Evaluation and Evolution Engine

Implements the sense-act-evaluate-evolve loop. The robot scores its own performance, accumulates performance data, and periodically uses inference to propose improvements to its own behavior.

**Public interface:**

- `init(config)` — Load evaluation criteria and weights from config
- `score_cycle(sensor_state_before, action_taken, sensor_state_after, safety_events)` — Score a single main loop cycle. Returns a `CycleScore` object.
- `get_session_stats()` — Aggregate statistics for the current run session
- `propose_improvement(session_stats)` — Uses inference to analyze accumulated performance data and propose a specific code or config change. Returns an `EvolutionProposal` object.
- `apply_proposal(proposal, authorized_by)` — Apply an approved proposal. Only config-level changes can be auto-applied. Code changes require human review.

**Evaluation dimensions:**

| Dimension | What It Measures | Score Range |
|---|---|---|
| **Safety** | Were any safety events triggered? Did emergency stop fire? | 0.0 (E_STOP fired) to 1.0 (clean cycle) |
| **Progress** | Did the robot make progress toward its current objective? | 0.0 (no progress) to 1.0 (objective achieved) |
| **Efficiency** | Energy and time cost relative to progress made. Unnecessary movements, excessive corrections. | 0.0 (wasteful) to 1.0 (optimal) |
| **Smoothness** | Were motor commands smooth or jerky? Large corrections indicate poor anticipation. | 0.0 (erratic) to 1.0 (smooth) |
| **Prediction accuracy** | Did the robot's predictions about sensor changes match reality? | 0.0 (wildly wrong) to 1.0 (predicted correctly) |

**CycleScore object:**

```
CycleScore:
    timestamp: float
    safety: float
    progress: float
    efficiency: float
    smoothness: float
    prediction_accuracy: float
    composite: float          # weighted average
    notes: list[str]          # human-readable observations
```

**Evolution proposal flow:**

1. After N cycles (configurable, default: 1000), `propose_improvement()` is called
2. It packages session stats and sends them to the inference backend (complexity: `"complex"`)
3. The inference response is a structured `EvolutionProposal`:
   - `target`: what to change (a config parameter, a threshold, a behavioral rule)
   - `current_value`: what it is now
   - `proposed_value`: what it should be
   - `reasoning`: why this change should improve performance
   - `expected_improvement`: which evaluation dimension should improve, and by how much
   - `risk_assessment`: what could go wrong
   - `authorization_required`: `"auto"` (config-only, no safety impact) or `"human"` (affects behavior or safety)
4. Proposals are logged. If `authorization_required == "auto"` and the change is within safe bounds, it is applied immediately. Otherwise, it is queued for human review.
5. After a proposal is applied, the next N cycles measure whether the expected improvement materialized. If not, the change is reverted.

**Constitutional constraint (SOUL.md Art. 22):** Self-evolution means better judgment, not fewer constraints. The evolution engine can never propose changes to safety thresholds that reduce safety margins. It can propose tighter safety margins (more cautious), or changes to non-safety parameters.

#### logger.py — Structured Logging

All operational data flows through this module. Produces structured, queryable logs that support both debugging and self-evaluation.

**Public interface:**

- `init(config)` — Create session log file, configure log levels and rotation
- `log(level, module, message, data=None)` — Write a structured log entry
- `log_cycle(cycle_data)` — Write a complete cycle record (sensor state, decision, action, score)
- `log_safety(event)` — Write to the separate safety log (append-only, never truncated)
- `log_evolution(proposal)` — Write evolution proposal and outcome to evolution log
- `flush()` — Force write all buffers to disk
- `get_session_path()` — Return path to current session log

**Log structure:**

Each log entry is a JSON line (one JSON object per line, for easy parsing):

```
{
    "ts": 1708801234.567,
    "level": "INFO",
    "module": "motors",
    "msg": "Speed command sent",
    "data": {"left": 50, "right": 45, "serial_latency_ms": 2.3}
}
```

**Log files:**

| File | Contents | Rotation |
|---|---|---|
| `logs/session_YYYYMMDD_HHMMSS.jsonl` | All operational logs for one run session | New file per session |
| `logs/safety.jsonl` | Safety events only. Append-only. Never deleted automatically. | Manual rotation only |
| `logs/evolution.jsonl` | Evolution proposals and outcomes | New file per session |

**Log levels:** `DEBUG`, `INFO`, `WARN`, `ERROR`, `CRITICAL`

**Per SOUL.md Article 17:** Logs are never deleted or modified by the robot software. Retention and cleanup are human decisions only. The safety log is append-only with no programmatic delete capability.

### 1.3 Configuration System (YAML)

All build-specific parameters live in YAML config files. The code contains no magic numbers, no hard-coded pins, and no embedded URLs. Changing the inference backend, swapping a sensor, or adjusting safety thresholds is a config edit, not a code change.

#### configs/robot.yaml

```yaml
# reference-01 Robot Configuration
# ---
# This file defines all hardware-specific parameters for this build.
# Change these values to adapt the software to different hardware.

robot:
  name: "reference-01"
  version: "0.1.0"

# Main loop timing
loop:
  target_hz: 10                    # Main decision loop rate
  sensor_poll_hz: 20               # Sensor read rate (can be faster than main loop)
  heartbeat_interval_ms: 200       # How often to send heartbeat to ESP32

# Serial connection to ESP32
serial:
  port: "/dev/ttyS0"              # UART port (ttyS0 for Pi 3 mini-UART, ttyAMA0 for PL011)
  baud: 115200
  timeout_ms: 100                  # Read timeout per message
  handshake_retries: 5             # How many times to retry ESP32 handshake on startup

# Ultrasonic sensors (connected to Pi GPIO)
sensors:
  ultrasonic:
    front:
      trigger_pin: 23
      echo_pin: 24
    rear:
      trigger_pin: 5
      echo_pin: 6
  imu:
    bus: 1                         # I2C bus number
    address: 0x68                  # MPU6050 default address
  camera:
    device: 0                      # /dev/video0
    resolution: [320, 240]         # Keep low for Pi 3 performance
    fps: 10

# Safety thresholds
safety:
  emergency_stop_distance_cm: 15
  warning_distance_cm: 40
  max_speed_near_obstacle: 30
  max_tilt_degrees: 30
  min_battery_voltage: 6.0
  watchdog_timeout_ms: 500
  constitution_path: "../../docs/SOUL.md"

# Motor parameters (these map to ESP32 expectations)
motors:
  max_speed: 100                   # Maximum speed value (maps to ESP32 PWM duty)
  ramp_rate: 10                    # Max speed change per cycle (acceleration limiting)
  deadband: 5                      # Below this speed value, motors don't move (stiction)

# Evolution parameters
evolution:
  evaluation_window: 1000          # Score N cycles before proposing improvements
  auto_apply_threshold: 0.8        # Confidence threshold for auto-applying config changes
  revert_if_no_improvement: true   # Auto-revert proposals that don't improve scores
  revert_window: 500               # Cycles to measure improvement before reverting

# Logging
logging:
  level: "INFO"
  log_dir: "logs/"
  log_cycles: true                 # Log every cycle (verbose, disable for long runs)
  safety_log: "logs/safety.jsonl"
```

#### configs/inference.yaml

```yaml
# Inference Backend Configuration
# ---
# Defines available inference backends and routing rules.
# The robot uses these settings to decide where to send inference requests.

# Backend definitions
backends:
  ollama_lan:
    type: "ollama"
    url: "http://192.168.1.100:11434"    # Replace with your Ollama server IP
    model: "llama3.2:3b"                  # Model to use for routine queries
    model_complex: "llama3.2:8b"          # Model to use for analytical queries
    timeout_ms: 5000
    enabled: true

  claude_api:
    type: "anthropic"
    # API key loaded from environment variable ANTHROPIC_API_KEY, never from config file
    model: "claude-sonnet-4-20250514"
    timeout_ms: 15000
    enabled: true

  cached_heuristics:
    type: "heuristic"
    # No external service — hard-coded conservative behaviors
    # This backend always succeeds (it's the fallback of last resort)
    enabled: true

# Routing rules: which backend handles which complexity level
routing:
  routine:
    priority: ["ollama_lan", "cached_heuristics"]
  analytical:
    priority: ["ollama_lan", "claude_api", "cached_heuristics"]
  complex:
    priority: ["claude_api", "ollama_lan", "cached_heuristics"]

# Retry and fallback behavior
fallback:
  max_retries_per_backend: 2
  retry_delay_ms: 500
  log_fallback_events: true        # Always log when a fallback occurs

# Rate limiting (protect against runaway inference calls)
rate_limits:
  ollama_lan:
    max_calls_per_minute: 30
  claude_api:
    max_calls_per_minute: 10       # Cloud calls cost money — be conservative
    max_calls_per_session: 100     # Hard cap per session
```

---

## 2. ESP32-Side Motor Firmware

### 2.1 Overview

The ESP32 runs a dedicated real-time firmware focused exclusively on motor control and safety. It does not make decisions, run inference, or think. It receives velocity commands from the Pi over UART, runs PID loops to maintain those velocities using encoder feedback, and independently monitors for safety conditions.

**Language:** C++ (Arduino framework) for reference-01. MicroPython is an alternative for rapid prototyping but C++ is preferred for production due to deterministic timing.

### 2.2 PID Loop

One PID controller per motor (left and right). Each runs at a fixed interval (default: 20ms / 50 Hz).

**PID loop flow:**

```
Every 20ms:
  1. Read encoder ticks since last cycle
  2. Calculate actual speed (ticks/sec)
  3. Compare actual speed to target speed (received from Pi)
  4. Compute PID output:
     error = target_speed - actual_speed
     integral += error * dt
     derivative = (error - last_error) / dt
     output = (Kp * error) + (Ki * integral) + (Kd * derivative)
  5. Clamp output to valid PWM range (0-255)
  6. Apply anti-windup: if output is clamped, stop accumulating integral
  7. Write PWM to motor driver
  8. Store error for next derivative calculation
```

**PID parameters (configurable, stored in ESP32 flash):**

```
Kp = 2.0     # Proportional gain — start conservative, tune up
Ki = 0.5     # Integral gain — handles steady-state error
Kd = 0.1     # Derivative gain — dampens oscillation
```

**Tuning notes:** PID values will be tuned empirically on real hardware. The ESP32 firmware exposes a serial command (`SET_PID Kp Ki Kd`) to adjust these values at runtime from the Pi without reflashing. This enables the evolution engine to propose PID tuning changes.

### 2.3 Encoder Reading

Each motor has a quadrature encoder. The ESP32 reads encoder pulses using hardware interrupts (ISRs) for accurate counting even during high-speed operation.

**Encoder ISR (per motor):**

```
On rising edge of encoder channel A:
  If channel B is HIGH: ticks++   (forward)
  If channel B is LOW:  ticks--   (reverse)
```

**Encoder data reported to Pi:**

- `left_ticks`: cumulative tick count (wraps at int32 boundaries)
- `right_ticks`: cumulative tick count
- `left_speed`: computed ticks/sec (averaged over last N readings for smoothness)
- `right_speed`: computed ticks/sec

The Pi can request encoder data at any time via the `GET_ENCODERS` serial command. The ESP32 also includes encoder data in periodic status messages.

### 2.4 Safety Watchdog

The ESP32 runs an independent safety watchdog that is NOT controlled by the Pi. This is the hard safety net. If the Pi crashes, hangs, loses serial connection, or enters an infinite loop, the ESP32 independently detects the loss of communication and stops the motors.

**Watchdog behavior:**

```
watchdog_timer starts at 0
On every HEARTBEAT received from Pi:
    watchdog_timer = 0

Every 10ms:
    watchdog_timer += 10
    if watchdog_timer > WATCHDOG_TIMEOUT_MS:
        set both motors to 0 PWM (immediate stop)
        set watchdog_tripped flag
        send "ERROR WATCHDOG_TIMEOUT" over serial
        remain in stopped state until:
            a) a new HEARTBEAT is received, OR
            b) hardware reset
```

**WATCHDOG_TIMEOUT_MS:** Configured to 500ms by default (matches `safety.watchdog_timeout_ms` in robot.yaml). This means if the Pi fails to send a heartbeat for half a second, the motors stop. This is long enough to survive brief serial delays but short enough to stop the robot before it travels far uncontrolled.

### 2.5 Emergency Stop Handling

Two types of stop commands:

| Command | Behavior | Use Case |
|---|---|---|
| `STOP` | Ramp motors to zero over ~200ms (configurable deceleration) | Normal stop, controlled deceleration |
| `E_STOP` | Set PWM to 0 immediately, no ramp | Danger detected, stop NOW |

**E_STOP sources:**

1. Pi sends `E_STOP` command over serial (software-triggered by safety.py)
2. ESP32 watchdog fires (Pi unresponsive)
3. (Future) Hardware E_STOP button wired directly to ESP32 GPIO — cuts motor power independent of all software

After an `E_STOP`, the ESP32 enters a locked state where it will not accept `SET_SPEED` commands until it receives a `RESET` command from the Pi. This prevents the robot from immediately resuming motion after an emergency stop without the Pi explicitly confirming it is safe.

### 2.6 ESP32 Firmware Structure

```
esp32_firmware/
├── src/
│   ├── main.cpp           # Setup, main loop, serial dispatcher
│   ├── motor_control.h/cpp # PID loop, PWM output, encoder ISR
│   ├── serial_protocol.h/cpp # Parse incoming commands, format responses
│   ├── watchdog.h/cpp     # Independent watchdog timer
│   └── config.h           # Pin definitions, PID defaults, timing constants
├── platformio.ini         # PlatformIO build configuration
└── README.md
```

---

## 3. Serial Protocol (Pi <-> ESP32)

### 3.1 Design Principles

- **Human-readable:** Plain ASCII text, not binary. This means you can debug by opening a serial terminal and typing commands manually.
- **Line-based:** One message per line, terminated by `\n`.
- **Stateless:** Each message is self-contained. No multi-message transactions.
- **Checksummed:** Optional CRC8 at end of line for error detection. If present, prefixed with `*`. If absent, message is accepted without checksum validation.

### 3.2 Message Format

```
COMMAND [ARG1] [ARG2] [...] [*CRC8]\n
```

Examples:

```
SET_SPEED 50 45
SET_SPEED 50 45 *A3
STOP
E_STOP
HEARTBEAT
GET_ENCODERS
SET_PID 2.0 0.5 0.1
```

### 3.3 Commands (Pi -> ESP32)

| Command | Arguments | Description | Response |
|---|---|---|---|
| `SET_SPEED` | `left right` | Set target speed for each motor. Values: -100 to +100 (negative = reverse). 0 = stop. | `OK SET_SPEED left right` |
| `STOP` | (none) | Controlled deceleration to zero | `OK STOP` |
| `E_STOP` | (none) | Immediate stop, enter locked state | `OK E_STOP` |
| `RESET` | (none) | Clear E_STOP lock, allow motor commands again | `OK RESET` |
| `HEARTBEAT` | (none) | Reset watchdog timer | `OK HEARTBEAT` |
| `GET_ENCODERS` | (none) | Request current encoder data | `ENCODER_DATA left_ticks right_ticks left_speed right_speed` |
| `GET_STATUS` | (none) | Request ESP32 system status | `STATUS uptime_ms watchdog_ok error_count estop_active` |
| `SET_PID` | `Kp Ki Kd` | Update PID parameters (runtime, does not persist across reboot) | `OK SET_PID Kp Ki Kd` |
| `SAVE_PID` | (none) | Persist current PID parameters to flash | `OK SAVE_PID` |

### 3.4 Responses (ESP32 -> Pi)

| Response | Fields | Description |
|---|---|---|
| `OK <command> [args]` | Echoes the command | Command accepted and executed |
| `ENCODER_DATA` | `left_ticks right_ticks left_speed right_speed` | Encoder state. Ticks are cumulative int32, speeds are float ticks/sec |
| `STATUS` | `uptime_ms watchdog_ok error_count estop_active` | System health. `watchdog_ok`: 1/0, `estop_active`: 1/0 |
| `ERROR` | `error_code [description]` | Something went wrong |

### 3.5 Error Codes

| Code | Meaning |
|---|---|
| `UNKNOWN_CMD` | Received a command the ESP32 does not recognize |
| `BAD_ARGS` | Command recognized but arguments are invalid (wrong count, out of range) |
| `BAD_CRC` | Checksum mismatch — message corrupted in transit |
| `WATCHDOG_TIMEOUT` | Watchdog fired, motors stopped |
| `ESTOP_LOCKED` | `SET_SPEED` received while in E_STOP locked state (need `RESET` first) |
| `MOTOR_FAULT` | Motor driver reported a fault (overcurrent, thermal, etc.) |

### 3.6 Timing

| Parameter | Value | Rationale |
|---|---|---|
| Baud rate | 115200 | Fast enough for all commands, universally supported |
| Heartbeat interval | 200ms | 5 Hz — lightweight, sufficient for safety |
| Watchdog timeout | 500ms | 2.5 missed heartbeats before kill. Tolerates jitter. |
| Command latency budget | <10ms | Time from Pi send to ESP32 execute. Easily met at 115200 baud. |
| Encoder report rate | On request | Pi requests via `GET_ENCODERS` at sensor poll rate (20 Hz) |

### 3.7 Handshake on Startup

When the Pi opens the serial port:

```
Pi sends:    HEARTBEAT
ESP32 sends: OK HEARTBEAT
Pi sends:    GET_STATUS
ESP32 sends: STATUS 1234 1 0 0
```

If the Pi does not receive `OK HEARTBEAT` within the configured timeout, it retries up to `serial.handshake_retries` times. If all retries fail, startup aborts with a critical error.

---

## 4. Inference Routing

### 4.1 Architecture

The inference system is a layered abstraction that hides backend details from the robot's decision-making code. The caller provides a prompt and a complexity hint. The inference module handles backend selection, failover, and retry.

```
Robot code
    │
    ▼
inference.query(prompt, complexity="routine")
    │
    ▼
┌─────────────────────────────────┐
│  Backend Router                 │
│                                  │
│  1. Look up complexity level    │
│  2. Get priority list from     │
│     inference.yaml routing     │
│  3. Try backends in order      │
│  4. Return first success       │
│  5. If all fail → heuristic    │
└─────────────────────────────────┘
    │
    ├──→ Ollama (LAN)      → HTTP POST to Ollama API → response
    ├──→ Claude API (cloud) → HTTP POST to Anthropic API → response
    └──→ Cached heuristics  → Local lookup table → response
```

### 4.2 Backend Details

#### Ollama (Local LAN)

- **Protocol:** HTTP REST API (`POST /api/generate`)
- **Location:** LAN server (configurable IP in inference.yaml)
- **Latency:** ~100-500ms for small models on GPU, 1-5s on CPU
- **Cost:** Free
- **Offline capable:** Yes (requires only LAN, not internet)
- **Use case:** Routine decisions (obstacle response, navigation choices), analytical queries

#### Claude API (Cloud)

- **Protocol:** HTTPS REST API (`POST /v1/messages`)
- **Location:** Anthropic cloud servers
- **Latency:** ~500ms-3s
- **Cost:** Per token (tracked and logged)
- **Offline capable:** No
- **Use case:** Complex reasoning (self-evaluation analysis, evolution proposals, novel situations)
- **API key:** Loaded from environment variable `ANTHROPIC_API_KEY`, never stored in config or code

#### Cached Heuristics (Fallback)

- **Protocol:** None — local function calls
- **Location:** Hard-coded in inference.py
- **Latency:** <1ms
- **Cost:** Free
- **Offline capable:** Yes (always available)
- **Use case:** Last-resort fallback when all external backends are down

**Heuristic examples:**

| Situation | Heuristic Response |
|---|---|
| Obstacle ahead, nothing on sides | Turn toward the more open side |
| Obstacle on all sides | Stop, wait, try reverse |
| Low battery | Return to starting position (if known), stop |
| No sensor data | Stop immediately |
| Unknown situation | Stop, log, wait for backend recovery or human input |

These heuristics are deliberately conservative. They keep the robot safe but not smart. The robot functions, but does not evolve, when running on heuristics alone.

### 4.3 Graceful Degradation

The system degrades through three tiers:

```
TIER 1: Full capability
  Cloud available + Local available
  Complex reasoning via Claude, routine via Ollama
  Self-evolution fully operational

TIER 2: Degraded reasoning
  Cloud unavailable, Local available
  All queries go to Ollama (local)
  Self-evolution paused (complex reasoning unavailable)
  Robot navigates and avoids obstacles normally

TIER 3: Survival mode
  Cloud unavailable + Local unavailable
  All queries answered by cached heuristics
  Robot can move, avoid obstacles, maintain safety
  No learning, no adaptation, no evolution
  Logs accumulate for later analysis when backends return
```

**Tier transitions are automatic and logged.** The system periodically probes unavailable backends (configurable: every 30 seconds) and restores them when they come back. Tier changes are logged as safety events because they affect the robot's cognitive capability.

### 4.4 Complexity Routing Logic

The caller provides a complexity hint. The router uses it to select the appropriate backend priority list.

**Decision flow in the THINK phase of the main loop:**

```
1. Evaluate sensor state
2. Determine situation complexity:
   - Obstacle avoidance with clear options → "routine"
   - Ambiguous sensor data, multiple interpretations → "analytical"
   - Self-evaluation, evolution reasoning, novel scenario → "complex"
3. Call inference.query(prompt, complexity=determined_level)
4. Inference module routes to best available backend
5. Main loop acts on the response
```

**Complexity determination is itself a lightweight local decision.** It does not require an inference call. Simple rules:

- If sensor data is unambiguous and the response is well-defined: `"routine"`
- If sensor data has ambiguity or the decision has tradeoffs: `"analytical"`
- If the question is about the robot's own performance, identity, or proposed changes: `"complex"`

---

## 5. File and Directory Structure on the Pi

```
/home/scott/evobot/
├── src/
│   ├── main.py                 # Entry point — main loop, startup, shutdown
│   ├── sensors.py              # Sensor abstraction (ultrasonic, IMU, camera, encoders)
│   ├── motors.py               # Serial interface to ESP32 (send commands, receive data)
│   ├── inference.py            # Inference backend abstraction (Ollama, Claude, heuristics)
│   ├── safety.py               # Constitutional compliance engine (validate, monitor, veto)
│   ├── evolution.py            # Self-evaluation scoring and evolution proposal engine
│   └── logger.py               # Structured logging (operational, safety, evolution)
├── configs/
│   ├── robot.yaml              # Hardware config (pins, serial, safety thresholds, timing)
│   └── inference.yaml          # Inference backends, routing rules, rate limits
├── logs/                        # Created at runtime
│   ├── session_YYYYMMDD_HHMMSS.jsonl   # Per-session operational log
│   ├── safety.jsonl            # Append-only safety event log (never auto-deleted)
│   └── evolution.jsonl         # Evolution proposals and outcomes
├── docs/
│   └── SOUL.md                 # Opengates Constitution (symlink or copy from repo)
├── venv/                        # Python virtual environment
├── requirements.txt            # Python dependencies
└── README.md                   # On-device documentation and quick-start
```

**Key directories:**

| Directory | Purpose | Deployed How |
|---|---|---|
| `src/` | All robot source code | `scp` from workstation |
| `configs/` | Build-specific configuration | `scp` from workstation, then tuned on-device |
| `logs/` | Runtime logs (created by the robot) | Never deployed — generated on-device |
| `docs/` | Constitution reference | `scp` from workstation |
| `venv/` | Python virtual environment | Created on-device via `python3 -m venv venv` |

**Python dependencies (requirements.txt):**

```
pyserial          # Serial communication with ESP32
pyyaml            # Configuration file parsing
requests          # HTTP calls to Ollama and Claude API
numpy             # Sensor data processing, camera frames
RPi.GPIO          # GPIO access for ultrasonic sensors (Pi-side)
smbus2            # I2C access for IMU
opencv-python-headless  # Camera capture (headless — no GUI on Pi)
```

---

## 6. Data Flow Summary

### 6.1 One Complete Main Loop Cycle

```
1. SENSE
   ├── sensors.py reads ultrasonics (GPIO, ~10ms)
   ├── sensors.py reads IMU (I2C, ~2ms)
   ├── sensors.py reads camera frame (USB, ~33ms at 30fps, async)
   ├── motors.py sends GET_ENCODERS to ESP32 (serial, ~5ms)
   └── sensors.py assembles SensorState object

2. THINK
   ├── safety.py checks SensorState for immediate dangers
   │   └── If danger: skip inference, go to ACT with E_STOP
   ├── Determine situation complexity (local logic, <1ms)
   ├── If inference needed: inference.py.query(prompt, complexity)
   │   └── Route to best available backend, get response
   └── Decide action: speed values, direction, or stop

3. ACT
   ├── safety.py validates proposed motor command against SensorState
   │   └── If rejected: log reason, substitute safe command (reduce speed or stop)
   ├── motors.py sends SET_SPEED to ESP32 (serial, ~2ms)
   ├── motors.py sends HEARTBEAT to ESP32 (serial, ~1ms)
   └── ESP32 PID loop takes over (maintains speed autonomously until next command)

4. EVALUATE
   ├── evolution.py scores this cycle
   │   ├── Safety score: any safety events this cycle?
   │   ├── Progress score: closer to objective?
   │   ├── Efficiency score: energy spent vs. progress made?
   │   └── Smoothness score: how different was this command from last?
   └── Accumulate score into session statistics

5. LOG
   ├── logger.py writes cycle record to session log
   ├── If safety event: logger.py writes to safety log
   └── If evaluation window complete: evolution.py proposes improvement
```

### 6.2 Inference Call Path (Example: Obstacle Avoidance)

```
Situation: Front ultrasonic reads 35cm (within warning zone), left reads 120cm, right reads 80cm.

1. Main loop THINK phase evaluates: obstacle ahead, both sides open
2. Complexity assessment: routine (clear options, unambiguous data)
3. inference.query(
       prompt="Front obstacle at 35cm. Left clear at 120cm. Right open at 80cm. "
              "Currently moving forward at speed 60. What should I do?",
       complexity="routine"
   )
4. Router checks inference.yaml: routine → ["ollama_lan", "cached_heuristics"]
5. Try Ollama: POST http://192.168.1.100:11434/api/generate
6. Ollama responds: "Turn left — more clearance on left side. Reduce speed to 40."
7. inference.py returns response to main loop
8. Main loop generates SET_SPEED command: left=30, right=50 (gentle left turn at reduced speed)
9. safety.py validates: speed within limits for obstacle distance? Yes. Approved.
10. motors.py sends: SET_SPEED 30 50
```

### 6.3 Safety Intervention Path (Example: Sudden Close Obstacle)

```
Situation: Front ultrasonic suddenly reads 12cm (below emergency_stop_distance_cm of 15cm).

1. Main loop SENSE phase reads SensorState
2. Main loop THINK phase: safety.check_continuous(sensor_state)
3. safety.py detects: front distance 12cm < emergency threshold 15cm
4. safety.py returns: EMERGENCY_STOP condition
5. Main loop skips inference entirely
6. Main loop ACT phase: motors.e_stop() — sends E_STOP to ESP32
7. ESP32 immediately sets both motors to 0 PWM
8. safety.py logs safety event: "E_STOP triggered, front obstacle at 12cm"
9. Main loop enters stopped state, waits for obstacle to clear
10. When front ultrasonic reads > warning_distance_cm: send RESET, resume normal operation
```

---

## 7. Constitutional Compliance Summary

Every module in the system maps back to specific SOUL.md articles. This is not decoration — it is the design requirement.

| SOUL.md Article | Implementation Location | How Enforced |
|---|---|---|
| **Art. 1.3 — Evolution** | `evolution.py` | Robot scores itself and proposes improvements |
| **Art. 1.4 — Steward, Not Sovereign** | `evolution.py`, `safety.py` | Human approval required for safety-affecting changes |
| **Art. 2 — Truth** | `logger.py`, `inference.py` | Logs are never falsified. Uncertainty is reported. Inference confidence is tracked. |
| **Art. 4 — Irreversibility** | `safety.py` | Commands assessed for reversibility before execution |
| **Art. 5 — Cascading Consequences** | `safety.py` | Stopping distance calculated: "Can I stop in time at this speed given this distance?" |
| **Art. 12 — Safety Hierarchy** | `safety.py` | Hard-coded priority order in all decision paths |
| **Art. 13 — Physical Action Protocols** | `main.py` loop structure | Pre-verify (THINK), monitor (ACT), confirm (EVALUATE) |
| **Art. 14 — Fail-Safe Defaults** | ESP32 watchdog, `safety.py` | When in doubt, stop. When sensors disagree, trust danger. When communication lost, safe state. |
| **Art. 15 — Authorization Levels** | `safety.py` | Every action classified by risk level |
| **Art. 17 — Logging** | `logger.py` | All decisions logged. Safety log is append-only. |
| **Art. 18 — Error Acknowledgment** | `logger.py`, `evolution.py` | Errors logged honestly, used for learning |
| **Art. 22 — Growth Within Principles** | `evolution.py` | Cannot propose weakening safety margins |

---

## 8. Deployment and Development Workflow

```
1. Claude Code (on WSL workstation) writes/edits code in:
   /mnt/c/Users/homet/Documents/EvoBot/code/

2. Deploy to Pi:
   scp -r code/ evobot:~/evobot/src/
   scp configs/ evobot:~/evobot/configs/

3. SSH to Pi, activate venv, run:
   ssh evobot
   cd ~/evobot
   source venv/bin/activate
   python3 -u src/main.py

4. During development: run manually, watch output, iterate
5. Once stable: create systemd service for autonomous operation
6. Logs accumulate on Pi in ~/evobot/logs/
7. SCP logs back to workstation for analysis if needed
```

---

## 9. Future Considerations (Out of Scope for v1, Documented for Reference)

These are acknowledged but not implemented in the initial architecture:

- **Multi-sensor fusion:** Combining ultrasonic, IMU, camera, and encoder data into a unified world model. v1 treats each sensor independently.
- **SLAM / mapping:** v1 has no persistent map. The robot reacts to the current moment.
- **Voice (TTS/STT):** Architecture supports it (abstracted interfaces in ARCHITECTURE_VISION.md), but not wired into v1.
- **Arm control:** Future SO-101 integration would add a new module (`arm.py`) with its own serial or I2C connection.
- **Multi-robot coordination:** The Pi fleet is available, but v1 is a single robot.
- **Hardware E_STOP button:** Should be wired directly to ESP32 or motor driver, independent of all software. Strongly recommended before autonomous operation.

---

*This document was written as the software architecture specification for EvoBot reference-01. It defines the contract that all implementation code must follow. When code disagrees with this document, fix the code.*
