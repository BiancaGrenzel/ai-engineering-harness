"""Vendor-neutral Tool System runtime primitives.

This package currently exposes Tool resolution and read-only CLI detection.
It does not install Tools, compute effective risk, or integrate with adapters.
"""

from __future__ import annotations

from harness.tools.detection import (
    VERSION_DETECTION_TIMEOUT_SECONDS,
    DetectionResult,
    DetectionStatus,
    ToolDetector,
)
from harness.tools.resolution import (
    ToolDefinition,
    ToolResolutionError,
    load_tool_registry,
    resolve_tool,
)

__all__ = [
    "VERSION_DETECTION_TIMEOUT_SECONDS",
    "DetectionResult",
    "DetectionStatus",
    "ToolDefinition",
    "ToolDetector",
    "ToolResolutionError",
    "load_tool_registry",
    "resolve_tool",
]
