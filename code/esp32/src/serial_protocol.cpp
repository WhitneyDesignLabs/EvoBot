// =============================================================================
// EvoBot reference-01 — Serial Protocol Implementation
// =============================================================================
// The parser is deliberately defensive. It rejects anything it doesn't
// understand rather than guessing. A robot that misinterprets a command
// is more dangerous than one that rejects it.
// =============================================================================

#include "serial_protocol.h"
#include "config.h"

SerialProtocol::SerialProtocol()
    : _bufferPos(0)
{
    memset(_buffer, 0, sizeof(_buffer));
}

void SerialProtocol::init() {
    // Initialize UART2 on the designated pins for Pi communication
    Serial2.begin(UART_BAUD, SERIAL_8N1, UART_RX_PIN, UART_TX_PIN);
}

bool SerialProtocol::available() {
    // Accumulate characters from Serial2 into the line buffer.
    // Return true when a newline is found (complete command ready).
    while (Serial2.available()) {
        char c = Serial2.read();

        if (c == '\n' || c == '\r') {
            // End of line — if we have any content, it's a complete command
            if (_bufferPos > 0) {
                _buffer[_bufferPos] = '\0';
                return true;
            }
            // Empty line (just a newline) — ignore it
            continue;
        }

        // Accumulate character, guarding against buffer overflow
        if (_bufferPos < (int)sizeof(_buffer) - 1) {
            _buffer[_bufferPos++] = c;
        } else {
            // Buffer overflow — discard everything and report error.
            // This prevents a malformed mega-string from corrupting state.
            _bufferPos = 0;
            memset(_buffer, 0, sizeof(_buffer));
        }
    }
    return false;
}

Command SerialProtocol::readCommand() {
    // Extract the buffered line and parse it
    String line = String(_buffer);

    // Clear the buffer for the next command
    _bufferPos = 0;
    memset(_buffer, 0, sizeof(_buffer));

    return parseCommand(line);
}

Command SerialProtocol::parseCommand(const String& line) {
    Command cmd;
    cmd.type = CMD_NONE;
    cmd.leftSpeed = 0;
    cmd.rightSpeed = 0;
    cmd.kp = 0;
    cmd.ki = 0;
    cmd.kd = 0;
    cmd.errorMsg = "";

    String trimmed = trim(line);

    if (trimmed.length() == 0) {
        cmd.type = CMD_NONE;
        return cmd;
    }

    // --- Single-character commands ---

    // H — Heartbeat
    if (trimmed == "H") {
        cmd.type = CMD_HEARTBEAT;
        return cmd;
    }

    // S — Controlled stop
    if (trimmed == "S") {
        cmd.type = CMD_STOP;
        return cmd;
    }

    // E — Emergency stop
    if (trimmed == "E") {
        cmd.type = CMD_E_STOP;
        return cmd;
    }

    // R — Reset after e-stop
    if (trimmed == "R") {
        cmd.type = CMD_RESET;
        return cmd;
    }

    // --- Query commands ---

    // E? — Request encoder data
    if (trimmed == "E?") {
        cmd.type = CMD_GET_ENCODERS;
        return cmd;
    }

    // S? — Request status
    if (trimmed == "S?") {
        cmd.type = CMD_GET_STATUS;
        return cmd;
    }

    // --- Commands with arguments ---

    // M <left> <right> — Set motor speeds
    if (trimmed.startsWith("M ")) {
        String args = trimmed.substring(2);
        args = trim(args);

        // Parse two integer arguments separated by space
        int spaceIdx = args.indexOf(' ');
        if (spaceIdx <= 0) {
            cmd.type = CMD_UNKNOWN;
            cmd.errorMsg = "BAD_ARGS M requires two arguments";
            return cmd;
        }

        String leftStr = args.substring(0, spaceIdx);
        String rightStr = trim(args.substring(spaceIdx + 1));

        // Validate that both are numbers
        // atoi returns 0 for non-numeric strings, so we also check the string
        bool leftValid = (leftStr.length() > 0);
        bool rightValid = (rightStr.length() > 0);

        // Check for non-numeric characters (allow leading minus sign)
        for (unsigned int i = 0; i < leftStr.length(); i++) {
            char c = leftStr.charAt(i);
            if (c != '-' && c != '+' && !isDigit(c)) {
                leftValid = false;
                break;
            }
        }
        for (unsigned int i = 0; i < rightStr.length(); i++) {
            char c = rightStr.charAt(i);
            if (c != '-' && c != '+' && !isDigit(c)) {
                rightValid = false;
                break;
            }
        }

        if (!leftValid || !rightValid) {
            cmd.type = CMD_UNKNOWN;
            cmd.errorMsg = "BAD_ARGS M arguments must be integers";
            return cmd;
        }

        int left = leftStr.toInt();
        int right = rightStr.toInt();

        // Range check: -100 to +100
        if (left < -SPEED_MAX || left > SPEED_MAX ||
            right < -SPEED_MAX || right > SPEED_MAX) {
            cmd.type = CMD_UNKNOWN;
            cmd.errorMsg = "BAD_ARGS speed must be -100 to 100";
            return cmd;
        }

        cmd.type = CMD_MOTOR;
        cmd.leftSpeed = left;
        cmd.rightSpeed = right;
        return cmd;
    }

    // P <Kp> <Ki> <Kd> — Set PID parameters
    if (trimmed.startsWith("P ")) {
        String args = trimmed.substring(2);
        args = trim(args);

        // Parse three float arguments separated by spaces
        int space1 = args.indexOf(' ');
        if (space1 <= 0) {
            cmd.type = CMD_UNKNOWN;
            cmd.errorMsg = "BAD_ARGS P requires three arguments (Kp Ki Kd)";
            return cmd;
        }

        String kpStr = args.substring(0, space1);
        String remaining = trim(args.substring(space1 + 1));

        int space2 = remaining.indexOf(' ');
        if (space2 <= 0) {
            cmd.type = CMD_UNKNOWN;
            cmd.errorMsg = "BAD_ARGS P requires three arguments (Kp Ki Kd)";
            return cmd;
        }

        String kiStr = remaining.substring(0, space2);
        String kdStr = trim(remaining.substring(space2 + 1));

        if (kpStr.length() == 0 || kiStr.length() == 0 || kdStr.length() == 0) {
            cmd.type = CMD_UNKNOWN;
            cmd.errorMsg = "BAD_ARGS P requires three arguments (Kp Ki Kd)";
            return cmd;
        }

        float kp = kpStr.toFloat();
        float ki = kiStr.toFloat();
        float kd = kdStr.toFloat();

        // Sanity check: gains should be non-negative and not absurdly large
        if (kp < 0 || ki < 0 || kd < 0 || kp > 100 || ki > 100 || kd > 100) {
            cmd.type = CMD_UNKNOWN;
            cmd.errorMsg = "BAD_ARGS PID gains must be 0-100";
            return cmd;
        }

        cmd.type = CMD_SET_PID;
        cmd.kp = kp;
        cmd.ki = ki;
        cmd.kd = kd;
        return cmd;
    }

    // Unknown command — reject with error
    cmd.type = CMD_UNKNOWN;
    cmd.errorMsg = "BAD_CMD unrecognized command";
    return cmd;
}

// ---------------------------------------------------------------------------
// Response methods — all write to Serial2 (UART2 to Pi)
// ---------------------------------------------------------------------------

void SerialProtocol::sendOK() {
    Serial2.println("OK");
}

void SerialProtocol::sendEncoderData(long leftTicks, long rightTicks,
                                      float leftSpeed, float rightSpeed) {
    // Format: D <leftTicks> <rightTicks> <leftSpeed> <rightSpeed>
    Serial2.print("D ");
    Serial2.print(leftTicks);
    Serial2.print(" ");
    Serial2.print(rightTicks);
    Serial2.print(" ");
    Serial2.print(leftSpeed, 2);    // 2 decimal places
    Serial2.print(" ");
    Serial2.println(rightSpeed, 2);
}

void SerialProtocol::sendStatus(const char* state, unsigned long uptimeMs,
                                 unsigned long watchdogRemainingMs) {
    // Format: ST <state> <uptime_ms> <watchdog_remaining_ms>
    Serial2.print("ST ");
    Serial2.print(state);
    Serial2.print(" ");
    Serial2.print(uptimeMs);
    Serial2.print(" ");
    Serial2.println(watchdogRemainingMs);
}

void SerialProtocol::sendError(const char* code, const char* message) {
    // Format: ER <code> <message>
    Serial2.print("ER ");
    Serial2.print(code);
    Serial2.print(" ");
    Serial2.println(message);
}

void SerialProtocol::sendWatchdogTimeout() {
    Serial2.println("WDT");
}

// ---------------------------------------------------------------------------
// Helper: trim whitespace from both ends of a String
// ---------------------------------------------------------------------------
String SerialProtocol::trim(const String& s) {
    int start = 0;
    int end = s.length() - 1;

    while (start <= end && (s.charAt(start) == ' ' || s.charAt(start) == '\t')) {
        start++;
    }
    while (end >= start && (s.charAt(end) == ' ' || s.charAt(end) == '\t')) {
        end--;
    }

    if (start > end) return "";
    return s.substring(start, end + 1);
}
