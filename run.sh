#!/bin/bash

# 1. Mergem în folderul proiectului (pentru siguranță)
cd "$(dirname "$0")"

echo "🚀 Pornire Linux System Monitor..."

# 2. Activăm mediul virtual automat
source ~/pyqt-env/bin/activate

# 3. Rulăm interfața Python
python3 src/frontend/main.py