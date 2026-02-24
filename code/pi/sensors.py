"""
EvoBot Sensor Interface — Perception abstraction layer

Reads all onboard sensors and returns clean data to the main loop.
The main loop never talks to GPIO directly — it calls SensorHub.read_all()
and gets a SensorState dataclass.

Sensors:
    - HC-SR04 ultrasonic x2 (left, right) via GPIO trigger/echo
    - MPU6050 IMU via I2C (accelerometer + gyroscope)
    - USB webcam via OpenCV

All sensors handle errors gracefully: return None or stale data, never crash.
If a sensor is unavailable at startup, it is marked disabled and skipped.
"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

import numpy as np

from logger import Logger

# Attempt GPIO import — will fail off-Pi, that is handled gracefully
try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    _GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    _GPIO_AVAILABLE = False

# Attempt I2C import
try:
    import smbus2
    _I2C_AVAILABLE = True
except ImportError:
    _I2C_AVAILABLE = False

# Attempt OpenCV import
try:
    import cv2
    _CV2_AVAILABLE = True
except ImportError:
    _CV2_AVAILABLE = False


# ---------- Data structures ----------


@dataclass
class IMUData:
    """Orientation and acceleration from the MPU6050."""
    accel_x: float = 0.0  # m/s^2
    accel_y: float = 0.0
    accel_z: float = 0.0
    gyro_x: float = 0.0   # degrees/s
    gyro_y: float = 0.0
    gyro_z: float = 0.0
    temperature: float = 0.0  # Celsius


@dataclass
class EncoderData:
    """Encoder tick counts from the ESP32 (populated by main loop)."""
    left_ticks: int = 0
    right_ticks: int = 0


@dataclass
class SensorState:
    """
    Complete snapshot of all sensor readings at a point in time.

    This is the primary data object passed through the main loop.
    """
    timestamp: float = 0.0
    ultrasonics: Dict[str, Optional[float]] = field(default_factory=dict)
    imu: Optional[IMUData] = None
    encoders: Optional[EncoderData] = None
    camera_frame: Optional[np.ndarray] = None
    battery_voltage: Optional[float] = None


# ---------- Individual sensor classes ----------


class UltrasonicSensor:
    """
    HC-SR04 ultrasonic distance sensor via GPIO trigger/echo.

    Sends a 10us trigger pulse and measures the echo return time to
    calculate distance in centimeters. Uses level-shifted echo pins
    (5V -> 3.3V) per the wiring guide.
    """

    # Speed of sound at ~20C in cm/us (divided by 2 for round-trip)
    _CM_PER_US = 0.01715

    def __init__(
        self,
        name: str,
        trigger_pin: int,
        echo_pin: int,
        logger: Logger,
        timeout_s: float = 0.04,
    ) -> None:
        """
        Args:
            name: Sensor identifier (e.g. 'left', 'right')
            trigger_pin: BCM GPIO number for trigger output
            echo_pin: BCM GPIO number for echo input
            logger: Logger instance
            timeout_s: Max time to wait for echo (default 40ms ~= 680cm max)
        """
        self.name = name
        self._trigger = trigger_pin
        self._echo = echo_pin
        self._logger = logger
        self._timeout = timeout_s
        self._enabled = False
        self._last_reading: Optional[float] = None

    def init(self) -> bool:
        """
        Set up GPIO pins for this sensor.

        Returns:
            True if GPIO setup succeeded.
        """
        if not _GPIO_AVAILABLE:
            self._logger.log(
                "WARN", "sensors",
                f"Ultrasonic '{self.name}': GPIO not available, sensor disabled",
            )
            return False

        try:
            GPIO.setup(self._trigger, GPIO.OUT, initial=GPIO.LOW)
            GPIO.setup(self._echo, GPIO.IN)
            self._enabled = True
            self._logger.log(
                "INFO", "sensors",
                f"Ultrasonic '{self.name}': trigger=GPIO{self._trigger}, "
                f"echo=GPIO{self._echo} — initialized",
            )
            return True
        except Exception as e:
            self._logger.log(
                "ERROR", "sensors",
                f"Ultrasonic '{self.name}' init failed: {e}",
            )
            return False

    def read(self) -> Optional[float]:
        """
        Take a single distance measurement.

        Returns:
            Distance in centimeters, or None on timeout/error.
            Returns stale cached value if current read fails.
        """
        if not self._enabled:
            return self._last_reading

        try:
            # Send 10us trigger pulse
            GPIO.output(self._trigger, GPIO.HIGH)
            time.sleep(0.00001)  # 10 microseconds
            GPIO.output(self._trigger, GPIO.LOW)

            # Wait for echo to go HIGH (start of return pulse)
            start_wait = time.time()
            while GPIO.input(self._echo) == 0:
                pulse_start = time.time()
                if pulse_start - start_wait > self._timeout:
                    return self._last_reading  # Timeout waiting for echo start

            # Wait for echo to go LOW (end of return pulse)
            while GPIO.input(self._echo) == 1:
                pulse_end = time.time()
                if pulse_end - pulse_start > self._timeout:
                    return self._last_reading  # Timeout waiting for echo end

            # Calculate distance from pulse duration
            pulse_duration = pulse_end - pulse_start
            distance_cm = pulse_duration * 1_000_000 * self._CM_PER_US

            # Sanity check — HC-SR04 range is 2-400cm
            if 2.0 <= distance_cm <= 400.0:
                self._last_reading = round(distance_cm, 1)
                return self._last_reading
            else:
                return self._last_reading  # Out of range, return stale

        except Exception as e:
            self._logger.log(
                "WARN", "sensors",
                f"Ultrasonic '{self.name}' read error: {e}",
            )
            return self._last_reading

    def cleanup(self) -> None:
        """Release GPIO pins."""
        if self._enabled and _GPIO_AVAILABLE:
            try:
                GPIO.cleanup(self._trigger)
                GPIO.cleanup(self._echo)
            except Exception:
                pass


class IMU:
    """
    MPU6050 6-axis IMU via I2C (smbus2).

    Reads 3-axis accelerometer and 3-axis gyroscope data over the I2C bus.
    Also reads the onboard temperature sensor.
    """

    # MPU6050 register addresses
    _PWR_MGMT_1 = 0x6B
    _ACCEL_XOUT_H = 0x3B
    _TEMP_OUT_H = 0x41
    _GYRO_XOUT_H = 0x43
    _WHO_AM_I = 0x75

    # Scale factors for default ranges (+/- 2g accel, +/- 250 deg/s gyro)
    _ACCEL_SCALE = 16384.0  # LSB/g
    _GYRO_SCALE = 131.0     # LSB/(deg/s)
    _G_TO_MS2 = 9.80665     # Convert g to m/s^2

    def __init__(
        self,
        bus_number: int,
        address: int,
        logger: Logger,
    ) -> None:
        """
        Args:
            bus_number: I2C bus (typically 1 on Pi 3B)
            address: Device address (0x68 default for MPU6050)
            logger: Logger instance
        """
        self._bus_number = bus_number
        self._address = address
        self._logger = logger
        self._bus: Optional[smbus2.SMBus] = None  # type: ignore
        self._enabled = False
        self._last_data: Optional[IMUData] = None

    def init(self) -> bool:
        """
        Initialize the MPU6050 — wake it from sleep and verify identity.

        Returns:
            True if MPU6050 is responding correctly.
        """
        if not _I2C_AVAILABLE:
            self._logger.log(
                "WARN", "sensors",
                "IMU: smbus2 not available, sensor disabled",
            )
            return False

        try:
            self._bus = smbus2.SMBus(self._bus_number)

            # Check WHO_AM_I register (should return 0x68)
            who = self._bus.read_byte_data(self._address, self._WHO_AM_I)
            if who != 0x68:
                self._logger.log(
                    "WARN", "sensors",
                    f"IMU: WHO_AM_I returned 0x{who:02X}, expected 0x68",
                )

            # Wake up MPU6050 (it starts in sleep mode)
            self._bus.write_byte_data(self._address, self._PWR_MGMT_1, 0x00)
            time.sleep(0.1)  # Allow sensor to stabilize

            self._enabled = True
            self._logger.log(
                "INFO", "sensors",
                f"IMU: MPU6050 on I2C bus {self._bus_number} "
                f"at 0x{self._address:02X} — initialized",
            )
            return True

        except Exception as e:
            self._logger.log(
                "ERROR", "sensors", f"IMU init failed: {e}",
            )
            return False

    def read(self) -> Optional[IMUData]:
        """
        Read all 6 axes plus temperature from the MPU6050.

        Returns:
            IMUData with accelerometer, gyroscope, and temperature readings.
            Returns stale cached data on read failure.
        """
        if not self._enabled or self._bus is None:
            return self._last_data

        try:
            # Read 14 bytes starting from ACCEL_XOUT_H
            # Layout: accel(6) + temp(2) + gyro(6) = 14 bytes
            raw = self._bus.read_i2c_block_data(
                self._address, self._ACCEL_XOUT_H, 14
            )

            # Convert raw bytes to signed 16-bit values
            ax = self._to_signed(raw[0], raw[1])
            ay = self._to_signed(raw[2], raw[3])
            az = self._to_signed(raw[4], raw[5])
            temp_raw = self._to_signed(raw[6], raw[7])
            gx = self._to_signed(raw[8], raw[9])
            gy = self._to_signed(raw[10], raw[11])
            gz = self._to_signed(raw[12], raw[13])

            data = IMUData(
                accel_x=round((ax / self._ACCEL_SCALE) * self._G_TO_MS2, 3),
                accel_y=round((ay / self._ACCEL_SCALE) * self._G_TO_MS2, 3),
                accel_z=round((az / self._ACCEL_SCALE) * self._G_TO_MS2, 3),
                gyro_x=round(gx / self._GYRO_SCALE, 2),
                gyro_y=round(gy / self._GYRO_SCALE, 2),
                gyro_z=round(gz / self._GYRO_SCALE, 2),
                temperature=round(temp_raw / 340.0 + 36.53, 1),
            )

            self._last_data = data
            return data

        except Exception as e:
            self._logger.log(
                "WARN", "sensors", f"IMU read error: {e}",
            )
            return self._last_data

    def cleanup(self) -> None:
        """Close the I2C bus."""
        if self._bus is not None:
            try:
                self._bus.close()
            except Exception:
                pass

    @staticmethod
    def _to_signed(high: int, low: int) -> int:
        """Convert two bytes (high, low) to a signed 16-bit integer."""
        value = (high << 8) | low
        if value >= 0x8000:
            value -= 0x10000
        return value


class Camera:
    """
    USB webcam capture via OpenCV.

    Captures frames from the first available USB camera. Resolution is kept
    low (320x240 default) to stay within Pi 3B CPU budget.
    """

    def __init__(
        self,
        device: int,
        resolution: Tuple[int, int],
        fps: int,
        logger: Logger,
    ) -> None:
        """
        Args:
            device: Video device index (0 = /dev/video0)
            resolution: (width, height) tuple
            fps: Target capture framerate
            logger: Logger instance
        """
        self._device = device
        self._width, self._height = resolution
        self._fps = fps
        self._logger = logger
        self._cap: Optional[cv2.VideoCapture] = None  # type: ignore
        self._enabled = False
        self._last_frame: Optional[np.ndarray] = None

    def init(self) -> bool:
        """
        Open the camera device and configure resolution/FPS.

        Returns:
            True if camera opened successfully and is providing frames.
        """
        if not _CV2_AVAILABLE:
            self._logger.log(
                "WARN", "sensors",
                "Camera: OpenCV not available, camera disabled",
            )
            return False

        try:
            self._cap = cv2.VideoCapture(self._device)
            if not self._cap.isOpened():
                self._logger.log(
                    "WARN", "sensors",
                    f"Camera: device {self._device} could not be opened",
                )
                return False

            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
            self._cap.set(cv2.CAP_PROP_FPS, self._fps)

            # Test capture
            ret, frame = self._cap.read()
            if ret and frame is not None:
                self._enabled = True
                actual_w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                actual_h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                self._logger.log(
                    "INFO", "sensors",
                    f"Camera: device {self._device} — "
                    f"{actual_w}x{actual_h} @ {self._fps}fps — initialized",
                )
                return True
            else:
                self._logger.log(
                    "WARN", "sensors",
                    "Camera: test capture failed, camera disabled",
                )
                self._cap.release()
                return False

        except Exception as e:
            self._logger.log(
                "ERROR", "sensors", f"Camera init failed: {e}",
            )
            return False

    def read(self) -> Optional[np.ndarray]:
        """
        Capture a single frame from the webcam.

        Returns:
            numpy array (BGR format) or None on failure.
            Returns stale cached frame on read failure.
        """
        if not self._enabled or self._cap is None:
            return self._last_frame

        try:
            ret, frame = self._cap.read()
            if ret and frame is not None:
                self._last_frame = frame
                return frame
            return self._last_frame
        except Exception as e:
            self._logger.log(
                "WARN", "sensors", f"Camera read error: {e}",
            )
            return self._last_frame

    def cleanup(self) -> None:
        """Release the camera device."""
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass


# ---------- Sensor aggregator ----------


class SensorHub:
    """
    Aggregates all sensors and returns a unified SensorState.

    The main loop calls SensorHub.read_all() each cycle and gets a clean
    data object regardless of which sensors are available. Failed or
    missing sensors return None — they never crash the hub.
    """

    def __init__(self, config: dict, logger: Logger) -> None:
        """
        Initialize all sensors from the 'sensors' section of robot.yaml.

        Args:
            config: The 'sensors' section from robot.yaml
            logger: Logger instance
        """
        self._logger = logger
        self._ultrasonics: Dict[str, UltrasonicSensor] = {}
        self._imu: Optional[IMU] = None
        self._camera: Optional[Camera] = None

        # Initialize ultrasonic sensors
        us_config = config.get("ultrasonic", {})
        for name, pins in us_config.items():
            trigger = pins.get("trigger_pin")
            echo = pins.get("echo_pin")
            if trigger is not None and echo is not None:
                sensor = UltrasonicSensor(name, trigger, echo, logger)
                self._ultrasonics[name] = sensor

        # Initialize IMU
        imu_config = config.get("imu", {})
        if imu_config:
            bus = imu_config.get("bus", 1)
            # Handle hex string or int for address
            addr_raw = imu_config.get("address", 0x68)
            if isinstance(addr_raw, str):
                addr = int(addr_raw, 16)
            else:
                addr = addr_raw
            self._imu = IMU(bus, addr, logger)

        # Initialize camera
        cam_config = config.get("camera", {})
        if cam_config:
            device = cam_config.get("device", 0)
            resolution = tuple(cam_config.get("resolution", [320, 240]))
            fps = cam_config.get("fps", 10)
            self._camera = Camera(device, resolution, fps, logger)

    def init(self) -> dict:
        """
        Initialize all sensors. Non-fatal — sensors that fail are disabled.

        Returns:
            Dict of sensor names to init success booleans.
        """
        results = {}

        for name, sensor in self._ultrasonics.items():
            results[f"ultrasonic_{name}"] = sensor.init()

        if self._imu is not None:
            results["imu"] = self._imu.init()

        if self._camera is not None:
            results["camera"] = self._camera.init()

        self._logger.log(
            "INFO", "sensors",
            f"Sensor init complete: {results}",
            results,
        )
        return results

    def read_all(self, encoder_data: Optional[Tuple[int, int]] = None) -> SensorState:
        """
        Read all sensors and return a unified SensorState.

        Args:
            encoder_data: Optional (left_ticks, right_ticks) from motors.get_encoders().
                         Passed in because encoder data comes from the ESP32 via motors.py,
                         not directly from sensor hardware.

        Returns:
            SensorState with all current readings.
        """
        state = SensorState(timestamp=time.time())

        # Ultrasonic readings — stagger by 30ms to avoid echo cross-talk
        for name, sensor in self._ultrasonics.items():
            state.ultrasonics[name] = sensor.read()
            if len(self._ultrasonics) > 1:
                time.sleep(0.03)  # 30ms stagger per WIRING.md spec

        # IMU
        if self._imu is not None:
            state.imu = self._imu.read()

        # Camera
        if self._camera is not None:
            state.camera_frame = self._camera.read()

        # Encoders (passed in from main loop)
        if encoder_data is not None:
            state.encoders = EncoderData(
                left_ticks=encoder_data[0],
                right_ticks=encoder_data[1],
            )

        return state

    def read_ultrasonic(self, sensor_name: str) -> Optional[float]:
        """
        Read a single ultrasonic sensor by name.

        Args:
            sensor_name: Sensor identifier (e.g. 'left', 'right')

        Returns:
            Distance in cm, or None if sensor not found/disabled.
        """
        sensor = self._ultrasonics.get(sensor_name)
        if sensor is not None:
            return sensor.read()
        return None

    def read_imu(self) -> Optional[IMUData]:
        """Read the IMU sensor."""
        if self._imu is not None:
            return self._imu.read()
        return None

    def read_camera(self) -> Optional[np.ndarray]:
        """Capture a camera frame."""
        if self._camera is not None:
            return self._camera.read()
        return None

    def self_test(self) -> dict:
        """
        Verify all configured sensors respond with sane values.

        Returns:
            Dict of sensor names to test results.
        """
        results = {}

        for name, sensor in self._ultrasonics.items():
            reading = sensor.read()
            results[f"ultrasonic_{name}"] = {
                "ok": reading is not None,
                "value_cm": reading,
            }

        if self._imu is not None:
            imu_data = self._imu.read()
            # Sane check: accel_z should be roughly 9.8 m/s^2 when stationary
            if imu_data is not None:
                accel_magnitude = (
                    imu_data.accel_x**2
                    + imu_data.accel_y**2
                    + imu_data.accel_z**2
                ) ** 0.5
                results["imu"] = {
                    "ok": 5.0 < accel_magnitude < 15.0,
                    "accel_magnitude": round(accel_magnitude, 2),
                }
            else:
                results["imu"] = {"ok": False, "reason": "no data"}

        if self._camera is not None:
            frame = self._camera.read()
            results["camera"] = {
                "ok": frame is not None,
                "shape": list(frame.shape) if frame is not None else None,
            }

        self._logger.log(
            "INFO", "sensors", f"Self-test results: {results}", results,
        )
        return results

    def cleanup(self) -> None:
        """Release all sensor resources."""
        for sensor in self._ultrasonics.values():
            sensor.cleanup()
        if self._imu is not None:
            self._imu.cleanup()
        if self._camera is not None:
            self._camera.cleanup()

        if _GPIO_AVAILABLE:
            try:
                GPIO.cleanup()
            except Exception:
                pass

        self._logger.log("INFO", "sensors", "All sensors cleaned up")
