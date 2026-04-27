#!/usr/bin/env bash
set -euo pipefail

# Build standalone wirecup binary from wirecup.py
source .venv/bin/activate
pyinstaller wirecup.spec

echo "Built: dist/wirecup"
echo "Run: ./dist/wirecup ."
