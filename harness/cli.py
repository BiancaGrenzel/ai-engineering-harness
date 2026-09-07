"""AI Engineering Harness CLI (argparse).

Thin interface over existing validation and adapters. Does not own generation
or schema validation logic.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from harness.commands import cmd_generate, cmd_validate, cmd_version
from harness.dispatch import supported_adapters


def _attach_unknown_adapter_error(parser: argparse.ArgumentParser) -> None:
    """Replace parser.error so unknown adapter names use a stable message and exit 1."""
    original_error = parser.error

    def error(message: str) -> None:  # type: ignore[misc]
        match = re.search(r"invalid choice: ['\"]([^'\"]+)['\"]", message)
        if match:
            print(
                f"Unknown or unsupported adapter: {match.group(1)}",
                file=sys.stderr,
            )
            raise SystemExit(1)
        original_error(message)

    parser.error = error  # type: ignore[method-assign]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="harness",
        description="AI Engineering Harness",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Usage:\n"
            "  harness <command>\n\n"
            "Commands:\n"
            "  validate\n"
            "  generate\n"
            "  version"
        ),
    )

    sub = parser.add_subparsers(dest="command", metavar="<command>")

    validate = sub.add_parser(
        "validate",
        help="Validate Harness configuration and the Tool Registry when present",
        description=(
            "Validate project Harness configuration and a provided Tool Registry "
            "(syntax only). Uses schemas/harness.schema.json and "
            "schemas/tool-registry.schema.json."
        ),
    )
    validate.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Project root containing .harness/harness.yaml (default: discover upward)",
    )
    validate.set_defaults(func=cmd_validate)

    generate = sub.add_parser(
        "generate",
        help="Generate agent-specific configuration via an adapter",
        description=(
            "Dispatch to an adapter generator. "
            f"Supported: {', '.join(supported_adapters())}."
        ),
    )
    _attach_unknown_adapter_error(generate)
    gen_sub = generate.add_subparsers(dest="adapter", metavar="<adapter>", required=True)

    for name in supported_adapters():
        adapter_parser = gen_sub.add_parser(
            name,
            help=f"Generate {name} agent configuration from Harness config",
            description=(
                f"Run the {name} adapter generator. "
                "Planning, conflicts, and rendering stay in the adapter."
            ),
        )
        adapter_parser.add_argument(
            "--root",
            type=Path,
            default=None,
            help="Project root containing .harness/harness.yaml (default: discover upward)",
        )
        adapter_parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show planned actions without writing files (passed to the adapter)",
        )
        adapter_parser.set_defaults(func=cmd_generate)

    version = sub.add_parser(
        "version",
        help="Print Harness CLI version",
        description=(
            "Print the Harness package/CLI version. "
            "Not the adapter version, tool version, or harness.yaml version field."
        ),
    )
    version.set_defaults(func=cmd_version)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 0
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
