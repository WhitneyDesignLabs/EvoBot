# EvoBot Hardware Inventory

**Date inventoried:** 2026-02-24
**Inventoried by:** Scott Whitney
**Status:** Initial catalogue — quantities approximate, to be refined

---

## Motors

| # | Type | Description | Qty | Voltage | Notes |
|---|------|------------|-----|---------|-------|
| M1 | BLDC w/ Hall | Hoverboard hub motors | 2+ | 36V nominal | Hall effect feedback, paired with Riorand controllers |
| M2 | Stepper | Various sizes (NEMA 17, 23, etc.) | Multiple | 12-48V | Range from 3D printer size to CNC size |
| M3 | Hobby Servo | Standard and micro sizes | Multiple | 5-6V | Both continuous rotation and standard position |
| M4 | DC Brushed | Various | Multiple | Various | Less preferred — want better control options |
| **M5** | **TT Geared DC w/ Encoder** | **Yellow gearbox motor** | **4** | **3-6V** | **v1 DRIVE MOTORS — confirmed in stock, cheap and ubiquitous** |

---

## Motor Drivers / Controllers

| # | Type | Model/Marking | Qty | Notes |
|---|------|--------------|-----|-------|
| D1 | High-current H-Bridge | **BTS7960** (43A) | 1+ | For large DC motors — dual H-bridge, PWM capable |
| D2 | BLDC Controller | Riorand | 1+ | For hoverboard-style hall effect BLDC motors |
| D3 | CNC Stepper Drivers | Large (DM542/similar) | Multiple | For CNC-class steppers |
| D4 | 3D Printer Stepper Drivers | A4988, DRV8825 | Multiple | For NEMA 17 class steppers |
| **D5** | **Arduino Motor Shield** | **L293D-based (Motor A&B)** | **1+** | **v1 DRIVE — drives TT motors directly, 5-12V** |
| D6 | Arduino Motor Shields | Older era shields | Multiple | Various, to be tested |

---

## Sensors

| # | Type | Model/Marking | Qty | Interface | Notes |
|---|------|--------------|-----|-----------|-------|
| S1 | Ultrasonic | HC-SR04 (or similar) | Multiple | GPIO | Distance/obstacle detection |
| S2 | PIR Motion | Standard | Multiple | GPIO | Motion detection |
| S3 | Temperature/Humidity | DHT11 | Multiple | GPIO | Already proven on sensor Pi project |
| S4 | IMU/Accelerometer | MPU6050 or similar | 1+ | I2C | Balance, orientation, motion sensing |
| S5 | Hall Effect | Discrete sensors | Multiple | GPIO | Position sensing, RPM |
| S6 | Light Sensor | LDR / photodiode | Multiple | Analog/GPIO | Ambient light detection |
| S7 | Rotary Encoder | Standard | Multiple | GPIO | Precise rotation measurement |
| S8 | Opto-interrupter | Emitter/detector pair | Multiple | GPIO | Wheel encoder style — light-blocking slot sensors |
| S9 | Limit Switch | Mechanical | Multiple | GPIO | End-stop / contact detection |

---

## Compute Boards

| # | Type | Model | Qty | Notes |
|---|------|-------|-----|-------|
| C1 | Raspberry Pi 3B | Rev 1.2 | 6-7 | Tested stock (1 allocated to EvoBot, 6 remaining) |
| C2 | Raspberry Pi Zero | Various | Multiple | Low power, compact |
| C3 | Raspberry Pi Pico | RP2040 | Multiple | Microcontroller, real-time GPIO |
| C4 | Orange Pi | v1 (w/ HDMI, USB, desktop Linux) | ~6-7 | Weak but usable as dedicated task nodes (camera, motor ctrl, sensors) |
| C5 | ESP32 Dev | Standard dev boards | Multiple | WiFi+BT, dual core, ADC |
| C6 | ESP32-CAM | AI Thinker or similar | 1+ | Camera + WiFi in one module |
| C7 | Arduino Uno | Clone | Multiple | 5V ATmega328, classic |
| C8 | Arduino Mega | Clone | Multiple | More GPIO, more memory |
| C9 | Arduino Micro | Clone | Multiple | Compact ATmega32U4 |
| C10 | Teensy | Model TBD | 1+ | High-speed, USB native |
| C11 | Adafruit RP2040 boards | Pico-based | Multiple | Adafruit ecosystem |
| C12 | Seeeduino XIAO | SAMD21/RP2040/nRF52840 | Multiple | Tiny, versatile |

---

## Power

| # | Type | Description | Qty | Notes |
|---|------|------------|-----|-------|
| P1 | Li-Ion cells/packs | Various | Multiple | Can build custom packs |
| P2 | LiFePO4 cells/packs | Various | Multiple | Safer chemistry, lower energy density |
| P3 | Buck converters | Various ratings | Multiple | Step-down voltage regulation |
| P4 | Hoverboard batteries | 36V packs | 2+ | From hoverboard teardowns |
| P5 | Custom pack capability | Spot welder / holder | — | Can build 12V, 24V, 36V packs to spec |

| **P6** | **2S LiPo/Li-Ion packs** | **Ready to go** | **Multiple** | **~7.4V — good for servo power, could run TT motors directly** |

*v1 power: 2S pack (7.4V) for motors + buck to 5V for Pi. Can build 3S (12V) when needed.*

---

## Displays / Output

| # | Type | Description | Qty | Notes |
|---|------|------------|-----|-------|
| O1 | LCD | Arduino-style (1602/2004 I2C) | Multiple | Classic character displays |
| O2 | Color Display | TFT/IPS (SPI) | Multiple | Graphical, various sizes |
| O3 | Misc Displays | Other types | Multiple | To be identified |
| O4 | Speakers | Hardwired + USB | Multiple | Audio output for TTS |
| O5 | Microphones | Hardwired + USB | Multiple | Audio input for STT |
| O6 | LED Drivers | Various | Multiple | For indicator/status LEDs or strips |

---

## Cameras

| # | Type | Model | Qty | Notes |
|---|------|-------|-----|-------|
| V1 | USB Webcam | Various | Multiple | Plug-and-play on Pi |
| V2 | ESP32-CAM | AI Thinker or similar | 1+ | Standalone WiFi camera node |

---

## Breakout Boards / Modules

| # | Type | Model/Marking | Qty | Notes |
|---|------|--------------|-----|-------|
| B1 | ADC | ADS1115 or similar | Multiple | 16-bit, I2C — reads analog sensors on Pi |
| B2 | RTC | DS3231 or similar | Multiple | Real-time clock, I2C |
| B3 | SD Card Module | SPI breakout | Multiple | Data logging |
| B4 | Level Shifter | 3.3V↔5V | Multiple | Critical for Pi↔Arduino/5V sensor interfacing |
| B5 | Relay Module | Mechanical | Multiple | Switching loads |
| B6 | SSR | Solid State Relay | Multiple | Silent/fast switching |
| B7 | Opto-isolator | Various | Multiple | Signal isolation between circuits |

---

## Mechanical / Structural

| # | Type | Description | Qty | Notes |
|---|------|------------|-----|-------|
| **X1** | **TT Motor Wheels** | **Yellow motor compatible** | **3** | **v1 — 1 short for 4WD, fine for 2WD+caster or 3-wheel config** |
| X2 | Wiring | Assorted gauge | Bulk | Hook-up wire, various gauges |
| X3 | Terminal Blocks | Various | Multiple | Power distribution, connections |
| X4 | Misc Connectors | Various | Multiple | JST, Dupont, barrel, etc. |

---

## Fabrication Capability (In-House)

| Tool | Type | Material | Notes |
|------|------|----------|-------|
| Plasma CNC | Cutting | Metal | Heavy structural parts |
| Laser CNC | Cutting/engraving | Wood, soft materials | Chassis plates, mounting |
| 3D Printer | FDM | PETG, Flex (TPU) | Brackets, mounts, enclosures, wheels |
| CNC Router | Milling | Wood | Larger structural — currently outsourced, prefer in-house |

*Strong fabrication capability means chassis/frame/mounts can be custom-designed and built to spec rather than purchased.*

---

## Summary

**Total unique item categories:** 45+
**Compute boards available:** 20+ across 12 types
**Fabrication methods:** 4 (plasma, laser, 3D print, CNC route)
**Strongest assets:** Deep motor selection, full voltage range, in-house fabrication, massive compute board variety
**Key gaps to fill:** Wheels (make or buy), chassis design, Pi Camera (CSI), servo driver board (PCA9685), dedicated power distribution board

---

*This inventory represents starting stock. Additional parts can be purchased as needed — see PROCUREMENT.md (TBD).*
