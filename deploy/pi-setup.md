# Pi Setup — Echo Protocol

Sets up a Raspberry Pi to run the Echo Protocol generator behind a Cloudflare
Tunnel, reachable over Tailscale for admin access.

> **WSL note:** These instructions target a physical Raspberry Pi running
> Raspberry Pi OS. Docker and Tailscale do not auto-start on WSL — they
> require manual `sudo service docker start` and `sudo tailscale up` after
> each Windows reboot. Use `streamlit run app.py` for local testing on WSL.

## Requirements

| Item | Minimum | Recommended |
|------|---------|-------------|
| Hardware | Raspberry Pi 3 | Raspberry Pi 4 or 5 |
| OS | Raspberry Pi OS Lite (64-bit) | Same |
| Storage | 16 GB SD | 32+ GB SSD (USB boot) |
| Network | Wired Ethernet | Ethernet + Wi-Fi fallback |
| Power | 2.5 A supply | Official Pi PSU |

## Step 1 — Flash and Boot

1. Flash Raspberry Pi OS Lite (64-bit) to an SD card with the
   [Raspberry Pi Imager](https://www.raspberrypi.com/software/).
2. In Imager settings:
   - Set hostname (e.g. `rpi-echo`)
   - Enable SSH **with public key only**
   - Set username/password
   - Configure Wi-Fi (if not using Ethernet)
   - Set locale
3. Boot the Pi and SSH in:

```bash
ssh mollopi5@rpi-echo.local
```

## Step 2 — Base Packages

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io docker-compose-v2
sudo usermod -aG docker $USER
# Log out and back in for group to take effect
```

Verify Docker:

```bash
docker --version
docker compose version
```

## Step 3 — Tailscale

Tailscale provides secure SSH access without open firewall ports.

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up --ssh
```

Open the auth URL in a browser to authenticate. After that:

```bash
tailscale status          # verify connected
tailscale ip -4           # get Tailscale IP
```

Your Pi is now reachable from any device on your Tailnet via:

```bash
ssh mollopi5@rpi-echo     # or use the Tailscale IP
```

No ports need to be opened in your router.

## Step 4 — Cloudflare Tunnel

Cloudflare Tunnel is already running on this Pi as a host systemd service.
It proxies the Echo web UI at `http://localhost:8501`.

See [cloudflare-tunnel.md](cloudflare-tunnel.md) for details on the existing
tunnel configuration.

To verify the tunnel is working:

```bash
sudo systemctl status cloudflared
cloudflared tunnel list
```

## Step 5 — Deploy Echo Protocol

```bash
# Create the app directory
mkdir -p ~/projects/echo/generated

# Pull the image
docker pull ghcr.io/atmollohan/echo:latest

# Start the stack
docker compose -f deploy/docker-compose.yml up -d
```

Verify:

```bash
docker compose -f deploy/docker-compose.yml ps
curl -s -o /dev/null -w "%{http_code}" http://localhost:8501
# Should print 200
```

If the tunnel is configured to point at `localhost:8501`, your app is now
live at the tunnel's public hostname (e.g. `https://echo.yourlab.com`).

## Step 6 — Keep Running

The compose file uses `restart: unless-stopped`, so the stack comes back
after a reboot. To update:

```bash
docker compose -f deploy/docker-compose.yml pull
docker compose -f deploy/docker-compose.yml up -d
```

## Security Notes

- The Echo service binds to `127.0.0.1:8501` — not accessible from the LAN
- All public traffic goes through Cloudflare (TLS termination, DDoS protection)
- Admin SSH goes through Tailscale (not exposed to internet)
- No router port forwarding is required
- Generated protocol files persist in a Docker volume
