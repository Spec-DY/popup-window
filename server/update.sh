#!/bin/bash
set -e

# ============================================
# Popup Server - One-click Update Script
# ============================================

GITHUB_RAW="https://raw.githubusercontent.com/Spec-DY/popup-window/main/server"
INSTALL_DIR="$HOME/popup-server"
SERVICE_NAME="popup"

echo "============================="
echo " Popup Server Update"
echo "============================="

# Check install dir exists
if [ ! -f "$INSTALL_DIR/server.py" ]; then
    echo "Error: server.py not found in $INSTALL_DIR. Run setup.sh first."
    exit 1
fi

# Download latest files
echo "[1/2] Downloading latest server files..."
curl -fsSL "${GITHUB_RAW}/server.py"  -o "$INSTALL_DIR/server.py"
curl -fsSL "${GITHUB_RAW}/update.sh"  -o "$INSTALL_DIR/update.sh"
chmod +x "$INSTALL_DIR/update.sh"
echo "Downloaded server.py and update.sh"

# Restart service
echo "[2/2] Restarting service..."
sudo systemctl restart ${SERVICE_NAME}.service

echo ""
echo "============================="
echo " Update complete!"
echo "============================="
echo ""
echo "Service status:"
sudo systemctl status ${SERVICE_NAME}.service --no-pager
