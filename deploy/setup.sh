#!/usr/bin/env bash
# setup.sh — One-shot setup for Echo Protocol on a fresh Raspberry Pi
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/atmollohan/echo/main/deploy/setup.sh | bash
#
# Or locally:
#   bash deploy/setup.sh
#
# This script is idempotent and public-safe (no secrets).
# After running, set CLOUDFLARE_TUNNEL_TOKEN and start the stack.

set -euo pipefail

echo "=== Echo Protocol — Pi Setup ==="

# ── Detect ──────────────────────────────────────────────────────────────
if [ "$(uname -m)" != "aarch64" ] && [ "$(uname -m)" != "armv7l" ]; then
  echo "Warning: This script is designed for ARM (Raspberry Pi)."
  echo "Detected: $(uname -m)"
fi

# ── System Packages ─────────────────────────────────────────────────────
echo "Installing system packages..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io docker-compose-v2 curl

# ── Docker without sudo ──────────────────────────────────────────────────
if ! groups "$USER" | grep -q docker; then
  echo "Adding $USER to docker group..."
  sudo usermod -aG docker "$USER"
  echo "You'll need to log out and back in for this to take effect."
fi

# ── Enable Docker on boot ────────────────────────────────────────────────
sudo systemctl enable docker
sudo systemctl start docker

# ── Tailscale ────────────────────────────────────────────────────────────
if ! command -v tailscale &>/dev/null; then
  echo "Installing Tailscale..."
  curl -fsSL https://tailscale.com/install.sh | sh
  echo "Run 'sudo tailscale up --ssh' to authenticate."
else
  echo "Tailscale already installed."
  tailscale status 2>/dev/null || echo "Tailscale not authenticated. Run 'sudo tailscale up --ssh'."
fi

# ── Docker Compose ───────────────────────────────────────────────────────
echo "Creating project directory..."
mkdir -p ~/projects/echo/generated

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Authenticate Tailscale:  sudo tailscale up --ssh"
echo "  2. Configure cloudflared:    See deploy/cloudflare-tunnel.md"
echo "  3. Start the stack:          docker compose -f deploy/docker-compose.yml up -d"
echo ""
echo "Your app will be available at http://localhost:8501"
echo "And publicly at https://echo.yourdomain.com (once tunnel points at :8501)"
