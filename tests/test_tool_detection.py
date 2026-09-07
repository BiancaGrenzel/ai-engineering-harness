#!/usr/bin/env python3
"""Tests for read-only Tool Detection. No real Tools are executed."""

from __future__ import annotations

import hashlib
import inspect
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harness.tools.detection import (  # noqa: E402
    VERSION_DETECTION_TIMEOUT_SECONDS,
    DetectionStatus,
    ToolDetector,
    validate_detection_contract,
)
from harness.tools.resolution import (  # noqa: E402
    ToolResolutionError,
    load_tool_registry,
    resolve_tool,
)

REGISTRY = ROOT / "tools" / "registry.yaml"
HARNESS_YAML = ROOT / ".harness" / "harness.yaml"


def _file_fingerprint(path: Path) -> tuple[str, int]:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest(), path.stat().st_mtime_ns


def cli_tool(
    *,
    tool_id: str = "sample",
    executable: str = "sample",
    version_arguments: list[str] | None = None,
    platforms: list[dict] | None = None,
    kind: str = "cli",
    detection: dict | None = ...,  # type: ignore[assignment]
) -> dict:
    tool: dict = {
        "id": tool_id,
        "name": "Sample",
        "kind": kind,
    }
    if detection is ...:
        tool["detection"] = {
            "executable": executable,
            "version_arguments": version_arguments or ["--version"],
        }
    elif detection is not None:
        tool["detection"] = detection
    if platforms is not None:
        tool["platforms"] = platforms
    return tool


class FakeRunner:
    """Records structured argv invocations; never uses a shell."""

    def __init__(
        self,
        *,
        returncode: int = 0,
        stdout: str = "sample 1.2.3\n",
        stderr: str = "",
        timeout: bool = False,
        error: Exception | None = None,
    ) -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.timeout = timeout
        self.error = error
        self.calls: list[dict] = []

    def __call__(self, args, *, timeout):
        self.calls.append({"args": list(args), "timeout": timeout, "shell": False})
        if self.timeout:
            raise subprocess.TimeoutExpired(cmd=list(args), timeout=timeout)
        if self.error is not None:
            raise self.error
        return subprocess.CompletedProcess(
            args=list(args),
            returncode=self.returncode,
            stdout=self.stdout,
            stderr=self.stderr,
        )


class ToolDetectionTests(unittest.TestCase):
    def test_cli_found(self) -> None:
        runner = FakeRunner()
        detector = ToolDetector(
            which=lambda name: f"/usr/bin/{name}",
            run=runner,
            platform_info=lambda: ("linux", "x64"),
        )
        result = detector.detect(cli_tool())
        self.assertTrue(result.detected)
        self.assertEqual(result.status, DetectionStatus.DETECTED)
        self.assertEqual(result.path, "/usr/bin/sample")
        self.assertEqual(result.version, "sample 1.2.3")
        self.assertTrue(result.compatible)

    def test_cli_not_found(self) -> None:
        detector = ToolDetector(
            which=lambda _name: None,
            run=FakeRunner(),
            platform_info=lambda: ("linux", "x64"),
        )
        result = detector.detect(cli_tool())
        self.assertFalse(result.detected)
        self.assertEqual(result.status, DetectionStatus.NOT_FOUND)
        self.assertIsNone(result.path)
        self.assertTrue(result.compatible)

    def test_version_detected(self) -> None:
        runner = FakeRunner(stdout="rtk 0.9.0\n")
        detector = ToolDetector(
            which=lambda name: f"/opt/{name}",
            run=runner,
            platform_info=lambda: ("macos", "arm64"),
        )
        result = detector.detect(cli_tool(tool_id="rtk", executable="rtk"))
        self.assertEqual(result.version, "rtk 0.9.0")
        self.assertEqual(result.status, DetectionStatus.DETECTED)

    def test_version_unavailable_empty_output(self) -> None:
        runner = FakeRunner(stdout="", stderr="")
        detector = ToolDetector(
            which=lambda name: f"/bin/{name}",
            run=runner,
            platform_info=lambda: ("linux", "x64"),
        )
        result = detector.detect(cli_tool())
        self.assertTrue(result.detected)
        self.assertEqual(result.status, DetectionStatus.VERSION_UNAVAILABLE)

    def test_timeout(self) -> None:
        runner = FakeRunner(timeout=True)
        detector = ToolDetector(
            which=lambda name: f"/bin/{name}",
            run=runner,
            platform_info=lambda: ("linux", "x64"),
            timeout_seconds=0.5,
        )
        result = detector.detect(cli_tool())
        self.assertTrue(result.detected)
        self.assertEqual(result.status, DetectionStatus.TIMEOUT)
        self.assertIn("timed out", result.reason or "")
        self.assertEqual(runner.calls[0]["timeout"], 0.5)

    def test_platform_compatible(self) -> None:
        detector = ToolDetector(
            which=lambda name: f"/bin/{name}",
            run=FakeRunner(),
            platform_info=lambda: ("linux", "x64"),
        )
        tool = cli_tool(
            platforms=[{"os": "linux", "architectures": ["x64", "arm64"]}],
        )
        result = detector.detect(tool)
        self.assertTrue(result.compatible)
        self.assertEqual(result.status, DetectionStatus.DETECTED)
        self.assertEqual(result.platform, "linux")
        self.assertEqual(result.architecture, "x64")

    def test_platform_incompatible_still_reports_discovery(self) -> None:
        runner = FakeRunner()
        detector = ToolDetector(
            which=lambda name: f"/bin/{name}",
            run=runner,
            platform_info=lambda: ("windows", "x64"),
        )
        tool = cli_tool(platforms=[{"os": "linux", "architectures": ["x64"]}])
        result = detector.detect(tool)
        self.assertTrue(result.detected)
        self.assertFalse(result.compatible)
        self.assertEqual(result.status, DetectionStatus.INCOMPATIBLE)
        self.assertEqual(result.path, "/bin/sample")
        self.assertEqual(runner.calls, [])

    def test_kind_unsupported(self) -> None:
        detector = ToolDetector(
            which=lambda _name: "/bin/x",
            run=FakeRunner(),
            platform_info=lambda: ("linux", "x64"),
        )
        result = detector.detect(cli_tool(kind="mcp-server", detection=None))
        self.assertFalse(result.detected)
        self.assertEqual(result.status, DetectionStatus.UNSUPPORTED)

    def test_executable_resolution_uses_which(self) -> None:
        seen: list[str] = []

        def fake_which(name: str) -> str | None:
            seen.append(name)
            return f"/resolved/{name}"

        detector = ToolDetector(
            which=fake_which,
            run=FakeRunner(),
            platform_info=lambda: ("linux", "x64"),
        )
        result = detector.detect(cli_tool(executable="rtk"))
        self.assertEqual(seen, ["rtk"])
        self.assertEqual(result.path, "/resolved/rtk")

    def test_structured_arguments_only(self) -> None:
        runner = FakeRunner()
        detector = ToolDetector(
            which=lambda name: f"/bin/{name}",
            run=runner,
            platform_info=lambda: ("linux", "x64"),
        )
        detector.detect(cli_tool(version_arguments=["--version"]))
        self.assertEqual(runner.calls[0]["args"], ["/bin/sample", "--version"])

    def test_shell_true_never_used_in_default_runner(self) -> None:
        source = inspect.getsource(ToolDetector._default_run)
        self.assertIn("shell=False", source)
        self.assertNotIn("shell=True", source)

        with mock.patch("harness.tools.detection.subprocess.run") as run_mock:
            run_mock.return_value = subprocess.CompletedProcess(
                args=["/bin/sample", "--version"],
                returncode=0,
                stdout="ok\n",
                stderr="",
            )
            detector = ToolDetector(
                which=lambda name: f"/bin/{name}",
                platform_info=lambda: ("linux", "x64"),
            )
            detector.detect(cli_tool())
            kwargs = run_mock.call_args.kwargs
            self.assertFalse(kwargs.get("shell", False))
            self.assertIsInstance(run_mock.call_args.args[0], list)

    def test_registry_not_modified(self) -> None:
        before = _file_fingerprint(REGISTRY)
        registry = load_tool_registry(REGISTRY)
        tool = resolve_tool(registry, "rtk")
        ToolDetector(
            which=lambda _name: None,
            run=FakeRunner(),
            platform_info=lambda: ("linux", "x64"),
        ).detect(tool)
        self.assertEqual(_file_fingerprint(REGISTRY), before)

    def test_harness_yaml_not_modified(self) -> None:
        self.assertTrue(HARNESS_YAML.is_file())
        before = _file_fingerprint(HARNESS_YAML)
        ToolDetector(
            which=lambda _name: None,
            run=FakeRunner(),
            platform_info=lambda: ("linux", "x64"),
        ).detect(cli_tool())
        self.assertEqual(_file_fingerprint(HARNESS_YAML), before)

    def test_project_filesystem_not_modified(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            marker = root / "marker.txt"
            marker.write_text("unchanged\n", encoding="utf-8")
            before = _file_fingerprint(marker)
            entries_before = sorted(p.name for p in root.iterdir())
            ToolDetector(
                which=lambda _name: None,
                run=FakeRunner(),
                platform_info=lambda: ("linux", "x64"),
            ).detect(cli_tool())
            self.assertEqual(sorted(p.name for p in root.iterdir()), entries_before)
            self.assertEqual(_file_fingerprint(marker), before)

    def test_result_not_persisted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            detector = ToolDetector(
                which=lambda name: f"/bin/{name}",
                run=FakeRunner(),
                platform_info=lambda: ("linux", "x64"),
            )
            result = detector.detect(cli_tool())
            self.assertTrue(result.detected)
            self.assertEqual(list(root.iterdir()), [])

    def test_stderr_used_when_stdout_empty(self) -> None:
        runner = FakeRunner(stdout="  \n", stderr="tool 9.9.9\n")
        detector = ToolDetector(
            which=lambda name: f"/bin/{name}",
            run=runner,
            platform_info=lambda: ("linux", "x64"),
        )
        result = detector.detect(cli_tool())
        self.assertEqual(result.version, "tool 9.9.9")
        self.assertEqual(result.status, DetectionStatus.DETECTED)

    def test_nonzero_exit_code(self) -> None:
        runner = FakeRunner(returncode=2, stdout="", stderr="boom\n")
        detector = ToolDetector(
            which=lambda name: f"/bin/{name}",
            run=runner,
            platform_info=lambda: ("linux", "x64"),
        )
        result = detector.detect(cli_tool())
        self.assertTrue(result.detected)
        self.assertEqual(result.status, DetectionStatus.VERSION_UNAVAILABLE)
        self.assertEqual(result.version, "boom")
        self.assertIn("exited with code 2", result.reason or "")

    def test_invalid_arguments_rejected(self) -> None:
        detector = ToolDetector(
            which=lambda name: f"/bin/{name}",
            run=FakeRunner(),
            platform_info=lambda: ("linux", "x64"),
        )
        result = detector.detect(
            cli_tool(version_arguments=["--version", "&&", "whoami"])
        )
        self.assertEqual(result.status, DetectionStatus.ERROR)
        self.assertFalse(result.detected)

    def test_executable_missing_in_registry(self) -> None:
        detector = ToolDetector(
            which=lambda _name: "/bin/x",
            run=FakeRunner(),
            platform_info=lambda: ("linux", "x64"),
        )
        result = detector.detect(
            {
                "id": "sample",
                "kind": "cli",
                "detection": {"version_arguments": ["--version"]},
            }
        )
        self.assertEqual(result.status, DetectionStatus.ERROR)
        self.assertIn("executable", result.reason or "")

    def test_detection_metadata_missing(self) -> None:
        detector = ToolDetector(
            which=lambda _name: "/bin/x",
            run=FakeRunner(),
            platform_info=lambda: ("linux", "x64"),
        )
        result = detector.detect({"id": "sample", "kind": "cli"})
        self.assertEqual(result.status, DetectionStatus.ERROR)
        self.assertIn("detection metadata is missing", result.reason or "")

    def test_malicious_registry_cannot_run_arbitrary_commands(self) -> None:
        payloads = [
            cli_tool(executable="rtk && whoami"),
            cli_tool(executable="rtk | cat"),
            cli_tool(executable="rtk; malicious-command"),
            cli_tool(executable="bash", version_arguments=["-c"]),
            cli_tool(executable="powershell", version_arguments=["-Command"]),
            cli_tool(executable="python", version_arguments=["-c"]),
            cli_tool(version_arguments=["--version;rm", "-rf"]),
            {
                "id": "evil",
                "kind": "cli",
                "detection": {
                    "executable": "rtk",
                    "version_arguments": ["--version && whoami"],
                },
            },
        ]
        runner = FakeRunner()
        detector = ToolDetector(
            which=lambda name: f"/bin/{name}",
            run=runner,
            platform_info=lambda: ("linux", "x64"),
        )
        for payload in payloads:
            with self.subTest(payload=payload):
                result = detector.detect(payload)
                self.assertEqual(result.status, DetectionStatus.ERROR)
                self.assertFalse(result.detected)
        self.assertEqual(runner.calls, [])

    def test_validate_detection_contract_helper(self) -> None:
        self.assertIsNone(validate_detection_contract("rtk", ["--version"]))
        self.assertIsNotNone(validate_detection_contract("rtk && x", ["--version"]))

    def test_timeout_constant_is_detector_owned(self) -> None:
        self.assertGreater(VERSION_DETECTION_TIMEOUT_SECONDS, 0)
        self.assertLessEqual(VERSION_DETECTION_TIMEOUT_SECONDS, 10)

    def test_resolve_rtk_from_real_registry_without_executing(self) -> None:
        try:
            import yaml  # noqa: F401
        except ImportError as exc:  # pragma: no cover
            raise unittest.SkipTest(
                "Install scripts/requirements.txt before running tests"
            ) from exc

        registry = load_tool_registry(REGISTRY)
        tool = resolve_tool(registry, "rtk")
        runner = FakeRunner(stdout="rtk fake\n")
        result = ToolDetector(
            which=lambda name: f"/mock/{name}",
            run=runner,
            platform_info=lambda: ("linux", "x64"),
        ).detect(tool)
        self.assertEqual(result.tool_id, "rtk")
        self.assertEqual(result.status, DetectionStatus.DETECTED)
        self.assertEqual(runner.calls[0]["args"], ["/mock/rtk", "--version"])

    def test_resolve_unknown_tool(self) -> None:
        with self.assertRaises(ToolResolutionError):
            resolve_tool({"version": 1, "tools": []}, "missing")


if __name__ == "__main__":
    unittest.main()
