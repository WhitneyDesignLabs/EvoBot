"""
EvoBot Structured Logging System

JSON-lines format logging with separate files for operational, safety, and
evolution data. Implements Constitution Article 17: all decisions logged with
reasoning. Safety log is append-only and never deleted by software.

Log levels: DEBUG, INFO, ACTION, SAFETY, EVOLUTION
"""

import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


# Custom log levels ordered by severity
LOG_LEVELS = {
    "DEBUG": 10,
    "INFO": 20,
    "ACTION": 30,
    "SAFETY": 40,
    "EVOLUTION": 50,
    "WARN": 60,
    "ERROR": 70,
    "CRITICAL": 80,
}


@dataclass
class LogEntry:
    """A single structured log entry."""
    ts: float
    level: str
    module: str
    msg: str
    data: Optional[dict] = None

    def to_dict(self) -> dict:
        d = {"ts": self.ts, "level": self.level, "module": self.module, "msg": self.msg}
        if self.data is not None:
            d["data"] = self.data
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)


class Logger:
    """
    Structured logger for EvoBot.

    Writes JSON-lines to session log files. Maintains a separate append-only
    safety log that is never truncated or deleted by software (Constitution
    Article 17). Evolution proposals get their own log file.

    Console output shows a simplified human-readable format.
    File output contains full JSON detail.
    """

    def __init__(self, config: dict) -> None:
        self._level_threshold = LOG_LEVELS.get(
            config.get("level", "INFO").upper(), 20
        )
        self._log_cycles = config.get("log_cycles", True)

        # Resolve log directory relative to home
        log_dir_raw = config.get("log_dir", "logs/")
        if log_dir_raw.startswith("~/") or log_dir_raw.startswith("/"):
            self._log_dir = Path(os.path.expanduser(log_dir_raw))
        else:
            # Relative to ~/evobot/
            self._log_dir = Path(os.path.expanduser("~/evobot")) / log_dir_raw

        self._log_dir.mkdir(parents=True, exist_ok=True)

        # Session log — one per run
        session_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._session_path = self._log_dir / f"session_{session_ts}.jsonl"
        self._session_file = open(self._session_path, "a", encoding="utf-8")

        # Safety log — append-only, never rotated by software
        safety_log_path = config.get("safety_log", "logs/safety.jsonl")
        if safety_log_path.startswith("~/") or safety_log_path.startswith("/"):
            self._safety_path = Path(os.path.expanduser(safety_log_path))
        else:
            self._safety_path = Path(os.path.expanduser("~/evobot")) / safety_log_path
        self._safety_path.parent.mkdir(parents=True, exist_ok=True)
        self._safety_file = open(self._safety_path, "a", encoding="utf-8")

        # Evolution log — one per session
        self._evolution_path = self._log_dir / f"evolution_{session_ts}.jsonl"
        self._evolution_file: Optional[Any] = None  # Opened lazily

        self._console_enabled = True

    def log(
        self,
        level: str,
        module: str,
        message: str,
        data: Optional[dict] = None,
    ) -> None:
        """
        Write a structured log entry.

        Args:
            level: Log level string (DEBUG, INFO, ACTION, SAFETY, etc.)
            module: Source module name (e.g. 'motors', 'sensors', 'safety')
            message: Human-readable message
            data: Optional dict of structured data
        """
        level_upper = level.upper()
        if LOG_LEVELS.get(level_upper, 0) < self._level_threshold:
            return

        entry = LogEntry(
            ts=time.time(),
            level=level_upper,
            module=module,
            msg=message,
            data=data,
        )

        # Write to session log file
        try:
            self._session_file.write(entry.to_json() + "\n")
        except Exception:
            pass  # Never crash on log failure

        # Console output (simplified)
        if self._console_enabled:
            self._console_write(entry)

    def log_cycle(self, cycle_data: dict) -> None:
        """
        Write a complete main-loop cycle record.

        Args:
            cycle_data: Dict containing sensor state, decision, action, score
        """
        if not self._log_cycles:
            return
        entry = LogEntry(
            ts=time.time(),
            level="INFO",
            module="cycle",
            msg="cycle_record",
            data=cycle_data,
        )
        try:
            self._session_file.write(entry.to_json() + "\n")
        except Exception:
            pass

    def log_safety(self, event_type: str, details: dict) -> None:
        """
        Write to the append-only safety log.

        Per Constitution Article 17, safety events are recorded in a separate
        log that is never truncated or deleted by software.

        Args:
            event_type: Category of safety event (e.g. 'e_stop', 'violation')
            details: Full event details
        """
        entry = LogEntry(
            ts=time.time(),
            level="SAFETY",
            module="safety",
            msg=event_type,
            data=details,
        )
        json_line = entry.to_json() + "\n"
        try:
            self._safety_file.write(json_line)
            self._safety_file.flush()  # Safety log always flushed immediately
        except Exception:
            pass

        # Also write to session log
        try:
            self._session_file.write(json_line)
        except Exception:
            pass

        if self._console_enabled:
            self._console_write(entry)

    def log_evolution(self, proposal: dict) -> None:
        """
        Write an evolution proposal or outcome to the evolution log.

        Args:
            proposal: Dict describing the evolution proposal and/or result
        """
        if self._evolution_file is None:
            self._evolution_file = open(
                self._evolution_path, "a", encoding="utf-8"
            )

        entry = LogEntry(
            ts=time.time(),
            level="EVOLUTION",
            module="evolution",
            msg="evolution_proposal",
            data=proposal,
        )
        json_line = entry.to_json() + "\n"
        try:
            self._evolution_file.write(json_line)
            self._evolution_file.flush()
        except Exception:
            pass

        # Also to session log
        try:
            self._session_file.write(json_line)
        except Exception:
            pass

        if self._console_enabled:
            self._console_write(entry)

    def flush(self) -> None:
        """Force write all buffers to disk."""
        try:
            self._session_file.flush()
        except Exception:
            pass
        try:
            self._safety_file.flush()
        except Exception:
            pass
        if self._evolution_file is not None:
            try:
                self._evolution_file.flush()
            except Exception:
                pass

    def get_session_path(self) -> str:
        """Return the path to the current session log file."""
        return str(self._session_path)

    def close(self) -> None:
        """Close all log files gracefully."""
        self.flush()
        for f in (self._session_file, self._safety_file, self._evolution_file):
            if f is not None:
                try:
                    f.close()
                except Exception:
                    pass

    def _console_write(self, entry: LogEntry) -> None:
        """Write a simplified line to stderr for console display."""
        ts_str = datetime.fromtimestamp(entry.ts).strftime("%H:%M:%S.%f")[:-3]
        level_pad = entry.level.ljust(9)
        mod_pad = entry.module.ljust(10)

        # Color codes for terminal readability
        color = ""
        reset = ""
        if sys.stderr.isatty():
            colors = {
                "DEBUG": "\033[37m",      # white
                "INFO": "\033[36m",       # cyan
                "ACTION": "\033[32m",     # green
                "SAFETY": "\033[91m",     # bright red
                "EVOLUTION": "\033[35m",  # magenta
                "WARN": "\033[33m",       # yellow
                "ERROR": "\033[31m",      # red
                "CRITICAL": "\033[41m",   # red background
            }
            color = colors.get(entry.level, "")
            reset = "\033[0m"

        line = f"{color}[{ts_str}] {level_pad} {mod_pad} {entry.msg}{reset}"
        try:
            print(line, file=sys.stderr)
        except Exception:
            pass
