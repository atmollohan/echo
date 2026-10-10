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

On rpi3, cloudflared runs as a **host service** — one tunnel per device with
multiple domains. Echo reuses the existing rpi3 tunnel; no new tunnel or
`TUNNEL_TOKEN` is needed.

Add `echo.mollo.tech` as an ingress pointing at `http://localhost:8501`:

```bash
cloudflared tunnel route dns <rpi3-tunnel-name> echo.mollo.tech
# edit the cloudflared config (e.g. ~/.cloudflared/config.yml):
#   - hostname: echo.mollo.tech
#     service: http://localhost:8501
cloudflared tunnel ingress validate
sudo systemctl restart cloudflared
```

See [cloudflare-tunnel.md](cloudflare-tunnel.md) for details.

## Step 5 — Deploy Echo Protocol

```bash
# Create the app directory
mkdir -p ~/projects/echo

# Start the Echo container (binds 127.0.0.1:8501 for the host tunnel)
docker compose -f deploy/docker-compose.yml up -d
```

Verify:

```bash
docker compose -f deploy/docker-compose.yml ps
curl -s -o /dev/null -w "%{http_code}" http://localhost:8501
# Should print 200
```

Once `echo.mollo.tech` routes to `localhost:8501` on the rpi3 tunnel, the app is
live at `https://echo.mollo.tech`.

## Step 6 — Keep Running

The compose file uses `restart: unless-stopped`, so the stack comes back
after a reboot. To update:

```bash
docker compose -f deploy/docker-compose.yml pull
docker compose -f deploy/docker-compose.yml up -d
```

## Security Notes

- The Echo service binds to `127.0.0.1:8501` — only the host `cloudflared` reaches it
- All public traffic goes through Cloudflare (TLS termination, DDoS protection)
- Admin SSH goes through Tailscale (not exposed to internet)
- No router port forwarding is required
- Generated protocol files persist in a Docker volume
