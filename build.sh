#!/usr/bin/env bash
set -euo pipefail

# Build standalone wirecup binary from wirecup.py
source .venv/bin/activate
rm -rf build dist
pyinstaller wirecup.spec
cp dist/wirecup wirecup

echo "Built and copied to: wirecup"
echo "Run: ./wirecup ."
