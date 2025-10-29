#!/bin/bash
# Script to fix Docker IPv6 connectivity issues for Docker Desktop

echo "Configuring Docker Desktop to prefer IPv4..."

DOCKER_CONFIG="$HOME/.docker/daemon.json"

# Backup existing daemon.json if it exists
if [ -f "$DOCKER_CONFIG" ]; then
    cp "$DOCKER_CONFIG" "$DOCKER_CONFIG.backup"
    echo "Backed up existing daemon.json to $DOCKER_CONFIG.backup"
fi

# Check if Docker Desktop is running
if ! docker info > /dev/null 2>&1; then
    echo "✗ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Update daemon.json with IPv4 settings
# First, check if we need to merge with existing config
if [ -f "$DOCKER_CONFIG" ]; then
    # Use Python to safely merge JSON (more reliable than shell)
    python3 << 'PYTHON_SCRIPT'
import json
import sys
import os

config_path = os.path.expanduser("~/.docker/daemon.json")

# Read existing config
try:
    with open(config_path, 'r') as f:
        config = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    config = {}

# Add/update IPv4 settings
config["dns"] = ["8.8.8.8", "8.8.4.4"]
config["ipv6"] = False
config["fixed-cidr-v6"] = ""

# Write back
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print("✓ Configuration updated successfully")
PYTHON_SCRIPT
else
    # Create new config file
    cat > "$DOCKER_CONFIG" << 'EOF'
{
  "dns": ["8.8.8.8", "8.8.4.4"],
  "ipv6": false,
  "fixed-cidr-v6": ""
}
EOF
    echo "✓ Created new daemon.json configuration"
fi

echo ""
echo "Docker daemon configuration updated at: $DOCKER_CONFIG"
echo ""
echo "⚠️  IMPORTANT: You need to restart Docker Desktop for changes to take effect."
echo ""
echo "You can restart Docker Desktop by:"
echo "  1. Open Docker Desktop application"
echo "  2. Go to Settings (gear icon)"
echo "  3. Click 'Restart' button, OR"
echo "  4. Right-click Docker icon in system tray → Restart"
echo ""
echo "After restarting, try building your Docker image again:"
echo "  docker compose run --rm api python -m app.scripts.ingest_docs"

