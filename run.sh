#!/bin/bash

cd "$(dirname "$0")"

echo "Pornire Linux System Monitor..."

source "$(dirname "$0")/.venv/bin/activate"

python3 src/frontend/main.py