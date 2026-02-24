"""
EvoBot Safety Monitor — Constitutional Compliance Engine

The most critical module. Enforces the Opengates Constitution at runtime.
Every physical action passes through this module before execution.
It is not advisory — it has veto power.

Constitutional article mapping:
    Art. 4  — Irreversibility: assess if action is reversible
    Art. 5  — Cascading Consequences: evaluate second-order effects
    Art. 12 — Safety Hierarchy: human > living being > property > task
    Art. 13 — Physical Action Protocols: pre-verify, monitor, confirm
    Art. 14 — Fail-Safe Defaults: when in doubt, stop
    Art. 15 — Authorization Levels: classify every action by risk
    Art. 17 — Logging: all safety events recorded in append-only log
"""

import math
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple

from logger import Logger
from sensors import SensorState


@dataclass
class SafetyEvent:
    """A single safety event for logging."""
    timestamp: float
    event_type: str
    article: str
    details: str
    action_taken: str


# Authorization levels per Constitution Article 15
AUTH_LEVEL_DESCRIPTIONS = {
    0: "Passive observation (read sensors, log data) — no authorization needed",
    1: "Low-speed movement (< 30% max speed) — auto-approved",
    2: "Normal movement (30-70% max speed) — auto-approved with monitoring",
    3: "High-speed or sustained operation — requires human authorization",
    4: "Irreversible or safety-affecting action — requires explicit human confirmation",
}


class SafetyMonitor:
    """
    Constitutional compliance engine for EvoBot.

    Validates every proposed motor command against current sensor state
    and constitutional rules. Has veto power over any action. Monitors
    continuously during operation for emergency conditions.

    This module can trigger emergency stops independently via the
    motor controller reference.
    """

    def __init__(
        self,
        config: dict,
        logger: Logger,
        motors: Optional[object] = None,
    ) -> None:
        """
        Initialize safety monitor from the 'safety' section of robot.yaml.

        Args:
            config: The 'safety' section from robot.yaml
            logger: Logger instance
            motors: Reference to MotorController for emergency stop capability.
                    Set via set_motors() after construction if not available at init.
        """
        self._logger = logger
        self._motors = motors

        # Safety thresholds from config
        self._emergency_distance_cm = config.get("emergency_stop_distance_cm", 15)
        self._warning_distance_cm = config.get("warning_distance_cm", 40)
        self._max_speed_near_obstacle = config.get("max_speed_near_obstacle", 30)
        self._max_tilt_degrees = config.get("max_tilt_degrees", 30)
        self._min_battery_voltage = config.get("min_battery_voltage", 6.0)

        # Internal state
        self._consecutive_safety_events = 0
        self._max_consecutive_before_halt = 5
        self._last_action_time = 0.0
        self._human_auth_level = 2  # Max auto-approved level (0, 1, 2 auto-approved)

        self._logger.log(
            "INFO", "safety",
            "Safety monitor initialized",
            {
                "emergency_distance_cm": self._emergency_distance_cm,
                "warning_distance_cm": self._warning_distance_cm,
                "max_speed_near_obstacle": self._max_speed_near_obstacle,
                "max_tilt_degrees": self._max_tilt_degrees,
            },
        )

    def set_motors(self, motors: object) -> None:
        """
        Set the motor controller reference for emergency stop capability.

        Args:
            motors: MotorController instance
        """
        self._motors = motors

    def check_action(
        self,
        action: dict,
        sensor_state: Optional[SensorState] = None,
    ) -> Tuple[bool, str]:
        """
        Validate a proposed action against safety rules.

        This is called BEFORE any physical action is executed. If this
        returns (False, reason), the action MUST NOT be executed.

        Args:
            action: Dict describing the proposed action. Expected keys:
                    - "type": "set_speed" | "stop" | "e_stop"
                    - "left": int (-100 to 100), for set_speed
                    - "right": int (-100 to 100), for set_speed
            sensor_state: Current sensor readings for context.

        Returns:
            Tuple of (approved: bool, reason: str).
            If approved is False, reason explains which rule was violated.
        """
        action_type = action.get("type", "unknown")

        # Stop and e_stop are always approved
        if action_type in ("stop", "e_stop"):
            return True, "Stop commands are always approved"

        if action_type != "set_speed":
            return False, f"Unknown action type: {action_type}"

        left = action.get("left", 0)
        right = action.get("right", 0)
        max_speed = max(abs(left), abs(right))

        # --- Authorization Level Check (Art. 15) ---
        auth_required = self.get_authorization_level(action)
        if auth_required > self._human_auth_level:
            reason = (
                f"Art. 15: Action requires authorization level {auth_required} "
                f"({AUTH_LEVEL_DESCRIPTIONS.get(auth_required, 'unknown')}). "
                f"Current auto-approved max: {self._human_auth_level}."
            )
            self._log_safety_event("auth_denied", "Art. 15", reason, "blocked")
            return False, reason

        # --- Sensor-Based Safety Checks ---
        if sensor_state is not None:
            # Check ultrasonic distances (Art. 12, 14)
            rejection = self._check_obstacle_distance(left, right, max_speed, sensor_state)
            if rejection is not None:
                return False, rejection

            # Check IMU tilt (Art. 14)
            rejection = self._check_tilt(sensor_state)
            if rejection is not None:
                return False, rejection

            # Check battery voltage (Art. 14)
            rejection = self._check_battery(sensor_state)
            if rejection is not None:
                return False, rejection

        # --- Cascading Consequence Check (Art. 5) ---
        # At the proposed speed, can we stop before hitting an obstacle?
        if sensor_state is not None and max_speed > 0:
            rejection = self._check_stopping_distance(max_speed, sensor_state)
            if rejection is not None:
                return False, rejection

        # All checks passed
        self._consecutive_safety_events = 0
        return True, "Approved"

    def check_continuous(self, sensor_state: SensorState) -> List[str]:
        """
        Continuous safety monitoring — called every cycle during execution.

        Returns a list of active safety conditions. Can trigger automatic
        E_STOP for immediate dangers.

        Args:
            sensor_state: Current sensor readings.

        Returns:
            List of active safety condition strings (empty = all clear).
        """
        conditions = []

        # Check for emergency distance violations
        for name, distance in sensor_state.ultrasonics.items():
            if distance is not None and distance < self._emergency_distance_cm:
                condition = (
                    f"EMERGENCY: {name} ultrasonic at {distance:.1f}cm "
                    f"(threshold: {self._emergency_distance_cm}cm)"
                )
                conditions.append(condition)
                self._trigger_e_stop(condition)

        # Check IMU tilt
        if sensor_state.imu is not None:
            tilt = self._calculate_tilt(sensor_state)
            if tilt is not None and tilt > self._max_tilt_degrees:
                condition = (
                    f"EMERGENCY: Tilt at {tilt:.1f} degrees "
                    f"(max: {self._max_tilt_degrees} degrees)"
                )
                conditions.append(condition)
                self._trigger_e_stop(condition)

        # Check battery
        if sensor_state.battery_voltage is not None:
            if sensor_state.battery_voltage < self._min_battery_voltage:
                condition = (
                    f"CRITICAL: Battery at {sensor_state.battery_voltage:.1f}V "
                    f"(min: {self._min_battery_voltage}V)"
                )
                conditions.append(condition)
                self._trigger_e_stop(condition)

        # Track consecutive safety events
        if conditions:
            self._consecutive_safety_events += 1
            if self._consecutive_safety_events >= self._max_consecutive_before_halt:
                conditions.append(
                    f"HALT: {self._consecutive_safety_events} consecutive "
                    f"safety events — system requires human intervention"
                )
        else:
            self._consecutive_safety_events = 0

        return conditions

    def get_authorization_level(self, action: dict) -> int:
        """
        Classify an action by its required authorization level.

        Per Constitution Article 15:
            Level 0: Read sensors, log data — no authorization
            Level 1: Low-speed movement (< 30%) — auto-approved
            Level 2: Normal movement (30-70%) — auto-approved with monitoring
            Level 3: High-speed or sustained — requires human auth
            Level 4: Irreversible or safety-affecting — requires human confirmation

        Args:
            action: Dict describing the action.

        Returns:
            Integer authorization level 0-4.
        """
        action_type = action.get("type", "unknown")

        if action_type in ("read_sensors", "log"):
            return 0

        if action_type in ("stop", "e_stop"):
            return 0  # Stopping is always safe

        if action_type == "set_speed":
            left = abs(action.get("left", 0))
            right = abs(action.get("right", 0))
            max_speed = max(left, right)

            if max_speed == 0:
                return 0
            elif max_speed <= 30:
                return 1
            elif max_speed <= 70:
                return 2
            elif max_speed <= 100:
                return 3
            else:
                return 4  # Over 100 is out of range — should not happen

        # Unknown action type gets highest level
        return 4

    def log_safety_event(
        self,
        event_type: str,
        details: dict,
    ) -> None:
        """
        Record a safety event in the append-only safety log.

        Per Constitution Article 17, safety events are logged separately
        and the safety log is never truncated by software.

        Args:
            event_type: Category string (e.g. 'e_stop', 'command_blocked')
            details: Dict with full event details
        """
        self._logger.log_safety(event_type, details)

    # --- Private methods ---

    def _check_obstacle_distance(
        self,
        left: int,
        right: int,
        max_speed: int,
        state: SensorState,
    ) -> Optional[str]:
        """
        Check if proposed movement is safe given obstacle distances.

        Art. 12: Safety hierarchy — obstacles take priority over task.
        Art. 14: Fail-safe — if sensor reads danger, respect it.

        Returns:
            Rejection reason string, or None if safe.
        """
        for name, distance in state.ultrasonics.items():
            if distance is None:
                continue

            # Emergency distance — reject any forward movement
            if distance < self._emergency_distance_cm:
                # Only block if we are moving toward the obstacle
                # For now, treat all movement as potentially toward obstacle
                if max_speed > 0:
                    reason = (
                        f"Art. 12/14: {name} obstacle at {distance:.1f}cm "
                        f"(emergency threshold: {self._emergency_distance_cm}cm). "
                        f"Movement blocked."
                    )
                    self._log_safety_event(
                        "obstacle_emergency", "Art. 12, 14", reason, "blocked",
                    )
                    return reason

            # Warning distance — cap speed
            elif distance < self._warning_distance_cm:
                if max_speed > self._max_speed_near_obstacle:
                    reason = (
                        f"Art. 12/14: {name} obstacle at {distance:.1f}cm "
                        f"(warning zone: {self._warning_distance_cm}cm). "
                        f"Speed {max_speed} exceeds max-near-obstacle "
                        f"({self._max_speed_near_obstacle})."
                    )
                    self._log_safety_event(
                        "speed_limited", "Art. 12, 14", reason, "blocked",
                    )
                    return reason

        return None

    def _check_tilt(self, state: SensorState) -> Optional[str]:
        """
        Check if the robot is tilting dangerously.

        Art. 14: Fail-safe — excessive tilt means possible fall.

        Returns:
            Rejection reason or None.
        """
        tilt = self._calculate_tilt(state)
        if tilt is not None and tilt > self._max_tilt_degrees:
            reason = (
                f"Art. 14: Tilt at {tilt:.1f} degrees exceeds maximum "
                f"({self._max_tilt_degrees} degrees). Movement blocked."
            )
            self._log_safety_event("tilt_danger", "Art. 14", reason, "blocked")
            return reason
        return None

    def _check_battery(self, state: SensorState) -> Optional[str]:
        """
        Check battery voltage against minimum threshold.

        Art. 14: Fail-safe — low battery risks uncontrolled shutdown.

        Returns:
            Rejection reason or None.
        """
        if state.battery_voltage is not None:
            if state.battery_voltage < self._min_battery_voltage:
                reason = (
                    f"Art. 14: Battery at {state.battery_voltage:.1f}V "
                    f"below minimum ({self._min_battery_voltage}V). "
                    f"Movement blocked."
                )
                self._log_safety_event(
                    "low_battery", "Art. 14", reason, "blocked",
                )
                return reason
        return None

    def _check_stopping_distance(
        self,
        max_speed: int,
        state: SensorState,
    ) -> Optional[str]:
        """
        Estimate if we can stop in time at the proposed speed.

        Art. 5: Cascading consequences — "If I accelerate now and
        the sensor reads X cm, will I be able to stop in time?"

        Simple model: stopping distance proportional to speed squared.
        At 100% speed, assume ~30cm stopping distance (conservative
        estimate for small robot with TT motors).

        Returns:
            Rejection reason or None.
        """
        # Rough stopping distance model: d = k * (speed/100)^2
        # k = 30cm at full speed (conservative for TT motor robot)
        k = 30.0
        stopping_distance_cm = k * (max_speed / 100.0) ** 2

        for name, distance in state.ultrasonics.items():
            if distance is None:
                continue
            if distance < stopping_distance_cm + self._emergency_distance_cm:
                reason = (
                    f"Art. 5: At speed {max_speed}, estimated stopping distance "
                    f"is {stopping_distance_cm:.1f}cm + {self._emergency_distance_cm}cm buffer. "
                    f"{name} obstacle at {distance:.1f}cm — cannot guarantee safe stop."
                )
                self._log_safety_event(
                    "stopping_distance", "Art. 5", reason, "blocked",
                )
                return reason

        return None

    def _calculate_tilt(self, state: SensorState) -> Optional[float]:
        """
        Calculate tilt angle in degrees from IMU accelerometer data.

        Uses the accelerometer to determine how far the robot is tilted
        from level. When level, accel_z ~= 9.8 and accel_x, accel_y ~= 0.

        Returns:
            Tilt angle in degrees, or None if IMU data unavailable.
        """
        if state.imu is None:
            return None

        ax = state.imu.accel_x
        ay = state.imu.accel_y
        az = state.imu.accel_z

        # Tilt = angle between gravity vector and z-axis
        # When level: ax=0, ay=0, az=9.8 -> tilt=0
        magnitude = math.sqrt(ax * ax + ay * ay + az * az)
        if magnitude < 0.1:
            return None  # No meaningful reading

        # cos(tilt) = az / magnitude
        cos_tilt = az / magnitude
        cos_tilt = max(-1.0, min(1.0, cos_tilt))  # Clamp for acos
        tilt_degrees = math.degrees(math.acos(cos_tilt))

        return round(tilt_degrees, 1)

    def _trigger_e_stop(self, reason: str) -> None:
        """
        Trigger emergency stop via the motor controller.

        This is the hard safety intervention — motors stop immediately.
        """
        if self._motors is not None:
            try:
                self._motors.e_stop()  # type: ignore
            except Exception as e:
                self._logger.log(
                    "CRITICAL", "safety",
                    f"E_STOP call failed: {e}",
                )

        self._log_safety_event("e_stop_triggered", "Art. 14", reason, "e_stop")

    def _log_safety_event(
        self,
        event_type: str,
        article: str,
        details: str,
        action_taken: str,
    ) -> None:
        """Write a safety event to the append-only safety log."""
        self._logger.log_safety(event_type, {
            "article": article,
            "details": details,
            "action_taken": action_taken,
            "timestamp": time.time(),
        })
