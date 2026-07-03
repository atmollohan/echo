# Cloudflare Tunnel — Echo Protocol

cloudflared runs as a **host systemd service** on the Raspberry Pi (not in
Docker). It proxies the Echo web UI at `localhost:8501`.

## Existing Setup

Check the current tunnel status:

```bash
sudo systemctl status cloudflared
cloudflared tunnel list
cloudflared tunnel info <tunnel-name>
```

The tunnel config is at `/etc/cloudflared/config.yml`. To add or verify the
Echo service, ensure it has an ingress rule pointing to `localhost:8501`:

```yaml
# /etc/cloudflared/config.yml
tunnel: <tunnel-id>
credentials-file: /etc/cloudflared/<tunnel-id>.json

ingress:
  - hostname: echo.mollo.tech
    service: http://localhost:8501
  - hostname: another-service.mollo.tech
    service: http://localhost:<port>
  - service: http_status:404
```

After editing:

```bash
sudo systemctl restart cloudflared
```

## Add Echo to an Existing Tunnel

If the tunnel already exists for other services, just add an ingress entry:

```bash
sudo cloudflared tunnel config validate
sudo systemctl restart cloudflared
```

Then in the Cloudflare Zero Trust dashboard, add a public hostname:
- Subdomain: `echo`
- Domain: `mollo.tech`
- Type: `HTTP`
- URL: `http://localhost:8501`

## Verify

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

## Resources

- [Cloudflare Tunnel docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)
