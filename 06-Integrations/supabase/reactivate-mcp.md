# Supabase Reactivation Guide

> Steps to reactivate your paused Supabase project and reconnect it to OpenClaw.

---

## Your Supabase Project

| Property | Value |
|---|---|
| **Project ID** | `jitawzicdwgbhatvjblh` |
| **Project URL** | `https://jitawzicdwgbhatvjblh.supabase.co` |
| **Status** | Disabled (project paused) |
| **MCP Status** | Was configured in Claude Code, currently non-functional |
| **Existing Skill** | `supabase-ops` Claude Code slash command |
| **Database** | PostgreSQL 15 (standard Supabase) |

---

## Reactivation Steps

### Step 1: Log into Supabase Dashboard

1. Go to [https://supabase.com/dashboard](https://supabase.com/dashboard)
2. Log in with your account credentials
3. You should see your project `jitawzicdwgbhatvjblh` listed as "Paused"

### Step 2: Reactivate the Project

1. Click on the paused project
2. You will see a banner or prompt saying the project is paused
3. Click **"Restore Project"** or **"Reactivate"**
4. Confirm any billing acknowledgment (free tier projects can be restored; Pro tier may require payment confirmation)
5. Wait 2-5 minutes for the project to come back online

**What happens during reactivation:**
- The PostgreSQL database is restored from its paused state
- All data, schemas, and extensions that existed before pausing are preserved
- API endpoints become active again
- Realtime subscriptions can be re-established

### Step 3: Verify Database Accessibility

Once reactivated, verify connectivity:

```bash
# Using psql (if installed)
psql "postgresql://postgres:[YOUR-DB-PASSWORD]@db.jitawzicdwgbhatvjblh.supabase.co:5432/postgres"

# Quick test: list tables
\dt

# Or use the Supabase dashboard SQL editor:
SELECT current_database(), current_user, version();
```

**Via Supabase REST API:**
```bash
curl -X GET "https://jitawzicdwgbhatvjblh.supabase.co/rest/v1/" \
  -H "apikey: YOUR_ANON_KEY" \
  -H "Authorization: Bearer YOUR_ANON_KEY"
```

### Step 4: Retrieve API Keys

After reactivation, confirm you have the required keys:

1. In Supabase Dashboard, go to **Settings** > **API**
2. Note these values:
   - **Project URL:** `https://jitawzicdwgbhatvjblh.supabase.co`
   - **anon (public) key:** For client-side operations (limited access)
   - **service_role key:** For server-side operations (full access - keep secret)
   - **Database password:** For direct PostgreSQL connections

### Step 5: Re-enable MCP Server

Update your Claude Code / OpenClaw configuration to re-enable the Supabase MCP server:

**In Claude Code MCP config (`~/.claude/config.json` or similar):**
```json
{
  "mcpServers": {
    "supabase": {
      "command": "npx",
      "args": ["-y", "@supabase/mcp-server"],
      "env": {
        "SUPABASE_URL": "https://jitawzicdwgbhatvjblh.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "${SUPABASE_SERVICE_ROLE_KEY}"
      }
    }
  }
}
```

**Set the environment variable:**
```bash
# Add to your shell profile (~/.bashrc, ~/.zshrc, or Windows environment)
export SUPABASE_SERVICE_ROLE_KEY="your-service-role-key-here"
```

### Step 6: Test MCP Connectivity

From Claude Code or OpenClaw, run a simple test:

```
"Run a test query on Supabase: SELECT 1 as test"
```

Expected: The Supabase MCP server starts, connects to your project, and returns `[{"test": 1}]`.

**Additional tests:**
- List existing tables: `SELECT tablename FROM pg_tables WHERE schemaname = 'public';`
- Check extensions: `SELECT * FROM pg_extension;`
- Verify pgvector availability: `SELECT * FROM pg_available_extensions WHERE name = 'vector';`

---

## Cost Considerations

### Free Tier (Sufficient for Development and Light Production)

| Resource | Free Tier Limit |
|---|---|
| Database | 500 MB |
| API requests | 500K/month |
| Realtime connections | 200 concurrent |
| Edge Functions | 500K invocations/month |
| Storage | 1 GB |
| Bandwidth | 2 GB |

**For OpenClaw's needs, the free tier is likely sufficient** during development and early production. You will need to monitor:
- Database size (enrichment data can grow quickly)
- API request count (frequent polling could hit limits)

### Pro Tier ($25/month)

| Resource | Pro Tier Limit |
|---|---|
| Database | 8 GB |
| API requests | Unlimited |
| Realtime connections | 500 concurrent |
| Edge Functions | 2M invocations/month |
| Storage | 100 GB |
| Bandwidth | 250 GB |

**Upgrade to Pro when:**
- Database exceeds 500 MB (likely after storing 50K+ enriched leads)
- You need more than 200 concurrent Realtime connections
- You are hitting API rate limits

---

## Decision: When to Reactivate

**Do NOT reactivate yet if:**
- You are still in the planning/architecture phase
- You have not finalized the database schema
- You do not need persistent storage yet (Airtable suffices as interim)

**Reactivate when you are ready to:**
- Deploy the database schema (see `schema-design.md`)
- Set up pgvector for RAG embeddings (see `pgvector-rag.md`)
- Store enrichment data persistently
- Enable Realtime event triggers

**Recommended timing:** Reactivate at the start of Week 2 of OpenClaw development, after P0 integrations (GHL, n8n, Airtable, Clay) are working.

---

## Your Existing supabase-ops Skill

You have a Claude Code skill called `supabase-ops` that was built for database operations. After reactivation, this skill can be used immediately for:

- Running SQL queries
- Creating and modifying tables
- Inserting and querying data
- Managing database migrations

**Verify the skill works after reactivation:**
```
/supabase-ops
> Run query: SELECT current_timestamp;
```

---

## Post-Reactivation Checklist

- [ ] Project reactivated in Supabase dashboard
- [ ] Database accessible via psql or REST API
- [ ] API keys retrieved and stored as environment variables
- [ ] MCP server re-enabled in config
- [ ] MCP connectivity tested with simple query
- [ ] supabase-ops skill verified working
- [ ] pgvector extension available (not yet enabled)
- [ ] Realtime feature accessible in dashboard
- [ ] Database backup schedule confirmed
- [ ] Row Level Security policies reviewed (none exist yet, which is fine for now)

---

## Troubleshooting

| Issue | Cause | Fix |
|---|---|---|
| Project won't reactivate | Billing issue | Check payment method in Supabase settings |
| MCP server fails to start | Missing npm package | Run `npx @supabase/mcp-server` manually to test |
| Connection refused | Project still spinning up | Wait 5 minutes, retry |
| Auth error (403) | Wrong API key | Verify service_role key, not anon key |
| Database empty | Pausing preserves data but check | Query `pg_tables` to verify schema exists |
| pgvector not available | Extension not installed | Enable via SQL: `CREATE EXTENSION IF NOT EXISTS vector;` |
| Slow queries | Cold start after pause | First few queries may be slow, performance improves |

---

## RESEARCH GAPS

- [ ] Verify your Supabase project's exact free tier status and any billing implications
- [ ] Confirm the supabase-ops skill is in your Claude Code configuration
- [ ] Check if any data existed in the database before it was paused
- [ ] Verify the Supabase MCP server npm package name and version
- [ ] Determine if project reactivation resets any settings or requires reconfiguration
