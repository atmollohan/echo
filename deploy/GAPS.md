# Deployment Gaps — Echo Protocol

Known gaps and outstanding tasks for the rpi3 deployment. Keep this list current;
strike items when verified, add new ones as they surface.

Legend: 🔴 blocker · 🟠 action needed · 🟡 verify · 🟢 done

## External / configuration

| # | Status | Gap | Notes / next step |
|---|--------|-----|-------------------|
| 1 | 🟠 | **Cloudflare tunnel + hostname do not exist yet** | `echo.mollo.tech` is not listed in Cloudflare. Create a tunnel + public hostname targeting `http://echo-protocol:8501`, then copy the token. See `cloudflare-tunnel.md`. |
| 2 | 🟠 | **Repo secrets unverified** | Workflows now require `TAILSCALE_AUTHKEY`, `GHCR_PAT`, `TUNNEL_TOKEN` on `atmollohan/echo`. The old `TS_OAUTH_CLIENT_ID` / `TS_OAUTH_SECRET` are no longer used. Confirm the three secrets exist. |
| 3 | 🟡 | **rpi3 Tailscale node + ACL** | Deploy assumes `mollopi5@rpi3` is reachable over Tailscale and that the CI tag is allowed by the ACL. Not verifiable from WSL (tailscaled not running). Confirm with `tailscale status` on a Tailnet host. |
| 4 | 🟡 | **GHCR package visibility** | README implies `ghcr.io/atmollohan/echo` is public. If it is private, the `GHCR_PAT` login is required (now wired) and the PAT needs `read:packages`. |
| 5 | 🟡 | **Stale host cloudflared on rpi3** | Earlier design used a host systemd `cloudflared`. If it still exists, disable it to avoid two connectors for the same tunnel: `sudo systemctl disable --now cloudflared`. |

## Code / compose

| # | Status | Gap | Notes / next step |
|---|--------|-----|-------------------|
| 6 | 🟡 | **Port published on all interfaces** | Compose uses `8501:8501`, exposing the UI on the LAN. Consider `127.0.0.1:8501:8501` — the sidecar reaches the app via the compose network, so a host bind is only needed for debugging. |
| 7 | 🟡 | **Pi 3 resource headroom** | rpi3 already runs the games server. Echo's image (Streamlit + Jupyter + papermill + matplotlib) is heavy for a 1 GB Pi 3. Watch memory; move to rpi5 if OOM/slow. |
| 8 | 🟠 | **`release.yml` deploys `:latest`** | The release builds `:latest` *and* `:vX.Y.Z`, but the deploy step pulls `:latest`. Decide whether deploys should pin the release tag instead. |
| 9 | 🟢 | **Output volume path** | Verified: app writes to `PROJECT_ROOT/generated` = `/app/generated`, which matches the `echo-data` volume mount. |

## Inherited from the shared pattern

| # | Status | Gap | Notes / next step |
|---|--------|-----|-------------------|
| 10 | 🟠 | **`sed` delimiter bug in the games workflow** | `games/.github/workflows/deploy.yml` uses `sed 's/MAG_PLACEHOLDER/<ghcr.io/...>/g'`; the slash in the image name makes sed fail (`unknown option to 's'`). Echo avoids this with `s\|...\|...\|g`. Consider fixing upstream in `games`. |
| 11 | 🟡 | **CI/CD not auto-deploy on push** | Same as the games `PLAN`/`GAPS`: push builds the image but does not auto-deploy; deploy is manual or on PR merge. Intentional for now. |

## Verification checklist (once on rpi3)

```bash
# Containers up
docker ps --filter name=echo --format '{{.Names}} {{.Status}}'

# App responds locally
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8501          # 200
curl -s http://localhost:8501/_stcore/health                            # ok

# Tunnel connected
docker logs echo-tunnel --tail 20

# Public hostname (after tunnel created)
curl -s -o /dev/null -w '%{http_code}\n' https://echo.mollo.tech        # 200
```
