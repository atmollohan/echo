# Cloudflare Tunnel — Echo Protocol

On rpi3, cloudflared runs as a **sidecar container** in the Echo compose stack
(not a host systemd service). It authenticates with a tunnel token and proxies
the Echo web UI over the compose network.

## Setup

1. In the Cloudflare Zero Trust dashboard, go to **Networks → Tunnels** and
   **Create a tunnel** (Cloudflared connector).
2. Copy the generated tunnel token.
3. Add a **public hostname** to the tunnel:
   - Subdomain: `echo`
   - Domain: `mollo.tech`
   - Type: `HTTP`
   - URL: `http://echo-protocol:8501`

   > Use the compose **service name** (`echo-protocol`), not `localhost`.
   > cloudflared runs in its own container, so `localhost` would resolve to the
   > tunnel container itself, not the Echo app.

4. Store the token:
   - **CI:** set repo secret `TUNNEL_TOKEN` (used by `deploy.yml` / `release.yml`)
   - **Manual:** write `TUNNEL_TOKEN=<token>` to `deploy/.env`

## Verify

Locally on the Pi:

```bash
docker ps --filter name=echo-tunnel --format '{{.Status}}'
docker logs echo-tunnel --tail 20
```

From anywhere:

```bash
curl -s -o /dev/null -w "%{http_code}" https://echo.mollo.tech
# Should print 200
```

## Optional — Access Policies

Restrict access behind Cloudflare's authentication:

1. In **Zero Trust → Access → Applications**, add a self-hosted app
2. Set domain to `echo.mollo.tech`
3. Choose a policy (e.g. email-based, one-time PIN)
4. Users authenticate before reaching the Echo UI

## Legacy note

Earlier deployments used a host-level `cloudflared` systemd service with
`/etc/cloudflared/config.yml`. That is **no longer the pattern** — Echo now uses
the sidecar token approach shared with the games server. If a host service still
exists on rpi3, disable it to avoid two connectors for the same tunnel:

```bash
sudo systemctl disable --now cloudflared
```

## Resources

- [Cloudflare Tunnel docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)
