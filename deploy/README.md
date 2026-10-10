# Deploy — Echo Protocol

This directory contains deployment configurations for running Echo Protocol on
a Raspberry Pi behind a Cloudflare Tunnel, reachable over Tailscale for admin
access.

## Architecture

Echo runs on **rpi3** alongside the [games](https://github.com/atmollohan/games)
server, using the same pattern as the other homelab apps.

```
User browser ──► Cloudflare Edge ──► cloudflared (host service) ──► localhost:8501
                                        ▲
                                   Tailscale SSH — admin access
                                        │
                                    [Raspberry Pi — rpi3]
```

- **cloudflared runs as a host service**, one tunnel per device with multiple
  domains each (`echo.mollo.tech` is added as another ingress on the rpi3 tunnel)
- **No open firewall ports** — Cloudflare Tunnel handles inbound traffic
- **No static IP needed** — Tailscale provides reliable SSH access
- **Multi-arch image** — builds for `linux/amd64` and `linux/arm64`
- Echo publishes `127.0.0.1:8501` so only the host `cloudflared` reaches it

## Files

| File | What it is |
|------|------------|
| `docker-compose.yml` | Echo app service (machine-readable) |
| `pi-setup.md` | Step-by-step Raspberry Pi setup guide |
| `cloudflare-tunnel.md` | Cloudflare Tunnel configuration (host-level) |
| `ops.md` | Day-to-day operations and troubleshooting |
| `setup.sh` | Idempotent one-shot setup script |
| `GAPS.md` | Known gaps / outstanding deployment tasks |

## Quick Start

1. **Flash a Pi 3+** with Raspberry Pi OS Lite (64-bit)
2. **Run setup** on the Pi: `bash deploy/setup.sh`
3. **Set up Tailscale**: `sudo tailscale up --ssh`
4. **Add `echo.mollo.tech`** to the existing rpi3 Cloudflare tunnel (see `cloudflare-tunnel.md`)
5. **Deploy**: `docker compose -f deploy/docker-compose.yml up -d`

> **WSL note:** This deployment targets a physical Raspberry Pi running Linux.
> WSL does not auto-start Docker or Tailscale — both require manual `sudo
> service docker start` and `sudo tailscale up` after each reboot. For local
> testing on WSL, use `streamlit run app.py` directly (no Docker needed).

Users can then reach the Echo UI at `https://echo.mollo.tech`.

## Versioning

Images are tagged and pushed to GHCR on every push to `main`:

- `ghcr.io/atmollohan/echo:latest` — always tracks `main`
- `ghcr.io/atmollohan/echo:<sha>` — immutable per-commit images

The deploy workflows pull the image onto the Pi and reconcile the stack with
`docker compose up -d`.

## CI/CD

GitHub Actions workflows in `.github/workflows/`:

- `docker.yml` — Builds and pushes multi-arch image to GHCR on push to `main`
- `deploy.yml` — Manual deploy: connects via Tailscale SSH and deploys to rpi3
- `release.yml` — On PR merge: creates a release, builds, and deploys to rpi3

Both deploy workflows authenticate to Tailscale with `secrets.TAILSCALE_AUTHKEY`
and optionally log in to GHCR with `secrets.GHCR_PAT` (the image is public, so
the login is skipped when the secret is unset). Public traffic is handled by the
host-level cloudflared tunnel — no `TUNNEL_TOKEN` secret is needed.

## Related Projects

The same deployment pattern is used for:

- **[Lil Chef](https://github.com/atmollohan/lil-chef)** — AI meal planner (Next.js)
- **[Games](https://github.com/atmollohan/games)** — Classic arcade games (Python)
- **[The Will of the People](https://github.com/l-town-fc/the-will-of-the-people)** — Discord bot (Node.js)

All share: Docker → GHCR multi-arch → Tailscale SSH deploy → Cloudflare Tunnel.
