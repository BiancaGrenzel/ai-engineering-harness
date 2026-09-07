# Cursor adapter test fixtures

Isolated project trees for adapter generation tests.

The executable test module is [`tests/test_cursor_adapter.py`](../../test_cursor_adapter.py)
so `unittest` discovery under `tests/` does not shadow the real top-level `adapters/` package.

## Schema policy

Fixtures do **not** copy `schemas/*.json`.

Tests copy the repository canonical schemas from `schemas/` into each temporary
project root so schema drift cannot diverge from the source of truth.
