// =============================================================================
// EvoBot reference-01 — ESP32 Motor Controller Configuration
// =============================================================================
// All pin definitions and tunable constants live here. Change this file
// to adapt the firmware to different wiring or hardware. No magic numbers
// should exist anywhere else in the codebase.
//
// Pin assignments match WIRING.md (the single source of truth for electrical
// connections). If this file disagrees with WIRING.md, fix this file.
// =============================================================================

#ifndef CONFIG_H
#define CONFIG_H

// ---------------------------------------------------------------------------
// Motor A (Left) — L293D channel A
// ---------------------------------------------------------------------------
#define MOTOR_A_IN1     25      // GPIO25 → L293D IN1 (direction pin 1)
#define MOTOR_A_IN2     26      // GPIO26 → L293D IN2 (direction pin 2)
#define MOTOR_A_ENA     32      // GPIO32 → L293D ENA (PWM speed control)

// ---------------------------------------------------------------------------
// Motor B (Right) — L293D channel B
// ---------------------------------------------------------------------------
#define MOTOR_B_IN3     27      // GPIO27 → L293D IN3 (direction pin 1)
#define MOTOR_B_IN4     14      // GPIO14 → L293D IN4 (direction pin 2)
#define MOTOR_B_ENB     33      // GPIO33 → L293D ENB (PWM speed control)

// ---------------------------------------------------------------------------
// PWM Configuration
// ---------------------------------------------------------------------------
#define PWM_FREQ        20000   // 20 kHz — above human hearing, no motor whine
#define PWM_RESOLUTION  8       // 8-bit resolution: 0-255 duty cycle
#define PWM_CHANNEL_A   0       // LEDC channel for Motor A
#define PWM_CHANNEL_B   1       // LEDC channel for Motor B

// ---------------------------------------------------------------------------
// Encoder Inputs (ESP32 input-only GPIOs — external 10k pull-ups required)
// ---------------------------------------------------------------------------
#define ENC_LEFT_A      34      // GPIO34 — Left motor encoder channel A
#define ENC_LEFT_B      35      // GPIO35 — Left motor encoder channel B
#define ENC_RIGHT_A     36      // GPIO36 (VP) — Right motor encoder channel A
#define ENC_RIGHT_B     39      // GPIO39 (VN) — Right motor encoder channel B

// ---------------------------------------------------------------------------
// UART2 — Serial link to Raspberry Pi
// ---------------------------------------------------------------------------
#define UART_RX_PIN     16      // GPIO16 — receives commands from Pi TX (GPIO14)
#define UART_TX_PIN     17      // GPIO17 — sends data to Pi RX (GPIO15)
#define UART_BAUD       115200  // 115200 baud, 8N1, no flow control

// ---------------------------------------------------------------------------
// PID Controller Defaults
// ---------------------------------------------------------------------------
// These are starting values. Tune empirically on real hardware.
// Adjustable at runtime via the 'P <Kp> <Ki> <Kd>' serial command.
#define PID_KP_DEFAULT  2.0f
#define PID_KI_DEFAULT  0.5f
#define PID_KD_DEFAULT  0.1f

// Output limits — PID output is clamped to valid PWM range
#define PID_OUTPUT_MIN  0.0f
#define PID_OUTPUT_MAX  255.0f

// Anti-windup: maximum absolute value the integral term can accumulate.
// Prevents integral windup when the motor is saturated or stalled.
#define PID_INTEGRAL_MAX 200.0f

// ---------------------------------------------------------------------------
// PID Loop Timing
// ---------------------------------------------------------------------------
#define PID_LOOP_HZ     50      // PID runs at 50 Hz (every 20ms)
#define PID_LOOP_INTERVAL_MS (1000 / PID_LOOP_HZ)  // 20ms

// ---------------------------------------------------------------------------
// Speed Command Mapping
// ---------------------------------------------------------------------------
// Speed commands from the Pi are -100 to +100 (percentage of max).
// These are mapped to a target ticks-per-interval for the PID controller.
// This scaling factor converts speed percentage to encoder ticks per PID
// interval. It depends on motor RPM, gear ratio, and encoder resolution.
//
// TT motors with 20-slot encoder and ~1:48 gear ratio give ~960 edges per
// wheel revolution (quadrature). At full speed (~200 RPM output shaft):
//   960 ticks/rev * 200 RPM / 60 sec = 3200 ticks/sec
//   At 50 Hz PID: 3200 / 50 = 64 ticks per interval at full speed
//
// So speed=100 maps to ~64 ticks/interval. This is approximate and will
// need tuning with real hardware.
#define SPEED_TO_TICKS_SCALE 0.64f  // speed * scale = target ticks/interval
                                     // 100 * 0.64 = 64 ticks/interval

// Minimum speed below which motors don't move (deadband / stiction)
#define SPEED_DEADBAND  5

// Maximum allowed speed value from serial commands
#define SPEED_MAX       100

// ---------------------------------------------------------------------------
// Watchdog / Heartbeat
// ---------------------------------------------------------------------------
// The watchdog is the hard safety net. If the Pi stops sending heartbeats,
// the ESP32 kills the motors independently. Constitution Article 14:
// "When communication is lost, return to safe state."
#define WATCHDOG_TIMEOUT_MS  1000   // 1 second without heartbeat → motors off

// ---------------------------------------------------------------------------
// Controlled Stop Ramp
// ---------------------------------------------------------------------------
// When a controlled stop (S command) is issued, ramp speed to zero over
// this many milliseconds. E-stop ignores this and goes to zero instantly.
#define STOP_RAMP_MS    200
#define STOP_RAMP_STEP_MS 10    // Ramp step interval

// ---------------------------------------------------------------------------
// Serial Buffer
// ---------------------------------------------------------------------------
#define SERIAL_BUFFER_SIZE 128  // Max characters per incoming command line

// ---------------------------------------------------------------------------
// Debug Output
// ---------------------------------------------------------------------------
// Set to 1 to enable debug messages on Serial (USB console).
// Set to 0 for production — only Serial2 (Pi link) is active.
#define DEBUG_ENABLED   1

#endif // CONFIG_H
