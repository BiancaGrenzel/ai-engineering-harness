# Validation script dependencies
#
# Why Python:
# - Available on Linux, macOS, and Windows
# - No Node/npm ecosystem required for a single validator
# - Fits a vendor-neutral harness that must not assume one agent runtime
#
# Why these libraries:
# - PyYAML: mature YAML 1.1 loader used widely for config files
# - jsonschema: Draft 2020-12 validation matching schemas/*.schema.json
#
# Install:
#   pip install -r scripts/requirements.txt
#
# Run:
#   python scripts/validate-config.py
#
# Tests:
#   python -m unittest discover -s tests -v
