// =============================================================================
// EvoBot reference-01 — Serial Protocol Parser
// =============================================================================
// Parses ASCII commands from the Pi over UART2 and formats responses.
// Protocol is human-readable, line-based, newline-terminated.
//
// Commands (Pi → ESP32):
//   M <left> <right>      Set motor speeds (-100 to 100)
//   S                     Controlled stop (ramp down)
//   E                     Emergency stop (immediate zero, lockout)
//   R                     Reset after e-stop
//   H                     Heartbeat (reset watchdog timer)
//   E?                    Request encoder data
//   S?                    Request status
//   P <Kp> <Ki> <Kd>     Set PID parameters
//
// Responses (ESP32 → Pi):
//   OK                    Command acknowledged
//   D <lt> <rt> <ls> <rs> Encoder data (ticks and speeds)
//   ST <state> <up> <wdt> Status (state, uptime_ms, watchdog_remaining_ms)
//   ER <code> <message>   Error
//   WDT                   Watchdog timeout notification
//
// Malformed commands are rejected with ER BAD_CMD or ER BAD_ARGS.
// The parser never crashes on garbage input.
// =============================================================================

#ifndef SERIAL_PROTOCOL_H
#define SERIAL_PROTOCOL_H

#include <Arduino.h>

// ---------------------------------------------------------------------------
// Command types returned by the parser
// ---------------------------------------------------------------------------
enum CommandType {
    CMD_NONE,           // No command (empty line or parse failure)
    CMD_MOTOR,          // M <left> <right>
    CMD_STOP,           // S
    CMD_E_STOP,         // E
    CMD_RESET,          // R
    CMD_HEARTBEAT,      // H
    CMD_GET_ENCODERS,   // E?
    CMD_GET_STATUS,     // S?
    CMD_SET_PID,        // P <Kp> <Ki> <Kd>
    CMD_UNKNOWN         // Unrecognized command
};

// ---------------------------------------------------------------------------
// Parsed command structure
// ---------------------------------------------------------------------------
struct Command {
    CommandType type;

    // Motor command arguments (only valid when type == CMD_MOTOR)
    int leftSpeed;
    int rightSpeed;

    // PID command arguments (only valid when type == CMD_SET_PID)
    float kp;
    float ki;
    float kd;

    // Error info (only valid when type == CMD_UNKNOWN or CMD_NONE)
    String errorMsg;
};

// ---------------------------------------------------------------------------
// Serial Protocol class
// ---------------------------------------------------------------------------
class SerialProtocol {
public:
    SerialProtocol();

    // Initialize UART2 for Pi communication. Call once in setup().
    void init();

    // Check if a complete line is available. Non-blocking.
    // Returns true if a newline-terminated line has been received.
    bool available();

    // Read and parse the next complete command line.
    // Returns a Command struct with the parsed type and arguments.
    // If no complete line is available, returns CMD_NONE.
    Command readCommand();

    // Parse a command string into a Command struct.
    // Exposed publicly for unit testing.
    Command parseCommand(const String& line);

    // --- Response formatting and sending ---

    // Send OK acknowledgment
    void sendOK();

    // Send encoder data: D <leftTicks> <rightTicks> <leftSpeed> <rightSpeed>
    void sendEncoderData(long leftTicks, long rightTicks,
                         float leftSpeed, float rightSpeed);

    // Send status: ST <state> <uptime_ms> <watchdog_remaining_ms>
    void sendStatus(const char* state, unsigned long uptimeMs,
                    unsigned long watchdogRemainingMs);

    // Send error: ER <code> <message>
    void sendError(const char* code, const char* message);

    // Send watchdog timeout notification: WDT
    void sendWatchdogTimeout();

private:
    // Internal line buffer for accumulating incoming characters
    char _buffer[128];
    int _bufferPos;

    // Helper: trim whitespace from a String
    String trim(const String& s);
};

#endif // SERIAL_PROTOCOL_H
