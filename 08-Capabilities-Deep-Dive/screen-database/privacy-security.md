# Screen Database -- Privacy & Security

> **Status:** Research | **Last Updated:** 2026-02-26
> **Depends on:** [Windows Capture Pipeline](windows-capture-pipeline.md), [Data Privacy](../../09-Legal-Compliance/data-privacy.md)

---

## 1. The Privacy Challenge

Continuous screen capture records everything the user sees, including:
- Banking and financial interfaces
- Password managers and login screens
- Private messages and emails from other people
- Medical and health information
- Legal documents
- Personal photos and content

Without proper safeguards, the screen database becomes a comprehensive surveillance record of the user's digital life.

---

## 2. Privacy Overlay (Application Exclusion)

### 2.1 Excluded Applications

The capture service skips screenshots when the active window matches excluded patterns:

```python
EXCLUDED_APPS = {
    # Password managers
    "1Password", "Bitwarden", "KeePass", "LastPass", "Dashlane",

    # Banking
    "Chase", "Wells Fargo", "Bank of America", "Capital One",
    "Schwab", "Fidelity", "Vanguard", "PayPal",

    # Medical
    "MyChart", "HealthVault",

    # System security
    "Windows Security", "Credential Manager",
}

EXCLUDED_TITLE_PATTERNS = [
    r"password",
    r"credential",
    r"sign.?in",
    r"log.?in",
    r"private.?browsing",
    r"incognito",
    r"bank",
    r"account.?balance",
    r"credit.?card",
    r"social.?security",
    r"SSN",
]
```

### 2.2 Browser Privacy Mode Detection

Skip capture when the browser is in private/incognito mode:

```python
def is_private_browsing(window_title: str) -> bool:
    """Detect private browsing mode from window title."""
    private_indicators = [
        "InPrivate",           # Edge
        "Incognito",           # Chrome
        "Private Browsing",    # Firefox
    ]
    return any(ind.lower() in window_title.lower() for ind in private_indicators)
```

### 2.3 User-Configurable Exclusions

```yaml
# screen_capture_config.yaml
exclusions:
  apps:
    - "1Password"
    - "Banking*"       # Wildcard matching
  title_patterns:
    - "password"
    - "sign in"
  urls:                # If browser tab title contains URL
    - "*.bank.com"
    - "paypal.com"
  always_skip_private: true  # Skip private/incognito browsing
```

---

## 3. Pause / Resume / Delete Controls

### 3.1 System Tray Controls (Windows)

The capture service runs with a system tray icon providing quick controls:

| Action | Method |
|--------|--------|
| **Pause** | Click tray icon > "Pause capture" or keyboard shortcut (Ctrl+Alt+P) |
| **Resume** | Click tray icon > "Resume capture" |
| **Delete last N minutes** | Click tray icon > "Delete last 30 min" |
| **Delete all today** | Click tray icon > "Delete today's captures" |
| **Delete everything** | Settings > "Delete all capture data" |
| **View status** | Tray icon shows green (active) / red (paused) / gray (excluded app) |

### 3.2 Telegram Controls

The user can control the capture service via Telegram commands to the OpenClaw agent:

```
/screen pause         -- Pause capture
/screen resume        -- Resume capture
/screen delete 30m    -- Delete last 30 minutes of captures
/screen delete today  -- Delete today's captures
/screen status        -- Show capture status
```

---

## 4. Encryption

### 4.1 At Rest (Windows)

```python
# Encrypt the local SQLite database using SQLCipher
# pip install pysqlcipher3

import pysqlcipher3.dbapi2 as sqlcipher

conn = sqlcipher.connect(DB_PATH)
conn.execute(f"PRAGMA key='{ENCRYPTION_KEY}'")
```

Alternatively, use Windows BitLocker on the drive containing capture data.

### 4.2 In Transit

- **To Supabase:** HTTPS (TLS 1.3). No additional encryption needed.
- **To Mac Mini (if using Tailscale push):** WireGuard encryption via Tailscale. No additional encryption needed.

### 4.3 At Rest (Supabase)

Supabase encrypts data at rest by default (AES-256). Row-level security restricts access to the service role key.

---

## 5. Access Control

### 5.1 Supabase RLS

```sql
-- Only the OpenClaw service role can access screen captures
ALTER TABLE screen_captures ENABLE ROW LEVEL SECURITY;

-- No public access
CREATE POLICY "No public access to screen captures"
    ON screen_captures FOR ALL
    USING (false);

-- Service role bypasses RLS (used by OpenClaw)
-- This is the default behavior with service_role key
```

### 5.2 Agent Access Rules

The OpenClaw agent should only access screen capture data when:
1. The user explicitly asks a recall question
2. Generating context for a proactive check-in (metadata only, not full OCR text)
3. Building a daily activity summary

The agent should NOT:
- Proactively analyze screen captures for patterns without user request
- Share screen capture data with external services
- Include screen capture text in messages to other people

---

## 6. Data Minimization

| Principle | Implementation |
|-----------|---------------|
| Capture only what is needed | Skip idle screens (change detection) |
| Store minimal data remotely | OCR text + metadata in Supabase; images stay local |
| Retain for limited time | 30 days raw images, 90 days OCR text |
| Summarize and discard | Daily AI summaries replace raw captures after retention period |
| User controls deletion | Pause, delete, and clear controls always available |

---

## 7. Legal Considerations

### 7.1 Your Own Screen

Capturing your own screen is legal. No consent from others is needed because you are recording your own device activity.

### 7.2 Content from Others

If the screen shows messages, emails, or documents from other people:
- This content is incidentally captured, not targeted
- Treat with the same care as iMessage data (see [iMessage Privacy](../../07-Channel-Setup/imessage/privacy-considerations.md))
- Do not extract or store other people's personal information from screen captures
- Do not use screen captures to build contact lists or marketing data

### 7.3 Work Environment

If the Windows desktop is used for client work:
- Client confidential information may appear in captures
- Consider pausing capture during sensitive client work
- Client data in captures should follow the same retention and deletion policies as other client data

---

## 8. Security Checklist

- [ ] Excluded apps list configured (password managers, banking, medical)
- [ ] Private browsing detection enabled
- [ ] User-configurable exclusion patterns set
- [ ] System tray pause/resume controls working
- [ ] Telegram /screen commands configured
- [ ] Local database encrypted (SQLCipher or BitLocker)
- [ ] Supabase RLS enabled on screen_captures table
- [ ] Retention policy configured (30 days images, 90 days text)
- [ ] Daily summary generation running
- [ ] Delete controls tested (delete last 30 min, today, all)
- [ ] Agent access restricted to explicit queries and check-in metadata

---

## Next Steps

- [Windows Capture Pipeline](windows-capture-pipeline.md) -- implementation
- [Data Privacy](../../09-Legal-Compliance/data-privacy.md) -- broader privacy framework
- [Tool Comparison](tool-comparison.md) -- alternative tools evaluated
