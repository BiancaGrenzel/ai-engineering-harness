#!/usr/bin/env python3
"""Validate .harness/harness.yaml against schemas/harness.schema.json.

Syntax validation only. Does not resolve whether referenced profiles, rules,
skills, or tools exist on disk.

Shared by ``scripts/validate-config.py`` and ``harness validate``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - dependency guard
    yaml = None  # type: ignore[assignment]

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - dependency guard
    Draft202012Validator = None  # type: ignore[misc, assignment]


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parent.parent


def _require_deps() -> int | None:
    if yaml is None:
        print(
            "Missing dependency: PyYAML. Install with:\n"
            "  pip install -r scripts/requirements.txt",
            file=sys.stderr,
        )
        return 2
    if Draft202012Validator is None:
        print(
            "Missing dependency: jsonschema. Install with:\n"
            "  pip install -r scripts/requirements.txt",
            file=sys.stderr,
        )
        return 2
    return None


def load_yaml(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)  # type: ignore[union-attr]


def load_json(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def format_error(error: object) -> str:
    path = ".".join(str(part) for part in error.absolute_path)  # type: ignore[attr-defined]
    location = path if path else "(root)"
    return f"- {location}: {error.message}"  # type: ignore[attr-defined]


def validate_document(instance: object, schema: dict) -> list[str]:
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.absolute_path))
    return [format_error(error) for error in errors]


def validate_paths(config_path: Path, schema_path: Path) -> int:
    """Validate harness.yaml at config_path against schema_path.

    Returns 0 on success, 1 on invalid configuration.
    """
    dep_code = _require_deps()
    if dep_code is not None:
        return dep_code

    if not config_path.is_file():
        print(f"Harness configuration is invalid.\n\nConfig not found: {config_path}", file=sys.stderr)
        return 1
    if not schema_path.is_file():
        print(f"Harness configuration is invalid.\n\nSchema not found: {schema_path}", file=sys.stderr)
        return 1

    try:
        instance = load_yaml(config_path)
    except yaml.YAMLError as exc:  # type: ignore[union-attr]
        print(f"Harness configuration is invalid.\n\nYAML parse error:\n{exc}", file=sys.stderr)
        return 1

    if instance is None:
        print(
            "Harness configuration is invalid.\n\n- (root): document is empty",
            file=sys.stderr,
        )
        return 1

    try:
        schema = load_json(schema_path)
    except json.JSONDecodeError as exc:
        print(f"Harness configuration is invalid.\n\nSchema JSON parse error:\n{exc}", file=sys.stderr)
        return 1

    if not isinstance(schema, dict):
        print(
            "Harness configuration is invalid.\n\n- schema: root must be a JSON object",
            file=sys.stderr,
        )
        return 1

    messages = validate_document(instance, schema)
    if messages:
        print("Harness configuration is invalid.\n", file=sys.stderr)
        print("\n".join(messages), file=sys.stderr)
        return 1

    print("Harness configuration is valid.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate harness.yaml against the Harness JSON Schema (syntax only)."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to harness.yaml (default: <repo>/.harness/harness.yaml)",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=None,
        help="Path to JSON Schema (default: <repo>/schemas/harness.schema.json)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = repo_root_from_script()
    config_path = args.config or (root / ".harness" / "harness.yaml")
    schema_path = args.schema or (root / "schemas" / "harness.schema.json")
    return validate_paths(config_path.resolve(), schema_path.resolve())
