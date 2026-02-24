# EvoBot reference-01 Wiring Guide

**Build:** reference-01
**Date:** 2026-02-24
**Author:** Claude (architect), Scott Whitney (builder)
**Status:** REFERENCE DOCUMENT -- wire to this spec

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Wire Color Conventions](#2-wire-color-conventions)
3. [Power Distribution](#3-power-distribution)
4. [Raspberry Pi 3B GPIO Pin Assignment](#4-raspberry-pi-3b-gpio-pin-assignment)
5. [ESP32 Pin Assignment](#5-esp32-pin-assignment)
6. [UART Serial Link (Pi to ESP32)](#6-uart-serial-link-pi-to-esp32)
7. [I2C Bus Layout](#7-i2c-bus-layout)
8. [Motor Driver Wiring (L293D Shield)](#8-motor-driver-wiring-l293d-shield)
9. [TT Motor and Encoder Wiring](#9-tt-motor-and-encoder-wiring)
10. [HC-SR04 Ultrasonic Sensor Wiring](#10-hc-sr04-ultrasonic-sensor-wiring)
11. [MPU6050 IMU Wiring](#11-mpu6050-imu-wiring)
12. [USB Webcam](#12-usb-webcam)
13. [Level Shifter Wiring](#13-level-shifter-wiring)
14. [Physical Kill Switch](#14-physical-kill-switch)
15. [Safety Watchdog Design (Constitution Art. 14)](#15-safety-watchdog-design-constitution-art-14)
16. [Complete System Wiring Diagram](#16-complete-system-wiring-diagram)
17. [Safety Notes and Current Budget](#17-safety-notes-and-current-budget)
18. [Pre-Power Checklist](#18-pre-power-checklist)

---

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        EvoBot reference-01                              │
│                                                                         │
│   2S Li-Ion (7.4V) ──[KILL SWITCH]──┬── L293D Motor Driver (direct)    │
│                                      │                                  │
│                                      └── Buck Converter ── 5V Rail      │
│                                                             │           │
│                                          ┌──────────────────┼─────┐     │
│                                          │                  │     │     │
│                                     [Pi 3B]           [ESP32]  [Sensors]│
│                                       │  │               │              │
│                                    [I2C] [USB]       [UART]            │
│                                       │    │           │                │
│                                   [MPU6050][Webcam] [L293D]            │
│                                                        │                │
│                                                   [TT Motors x2]       │
└─────────────────────────────────────────────────────────────────────────┘
```

**Signal flow:** Pi (brain) sends commands over UART serial to ESP32 (motor controller). ESP32 generates PWM, reads encoders, runs PID loop, and drives motors through L293D. Pi reads IMU over I2C and ultrasonic sensors through level-shifted GPIO. Webcam feeds directly to Pi over USB.

---

## 2. Wire Color Conventions

Use these colors consistently throughout the build. Label wires at both ends with tape or heat-shrink markers when colors are unavailable.

| Color | Function | Notes |
|---|---|---|
| **Red** | Power positive (any voltage) | Battery+, 5V, 3.3V -- label which |
| **Black** | Ground (GND) | ALL grounds tied together (common ground) |
| **Orange** | Battery voltage (7.4V raw) | From kill switch to buck converter and motor driver |
| **Yellow** | 5V regulated rail | Buck converter output to Pi, ESP32, sensors |
| **White** | UART TX lines | Pi TX, ESP32 TX |
| **Green** | UART RX lines | Pi RX, ESP32 RX |
| **Blue** | I2C SDA | Data line |
| **Purple/Violet** | I2C SCL | Clock line |
| **Grey** | Encoder signals | Encoder A and B channels |
| **Brown** | Motor power leads | Motor + and - to driver outputs |
| **Pink** | Ultrasonic trigger | HC-SR04 TRIG pins |
| **Tan/Beige** | Ultrasonic echo (level-shifted) | HC-SR04 ECHO through level shifter |

**Rule:** Every ground wire is black. No exceptions. If you run out of colored wire, use black with colored heat-shrink on the ends as labels.

---

## 3. Power Distribution

### 3.1 Power Architecture Diagram

```
                         ┌──────────────────────────────────────────────┐
                         │            POWER DISTRIBUTION                │
                         │                                              │
  ┌──────────┐    ┌──────┴──────┐                                       │
  │ 2S Li-Ion│    │ KILL SWITCH │                                       │
  │  7.4V    │────│ (SPST toggle│                                       │
  │  pack    │    │  on battery │                                       │
  └──────────┘    │  positive)  │                                       │
                  └──────┬──────┘                                       │
                         │                                              │
                    7.4V RAW BUS (orange wire)                          │
                         │                                              │
              ┌──────────┼──────────┐                                   │
              │                     │                                   │
     ┌────────┴────────┐   ┌───────┴────────┐                          │
     │  Buck Converter  │   │  L293D Motor   │                          │
     │  IN: 7.4V        │   │  Driver        │                          │
     │  OUT: 5.0V, 3A   │   │  VS (motor     │                          │
     │  (adjust pot     │   │  supply): 7.4V │                          │
     │   BEFORE wiring) │   │  VSS (logic):  │                          │
     └────────┬─────────┘   │  5V from rail  │                          │
              │              └────────────────┘                          │
         5V RAIL (yellow wire)                                          │
              │                                                         │
    ┌─────────┼─────────┬──────────┬──────────┐                         │
    │         │         │          │          │                          │
┌───┴───┐ ┌──┴───┐ ┌───┴───┐ ┌───┴────┐ ┌──┴──────────┐              │
│Pi 3B  │ │ESP32 │ │HC-SR04│ │HC-SR04 │ │Level Shifter│              │
│via    │ │VIN   │ │VCC x2 │ │VCC x2  │ │HV side      │              │
│micro  │ │pin   │ │(5V)   │ │(5V)    │ │(5V)         │              │
│USB    │ │(5V)  │ │       │ │        │ │             │              │
└───────┘ └──────┘ └───────┘ └────────┘ └─────────────┘              │
                                                                       │
                  3.3V RAIL (from Pi 3.3V pin and ESP32 3.3V pin)      │
                         │                                              │
              ┌──────────┼──────────┐                                   │
              │                     │                                   │
         ┌────┴────┐         ┌─────┴─────┐                             │
         │MPU6050  │         │Level      │                             │
         │VCC      │         │Shifter    │                             │
         │(3.3V)   │         │LV side    │                             │
         └─────────┘         └───────────┘                             │
                                                                       │
                  GND BUS (black wire -- ALL devices share)            │
                         │                                              │
    ┌────┬────┬────┬─────┼─────┬──────┬───────┬──────────┐            │
    │    │    │    │     │     │      │       │          │            │
   Pi  ESP32 L293D Buck  Batt- HC-SR04 HC-SR04 MPU6050  Lvl Shift   │
   GND  GND  GND  GND   GND   GND(L) GND(R)  GND      GND         │
                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

### 3.2 Power Rail Summary

| Rail | Voltage | Source | Max Current | Consumers |
|---|---|---|---|---|
| Battery raw | 7.4V nominal (6.0V-8.4V) | 2S Li-Ion pack | Depends on cells (typically 2-5A continuous) | Buck converter input, L293D VS (motor supply) |
| 5V regulated | 5.0V | Buck converter output | 3A (use a 3A+ rated buck) | Pi 3B (2.5A max), ESP32 VIN, HC-SR04 VCC x2, level shifter HV |
| 3.3V | 3.3V | Pi onboard regulator / ESP32 onboard regulator | ~50mA available from Pi pin 1 | MPU6050, level shifter LV side |

### 3.3 Critical Power Notes

1. **Measure buck converter output BEFORE connecting anything.** Adjust the pot to read 5.00-5.10V on a multimeter. Connecting a Pi to 7.4V will destroy it instantly.
2. **Pi power via micro-USB.** Cut a micro-USB cable, connect the red wire to 5V rail and black to GND. Or use a dedicated 5V micro-USB breakout. Do NOT power the Pi through GPIO pin 2 (5V) -- this bypasses the polyfuse and offers no protection.
3. **ESP32 power via VIN pin** (not the 3.3V pin). The VIN pin feeds the ESP32's onboard regulator. Acceptable input: 5V from the buck converter.
4. **Common ground is mandatory.** Every device on the robot must share the same ground bus. Float a ground and signals will not work, or worse, magic smoke escapes.

---

## 4. Raspberry Pi 3B GPIO Pin Assignment

The Pi 3B has a 40-pin GPIO header. Physical pin numbers count from the top-left (pin 1 = 3.3V, near the board edge). BCM numbers are the GPIO numbers used in software.

### 4.1 Complete Pin Map (40-pin header)

```
                    Pi 3B GPIO Header (top view, USB ports at bottom)
                    ┌─────────────────────────────────┐
                    │  oooooooooooooooooooo            │
                    │  oooooooooooooooooooo            │
                    │  Pin 1 (3V3)  Pin 2 (5V)        │
                    └─────────────────────────────────┘

     Pin 1 side (odd)          Pin 2 side (even)
    ┌──────────────────────┬──────────────────────┐
    │ Phys │ BCM  │ Func   │ Func   │ BCM  │ Phys │
    ├──────┼──────┼────────┼────────┼──────┼──────┤
    │   1  │ —    │ 3V3    │ 5V     │ —    │   2  │
    │   3  │ GP2  │ I2C SDA│ 5V     │ —    │   4  │
    │   5  │ GP3  │ I2C SCL│ GND    │ —    │   6  │
    │   7  │ GP4  │ —      │ UART TX│ GP14 │   8  │
    │   9  │ —    │ GND    │ UART RX│ GP15 │  10  │
    │  11  │ GP17 │ —      │ —      │ GP18 │  12  │
    │  13  │ GP27 │ —      │ GND    │ —    │  14  │
    │  15  │ GP22 │ —      │ —      │ GP23 │  16  │
    │  17  │ —    │ 3V3    │ —      │ GP24 │  18  │
    │  19  │ GP10 │ SPI MO │ GND    │ —    │  20  │
    │  21  │ GP9  │ SPI MI │ —      │ GP25 │  22  │
    │  23  │ GP11 │ SPI CLK│ SPI CE0│ GP8  │  24  │
    │  25  │ —    │ GND    │ SPI CE1│ GP7  │  26  │
    │  27  │ GP0  │ ID SD  │ ID SC  │ GP1  │  28  │
    │  29  │ GP5  │ —      │ GND    │ —    │  30  │
    │  31  │ GP6  │ —      │ —      │ GP12 │  32  │
    │  33  │ GP13 │ —      │ GND    │ —    │  34  │
    │  35  │ GP19 │ —      │ —      │ GP16 │  36  │
    │  37  │ GP26 │ —      │ —      │ GP20 │  38  │
    │  39  │ —    │ GND    │ —      │ GP21 │  40  │
    └──────┴──────┴────────┴────────┴──────┴──────┘
```

### 4.2 Pi GPIO Assignments for EvoBot reference-01

| Physical Pin | BCM GPIO | Direction | Connected To | Wire Color | Notes |
|---|---|---|---|---|---|
| 1 | -- | PWR | 3.3V rail out | Red (labeled 3V3) | Powers MPU6050, level shifter LV |
| 2 | -- | PWR | 5V (from USB) | -- | Do NOT use as power input |
| 3 | GPIO2 | I/O | MPU6050 SDA | Blue | I2C1 SDA (hardware I2C) |
| 4 | -- | PWR | 5V | -- | Not connected |
| 5 | GPIO3 | I/O | MPU6050 SCL | Purple | I2C1 SCL (hardware I2C) |
| 6 | -- | GND | Ground bus | Black | Primary GND tie point |
| 8 | GPIO14 | OUT | ESP32 RX (GPIO16) | White | Pi UART TX -> ESP32 RX |
| 9 | -- | GND | Ground bus | Black | |
| 10 | GPIO15 | IN | ESP32 TX (GPIO17) | Green | Pi UART RX <- ESP32 TX |
| 11 | GPIO17 | IN | HC-SR04 LEFT Echo (via level shifter) | Tan | 3.3V level-shifted echo |
| 13 | GPIO27 | IN | HC-SR04 RIGHT Echo (via level shifter) | Tan | 3.3V level-shifted echo |
| 15 | GPIO22 | OUT | HC-SR04 LEFT Trigger | Pink | 3.3V out, HC-SR04 accepts 3.3V trigger |
| 16 | GPIO23 | OUT | HC-SR04 RIGHT Trigger | Pink | 3.3V out, HC-SR04 accepts 3.3V trigger |
| 14 | -- | GND | Ground bus | Black | |
| 17 | -- | PWR | 3.3V | -- | Alternate 3.3V source (spare) |
| 20 | -- | GND | Ground bus | Black | |
| 25 | -- | GND | Ground bus | Black | |
| 30 | -- | GND | Ground bus | Black | |
| 34 | -- | GND | Ground bus | Black | |
| 39 | -- | GND | Ground bus | Black | |

**Pins NOT used (reserved/available for future expansion):**

| Physical Pin | BCM GPIO | Reserved For |
|---|---|---|
| 7 | GPIO4 | Future: 1-Wire bus (temp sensors) |
| 12 | GPIO18 | Future: PWM output (buzzer, LED) |
| 18 | GPIO24 | Future: additional sensor |
| 19 | GPIO10 | SPI MOSI (reserved for SPI devices) |
| 21 | GPIO9 | SPI MISO (reserved for SPI devices) |
| 22 | GPIO25 | Future: status LED |
| 23 | GPIO11 | SPI SCLK (reserved for SPI devices) |
| 24 | GPIO8 | SPI CE0 (reserved for SPI devices) |
| 26 | GPIO7 | SPI CE1 (reserved for SPI devices) |
| 27 | GPIO0 | EEPROM ID (do not use) |
| 28 | GPIO1 | EEPROM ID (do not use) |
| 29 | GPIO5 | Future: additional sensor/interrupt |
| 31 | GPIO6 | Future: additional sensor/interrupt |
| 32 | GPIO12 | Future: PWM output |
| 33 | GPIO13 | Future: PWM output |
| 35 | GPIO19 | Future: additional I/O |
| 36 | GPIO16 | Future: additional I/O |
| 37 | GPIO26 | Future: additional I/O |
| 38 | GPIO20 | Future: additional I/O |
| 40 | GPIO21 | Future: additional I/O |

### 4.3 Pi UART Configuration

The Pi 3B maps the hardware UART (PL011) to Bluetooth by default. For reliable serial communication with the ESP32, you must swap this:

```bash
# Add to /boot/config.txt (or /boot/firmware/config.txt on Bookworm):
dtoverlay=disable-bt

# Disable the Bluetooth modem service:
sudo systemctl disable hciuart

# Reboot. After reboot:
# /dev/ttyAMA0 = PL011 UART on GPIO14/GPIO15 (reliable, no jitter)
# Bluetooth is disabled (acceptable -- Pi uses WiFi for networking)
```

**If you need Bluetooth AND serial:** use `dtoverlay=miniuart-bt` instead, which puts the mini UART on Bluetooth and PL011 on GPIO. But the mini UART's baud rate drifts with CPU clock. Disabling BT entirely is cleaner for v1.

---

## 5. ESP32 Pin Assignment

Standard ESP32 DevKit v1 (30-pin or 38-pin). Pin labels vary by manufacturer -- verify against YOUR specific board's silkscreen. The GPIO numbers below are universal across ESP32 WROOM-32 modules.

### 5.1 ESP32 Pin Map for EvoBot reference-01

| ESP32 GPIO | Direction | Connected To | Wire Color | Notes |
|---|---|---|---|---|
| **GPIO16** | IN (RX) | Pi GPIO14 TX (phys pin 8) | White | UART2 RX -- receives commands from Pi |
| **GPIO17** | OUT (TX) | Pi GPIO15 RX (phys pin 10) | Green | UART2 TX -- sends data to Pi |
| **GPIO25** | OUT | L293D IN1 (Motor A input 1) | -- | Motor A direction pin 1 |
| **GPIO26** | OUT | L293D IN2 (Motor A input 2) | -- | Motor A direction pin 2 |
| **GPIO27** | OUT | L293D IN3 (Motor B input 1) | -- | Motor B direction pin 1 |
| **GPIO14** | OUT | L293D IN4 (Motor B input 2) | -- | Motor B direction pin 2 |
| **GPIO32** | OUT (PWM) | L293D ENA (Motor A enable/speed) | -- | LEDC PWM channel 0, 20 kHz |
| **GPIO33** | OUT (PWM) | L293D ENB (Motor B enable/speed) | -- | LEDC PWM channel 1, 20 kHz |
| **GPIO34** | IN | Left motor encoder channel A | Grey | Input-only pin (no pullup, add external 10k to 3.3V) |
| **GPIO35** | IN | Left motor encoder channel B | Grey | Input-only pin (no pullup, add external 10k to 3.3V) |
| **GPIO36** (VP) | IN | Right motor encoder channel A | Grey | Input-only pin (no pullup, add external 10k to 3.3V) |
| **GPIO39** (VN) | IN | Right motor encoder channel B | Grey | Input-only pin (no pullup, add external 10k to 3.3V) |
| **GPIO4** | OUT | Heartbeat watchdog timeout -> motor kill | -- | Goes LOW to disable L293D enable pins (see Section 15) |
| **VIN** | PWR IN | 5V rail (from buck converter) | Yellow | Powers ESP32 via onboard regulator |
| **3V3** | PWR OUT | Level shifter LV reference (if needed) | Red (labeled 3V3) | 3.3V output from ESP32 regulator |
| **GND** | GND | Ground bus | Black | Common ground |

### 5.2 ESP32 Pins to Avoid

| GPIO | Reason |
|---|---|
| GPIO0 | Boot mode select -- pulled LOW enters flash mode. Do not use for general I/O. |
| GPIO1 | UART0 TX (USB serial debug console). Leave for debug output. |
| GPIO2 | Boot mode related, connected to onboard LED on most DevKits. Avoid for critical I/O. |
| GPIO3 | UART0 RX (USB serial debug console). Leave for debug input. |
| GPIO5 | Strapping pin (SPI SS). May cause boot issues if pulled LOW at startup. |
| GPIO6-11 | Connected to internal SPI flash. NEVER use these. |
| GPIO12 | Strapping pin (MTDI). If HIGH at boot, flash voltage set wrong -> boot failure. |
| GPIO15 | Strapping pin (MTDO). Pulling LOW suppresses boot log. Usable but be cautious. |

### 5.3 ESP32 PWM Configuration

```
Motor A (Left):  LEDC Channel 0, GPIO32, 20 kHz, 8-bit resolution (0-255)
Motor B (Right): LEDC Channel 1, GPIO33, 20 kHz, 8-bit resolution (0-255)

20 kHz is above human hearing -- no motor whine.
8-bit gives 256 speed steps -- adequate for TT motors.
```

---

## 6. UART Serial Link (Pi to ESP32)

### 6.1 Physical Connection

```
     Pi 3B                              ESP32
    ┌──────────┐                      ┌──────────┐
    │ GPIO14   │──── White wire ─────→│ GPIO16   │
    │ (TX)     │     (Pi TX -> ESP RX)│ (RX2)    │
    │ Pin 8    │                      │          │
    │          │                      │          │
    │ GPIO15   │←─── Green wire ──────│ GPIO17   │
    │ (RX)     │     (ESP TX -> Pi RX)│ (TX2)    │
    │ Pin 10   │                      │          │
    │          │                      │          │
    │ GND      │──── Black wire ──────│ GND      │
    │ Pin 6    │     (common ground)  │          │
    └──────────┘                      └──────────┘
```

**NO level shifter needed.** Both Pi GPIO and ESP32 GPIO operate at 3.3V logic levels.

### 6.2 Serial Protocol Specification

| Parameter | Value |
|---|---|
| Baud rate | **115200** |
| Data bits | 8 |
| Parity | None |
| Stop bits | 1 |
| Flow control | None |
| Logic level | 3.3V (both sides) |
| Pi device | `/dev/ttyAMA0` (after `dtoverlay=disable-bt`) |
| ESP32 UART | UART2 (GPIO16 RX, GPIO17 TX) |
| Encoding | ASCII text, newline-terminated (`\n`) |

### 6.3 Command Protocol (Pi -> ESP32)

Commands are ASCII strings terminated by newline (`\n`). Simple, human-readable, debuggable with a serial terminal.

| Command | Format | Example | Description |
|---|---|---|---|
| Set motor speeds | `M <left> <right>\n` | `M 150 150\n` | Set PWM: -255 to +255 (negative = reverse) |
| Stop all motors | `S\n` | `S\n` | Immediate stop (both motors to 0) |
| Query encoders | `E?\n` | `E?\n` | Request encoder counts |
| Heartbeat | `H\n` | `H\n` | Watchdog keep-alive (must send every 500ms) |
| Set PID params | `P <Kp> <Ki> <Kd>\n` | `P 1.0 0.1 0.05\n` | Update PID tuning (applies to both motors) |

### 6.4 Response Protocol (ESP32 -> Pi)

| Response | Format | Example | Description |
|---|---|---|---|
| Encoder counts | `E <left> <right>\n` | `E 1024 1019\n` | Cumulative encoder ticks since boot |
| Acknowledgment | `OK\n` | `OK\n` | Command received and executed |
| Error | `ERR <msg>\n` | `ERR BAD_CMD\n` | Command not recognized or invalid |
| Watchdog timeout | `WDT\n` | `WDT\n` | Heartbeat missed, motors killed |

### 6.5 Heartbeat Watchdog Timing

| Parameter | Value |
|---|---|
| Heartbeat interval (Pi sends) | Every **250ms** (4 Hz) |
| Watchdog timeout (ESP32 triggers) | **1000ms** (1 second without heartbeat) |
| Action on timeout | ESP32 sets both motor PWMs to 0, sends `WDT\n` |
| Recovery | Pi resumes sending `H\n`, ESP32 re-enables motor commands |

This implements **Constitution Article 14.3**: "When communication is lost, return to safe state." The ESP32 does not need the Pi's permission to stop the motors. If the Pi crashes, hangs, or loses serial connection, the motors stop within 1 second. The ESP32 is the independent safety layer.

---

## 7. I2C Bus Layout

### 7.1 Bus Configuration

| Parameter | Value |
|---|---|
| Bus | I2C1 (hardware I2C on Pi 3B) |
| SDA | GPIO2 (physical pin 3) |
| SCL | GPIO3 (physical pin 5) |
| Bus voltage | 3.3V |
| Bus speed | 100 kHz (standard mode) |
| Pull-up resistors | **4.7k ohm** to 3.3V on both SDA and SCL |

### 7.2 I2C Device Table

| Device | I2C Address | Voltage | Notes |
|---|---|---|---|
| MPU6050 IMU | **0x68** (AD0 pin LOW or floating) | 3.3V native | Alt address: 0x69 if AD0 pulled HIGH |

### 7.3 Pull-Up Resistor Placement

The MPU6050 breakout board typically has onboard 4.7k pull-ups to VCC. **Verify this on your specific board** by checking for resistors near the SDA/SCL pins (often labeled R1, R2 or marked 472).

- **If your MPU6050 board has pull-ups:** No additional resistors needed.
- **If your MPU6050 board lacks pull-ups:** Add 4.7k resistors from SDA to 3.3V and from SCL to 3.3V on a breadboard.
- **Never double up pull-ups** (board + external). Too-strong pull-ups can cause communication errors.

### 7.4 I2C Wiring Diagram

```
     Pi 3B                              MPU6050
    ┌──────────┐                      ┌──────────┐
    │ Pin 1    │─── Red ─────────────→│ VCC      │  (3.3V)
    │ (3V3)    │                      │          │
    │          │                      │          │
    │ Pin 3    │─── Blue ────────────→│ SDA      │
    │ (GPIO2)  │                      │          │
    │          │                      │          │
    │ Pin 5    │─── Purple ──────────→│ SCL      │
    │ (GPIO3)  │                      │          │
    │          │                      │          │
    │ Pin 6    │─── Black ───────────→│ GND      │
    │ (GND)    │                      │          │
    │          │                      │ AD0      │──→ Leave floating or tie to GND (addr 0x68)
    │          │                      │ INT      │──→ Not connected in v1 (future: Pi GPIO for interrupt)
    └──────────┘                      └──────────┘

    Pull-ups (if not on MPU6050 board):
    SDA (Blue) ──── 4.7k ──── 3.3V (Red)
    SCL (Purple) ── 4.7k ──── 3.3V (Red)
```

### 7.5 I2C Verification

After wiring, before running any code:

```bash
# On the Pi, scan I2C bus 1:
sudo apt install i2c-tools    # if not already installed
i2cdetect -y 1

# Expected output: device at address 0x68
#      0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
# 60: -- -- -- -- -- -- -- -- 68 -- -- -- -- -- -- --
```

If `0x68` does not appear: check wiring, check pull-ups, check that I2C is enabled in `raspi-config`.

---

## 8. Motor Driver Wiring (L293D Shield)

### 8.1 About the L293D

The Arduino Motor Shield (L293D-based) provides two H-bridge channels (Motor A and Motor B), each capable of driving a DC motor bidirectionally. In this build, the shield is used as a standalone breakout -- it is NOT plugged into an Arduino. The ESP32 drives its control pins directly.

**If using a standalone L293D chip** instead of the shield, the pinout differs. This section covers BOTH options.

### 8.2 Option A: Arduino L293D Motor Shield (as breakout)

The shield has screw terminals for motors and a separate power input for motor voltage. The control pins are exposed on the Arduino-format headers.

| Shield Pin | Function | Connected To |
|---|---|---|
| Motor A terminal (+/-) | Motor A output | Left TT motor wires |
| Motor B terminal (+/-) | Motor B output | Right TT motor wires |
| EXT_PWR (+) | Motor supply voltage | 7.4V battery raw (orange wire) |
| EXT_PWR (-) | Motor supply ground | Ground bus (black wire) |
| EXT_PWR jumper | Cut or remove if present | Isolates Arduino 5V from motor voltage |

**Shield control pins (directly map to Arduino digital pins):**

| Arduino Pin Label | Shield Function | ESP32 GPIO |
|---|---|---|
| D12 | Direction A (IN1 equivalent) | GPIO25 |
| D13 | Direction A (IN2 equivalent) | GPIO26 |
| D8 | Direction B (IN3 equivalent) | GPIO27 |
| D11 | Direction B (IN4 equivalent) | GPIO14 |
| D3 | Enable A (ENA / PWM speed) | GPIO32 |
| D9 or D11 | Enable B (ENB / PWM speed) | GPIO33 |

**Important:** Different L293D shield clones have different pin mappings. The Adafruit Motor Shield v1 uses D4, D7, D8, D12 for direction and D3, D11 for PWM. Check YOUR shield's schematic. If in doubt, use a multimeter in continuity mode to trace which header pin connects to which L293D chip pin.

**Power jumper:** Most shields have a jumper connecting the motor power to Arduino VIN. **Remove this jumper.** You do not want 7.4V feeding back to the ESP32. The shield's logic power comes from the 5V rail through separate wiring.

### 8.3 Option B: Standalone L293D Chip (DIP-16)

If using a bare L293D on a breadboard instead of a shield:

```
              L293D (DIP-16, top view)
           ┌────────┐
  ENA  1 ──┤        ├── 16  VSS (logic 5V)
  IN1  2 ──┤        ├── 15  IN4
  OUT1 3 ──┤        ├── 14  OUT4
  GND  4 ──┤ L293D  ├── 13  GND
  GND  5 ──┤        ├── 12  GND
  OUT2 6 ──┤        ├── 11  OUT3
  IN2  7 ──┤        ├── 10  IN3
  VS   8 ──┤        ├──  9  ENB
           └────────┘
```

| L293D Pin | Name | Connected To |
|---|---|---|
| 1 | ENA (Enable A) | ESP32 GPIO32 (PWM) |
| 2 | IN1 | ESP32 GPIO25 |
| 3 | OUT1 | Left motor wire 1 (brown) |
| 4, 5, 12, 13 | GND (all four) | Ground bus (black). Solder/connect ALL four GND pins -- they are heat sinks. |
| 6 | OUT2 | Left motor wire 2 (brown) |
| 7 | IN2 | ESP32 GPIO26 |
| 8 | VS (motor supply) | 7.4V battery raw (orange wire) |
| 9 | ENB (Enable B) | ESP32 GPIO33 (PWM) |
| 10 | IN3 | ESP32 GPIO27 |
| 11 | OUT3 | Right motor wire 1 (brown) |
| 14 | OUT4 | Right motor wire 2 (brown) |
| 15 | IN4 | ESP32 GPIO14 |
| 16 | VSS (logic supply) | 5V rail (yellow wire) |

### 8.4 Motor Direction Truth Table

| IN1 | IN2 | Motor A Behavior |
|---|---|---|
| HIGH | LOW | Forward |
| LOW | HIGH | Reverse |
| LOW | LOW | Coast (free spin) |
| HIGH | HIGH | Brake (short circuit) |

Same logic applies to IN3/IN4 for Motor B. ENA/ENB PWM controls speed (0 = stopped, 255 = full speed).

**Note:** "Forward" and "reverse" depend on motor wiring polarity. If a motor spins the wrong way, swap its two output wires (OUT1/OUT2 or OUT3/OUT4) rather than changing code.

---

## 9. TT Motor and Encoder Wiring

### 9.1 TT Motor Connections

Each TT geared DC motor has two power wires (motor+ and motor-). These connect to the L293D output terminals.

| Motor | L293D Output | Notes |
|---|---|---|
| Left motor wire 1 | OUT1 (pin 3) | |
| Left motor wire 2 | OUT2 (pin 6) | If motor spins wrong direction, swap these two wires |
| Right motor wire 1 | OUT3 (pin 11) | |
| Right motor wire 2 | OUT4 (pin 14) | If motor spins wrong direction, swap these two wires |

### 9.2 Encoder Connections

The TT motor encoders (if your motors have them -- the yellow TT motors with the encoder disk on the back) typically have 4 pins:

| Encoder Pin | Label | Connected To | Wire Color |
|---|---|---|---|
| VCC | + / VCC | 3.3V (from ESP32 3V3 pin or Pi pin 1) | Red |
| GND | - / GND | Ground bus | Black |
| Channel A | OUT A / C1 | See table below | Grey |
| Channel B | OUT B / C2 | See table below | Grey |

**Encoder signal connections to ESP32:**

| Signal | ESP32 GPIO | Notes |
|---|---|---|
| Left encoder channel A | GPIO34 | Input-only. Add 10k pull-up to 3.3V. |
| Left encoder channel B | GPIO35 | Input-only. Add 10k pull-up to 3.3V. |
| Right encoder channel A | GPIO36 (VP) | Input-only. Add 10k pull-up to 3.3V. |
| Right encoder channel B | GPIO39 (VN) | Input-only. Add 10k pull-up to 3.3V. |

### 9.3 Encoder Pull-Up Resistors

ESP32 GPIO34, 35, 36, 39 are input-only pins with NO internal pull-up capability. You MUST add external pull-up resistors:

```
    3.3V ─── 10k ──┬── Encoder Channel A ──→ ESP32 GPIO34
                    │
              (encoder output drives this line)

    Repeat for GPIO35, GPIO36, GPIO39.
```

Place these four 10k resistors on the mini breadboard near the ESP32.

### 9.4 Encoder Notes

- TT motor encoders are typically 20 slots per revolution of the encoder disk. With the gear ratio (~1:48), this gives approximately 960 edges per wheel revolution (with quadrature decoding).
- Encoder output is open-collector or push-pull depending on the specific module. The pull-ups ensure a clean HIGH when no pulse is active.
- The ESP32 handles encoder counting via hardware interrupts (PCNT peripheral or ISR) -- this is why encoder signals go to the ESP32, not the Pi. Linux cannot reliably count pulses at motor speed.

---

## 10. HC-SR04 Ultrasonic Sensor Wiring

### 10.1 HC-SR04 Overview

The HC-SR04 requires 5V power and outputs a 5V echo pulse. The Pi GPIO is 3.3V and is NOT 5V tolerant. The echo pin MUST be level-shifted before connecting to the Pi.

| HC-SR04 Pin | Voltage | Notes |
|---|---|---|
| VCC | 5V | Power supply |
| GND | GND | Ground |
| TRIG | Accepts 3.3V or 5V | Pi 3.3V output is sufficient to trigger |
| ECHO | Outputs 5V | MUST level-shift to 3.3V before Pi GPIO |

### 10.2 Ultrasonic Sensor Placement

| Sensor | Position | Purpose |
|---|---|---|
| HC-SR04 LEFT | Front-left, angled ~30 degrees outward | Left obstacle detection |
| HC-SR04 RIGHT | Front-right, angled ~30 degrees outward | Right obstacle detection |

### 10.3 Wiring (Both Sensors)

```
                                    Level Shifter
    Pi 3B                          (3.3V <-> 5V)              HC-SR04 LEFT
   ┌──────────┐                   ┌─────────────┐            ┌──────────┐
   │ Pin 1    │─── Red ─────────→│ LV (3.3V)   │            │          │
   │ (3V3)    │                   │             │            │          │
   │          │                   │ HV (5V) ────│── Yellow ──│→ VCC     │
   │          │     5V Rail ─────→│             │            │          │
   │          │                   │             │            │          │
   │ GPIO22   │─── Pink ─────────────────────────────────────│→ TRIG    │
   │ (Pin 15) │   (direct, 3.3V is fine for trigger)        │          │
   │          │                   │             │            │          │
   │ GPIO17   │←── Tan ──────────│← LV1    HV1─│←── Tan ───│← ECHO    │
   │ (Pin 11) │   (3.3V shifted) │             │  (5V raw)  │          │
   │          │                   │             │            │          │
   │ GND      │─── Black ───────→│ GND ────────│── Black ──→│ GND      │
   │ (Pin 6)  │                   │             │            │          │
   └──────────┘                   └─────────────┘            └──────────┘


    Pi 3B                          Level Shifter              HC-SR04 RIGHT
   ┌──────────┐                   (same module,             ┌──────────┐
   │          │                    channel 2)                │          │
   │          │                   ┌─────────────┐            │          │
   │          │     5V Rail ─────→│ HV (shared) │── Yellow ──│→ VCC     │
   │          │                   │             │            │          │
   │ GPIO23   │─── Pink ─────────────────────────────────────│→ TRIG    │
   │ (Pin 16) │   (direct, 3.3V trigger)                    │          │
   │          │                   │             │            │          │
   │ GPIO27   │←── Tan ──────────│← LV2    HV2─│←── Tan ───│← ECHO    │
   │ (Pin 13) │   (3.3V shifted) │             │  (5V raw)  │          │
   │          │                   │             │            │          │
   │ GND      │─── Black ───────→│ GND ────────│── Black ──→│ GND      │
   └──────────┘                   └─────────────┘            └──────────┘
```

### 10.4 Trigger Pin Note

The HC-SR04 trigger input threshold is typically ~2.0V. The Pi GPIO outputs 3.3V when HIGH, which exceeds this threshold reliably. No level shifting is needed on the trigger pin -- only on the echo pin.

### 10.5 Timing

- Trigger pulse: 10 microsecond HIGH pulse
- Echo pulse width: proportional to distance (58 us per cm, round-trip)
- Minimum reading interval: 60ms between triggers (to avoid echo cross-talk between the two sensors)
- Stagger the left and right sensor triggers by 30ms

---

## 11. MPU6050 IMU Wiring

See Section 7 (I2C Bus Layout) for complete wiring details.

### 11.1 Connection Summary

| MPU6050 Pin | Connected To | Wire Color |
|---|---|---|
| VCC | Pi pin 1 (3.3V) | Red |
| GND | Pi pin 6 (GND) | Black |
| SDA | Pi pin 3 (GPIO2) | Blue |
| SCL | Pi pin 5 (GPIO3) | Purple |
| AD0 | GND or floating | -- (sets address to 0x68) |
| INT | Not connected (v1) | -- (future: Pi GPIO for data-ready interrupt) |
| XDA | Not connected | -- (auxiliary I2C master, unused) |
| XCL | Not connected | -- (auxiliary I2C master, unused) |

### 11.2 MPU6050 Provides

| Data | Resolution | Update Rate |
|---|---|---|
| 3-axis accelerometer | 16-bit, +/- 2g (configurable to +/-16g) | Up to 1 kHz |
| 3-axis gyroscope | 16-bit, +/- 250 deg/s (configurable to +/-2000 deg/s) | Up to 1 kHz |
| Temperature | Built-in | With each sample |

For v1, read at 100 Hz. This is more than sufficient for tilt detection and heading estimation on a slow-moving floor robot.

---

## 12. USB Webcam

| Connection | Details |
|---|---|
| Interface | USB 2.0 (Pi has 4x USB-A ports) |
| Power | Drawn from Pi USB port (max 600mA combined across all ports without powered hub) |
| Software | OpenCV (`cv2.VideoCapture(0)`) or `fswebcam` for still capture |
| Resolution | 640x480 recommended for Pi 3B (720p is possible but CPU-heavy) |

**No wiring diagram needed** -- plug into any Pi USB port. If the webcam draws too much current and causes Pi undervolt (lightning bolt icon on screen), use a powered USB hub or a lower-power webcam.

---

## 13. Level Shifter Wiring

### 13.1 Module Type

Use a bidirectional logic level converter module (commonly marked "Logic Level Converter" or "BSS138-based 4-channel"). These modules have:

- **LV** side: Low voltage reference (3.3V)
- **HV** side: High voltage reference (5V)
- **4 channels** (labeled 1-4 or A1-A4 / B1-B4): Each channel shifts one signal

### 13.2 Level Shifter Connections

| Module Pin | Connected To | Notes |
|---|---|---|
| LV | Pi pin 1 (3.3V) or Pi pin 17 (3.3V) | Low-voltage reference |
| HV | 5V rail | High-voltage reference |
| GND (LV side) | Ground bus | Common ground |
| GND (HV side) | Ground bus | Common ground |
| LV1 | Pi GPIO17 (pin 11) | Left echo, 3.3V side |
| HV1 | HC-SR04 LEFT Echo pin | Left echo, 5V side |
| LV2 | Pi GPIO27 (pin 13) | Right echo, 3.3V side |
| HV2 | HC-SR04 RIGHT Echo pin | Right echo, 5V side |
| LV3 | Not connected | Spare channel |
| LV4 | Not connected | Spare channel |
| HV3 | Not connected | Spare channel |
| HV4 | Not connected | Spare channel |

### 13.3 Alternative: Voltage Divider

If no level shifter module is available, a simple voltage divider on each echo pin works:

```
    HC-SR04 ECHO (5V) ──── 1k ohm ────┬──── Pi GPIO (3.3V safe)
                                        │
                                    2k ohm
                                        │
                                       GND

    Output = 5V * (2k / (1k + 2k)) = 3.33V
```

The level shifter module is preferred because it provides a cleaner signal and works bidirectionally. The voltage divider is one-way (5V to 3.3V only) but is adequate for the echo pin which only needs to be read by the Pi.

---

## 14. Physical Kill Switch

### 14.1 Purpose

Per **Constitution Article 14** (Fail-Safe Defaults): The robot must have an immediately accessible physical means to cut all power. No software, no wireless, no delays. A human hand on a switch kills everything.

### 14.2 Switch Specification

| Parameter | Value |
|---|---|
| Type | SPST toggle switch (ON/OFF) |
| Current rating | Minimum 5A (10A preferred) |
| Voltage rating | Minimum 12V DC |
| Mounting | Chassis top deck, clearly visible and accessible |
| Label | **"KILL"** or **"POWER"** -- clearly marked |

### 14.3 Wiring

```
    ┌──────────────┐
    │  2S Li-Ion    │
    │  Battery Pack │
    │               │
    │  (+) ────────────── RED wire ──────┐
    │               │                     │
    │  (-) ────────────── BLACK wire ──┐  │
    └──────────────┘                   │  │
                                       │  │
                                       │  │
                              ┌────────┴──┴─────────┐
                              │    KILL SWITCH       │
                              │    (SPST Toggle)     │
                              │                      │
                              │  Battery(+) ── IN    │
                              │  OUT ── System(+)    │
                              │                      │
                              │  (switch is on the   │
                              │   POSITIVE lead only) │
                              └──────────┬───────────┘
                                         │
                                    ORANGE wire
                                    (7.4V switched)
                                         │
                              ┌──────────┴──────────┐
                              │                     │
                         To Buck Conv          To L293D VS
                         (IN+)                 (motor supply)

    Battery(-) ── BLACK wire ──→ Ground bus (direct, no switch)
```

### 14.4 Switch Placement

- Mount on the **top deck** of the chassis where a human hand can reach it without bending down or reaching around.
- The switch should be **the most prominent feature** on the top deck -- not hidden among wires.
- Consider a **red** switch or red surround for visibility.
- Test the switch by flipping it OFF while motors are running. Everything should stop instantly. The Pi will lose power and shut down (not clean, but safe -- use a filesystem in read-only mode or accept the rare SD card corruption risk).

### 14.5 Optional: Separate Logic Power

For a cleaner shutdown, you can add a second switch (or use a DPST toggle) that cuts motor power on one pole and keeps logic power on the other. This allows the Pi to remain powered for clean shutdown while motors are killed. For v1, a single switch cutting everything is simpler and acceptable.

---

## 15. Safety Watchdog Design (Constitution Art. 14)

### 15.1 Principle

**Constitution Article 14.3:** "When communication is lost, return to safe state."

The ESP32 acts as an independent safety watchdog. If the Pi stops communicating (crash, hang, kernel panic, serial cable disconnected), the ESP32 kills motor power automatically. The ESP32 does not need the Pi's permission to stop the motors. This is the foundational fail-safe.

### 15.2 Watchdog State Machine

```
                         ┌─────────────────────┐
                         │   ESP32 BOOT         │
                         │   Motors: DISABLED    │
                         │   Waiting for first H │
                         └──────────┬────────────┘
                                    │
                              First 'H\n' received
                                    │
                                    v
                         ┌─────────────────────┐
                    ┌───→│   ACTIVE              │
                    │    │   Motors: ENABLED      │←─────────┐
                    │    │   Watchdog timer: reset│          │
                    │    └──────────┬────────────┘          │
                    │               │                        │
                    │         No 'H\n' for 1000ms           │
                    │               │                        │
                    │               v                        │
                    │    ┌─────────────────────┐             │
                    │    │   TIMED OUT          │             │
                    │    │   Motors: KILLED (0)  │             │
                    │    │   Sends 'WDT\n' to Pi│             │
                    │    └──────────┬────────────┘            │
                    │               │                        │
                    │         'H\n' received again           │
                    │               │                        │
                    └───────────────┘                        │
                              (recovery)
```

### 15.3 Implementation (ESP32 Pseudocode)

```cpp
unsigned long lastHeartbeat = 0;
bool motorsEnabled = false;
const unsigned long WATCHDOG_TIMEOUT_MS = 1000;

void loop() {
    // Check serial for commands
    if (Serial2.available()) {
        String cmd = Serial2.readStringUntil('\n');
        if (cmd == "H") {
            lastHeartbeat = millis();
            motorsEnabled = true;
        } else if (cmd == "S") {
            stopMotors();
        } else if (cmd.startsWith("M ")) {
            if (motorsEnabled) {
                parseAndSetMotors(cmd);
            }
        }
        // ... other commands
    }

    // WATCHDOG CHECK -- runs every loop iteration
    if (motorsEnabled && (millis() - lastHeartbeat > WATCHDOG_TIMEOUT_MS)) {
        stopMotors();
        motorsEnabled = false;
        Serial2.println("WDT");
    }

    // PID loop runs here at fixed interval
    runPID();
}
```

### 15.4 Fail-Safe Defaults Summary

| Condition | ESP32 Action | Motors |
|---|---|---|
| ESP32 just booted, no heartbeat received yet | Wait | DISABLED |
| Heartbeat arriving normally | Process commands | ENABLED |
| Heartbeat missed for > 1 second | Kill motors, send WDT | DISABLED |
| Heartbeat resumes after timeout | Re-enable commands | ENABLED |
| Invalid/corrupt command received | Ignore, send ERR | Unchanged |
| ESP32 itself crashes/resets | Boots into disabled state | DISABLED (safe default) |

**Every failure mode results in motors OFF.** This is the definition of fail-safe.

---

## 16. Complete System Wiring Diagram

### 16.1 Full ASCII Wiring Diagram

```
═══════════════════════════════════════════════════════════════════════════════
                     EvoBot reference-01 — COMPLETE WIRING
═══════════════════════════════════════════════════════════════════════════════

   ┌─────────────┐         ┌──────────────┐
   │ 2S Li-Ion   │         │  KILL SWITCH │
   │ Battery     │         │  (SPST)      │
   │ 7.4V        │         │              │
   │  (+)────────│─── RED──│─ IN     OUT ─│── ORANGE ──┬──────────────────────┐
   │  (-)────────│─ BLACK ─│──────────────│────────┐   │                      │
   └─────────────┘         └──────────────┘        │   │                      │
                                                   │   │                      │
                                              GND BUS  │  7.4V SWITCHED BUS   │
                                              (black)  │  (orange)            │
                                                   │   │                      │
                          ┌────────────────────────┤   │                      │
                          │                        │   │                      │
                   ┌──────┴──────┐          ┌──────┴───┴──────┐               │
                   │ BUCK CONV   │          │  L293D MOTOR    │               │
                   │ IN+: orange │          │  DRIVER         │               │
                   │ IN-: black  │          │                 │               │
                   │ OUT+: 5.0V  │          │  VS: orange     │               │
                   │ OUT-: black │          │  (7.4V motor    │               │
                   │             │          │   supply)       │               │
                   │ ADJUST POT  │          │  VSS: yellow    │               │
                   │ TO 5.00V    │          │  (5V logic)     │               │
                   │ BEFORE USE! │          │  GND: black     │               │
                   └──────┬──────┘          │                 │               │
                          │                 │  IN1: ESP GPIO25│               │
                     5V RAIL                │  IN2: ESP GPIO26│               │
                    (yellow)                │  IN3: ESP GPIO27│               │
                          │                 │  IN4: ESP GPIO14│               │
      ┌───────┬───────┬───┴───┐             │  ENA: ESP GPIO32│               │
      │       │       │       │             │  ENB: ESP GPIO33│               │
      │       │       │       │             │                 │               │
 ┌────┴──┐ ┌──┴───┐ ┌─┴────┐ │             │  OUT1: L motor+ │               │
 │ Pi 3B │ │ESP32 │ │HC-SR04│ │             │  OUT2: L motor- │               │
 │ micro │ │ VIN  │ │VCC x2│ │             │  OUT3: R motor+ │               │
 │ USB   │ │(5V)  │ │(5V)  │ │             │  OUT4: R motor- │               │
 │ power │ │      │ │      │ │             └─────────────────┘               │
 └───────┘ └──────┘ └──────┘ │                  │  │  │  │                   │
                              │                  │  │  │  │                   │
                         ┌────┴──────┐      ┌────┘  │  │  └────┐             │
                         │ Level     │      │       │  │       │             │
                         │ Shifter   │   ┌──┴──┐ ┌──┴──┴──┐ ┌──┴──┐         │
                         │ HV: 5V   │   │ LEFT │ │        │ │RIGHT│         │
                         │ LV: 3.3V │   │ TT   │ │        │ │ TT  │         │
                         └──────────┘   │MOTOR │ │        │ │MOTOR│         │
                                        └──┬───┘ │        │ └──┬──┘         │
                                           │     │        │    │            │
                                        ENCODER  │        │ ENCODER        │
                                        signals  │        │ signals        │
                                        to ESP32 │        │ to ESP32       │
                                        GPIO34/35│        │ GPIO36/39      │
                                                 │        │                │
                                                 └────────┘                │


═══════════════════════════════════════════════════════════════════════════════
                           SIGNAL CONNECTIONS
═══════════════════════════════════════════════════════════════════════════════

    Pi 3B                           ESP32
   ┌──────────────────┐           ┌──────────────────┐
   │                  │           │                  │
   │  GPIO14 (TX)  ───│── white ──│──→ GPIO16 (RX)  │  UART (115200, 3.3V)
   │  Pin 8           │           │                  │
   │                  │           │                  │
   │  GPIO15 (RX)  ←──│── green ──│─── GPIO17 (TX)  │
   │  Pin 10          │           │                  │
   │                  │           │                  │
   │  GND (Pin 6)  ───│── black ──│─── GND          │  Common ground
   │                  │           │                  │
   │                  │           │  GPIO25 ─────────│──→ L293D IN1
   │                  │           │  GPIO26 ─────────│──→ L293D IN2
   │                  │           │  GPIO27 ─────────│──→ L293D IN3
   │                  │           │  GPIO14 ─────────│──→ L293D IN4
   │                  │           │  GPIO32 (PWM) ───│──→ L293D ENA
   │                  │           │  GPIO33 (PWM) ───│──→ L293D ENB
   │                  │           │                  │
   │                  │           │  GPIO34 ←────────│─── L Encoder A
   │                  │           │  GPIO35 ←────────│─── L Encoder B
   │                  │           │  GPIO36 ←────────│─── R Encoder A
   │                  │           │  GPIO39 ←────────│─── R Encoder B
   │                  │           │                  │
   │  GPIO2 (SDA) ────│── blue ──→│  (not connected) │
   │  Pin 3       ────│── to ────→│  I2C is on Pi    │
   │                  │  MPU6050  │                  │
   │  GPIO3 (SCL) ────│── purple─→│                  │
   │  Pin 5           │  to      │                  │
   │                  │  MPU6050  │                  │
   │                  │           │                  │
   │  USB ────────────│── webcam  │                  │
   │                  │           │                  │
   │  GPIO22 (out) ───│── pink ──────────────────────│──→ HC-SR04 L TRIG
   │  Pin 15          │           │                  │
   │  GPIO23 (out) ───│── pink ──────────────────────│──→ HC-SR04 R TRIG
   │  Pin 16          │           │                  │
   │                  │           │                  │
   │  GPIO17 (in) ←───│── tan ── LV1 ←── HV1 ──────│─── HC-SR04 L ECHO
   │  Pin 11          │     (level shifter)          │
   │  GPIO27 (in) ←───│── tan ── LV2 ←── HV2 ──────│─── HC-SR04 R ECHO
   │  Pin 13          │     (level shifter)          │
   │                  │           │                  │
   └──────────────────┘           └──────────────────┘


    MPU6050                Level Shifter (4-ch)
   ┌──────────┐           ┌──────────────────┐
   │ VCC ← 3.3V (Pi)     │ LV ← 3.3V (Pi)  │
   │ GND ← GND           │ HV ← 5V rail     │
   │ SDA → Pi GPIO2      │ GND ← GND        │
   │ SCL → Pi GPIO3      │                  │
   │ AD0 → GND           │ LV1 → Pi GPIO17  │
   │ INT → NC             │ HV1 ← SR04 L ECHO│
   └──────────┘           │ LV2 → Pi GPIO27  │
                          │ HV2 ← SR04 R ECHO│
                          │ LV3 → NC (spare) │
                          │ HV3 → NC (spare) │
                          │ LV4 → NC (spare) │
                          │ HV4 → NC (spare) │
                          └──────────────────┘
```

### 16.2 Ground Bus Detail

ALL ground connections must be tied together. Use a breadboard ground rail or a terminal block as the central ground bus.

```
    GND BUS (terminal block or breadboard rail)
    ─────────────────────────────────────────────
      │    │    │    │    │     │     │     │    │
     Batt  Pi  ESP32 Buck L293D SR04L SR04R MPU  LvlShift
     (-)  GND  GND   GND  GND  GND   GND   GND  GND
```

**If you get weird behavior** (sensors reading wrong, motors twitching, serial corruption), the FIRST thing to check is whether all grounds are solidly connected to the same bus. A floating ground is the most common wiring bug.

---

## 17. Safety Notes and Current Budget

### 17.1 Voltage and Level Shifting

| Risk | Mitigation |
|---|---|
| 7.4V to Pi (destroys Pi instantly) | Verify buck converter output with multimeter BEFORE connecting Pi. NEVER connect battery direct to Pi. |
| 5V to Pi GPIO (damages GPIO pin) | Level shift ALL 5V signals. HC-SR04 echo pins go through level shifter. |
| 5V to ESP32 GPIO (may damage ESP32) | ESP32 GPIOs are 3.3V. Do not connect 5V signals to ESP32 GPIO pins. Encoder outputs should be 3.3V (powered from 3.3V rail). |
| Backfeed from motor driver | Remove power jumper on L293D shield. Keep motor voltage and logic voltage on separate paths. |

### 17.2 Current Budget

| Device | Max Current Draw | Supply Rail |
|---|---|---|
| Raspberry Pi 3B | 1.4A typical, 2.5A peak (with USB devices) | 5V (via micro-USB) |
| ESP32 DevKit | 0.5A peak (with WiFi active) | 5V (via VIN) |
| HC-SR04 x2 | 15mA each, 30mA total | 5V |
| MPU6050 | 3.9mA | 3.3V |
| Level shifter | < 1mA | 3.3V + 5V |
| USB webcam | 200-500mA | 5V (via Pi USB) |
| **Total 5V rail** | **~3.5-4.5A peak** | **Buck converter must supply this** |

| Device | Max Current Draw | Supply Rail |
|---|---|---|
| TT motor x2 (no load) | 200mA each, 400mA total | 7.4V (through L293D) |
| TT motor x2 (stall) | 800mA-1.2A each, up to 2.4A total | 7.4V (through L293D) |
| L293D driver losses | ~30% overhead at rated current | 7.4V |
| **Total motor rail** | **~0.5-3A** | **Battery direct** |

### 17.3 Fuse Recommendations

| Location | Fuse Rating | Type | Purpose |
|---|---|---|---|
| Battery positive lead (after kill switch) | **5A** blade fuse | Automotive mini blade | Protects entire system from short circuit |
| 5V rail (buck converter output) | **4A** polyfuse (resettable) | PTC thermistor | Protects Pi + ESP32 from overcurrent |
| Motor supply (battery to L293D VS) | **3A** blade fuse | Automotive mini blade | Protects L293D and wiring from motor stall overcurrent |

**For v1, fuses are recommended but not mandatory.** The kill switch is the primary safety device. Add fuses when transitioning from bench testing to mobile operation.

### 17.4 L293D Current Limits

The L293D is rated at **600mA per channel** continuous, **1.2A peak**. TT motors can draw up to 800mA-1.2A at stall. This means:

- **Normal operation:** Fine. TT motors draw ~200-400mA under load.
- **Stall condition:** The L293D may overheat or shut down. This is actually a SAFETY FEATURE -- it limits stall current and protects the motor.
- **If L293D overheats regularly:** Upgrade to an L298N (2A per channel) or TB6612FNG (1.2A per channel, more efficient).

The L293D is adequate for v1 bench testing and light-load floor driving. It is the weakest link in the power chain and will be the first thing upgraded if needed.

### 17.5 Wire Gauge Recommendations

| Wire Run | Minimum Gauge | Notes |
|---|---|---|
| Battery to kill switch | 18 AWG | Carries full system current |
| Kill switch to bus | 18 AWG | Carries full system current |
| Bus to buck converter | 20 AWG | Up to 4-5A at 7.4V |
| Bus to L293D motor supply | 20 AWG | Up to 3A |
| Buck converter to Pi (micro-USB) | 22 AWG | 2-3A at 5V |
| Buck converter to ESP32 VIN | 22 AWG | < 1A |
| Signal wires (UART, I2C, GPIO) | 26-28 AWG (jumper wire) | Milliamp-level signals |
| Motor wires (L293D to motors) | 22 AWG | Up to 1A per motor |

### 17.6 ESD and Handling

- **Always disconnect the battery** before wiring or rewiring anything.
- **Touch a grounded metal object** before handling the Pi or ESP32 (static discharge can kill them).
- **Never hot-plug the IMU or level shifter** while the system is powered -- I2C bus can latch up.
- **Never plug or unplug motor wires while PWM is active** -- inductive kickback can damage the driver.

---

## 18. Pre-Power Checklist

Run through this checklist EVERY TIME before applying power. This is **Constitution Article 13.1** (Pre-Action Verification) applied to the wiring bench.

### 18.1 Before First Power-Up

- [ ] Kill switch is in OFF position
- [ ] Buck converter output verified at 5.00-5.10V with multimeter (use bench supply to test converter, NOT the battery)
- [ ] No bare wire ends touching each other or the chassis
- [ ] All grounds connected to the same bus (continuity test with multimeter)
- [ ] Pi micro-USB power cable connected to 5V rail (NOT 7.4V rail)
- [ ] ESP32 VIN connected to 5V rail (NOT 7.4V rail)
- [ ] L293D motor supply (VS) connected to 7.4V rail
- [ ] L293D logic supply (VSS) connected to 5V rail
- [ ] L293D power jumper REMOVED (motor voltage isolated from logic)
- [ ] Level shifter LV connected to 3.3V, HV connected to 5V
- [ ] HC-SR04 ECHO pins go through level shifter (NOT direct to Pi)
- [ ] Pi UART TX (pin 8) connects to ESP32 RX (GPIO16) -- NOT TX to TX
- [ ] Pi UART RX (pin 10) connects to ESP32 TX (GPIO17) -- NOT RX to RX
- [ ] Encoder pull-up resistors (10k to 3.3V) installed on GPIO34, 35, 36, 39
- [ ] MPU6050 powered from 3.3V (NOT 5V)
- [ ] No wires pinched under boards or standoffs

### 18.2 Power-Up Sequence

1. Kill switch OFF
2. Connect battery to kill switch input
3. Verify no smoke, no heat, no LEDs lighting up (everything should be dead)
4. Flip kill switch ON
5. Check: Buck converter LED (if present) should light
6. Check: Pi red LED should light, then green LED should blink (booting)
7. Check: ESP32 LED should light (powered)
8. Wait for Pi to fully boot (30-60 seconds)
9. SSH into Pi: `ssh evobot`
10. Run `i2cdetect -y 1` -- verify MPU6050 at 0x68
11. Test serial: `echo "H" > /dev/ttyAMA0` -- ESP32 should respond
12. Test motors at LOW speed first: `M 50 50` -- both wheels should turn slowly forward
13. Test kill switch: flip OFF while motors are running -- everything should stop instantly

### 18.3 After Any Wiring Change

- [ ] Kill switch OFF before touching any wire
- [ ] Re-run the full pre-power checklist (Section 18.1)
- [ ] Power up and re-verify all subsystems

---

## Appendix A: Quick Reference — Connection Summary

| From | To | Wire | Signal | Voltage |
|---|---|---|---|---|
| Battery (+) | Kill switch IN | Red | Power | 7.4V |
| Kill switch OUT | Buck IN+ / L293D VS | Orange | Power | 7.4V |
| Battery (-) | GND bus | Black | Ground | 0V |
| Buck OUT+ | Pi USB / ESP32 VIN / sensors | Yellow | Power | 5.0V |
| Buck OUT- | GND bus | Black | Ground | 0V |
| Pi pin 1 | MPU6050 VCC / LvlShift LV | Red (3V3) | Power | 3.3V |
| Pi pin 8 (GPIO14 TX) | ESP32 GPIO16 (RX) | White | UART TX | 3.3V |
| Pi pin 10 (GPIO15 RX) | ESP32 GPIO17 (TX) | Green | UART RX | 3.3V |
| Pi pin 3 (GPIO2) | MPU6050 SDA | Blue | I2C SDA | 3.3V |
| Pi pin 5 (GPIO3) | MPU6050 SCL | Purple | I2C SCL | 3.3V |
| Pi pin 15 (GPIO22) | HC-SR04 LEFT Trig | Pink | GPIO out | 3.3V |
| Pi pin 16 (GPIO23) | HC-SR04 RIGHT Trig | Pink | GPIO out | 3.3V |
| Pi pin 11 (GPIO17) | LvlShift LV1 | Tan | Echo (shifted) | 3.3V |
| Pi pin 13 (GPIO27) | LvlShift LV2 | Tan | Echo (shifted) | 3.3V |
| LvlShift HV1 | HC-SR04 LEFT Echo | Tan | Echo (raw) | 5.0V |
| LvlShift HV2 | HC-SR04 RIGHT Echo | Tan | Echo (raw) | 5.0V |
| ESP32 GPIO25 | L293D IN1 | -- | Motor A dir | 3.3V |
| ESP32 GPIO26 | L293D IN2 | -- | Motor A dir | 3.3V |
| ESP32 GPIO27 | L293D IN3 | -- | Motor B dir | 3.3V |
| ESP32 GPIO14 | L293D IN4 | -- | Motor B dir | 3.3V |
| ESP32 GPIO32 | L293D ENA | -- | Motor A PWM | 3.3V |
| ESP32 GPIO33 | L293D ENB | -- | Motor B PWM | 3.3V |
| ESP32 GPIO34 | Left encoder ch A | Grey | Encoder | 3.3V |
| ESP32 GPIO35 | Left encoder ch B | Grey | Encoder | 3.3V |
| ESP32 GPIO36 | Right encoder ch A | Grey | Encoder | 3.3V |
| ESP32 GPIO39 | Right encoder ch B | Grey | Encoder | 3.3V |
| L293D OUT1/OUT2 | Left TT motor | Brown | Motor power | 0-7.4V |
| L293D OUT3/OUT4 | Right TT motor | Brown | Motor power | 0-7.4V |
| Pi USB port | USB webcam | USB cable | Video | 5V USB |

---

## Appendix B: Required Passive Components

| Component | Quantity | Purpose | Location |
|---|---|---|---|
| 10k ohm resistor (1/4W) | 4 | Encoder pull-ups (GPIO34, 35, 36, 39) | Mini breadboard near ESP32 |
| 4.7k ohm resistor (1/4W) | 2 | I2C pull-ups (if not on MPU6050 board) | Near MPU6050 or Pi header |
| 5A blade fuse + holder | 1 | Main power protection | Inline after kill switch |
| 3A blade fuse + holder | 1 | Motor supply protection | Inline before L293D VS |

---

## Appendix C: Test Points

When debugging, check these voltages with a multimeter. Kill switch must be ON.

| Test Point | Expected Voltage | Measured | OK? |
|---|---|---|---|
| Battery pack terminals | 7.0-8.4V | _______ | [ ] |
| After kill switch (orange bus) | Same as battery | _______ | [ ] |
| Buck converter output (5V rail) | 4.95-5.10V | _______ | [ ] |
| Pi 3.3V pin (pin 1) | 3.25-3.35V | _______ | [ ] |
| ESP32 3.3V pin | 3.25-3.35V | _______ | [ ] |
| L293D VSS (logic supply) | 4.95-5.10V | _______ | [ ] |
| L293D VS (motor supply) | Same as battery | _______ | [ ] |
| HC-SR04 VCC | 4.95-5.10V | _______ | [ ] |
| MPU6050 VCC | 3.25-3.35V | _______ | [ ] |
| Level shifter LV | 3.25-3.35V | _______ | [ ] |
| Level shifter HV | 4.95-5.10V | _______ | [ ] |

---

*This wiring document is the single source of truth for reference-01 electrical connections. If the physical wiring disagrees with this document, one of them is wrong. Fix it before powering on.*
