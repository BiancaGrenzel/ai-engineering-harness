"""Read-only CLI Tool detection.

Detection observes whether a Registry-declared CLI Tool is available on the
local host. It never installs, configures, persists state, or evaluates
effective risk.
"""

from __future__ import annotations

import platform
import re
import shutil
import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Mapping, Sequence

# Controlled by the detector, not by Registry metadata.
VERSION_DETECTION_TIMEOUT_SECONDS = 3.0

# Basename-only executable names. Paths, spaces, and shell metacharacters are rejected.
_EXECUTABLE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
# Version flags only: -V, --version, etc. Not a shell argument language.
_VERSION_ARG_PATTERN = re.compile(r"^-{1,2}[A-Za-z0-9][A-Za-z0-9._-]*$")

# Flags that commonly turn a binary into an arbitrary command interpreter.
_FORBIDDEN_VERSION_FLAGS = frozenset(
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

WhichFn = Callable[[str], str | None]
RunFn = Callable[..., subprocess.CompletedProcess[str]]
PlatformFn = Callable[[], tuple[str, str]]


class DetectionStatus(str, Enum):
    """Structured detection outcome.

    ``detected`` means a candidate executable was found. Other statuses describe
    why detection stopped or why the result is not a successful version probe.
    """

    DETECTED = "detected"
    NOT_FOUND = "not-found"
    VERSION_UNAVAILABLE = "version-unavailable"
    INCOMPATIBLE = "incompatible"
    UNSUPPORTED = "unsupported"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass(frozen=True)
class DetectionResult:
    """Transient runtime observation for one Tool.

    This object is never written back to the Registry or harness configuration.
    """

    tool_id: str
    detected: bool
    status: DetectionStatus
    executable: str | None = None
    path: str | None = None
    version: str | None = None
    compatible: bool | None = None
    platform: str | None = None
    architecture: str | None = None
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "detected": self.detected,
            "status": self.status.value,
            "executable": self.executable,
            "path": self.path,
            "version": self.version,
            "compatible": self.compatible,
            "platform": self.platform,
            "architecture": self.architecture,
            "reason": self.reason,
        }


def current_platform() -> tuple[str, str]:
    """Return ``(os, architecture)`` using Registry taxonomy values when possible."""
    system = platform.system().lower()
    if system == "darwin":
        os_name = "macos"
    elif system == "windows":
        os_name = "windows"
    elif system == "linux":
        os_name = "linux"
    else:
        os_name = system

    machine = platform.machine().lower()
    if machine in {"x86_64", "amd64"}:
        arch = "x64"
    elif machine in {"aarch64", "arm64"}:
        arch = "arm64"
    else:
        arch = machine
    return os_name, arch


def platform_is_compatible(
    platforms: Sequence[Mapping[str, Any]] | None,
    os_name: str,
    architecture: str,
) -> bool:
    """Return whether the host matches declared Registry platform support.

    Missing or empty ``platforms`` means no restriction was declared, so the
    host is treated as compatible for detection purposes.
    """
    if not platforms:
        return True
    for entry in platforms:
        if not isinstance(entry, dict):
            continue
        if entry.get("os") != os_name:
            continue
        architectures = entry.get("architectures")
        if isinstance(architectures, list) and architecture in architectures:
            return True
    return False


def validate_detection_contract(
    executable: str | None,
    version_arguments: Sequence[str] | None,
) -> str | None:
    """Validate Registry detection fields before any process is started.

    Returns an error reason, or ``None`` when the contract is acceptable.
    """
    if executable is None:
        return "detection.executable is required"
    if not isinstance(executable, str) or not executable:
        return "detection.executable must be a non-empty string"
    if "/" in executable or "\\" in executable:
        return "detection.executable must be a basename, not a path"
    if _SHELL_METACHAR_PATTERN.search(executable) or " " in executable:
        return "detection.executable contains forbidden characters"
    if not _EXECUTABLE_PATTERN.fullmatch(executable):
        return "detection.executable does not match the safe basename contract"

    if version_arguments is None:
        return "detection.version_arguments is required"
    if not isinstance(version_arguments, (list, tuple)) or not version_arguments:
        return "detection.version_arguments must be a non-empty list"
    for arg in version_arguments:
        if not isinstance(arg, str) or not arg:
            return "detection.version_arguments entries must be non-empty strings"
        if " " in arg or _SHELL_METACHAR_PATTERN.search(arg):
            return "detection.version_arguments contains forbidden characters"
        if not _VERSION_ARG_PATTERN.fullmatch(arg):
            return "detection.version_arguments must be simple flags only"
        if arg in _FORBIDDEN_VERSION_FLAGS:
            return f"detection.version_arguments flag is not allowed: {arg}"
    return None


def _extract_version(stdout: str, stderr: str) -> str | None:
    for blob in (stdout, stderr):
        for line in blob.splitlines():
            text = line.strip()
            if text:
                return text
    return None


class ToolDetector:
    """Detect whether a Tool definition is available on the local host.

    Only ``kind: cli`` is supported in this phase. Execution always uses a
    structured argv list with ``shell=False``.
    """

    def __init__(
        self,
        *,
        which: WhichFn | None = None,
        run: RunFn | None = None,
        platform_info: PlatformFn | None = None,
        timeout_seconds: float = VERSION_DETECTION_TIMEOUT_SECONDS,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self._which = which or shutil.which
        self._run = run or self._default_run
        self._platform_info = platform_info or current_platform
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

    def detect(self, tool: Mapping[str, Any]) -> DetectionResult:
        """Detect one Tool definition. Does not mutate ``tool`` or any files."""
        os_name, architecture = self._platform_info()
        tool_id = tool.get("id")
        if not isinstance(tool_id, str) or not tool_id:
            return DetectionResult(
                tool_id="",
                detected=False,
                status=DetectionStatus.ERROR,
                platform=os_name,
                architecture=architecture,
                reason="tool id is required",
            )

        kind = tool.get("kind")
        if kind != "cli":
            return DetectionResult(
                tool_id=tool_id,
                detected=False,
                status=DetectionStatus.UNSUPPORTED,
                compatible=None,
                platform=os_name,
                architecture=architecture,
                reason=f"detection supports kind 'cli' only; got {kind!r}",
            )

        detection = tool.get("detection")
        if detection is None:
            return DetectionResult(
                tool_id=tool_id,
                detected=False,
                status=DetectionStatus.ERROR,
                platform=os_name,
                architecture=architecture,
                reason="detection metadata is missing",
            )
        if not isinstance(detection, Mapping):
            return DetectionResult(
                tool_id=tool_id,
                detected=False,
                status=DetectionStatus.ERROR,
                platform=os_name,
                architecture=architecture,
                reason="detection metadata must be a mapping",
            )

        executable = detection.get("executable")
        version_arguments = detection.get("version_arguments")
        contract_error = validate_detection_contract(executable, version_arguments)
        if contract_error is not None:
            return DetectionResult(
                tool_id=tool_id,
                detected=False,
                status=DetectionStatus.ERROR,
                executable=executable if isinstance(executable, str) else None,
                platform=os_name,
                architecture=architecture,
                reason=contract_error,
            )

        assert isinstance(executable, str)
        assert isinstance(version_arguments, (list, tuple))

        platforms = tool.get("platforms")
        compatible = platform_is_compatible(
            platforms if isinstance(platforms, list) else None,
            os_name,
            architecture,
        )

        resolved = self._which(executable)
        if not resolved:
            if not compatible:
                return DetectionResult(
                    tool_id=tool_id,
                    detected=False,
                    status=DetectionStatus.INCOMPATIBLE,
                    executable=executable,
                    compatible=False,
                    platform=os_name,
                    architecture=architecture,
                    reason="host platform/architecture is not declared as supported",
                )
            return DetectionResult(
                tool_id=tool_id,
                detected=False,
                status=DetectionStatus.NOT_FOUND,
                executable=executable,
                compatible=True,
                platform=os_name,
                architecture=architecture,
                reason=f"executable not found on PATH: {executable}",
            )

        if not compatible:
            # Discovery is preserved even when the platform is unsupported.
            return DetectionResult(
                tool_id=tool_id,
                detected=True,
                status=DetectionStatus.INCOMPATIBLE,
                executable=executable,
                path=resolved,
                compatible=False,
                platform=os_name,
                architecture=architecture,
                reason="host platform/architecture is not declared as supported",
            )

        argv = [resolved, *list(version_arguments)]
        try:
            completed = self._run(argv, timeout=self._timeout_seconds)
        except subprocess.TimeoutExpired:
            return DetectionResult(
                tool_id=tool_id,
                detected=True,
                status=DetectionStatus.TIMEOUT,
                executable=executable,
                path=resolved,
                compatible=True,
                platform=os_name,
                architecture=architecture,
                reason=f"version detection timed out after {self._timeout_seconds:g}s",
            )
        except OSError as exc:
            return DetectionResult(
                tool_id=tool_id,
                detected=True,
                status=DetectionStatus.ERROR,
                executable=executable,
                path=resolved,
                compatible=True,
                platform=os_name,
                architecture=architecture,
                reason=f"failed to execute version probe: {exc}",
            )

        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        version = _extract_version(stdout, stderr)

        if completed.returncode != 0:
            return DetectionResult(
                tool_id=tool_id,
                detected=True,
                status=DetectionStatus.VERSION_UNAVAILABLE,
                executable=executable,
                path=resolved,
                version=version,
                compatible=True,
                platform=os_name,
                architecture=architecture,
                reason=f"version probe exited with code {completed.returncode}",
            )

        if version is None:
            return DetectionResult(
                tool_id=tool_id,
                detected=True,
                status=DetectionStatus.VERSION_UNAVAILABLE,
                executable=executable,
                path=resolved,
                compatible=True,
                platform=os_name,
                architecture=architecture,
                reason="version probe produced no usable output",
            )

        return DetectionResult(
            tool_id=tool_id,
            detected=True,
            status=DetectionStatus.DETECTED,
            executable=executable,
            path=resolved,
            version=version,
            compatible=True,
            platform=os_name,
            architecture=architecture,
            reason=None,
        )
