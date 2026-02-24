// =============================================================================
// EvoBot reference-01 — ESP32 Motor Control Firmware
// =============================================================================
// This firmware runs on the ESP32 and is responsible for:
//   1. Receiving motor commands from the Raspberry Pi over UART2
//   2. Running PID loops to maintain commanded velocities using encoder feedback
//   3. Independently monitoring for safety conditions (watchdog)
//   4. Reporting encoder data and status back to the Pi
//
// The ESP32 does NOT make decisions. It does not think. It executes motor
// commands faithfully and stops the motors if the Pi goes silent.
// This is the hard safety layer — Constitution Article 14.
//
// Boot sequence:
//   1. Initialize hardware (pins, PWM, UART, encoders)
//   2. Motors are OFF (BOOT state, waiting for first heartbeat)
//   3. Wait for Pi to send 'H' (heartbeat) to transition to ACTIVE
//   4. Once ACTIVE, process motor commands and run PID loops
//   5. If heartbeats stop → TIMED_OUT → motors killed
//   6. If 'E' received → E_STOP → motors locked until 'R' (reset)
//
// Safety invariant: every code path that can reach motor output passes
// through the watchdog check first. If motorsAllowed() is false, the
// motors stay at zero regardless of what commands arrive.
// =============================================================================

#include <Arduino.h>
#include "config.h"
#include "pid.h"
#include "motors.h"
#include "encoders.h"
#include "watchdog.h"
#include "serial_protocol.h"

// ---------------------------------------------------------------------------
// Global objects
// ---------------------------------------------------------------------------
Motors motors;
Encoders encoders;
Watchdog watchdog;
SerialProtocol protocol;
PIDController pidLeft;
PIDController pidRight;

// ---------------------------------------------------------------------------
// PID state
// ---------------------------------------------------------------------------
// Target speeds as received from the Pi (-100 to +100).
// These are converted to target ticks-per-interval for the PID.
int targetLeftSpeed = 0;
int targetRightSpeed = 0;

// PID loop timing
unsigned long lastPIDTime = 0;

// Encoder speed tracking (ticks per second, smoothed)
float leftTicksPerSec = 0.0f;
float rightTicksPerSec = 0.0f;

// Smoothing factor for speed calculation (exponential moving average)
// Lower = smoother but more lag. 0.3 is a reasonable starting point.
const float SPEED_SMOOTH_ALPHA = 0.3f;

// ---------------------------------------------------------------------------
// Debug helper
// ---------------------------------------------------------------------------
#if DEBUG_ENABLED
    #define DEBUG_PRINT(x)   Serial.print(x)
    #define DEBUG_PRINTLN(x) Serial.println(x)
#else
    #define DEBUG_PRINT(x)
    #define DEBUG_PRINTLN(x)
#endif

// ===========================================================================
// setup() — called once at boot
// ===========================================================================
void setup() {
    // --- Debug serial (USB console) ---
    #if DEBUG_ENABLED
    Serial.begin(115200);
    delay(100);
    Serial.println();
    Serial.println("==========================================");
    Serial.println("EvoBot reference-01 — ESP32 Motor Firmware");
    Serial.println("==========================================");
    Serial.println("State: BOOT (motors disabled, waiting for heartbeat)");
    #endif

    // --- Initialize subsystems ---

    // Serial protocol (UART2 to Pi)
    protocol.init();
    DEBUG_PRINTLN("[INIT] UART2 initialized (Pi link)");

    // Encoder ISRs
    encoders.init();
    DEBUG_PRINTLN("[INIT] Encoders initialized (ISR attached)");

    // Motor driver (PWM channels, direction pins)
    motors.init();
    DEBUG_PRINTLN("[INIT] Motors initialized (PWM off, direction pins LOW)");

    // PID controllers
    pidLeft.init(PID_KP_DEFAULT, PID_KI_DEFAULT, PID_KD_DEFAULT);
    pidRight.init(PID_KP_DEFAULT, PID_KI_DEFAULT, PID_KD_DEFAULT);
    DEBUG_PRINTLN("[INIT] PID controllers initialized");
    DEBUG_PRINT("[INIT] PID gains: Kp=");
    DEBUG_PRINT(PID_KP_DEFAULT);
    DEBUG_PRINT(" Ki=");
    DEBUG_PRINT(PID_KI_DEFAULT);
    DEBUG_PRINT(" Kd=");
    DEBUG_PRINTLN(PID_KD_DEFAULT);

    // Safety watchdog
    watchdog.init(WATCHDOG_TIMEOUT_MS);
    DEBUG_PRINT("[INIT] Watchdog initialized, timeout=");
    DEBUG_PRINT(WATCHDOG_TIMEOUT_MS);
    DEBUG_PRINTLN("ms");

    // PID loop timer
    lastPIDTime = millis();

    DEBUG_PRINTLN("[INIT] Boot complete. Waiting for first heartbeat...");
    DEBUG_PRINTLN();
}

// ===========================================================================
// loop() — runs continuously
// ===========================================================================
void loop() {
    unsigned long now = millis();

    // -----------------------------------------------------------------------
    // 1. WATCHDOG CHECK — runs every iteration, before anything else.
    //    This is the hard safety net. If the Pi is unresponsive, we kill
    //    the motors before processing any other logic.
    // -----------------------------------------------------------------------
    bool watchdogJustFired = watchdog.check();

    if (watchdogJustFired) {
        // Watchdog just transitioned to TIMED_OUT.
        // Kill motors immediately and notify Pi (if it's listening).
        motors.eStop();
        targetLeftSpeed = 0;
        targetRightSpeed = 0;
        pidLeft.reset();
        pidRight.reset();

        protocol.sendWatchdogTimeout();

        DEBUG_PRINTLN("[WDT] Watchdog timeout! Motors killed.");
    }

    // -----------------------------------------------------------------------
    // 2. SERIAL COMMAND PROCESSING — non-blocking read and dispatch.
    // -----------------------------------------------------------------------
    if (protocol.available()) {
        Command cmd = protocol.readCommand();

        switch (cmd.type) {

            // --- H: Heartbeat ---
            // Resets the watchdog timer. This is the lifeblood of the
            // safety system. If the Pi is alive, it sends this regularly.
            case CMD_HEARTBEAT:
                watchdog.feed();
                protocol.sendOK();
                DEBUG_PRINTLN("[CMD] Heartbeat received");
                break;

            // --- M <left> <right>: Motor speed command ---
            // Sets target velocity for PID control. Only processed if
            // the watchdog allows motor operation.
            case CMD_MOTOR:
                if (watchdog.getState() == WDT_E_STOP) {
                    protocol.sendError("ESTOP_LOCKED",
                        "E-stop active, send R to reset");
                    DEBUG_PRINTLN("[CMD] Motor command rejected: E_STOP active");
                } else if (!watchdog.motorsAllowed()) {
                    protocol.sendError("NOT_ACTIVE",
                        "No heartbeat received yet or watchdog timed out");
                    DEBUG_PRINTLN("[CMD] Motor command rejected: not ACTIVE");
                } else {
                    targetLeftSpeed = cmd.leftSpeed;
                    targetRightSpeed = cmd.rightSpeed;
                    protocol.sendOK();
                    DEBUG_PRINT("[CMD] Motor: L=");
                    DEBUG_PRINT(cmd.leftSpeed);
                    DEBUG_PRINT(" R=");
                    DEBUG_PRINTLN(cmd.rightSpeed);
                }
                break;

            // --- S: Controlled stop ---
            // Ramp motors to zero gracefully.
            case CMD_STOP:
                targetLeftSpeed = 0;
                targetRightSpeed = 0;
                motors.stop();
                pidLeft.reset();
                pidRight.reset();
                protocol.sendOK();
                DEBUG_PRINTLN("[CMD] Controlled stop");
                break;

            // --- E: Emergency stop ---
            // Immediate zero, lockout until reset. Constitution Art. 14.
            case CMD_E_STOP:
                motors.eStop();
                targetLeftSpeed = 0;
                targetRightSpeed = 0;
                pidLeft.reset();
                pidRight.reset();
                watchdog.triggerEStop();
                protocol.sendOK();
                DEBUG_PRINTLN("[CMD] EMERGENCY STOP — motors locked");
                break;

            // --- R: Reset after e-stop ---
            // Clears the e-stop lockout. Motors remain off until the Pi
            // sends a new heartbeat (transitions through BOOT → ACTIVE).
            case CMD_RESET:
                watchdog.reset();
                motors.eStop();  // Ensure motors are off during transition
                targetLeftSpeed = 0;
                targetRightSpeed = 0;
                pidLeft.reset();
                pidRight.reset();
                protocol.sendOK();
                DEBUG_PRINTLN("[CMD] Reset — waiting for heartbeat");
                break;

            // --- E?: Request encoder data ---
            case CMD_GET_ENCODERS: {
                long lt = encoders.getLeftTicks();
                long rt = encoders.getRightTicks();
                protocol.sendEncoderData(lt, rt, leftTicksPerSec, rightTicksPerSec);
                DEBUG_PRINT("[CMD] Encoders: L=");
                DEBUG_PRINT(lt);
                DEBUG_PRINT(" R=");
                DEBUG_PRINTLN(rt);
                break;
            }

            // --- S?: Request status ---
            case CMD_GET_STATUS:
                protocol.sendStatus(
                    watchdog.getStateName(),
                    watchdog.getUptime(),
                    watchdog.getTimeRemaining()
                );
                DEBUG_PRINT("[CMD] Status: ");
                DEBUG_PRINTLN(watchdog.getStateName());
                break;

            // --- P <Kp> <Ki> <Kd>: Set PID parameters ---
            case CMD_SET_PID:
                pidLeft.setGains(cmd.kp, cmd.ki, cmd.kd);
                pidRight.setGains(cmd.kp, cmd.ki, cmd.kd);
                protocol.sendOK();
                DEBUG_PRINT("[CMD] PID: Kp=");
                DEBUG_PRINT(cmd.kp);
                DEBUG_PRINT(" Ki=");
                DEBUG_PRINT(cmd.ki);
                DEBUG_PRINT(" Kd=");
                DEBUG_PRINTLN(cmd.kd);
                break;

            // --- Unknown or malformed command ---
            case CMD_UNKNOWN:
                protocol.sendError("BAD_CMD", cmd.errorMsg.c_str());
                DEBUG_PRINT("[CMD] Unknown: ");
                DEBUG_PRINTLN(cmd.errorMsg);
                break;

            // --- Empty line or parse failure ---
            case CMD_NONE:
            default:
                break;
        }
    }

    // -----------------------------------------------------------------------
    // 3. PID LOOP — runs at PID_LOOP_HZ (50 Hz, every 20ms).
    //    Only drives motors when watchdog allows it.
    // -----------------------------------------------------------------------
    if (now - lastPIDTime >= PID_LOOP_INTERVAL_MS) {
        float dt = (float)(now - lastPIDTime) / 1000.0f;  // seconds
        lastPIDTime = now;

        // Read encoder deltas (ticks since last PID cycle)
        long leftDelta = encoders.getLeftDelta();
        long rightDelta = encoders.getRightDelta();

        // Calculate ticks per second with exponential smoothing
        float rawLeftTPS = (float)leftDelta / dt;
        float rawRightTPS = (float)rightDelta / dt;

        leftTicksPerSec = (SPEED_SMOOTH_ALPHA * rawLeftTPS) +
                          ((1.0f - SPEED_SMOOTH_ALPHA) * leftTicksPerSec);
        rightTicksPerSec = (SPEED_SMOOTH_ALPHA * rawRightTPS) +
                           ((1.0f - SPEED_SMOOTH_ALPHA) * rightTicksPerSec);

        // Only run PID and drive motors if watchdog allows it
        if (watchdog.motorsAllowed()) {

            if (targetLeftSpeed == 0 && targetRightSpeed == 0) {
                // Both targets are zero — set motors off directly, skip PID.
                // This prevents PID integral from winding up while stopped.
                motors.setLeftPWM(0, 0);
                motors.setRightPWM(0, 0);
                pidLeft.reset();
                pidRight.reset();
            } else {
                // --- Left motor PID ---
                float leftSetpoint = (float)targetLeftSpeed * SPEED_TO_TICKS_SCALE;
                float leftMeasurement = (float)leftDelta;  // ticks this interval

                // The PID computes based on absolute values. Direction is
                // determined by the sign of the target speed.
                float leftAbsSetpoint = fabsf(leftSetpoint);
                float leftAbsMeasurement = fabsf(leftMeasurement);

                float leftPWM = pidLeft.compute(leftAbsSetpoint, leftAbsMeasurement, dt);

                int leftDir = 0;
                if (targetLeftSpeed > 0) leftDir = 1;
                else if (targetLeftSpeed < 0) leftDir = -1;

                // Apply deadband: if target is within deadband, set PWM to 0
                if (abs(targetLeftSpeed) < SPEED_DEADBAND) {
                    leftPWM = 0;
                    leftDir = 0;
                }

                motors.setLeftPWM((int)leftPWM, leftDir);

                // --- Right motor PID ---
                float rightSetpoint = (float)targetRightSpeed * SPEED_TO_TICKS_SCALE;
                float rightMeasurement = (float)rightDelta;

                float rightAbsSetpoint = fabsf(rightSetpoint);
                float rightAbsMeasurement = fabsf(rightMeasurement);

                float rightPWM = pidRight.compute(rightAbsSetpoint, rightAbsMeasurement, dt);

                int rightDir = 0;
                if (targetRightSpeed > 0) rightDir = 1;
                else if (targetRightSpeed < 0) rightDir = -1;

                if (abs(targetRightSpeed) < SPEED_DEADBAND) {
                    rightPWM = 0;
                    rightDir = 0;
                }

                motors.setRightPWM((int)rightPWM, rightDir);
            }
        } else {
            // Motors not allowed (BOOT, TIMED_OUT, or E_STOP).
            // Ensure motors are at zero and PID is reset.
            motors.setLeftPWM(0, 0);
            motors.setRightPWM(0, 0);
            pidLeft.reset();
            pidRight.reset();
        }
    }

    // -----------------------------------------------------------------------
    // 4. Small yield to prevent watchdog task starvation on ESP32.
    //    The ESP32 has a built-in task watchdog that fires if loop() never
    //    yields. A 1ms delay is sufficient and doesn't affect timing.
    // -----------------------------------------------------------------------
    delay(1);
}
