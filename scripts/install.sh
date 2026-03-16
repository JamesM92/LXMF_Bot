#!/usr/bin/env bash
set -e

PROJECT_DIR="$(pwd)"
SERVICE_NAME="lxmfbot"

echo "Installing LXMF Bot..."

# Ensure uv exists
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -Ls https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "Installing Python dependencies..."
uv sync

echo "Installing systemd service..."
sudo cp systemd/lxmfbot.service /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl restart $SERVICE_NAME

echo ""
echo "LXMF Bot installed!"
echo ""
echo "Check status:"
echo "systemctl status lxmfbot"
