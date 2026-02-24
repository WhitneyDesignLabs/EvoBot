// =============================================================================
// EvoBot reference-01 — Quadrature Encoder Implementation
// =============================================================================
// Interrupt-driven quadrature decoding. On each rising edge of channel A,
// we read channel B to determine direction:
//   - Channel B HIGH → forward (increment)
//   - Channel B LOW  → reverse (decrement)
//
// This gives one count per encoder slot transition on channel A. Full
// quadrature decoding (rising + falling on both channels) would give 4x
// resolution but is more CPU-intensive. 1x decoding is sufficient for
// TT motors at the PID rates we use.
// =============================================================================

#include "encoders.h"
#include "config.h"

// Static instance pointer — allows ISRs (which must be static/free functions)
// to call back into the Encoders object.
Encoders* Encoders::_instance = nullptr;

Encoders::Encoders()
    : _leftTicks(0)
    , _rightTicks(0)
    , _leftTicksLast(0)
    , _rightTicksLast(0)
    , _mux(portMUX_INITIALIZER_UNLOCKED)
{
    _instance = this;
}

void Encoders::init() {
    // Configure encoder pins as inputs.
    // GPIO34, 35, 36, 39 are input-only on ESP32 — no pull-up capability.
    // External 10k pull-ups to 3.3V must be installed (see WIRING.md).
    pinMode(ENC_LEFT_A, INPUT);
    pinMode(ENC_LEFT_B, INPUT);
    pinMode(ENC_RIGHT_A, INPUT);
    pinMode(ENC_RIGHT_B, INPUT);

    // Attach interrupts on rising edge of channel A for each motor.
    // RISING edge gives one count per slot. This is 1x decoding.
    attachInterrupt(digitalPinToInterrupt(ENC_LEFT_A), isrLeftA, RISING);
    attachInterrupt(digitalPinToInterrupt(ENC_RIGHT_A), isrRightA, RISING);
}

// ---------------------------------------------------------------------------
// ISR: Left motor encoder — channel A rising edge
// ---------------------------------------------------------------------------
void IRAM_ATTR Encoders::isrLeftA() {
    if (_instance == nullptr) return;

    // Read channel B to determine direction
    if (digitalRead(ENC_LEFT_B)) {
        _instance->_leftTicks++;   // Channel B HIGH → forward
    } else {
        _instance->_leftTicks--;   // Channel B LOW → reverse
    }
}

// ---------------------------------------------------------------------------
// ISR: Right motor encoder — channel A rising edge
// ---------------------------------------------------------------------------
void IRAM_ATTR Encoders::isrRightA() {
    if (_instance == nullptr) return;

    // Read channel B to determine direction
    if (digitalRead(ENC_RIGHT_B)) {
        _instance->_rightTicks++;  // Channel B HIGH → forward
    } else {
        _instance->_rightTicks--;  // Channel B LOW → reverse
    }
}

// ---------------------------------------------------------------------------
// Thread-safe tick accessors
// ---------------------------------------------------------------------------
// Uses a portMUX spinlock to prevent torn reads. On ESP32, volatile long
// reads are not atomic on both cores — the ISR could fire mid-read and
// give a partially updated value.
// ---------------------------------------------------------------------------

long Encoders::getLeftTicks() {
    long ticks;
    portENTER_CRITICAL(&_mux);
    ticks = _leftTicks;
    portEXIT_CRITICAL(&_mux);
    return ticks;
}

long Encoders::getRightTicks() {
    long ticks;
    portENTER_CRITICAL(&_mux);
    ticks = _rightTicks;
    portEXIT_CRITICAL(&_mux);
    return ticks;
}

long Encoders::getLeftDelta() {
    long ticks = getLeftTicks();
    long delta = ticks - _leftTicksLast;
    _leftTicksLast = ticks;
    return delta;
}

long Encoders::getRightDelta() {
    long ticks = getRightTicks();
    long delta = ticks - _rightTicksLast;
    _rightTicksLast = ticks;
    return delta;
}

void Encoders::reset() {
    portENTER_CRITICAL(&_mux);
    _leftTicks = 0;
    _rightTicks = 0;
    portEXIT_CRITICAL(&_mux);
    _leftTicksLast = 0;
    _rightTicksLast = 0;
}
