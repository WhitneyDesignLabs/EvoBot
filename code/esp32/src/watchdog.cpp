// =============================================================================
// EvoBot reference-01 — Safety Watchdog Implementation
// =============================================================================
// Every failure mode results in motors OFF. This is the definition of
// fail-safe. The watchdog is the ESP32's independent safety layer — it does
// not need the Pi's permission to stop the motors.
// =============================================================================

#include "watchdog.h"

Watchdog::Watchdog()
    : _state(WDT_BOOT)
    , _timeoutMs(1000)
    , _lastFeedTime(0)
    , _bootTime(0)
{
}

void Watchdog::init(unsigned long timeoutMs) {
    _timeoutMs = timeoutMs;
    _bootTime = millis();
    _lastFeedTime = 0;  // No heartbeat received yet
    _state = WDT_BOOT;  // Motors disabled until first heartbeat
}

void Watchdog::feed() {
    _lastFeedTime = millis();

    // State transitions on heartbeat:
    //   BOOT → ACTIVE      (first heartbeat received, enable motors)
    //   TIMED_OUT → ACTIVE  (heartbeat resumed after timeout, re-enable motors)
    //   ACTIVE → ACTIVE     (normal operation, just refresh timer)
    //   E_STOP → E_STOP     (heartbeat does NOT clear e-stop, only reset() does)
    if (_state == WDT_BOOT || _state == WDT_TIMED_OUT) {
        _state = WDT_ACTIVE;
    }
    // If _state == WDT_E_STOP, stay in E_STOP. The Pi must send R (reset)
    // to explicitly acknowledge and clear the emergency stop.
}

bool Watchdog::check() {
    // E_STOP state is sticky — only reset() clears it.
    // Don't apply timeout logic while in E_STOP.
    if (_state == WDT_E_STOP) {
        return false;
    }

    // BOOT state: we haven't received any heartbeat yet. Stay in BOOT.
    // Motors remain disabled. Don't trigger a timeout notification — the
    // Pi might still be booting.
    if (_state == WDT_BOOT) {
        return false;
    }

    // ACTIVE state: check if heartbeat has timed out
    if (_state == WDT_ACTIVE) {
        unsigned long now = millis();
        unsigned long elapsed = now - _lastFeedTime;

        // Handle millis() overflow (wraps every ~49 days)
        if (elapsed > _timeoutMs) {
            _state = WDT_TIMED_OUT;
            return true;  // Signal: watchdog just fired, caller should notify
        }
    }

    // TIMED_OUT state: remain timed out. Return false because we already
    // signaled the transition. The caller only needs to know ONCE.
    return false;
}

void Watchdog::triggerEStop() {
    _state = WDT_E_STOP;
}

void Watchdog::reset() {
    // Reset from E_STOP goes back to BOOT, not ACTIVE.
    // The Pi must send a heartbeat to transition to ACTIVE.
    // This ensures the Pi is actually alive and communicating before
    // motors are re-enabled after an emergency stop.
    _state = WDT_BOOT;
    _lastFeedTime = 0;
}

unsigned long Watchdog::getTimeRemaining() const {
    if (_state != WDT_ACTIVE) {
        return 0;
    }

    unsigned long now = millis();
    unsigned long elapsed = now - _lastFeedTime;

    if (elapsed >= _timeoutMs) {
        return 0;
    }
    return _timeoutMs - elapsed;
}

unsigned long Watchdog::getUptime() const {
    return millis() - _bootTime;
}

const char* Watchdog::getStateName() const {
    switch (_state) {
        case WDT_BOOT:      return "BOOT";
        case WDT_ACTIVE:    return "ACTIVE";
        case WDT_TIMED_OUT: return "TIMED_OUT";
        case WDT_E_STOP:    return "E_STOP";
        default:             return "UNKNOWN";
    }
}
