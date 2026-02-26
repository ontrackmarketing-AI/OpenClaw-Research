# Tailscale VPN for OpenClaw Access

> **Rule: NEVER expose OpenClaw to the public internet.** Not even "just for testing." Not even "just the webhook endpoint." The web UI, the gateway, and the API should be accessible only through a VPN. Tailscale is the recommended solution because it is free, fast, and trivially easy to set up.

---

## Why Not Public Internet?

OpenClaw's web UI and gateway provide full control over an AI agent that can execute shell commands, access your files, and call APIs with your credentials. Exposing this to the internet is equivalent to putting an SSH server with password "admin" on a public IP.

| Public Exposure Risk | What Happens |
|---|---|
| No authentication on gateway | Anyone can send commands to your agent |
| Brute force on web UI | Automated scanners find and attack open ports within minutes |
| Zero-day in OpenClaw | Attacker exploits vulnerability before patch is available |
| Session hijacking | Auth tokens intercepted on unsecured connections |
| Bot scanning | Shodan/Censys index your server within hours of exposure |

**Real-world timeline:** Security researchers have demonstrated that a new public-facing service is scanned by automated bots within 5-15 minutes of going live. OpenClaw would be found and probed almost immediately.

---

## Tailscale Overview

**What it is:** A mesh VPN built on WireGuard (the modern, fast, audited VPN protocol). It creates a private network (called a "tailnet") between your devices. Only devices on your tailnet can see each other.

**Why Tailscale (not alternatives):**

| Feature | Tailscale | WireGuard (manual) | OpenVPN | ZeroTier |
|---|---|---|---|---|
| Setup complexity | 2 minutes | 30-60 minutes | 60+ minutes | 10 minutes |
| NAT traversal | Automatic | Manual | Manual | Automatic |
| Key management | Automatic | Manual | Manual (CA setup) | Automatic |
| MagicDNS | Yes | No | No | No |
| ACLs | Yes (web UI) | iptables | Config files | Rules |
| Free tier | 100 devices | Free (self-hosted) | Free (self-hosted) | 25 devices |
| Performance overhead | Minimal (~1ms) | Minimal | Moderate | Minimal |
| Client platforms | All major | All major | All major | All major |

---

## Installation on Mac Mini

### Step 1: Install Tailscale

```bash
# Using Homebrew (recommended)
brew install --cask tailscale

# Or download from https://tailscale.com/download/mac
```

### Step 2: Start Tailscale and Log In

```bash
# Start the Tailscale service
# On macOS, Tailscale runs as a menu bar app after installation
# Click the Tailscale icon in the menu bar > "Log in"

# Or via command line:
sudo tailscale up
```

This opens a browser window to authenticate. Log in with your preferred identity provider (Google, Microsoft, GitHub, etc.).

### Step 3: Verify Connection

```bash
# Check Tailscale status
tailscale status

# Get your Tailscale IP
tailscale ip -4
# Example output: 100.64.x.x (this is your Mac Mini's Tailscale IP)

# Check connectivity
tailscale ping <your-other-device-name>
```

### Step 4: Note Your Mac Mini's Tailscale Address

After connecting, your Mac Mini gets:
- A Tailscale IP: `100.x.y.z` (stable, private)
- A MagicDNS name: `mac-mini.tailnet-name.ts.net` (human-readable)

---

## Setting Up Your Tailnet (Private Network)

### Device Enrollment

Every device that needs to access OpenClaw must be enrolled in your tailnet:

| Device | Purpose | How to Install |
|---|---|---|
| **Mac Mini** | Runs OpenClaw | `brew install --cask tailscale` |
| **Windows PC** | Primary workstation, access web UI | Download from tailscale.com/download/windows |
| **iPhone** | Mobile monitoring/approvals | App Store: "Tailscale" |
| **Android** | Mobile monitoring/approvals | Play Store: "Tailscale" |
| **iPad** (optional) | Tablet access | App Store: "Tailscale" |

### Connecting Your Windows PC

1. Download Tailscale from https://tailscale.com/download/windows
2. Install and run
3. Click "Log in" and use the SAME identity provider as your Mac Mini
4. Both devices now appear in your tailnet

**Test the connection:**
```powershell
# From Windows PC
ping mac-mini.tailnet-name.ts.net

# Or use the Tailscale IP
ping 100.x.y.z

# Access OpenClaw Web UI
# Open browser to: http://mac-mini.tailnet-name.ts.net:3000
```

### Connecting from Phone (iOS/Android)

1. Install "Tailscale" from your app store
2. Log in with the same identity provider
3. The VPN activates automatically
4. Access OpenClaw via `http://mac-mini.tailnet-name.ts.net:3000` in your phone's browser

**Mobile use cases:**
- Approve HITL requests while away from your desk
- Monitor agent activity
- Emergency stop if you get an alert
- Quick check on agent status

---

## ACL Configuration (Access Control Lists)

ACLs control which devices on your tailnet can access which ports. This is defense in depth -- even if someone gains access to your tailnet, they can only reach the services you explicitly allow.

### Access the ACL Editor

1. Go to https://login.tailscale.com/admin/acls
2. Edit the ACL policy file

### Recommended ACL Policy

```jsonc
{
  "acls": [
    // Allow your devices to access OpenClaw ports on the Mac Mini
    {
      "action": "accept",
      "src": ["autogroup:owner"],  // Your devices only
      "dst": [
        "mac-mini:3000",    // OpenClaw Web UI
        "mac-mini:18789"    // OpenClaw Gateway
      ]
    },
    // Allow SSH to Mac Mini for remote management
    {
      "action": "accept",
      "src": ["autogroup:owner"],
      "dst": ["mac-mini:22"]
    },
    // Block everything else by default
    // (Tailscale's default-deny policy handles this)
  ],

  // Tag definitions (useful if you add more devices later)
  "tagOwners": {
    "tag:server":    ["autogroup:owner"],
    "tag:workstation": ["autogroup:owner"]
  }
}
```

### What This ACL Does

| Source | Destination | Allowed? |
|---|---|---|
| Your Windows PC | Mac Mini port 3000 (Web UI) | YES |
| Your Windows PC | Mac Mini port 18789 (Gateway) | YES |
| Your Windows PC | Mac Mini port 22 (SSH) | YES |
| Your phone | Mac Mini port 3000 (Web UI) | YES |
| Random tailnet device | Mac Mini port 3000 | NO (if not tagged as owner) |
| Any device | Mac Mini port 5432 (Postgres) | NO (not in ACL) |
| Any device | Mac Mini port 8080 (anything else) | NO (not in ACL) |

---

## MagicDNS

MagicDNS gives every device on your tailnet a human-readable hostname. Instead of remembering `100.64.23.47`, you use `mac-mini.tailnet-name.ts.net`.

### Enable MagicDNS

1. Go to https://login.tailscale.com/admin/dns
2. Enable MagicDNS
3. Your devices are now addressable by name

### Using MagicDNS with OpenClaw

```
# Instead of:
http://100.64.23.47:3000

# Use:
http://mac-mini.your-tailnet.ts.net:3000
```

**Rename your Mac Mini** for clarity:
1. Go to https://login.tailscale.com/admin/machines
2. Click on your Mac Mini
3. Edit the machine name to something clear (e.g., "mac-mini" or "openclaw-server")

---

## Tailscale Funnel (For Webhooks Only)

**What it is:** Tailscale Funnel exposes a specific port on your device to the public internet through Tailscale's infrastructure. The traffic goes: Internet -> Tailscale servers -> Your device.

**When to use it:** ONLY if you need to receive webhooks from external services (GHL, n8n, Stripe) that cannot be routed through Tailscale.

**When NOT to use it:** Never for the OpenClaw web UI or gateway. Those should remain VPN-only.

### Setting Up Funnel for Webhooks

```bash
# Expose a specific port for incoming webhooks
# This creates a public HTTPS URL that routes to your local port
tailscale funnel --bg 8443

# Your webhook URL will be:
# https://mac-mini.tailnet-name.ts.net:8443
```

### Webhook Architecture with Funnel

```
External Service (GHL, n8n)
        |
        | HTTPS POST to webhook URL
        v
Tailscale Funnel (public endpoint)
        |
        | Encrypted tunnel
        v
Mac Mini port 8443
        |
        | Webhook handler validates signature
        v
OpenClaw processes the webhook
```

### Critical Funnel Security Rules

1. **NEVER Funnel the OpenClaw web UI (port 3000) or gateway (port 18789)**
2. Use a SEPARATE port for webhooks (e.g., 8443)
3. Run a lightweight webhook receiver that validates signatures before passing data to OpenClaw
4. Validate webhook signatures for every service:
   - GHL: Verify `X-Hook-Secret` header
   - n8n: Verify webhook authentication header
   - Stripe: Verify `Stripe-Signature` header
5. Rate-limit the webhook endpoint
6. Log all incoming webhook requests for auditing

### Disabling Funnel

```bash
# Stop exposing the port
tailscale funnel --bg 8443 off

# Verify it is off
tailscale funnel status
```

---

## Tailscale SSH (Remote Management)

Tailscale SSH lets you SSH into your Mac Mini without opening port 22 to any network. The SSH connection goes entirely through the Tailscale tunnel.

### Enable Tailscale SSH

```bash
# On the Mac Mini
sudo tailscale up --ssh
```

### Connect from Windows PC

```powershell
# Use Tailscale SSH (no port configuration needed)
ssh user@mac-mini.tailnet-name.ts.net

# Or use the Tailscale IP
ssh user@100.x.y.z
```

### Advantages Over Regular SSH

| Feature | Regular SSH | Tailscale SSH |
|---|---|---|
| Port 22 exposed | Yes (to at least your network) | No (goes through Tailscale tunnel) |
| Key management | Manual (ssh-keygen, authorized_keys) | Automatic (Tailscale identity) |
| Brute force risk | Yes (if port is accessible) | No (not publicly accessible) |
| Audit logging | Local logs only | Tailscale admin console |
| MFA | Configured separately | Inherits from Tailscale identity provider |

---

## Cost

| Plan | Devices | Cost | Sufficient for You? |
|---|---|---|---|
| **Personal (Free)** | Up to 100 devices, 3 users | $0/month | YES |
| Starter | Up to 10 users | $6/user/month | Only if multiple people need access |
| Premium | Advanced features | $18/user/month | Overkill for personal use |

**For your use case (one person, 3-5 devices), the free plan is more than sufficient.**

---

## Complete Setup Checklist

- [ ] Install Tailscale on Mac Mini: `brew install --cask tailscale`
- [ ] Log in and note the Mac Mini's Tailscale IP and MagicDNS name
- [ ] Install Tailscale on Windows PC
- [ ] Install Tailscale on phone
- [ ] Verify all devices appear in the Tailscale admin console
- [ ] Test connectivity: ping Mac Mini from Windows PC using MagicDNS name
- [ ] Configure ACLs to restrict port access (3000, 18789, 22 only)
- [ ] Enable MagicDNS for readable hostnames
- [ ] Rename Mac Mini in Tailscale admin for clarity
- [ ] Test accessing OpenClaw web UI via `http://mac-mini.ts-name.ts.net:3000`
- [ ] Enable Tailscale SSH for remote management
- [ ] (If needed) Set up Funnel for webhook endpoint only
- [ ] Verify Docker ports are bound to `127.0.0.1` (Tailscale handles remote access)

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Cannot ping Mac Mini from Windows PC | Check both devices are on the same tailnet; check Tailscale is running on both |
| Web UI loads but is slow | Tailscale adds minimal latency (~1ms); issue is likely OpenClaw itself |
| Funnel URL not working | Verify Funnel is enabled: `tailscale funnel status`; check HTTPS is required |
| MagicDNS name not resolving | Enable MagicDNS in admin console; restart Tailscale on client device |
| ACL blocking access | Check ACL policy; use `tailscale ping` to test connectivity; check port numbers |
| Tailscale disconnects on Mac Mini sleep | Disable sleep: System Settings > Energy Saver > Prevent automatic sleeping |
| Phone cannot connect | Ensure Tailscale VPN is active in phone settings; check it is the same account |
