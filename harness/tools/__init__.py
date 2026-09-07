"""Vendor-neutral Tool System runtime primitives.

This package currently exposes Tool resolution, read-only CLI detection, and
read-only health checking. It does not install Tools, compute effective risk,
or integrate with adapters.
"""

from __future__ import annotations

from harness.tools.detection import (
    VERSION_DETECTION_TIMEOUT_SECONDS,
    DetectionResult,
    DetectionStatus,
    ToolDetector,
)
from harness.tools.health import (
    HEALTH_CHECK_TIMEOUT_SECONDS,
    HealthResult,
    HealthStatus,
    ToolHealthChecker,
    format_health_cli_report,
    validate_health_contract,
)
from harness.tools.resolution import (
    ToolDefinition,
    ToolResolutionError,
    load_tool_registry,
    resolve_tool,
)

__all__ = [
    "HEALTH_CHECK_TIMEOUT_SECONDS",
    "VERSION_DETECTION_TIMEOUT_SECONDS",
    "DetectionResult",
    "DetectionStatus",
    "HealthResult",
    "HealthStatus",
    "ToolDefinition",
    "ToolDetector",
    "ToolHealthChecker",
    "ToolResolutionError",
    "format_health_cli_report",
    "load_tool_registry",
    "resolve_tool",
    "validate_health_contract",
]
