# Operations — Echo Protocol

Day-to-day operations for the Echo Protocol deployment on Raspberry Pi.

## Service Status

```bash
# Check Echo container
docker compose -f deploy/docker-compose.yml ps
docker logs -f echo

# Check the cloudflared sidecar
docker ps --filter name=echo-tunnel --format '{{.Status}}'
docker logs echo-tunnel --tail 20

# Check resource usage
docker stats --no-stream
```

## Updating

### Update the App

```bash
# Pull latest images
docker compose -f deploy/docker-compose.yml pull

# Recreate containers
docker compose -f deploy/docker-compose.yml up -d

# Clean up old images
docker image prune -a -f
```

Deploys are also automated via GitHub Actions — see `.github/workflows/`.

### Update the Pi

```bash
sudo apt update && sudo apt upgrade -y
sudo reboot
```

After reboot, verify the stack comes back:

```bash
docker compose -f deploy/docker-compose.yml ps
```

## Backups

Generated protocol files are stored in a Docker volume:

```bash
# Backup volume
docker run --rm -v echo-data:/source -v /tmp/backup:/dest \
  alpine tar czf /dest/echo-data-$(date +%Y%m%d).tar.gz -C /source .

# Restore volume
docker run --rm -v echo-data:/dest -v /tmp/backup:/source \
  alpine tar xzf /source/echo-data-*.tar.gz -C /dest
```

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `http://localhost:8501` returns nothing | Container not running | `docker compose up -d` |
| Public URL returns 502 | cloudflared can't reach the app | Check `echo` container is up; check `docker logs echo-tunnel` |
| Public URL returns 403 | Cloudflare Access blocking | Check Access policies in Zero Trust dashboard |
| Tunnel not connecting | Missing/invalid `TUNNEL_TOKEN`, or wrong ingress target | Check `docker logs echo-tunnel`; verify public hostname targets `http://echo-protocol:8501` |
| Out of disk space | Old Docker images or logs | `docker image prune -a -f` and check `docker system df` |
| Pi unresponsive via Tailscale | Tailscale daemon crashed | `sudo systemctl restart tailscaled` (needs physical access or IPMI) |

## Monitoring (Minimal)

On a Pi, keep it simple:

```bash
# Basic health — run from cron or monitoring script
curl -s -o /dev/null -w "%{http_code}" http://localhost:8501 || \
  echo "Echo app down" | mail -s "Echo Alert" you@example.com
```

## CI/CD Deploy

A deploy is triggered from GitHub Actions using Tailscale SSH:

1. GitHub Actions connects to Tailscale via `tailscale/github-action@v4`
   (`TAILSCALE_AUTHKEY` secret)
2. SSHs into rpi3 via `tailscale ssh`
3. Writes `deploy/docker-compose.yml` + `.env` (from `TUNNEL_TOKEN`), logs in to
   GHCR (`GHCR_PAT` secret), pulls the image, and reconciles the stack

See `.github/workflows/deploy.yml` and `.github/workflows/release.yml`.
