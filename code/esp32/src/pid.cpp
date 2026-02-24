// =============================================================================
// EvoBot reference-01 — PID Controller Implementation
// =============================================================================

#include "pid.h"
#include "config.h"

PIDController::PIDController()
    : _kp(0.0f)
    , _ki(0.0f)
    , _kd(0.0f)
    , _integral(0.0f)
    , _prevError(0.0f)
    , _firstRun(true)
{
}

void PIDController::init(float kp, float ki, float kd) {
    _kp = kp;
    _ki = ki;
    _kd = kd;
    reset();
}

float PIDController::compute(float setpoint, float measurement, float dt) {
    // Guard against zero or negative dt (should never happen, but be safe)
    if (dt <= 0.0f) {
        return 0.0f;
    }

    float error = setpoint - measurement;

    // --- Proportional term ---
    float pTerm = _kp * error;

    // --- Integral term with anti-windup ---
    _integral += error * dt;

    // Clamp integral to prevent windup.
    // If the motor is saturated (output at max/min), the integral would
    // keep growing, causing massive overshoot when the setpoint changes.
    if (_integral > PID_INTEGRAL_MAX) {
        _integral = PID_INTEGRAL_MAX;
    } else if (_integral < -PID_INTEGRAL_MAX) {
        _integral = -PID_INTEGRAL_MAX;
    }

    float iTerm = _ki * _integral;

    // --- Derivative term ---
    float dTerm = 0.0f;
    if (!_firstRun) {
        float derivative = (error - _prevError) / dt;
        dTerm = _kd * derivative;
    }
    _firstRun = false;
    _prevError = error;

    // --- Combine and clamp output ---
    float output = pTerm + iTerm + dTerm;

    // Clamp to valid PWM range
    if (output > PID_OUTPUT_MAX) {
        output = PID_OUTPUT_MAX;

        // Anti-windup: if output is saturated, stop accumulating integral
        // in the direction that would increase saturation.
        if (error > 0.0f) {
            _integral -= error * dt;  // Undo the integral accumulation
        }
    } else if (output < PID_OUTPUT_MIN) {
        output = PID_OUTPUT_MIN;

        // Anti-windup for negative saturation
        if (error < 0.0f) {
            _integral -= error * dt;
        }
    }

    return output;
}

void PIDController::setGains(float kp, float ki, float kd) {
    _kp = kp;
    _ki = ki;
    _kd = kd;
    // Don't reset integral/prev error — allow live tuning without disruption.
    // If the caller wants a full reset, they call reset() explicitly.
}

void PIDController::reset() {
    _integral = 0.0f;
    _prevError = 0.0f;
    _firstRun = true;
}
