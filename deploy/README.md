# Deploy — Echo Protocol

This directory contains deployment configurations for running Echo Protocol on
a Raspberry Pi behind a Cloudflare Tunnel, reachable over Tailscale for admin
access.

## Architecture

```
User browser ──► Cloudflare Edge ──► cloudflared (host systemd) ──► localhost:8501
                                       ▲
                                  Tailscale SSH — admin access
                                       │
                                   [Raspberry Pi]
```

- **cloudflared runs as a host service** on the Pi, not inside Docker
- **No open firewall ports** — Cloudflare Tunnel handles inbound traffic
- **No static IP needed** — Tailscale provides reliable SSH access
- **Multi-arch image** — builds for `linux/amd64` and `linux/arm64`

## Files

| File | What it is |
|------|------------|
| `docker-compose.yml` | Echo app service (machine-readable) |
| `pi-setup.md` | Step-by-step Raspberry Pi setup guide |
| `cloudflare-tunnel.md` | Cloudflare Tunnel configuration (host-level) |
| `ops.md` | Day-to-day operations and troubleshooting |
| `setup.sh` | Idempotent one-shot setup script |

## Quick Start

1. **Flash a Pi** with Raspberry Pi OS Lite (64-bit)
2. **Run setup** on the Pi: `bash deploy/setup.sh`
3. **Set up Tailscale**: `sudo tailscale up --ssh`
4. **Ensure cloudflared tunnel** is configured and pointing at `localhost:8501`
5. **Deploy**: `docker compose -f deploy/docker-compose.yml up -d`

> **WSL note:** This deployment targets a physical Raspberry Pi running Linux.
> WSL does not auto-start Docker or Tailscale — both require manual `sudo
> service docker start` and `sudo tailscale up` after each reboot. For local
> testing on WSL, use `streamlit run app.py` directly (no Docker needed).

Users can then reach the Echo UI at `https://echo.yourdomain.com`.

## CI/CD

GitHub Actions workflows in `.github/workflows/`:

- `docker.yml` — Builds and pushes multi-arch image to GHCR on push to `main`
- `deploy.yml` — Connects via Tailscale SSH and deploys to the Pi

## Related Projects

The same deployment pattern is used for:

- **[Lil Chef](https://github.com/atmollohan/lil-chef)** — AI meal planner (Next.js)
- **[Games](https://github.com/atmollohan/games)** — Classic arcade games (Python)
- **[The Will of the People](https://github.com/l-town-fc/the-will-of-the-people)** — Discord bot (Node.js)

All share: Docker → GHCR multi-arch → Tailscale SSH deploy → Cloudflare Tunnel.
