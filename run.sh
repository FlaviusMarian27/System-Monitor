#!/bin/bash

cd "$(dirname "$0")"

echo "Pornire Linux System Monitor..."

source ~/pyqt-env/bin/activate

python3 src/frontend/main.py