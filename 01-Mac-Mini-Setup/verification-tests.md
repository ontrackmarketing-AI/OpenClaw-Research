# Verification Tests for OpenClaw Installation

## Overview

After completing the OpenClaw setup on your Mac Mini M4, run through this verification
sequence to confirm everything works. Each test includes the command to run, expected output,
and troubleshooting steps if it fails.

Run these tests in order -- later tests depend on earlier ones passing.

---

## Pre-Flight Checks

Before testing OpenClaw itself, verify the supporting infrastructure.

### Test 0.1: Ollama Service Running

```bash
curl -s http://localhost:11434/api/tags | jq .
```

**Expected output:**

```json
{
  "models": [
    {
      "name": "qwen3:14b",
      "model": "qwen3:14b",
      "size": 9000000000,
      ...
    }
  ]
}
```

**If it fails:**
- `Connection refused`: Ollama is not running.
  - Fix: `brew services start ollama` or `ollama serve &`
- Empty models list: No models pulled yet.
  - Fix: `ollama pull qwen3:14b`
- Command not found (jq): `brew install jq`

### Test 0.2: Ollama Model List

```bash
ollama list
```

**Expected output:**

```
NAME                 ID              SIZE      MODIFIED
qwen3:14b           abcdef123456    8.5 GB    2 days ago
deepseek-r1:14b     789012ghijkl    9.0 GB    2 days ago
nomic-embed-text    mnopqr345678    274 MB    2 days ago
```

**If it fails:**
- No models listed: Pull your models first (see [ollama-local-models.md](ollama-local-models.md))

### Test 0.3: Ollama Generation Test

```bash
curl -s http://localhost:11434/api/generate -d '{
  "model": "qwen3:14b",
  "prompt": "Respond with exactly: OLLAMA_OK",
  "stream": false
}' | jq -r '.response'
```

**Expected output:**

```
OLLAMA_OK
```

(The model may add slight variations, but you should see a coherent response.)

**If it fails:**
- `model not found`: The specified model is not pulled. Run `ollama pull qwen3:14b`.
- Timeout or hang: The model may be loading for the first time (can take 10-30 seconds for
  14B models). Wait and retry.
- Out of memory: The model is too large for your available RAM. Check `memory_pressure` and
  try a smaller model.

### Test 0.4: Docker Running (Docker Installation Only)

```bash
docker info > /dev/null 2>&1 && echo "Docker: OK" || echo "Docker: NOT RUNNING"
```

**Expected output:**

```
Docker: OK
```

**If it fails:**
- Docker Desktop may not be running. Open it from Applications.
- After installing Docker Desktop, you may need to accept the license agreement.

---

## Stage 1: OpenClaw Gateway Health

### Test 1.1: Gateway Health Endpoint

This is the most fundamental check. The `/health` endpoint confirms the Gateway WebSocket
server is running and responsive.

```bash
curl -s http://localhost:18789/health | jq .
```

**Expected output:**

```json
{
  "status": "ok",
  "version": "1.5.2",
  "uptime": 3600,
  "timestamp": "2026-02-05T12:00:00.000Z"
}
```

Key fields to verify:
- `status` is `"ok"`
- `version` shows the expected OpenClaw version
- `uptime` is a positive number (seconds since start)

**If it fails:**
- `Connection refused`:
  - OpenClaw is not running.
  - Docker: `docker compose ps` to check container status. Then `docker compose logs openclaw` for errors.
  - Native: `pm2 status` or check if the process is running.
- `Connection reset`:
  - OpenClaw is starting up. Wait 10-15 seconds and retry.
  - Check logs for startup errors.
- Wrong port:
  - Verify `OPENCLAW_PORT` in your `.env` matches the port you are testing.
  - Docker: Verify port mapping in `docker-compose.yml` (`18789:18789`).

### Test 1.2: Gateway Health with Auth Token (If Configured)

If you set `OPENCLAW_AUTH_TOKEN` in your `.env`:

```bash
curl -s -H "Authorization: Bearer YOUR_AUTH_TOKEN_HERE" http://localhost:18789/health | jq .
```

**Expected:** Same output as Test 1.1.

**If it fails with 401 Unauthorized:**
- Your token does not match. Verify it matches exactly what is in `.env`.
- Check for trailing whitespace or newlines in the token.

---

## Stage 2: WebSocket Connection

The Gateway primarily operates over WebSocket. Test that WS connections work.

### Test 2.1: WebSocket Connection with websocat

Install websocat (WebSocket command-line client):

```bash
brew install websocat
```

Test the connection:

```bash
# Basic WebSocket connection test
echo '{"type":"ping"}' | websocat ws://localhost:18789 --one-message
```

**Expected output:**

```json
{"type":"pong","timestamp":"2026-02-05T12:00:00.000Z"}
```

**If it fails:**
- `Connection refused`: Same troubleshooting as Test 1.1.
- `WebSocket upgrade failed`: The server is running but WebSocket handshake fails. Check logs.
- Timeout: Firewall may be blocking. Check macOS firewall settings.

### Test 2.2: WebSocket Connection with Node.js

If websocat is not available, use a quick Node.js script:

```bash
node -e "
const WebSocket = require('ws');
const ws = new WebSocket('ws://localhost:18789');
ws.on('open', () => {
  console.log('WebSocket: CONNECTED');
  ws.send(JSON.stringify({type: 'ping'}));
});
ws.on('message', (data) => {
  console.log('Response:', data.toString());
  ws.close();
});
ws.on('error', (err) => {
  console.error('WebSocket: FAILED -', err.message);
  process.exit(1);
});
setTimeout(() => {
  console.error('WebSocket: TIMEOUT');
  process.exit(1);
}, 5000);
"
```

> **Note:** This requires the `ws` package. If not installed globally:
> `npm install -g ws` or `npx -y ws` -- alternatively you can create a temp script file with
> a local install.

---

## Stage 3: LLM Connectivity

Verify that OpenClaw can communicate with at least one LLM provider.

### Test 3.1: Ollama via OpenClaw

Send a test message through OpenClaw that triggers an LLM call:

```bash
curl -s -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Respond with exactly the word: VERIFIED",
    "model": "ollama/qwen3:14b"
  }' | jq .
```

**Expected output:**

```json
{
  "response": "VERIFIED",
  "model": "ollama/qwen3:14b",
  "tokens_used": {
    "prompt": 15,
    "completion": 2
  }
}
```

(The exact format depends on OpenClaw's API design. The key is getting a coherent response.)

**If it fails:**
- `model not found` or `provider not configured`: Check `OLLAMA_BASE_URL` in `.env`.
- Docker: Verify `host.docker.internal` resolves:
  ```bash
  docker exec openclaw-gateway curl -s http://host.docker.internal:11434/api/tags
  ```
- Timeout: Ollama may be loading the model. First inference after model load takes longer.

### Test 3.2: Cloud LLM Provider (If Configured)

If you have an Anthropic or OpenAI key configured:

```bash
# Test Anthropic Claude
curl -s -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Respond with exactly the word: VERIFIED",
    "model": "anthropic/claude-sonnet-4-20250514"
  }' | jq .

# Test OpenAI
curl -s -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Respond with exactly the word: VERIFIED",
    "model": "openai/gpt-4o"
  }' | jq .
```

**If it fails:**
- `API key invalid`: Double-check the key in `.env`. Ensure no extra whitespace.
- `Rate limited`: You have hit the provider's rate limit. Wait and retry.
- `Connection error`: Check internet connectivity from the Mac Mini.

---

## Stage 4: Memory System

Verify that OpenClaw can write to and read from its memory store.

### Test 4.1: Write to Memory

```bash
curl -s -X POST http://localhost:18789/api/memory \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Verification test entry created at '"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'",
    "metadata": {
      "source": "verification-test",
      "test_id": "mem-001"
    }
  }' | jq .
```

**Expected output:**

```json
{
  "success": true,
  "id": "mem_xxxxxxxxxxxx"
}
```

### Test 4.2: Read from Memory

```bash
curl -s -X GET "http://localhost:18789/api/memory/search?query=verification+test" \
  -H "Content-Type: application/json" | jq .
```

**Expected output:**

```json
{
  "results": [
    {
      "id": "mem_xxxxxxxxxxxx",
      "content": "Verification test entry created at 2026-02-05T12:00:00Z",
      "metadata": {
        "source": "verification-test",
        "test_id": "mem-001"
      },
      "relevance": 0.95
    }
  ]
}
```

**If it fails:**
- `SQLite error`: Check that `OPENCLAW_MEMORY_DIR` exists and is writable.
  ```bash
  # Native
  ls -la ~/.openclaw/memory/

  # Docker
  docker exec openclaw-gateway ls -la /app/data/memory/
  ```
- `Permission denied`: Fix directory permissions.
  ```bash
  chmod 755 ~/.openclaw/memory
  ```
- Empty results on search: Memory was written but search index may not be built. Check if
  the embedding model is configured (`nomic-embed-text` for Ollama or an API embedding model).

### Test 4.3: Verify SQLite Database

```bash
# Native
sqlite3 ~/.openclaw/memory/openclaw.db "SELECT COUNT(*) FROM memory;"

# Docker
docker exec openclaw-gateway sqlite3 /app/data/memory/openclaw.db "SELECT COUNT(*) FROM memory;"
```

**Expected:** A number greater than 0 (at least the test entry from 4.1).

---

## Stage 5: Skill Loading

### Test 5.1: List Loaded Skills

```bash
curl -s http://localhost:18789/api/skills | jq '.skills | length'
```

**Expected output:** A number greater than 0, indicating built-in skills are loaded.

### Test 5.2: Detailed Skill List

```bash
curl -s http://localhost:18789/api/skills | jq '.skills[] | .name'
```

**Expected output (example):**

```
"web-search"
"web-browse"
"code-execute"
"file-read"
"file-write"
"memory-store"
"memory-recall"
```

**If it fails:**
- Empty skills list: Check `OPENCLAW_SKILLS_DIR` and verify skill files exist.
- Specific skill missing: That skill may require additional configuration (API key, etc.).

---

## Stage 6: Web UI

### Test 6.1: Web UI Accessible

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
```

**Expected output:**

```
200
```

### Test 6.2: Web UI from Browser

Open in a browser on any device on the same network:

```
http://<mac-mini-ip>:3000
```

For example: `http://192.168.1.100:3000`

**Expected:** The OpenClaw Web UI loads with a chat interface.

**If it fails:**
- `Connection refused`: Web UI may not be enabled or is on a different port.
  - Check `OPENCLAW_WEB_UI_ENABLED` in `.env`.
  - Check Docker port mapping includes `3000:3000`.
- Cannot access from another device: Firewall is blocking.
  - Verify macOS firewall allows connections on port 3000.
  - Verify both devices are on the same network.

---

## Stage 7: Docker-Specific Checks (Docker Installation Only)

### Test 7.1: Container Status

```bash
docker compose -f ~/openclaw/docker-compose.yml ps
```

**Expected output:**

```
NAME                STATUS              PORTS
openclaw-gateway    Up 2 hours (healthy)   0.0.0.0:18789->18789/tcp, 0.0.0.0:3000->3000/tcp
openclaw-redis      Up 2 hours (healthy)   0.0.0.0:6379->6379/tcp
```

Key checks:
- Status shows "Up" (not "Restarting" or "Exited")
- Health shows "(healthy)" not "(unhealthy)" or "(starting)"
- Ports are mapped correctly

### Test 7.2: Container Logs (No Errors)

```bash
docker compose -f ~/openclaw/docker-compose.yml logs --tail 50 openclaw 2>&1 | grep -i "error\|fatal\|exception"
```

**Expected:** No output (no errors in the last 50 lines).

**If errors appear:** Read the full log context:

```bash
docker compose -f ~/openclaw/docker-compose.yml logs --tail 100 openclaw
```

### Test 7.3: Container Resource Usage

```bash
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" | grep openclaw
```

**Expected:**

```
openclaw-gateway    0.50%     150MiB / 4GiB     1.2MB / 500kB
openclaw-redis      0.10%     5MiB / 256MiB     100kB / 50kB
```

Check that memory usage is reasonable and CPU is low at idle.

### Test 7.4: Docker-to-Ollama Connectivity

```bash
docker exec openclaw-gateway curl -s http://host.docker.internal:11434/api/tags | head -c 200
```

**Expected:** JSON response listing Ollama models.

**If it fails:**
- `Could not resolve host`: The `extra_hosts` entry in `docker-compose.yml` may be missing.
- `Connection refused`: Ollama is not running on the host, or it is bound to `127.0.0.1` only.
  Ensure Ollama listens on all interfaces:
  ```bash
  OLLAMA_HOST=0.0.0.0 ollama serve
  ```

---

## Stage 8: Network Verification

### Test 8.1: Port Accessibility from Local Machine

```bash
lsof -i :18789 -P -n | head -5
lsof -i :3000 -P -n | head -5
lsof -i :11434 -P -n | head -5
```

**Expected:** Each command shows a LISTEN entry for the respective service.

### Test 8.2: Port Accessibility from Another Device

From your main workstation or another device on the same network:

```bash
# Replace with your Mac Mini's IP
curl -s http://192.168.1.100:18789/health | jq .
curl -s http://192.168.1.100:3000 -o /dev/null -w "%{http_code}\n"
```

**Expected:**
- Health endpoint returns JSON with `"status": "ok"`
- Web UI returns HTTP 200

**If it fails from another device but works locally:**
- macOS firewall is blocking incoming connections
- Router firewall or AP isolation is enabled
- The Mac Mini is on a different subnet/VLAN

### Test 8.3: Find Your Mac Mini's IP

```bash
# On the Mac Mini
ifconfig en0 | grep "inet " | awk '{print $2}'
# or
ipconfig getifaddr en0
```

---

## Complete Health Check Script

Save this as `~/verify-openclaw.sh` and run it after installation or any configuration change:

```bash
#!/bin/bash
# =============================================================================
# OpenClaw Complete Verification Script
# Run after installation or configuration changes
# =============================================================================

PASS=0
FAIL=0
WARN=0

check() {
  local name="$1"
  local result="$2"
  local expected="$3"

  if [ "$result" = "$expected" ]; then
    echo "[PASS] $name"
    PASS=$((PASS + 1))
  else
    echo "[FAIL] $name (got: $result, expected: $expected)"
    FAIL=$((FAIL + 1))
  fi
}

warn() {
  echo "[WARN] $1"
  WARN=$((WARN + 1))
}

echo "============================================="
echo " OpenClaw Verification Suite"
echo " $(date)"
echo "============================================="
echo ""

# --- Ollama ---
echo "--- Ollama ---"
OLLAMA_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:11434/api/tags 2>/dev/null)
check "Ollama API responding" "$OLLAMA_STATUS" "200"

OLLAMA_MODELS=$(curl -s http://localhost:11434/api/tags 2>/dev/null | jq -r '.models | length' 2>/dev/null)
if [ "$OLLAMA_MODELS" -gt 0 ] 2>/dev/null; then
  echo "[PASS] Ollama has $OLLAMA_MODELS model(s) downloaded"
  PASS=$((PASS + 1))
else
  echo "[FAIL] Ollama has no models downloaded"
  FAIL=$((FAIL + 1))
fi

# --- Docker (if applicable) ---
echo ""
echo "--- Docker ---"
if command -v docker &> /dev/null; then
  DOCKER_STATUS=$(docker info > /dev/null 2>&1 && echo "running" || echo "stopped")
  check "Docker daemon" "$DOCKER_STATUS" "running"

  GW_STATUS=$(docker inspect --format='{{.State.Health.Status}}' openclaw-gateway 2>/dev/null || echo "not_found")
  if [ "$GW_STATUS" != "not_found" ]; then
    check "OpenClaw container health" "$GW_STATUS" "healthy"
  else
    warn "OpenClaw Docker container not found (skip if using native install)"
  fi
else
  warn "Docker not installed (skip if using native install)"
fi

# --- OpenClaw Gateway ---
echo ""
echo "--- OpenClaw Gateway ---"
GW_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:18789/health 2>/dev/null)
check "Gateway health endpoint" "$GW_HEALTH" "200"

GW_STATUS_JSON=$(curl -s http://localhost:18789/health 2>/dev/null | jq -r '.status' 2>/dev/null)
check "Gateway status" "$GW_STATUS_JSON" "ok"

# --- Web UI ---
echo ""
echo "--- Web UI ---"
WEBUI_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null)
check "Web UI accessible" "$WEBUI_STATUS" "200"

# --- Ports ---
echo ""
echo "--- Network Ports ---"
PORT_18789=$(lsof -i :18789 -P -n 2>/dev/null | grep LISTEN | head -1 | awk '{print "open"}')
check "Port 18789 (Gateway)" "${PORT_18789:-closed}" "open"

PORT_3000=$(lsof -i :3000 -P -n 2>/dev/null | grep LISTEN | head -1 | awk '{print "open"}')
check "Port 3000 (Web UI)" "${PORT_3000:-closed}" "open"

PORT_11434=$(lsof -i :11434 -P -n 2>/dev/null | grep LISTEN | head -1 | awk '{print "open"}')
check "Port 11434 (Ollama)" "${PORT_11434:-closed}" "open"

# --- Summary ---
echo ""
echo "============================================="
echo " Results: $PASS passed, $FAIL failed, $WARN warnings"
echo "============================================="

if [ "$FAIL" -gt 0 ]; then
  echo ""
  echo "Some tests failed. Review the output above and check:"
  echo "  - Service logs: docker compose logs / pm2 logs"
  echo "  - .env configuration"
  echo "  - Network/firewall settings"
  exit 1
else
  echo ""
  echo "All tests passed. OpenClaw is operational."
  exit 0
fi
```

Make it executable:

```bash
chmod +x ~/verify-openclaw.sh
```

Run it:

```bash
~/verify-openclaw.sh
```

**Expected final output:**

```
=============================================
 Results: 9 passed, 0 failed, 0 warnings
=============================================

All tests passed. OpenClaw is operational.
```

---

## Troubleshooting Quick Reference

| Symptom                                    | Likely Cause                         | Fix                                          |
|--------------------------------------------|--------------------------------------|----------------------------------------------|
| `Connection refused` on :18789             | OpenClaw not running                 | Start it: `docker compose up -d` or `pm2 start openclaw` |
| `Connection refused` on :11434             | Ollama not running                   | `brew services start ollama`                 |
| Health returns `unhealthy`                 | OpenClaw crashed or misconfigured    | Check logs for error details                 |
| WebSocket connects then drops              | Auth token mismatch                  | Verify `OPENCLAW_AUTH_TOKEN` matches client  |
| Ollama model loads slowly on first use     | Normal: model loading into RAM       | Wait 10-30s for first load; subsequent calls are fast |
| Memory search returns empty                | Embedding model not configured       | Set `OPENCLAW_EMBEDDING_MODEL` or pull `nomic-embed-text` |
| Cannot access from other devices           | macOS firewall blocking              | Add exception for ports 18789, 3000          |
| Docker container keeps restarting          | Config error or missing dependency   | `docker compose logs openclaw` for details   |
| `EACCES` permission error                  | File permission issue                | `chmod 755` on data directories              |
| High CPU at idle                           | Ollama model still loaded and processing | Check `ollama ps`; wait for idle timeout  |

---

## Next Steps

If all tests pass, your OpenClaw installation is verified and operational. Proceed to:

- Configuring your first agent and skills
- Setting up channel integrations (Telegram, Discord, Slack, etc.)
- Building custom skills for your specific use cases
- Setting up monitoring and alerting for production operation
