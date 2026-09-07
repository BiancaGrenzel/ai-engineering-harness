"""Read-only CLI Tool health checking.

Health observes whether a previously detected Tool responds to a safe,
declarative probe. It never installs, configures, authorizes, persists state,
or evaluates effective risk.

Health composes DetectionResult. It does not reimplement discovery or PATH
resolution.
"""

from __future__ import annotations

import re
import subprocess
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Mapping, Sequence

from harness.tools.detection import DetectionResult, DetectionStatus

# Controlled by the checker, not by Registry metadata.
HEALTH_CHECK_TIMEOUT_SECONDS = 3.0

# Simple flags only: -V, --version, --help, etc. Not a shell argument language.
_HEALTH_ARG_PATTERN = re.compile(r"^-{1,2}[A-Za-z0-9][A-Za-z0-9._-]*$")

# Flags that commonly turn a binary into an arbitrary command interpreter.
_FORBIDDEN_HEALTH_FLAGS = frozenset(
    {
        "-c",
        "-e",
        "-Command",
        "-EncodedCommand",
        "--command",
        "--eval",
        "--execute",
    }
)

_SHELL_METACHAR_PATTERN = re.compile(r"[|&;<>`$(){}[\]\\\"'*?\n\r\t]")

RunFn = Callable[..., subprocess.CompletedProcess[str]]


class HealthStatus(str, Enum):
    """Structured health outcome.

    Status values describe operational observation. They are not Detection
    statuses and do not encode baseline risk or authorization.
    """

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNAVAILABLE = "unavailable"
    UNSUPPORTED = "unsupported"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass(frozen=True)
class HealthResult:
    """Transient runtime observation for one Tool health probe.

    This object is never written back to the Registry or harness configuration.
    """

    tool_id: str
    healthy: bool
    status: HealthStatus
    reason: str | None = None
    duration_ms: float | None = None
    exit_code: int | None = None
    detection_status: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "healthy": self.healthy,
            "status": self.status.value,
            "reason": self.reason,
            "duration_ms": self.duration_ms,
            "exit_code": self.exit_code,
            "detection_status": self.detection_status,
        }


def validate_health_contract(health: Mapping[str, Any] | None) -> str | None:
    """Validate Registry health fields before any process is started.

    Returns an error reason, or ``None`` when the contract is acceptable.
    Callers must treat a missing ``health`` block as unsupported separately;
    this helper expects a present mapping.
    """
    if health is None:
        return "health metadata is missing"
    if not isinstance(health, Mapping):
        return "health metadata must be a mapping"

    # Reject executable / shell surfaces that belong outside this contract.
    forbidden_keys = {
        "command",
        "commands",
        "script",
        "shell",
        "executable",
        "argv",
        "env",
        "cwd",
        "path",
        "install",
        "package",
    }
    for key in forbidden_keys:
        if key in health:
            return f"health metadata must not contain '{key}'"

    kind = health.get("kind")
    if kind is None:
        return "health.kind is required"
    if kind != "cli":
        return f"health supports kind 'cli' only; got {kind!r}"

    arguments = health.get("arguments")
    if arguments is None:
        return "health.arguments is required"
    if not isinstance(arguments, (list, tuple)) or not arguments:
        return "health.arguments must be a non-empty list"
    for arg in arguments:
        if not isinstance(arg, str) or not arg:
            return "health.arguments entries must be non-empty strings"
        if " " in arg or _SHELL_METACHAR_PATTERN.search(arg):
            return "health.arguments contains forbidden characters"
        if not _HEALTH_ARG_PATTERN.fullmatch(arg):
            return "health.arguments must be simple flags only"
        if arg in _FORBIDDEN_HEALTH_FLAGS:
            return f"health.arguments flag is not allowed: {arg}"
    return None


class ToolHealthChecker:
    """Check whether a detected Tool responds to its declared health probe.

    Only ``health.kind: cli`` is supported in this phase. Execution always uses
    a structured argv list with ``shell=False``. The resolved executable path
    comes from ``DetectionResult``; Health never searches PATH itself.
    """

    def __init__(
        self,
        *,
        run: RunFn | None = None,
        timeout_seconds: float = HEALTH_CHECK_TIMEOUT_SECONDS,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self._run = run or self._default_run
        self._timeout_seconds = timeout_seconds

    @staticmethod
    def _default_run(
        args: Sequence[str],
        *,
        timeout: float,
    ) -> subprocess.CompletedProcess[str]:
        # Explicit shell=False — never pass a shell string.
        return subprocess.run(
            list(args),
            shell=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

    def check(
        self,
        tool: Mapping[str, Any],
        detection: DetectionResult,
    ) -> HealthResult:
        """Probe one Tool using a prior DetectionResult. Does not mutate inputs."""
        started = time.perf_counter()
        tool_id = tool.get("id")
        if not isinstance(tool_id, str) or not tool_id:
            return HealthResult(
                tool_id="",
                healthy=False,
                status=HealthStatus.ERROR,
                reason="tool id is required",
                duration_ms=_elapsed_ms(started),
                detection_status=detection.status.value,
            )

        if not detection.detected or detection.path is None:
            return HealthResult(
                tool_id=tool_id,
                healthy=False,
                status=HealthStatus.UNAVAILABLE,
                reason=_unavailable_reason(detection),
                duration_ms=_elapsed_ms(started),
                detection_status=detection.status.value,
            )

        # Incompatible hosts remain Detection concerns; Health still refuses to
        # invent a probe when Detection already classified the host as unsupported.
        if detection.status == DetectionStatus.INCOMPATIBLE:
            return HealthResult(
                tool_id=tool_id,
                healthy=False,
                status=HealthStatus.UNAVAILABLE,
                reason=detection.reason
                or "host platform/architecture is not declared as supported",
                duration_ms=_elapsed_ms(started),
                detection_status=detection.status.value,
            )

        kind = tool.get("kind")
        if kind != "cli":
            return HealthResult(
                tool_id=tool_id,
                healthy=False,
                status=HealthStatus.UNSUPPORTED,
                reason=f"health supports kind 'cli' only; got {kind!r}",
                duration_ms=_elapsed_ms(started),
                detection_status=detection.status.value,
            )

        health = tool.get("health")
        if health is None:
            return HealthResult(
                tool_id=tool_id,
                healthy=False,
                status=HealthStatus.UNSUPPORTED,
                reason="no declarative health probe is declared for this Tool",
                duration_ms=_elapsed_ms(started),
                detection_status=detection.status.value,
            )
        if not isinstance(health, Mapping):
            return HealthResult(
                tool_id=tool_id,
                healthy=False,
                status=HealthStatus.ERROR,
                reason="health metadata must be a mapping",
                duration_ms=_elapsed_ms(started),
                detection_status=detection.status.value,
            )

        contract_error = validate_health_contract(health)
        if contract_error is not None:
            return HealthResult(
                tool_id=tool_id,
                healthy=False,
                status=HealthStatus.ERROR,
                reason=contract_error,
                duration_ms=_elapsed_ms(started),
                detection_status=detection.status.value,
            )

        arguments = health.get("arguments")
        assert isinstance(arguments, (list, tuple))

        # Refuse path-like resolution targets even if DetectionResult is mocked.
        if not isinstance(detection.path, str) or not detection.path:
            return HealthResult(
                tool_id=tool_id,
                healthy=False,
                status=HealthStatus.ERROR,
                reason="detection path is required for health probing",
                duration_ms=_elapsed_ms(started),
                detection_status=detection.status.value,
            )

        argv = [detection.path, *list(arguments)]
        probe_started = time.perf_counter()
        try:
            completed = self._run(argv, timeout=self._timeout_seconds)
        except subprocess.TimeoutExpired:
            return HealthResult(
                tool_id=tool_id,
                healthy=False,
                status=HealthStatus.TIMEOUT,
                reason=f"health probe timed out after {self._timeout_seconds:g}s",
                duration_ms=_elapsed_ms(probe_started),
                detection_status=detection.status.value,
            )
        except OSError as exc:
            return HealthResult(
                tool_id=tool_id,
                healthy=False,
                status=HealthStatus.ERROR,
                reason=f"failed to execute health probe: {exc}",
                duration_ms=_elapsed_ms(probe_started),
                detection_status=detection.status.value,
            )

        duration_ms = _elapsed_ms(probe_started)
        if completed.returncode != 0:
            return HealthResult(
                tool_id=tool_id,
                healthy=False,
                status=HealthStatus.UNHEALTHY,
                reason=f"probe exited with code {completed.returncode}",
                duration_ms=duration_ms,
                exit_code=completed.returncode,
                detection_status=detection.status.value,
            )

        return HealthResult(
            tool_id=tool_id,
            healthy=True,
            status=HealthStatus.HEALTHY,
            reason=None,
            duration_ms=duration_ms,
            exit_code=completed.returncode,
            detection_status=detection.status.value,
        )


def format_health_cli_report(
    *,
    tool_name: str,
    detection: DetectionResult,
    health: HealthResult,
) -> str:
    """Render a human-readable Tool Health report for the CLI."""
    lines = [
        "Tool Health",
        "",
        f"  {tool_name}",
        "",
        f"  Detection: {detection.status.value}",
        f"  Health: {health.status.value}",
    ]
    if detection.version:
        lines.append(f"  Version: {detection.version}")
    if health.duration_ms is not None:
        lines.append(f"  Duration: {health.duration_ms:.0f}ms")
    if health.reason:
        lines.append(f"  Reason: {health.reason}")
    lines.append("")
    return "\n".join(lines)


def _elapsed_ms(started: float) -> float:
    return (time.perf_counter() - started) * 1000.0


def _unavailable_reason(detection: DetectionResult) -> str:
    if detection.reason:
        return detection.reason
    if detection.status == DetectionStatus.NOT_FOUND:
        return "Tool is not detected"
    return f"Tool is not available for health checking (detection: {detection.status.value})"
