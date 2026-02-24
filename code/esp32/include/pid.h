// =============================================================================
// EvoBot reference-01 — PID Controller
// =============================================================================
// Clean, reusable PID implementation with anti-windup.
// One instance per motor. Computes at PID_LOOP_HZ (50 Hz default).
//
// The PID takes a setpoint (target ticks per interval) and a measurement
// (actual ticks per interval from the encoder), and outputs a PWM duty
// value (0-255). Direction is handled separately by the motor driver.
// =============================================================================

#ifndef PID_H
#define PID_H

class PIDController {
public:
    PIDController();

    // Initialize with gain values
    void init(float kp, float ki, float kd);

    // Compute PID output given setpoint and measurement.
    // Returns a value clamped to [PID_OUTPUT_MIN, PID_OUTPUT_MAX].
    // dt is the time step in seconds.
    float compute(float setpoint, float measurement, float dt);

    // Update PID gains at runtime (via serial command)
    void setGains(float kp, float ki, float kd);

    // Reset internal state (integral accumulator, previous error).
    // Call this when motors are stopped or after an e-stop to prevent
    // integral windup from carrying over.
    void reset();

    // Accessors for current gains (for status reporting)
    float getKp() const { return _kp; }
    float getKi() const { return _ki; }
    float getKd() const { return _kd; }

private:
    float _kp;
    float _ki;
    float _kd;

    float _integral;        // Accumulated integral term
    float _prevError;       // Previous error for derivative calculation
    bool  _firstRun;        // Flag to skip derivative on first computation
};

#endif // PID_H
