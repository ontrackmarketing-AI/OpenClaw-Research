# Network Security for OpenClaw

> Every open port is an attack surface. Every unencrypted connection is an opportunity for interception. Every unsecured webhook is an injection vector. This document covers how to lock down the network layer of your OpenClaw deployment on the Mac Mini.

---

## Port Configuration

### OpenClaw Default Ports

| Port | Service | Purpose | Exposure |
|---|---|---|---|
| **3000** | Web UI | Browser-based management interface | Local only (via Tailscale for remote) |
| **18789** | Gateway | API gateway for agent communication | Local only (via Tailscale for remote) |

### Docker Port Binding

**Always bind to `127.0.0.1` (localhost only), never to `0.0.0.0`:**

```yaml
# CORRECT: Only accessible from the Mac Mini itself (and via Tailscale)
ports:
  - "127.0.0.1:3000:3000"
  - "127.0.0.1:18789:18789"

# WRONG: Accessible from any device on your network (and possibly the internet)
ports:
  - "3000:3000"      # Implicitly binds to 0.0.0.0
  - "0.0.0.0:3000:3000"  # Explicitly binds to all interfaces
```

**Why this matters:** Binding to `0.0.0.0` means any device on your local network (and potentially the internet if your router has port forwarding) can reach the OpenClaw UI and gateway directly. Binding to `127.0.0.1` means only processes on the Mac Mini can connect -- Tailscale handles remote access securely.

### Verify Port Binding

```bash
# Check what ports are listening and on which interfaces
sudo lsof -i -P -n | grep LISTEN

# Look for:
# - 127.0.0.1:3000 (GOOD)
# - *:3000 or 0.0.0.0:3000 (BAD)

# Or use netstat
netstat -an | grep -E '3000|18789'
```

---

## macOS Firewall Configuration

### Enable the Built-in Firewall

The macOS firewall blocks incoming connections that are not authorized. This is a second layer of defense beyond Docker port binding.

**Via System Settings (GUI):**
1. Open System Settings (Apple menu > System Settings)
2. Go to Network > Firewall
3. Turn ON the firewall
4. Click "Options..."
5. Settings:
   - Block all incoming connections: OFF (this would block Tailscale)
   - Automatically allow built-in software: ON
   - Automatically allow signed software: ON
   - Stealth mode: ON (prevents your Mac from responding to ICMP pings and port scans from non-Tailscale sources)

**Via command line:**
```bash
# Enable firewall
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on

# Enable stealth mode (don't respond to pings/port scans)
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setstealthmode on

# Check status
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getstealthmode
```

### Firewall and Tailscale Interaction

Tailscale creates a virtual network interface (`utun` device on macOS). The macOS firewall applies to physical interfaces (Wi-Fi, Ethernet) but Tailscale traffic is already encrypted and authenticated before it reaches the firewall. You do not need to add special firewall rules for Tailscale.

**Result:**
- Local network traffic -> macOS firewall (blocks unauthorized incoming)
- Tailscale traffic -> WireGuard encryption -> Tailscale authentication -> reaches your services

---

## Disable mDNS/Bonjour (Network Discovery Prevention)

### What It Is

Bonjour (Apple's implementation of mDNS) broadcasts service availability on your local network. If OpenClaw registers a Bonjour service, any device on your local network can discover that OpenClaw is running and on which port.

### Why Disable It

If you are on a shared network (office, co-working space, even a home network with guests), Bonjour announces: "Hey, there's an OpenClaw instance on port 3000 at this IP!" This is an invitation for probing.

### How to Disable

```yaml
# In docker-compose.yml environment section
environment:
  - OPENCLAW_DISABLE_BONJOUR=1
```

**Verify Bonjour is not advertising OpenClaw:**
```bash
# List Bonjour services on the network
dns-sd -B _http._tcp local.

# If OpenClaw appears in the list, the Bonjour disable is not working.
# Check OpenClaw documentation for the correct environment variable name.
```

### System-Level mDNS (Optional, Aggressive)

If you want to disable mDNS entirely on the Mac Mini (prevents all Bonjour discovery, not just OpenClaw):

```bash
# Disable mDNS responder (CAUTION: breaks AirDrop, AirPlay, printer discovery)
sudo launchctl unload -w /System/Library/LaunchDaemons/com.apple.mDNSResponder.plist

# Re-enable if needed
sudo launchctl load -w /System/Library/LaunchDaemons/com.apple.mDNSResponder.plist
```

**Only do this if the Mac Mini is a dedicated server and you do not need AirDrop, AirPlay, or network printer discovery.**

---

## DNS Configuration

### Use Secure DNS Providers

Your Mac Mini's DNS queries reveal what domains it connects to. Using your ISP's DNS means your ISP can see every API call, every webhook destination, every website the agent browses.

**Recommended DNS providers:**

| Provider | Primary | Secondary | Features |
|---|---|---|---|
| **Cloudflare** | 1.1.1.1 | 1.0.0.1 | Fastest; privacy-focused; malware blocking on 1.1.1.2 |
| **Quad9** | 9.9.9.9 | 149.112.112.112 | Threat blocking; privacy-focused |
| **Google** | 8.8.8.8 | 8.8.4.4 | Reliable; fast; Google sees queries |

**Configure on macOS:**
1. System Settings > Network > Wi-Fi (or Ethernet) > Details > DNS
2. Remove existing DNS servers
3. Add: `1.1.1.1` and `1.0.0.1` (Cloudflare) or `9.9.9.9` and `149.112.112.112` (Quad9)

**Or via command line:**
```bash
# Set DNS for Wi-Fi interface
networksetup -setdnsservers Wi-Fi 1.1.1.1 1.0.0.1

# Set DNS for Ethernet interface
networksetup -setdnsservers "Ethernet" 1.1.1.1 1.0.0.1

# Verify
networksetup -getdnsservers Wi-Fi
```

### DNS over HTTPS (DoH) for Docker

Docker containers use the host's DNS by default. If you want encrypted DNS for containers:

```yaml
# In docker-compose.yml
services:
  openclaw:
    dns:
      - 1.1.1.1
      - 1.0.0.1
```

**Note:** This sends DNS queries in plaintext from the container to Cloudflare. For DNS over HTTPS, you would need a local DoH proxy (e.g., `cloudflared`) -- this is an advanced optimization and not required for most deployments.

---

## TLS/SSL: HTTPS for the Web UI

### Why HTTPS Matters (Even on a Private Network)

Without HTTPS:
- Login credentials sent in plaintext
- Session tokens visible to network sniffers
- Agent actions could be intercepted and modified (man-in-the-middle)

With HTTPS:
- All traffic encrypted end-to-end
- Credentials and tokens protected
- Tamper-proof connections

### Option 1: Tailscale HTTPS (Recommended -- Easiest)

Tailscale can provision free, valid TLS certificates for your devices automatically:

```bash
# Enable HTTPS certificates on Mac Mini
tailscale cert mac-mini.tailnet-name.ts.net

# This creates:
# - mac-mini.tailnet-name.ts.net.crt (certificate)
# - mac-mini.tailnet-name.ts.net.key (private key)
```

Configure OpenClaw or a reverse proxy to use these certificates:

```nginx
# If using nginx as a reverse proxy in front of OpenClaw
server {
    listen 443 ssl;
    server_name mac-mini.tailnet-name.ts.net;

    ssl_certificate     /path/to/mac-mini.tailnet-name.ts.net.crt;
    ssl_certificate_key /path/to/mac-mini.tailnet-name.ts.net.key;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Option 2: Self-Signed Certificate (Quick but Produces Browser Warnings)

```bash
# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout openclaw.key -out openclaw.crt \
  -subj "/CN=mac-mini.local"

# Trust the certificate on macOS (eliminates browser warnings)
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain openclaw.crt
```

### Option 3: Let's Encrypt via Tailscale Funnel

If you use Tailscale Funnel for webhooks, it automatically provides valid Let's Encrypt certificates for the Funnel endpoint. The web UI (non-Funnel) should use Tailscale HTTPS certificates separately.

---

## Rate Limiting

### Why Rate Limit

An attacker who gains access (or an agent in a loop) can overwhelm services by sending thousands of requests per second. Rate limiting prevents this.

### Gateway Rate Limiting

If OpenClaw supports rate limiting configuration:

```yaml
# Expected configuration (verify in OpenClaw docs)
gateway:
  rate_limit:
    requests_per_minute: 60      # Max 60 requests per minute
    requests_per_hour: 1000      # Max 1,000 requests per hour
    burst: 10                    # Allow bursts of 10 requests

    # Per-action limits
    actions:
      send_email:
        per_hour: 50             # Max 50 emails per hour
      clay_enrich:
        per_hour: 100            # Max 100 enrichments per hour
      ghl_api:
        per_minute: 30           # Max 30 GHL API calls per minute
```

### Reverse Proxy Rate Limiting (nginx)

If OpenClaw does not have built-in rate limiting, use nginx:

```nginx
# Define rate limit zones
limit_req_zone $binary_remote_addr zone=openclaw_ui:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=openclaw_api:10m rate=30r/s;

server {
    # Web UI rate limit
    location / {
        limit_req zone=openclaw_ui burst=20 nodelay;
        proxy_pass http://127.0.0.1:3000;
    }

    # API gateway rate limit
    location /api/ {
        limit_req zone=openclaw_api burst=50 nodelay;
        proxy_pass http://127.0.0.1:18789;
    }
}
```

---

## IP Allowlisting

### Only Allow Tailscale Connections

Since all legitimate access comes through Tailscale (100.x.y.z address range), you can block everything else.

**Using macOS pf (packet filter):**

```bash
# Create pf rules file
sudo nano /etc/pf.anchors/openclaw

# Add these rules:
# Block all incoming to OpenClaw ports
block in on en0 proto tcp to any port {3000, 18789}

# Allow only Tailscale subnet
pass in on utun* proto tcp to any port {3000, 18789}
```

**Simpler approach: Docker already handles this.** If ports are bound to `127.0.0.1`, only local traffic reaches them. Tailscale makes the Mac Mini's localhost-bound ports accessible to your other Tailscale devices via the Tailscale interface, which is separate from your physical network interface.

**Verification:**
```bash
# From a device NOT on your Tailscale network, try:
curl http://mac-mini-local-ip:3000
# Should fail / timeout

# From a device ON your Tailscale network, try:
curl http://mac-mini.tailnet-name.ts.net:3000
# Should succeed
```

**Important clarification:** When you bind Docker to `127.0.0.1:3000`, Tailscale does NOT automatically make this accessible to other Tailscale devices. You have two options:
1. Bind to `0.0.0.0:3000` and use macOS firewall + Tailscale ACLs to restrict access
2. Use Tailscale's `serve` feature to proxy Tailscale traffic to localhost:
```bash
tailscale serve --bg 3000
# Now accessible at https://mac-mini.tailnet-name.ts.net:443 via Tailscale only
```

Option 2 (Tailscale serve) is the most secure approach because the port never touches the physical network.

---

## Network Traffic Monitoring

### Little Snitch (Recommended for macOS)

Little Snitch monitors all outbound connections from your Mac Mini. This is critical for detecting if a compromised agent is sending data to unauthorized destinations.

**Why you want this:**
- See every connection OpenClaw makes
- Block unexpected outbound connections
- Get alerts when a new destination is contacted for the first time
- Create rules: allow connections to known APIs, block everything else

**Cost:** $59 one-time purchase. Worth it for a server running autonomous agents with access to your API keys.

**Configuration for OpenClaw:**

| Rule | Direction | Process | Destination | Action |
|---|---|---|---|---|
| Allow Anthropic API | Outbound | Docker/OpenClaw | api.anthropic.com | Allow |
| Allow GHL API | Outbound | Docker/OpenClaw | *.gohighlevel.com | Allow |
| Allow Clay API | Outbound | Docker/OpenClaw | api.clay.com | Allow |
| Allow Supabase | Outbound | Docker/OpenClaw | *.supabase.co | Allow |
| Allow Airtable | Outbound | Docker/OpenClaw | api.airtable.com | Allow |
| Allow Tailscale | Outbound | tailscaled | *.tailscale.com | Allow |
| Block all other | Outbound | Docker/OpenClaw | * | Deny + Alert |

### Free Alternative: macOS Activity Monitor + lsof

```bash
# See all network connections from Docker containers
sudo lsof -i -P -n | grep docker

# Watch connections in real-time
sudo watch -n 5 'lsof -i -P -n | grep docker'

# Check for connections to unexpected destinations
sudo lsof -i -P -n | grep docker | grep -v -E 'anthropic|gohighlevel|clay|supabase|airtable|tailscale'
# Any output here is suspicious and should be investigated
```

### Docker Network Monitoring

```bash
# See container network activity
docker stats openclaw

# Inspect container networking
docker inspect openclaw --format='{{json .NetworkSettings}}' | python3 -m json.tool

# Capture container traffic (advanced, requires tcpdump)
docker run --net=container:openclaw nicolaka/netshoot tcpdump -i any -w /tmp/capture.pcap
```

---

## Webhook Security

### The Problem

If you receive webhooks from external services (GHL, n8n, Stripe), you need a publicly-accessible endpoint. This is the ONE exception to the "never expose to the internet" rule. But it must be locked down.

### Webhook Architecture

```
External Service (GHL)
        |
        | HTTPS POST with signature header
        v
Tailscale Funnel (port 8443)
        |
        | Encrypted tunnel to Mac Mini
        v
Webhook Handler (validates signature)
        |
        | If valid: passes to OpenClaw
        | If invalid: logs and rejects (HTTP 403)
        v
OpenClaw processes the webhook
```

### Signature Validation by Service

**GHL Webhooks:**
```javascript
// Validate GHL webhook signature
const crypto = require('crypto');

function validateGHLWebhook(req) {
  const signature = req.headers['x-ghl-signature'];
  const payload = JSON.stringify(req.body);
  const expected = crypto
    .createHmac('sha256', process.env.GHL_WEBHOOK_SECRET)
    .update(payload)
    .digest('hex');
  return signature === expected;
}
```

**n8n Webhooks:**
```javascript
// Validate n8n webhook with shared secret
function validateN8nWebhook(req) {
  const authHeader = req.headers['authorization'];
  return authHeader === `Bearer ${process.env.N8N_WEBHOOK_SECRET}`;
}
```

**General Webhook Security Rules:**

1. **Always validate signatures** -- never process an unvalidated webhook
2. **Use HTTPS only** -- Tailscale Funnel provides this automatically
3. **Rate limit** the webhook endpoint (max 100 requests/minute)
4. **Log all incoming webhooks** (source IP, headers, payload hash -- NOT the full payload if it contains PII)
5. **Reject oversized payloads** (max 1MB or whatever is reasonable for your use case)
6. **Timeout** -- webhook processing should complete in under 30 seconds; queue long-running tasks
7. **Separate endpoint** -- use a dedicated port (8443) for webhooks, not the same port as the web UI

---

## Docker Network Isolation

### How Docker Networking Works

By default, Docker containers are on an isolated bridge network. They can reach the internet (for API calls) but cannot reach the host's localhost services or other containers on different networks.

```yaml
# Good: Custom bridge network (containers isolated from host)
networks:
  openclaw-net:
    driver: bridge

# Bad: Host networking (container shares host network stack)
# network_mode: host  # NEVER USE THIS
```

### Container-to-Container Communication

If OpenClaw needs to talk to other containers (e.g., a local database):

```yaml
services:
  openclaw:
    networks:
      - openclaw-net

  postgres:
    networks:
      - openclaw-net
    # Postgres is accessible ONLY from openclaw-net
    # It is NOT accessible from the host or the internet
    # No ports exposed outside Docker
```

### Preventing Container-to-Host Access

```yaml
# Additional Docker daemon configuration (/etc/docker/daemon.json)
{
  "icc": false,           # Disable inter-container communication (use links/networks explicitly)
  "userland-proxy": false  # Use iptables instead of userland proxy (more secure)
}
```

---

## Network Security Checklist

- [ ] Docker ports bound to `127.0.0.1` only (not `0.0.0.0`)
- [ ] macOS firewall enabled with stealth mode
- [ ] Bonjour/mDNS disabled for OpenClaw (`OPENCLAW_DISABLE_BONJOUR=1`)
- [ ] DNS configured to use `1.1.1.1` or `9.9.9.9`
- [ ] HTTPS configured for web UI (Tailscale cert or self-signed)
- [ ] Rate limiting configured on gateway or reverse proxy
- [ ] Tailscale ACLs restrict which devices can access OpenClaw ports
- [ ] Tailscale serve configured (if using localhost port binding)
- [ ] Webhook endpoint (if needed) uses Tailscale Funnel with signature validation
- [ ] Little Snitch installed (or equivalent monitoring)
- [ ] No host networking in Docker configuration
- [ ] Docker network mode is custom bridge (not default bridge, not host)
- [ ] Verified: cannot reach OpenClaw from non-Tailscale device
