// =============================================================================
// EvoBot reference-01 — Safety Watchdog
// =============================================================================
// Independent watchdog timer implementing Constitution Article 14:
// "When communication is lost, return to safe state."
//
// The watchdog tracks heartbeats from the Pi. If heartbeats stop arriving,
// the ESP32 kills the motors regardless of any other state. The Pi does
// NOT have the ability to disable or override this watchdog.
//
// State machine:
//
//   BOOT ──(first heartbeat)──→ ACTIVE ──(timeout)──→ TIMED_OUT
//     │                           ↑    ↑                  │
//     │                           │    └──(heartbeat)─────┘
//     │                           │
//     │                        (heartbeat resumes)
//     │                           │
//     │                      TIMED_OUT
//     │
//     └── Motors DISABLED until first heartbeat (fail-safe boot)
//
//   E_STOP is an orthogonal state: entered via E command, only cleared
//   by R (reset) command. While in E_STOP, motors stay at zero regardless
//   of heartbeat status.
// =============================================================================

#ifndef WATCHDOG_H
#define WATCHDOG_H

#include <Arduino.h>

// Watchdog states
enum WatchdogState {
    WDT_BOOT,          // Just powered on, no heartbeat received yet. Motors disabled.
    WDT_ACTIVE,        // Heartbeats arriving normally. Motors enabled.
    WDT_TIMED_OUT,     // Heartbeat missed for > timeout. Motors killed.
    WDT_E_STOP         // Emergency stop active. Motors locked at zero.
};

class Watchdog {
public:
    Watchdog();

    // Initialize the watchdog. Call once in setup().
    void init(unsigned long timeoutMs);

    // Feed the watchdog (heartbeat received from Pi).
    // Transitions: BOOT→ACTIVE, TIMED_OUT→ACTIVE.
    // Does NOT clear E_STOP — only reset() does that.
    void feed();

    // Check the watchdog. Call every loop iteration.
    // Returns true if the watchdog just transitioned to TIMED_OUT
    // (so the caller can send the WDT notification once).
    bool check();

    // Enter E_STOP state. Motors locked at zero until reset().
    void triggerEStop();

    // Reset from E_STOP state. Returns to BOOT (waits for next heartbeat).
    void reset();

    // Query current state
    WatchdogState getState() const { return _state; }

    // Are motors allowed to run?
    // Only true in ACTIVE state (not BOOT, not TIMED_OUT, not E_STOP).
    bool motorsAllowed() const { return _state == WDT_ACTIVE; }

    // Get milliseconds remaining before timeout (for status reporting).
    // Returns 0 if already timed out or in BOOT/E_STOP.
    unsigned long getTimeRemaining() const;

    // Get uptime in milliseconds since boot
    unsigned long getUptime() const;

    // Get a human-readable state name (for debug/status output)
    const char* getStateName() const;

private:
    WatchdogState _state;
    unsigned long _timeoutMs;
    unsigned long _lastFeedTime;
    unsigned long _bootTime;
};

#endif // WATCHDOG_H
