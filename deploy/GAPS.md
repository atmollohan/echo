# Deployment Gaps — Echo Protocol

Known gaps and outstanding tasks for the rpi3 deployment. Keep this list current;
strike items when verified, add new ones as they surface.

Legend: 🔴 blocker · 🟠 action needed · 🟡 verify · 🟢 done

## External / configuration

| # | Status | Gap | Notes / next step |
|---|--------|-----|-------------------|
| 1 | 🟠 | **`echo.mollo.tech` not yet routed on rpi3 host tunnel** | Not listed in Cloudflare yet. Add it as an ingress on the existing rpi3 host tunnel → `http://localhost:8501`, then restart cloudflared. See `cloudflare-tunnel.md`. |
| 2 | 🟢 | **No `TUNNEL_TOKEN` secret needed** | Echo uses the host tunnel (one per device, multiple domains). The sidecar design was removed; no token secret is required. |
| 3 | 🟢 | **`TAILSCALE_AUTHKEY` present** | Confirmed set on `atmollohan/echo` (and games, lil-chef). `atmollohan` is a User account — secrets are per-repo, not org-wide. |
| 4 | 🟢 | **GHCR package is public — no PAT needed** | `ghcr.io/atmollohan/echo` shows a Public visibility label and grants an anonymous pull token, so the Pi can pull without login. The deploy workflows now skip `docker login` when `GHCR_PAT` is unset. |
| 5 | 🟡 | **rpi3 Tailscale node + ACL** | Deploy assumes `mollopi5@rpi3` is reachable over Tailscale and that the CI tag is allowed by the ACL. Not verifiable from WSL (tailscaled not running). Confirm with `tailscale status` on a Tailnet host. |

## Code / compose

| # | Status | Gap | Notes / next step |
|---|--------|-----|-------------------|
| 6 | 🟢 | **Port binds to loopback** | Compose publishes `127.0.0.1:8501:8501` — only the host `cloudflared` can reach it, nothing on the LAN. |
| 7 | 🟡 | **Pi 3 resource headroom** | rpi3 already runs the games server. Echo's image (Streamlit + Jupyter + papermill + matplotlib) is heavy for a 1 GB Pi 3. Watch memory; move to rpi5 if OOM/slow. |
| 8 | 🟠 | **`release.yml` deploys `:latest`** | The release builds `:latest` *and* `:vX.Y.Z`, but the deploy step pulls `:latest`. Decide whether deploys should pin the release tag instead. |
| 9 | 🟢 | **Output volume path** | Verified: app writes to `PROJECT_ROOT/generated` = `/app/generated`, which matches the `echo-data` volume mount. |

## Inherited from the shared pattern

| # | Status | Gap | Notes / next step |
|---|--------|-----|-------------------|
| 10 | 🟠 | **`sed` delimiter bug in the games workflow** | `games/.github/workflows/deploy.yml` uses `sed 's/MAG_PLACEHOLDER/<ghcr.io/...>/g'`; the slash in the image name makes sed fail (`unknown option to 's'`). Echo avoids this with `s\|...\|...\|g`. Consider fixing upstream in `games`. |
| 11 | 🟢 | **`GHCR_PAT` on games not required either** | `ghcr.io/atmollohan/games` is also public (anonymous pull token granted), so games can skip the login too. Only lil-chef is private and genuinely needs its PAT. |
| 12 | 🟡 | **CI/CD not auto-deploy on push** | Same as the games `PLAN`/`GAPS`: push builds the image but does not auto-deploy; deploy is manual or on PR merge. Intentional for now. |

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
