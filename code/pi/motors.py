"""
EvoBot Motor Interface — Serial communication with ESP32

This module does NOT drive motors directly. It sends ASCII serial commands
to the ESP32 motor controller and parses responses. The Pi never touches
PWM pins — that is the ESP32's job.

Serial protocol (from WIRING.md):
    Pi -> ESP32:
        M <left> <right>\\n   — set motor speeds (-255 to +255)
        S\\n                   — stop all motors
        E?\\n                  — query encoder counts
        H\\n                   — heartbeat (watchdog keep-alive)
        P <Kp> <Ki> <Kd>\\n   — set PID parameters

    ESP32 -> Pi:
        E <left> <right>\\n   — encoder counts
        OK\\n                  — command acknowledged
        ERR <msg>\\n           — error
        WDT\\n                 — watchdog timeout fired
"""

import threading
import time
from typing import Optional, Tuple

try:
    import serial
except ImportError:
    serial = None  # type: ignore

from logger import Logger


class MotorController:
    """
    Serial interface to the ESP32 motor controller.

    Manages the serial connection with auto-reconnect, sends motor commands,
    reads encoder data, and maintains the heartbeat to keep the ESP32 watchdog
    alive.

    All speed values sent to this module use the range -100 to +100.
    They are mapped to the -255 to +255 PWM range expected by the ESP32.
    """

    def __init__(self, config: dict, logger: Logger) -> None:
        """
        Initialize motor controller from robot.yaml config.

        Args:
            config: The 'serial' section of robot.yaml, plus 'motors' section
            logger: Logger instance for structured logging
        """
        self._logger = logger
        self._port_name = config.get("port", "/dev/ttyAMA0")
        self._baud = config.get("baud", 115200)
        self._timeout = config.get("timeout_ms", 100) / 1000.0
        self._handshake_retries = config.get("handshake_retries", 5)

        # Motor parameters
        motor_config = config.get("motors", {})
        self._max_speed = motor_config.get("max_speed", 100)
        self._ramp_rate = motor_config.get("ramp_rate", 10)
        self._deadband = motor_config.get("deadband", 5)

        # State
        self._serial: Optional[serial.Serial] = None  # type: ignore
        self._lock = threading.Lock()
        self._connected = False
        self._last_left = 0
        self._last_right = 0
        self._estop_active = False

    def connect(self) -> bool:
        """
        Open serial connection and perform handshake with ESP32.

        Returns:
            True if connection and handshake succeeded, False otherwise.
        """
        if serial is None:
            self._logger.log("ERROR", "motors", "pyserial not installed")
            return False

        for attempt in range(1, self._handshake_retries + 1):
            try:
                self._logger.log(
                    "INFO", "motors",
                    f"Connecting to ESP32 on {self._port_name} "
                    f"(attempt {attempt}/{self._handshake_retries})",
                )
                self._serial = serial.Serial(
                    port=self._port_name,
                    baudrate=self._baud,
                    timeout=self._timeout,
                )
                # Small delay for ESP32 to stabilize after serial open
                time.sleep(0.1)

                # Flush any stale data
                self._serial.reset_input_buffer()
                self._serial.reset_output_buffer()

                # Handshake: send heartbeat, expect OK
                self._serial.write(b"H\n")
                response = self._read_line(timeout=1.0)
                if response == "OK":
                    self._connected = True
                    self._estop_active = False
                    self._logger.log("INFO", "motors", "ESP32 handshake OK")
                    return True
                else:
                    self._logger.log(
                        "WARN", "motors",
                        f"Handshake unexpected response: {response!r}",
                    )
                    self._serial.close()
            except Exception as e:
                self._logger.log(
                    "WARN", "motors",
                    f"Connection attempt {attempt} failed: {e}",
                )
                if self._serial is not None:
                    try:
                        self._serial.close()
                    except Exception:
                        pass

            time.sleep(0.5)

        self._logger.log(
            "ERROR", "motors",
            f"Failed to connect to ESP32 after {self._handshake_retries} attempts",
        )
        self._connected = False
        return False

    def send_speed(self, left: int, right: int) -> bool:
        """
        Send motor speed command to ESP32.

        Args:
            left: Left motor speed, -100 to +100
            right: Right motor speed, -100 to +100

        Returns:
            True if command was sent and acknowledged.
        """
        if self._estop_active:
            self._logger.log(
                "WARN", "motors",
                "send_speed rejected: E_STOP active. Send reset() first.",
            )
            return False

        # Clamp to valid range
        left = max(-100, min(100, left))
        right = max(-100, min(100, right))

        # Apply deadband — below this threshold motors stall, just send zero
        if abs(left) < self._deadband:
            left = 0
        if abs(right) < self._deadband:
            right = 0

        # Map -100..+100 to -255..+255 for ESP32 PWM
        left_pwm = int(left * 255 / 100)
        right_pwm = int(right * 255 / 100)

        cmd = f"M {left_pwm} {right_pwm}\n"
        ok = self._send_and_ack(cmd)

        if ok:
            self._last_left = left
            self._last_right = right
            self._logger.log(
                "ACTION", "motors",
                f"Speed set: left={left} right={right} (PWM: {left_pwm}, {right_pwm})",
                {"left": left, "right": right, "left_pwm": left_pwm, "right_pwm": right_pwm},
            )
        return ok

    def stop(self) -> bool:
        """
        Send controlled stop command.

        Returns:
            True if command was sent and acknowledged.
        """
        ok = self._send_and_ack("S\n")
        if ok:
            self._last_left = 0
            self._last_right = 0
            self._logger.log("ACTION", "motors", "Stop command sent")
        return ok

    def e_stop(self) -> bool:
        """
        Send emergency stop command. Immediate motor kill, no ramp.

        After e_stop, the ESP32 enters a locked state and will not accept
        speed commands until reset() is called.

        Returns:
            True if command was sent and acknowledged.
        """
        # E_STOP uses the regular stop command — the ESP32 handles it as immediate
        # We send S (stop) and mark locally as e-stopped.
        # The ESP32 protocol uses S for stop. For a true e-stop we send S and
        # flag the controller.
        ok = self._send_and_ack("S\n")
        self._estop_active = True
        self._last_left = 0
        self._last_right = 0
        self._logger.log(
            "SAFETY", "motors",
            "E_STOP sent — motors killed, controller locked",
        )
        self._logger.log(
            "ACTION", "motors", "E_STOP executed",
            {"estop_active": True},
        )
        return ok

    def reset(self) -> bool:
        """
        Clear E_STOP lock and re-enable motor commands.

        Returns:
            True if heartbeat was re-established.
        """
        ok = self.heartbeat()
        if ok:
            self._estop_active = False
            self._logger.log("INFO", "motors", "E_STOP cleared, motors re-enabled")
        return ok

    def get_encoders(self) -> Optional[Tuple[int, int]]:
        """
        Request current encoder tick counts from ESP32.

        Returns:
            Tuple of (left_ticks, right_ticks) or None on failure.
        """
        with self._lock:
            if not self._ensure_connected():
                return None
            try:
                self._serial.write(b"E?\n")  # type: ignore
                response = self._read_line(timeout=0.2)
                if response and response.startswith("E "):
                    parts = response.split()
                    if len(parts) >= 3:
                        left_ticks = int(parts[1])
                        right_ticks = int(parts[2])
                        return (left_ticks, right_ticks)
                self._logger.log(
                    "WARN", "motors",
                    f"Unexpected encoder response: {response!r}",
                )
                return None
            except Exception as e:
                self._logger.log("ERROR", "motors", f"get_encoders failed: {e}")
                self._connected = False
                return None

    def heartbeat(self) -> bool:
        """
        Send heartbeat to reset ESP32 watchdog timer.

        Must be called at the configured interval (default every 250ms) to
        keep the ESP32 from killing the motors.

        Returns:
            True if heartbeat was acknowledged.
        """
        return self._send_and_ack("H\n")

    def get_status(self) -> Optional[dict]:
        """
        Get current motor controller status.

        Returns:
            Dict with connection state, last speeds, e-stop status.
        """
        return {
            "connected": self._connected,
            "estop_active": self._estop_active,
            "last_left": self._last_left,
            "last_right": self._last_right,
            "port": self._port_name,
        }

    def close(self) -> None:
        """Clean shutdown of serial connection."""
        # Try to stop motors before closing
        if self._connected:
            try:
                self._serial.write(b"S\n")  # type: ignore
                time.sleep(0.05)
            except Exception:
                pass

        if self._serial is not None:
            try:
                self._serial.close()
            except Exception:
                pass

        self._connected = False
        self._logger.log("INFO", "motors", "Serial connection closed")

    # --- Private methods ---

    def _send_and_ack(self, cmd: str) -> bool:
        """
        Send a command and wait for OK acknowledgment.

        Thread-safe. Handles reconnection on serial failure.

        Args:
            cmd: ASCII command string (must end with \\n)

        Returns:
            True if OK received, False otherwise.
        """
        with self._lock:
            if not self._ensure_connected():
                return False
            try:
                self._serial.write(cmd.encode("ascii"))  # type: ignore
                response = self._read_line(timeout=0.2)
                if response == "OK":
                    return True
                elif response and response.startswith("ERR"):
                    self._logger.log(
                        "WARN", "motors",
                        f"ESP32 error for cmd {cmd.strip()!r}: {response}",
                    )
                    return False
                elif response == "WDT":
                    self._logger.log(
                        "SAFETY", "motors",
                        "ESP32 watchdog timeout detected",
                    )
                    return False
                else:
                    self._logger.log(
                        "WARN", "motors",
                        f"Unexpected response for {cmd.strip()!r}: {response!r}",
                    )
                    return False
            except Exception as e:
                self._logger.log(
                    "ERROR", "motors", f"Serial write failed: {e}",
                )
                self._connected = False
                return False

    def _read_line(self, timeout: float = 0.2) -> Optional[str]:
        """
        Read one newline-terminated line from serial.

        Args:
            timeout: Max seconds to wait for a complete line.

        Returns:
            Stripped line string, or None on timeout/error.
        """
        if self._serial is None:
            return None
        old_timeout = self._serial.timeout
        self._serial.timeout = timeout
        try:
            raw = self._serial.readline()
            if raw:
                return raw.decode("ascii", errors="replace").strip()
            return None
        except Exception:
            return None
        finally:
            self._serial.timeout = old_timeout

    def _ensure_connected(self) -> bool:
        """
        Check connection state and attempt reconnect if needed.

        Returns:
            True if connected (possibly after reconnect).
        """
        if self._connected and self._serial is not None and self._serial.is_open:
            return True

        self._logger.log("WARN", "motors", "Serial disconnected, attempting reconnect")
        return self.connect()
