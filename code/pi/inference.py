"""
EvoBot Inference Interface — Abstracted backend routing

Provides a single API for all inference calls. The caller never knows
or cares whether the response came from Ollama, Claude, or a cached
heuristic. Backend selection is driven by configuration and runtime
availability.

Complexity levels:
    "routine"    — obstacle avoidance, simple navigation (prefers Ollama)
    "analytical" — sensor interpretation, pattern recognition (Ollama or Claude)
    "complex"    — self-evaluation, evolution proposals (prefers Claude API)

Fallback chain: primary backend -> secondary -> cached heuristic response.
No special SDKs required — uses only the 'requests' library for HTTP calls.
"""

import json
import os
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

try:
    import requests
except ImportError:
    requests = None  # type: ignore

from logger import Logger


@dataclass
class BackendStats:
    """Tracks call counts, latencies, and errors for a single backend."""
    calls: int = 0
    successes: int = 0
    failures: int = 0
    total_latency_ms: float = 0.0
    last_error: Optional[str] = None
    last_call_time: float = 0.0


@dataclass
class RateLimiter:
    """Simple sliding-window rate limiter."""
    max_per_minute: int = 30
    max_per_session: Optional[int] = None
    _timestamps: deque = field(default_factory=deque)
    _session_count: int = 0

    def allow(self) -> bool:
        """Check if a call is allowed under rate limits."""
        now = time.time()

        # Purge timestamps older than 60 seconds
        while self._timestamps and (now - self._timestamps[0]) > 60.0:
            self._timestamps.popleft()

        # Check per-minute limit
        if len(self._timestamps) >= self.max_per_minute:
            return False

        # Check per-session limit
        if self.max_per_session is not None and self._session_count >= self.max_per_session:
            return False

        return True

    def record(self) -> None:
        """Record that a call was made."""
        self._timestamps.append(time.time())
        self._session_count += 1


# ---------- Heuristic fallback responses ----------

_HEURISTIC_RESPONSES = {
    "obstacle_ahead": "Obstacle detected ahead. Reduce speed and turn toward the side with more clearance.",
    "obstacle_all_sides": "Obstacles detected on all sides. Stop. Wait briefly, then try slow reverse.",
    "clear_path": "Path clear. Continue forward at current speed.",
    "low_battery": "Battery low. Reduce speed to minimum. Stop non-essential operations. Halt if voltage drops further.",
    "no_sensor_data": "Sensor data unavailable. Stop immediately. Wait for sensor recovery.",
    "unknown": "Situation unclear. Stop and wait. Log state for later analysis.",
    "tilt_warning": "Excessive tilt detected. Stop immediately. Possible fall risk.",
    "default": "No specific heuristic applies. Maintain current behavior. Proceed with caution.",
}


def _match_heuristic(prompt: str) -> str:
    """
    Match a prompt to the best cached heuristic response.

    This is the fallback of last resort — deliberately conservative.
    Keeps the robot safe but not smart.
    """
    prompt_lower = prompt.lower()

    if "no sensor" in prompt_lower or "sensor unavailable" in prompt_lower:
        return _HEURISTIC_RESPONSES["no_sensor_data"]
    if "battery" in prompt_lower and ("low" in prompt_lower or "critical" in prompt_lower):
        return _HEURISTIC_RESPONSES["low_battery"]
    if "tilt" in prompt_lower or "falling" in prompt_lower:
        return _HEURISTIC_RESPONSES["tilt_warning"]
    if "obstacle" in prompt_lower and "all" in prompt_lower:
        return _HEURISTIC_RESPONSES["obstacle_all_sides"]
    if "obstacle" in prompt_lower:
        return _HEURISTIC_RESPONSES["obstacle_ahead"]
    if "clear" in prompt_lower:
        return _HEURISTIC_RESPONSES["clear_path"]

    return _HEURISTIC_RESPONSES["default"]


# ---------- Backend caller functions ----------


def _call_ollama(
    url: str,
    model: str,
    prompt: str,
    timeout_s: float,
) -> Optional[str]:
    """
    Call Ollama HTTP API and return the generated text.

    Ollama API: POST /api/generate
    Body: {"model": "...", "prompt": "...", "stream": false}

    Returns:
        Response text or None on failure.
    """
    if requests is None:
        return None

    endpoint = f"{url.rstrip('/')}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }

    try:
        resp = requests.post(endpoint, json=payload, timeout=timeout_s)
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "").strip()
    except Exception:
        return None


def _call_claude(
    model: str,
    prompt: str,
    api_key: str,
    timeout_s: float,
) -> Optional[str]:
    """
    Call the Anthropic Messages API and return the generated text.

    API: POST https://api.anthropic.com/v1/messages
    Headers: x-api-key, anthropic-version, content-type

    Returns:
        Response text or None on failure.
    """
    if requests is None:
        return None

    endpoint = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": model,
        "max_tokens": 1024,
        "messages": [
            {"role": "user", "content": prompt},
        ],
    }

    try:
        resp = requests.post(
            endpoint, headers=headers, json=payload, timeout=timeout_s,
        )
        resp.raise_for_status()
        data = resp.json()
        # Anthropic Messages API returns content as a list of blocks
        content = data.get("content", [])
        if content and isinstance(content, list):
            return content[0].get("text", "").strip()
        return None
    except Exception:
        return None


# ---------- Main inference engine ----------


class InferenceEngine:
    """
    Abstracted inference interface for EvoBot.

    Routes queries to the best available backend based on complexity level
    and runtime availability. Implements the fallback chain:
    primary -> secondary -> cached heuristic.

    The robot's logic never knows or cares where the answer came from.
    Backend selection is configuration, not code.
    """

    def __init__(self, config: dict, logger: Logger) -> None:
        """
        Initialize the inference engine from inference.yaml config.

        Args:
            config: Full parsed inference.yaml dict
            logger: Logger instance
        """
        self._logger = logger
        self._backends_config = config.get("backends", {})
        self._routing = config.get("routing", {})
        self._fallback_config = config.get("fallback", {})
        self._rate_limit_config = config.get("rate_limits", {})

        # Backend availability flags
        self._backend_available: Dict[str, bool] = {}
        self._backend_stats: Dict[str, BackendStats] = {}
        self._rate_limiters: Dict[str, RateLimiter] = {}
        self._last_probe_time: Dict[str, float] = {}

        # Claude API key from environment
        self._claude_api_key = os.environ.get("ANTHROPIC_API_KEY", "")

        # Max retries per backend
        self._max_retries = self._fallback_config.get("max_retries_per_backend", 2)
        self._retry_delay_s = self._fallback_config.get("retry_delay_ms", 500) / 1000.0
        self._probe_interval_s = 30.0  # Re-check unavailable backends every 30s

        # Initialize each backend
        for name, bcfg in self._backends_config.items():
            if not bcfg.get("enabled", True):
                self._backend_available[name] = False
                continue

            self._backend_available[name] = True
            self._backend_stats[name] = BackendStats()
            self._last_probe_time[name] = 0.0

            # Rate limiter
            rl_cfg = self._rate_limit_config.get(name, {})
            self._rate_limiters[name] = RateLimiter(
                max_per_minute=rl_cfg.get("max_calls_per_minute", 60),
                max_per_session=rl_cfg.get("max_calls_per_session"),
            )

        self._logger.log(
            "INFO", "inference",
            f"Inference engine initialized. Backends: "
            f"{list(self._backends_config.keys())}",
        )

    def query(
        self,
        prompt: str,
        complexity: str = "routine",
        context: Optional[str] = None,
    ) -> str:
        """
        Send a prompt to the best available inference backend.

        The backend is selected based on the complexity level and the
        routing rules in inference.yaml. If the preferred backend fails,
        the engine falls through to the next in the priority list. If all
        backends fail, a cached heuristic response is returned.

        Args:
            prompt: The question or situation description.
            complexity: Complexity hint — "routine", "analytical", or "complex".
            context: Optional additional context to prepend to the prompt.

        Returns:
            Response text string (always returns something — never None).
        """
        if context:
            full_prompt = f"Context:\n{context}\n\nQuery:\n{prompt}"
        else:
            full_prompt = prompt

        # Get the priority list for this complexity level
        route = self._routing.get(complexity, self._routing.get("routine", {}))
        priority = route.get("priority", ["cached_heuristics"])

        # Try backends in priority order
        for backend_name in priority:
            if backend_name == "cached_heuristics":
                # Heuristic is always the last resort — handle below
                continue

            if not self._backend_available.get(backend_name, False):
                # Check if it is time to probe this backend again
                if time.time() - self._last_probe_time.get(backend_name, 0) < self._probe_interval_s:
                    continue
                # Probe it
                self._last_probe_time[backend_name] = time.time()
                self._logger.log(
                    "INFO", "inference",
                    f"Probing unavailable backend '{backend_name}'",
                )

            # Rate limit check
            limiter = self._rate_limiters.get(backend_name)
            if limiter and not limiter.allow():
                self._logger.log(
                    "WARN", "inference",
                    f"Rate limit reached for '{backend_name}', skipping",
                )
                continue

            # Try calling the backend
            response = self._try_backend(backend_name, full_prompt, complexity)
            if response is not None:
                return response

        # All backends failed — fall back to heuristic
        self._logger.log(
            "WARN", "inference",
            "All backends failed, using cached heuristic",
            {"complexity": complexity},
        )
        return _match_heuristic(prompt)

    def get_available_backends(self) -> List[str]:
        """Return list of currently reachable backend names."""
        return [
            name for name, available in self._backend_available.items()
            if available
        ]

    def get_backend_stats(self) -> Dict[str, dict]:
        """
        Return call counts, latencies, and error rates per backend.

        Returns:
            Dict mapping backend name to stats dict.
        """
        result = {}
        for name, stats in self._backend_stats.items():
            avg_latency = (
                stats.total_latency_ms / stats.calls if stats.calls > 0 else 0.0
            )
            result[name] = {
                "calls": stats.calls,
                "successes": stats.successes,
                "failures": stats.failures,
                "avg_latency_ms": round(avg_latency, 1),
                "available": self._backend_available.get(name, False),
                "last_error": stats.last_error,
            }
        return result

    # --- Private methods ---

    def _try_backend(
        self,
        name: str,
        prompt: str,
        complexity: str,
    ) -> Optional[str]:
        """
        Attempt to call a specific backend with retries.

        Args:
            name: Backend name from config.
            prompt: Full prompt text.
            complexity: Complexity level (used to select model variant).

        Returns:
            Response text or None if all retries failed.
        """
        bcfg = self._backends_config.get(name, {})
        backend_type = bcfg.get("type", "")
        stats = self._backend_stats.get(name, BackendStats())
        timeout_s = bcfg.get("timeout_ms", 5000) / 1000.0

        for attempt in range(self._max_retries):
            start = time.time()

            try:
                response = None

                if backend_type == "ollama":
                    url = bcfg.get("url", "http://localhost:11434")
                    # Use complex model if available and complexity warrants it
                    if complexity in ("analytical", "complex"):
                        model = bcfg.get("model_complex", bcfg.get("model", "llama3.2:3b"))
                    else:
                        model = bcfg.get("model", "llama3.2:3b")
                    response = _call_ollama(url, model, prompt, timeout_s)

                elif backend_type == "anthropic":
                    if not self._claude_api_key:
                        self._logger.log(
                            "WARN", "inference",
                            "Claude API key not set (ANTHROPIC_API_KEY env var)",
                        )
                        self._backend_available[name] = False
                        return None
                    model = bcfg.get("model", "claude-sonnet-4-20250514")
                    response = _call_claude(
                        model, prompt, self._claude_api_key, timeout_s,
                    )

                elapsed_ms = (time.time() - start) * 1000

                if response is not None and response.strip():
                    # Success
                    stats.calls += 1
                    stats.successes += 1
                    stats.total_latency_ms += elapsed_ms
                    stats.last_call_time = time.time()
                    self._backend_available[name] = True

                    # Record rate limit
                    limiter = self._rate_limiters.get(name)
                    if limiter:
                        limiter.record()

                    self._logger.log(
                        "INFO", "inference",
                        f"Backend '{name}' responded in {elapsed_ms:.0f}ms",
                        {"backend": name, "latency_ms": round(elapsed_ms, 1), "complexity": complexity},
                    )
                    return response

                # Got empty/None response
                stats.calls += 1
                stats.failures += 1
                stats.last_error = "empty_response"

            except Exception as e:
                elapsed_ms = (time.time() - start) * 1000
                stats.calls += 1
                stats.failures += 1
                stats.last_error = str(e)
                self._logger.log(
                    "WARN", "inference",
                    f"Backend '{name}' attempt {attempt + 1} failed: {e}",
                )

            # Wait before retry (except on last attempt)
            if attempt < self._max_retries - 1:
                time.sleep(self._retry_delay_s)

        # All retries exhausted
        self._backend_available[name] = False
        self._logger.log(
            "WARN", "inference",
            f"Backend '{name}' marked unavailable after {self._max_retries} failures",
        )
        return None
