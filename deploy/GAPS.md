# Deployment Gaps — Echo Protocol

Known gaps and outstanding tasks for the rpi3 deployment. Keep this list current;
strike items when verified, add new ones as they surface.

Legend: 🔴 blocker · 🟠 action needed · 🟡 verify · 🟢 done

## External / configuration

| # | Status | Gap | Notes / next step |
|---|--------|-----|-------------------|
| 1 | 🟢 | **`echo.mollo.tech` routed on rpi3 host tunnel** | Done 2026-10-10 (see item 6): ingress → `http://localhost:8501` added, CNAME created, restarted. |
| 2 | 🟢 | **No `TUNNEL_TOKEN` secret needed** | Echo uses the host tunnel (one per device, multiple domains). The sidecar design was removed; no token secret is required. |
| 3 | 🟢 | **`TAILSCALE_AUTHKEY` present** | Confirmed set on `atmollohan/echo` (and games, lil-chef). `atmollohan` is a User account — secrets are per-repo, not org-wide. |
| 4 | 🟢 | **GHCR package is public — no PAT needed** | `ghcr.io/atmollohan/echo` shows a Public visibility label and grants an anonymous pull token, so the Pi can pull without login. The deploy workflows now skip `docker login` when `GHCR_PAT` is unset. |
| 5 | 🟢 | **rpi3 Tailscale node + ACL** | Verified on 2026-10-10: `atmollo@rpi3` reachable at `100.116.36.62` over Tailscale (Tailscale SSH works, passwordless sudo). |
| 6 | 🟢 | **`echo.mollo.tech` routed on rpi3 host tunnel** | Ingress added to `/etc/cloudflared/config.yml` (→ `http://localhost:8501`, before the 404 catch-all), CNAME created, validated, cloudflared restarted. Verified `https://echo.mollo.tech` → 200. Config backed up to `config.yml.bak.*`. |

## Code / compose

| # | Status | Gap | Notes / next step |
|---|--------|-----|-------------------|
| 7 | 🟢 | **Port binds to loopback** | Compose publishes `127.0.0.1:8501:8501` — only the host `cloudflared` can reach it, nothing on the LAN. |
| 8 | 🟡 | **Pi 3 resource headroom** | rpi3 already runs the games server. Echo's image (Streamlit + Jupyter + papermill + matplotlib) is heavy for a 1 GB Pi 3. Watch memory; move to rpi5 if OOM/slow. |
| 9 | 🟡 | **`release.yml` deploys `:latest`** | `release.yml` builds `:latest` and `:vX.Y.Z`, but auto-deploy (now via `docker.yml`) always deploys `:latest`. Decide whether deploys should pin the release tag instead. |
| 10 | 🟢 | **Output volume path** | Verified: app writes to `/app/generated`, which matches the `echo-data` volume mount. |

## Inherited from the shared pattern

| # | Status | Gap | Notes / next step |
|---|--------|-----|-------------------|
| 11 | 🟠 | **`sed` delimiter bug in the games workflow** | `games/.github/workflows/deploy.yml` uses `sed 's/MAG_PLACEHOLDER/<ghcr.io/...>/g'`; the slash in the image name makes sed fail (`unknown option to 's'`). Echo avoids this with `s\|...\|...\|g`. Consider fixing upstream in `games`. |
| 12 | 🟢 | **`GHCR_PAT` on games not required either** | `ghcr.io/atmollohan/games` is also public (anonymous pull token granted), so games can skip the login too. Only lil-chef is private and genuinely needs its PAT. |
| 13 | 🟢 | **Auto-deploy on push now works** | Implemented 2026-10-10: `docker.yml` now adds a `deploy-rpi3` job on branch pushes to `main` (build → push → deploy `:latest` to rpi3 via Tailscale SSH). Manual `deploy.yml` still available for pinning a release tag. |

## Verification checklist (once on rpi3)

```bash
# Containers up
docker ps --filter name=echo --format '{{.Names}} {{.Status}}'

# App responds locally
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8501          # 200
curl -s http://localhost:8501/_stcore/health                            # ok

# Host tunnel up + echo ingress present
sudo systemctl status cloudflared
cloudflared tunnel ingress validate

# Public hostname (after adding echo.mollo.tech to the rpi3 tunnel)
curl -s -o /dev/null -w '%{http_code}\n' https://echo.mollo.tech        # 200
```
