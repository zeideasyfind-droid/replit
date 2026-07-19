#!/bin/bash
# Run all property normalizer tests
cd "$(dirname "$0")/.."
python -m pytest tests/test_property_normalizer.py -v
