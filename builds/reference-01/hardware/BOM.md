# EvoBot v1 Bill of Materials

## Build Target
**Cost: $0** — entirely from shop stock
**Config: 2WD differential drive + rear caster (3D printed or improvised)**

---

## Drive System

| Part | Source | Qty | Notes |
|---|---|---|---|
| TT Geared DC Motor w/ Encoder (yellow) | Shop stock (M5) | 2 | Left + right drive. 3-6V, ~200 RPM. Encoders for feedback. |
| TT Motor Wheels | Shop stock (X1) | 2 | Front left + right. Fits TT motor shaft. |
| Caster wheel | **3D print (TPU/PETG)** or ball from junk bin | 1 | Rear center. Ball caster or swivel. |
| Arduino Motor Shield (L293D) | Shop stock (D5) | 1 | Drives both TT motors. Controlled by ESP32/Pico over serial, or direct from Pi GPIO. |

### Drive Notes
- 2WD differential: two powered front wheels + one rear caster
- Turning: spin motors opposite directions (zero-radius turn capable)
- Straight line: both motors same speed with encoder PID correction
- TT motors are weak (~0.5kg/cm torque) but fine for a lightweight wood chassis

---

## Brain + Co-Processors

| Part | Source | Qty | Role |
|---|---|---|---|
| Raspberry Pi 3B (#1, c28bf021) | Allocated (C1) | 1 | Main brain — logic, WiFi, camera, SSH |
| ESP32 Dev Board | Shop stock (C5) | 1 | Motor control + encoder reading (real-time) |
| Pi Pico or Arduino | Shop stock (C3/C7) | 1 | Safety watchdog (optional for v1, recommended) |

### Compute Notes
- Pi 3 runs main Python logic, camera, WiFi, inference calls
- ESP32 handles motor PWM + encoder counting (needs microsecond timing)
- Pi ↔ ESP32: serial UART (3.3V, no level shifter needed)
- Safety watchdog: independent MCU that kills motor power if Pi stops heartbeating

---

## Sensors (v1 minimum)

| Part | Source | Qty | Role |
|---|---|---|---|
| HC-SR04 Ultrasonic | Shop stock (S1) | 2 | Front-facing obstacle detection (left + right) |
| IMU (MPU6050) | Shop stock (S4) | 1 | Orientation, tilt detection, acceleration |
| Wheel encoders | Built into TT motors (M5) | 2 | Odometry, speed feedback |
| USB Webcam | Shop stock (V1) | 1 | Vision — object detection, navigation |

### Sensor Notes
- HC-SR04 needs 5V trigger but 3.3V echo → level shifter (B4) or voltage divider
- MPU6050 is I2C, 3.3V native — direct to Pi or ESP32
- Webcam goes to Pi USB — OpenCV for image processing

---

## Power

| Part | Source | Qty | Notes |
|---|---|---|---|
| 2S LiPo/Li-Ion pack | Shop stock (P6) | 1 | ~7.4V nominal. Powers motors directly through driver. |
| Buck converter (5V out) | Shop stock (P3) | 1 | Steps 7.4V → 5V for Pi + ESP32 power |
| Wiring + terminal blocks | Shop stock (X2/X3) | — | Power distribution |

### Power Notes
- 2S pack (7.4V) is within TT motor range (they tolerate up to ~6-8V)
- Buck converter provides clean 5V 3A for Pi (needs at least 2.5A)
- Motor driver takes battery voltage directly, logic level from 5V rail
- Kill switch: physical toggle on battery lead (Constitution Art. 14 — easy emergency stop)

---

## Chassis

| Part | Source | Method | Notes |
|---|---|---|---|
| Base plate | Plywood/MDF 3-5mm | Laser cut | ~250x200mm rectangle with motor mounts, rounded corners |
| Upper deck | Plywood/MDF 3-5mm | Laser cut | Pi + electronics mounting plate, standoffs from base |
| Motor mounts | PETG 3D print | FDM | Clips/brackets to hold TT motors to base plate |
| Caster mount | PETG/TPU 3D print | FDM | Rear ball caster bracket |
| Standoffs | M3 x 30mm | Shop stock or 3D print | Deck-to-deck spacing |

### Chassis Notes
- Parametric design — SVG for laser, STEP for 3D parts
- Two-deck architecture: bottom = motors + battery, top = Pi + sensors + camera
- Everything bolts together — no glue — so it's modifiable
- Hand-cut alternative: print SVG at 1:1 on paper, trace to wood, jigsaw cut

---

## Interconnect

| Part | Source | Qty | Notes |
|---|---|---|---|
| Level shifter (3.3V↔5V) | Shop stock (B4) | 1 | For HC-SR04 echo pins |
| Jumper wires (M-F, F-F) | Shop stock (X4) | ~30 | Prototyping connections |
| Breadboard (mini) | Shop stock (B1 area) | 1 | Sensor/power distribution |
| USB cable (micro) | Shop stock | 1 | Pi power from buck converter |

---

## Total Cost

| Category | Cost |
|---|---|
| Drive | $0 |
| Compute | $0 |
| Sensors | $0 |
| Power | $0 |
| Chassis materials | $0 (scrap wood + filament on hand) |
| Interconnect | $0 |
| **TOTAL** | **$0** |

---

## What v1 Can Do

With these parts, v1 will be able to:
- [x] Drive forward, backward, turn (differential drive)
- [x] Know its wheel speed and distance (encoders)
- [x] Detect obstacles (ultrasonic)
- [x] Know its orientation (IMU)
- [x] See the world (USB webcam)
- [x] Think (Pi 3 + Ollama on LAN)
- [x] Be remotely operated (SSH/WiFi)
- [x] Emergency stop (physical kill switch)
- [x] Self-evaluate movement accuracy (encoder vs commanded)
- [x] Log all decisions and actions (Constitution Art. 17)

## What v1 Cannot Do (Yet)

- Voice interaction (no TTS/STT in v1)
- Navigate autonomously beyond obstacle avoidance
- Manipulate objects (no arms)
- Run untethered for long durations (2S pack, limited capacity)
- Self-modify its own hardware

---

*v1 is proof of concept. It proves the brain works. The body upgrades come after.*
