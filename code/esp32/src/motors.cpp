// =============================================================================
// EvoBot reference-01 — Motor Driver Implementation
// =============================================================================
// L293D truth table (per WIRING.md Section 8.4):
//   IN1=HIGH, IN2=LOW  → Forward
//   IN1=LOW,  IN2=HIGH → Reverse
//   IN1=LOW,  IN2=LOW  → Coast (free spin)
//   IN1=HIGH, IN2=HIGH → Brake (short circuit windings)
//
// We use coast (LOW/LOW) for the stopped state. This lets the robot roll
// to a gentle stop rather than locking the wheels.
// =============================================================================

#include "motors.h"
#include "config.h"

Motors::Motors()
    : _leftSpeed(0)
    , _rightSpeed(0)
    , _leftPWM(0)
    , _rightPWM(0)
    , _leftDir(0)
    , _rightDir(0)
{
}

void Motors::init() {
    // Configure direction pins as outputs
    pinMode(MOTOR_A_IN1, OUTPUT);
    pinMode(MOTOR_A_IN2, OUTPUT);
    pinMode(MOTOR_B_IN3, OUTPUT);
    pinMode(MOTOR_B_IN4, OUTPUT);

    // Configure PWM channels using ESP32 LEDC peripheral
    // ledcSetup(channel, frequency, resolution_bits)
    ledcSetup(PWM_CHANNEL_A, PWM_FREQ, PWM_RESOLUTION);
    ledcSetup(PWM_CHANNEL_B, PWM_FREQ, PWM_RESOLUTION);

    // Attach PWM channels to enable pins
    ledcAttachPin(MOTOR_A_ENA, PWM_CHANNEL_A);
    ledcAttachPin(MOTOR_B_ENB, PWM_CHANNEL_B);

    // Start with motors off — Constitution Article 14: fail-safe default
    eStop();
}

void Motors::setSpeed(int leftSpeed, int rightSpeed) {
    // Clamp to valid range
    leftSpeed = constrain(leftSpeed, -SPEED_MAX, SPEED_MAX);
    rightSpeed = constrain(rightSpeed, -SPEED_MAX, SPEED_MAX);

    _leftSpeed = leftSpeed;
    _rightSpeed = rightSpeed;

    // Determine direction and PWM for each motor
    int leftDir = 0;
    int rightDir = 0;

    if (leftSpeed > 0) leftDir = 1;
    else if (leftSpeed < 0) leftDir = -1;

    if (rightSpeed > 0) rightDir = 1;
    else if (rightSpeed < 0) rightDir = -1;

    int leftPWM = speedToPWM(abs(leftSpeed));
    int rightPWM = speedToPWM(abs(rightSpeed));

    _leftDir = leftDir;
    _rightDir = rightDir;
    _leftPWM = leftPWM;
    _rightPWM = rightPWM;

    applyMotorA(leftPWM, leftDir);
    applyMotorB(rightPWM, rightDir);
}

void Motors::setLeftPWM(int pwm, int direction) {
    pwm = constrain(pwm, 0, 255);
    _leftPWM = pwm;
    _leftDir = direction;
    applyMotorA(pwm, direction);
}

void Motors::setRightPWM(int pwm, int direction) {
    pwm = constrain(pwm, 0, 255);
    _rightPWM = pwm;
    _rightDir = direction;
    applyMotorB(pwm, direction);
}

void Motors::stop() {
    // Controlled stop: ramp down from current PWM to zero.
    // This prevents abrupt mechanical shock and reduces wheel skid.
    int stepsLeft = _leftPWM;
    int stepsRight = _rightPWM;
    int totalSteps = (STOP_RAMP_MS / STOP_RAMP_STEP_MS);

    if (totalSteps <= 0) totalSteps = 1;

    float leftDecrement = (float)stepsLeft / totalSteps;
    float rightDecrement = (float)stepsRight / totalSteps;

    float currentLeft = (float)_leftPWM;
    float currentRight = (float)_rightPWM;

    for (int i = 0; i < totalSteps; i++) {
        currentLeft -= leftDecrement;
        currentRight -= rightDecrement;

        if (currentLeft < 0) currentLeft = 0;
        if (currentRight < 0) currentRight = 0;

        applyMotorA((int)currentLeft, _leftDir);
        applyMotorB((int)currentRight, _rightDir);

        delay(STOP_RAMP_STEP_MS);
    }

    // Ensure we end at exactly zero
    eStop();
}

void Motors::eStop() {
    // IMMEDIATE stop. No ramp. No delay. Constitution Article 14.
    // Set PWM to zero and direction pins to coast (LOW/LOW).
    ledcWrite(PWM_CHANNEL_A, 0);
    ledcWrite(PWM_CHANNEL_B, 0);
    digitalWrite(MOTOR_A_IN1, LOW);
    digitalWrite(MOTOR_A_IN2, LOW);
    digitalWrite(MOTOR_B_IN3, LOW);
    digitalWrite(MOTOR_B_IN4, LOW);

    _leftSpeed = 0;
    _rightSpeed = 0;
    _leftPWM = 0;
    _rightPWM = 0;
    _leftDir = 0;
    _rightDir = 0;
}

// ---------------------------------------------------------------------------
// Private: Apply direction and PWM to Motor A (Left)
// ---------------------------------------------------------------------------
void Motors::applyMotorA(int pwm, int direction) {
    if (direction > 0) {
        // Forward: IN1=HIGH, IN2=LOW
        digitalWrite(MOTOR_A_IN1, HIGH);
        digitalWrite(MOTOR_A_IN2, LOW);
    } else if (direction < 0) {
        // Reverse: IN1=LOW, IN2=HIGH
        digitalWrite(MOTOR_A_IN1, LOW);
        digitalWrite(MOTOR_A_IN2, HIGH);
    } else {
        // Stop: coast (IN1=LOW, IN2=LOW)
        digitalWrite(MOTOR_A_IN1, LOW);
        digitalWrite(MOTOR_A_IN2, LOW);
        pwm = 0;
    }
    ledcWrite(PWM_CHANNEL_A, pwm);
}

// ---------------------------------------------------------------------------
// Private: Apply direction and PWM to Motor B (Right)
// ---------------------------------------------------------------------------
void Motors::applyMotorB(int pwm, int direction) {
    if (direction > 0) {
        // Forward: IN3=HIGH, IN4=LOW
        digitalWrite(MOTOR_B_IN3, HIGH);
        digitalWrite(MOTOR_B_IN4, LOW);
    } else if (direction < 0) {
        // Reverse: IN3=LOW, IN4=HIGH
        digitalWrite(MOTOR_B_IN3, LOW);
        digitalWrite(MOTOR_B_IN4, HIGH);
    } else {
        // Stop: coast
        digitalWrite(MOTOR_B_IN3, LOW);
        digitalWrite(MOTOR_B_IN4, LOW);
        pwm = 0;
    }
    ledcWrite(PWM_CHANNEL_B, pwm);
}

// ---------------------------------------------------------------------------
// Private: Map speed percentage to PWM duty cycle
// ---------------------------------------------------------------------------
int Motors::speedToPWM(int speed) {
    // Speed is 0-100 (absolute value, direction handled separately).
    // Below deadband: treat as zero (motor can't overcome stiction).
    if (speed < SPEED_DEADBAND) {
        return 0;
    }

    // Linear map: SPEED_DEADBAND..100 → ~some_min..255
    // The deadband creates a discontinuity. Motors jump from 0 to the
    // minimum effective PWM when speed crosses the deadband threshold.
    // This is intentional — values below the deadband just waste power
    // as heat without producing motion.
    return map(speed, 0, SPEED_MAX, 0, 255);
}
