#!/bin/bash

# 1. Automatically find the current project directory and the Desktop directory
PROJECT_DIR=$(pwd)
DESKTOP_DIR=$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")
SHORTCUT="$DESKTOP_DIR/SystemMonitor.desktop"

echo "⚙️  Creating shortcut on Desktop..."

# 2. Generate the .desktop file with the correct paths
cat > "$SHORTCUT" << EOF
[Desktop Entry]
Version=1.0
Name=Linux System Monitor
Comment=Custom system monitoring application
Exec=$PROJECT_DIR/run.sh
Icon=$PROJECT_DIR/icon.png
Terminal=false
Type=Application
Categories=System;Utility;
EOF

# 3. Make the shortcut executable
chmod +x "$SHORTCUT"

# 4. Ubuntu magic: Mark the app as 'trusted' so it doesn't ask for launch confirmation
if command -v gio &> /dev/null; then
    gio set "$SHORTCUT" metadata::trusted true
fi

echo "✅ Done! The shortcut was successfully created on your Desktop."
echo "💡 Go to your Desktop and double-click the icon to launch the app!"