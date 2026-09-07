#!/usr/bin/env python3
"""Validate declarative Harness configuration and Tool Registry documents.

Syntax validation only. It does not detect, install, configure, or execute Tools.

Shared by ``scripts/validate-config.py`` and ``harness validate``.

Schemas and the Tool Registry are loaded from the content pack. Project intent
is ``.harness/harness.yaml``; consumer projects do not need local ``schemas/``
or ``tools/``.
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
            "  pip install ai-engineering-harness\n"
            "  # or for local development: pip install -r scripts/requirements.txt",
            file=sys.stderr,
        )
        return 2
    if Draft202012Validator is None:
        print(
            "Missing dependency: jsonschema. Install with:\n"
            "  pip install ai-engineering-harness\n"
            "  # or for local development: pip install -r scripts/requirements.txt",
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


def _validate_paths(document_path: Path, schema_path: Path, label: str) -> tuple[int, object | None]:
    """Validate one YAML document against a JSON Schema.

    Returns an exit code and the parsed document when valid.
    """
    dep_code = _require_deps()
    if dep_code is not None:
        return dep_code, None

    if not document_path.is_file():
        print(f"{label} is invalid.\n\nDocument not found: {document_path}", file=sys.stderr)
        return 1, None
    if not schema_path.is_file():
        print(f"{label} is invalid.\n\nSchema not found: {schema_path}", file=sys.stderr)
        return 1, None

    try:
        instance = load_yaml(document_path)
    except yaml.YAMLError as exc:  # type: ignore[union-attr]
        print(f"{label} is invalid.\n\nYAML parse error:\n{exc}", file=sys.stderr)
        return 1, None

    if instance is None:
        print(
            f"{label} is invalid.\n\n- (root): document is empty",
            file=sys.stderr,
        )
        return 1, None

    try:
        schema = load_json(schema_path)
    except json.JSONDecodeError as exc:
        print(f"{label} is invalid.\n\nSchema JSON parse error:\n{exc}", file=sys.stderr)
        return 1, None

    if not isinstance(schema, dict):
        print(
            f"{label} is invalid.\n\n- schema: root must be a JSON object",
            file=sys.stderr,
        )
        return 1, None

    messages = validate_document(instance, schema)
    if messages:
        print(f"{label} is invalid.\n", file=sys.stderr)
        print("\n".join(messages), file=sys.stderr)
        return 1, None

    return 0, instance


def validate_paths(config_path: Path, schema_path: Path) -> int:
    """Validate harness.yaml at config_path against schema_path."""
    code, _ = _validate_paths(config_path, schema_path, "Harness configuration")
    if code == 0:
        print("Harness configuration is valid.")
    return code


def validate_registry_paths(registry_path: Path, schema_path: Path, root: Path) -> int:
    """Validate the declarative Tool Registry and its documentation references."""
    code, instance = _validate_paths(registry_path, schema_path, "Tool registry")
    if code != 0:
        return code

    assert isinstance(instance, dict)
    tool_entries = instance["tools"]
    assert isinstance(tool_entries, list)
    ids = [entry["id"] for entry in tool_entries]
    duplicates = sorted({tool_id for tool_id in ids if ids.count(tool_id) > 1})
    if duplicates:
        print("Tool registry is invalid.\n", file=sys.stderr)
        print(f"- tools: duplicate id(s): {', '.join(duplicates)}", file=sys.stderr)
        return 1

    docs_root = (root / "docs" / "tools").resolve()
    invalid_docs = []
    for entry in tool_entries:
        doc_path = (root / entry["documentation"]).resolve()
        if not doc_path.is_relative_to(docs_root) or not doc_path.is_file():
            invalid_docs.append(entry["documentation"])
    if invalid_docs:
        print("Tool registry is invalid.\n", file=sys.stderr)
        print(
            f"- documentation: referenced file(s) not found or outside docs/tools: {', '.join(invalid_docs)}",
            file=sys.stderr,
        )
        return 1

    print("Tool registry is valid.")
    return 0


def _content_pack_paths() -> tuple[Path, Path, Path, Path]:
    """Return (pack_root, harness_schema, registry_schema, registry_path)."""
    from harness.content.pack import ContentPackError, content_pack_root

    try:
        pack = content_pack_root()
    except ContentPackError as exc:
        raise FileNotFoundError(str(exc)) from exc
    return (
        pack,
        pack / "schemas" / "harness.schema.json",
        pack / "schemas" / "tool-registry.schema.json",
        pack / "tools" / "registry.yaml",
    )


def validate_repository(root: Path) -> int:
    """Validate project intent against the content pack and resolve selections."""
    try:
        pack, harness_schema, registry_schema, registry_file = _content_pack_paths()
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    config_code = validate_paths(root / ".harness" / "harness.yaml", harness_schema)
    if config_code != 0:
        return config_code

    try:
        from adapters.common.resolve import ResolutionError, resolve_harness
    except ImportError as exc:  # pragma: no cover
        print(f"Unable to import resolution helpers: {exc}", file=sys.stderr)
        return 1

    try:
        resolve_harness(root)
    except ResolutionError as exc:
        print("Harness configuration is invalid.\n", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1

    if not registry_file.is_file():
        return 0
    return validate_registry_paths(registry_file, registry_schema, pack)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate Harness configuration and the Tool Registry."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to harness.yaml (default: <repo>/.harness/harness.yaml)",
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=None,
        help="Path to tools/registry.yaml (validates the Registry instead of harness.yaml)",
    )
    parser.add_argument(
        "--registry-schema",
        type=Path,
        default=None,
        help="Path to Tool Registry JSON Schema",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=None,
        help="Path to JSON Schema (default: content pack schemas/harness.schema.json)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = repo_root_from_script()
    try:
        pack, harness_schema, registry_schema, registry_file = _content_pack_paths()
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.registry is not None or args.registry_schema is not None:
        registry_path = args.registry or registry_file
        schema_path = args.registry_schema or registry_schema
        # Documentation paths are pack-relative (authoring root or bundled pack).
        return validate_registry_paths(
            registry_path.resolve(), schema_path.resolve(), pack
        )
    if args.config is None and args.schema is None:
        return validate_repository(root)
    config_path = args.config or (root / ".harness" / "harness.yaml")
    schema_path = args.schema or harness_schema
    return validate_paths(config_path.resolve(), schema_path.resolve())
