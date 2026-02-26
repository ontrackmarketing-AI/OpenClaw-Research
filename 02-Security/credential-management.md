# Credential Management for OpenClaw

> **Principle: OpenClaw should have its own dedicated credentials with the absolute minimum permissions required.** Never give the agent your personal admin keys. If a key is compromised, the blast radius should be limited to one service at one privilege level -- not your entire business.

---

## Why Dedicated Credentials Matter

**Scenario without dedicated keys:**
You use your GHL agency-level API key for OpenClaw. An attacker extracts it via prompt injection. They now have access to every sub-account, every contact, every conversation across your entire agency.

**Scenario with dedicated keys:**
You create a sub-account-level GHL API key for OpenClaw that can only access one sub-account's contacts and conversations. An attacker extracts it. They have access to one sub-account only. You revoke the key and issue a new one. Downtime: minutes. Damage: contained.

---

## Service-by-Service Key Configuration

### GoHighLevel (GHL)

| Setting | Recommended Value | Why |
|---|---|---|
| **Key type** | Sub-account API key | Not agency-level; limits to one sub-account |
| **Permissions** | Contacts: read/write; Conversations: read/write; Opportunities: read/write | Only what the lead gen agent needs |
| **Excluded permissions** | Settings, Users, Integrations, Billing, Agency-level anything | Agent should not manage your GHL configuration |

**How to create:**
1. Log into GHL
2. Go to Settings > Business Profile > API (at the sub-account level)
3. Generate a new API key
4. Label it "OpenClaw Agent - [date created]"
5. Note the permissions granted
6. Set this as `GHL_API_KEY` in your `.env`

**What to monitor:**
- API call volume (if GHL provides usage stats)
- Unexpected contact list exports
- Messages sent outside of configured workflows

---

### Clay

| Setting | Recommended Value | Why |
|---|---|---|
| **Workspace** | Separate workspace for OpenClaw | Isolate from your main research workspace |
| **Budget** | Set monthly credit limit ($50-100 to start) | Prevent runaway enrichment costs |
| **API key** | Workspace-specific key | Not your personal account key |

**How to create:**
1. Create a new Clay workspace (e.g., "OpenClaw Automations")
2. Go to workspace Settings > API
3. Generate an API key for this workspace
4. Set a monthly credit limit on the workspace
5. Set this as `CLAY_API_KEY` in your `.env`

**What to monitor:**
- Daily credit consumption (set alerts if Clay supports them)
- Enrichment volume spikes
- Unusual enrichment targets (domains/companies you would never research)

---

### Supabase

| Setting | Recommended Value | Why |
|---|---|---|
| **Key type** | `anon` key (public) with Row Level Security | NEVER use `service_role` key for agents |
| **RLS policies** | Enabled on all tables | Agent can only access rows it is allowed to |
| **Dedicated role** | Create a custom Postgres role (e.g., `openclaw_agent`) | Fine-grained table/column permissions |

**CRITICAL: The `service_role` key bypasses ALL Row Level Security.** If the agent has this key, it can read, write, and delete every row in every table. This is equivalent to giving it `root` on your database.

**How to configure:**
1. Go to Supabase Dashboard > Settings > API
2. Copy the `anon` key (NOT `service_role`)
3. Set this as `SUPABASE_ANON_KEY` in your `.env`
4. Enable RLS on every table the agent accesses:
   ```sql
   -- Enable RLS
   ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

   -- Create a policy for the agent
   CREATE POLICY "openclaw_agent_access" ON leads
     FOR ALL
     USING (workspace_id = 'openclaw-workspace')
     WITH CHECK (workspace_id = 'openclaw-workspace');
   ```
5. For additional isolation, create a dedicated Postgres role:
   ```sql
   -- Create agent role with limited permissions
   CREATE ROLE openclaw_agent LOGIN PASSWORD 'strong-random-password';

   -- Grant only necessary table access
   GRANT SELECT, INSERT, UPDATE ON leads TO openclaw_agent;
   GRANT SELECT ON companies TO openclaw_agent;  -- Read-only for reference data
   -- Do NOT grant DELETE unless the agent must delete records
   -- Do NOT grant access to user tables, auth tables, or config tables
   ```

**What to monitor:**
- Query volume and patterns
- Any access to tables outside the agent's scope
- Large SELECT queries (potential data exfiltration)
- DELETE operations (should be rare or never)

---

### Claude API (Anthropic)

| Setting | Recommended Value | Why |
|---|---|---|
| **API key** | Separate key from your personal usage | Track agent spend separately |
| **Spend limit** | Monthly budget: $50-100 to start | Prevent runaway costs from loops |
| **Usage alerts** | Enable email alerts at 50% and 80% of budget | Early warning |

**How to create:**
1. Go to https://console.anthropic.com/settings/keys
2. Create a new API key labeled "OpenClaw Agent"
3. Go to Settings > Billing > Limits
4. Set a monthly spend limit for this key or your workspace
5. Enable usage alerts
6. Set this as `CLAUDE_API_KEY` in your `.env`

**What to monitor:**
- Daily token consumption
- Cost per day (set alerts for anomalies)
- Sudden spikes indicating loops or unexpected activity

---

### Airtable

| Setting | Recommended Value | Why |
|---|---|---|
| **Token type** | Personal Access Token (PAT) with scoped permissions | Not the deprecated API key |
| **Scopes** | `data.records:read` for reference bases; `data.records:write` only for bases the agent manages | Minimum necessary |
| **Base access** | Restrict to specific bases only | Agent cannot access your personal/other bases |

**How to create:**
1. Go to https://airtable.com/create/tokens
2. Create a new token labeled "OpenClaw Agent"
3. Under Scopes, select only:
   - `data.records:read` (always)
   - `data.records:write` (only for bases the agent must write to)
   - Do NOT add `schema:read`, `schema:write`, `user.email:read`, or any other scope
4. Under Access, select only the specific bases the agent needs
5. Set this as `AIRTABLE_API_KEY` in your `.env`

**What to monitor:**
- API rate limit usage
- Write operations to unexpected bases
- Bulk read operations (potential data export)

---

### Email Service (SendGrid/Mailgun/etc.)

| Setting | Recommended Value | Why |
|---|---|---|
| **API key** | Restricted key with "Mail Send" permission only | Cannot manage account, templates, or contacts |
| **Sending limits** | Set daily send limit (e.g., 100 emails/day) | Prevent mass email blast from rogue agent |
| **From address** | Dedicated sending address (e.g., `agent@yourdomain.com`) | Identify agent-sent emails; revoke without affecting your personal email |
| **Sandbox mode** | Enable during testing | Emails are validated but not actually delivered |

**What to monitor:**
- Daily send volume
- Bounce rates (sudden increase = agent sending to bad addresses)
- Content of sent emails (spot-check for hallucinated content)

---

## .env File Security

### File Structure

```bash
# .env -- OpenClaw Agent Credentials
# Created: [DATE]
# Last rotated: [DATE]
# NEVER commit this file to version control

# --- GoHighLevel ---
GHL_API_KEY=your-subaccount-key-here
GHL_LOCATION_ID=your-location-id

# --- Clay ---
CLAY_API_KEY=your-workspace-key-here

# --- Supabase ---
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
# SUPABASE_SERVICE_ROLE_KEY -- DO NOT SET THIS. Agent must not have this.

# --- Claude (Anthropic) ---
CLAUDE_API_KEY=sk-ant-your-key-here

# --- Airtable ---
AIRTABLE_API_KEY=pat-your-key-here

# --- Email ---
EMAIL_API_KEY=SG.your-sendgrid-key-here

# --- n8n (if applicable) ---
N8N_WEBHOOK_SECRET=your-webhook-secret-here
```

### File Permissions

```bash
# Set restrictive permissions (macOS)
chmod 600 .env

# Verify
ls -la .env
# Expected: -rw-------  1 youruser  staff  512 Jan 15 10:00 .env
# Only the owner can read or write this file.

# If using Git, ensure .env is ignored
echo ".env" >> .gitignore
echo ".env.*" >> .gitignore
echo "*.env" >> .gitignore
```

### What NEVER Goes in .env

- Your personal account passwords
- SSH private keys
- macOS Keychain passwords
- Database root/admin passwords
- Any key that has more permissions than the agent needs

---

## Secret Rotation Schedule

| Key | Rotation Frequency | Trigger for Immediate Rotation |
|---|---|---|
| GHL API Key | Monthly | Any suspected compromise; agent behavior anomaly |
| Clay API Key | Monthly | Credit usage anomaly |
| Supabase Anon Key | Quarterly | Database access anomaly |
| Claude API Key | Monthly | Usage spike; suspected extraction |
| Airtable PAT | Quarterly | Unexpected access patterns |
| Email API Key | Monthly | Deliverability issues; suspected spam sending |
| n8n Webhook Secret | Quarterly | Unauthorized webhook calls |

### Rotation Procedure

```bash
# 1. Generate new key in the service's dashboard (do NOT delete old key yet)

# 2. Update .env with new key
nano .env  # or your preferred editor

# 3. Restart OpenClaw to pick up new key
docker compose down && docker compose up -d

# 4. Verify agent works with new key (test a simple operation)

# 5. ONLY AFTER verification: revoke the old key in the service's dashboard

# 6. Update rotation log
echo "$(date): Rotated [SERVICE] API key" >> ~/.openclaw-key-rotation.log
```

**Critical:** Always create the new key BEFORE revoking the old one. If you revoke first and the new key has issues, you have zero working keys.

---

## Emergency Key Revocation Procedure

**When to execute:** You suspect any key has been compromised. Do not wait for confirmation. Revoke first, investigate later.

### Quick-Reference Revocation URLs

Save this list as a bookmark folder in your browser labeled "EMERGENCY - Key Revocation":

| Service | Revocation URL | Action |
|---|---|---|
| GHL | `https://app.gohighlevel.com` > Settings > API | Delete and regenerate key |
| Clay | `https://app.clay.com` > Settings > API | Delete and regenerate key |
| Supabase | `https://supabase.com/dashboard` > Settings > API | Regenerate keys (affects all apps using the project) |
| Claude | `https://console.anthropic.com/settings/keys` | Delete the compromised key |
| Airtable | `https://airtable.com/create/tokens` | Revoke the token |
| SendGrid | `https://app.sendgrid.com/settings/api_keys` | Delete the key |
| n8n | Your n8n instance settings | Rotate webhook secrets |

### Step-by-Step Emergency Response

```
MINUTE 0:  Stop OpenClaw immediately
            docker compose down

MINUTE 1:  Revoke ALL keys that the agent had access to
            (Yes, all of them. You cannot know which were extracted.)
            Use the URLs above.

MINUTE 5:  Check service dashboards for unauthorized activity
            - GHL: Check sent messages, contact exports
            - Clay: Check enrichment history
            - Supabase: Check recent queries
            - Claude: Check usage dashboard
            - Email: Check sent email logs

MINUTE 15: Generate new keys for each service
            Update .env with new keys

MINUTE 20: Investigate the incident
            - Review agent logs: docker logs openclaw > incident-logs.txt
            - Check for prompt injection in recent agent conversations
            - Check for modified skills or configurations
            - Check for unknown network connections

MINUTE 30: Restart OpenClaw with new keys (only if root cause identified)
            docker compose up -d

HOUR 1:    Full post-incident review
            - What was compromised?
            - How did it happen?
            - What data was accessed?
            - What changes are needed to prevent recurrence?
```

---

## Monitoring and Anomaly Detection

### Manual Monitoring Checklist (Weekly)

- [ ] Review Claude API usage dashboard -- any unexpected spikes?
- [ ] Check Clay credit balance -- consumption normal?
- [ ] Review GHL activity log -- any bulk operations you did not authorize?
- [ ] Check Supabase query logs -- any unusual patterns?
- [ ] Review email sending logs -- any unexpected recipients?
- [ ] Check Airtable activity -- any bulk reads or modifications?

### Automated Monitoring (If Available)

| Service | Monitoring Method |
|---|---|
| Claude API | Anthropic dashboard; set up spending alerts via console |
| Clay | Workspace credit alerts |
| Supabase | Enable Postgres logging; use Supabase dashboard > Logs |
| SendGrid | Activity feed; webhook alerts for bounces/complaints |
| GHL | API usage in account settings |
| All | Set up a simple daily script that checks `docker logs openclaw --since 24h` for error patterns |

### Anomaly Red Flags

| Signal | What It Might Mean |
|---|---|
| API costs 5x normal daily average | Agent in a loop; prompt injection causing excessive API calls |
| Large data export from Supabase | Data exfiltration attempt |
| Messages sent to contacts not in current workflow | Agent acting outside intended scope; possible prompt injection |
| Credential-related strings in agent output | Agent leaking keys (check logs immediately) |
| New outbound network connections to unknown IPs | Compromised agent calling home to attacker |
| Agent attempting to access `/etc/passwd`, `.ssh`, or `.env` | Active exploitation attempt |

---

## Vault Options (For Reference)

### 1Password CLI (Practical for Personal Use)

If you already use 1Password, you can inject secrets at runtime:

```bash
# Install 1Password CLI
brew install --cask 1password-cli

# Reference secrets in docker-compose.yml
# environment:
#   CLAUDE_API_KEY: op://vault-name/openclaw-claude/api-key
#   GHL_API_KEY: op://vault-name/openclaw-ghl/api-key

# Run with 1Password injection
op run --env-file=.env.1password -- docker compose up -d
```

**Pros:** Secrets never written to disk in plaintext; integrated with 1Password security model.
**Cons:** Adds complexity; requires 1Password subscription; `op` session can expire.

### HashiCorp Vault (Overkill for Personal Use)

Enterprise-grade secret management with automatic rotation, audit logging, and dynamic credentials.

**Verdict:** Unless you are running multiple agents or a team environment, HashiCorp Vault is unnecessary complexity. The `.env` + `chmod 600` + rotation schedule approach is sufficient for a single-user deployment.

---

## Summary: Credential Security Layers

```
Layer 1: DEDICATED KEYS (not your personal/admin keys)
    |
Layer 2: MINIMAL PERMISSIONS (read-only where possible; sub-account, not agency)
    |
Layer 3: SPEND LIMITS (hard caps on every metered service)
    |
Layer 4: FILE SECURITY (.env chmod 600; .gitignore; Docker secrets)
    |
Layer 5: ROTATION SCHEDULE (monthly for critical; quarterly for others)
    |
Layer 6: MONITORING (weekly manual review; automated alerts where available)
    |
Layer 7: EMERGENCY PROCEDURE (documented; bookmarked; practiced)
```

Every layer is independent. If one fails, the others still provide protection.
