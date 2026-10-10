# Pi Setup — Echo Protocol

Sets up a Raspberry Pi to run the Echo Protocol generator behind a Cloudflare
Tunnel, reachable over Tailscale for admin access.

Echo is deployed to **rpi3**, colocated with the [games](https://github.com/atmollohan/games)
server, using the same pattern as the other homelab apps.

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
   - Set hostname (e.g. `rpi3`)
   - Enable SSH **with public key only**
   - Set username/password
   - Configure Wi-Fi (if not using Ethernet)
   - Set locale
3. Boot the Pi and SSH in:

```bash
ssh mollopi5@rpi3.local
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
ssh mollopi5@rpi3     # or use the Tailscale IP
```

No ports need to be opened in your router.

> **CI note:** GitHub Actions connects to this Tailnet with a reusable auth key
> stored as the `TAILSCALE_AUTHKEY` repo secret. The Pi's `tailscaled` should be
> tagged (e.g. `tag:prod`) and the Tailscale ACL should allow
> `autogroup:member` → `tag:prod` and the CI tag. See the lil-chef / games repos
> for the working configuration.

## Step 4 — Cloudflare Tunnel

On rpi3, cloudflared runs as a **sidecar container** in the compose stack (not a
host systemd service). It authenticates with a tunnel token and proxies the Echo
web UI.

The tunnel token comes from `secrets.TUNNEL_TOKEN` in CI, or from
`deploy/.env` for manual deploys:

```bash
# deploy/.env
TUNNEL_TOKEN=<your-cloudflare-tunnel-token>
```

See [cloudflare-tunnel.md](cloudflare-tunnel.md) for setup details.

## Step 5 — Deploy Echo Protocol

```bash
# Create the app directory
mkdir -p ~/projects/echo

# Write the tunnel token
echo 'TUNNEL_TOKEN=<your-cloudflare-tunnel-token>' > ~/projects/echo/.env

# Start the stack (echo app + cloudflared sidecar)
docker compose -f deploy/docker-compose.yml up -d
```

Verify:

```bash
docker compose -f deploy/docker-compose.yml ps
curl -s -o /dev/null -w "%{http_code}" http://localhost:8501
# Should print 200
```

If the tunnel's public hostname targets `http://echo-protocol:8501`, your app is
live at the tunnel's public hostname (e.g. `https://echo.mollo.tech`).

## Step 6 — Keep Running

The compose file uses `restart: unless-stopped`, so the stack comes back
after a reboot. To update:

```bash
docker compose -f deploy/docker-compose.yml pull
docker compose -f deploy/docker-compose.yml up -d
```

## Security Notes

- The Echo service publishes `8501:8501` — see [GAPS.md](GAPS.md) for the
  recommendation to bind it to loopback
- All public traffic goes through Cloudflare (TLS termination, DDoS protection)
- Admin SSH goes through Tailscale (not exposed to internet)
- No router port forwarding is required
- Generated protocol files persist in a Docker volume
