// =============================================================================
// EvoBot reference-01 — Motor Driver
// =============================================================================
// Drives two DC motors via L293D H-bridge. Each motor has two direction
// pins (IN1/IN2 or IN3/IN4) and one PWM enable pin (ENA or ENB).
//
// Speed is set as -100 to +100 (percentage). Positive = forward,
// negative = reverse, 0 = stop. The driver translates this to:
//   - Direction pin states (HIGH/LOW for forward, LOW/HIGH for reverse)
//   - PWM duty cycle (0-255, mapped from absolute speed percentage)
//
// The driver does NOT run PID. It applies raw PWM values. The PID loop
// in main.cpp computes the PWM value and calls setPWM() directly.
//
// Safety: stop() ramps to zero. eStop() goes to zero instantly.
// =============================================================================

#ifndef MOTORS_H
#define MOTORS_H

#include <Arduino.h>

class Motors {
public:
    Motors();

    // Initialize motor pins and PWM channels. Call once in setup().
    void init();

    // Set motor speed as percentage: -100 (full reverse) to +100 (full forward).
    // Applies direction pins and maps |speed| to PWM duty (0-255).
    // Respects the deadband: speeds below SPEED_DEADBAND are treated as 0.
    void setSpeed(int leftSpeed, int rightSpeed);

    // Set raw PWM duty (0-255) and direction for each motor.
    // Used by the PID controller which computes its own PWM values.
    // direction: +1 = forward, -1 = reverse, 0 = stop
    void setLeftPWM(int pwm, int direction);
    void setRightPWM(int pwm, int direction);

    // Controlled stop: ramp both motors to zero over STOP_RAMP_MS.
    // Blocks until ramp is complete.
    void stop();

    // Emergency stop: immediately set both motors to zero PWM.
    // No ramp, no delay. Used for safety-critical stops.
    void eStop();

    // Get the last commanded speed values (for status reporting)
    int getLeftSpeed() const { return _leftSpeed; }
    int getRightSpeed() const { return _rightSpeed; }

private:
    // Apply direction and PWM to a single motor's hardware pins
    void applyMotorA(int pwm, int direction);
    void applyMotorB(int pwm, int direction);

    // Map speed percentage (-100..100) to PWM duty (0..255)
    int speedToPWM(int speed);

    // Last commanded speeds (for ramp-down calculation)
    int _leftSpeed;
    int _rightSpeed;

    // Current PWM values (for ramp-down)
    int _leftPWM;
    int _rightPWM;
    int _leftDir;
    int _rightDir;
};

#endif // MOTORS_H
