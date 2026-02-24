// =============================================================================
// EvoBot reference-01 — Quadrature Encoder Reader
// =============================================================================
// ISR-driven quadrature decoding for two motors. Each motor has two encoder
// channels (A and B). On a rising edge of channel A, channel B's state
// determines direction: B HIGH = forward, B LOW = reverse.
//
// ESP32 GPIO34, 35, 36, 39 are input-only with no internal pull-ups.
// External 10k pull-up resistors to 3.3V are REQUIRED (see WIRING.md).
//
// Tick counters are declared volatile because they are modified inside ISRs.
// Access from the main loop uses critical sections to prevent torn reads
// on the 32-bit counters.
// =============================================================================

#ifndef ENCODERS_H
#define ENCODERS_H

#include <Arduino.h>

class Encoders {
public:
    Encoders();

    // Initialize encoder pins and attach interrupts.
    // Call once in setup().
    void init();

    // Get cumulative tick count for each motor.
    // These are signed values: positive = forward, negative = reverse.
    // Thread-safe (uses critical section).
    long getLeftTicks();
    long getRightTicks();

    // Get ticks elapsed since the last call to getLeftSpeed/getRightSpeed.
    // Returns the delta ticks for the interval. The caller divides by the
    // time interval to get ticks/sec if needed.
    // Thread-safe (uses critical section).
    long getLeftDelta();
    long getRightDelta();

    // Reset cumulative tick counters to zero.
    void reset();

    // ISR handlers — these must be static because attachInterrupt() needs
    // a plain function pointer. They call into instance methods via a
    // static instance pointer.
    static void IRAM_ATTR isrLeftA();
    static void IRAM_ATTR isrRightA();

private:
    // Cumulative tick counters (modified by ISRs)
    volatile long _leftTicks;
    volatile long _rightTicks;

    // Snapshot values for delta computation
    long _leftTicksLast;
    long _rightTicksLast;

    // Spinlock for thread-safe access to tick counters
    portMUX_TYPE _mux;

    // Static instance pointer for ISR routing
    static Encoders* _instance;
};

#endif // ENCODERS_H
