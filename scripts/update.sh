#!/usr/bin/env bash
set -e

echo "Updating LXMF Bot..."

git pull
uv sync

sudo systemctl restart lxmfbot

echo "Update complete."
