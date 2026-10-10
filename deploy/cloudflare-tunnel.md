# Cloudflare Tunnel — Echo Protocol

On rpi3, cloudflared runs as a **host service** (one tunnel per device,
multiple domains each). `echo.mollo.tech` is added as another ingress on the
existing rpi3 tunnel and proxies to the Echo container at `localhost:8501`.

> Since Echo's deploy uses the host tunnel, no `TUNNEL_TOKEN` secret is needed.
> The tunnel config file and credentials live on the Pi itself.

## Add `echo.mollo.tech` to the rpi3 tunnel

On the Pi:

```bash
# 1. Route the hostname to the existing rpi3 tunnel (only needed if the DNS
#    route isn't already created — the dashboard can do this too)
cloudflared tunnel route dns <rpi3-tunnel-name> echo.mollo.tech

# 2. Add an ingress rule to the config file (path varies by setup —
#    e.g. ~/.cloudflared/config.yml or /etc/cloudflared/config.yml).
#    Insert BEFORE the catch-all entry:
#
#    ingress:
#      - hostname: echo.mollo.tech
#        service: http://localhost:8501
#      - hostname: <other-app>.mollo.tech
#        service: http://localhost:<port>
#      - service: http_status:404

# 3. Validate and restart
cloudflared tunnel ingress validate
sudo systemctl restart cloudflared
```

### Verify

```bash
# Tunnel process running
sudo systemctl status cloudflared
cloudflared tunnel list

# From anywhere
curl -s -o /dev/null -w "%{http_code}" https://echo.mollo.tech
# Should print 200
```

## Optional — Access Policies

Restrict access behind Cloudflare's authentication:

1. In **Zero Trust → Access → Applications**, add a self-hosted app
2. Set domain to `echo.mollo.tech`
3. Choose a policy (e.g. email-based, one-time PIN)
4. Users authenticate before reaching the Echo UI

## Why not a sidecar tunnel?

Earlier iterations of this repo considered a cloudflared sidecar container with
its own tunnel (`echo-tunnel`). That created a second tunnel on rpi3. The actual
homelab convention is **one tunnel per device with multiple domains**, so the
sidecar was removed — Echo uses the host tunnel instead and publishes
`127.0.0.1:8501` for it.

## Resources

- [Cloudflare Tunnel docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)