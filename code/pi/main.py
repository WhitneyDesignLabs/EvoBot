#!/usr/bin/env python3
"""
EvoBot Main Loop — reference-01

Five-phase execution cycle: SENSE -> THINK -> ACT -> EVALUATE -> LOG

This is the entry point for the EvoBot robot. It loads configuration,
initializes all subsystems, and runs the main decision loop at a
configurable rate (default 10 Hz).

Governed by the Opengates Constitution (SOUL.md).

Usage:
    python3 -u main.py
    python3 -u main.py --config /path/to/robot.yaml
"""

import argparse
import os
import signal
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from evolution import CycleScore, Evaluator
from inference import InferenceEngine
from logger import Logger
from motors import MotorController
from safety import SafetyMonitor
from sensors import SensorHub, SensorState


# ---------- Startup banner ----------

BANNER = r"""
    ______           ____        __
   / ____/  ______  / __ )____  / /_
  / __/ | / / __ \/ __  / __ \/ __/
 / /___| / / /_/ / /_/ / /_/ / /_
/_____/___/\____/_____/\____/\__/

  reference-01  |  Opengates Constitution
  Local-First   |  Self-Evolving
"""


def load_yaml(path: str) -> dict:
    """
    Load a YAML config file.

    Args:
        path: Absolute or relative path to YAML file.

    Returns:
        Parsed dict. Returns empty dict on error.
    """
    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f)
            return data if isinstance(data, dict) else {}
    except Exception as e:
        print(f"[ERROR] Failed to load {path}: {e}", file=sys.stderr)
        return {}


def find_config_dir() -> Path:
    """
    Locate the configs/ directory.

    Searches relative to this script's location, then common deployment paths.

    Returns:
        Path to configs/ directory.
    """
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir / "configs",
        script_dir.parent / "configs",
        Path.home() / "evobot" / "configs",
    ]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate

    # Fallback: use script directory
    return script_dir / "configs"


class EvoBot:
    """
    Main robot controller.

    Manages the five-phase execution loop and coordinates all subsystems.
    Handles graceful startup, shutdown, and error recovery.
    """

    def __init__(self, robot_config: dict, inference_config: dict) -> None:
        """
        Initialize EvoBot from parsed config dicts.

        Args:
            robot_config: Parsed robot.yaml
            inference_config: Parsed inference.yaml
        """
        self._robot_config = robot_config
        self._inference_config = inference_config
        self._running = False
        self._shutdown_requested = False

        # Extract config sections
        self._loop_config = robot_config.get("loop", {})
        self._serial_config = robot_config.get("serial", {})
        # Merge motor config into serial config so MotorController has access
        self._serial_config["motors"] = robot_config.get("motors", {})
        self._sensor_config = robot_config.get("sensors", {})
        self._safety_config = robot_config.get("safety", {})
        self._evolution_config = robot_config.get("evolution", {})
        self._logging_config = robot_config.get("logging", {})

        # Loop timing
        self._target_hz = self._loop_config.get("target_hz", 10)
        self._cycle_period = 1.0 / self._target_hz
        self._heartbeat_interval_s = self._loop_config.get("heartbeat_interval_ms", 250) / 1000.0

        # Initialize subsystems (order matters)
        self._logger = Logger(self._logging_config)
        self._motors = MotorController(self._serial_config, self._logger)
        self._sensors = SensorHub(self._sensor_config, self._logger)
        self._safety = SafetyMonitor(self._safety_config, self._logger, self._motors)
        self._inference = InferenceEngine(self._inference_config, self._logger)
        self._evaluator = Evaluator(self._evolution_config, self._logger)

        # Wire safety module to motors for e_stop capability
        self._safety.set_motors(self._motors)

        # Cycle state
        self._cycle_count = 0
        self._last_heartbeat_time = 0.0
        self._last_sensor_state: Optional[SensorState] = None
        self._last_action: Dict[str, Any] = {"type": "stop", "left": 0, "right": 0}

    def startup(self) -> bool:
        """
        Run the startup sequence.

        1. Print banner
        2. Log session start
        3. Initialize serial to ESP32
        4. Initialize sensors
        5. Run self-test
        6. Report ready status

        Returns:
            True if startup succeeded, False if critical failure.
        """
        # Print banner
        robot_name = self._robot_config.get("robot", {}).get("name", "evobot")
        robot_version = self._robot_config.get("robot", {}).get("version", "0.0.0")
        print(BANNER, file=sys.stderr)
        print(f"  Robot: {robot_name} v{robot_version}", file=sys.stderr)
        print(f"  Loop rate: {self._target_hz} Hz", file=sys.stderr)
        print(f"  Serial: {self._serial_config.get('port', 'N/A')} "
              f"@ {self._serial_config.get('baud', 'N/A')}", file=sys.stderr)
        print(f"  Log session: {self._logger.get_session_path()}", file=sys.stderr)
        print("", file=sys.stderr)

        self._logger.log(
            "INFO", "main",
            f"EvoBot {robot_name} v{robot_version} starting",
            {"config": {
                "target_hz": self._target_hz,
                "serial_port": self._serial_config.get("port"),
                "safety_emergency_cm": self._safety_config.get("emergency_stop_distance_cm"),
            }},
        )

        # Initialize serial connection to ESP32
        self._logger.log("INFO", "main", "Connecting to ESP32 motor controller...")
        serial_ok = self._motors.connect()
        if not serial_ok:
            self._logger.log(
                "WARN", "main",
                "ESP32 connection failed — running without motor control",
            )
            # Non-fatal: robot can still sense and think without motors

        # Initialize sensors
        self._logger.log("INFO", "main", "Initializing sensors...")
        sensor_results = self._sensors.init()

        # Run sensor self-test
        self._logger.log("INFO", "main", "Running sensor self-test...")
        test_results = self._sensors.self_test()
        self._logger.log(
            "INFO", "main",
            f"Self-test complete: {test_results}",
            test_results,
        )

        # Log available inference backends
        backends = self._inference.get_available_backends()
        self._logger.log(
            "INFO", "main",
            f"Inference backends available: {backends}",
        )

        self._logger.log("INFO", "main", "Startup complete — entering main loop")
        return True

    def run(self) -> None:
        """
        Run the main five-phase loop until shutdown is requested.

        Each cycle: SENSE -> THINK -> ACT -> EVALUATE -> LOG
        Runs at the configured target Hz with timing compensation.
        """
        self._running = True

        while self._running and not self._shutdown_requested:
            cycle_start = time.time()
            self._cycle_count += 1

            try:
                # ===== PHASE 1: SENSE =====
                sensor_state = self._phase_sense()

                # ===== PHASE 2: THINK =====
                action = self._phase_think(sensor_state)

                # ===== PHASE 3: ACT =====
                self._phase_act(action, sensor_state)

                # ===== PHASE 4: EVALUATE =====
                score = self._phase_evaluate(sensor_state, action)

                # ===== PHASE 5: LOG =====
                cycle_duration_ms = (time.time() - cycle_start) * 1000
                self._phase_log(sensor_state, action, score, cycle_duration_ms)

                # Store state for next cycle comparison
                self._last_sensor_state = sensor_state
                self._last_action = action

            except Exception as e:
                # Catch-all: robot doesn't crash on one bad cycle
                self._logger.log(
                    "ERROR", "main",
                    f"Cycle {self._cycle_count} exception: {e}",
                    {"cycle": self._cycle_count, "error": str(e)},
                )
                # After exception, try to stop motors as a safety measure
                try:
                    self._motors.stop()
                except Exception:
                    pass

            # Send heartbeat at configured interval
            now = time.time()
            if now - self._last_heartbeat_time >= self._heartbeat_interval_s:
                try:
                    self._motors.heartbeat()
                    self._last_heartbeat_time = now
                except Exception:
                    pass

            # Sleep to maintain target loop rate
            elapsed = time.time() - cycle_start
            sleep_time = self._cycle_period - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    def shutdown(self) -> None:
        """
        Graceful shutdown sequence.

        1. Stop the main loop
        2. Send STOP to ESP32
        3. Close serial connection
        4. Release sensor resources
        5. Flush and close logs
        """
        self._logger.log("INFO", "main", "Shutdown requested")
        self._running = False
        self._shutdown_requested = True

        # Stop motors
        try:
            self._motors.stop()
            time.sleep(0.1)
            self._motors.close()
        except Exception as e:
            self._logger.log("WARN", "main", f"Motor shutdown error: {e}")

        # Release sensors
        try:
            self._sensors.cleanup()
        except Exception as e:
            self._logger.log("WARN", "main", f"Sensor cleanup error: {e}")

        # Log final session stats
        stats = self._evaluator.get_session_stats()
        self._logger.log(
            "INFO", "main",
            f"Session complete: {self._cycle_count} cycles",
            stats,
        )

        # Flush and close logs
        self._logger.flush()
        self._logger.close()

        print(f"\nEvoBot shut down after {self._cycle_count} cycles.", file=sys.stderr)

    # ===== Main loop phases =====

    def _phase_sense(self) -> SensorState:
        """
        SENSE phase: Read all sensors and encoder data.

        Returns:
            SensorState with current readings.
        """
        # Get encoder data from ESP32
        encoder_data = self._motors.get_encoders()

        # Read all sensors (ultrasonics, IMU, camera)
        sensor_state = self._sensors.read_all(encoder_data=encoder_data)

        return sensor_state

    def _phase_think(self, sensor_state: SensorState) -> dict:
        """
        THINK phase: Evaluate sensor data and decide next action.

        Checks for immediate dangers first (safety pre-check).
        For simple situations, uses local heuristics.
        For complex situations, calls inference backend.

        Args:
            sensor_state: Current sensor readings.

        Returns:
            Action dict: {"type": "set_speed"|"stop"|"e_stop", "left": int, "right": int}
        """
        # Safety pre-check: any immediate dangers?
        safety_conditions = self._safety.check_continuous(sensor_state)
        if safety_conditions:
            # Danger detected — the safety monitor may have already e-stopped
            for condition in safety_conditions:
                if "EMERGENCY" in condition:
                    return {"type": "e_stop", "left": 0, "right": 0}
            # Non-emergency safety condition — stop
            return {"type": "stop", "left": 0, "right": 0}

        # Assess situation from sensors
        action = self._decide_action(sensor_state)

        return action

    def _phase_act(self, action: dict, sensor_state: SensorState) -> None:
        """
        ACT phase: Validate and execute the decided action.

        Safety validation runs BEFORE any command is sent to the ESP32.

        Args:
            action: Decided action dict.
            sensor_state: Current sensor state for validation context.
        """
        action_type = action.get("type", "stop")

        if action_type == "e_stop":
            self._motors.e_stop()
            return

        if action_type == "stop":
            self._motors.stop()
            return

        if action_type == "set_speed":
            # Safety validation gate
            approved, reason = self._safety.check_action(action, sensor_state)

            if approved:
                self._motors.send_speed(action.get("left", 0), action.get("right", 0))
            else:
                # Safety rejected — substitute safe command
                self._logger.log(
                    "SAFETY", "main",
                    f"Action blocked by safety: {reason}",
                    {"action": action, "reason": reason},
                )
                self._motors.stop()

    def _phase_evaluate(
        self,
        sensor_state: SensorState,
        action: dict,
    ) -> CycleScore:
        """
        EVALUATE phase: Score this cycle's performance.

        Args:
            sensor_state: Sensor readings from this cycle.
            action: Action taken this cycle.

        Returns:
            CycleScore for this cycle.
        """
        # Build simplified sensor summaries for evaluation
        sensor_summary = {
            "ultrasonics": sensor_state.ultrasonics,
        }
        prev_summary = None
        if self._last_sensor_state is not None:
            prev_summary = {
                "ultrasonics": self._last_sensor_state.ultrasonics,
            }

        # Get safety conditions (re-check for evaluation)
        safety_conditions = self._safety.check_continuous(sensor_state)

        score = self._evaluator.score_cycle(
            sensor_before=prev_summary,
            action_taken=action,
            sensor_after=sensor_summary,
            safety_events=safety_conditions,
        )

        # Check if it is time to propose an improvement
        if self._evaluator.should_propose():
            stats = self._evaluator.get_session_stats()
            proposal = self._evaluator.propose_improvement(stats)
            if proposal is not None:
                self._logger.log(
                    "INFO", "main",
                    f"Evolution proposal generated: {proposal.target}",
                )

        return score

    def _phase_log(
        self,
        sensor_state: SensorState,
        action: dict,
        score: CycleScore,
        cycle_duration_ms: float,
    ) -> None:
        """
        LOG phase: Write structured cycle record.

        Args:
            sensor_state: This cycle's sensor data.
            action: Action taken.
            score: Evaluation score.
            cycle_duration_ms: Total cycle time in milliseconds.
        """
        self._logger.log_cycle({
            "cycle": self._cycle_count,
            "duration_ms": round(cycle_duration_ms, 2),
            "ultrasonics": sensor_state.ultrasonics,
            "imu": {
                "accel_x": sensor_state.imu.accel_x,
                "accel_y": sensor_state.imu.accel_y,
                "accel_z": sensor_state.imu.accel_z,
            } if sensor_state.imu else None,
            "encoders": {
                "left": sensor_state.encoders.left_ticks,
                "right": sensor_state.encoders.right_ticks,
            } if sensor_state.encoders else None,
            "action": action,
            "score": score.to_dict(),
        })

    # ===== Decision logic =====

    def _decide_action(self, sensor_state: SensorState) -> dict:
        """
        Decide what action to take based on current sensor data.

        Uses local heuristics for simple obstacle avoidance.
        Falls through to inference engine for complex situations.

        Args:
            sensor_state: Current sensor readings.

        Returns:
            Action dict.
        """
        us = sensor_state.ultrasonics

        # Get distances (None means sensor unavailable)
        left_dist = us.get("left")
        right_dist = us.get("right")

        # If no ultrasonic data at all, stop (Art. 14: fail-safe)
        if left_dist is None and right_dist is None:
            return {"type": "stop", "left": 0, "right": 0}

        # Default safe distances for missing sensors
        if left_dist is None:
            left_dist = 999.0
        if right_dist is None:
            right_dist = 999.0

        # Calculate minimum distance to any obstacle
        min_dist = min(left_dist, right_dist)

        # --- Simple heuristic navigation ---

        # Emergency zone — should be caught by safety monitor, but belt-and-suspenders
        if min_dist < self._safety_config.get("emergency_stop_distance_cm", 15):
            return {"type": "stop", "left": 0, "right": 0}

        # Warning zone — slow down and turn
        warning_dist = self._safety_config.get("warning_distance_cm", 40)
        max_near = self._safety_config.get("max_speed_near_obstacle", 30)

        if min_dist < warning_dist:
            # Turn toward the side with more clearance
            if left_dist > right_dist:
                # More room on left — turn left (slow left motor, faster right)
                return {
                    "type": "set_speed",
                    "left": max_near // 3,
                    "right": max_near,
                }
            else:
                # More room on right — turn right
                return {
                    "type": "set_speed",
                    "left": max_near,
                    "right": max_near // 3,
                }

        # Clear path — drive forward at moderate speed
        cruise_speed = 40
        return {
            "type": "set_speed",
            "left": cruise_speed,
            "right": cruise_speed,
        }


# ---------- Signal handling ----------


_bot_instance: Optional[EvoBot] = None


def _signal_handler(signum: int, frame: Any) -> None:
    """Handle SIGINT/SIGTERM for graceful shutdown."""
    sig_name = signal.Signals(signum).name
    print(f"\n[{sig_name}] Shutdown signal received", file=sys.stderr)
    if _bot_instance is not None:
        _bot_instance.shutdown()
    sys.exit(0)


# ---------- Entry point ----------


def main() -> None:
    """
    EvoBot entry point.

    Parses arguments, loads config, initializes the robot, and enters
    the main loop. Handles graceful shutdown on SIGINT/SIGTERM.
    """
    global _bot_instance

    parser = argparse.ArgumentParser(description="EvoBot reference-01")
    parser.add_argument(
        "--config-dir",
        type=str,
        default=None,
        help="Path to configs/ directory (default: auto-detect)",
    )
    args = parser.parse_args()

    # Find configuration directory
    if args.config_dir:
        config_dir = Path(args.config_dir)
    else:
        config_dir = find_config_dir()

    # Load configuration files
    robot_yaml = config_dir / "robot.yaml"
    inference_yaml = config_dir / "inference.yaml"

    print(f"Loading config from: {config_dir}", file=sys.stderr)

    robot_config = load_yaml(str(robot_yaml))
    inference_config = load_yaml(str(inference_yaml))

    if not robot_config:
        print(f"[FATAL] Could not load {robot_yaml}", file=sys.stderr)
        sys.exit(1)

    if not inference_config:
        print(f"[WARN] Could not load {inference_yaml} — inference disabled",
              file=sys.stderr)

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    # Create and start the robot
    bot = EvoBot(robot_config, inference_config)
    _bot_instance = bot

    try:
        if bot.startup():
            bot.run()
    except KeyboardInterrupt:
        pass
    finally:
        bot.shutdown()


if __name__ == "__main__":
    main()
