#!/bin/bash
set -e

# ============================================
# Popup Server - First-time Deployment Script
# ============================================

GITHUB_RAW="https://raw.githubusercontent.com/Spec-DY/popup-window/main/server"
INSTALL_DIR="$HOME/popup-server"
SERVICE_NAME="popup"
SERVER_PORT=12345
CURRENT_USER=$(whoami)

echo "============================="
echo " Popup Server Setup"
echo "============================="
echo ""
echo "Install dir : $INSTALL_DIR"
echo "User        : $CURRENT_USER"
echo "Port        : $SERVER_PORT"
echo ""

# 1. Install system dependencies
echo "[1/5] Installing system dependencies..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update -qq
    sudo apt-get install -y -qq python3 python3-pip curl
elif command -v dnf &> /dev/null; then
    sudo dnf install -y python3 python3-pip curl
elif command -v yum &> /dev/null; then
    sudo yum install -y python3 python3-pip curl
elif command -v pacman &> /dev/null; then
    sudo pacman -S --noconfirm python python-pip curl
else
    echo "Unsupported package manager. Please install python3, pip, and curl manually."
    exit 1
fi

# 2. Download server files
echo "[2/5] Downloading server files..."
mkdir -p "$INSTALL_DIR"
curl -fsSL "${GITHUB_RAW}/server.py"  -o "$INSTALL_DIR/server.py"
curl -fsSL "${GITHUB_RAW}/update.sh"  -o "$INSTALL_DIR/update.sh"
chmod +x "$INSTALL_DIR/update.sh"
echo "Downloaded server.py and update.sh"

# 3. Install Python dependencies
echo "[3/5] Installing Python dependencies..."
python3 -m pip install --user cryptography

# 4. Create systemd service
echo "[4/5] Creating systemd service..."
sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null <<EOF
[Unit]
Description=Popup Server
After=network.target

[Service]
ExecStart=/usr/bin/python3 ${INSTALL_DIR}/server.py
WorkingDirectory=${INSTALL_DIR}
Restart=always
RestartSec=5
User=${CURRENT_USER}
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}.service

# 5. Open firewall port (if firewall is active)
echo "[5/5] Configuring firewall..."
if command -v ufw &> /dev/null && sudo ufw status | grep -q "active"; then
    sudo ufw allow ${SERVER_PORT}/tcp
    echo "UFW: port ${SERVER_PORT} opened"
elif command -v firewall-cmd &> /dev/null && sudo firewall-cmd --state 2>/dev/null | grep -q "running"; then
    sudo firewall-cmd --permanent --add-port=${SERVER_PORT}/tcp
    sudo firewall-cmd --reload
    echo "Firewalld: port ${SERVER_PORT} opened"
else
    echo "No active firewall detected, skipping"
fi

# Start the service
sudo systemctl start ${SERVICE_NAME}.service

echo ""
echo "============================="
echo " Setup complete!"
echo "============================="
echo ""
echo "Service status:"
sudo systemctl status ${SERVICE_NAME}.service --no-pager
echo ""
echo "Useful commands:"
echo "  sudo systemctl status ${SERVICE_NAME}   # Check status"
echo "  sudo systemctl restart ${SERVICE_NAME}   # Restart"
echo "  sudo journalctl -u ${SERVICE_NAME} -f    # View logs"
echo "  bash ${INSTALL_DIR}/update.sh             # Update server"
