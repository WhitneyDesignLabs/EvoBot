# EvoBot Shopping List

## Priority: Blocks v1 Build

These items are needed before the first drive test and are not currently in inventory.

| Item | Why | Est. Price | Link/Notes |
|---|---|---|---|
| **2x Geared DC Motor w/ Encoder** (12V, 6mm shaft) | Drive motors for v1. Encoder feedback essential for controlled movement. JGB37-520 or similar, ~100-300 RPM. | $15-25/pair | Amazon: "JGB37-520 encoder motor" or "12V geared DC motor encoder" |
| **1x Caster wheel** (ball or swivel, ~25-30mm) | Third contact point for differential drive stability | $3-5 | Amazon: "ball caster robot" |
| **1x Motor driver (L298N or TB6612FNG)** | Drive the two geared motors from Pi/ESP32. L298N if on hand works, TB6612 is more efficient. | $5-8 | May already have — check shop |
| **1x PCA9685 servo driver board** | 16-channel PWM over I2C. For future servo/arm control, keeps GPIO clean. | $5-8 | Amazon: "PCA9685 servo driver I2C" |
| **1x 12V battery pack** (3S LiPo or 3S LiFePO4) | Mobile power. XT60 connector preferred. ~2200-5000mAh for initial testing. | $15-30 | Could build from cells in stock instead |
| **Standoffs, M3 screws, nuts assortment** | Mounting boards to chassis | $8-12 | Amazon: "M3 standoff assortment kit" |

**Estimated total for v1 essentials: ~$50-90** (less if motors/battery built from stock)

---

## Priority: Nice to Have for v1

| Item | Why | Est. Price | Notes |
|---|---|---|---|
| Pi Camera Module v2 (or v3) | CSI interface, better than USB webcam for Pi integration | $25-30 | USB webcam works as fallback |
| Ribbon cable for Pi Camera | If buying Pi Camera | $3-5 | |
| XT60 connectors (male+female set) | Standard power connectors for battery swapping | $5-8 | |
| Wire management (cable ties, spiral wrap) | Keep the build clean and maintainable | $5-8 | |

---

## Future Phases

| Item | Phase | Est. Price | Notes |
|---|---|---|---|
| SO-101 arm kit (or parts to build) | Phase 5 | $100-300 | 6-DOF open source arm — Hugging Face LeRobot project |
| Dynamixel or serial bus servos | Phase 5 | $80-200 | For arm joints if not using SO-101 kit servos |
| LiDAR module (RPLIDAR A1 or similar) | Phase 2 | $80-100 | Better mapping than ultrasonic |
| Charging dock components | Phase 6 | $20-40 | Spring contacts, alignment guides |

---

## Procurement Notes

- **Build vs. buy:** Prefer building from stock (batteries, motor mounts, chassis) where possible
- **Budget authority:** Claude (architect) can recommend purchases; Scott approves
- **Vendor preference:** Amazon for speed; AliExpress for bulk/cost when time permits
- **Fabrication first:** If it can be 3D printed, laser cut, or built from stock — do that before buying

---

*Updated as needs are identified. Items move off this list when acquired.*
