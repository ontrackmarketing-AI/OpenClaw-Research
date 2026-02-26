# Detailed Integration Gap Analysis

> Per-tool assessment of current state, OpenClaw needs, gaps, effort, and priority.

---

## Summary Table

| Integration | Current State | OpenClaw Need | Gap Size | Effort | Priority | Status |
|---|---|---|---|---|---|---|
| GoHighLevel MCP | TypeScript MCP server built | MCP client connection | Small | 4-8 hrs | P0 | Exists, needs audit |
| Clay.com | No adapter, API available | REST adapter + waterfall logic | Medium | 16-24 hrs | P0 | Must build |
| Supabase | Project disabled | Reactivate + schema + pgvector | Medium | 8-16 hrs | P1 | Paused |
| n8n | Docker running, MCP available | MCP client connection | Small | 2-4 hrs | P0 | Ready to connect |
| Airtable MCP | Active and working | Already connected | None | 0 hrs | P0 | Done |
| Ralph AI | v0.9.9, Claude Code integrated | Minimal, dev-loop only | Small | 2-4 hrs | P2 | Low priority |
| OnTrack Marketing | FastAPI/Next.js running | API bridge for content ops | Medium | 16-24 hrs | P2 | Future |
| Rise Local Lead | Pipeline logic exists | Connect discovery to enrichment | Medium | 8-16 hrs | P1 | Needs adapter |
| RAFE+Obsidian | MCP active and working | Already connected | None | 0 hrs | P1 | Done |

---

## 1. GoHighLevel MCP

### Current State
- **Location:** `C:/Users/Owner/OneDrive/Desktop/GoHighLevel-MCP`
- **Language:** TypeScript
- **Format:** MCP server (stdio transport)
- **What works:** Core CRM operations via MCP tool calls. Built to interface with GHL API v2.
- **Authentication:** Uses GHL API key and Location ID from environment variables.

### OpenClaw Needs
- Contact CRUD: create, read, update, search, delete contacts
- Pipeline management: create/move opportunities through stages
- Tag management: add/remove tags for segmentation
- Appointment operations: create, list, update appointments
- Webhook registration: programmatic webhook setup
- Campaign triggers: start/stop marketing campaigns
- Custom field management: create and populate custom fields
- Conversation management: read/send messages in GHL conversations

### Gap Analysis
| Capability | Exists in MCP? | Gap |
|---|---|---|
| Contact CRUD | Likely yes | Need to audit exact operations |
| Pipeline ops | Likely partial | May need stage movement automation |
| Tag management | Unknown | Need to check MCP tools list |
| Appointments | Unknown | Need to verify |
| Webhook management | Unlikely | GHL webhook API is separate |
| Campaign triggers | Unknown | Need to check |
| Custom fields | Unknown | Need to check |
| Conversations | Unknown | Need to check |

### Effort Estimate
- **Audit existing MCP server:** 2 hours
- **Add missing operations:** 2-6 hours (depending on gaps)
- **Configure in OpenClaw:** 1 hour
- **Test end-to-end:** 2 hours
- **Total: 4-8 hours**

### Priority: P0
The CRM is the center of every lead workflow. Without GHL, leads have nowhere to go.

### Dependencies
- GHL API key must be valid and have correct permissions
- GHL sub-account must be configured for the target client

### Action Items
1. **IMMEDIATE:** Run the GHL MCP server locally and list all exposed tools
2. **IMMEDIATE:** Compare exposed tools to the full GHL API v2 capability list
3. Build missing operations as new MCP tool handlers
4. Configure in OpenClaw settings
5. Test contact creation + pipeline movement through OpenClaw

---

## 2. Clay.com Enrichment

### Current State
- **Format:** SaaS platform with REST API
- **What exists:** Manual usage through Clay UI. No code adapter built yet.
- **API docs:** Available at docs.clay.com
- **Authentication:** API key (workspace-level)
- **SDK:** No official Python SDK; REST API only.

### OpenClaw Needs
- Create enrichment tables programmatically
- Add rows (leads) to tables for enrichment
- Trigger waterfall enrichment on rows
- Poll for enrichment completion
- Retrieve enriched data
- Map enriched fields to GHL custom fields
- Cost tracking per enrichment run
- Webhook callback for async enrichment completion

### Gap Analysis
| Capability | Exists? | Gap |
|---|---|---|
| REST API adapter | No | Must build from scratch |
| Waterfall enrichment trigger | No | Must implement Clay API calls |
| Field mapping to GHL | No | Must define mapping schema |
| Credit tracking | No | Must build monitoring |
| Async completion handling | No | Must set up webhook/polling |
| Pre-enrichment filtering | No | Must implement qualification logic |
| Cost optimization logic | No | Must build staged enrichment |

### Effort Estimate
- **Build Clay API adapter:** 8 hours
- **Implement waterfall logic:** 4 hours
- **Build field mapping:** 4 hours
- **Add credit tracking:** 2 hours
- **Test with real data:** 4 hours
- **Total: 16-24 hours**

### Priority: P0
Enrichment is the core value differentiator. Without Clay integration, leads are just names and addresses.

### Dependencies
- Active Clay.com account with API access
- Sufficient Clay credits for testing (budget ~$50 for testing)
- GHL custom fields must be defined first (so mapping targets exist)

### Action Items
1. Get Clay API key and test basic API calls (create table, add row)
2. Build Python adapter class with all needed operations
3. Define the waterfall enrichment sequence (see `waterfall-design.md`)
4. Implement field mapping from Clay response to GHL contact schema
5. Build credit monitoring and cost alerts

---

## 3. Supabase

### Current State
- **Project ID:** `jitawzicdwgbhatvjblh`
- **Status:** Disabled (project paused in Supabase dashboard)
- **MCP:** Was configured in Claude Code, currently non-functional
- **What existed:** Basic project setup, no custom schema deployed yet
- **Existing skill:** `supabase-ops` Claude Code slash command exists

### OpenClaw Needs
- Persistent storage for enriched lead data
- pgvector for RAG document embeddings
- Session history and skill execution logs
- Competitor intelligence data store
- Real-time event triggers (Supabase Realtime)
- Backup/sync for data that lives in Airtable or GHL

### Gap Analysis
| Capability | Exists? | Gap |
|---|---|---|
| Active project | No | Must reactivate |
| Database schema | No | Must design and deploy all tables |
| pgvector extension | No | Must enable and configure |
| RAG functions (RPC) | No | Must write match_documents function |
| Row Level Security | No | Must define policies |
| Realtime config | No | Must enable on relevant tables |
| MCP reconnection | Config exists | Re-enable after reactivation |

### Effort Estimate
- **Reactivate project:** 0.5 hours
- **Design and deploy schema:** 4 hours
- **Set up pgvector + RAG functions:** 4 hours
- **Configure RLS and security:** 2 hours
- **Re-enable MCP:** 1 hour
- **Test all operations:** 2 hours
- **Total: 8-16 hours**

### Priority: P1
Not blocking initial workflow, but required for persistent RAG and analytics. Can use Airtable as interim storage.

### Dependencies
- Decision on whether to use Supabase free tier or Pro ($25/mo)
- Embedding model choice (determines vector dimensions: 768 for nomic, 1536 for OpenAI)
- Schema finalization (dependent on GHL field mapping)

### Action Items
1. Reactivate Supabase project when ready for RAG implementation
2. Deploy schema migrations (see `schema-design.md`)
3. Enable pgvector and create embedding tables
4. Write and test match_documents RPC function
5. Re-enable Supabase MCP in OpenClaw config

---

## 4. n8n Workflows

### Current State
- **Location:** `C:/Users/Owner/OneDrive/Desktop/rise-local-n8n`
- **Runtime:** Docker container, locally hosted
- **Status:** Running and accessible
- **MCP:** n8n MCP server is configured and available
- **Custom nodes:** Installed in the Docker container
- **Existing workflows:** Lead processing, enrichment sequences, email automation

### OpenClaw Needs
- Execute existing workflows programmatically
- Create new workflows via API for new automation needs
- Pass data bidirectionally (OpenClaw -> n8n and n8n -> OpenClaw)
- Monitor workflow execution status
- Handle webhook events from n8n
- Use n8n as a webhook relay for external services (GHL, Clay callbacks)

### Gap Analysis
| Capability | Exists? | Gap |
|---|---|---|
| n8n MCP connection | Yes | Verify tool list |
| Execute workflow | Likely yes | Test through OpenClaw |
| Create workflow | Likely yes | Test through OpenClaw |
| Bidirectional data flow | Partial | Need OpenClaw API endpoint for n8n to call |
| Webhook relay | Not configured | Need to set up n8n as relay |
| Execution monitoring | Unknown | Need to verify MCP capabilities |

### Effort Estimate
- **Verify MCP tools:** 1 hour
- **Test workflow execution through OpenClaw:** 2 hours
- **Set up webhook relay:** 2 hours
- **Build example integrated workflows:** 4 hours
- **Total: 2-4 hours (basic), 8 hours (with example workflows)**

### Priority: P0
n8n is the automation backbone. It handles the heavy lifting that OpenClaw orchestrates.

### Dependencies
- Docker container must be running
- n8n API key must be valid
- Network: OpenClaw and n8n must be on same network (Tailscale or local Docker network)

### Action Items
1. List all tools exposed by n8n MCP server
2. Test executing a simple workflow through OpenClaw
3. Set up n8n webhook relay for GHL and Clay callbacks
4. Build the 5 core integrated workflows (see `example-workflows.md`)

---

## 5. Airtable MCP

### Current State
- **Status:** Fully active and working
- **MCP:** Configured in Claude Code, all operations functional
- **Available tools:** list_bases, list_tables, create_table, CRUD records, search_records
- **Current data:** Bases exist for project tracking and content management

### OpenClaw Needs
- Content calendar management
- Client/lead tracking (interim before Supabase)
- Project management views
- Template storage for content generation

### Gap Analysis
| Capability | Exists? | Gap |
|---|---|---|
| MCP connection | Yes | None |
| Record CRUD | Yes | None |
| Search | Yes | None |
| Content calendar schema | Unknown | May need to create tables |
| Lead tracking schema | Unknown | May need to create tables |

### Effort Estimate
- **Already working:** 0 hours for basic connectivity
- **Create content calendar table:** 1 hour
- **Create lead tracking table:** 1 hour
- **Total: 0-2 hours**

### Priority: P0 (already done)
Zero work needed for basic integration. Minor work for new table schemas.

### Dependencies
- None. Already working.

### Action Items
1. Audit existing Airtable bases and tables
2. Create content calendar table if it does not exist
3. Document the schema for OpenClaw skills to reference

---

## 6. Ralph AI Dev Loop

### Current State
- **Version:** v0.9.9
- **Integration:** Works within Claude Code session
- **Function:** Development automation - code generation, testing, deployment
- **Relevance to OpenClaw:** Primarily used to BUILD OpenClaw, not as a runtime integration

### OpenClaw Needs
- Minimal runtime needs. Ralph is a development tool.
- Possible use: Ralph generates code that OpenClaw executes (skill generation)
- Possible use: Ralph manages OpenClaw's codebase updates

### Gap Analysis
This is a development dependency, not a runtime integration. Gap is minimal.

### Effort Estimate
- **Total: 2-4 hours** (document how Ralph and OpenClaw interact during development)

### Priority: P2
Not needed for OpenClaw operation. Useful for OpenClaw development velocity.

---

## 7. OnTrack Marketing

### Current State
- **Stack:** FastAPI (backend) + Next.js (frontend) + PostgreSQL + Redis + Qdrant
- **Function:** Marketing content generation and management platform
- **Status:** Running locally
- **API:** FastAPI exposes REST endpoints

### OpenClaw Needs
- Content generation API: ask OnTrack to generate marketing content
- Content publishing: push content to social platforms via OnTrack
- Performance data: pull content performance metrics
- Template library: access OnTrack's content templates

### Gap Analysis
| Capability | Exists? | Gap |
|---|---|---|
| API adapter | No | Must build REST adapter |
| Content generation endpoint | Exists in OnTrack | Need to document and connect |
| Publishing integration | Partial in OnTrack | Need to verify and connect |
| Performance metrics | Unknown | Need to check OnTrack API |

### Effort Estimate
- **Document OnTrack API endpoints:** 4 hours
- **Build REST adapter:** 8 hours
- **Test content generation through OpenClaw:** 4 hours
- **Total: 16-24 hours**

### Priority: P2
Content generation is important but not blocking lead workflows. Can be done manually until automated.

### Dependencies
- OnTrack must be running and API documented
- Authentication mechanism between OpenClaw and OnTrack

---

## 8. Rise Local Lead Pipeline

### Current State
- **Function:** Local business lead discovery and qualification
- **Components:** Google Places scraping, pain scoring (15 signals), lead routing
- **Status:** Logic exists across n8n workflows and Python scripts
- **Integration:** Feeds into Clay for enrichment, then GHL for CRM

### OpenClaw Needs
- Trigger lead discovery searches (industry + location)
- Receive discovered leads for enrichment
- Apply pain scoring to discovered leads
- Route qualified leads to enrichment pipeline
- Track discovery campaigns and results

### Gap Analysis
| Capability | Exists? | Gap |
|---|---|---|
| Discovery trigger | Exists in n8n | Connect n8n workflow to OpenClaw |
| Pain scoring logic | Exists in code | Port to OpenClaw skill or keep in n8n |
| Lead routing | Exists partially | Need full routing rules in OpenClaw |
| Campaign tracking | Minimal | Need tracking dashboard |

### Effort Estimate
- **Map existing pipeline components:** 4 hours
- **Build OpenClaw skills for discovery trigger:** 4 hours
- **Connect pain scoring:** 4 hours
- **Test end-to-end:** 4 hours
- **Total: 8-16 hours**

### Priority: P1
Lead discovery is the front of the funnel. Without it, there are no leads to enrich.

### Dependencies
- n8n workflows must be documented and accessible
- Google Places API key must be valid
- Pain scoring criteria must be finalized

---

## 9. RAFE + Obsidian Dashboard

### Current State
- **Status:** MCP active and fully working
- **Tools:** get_doc, list_docs, update_doc, create_doc, log_session, log_decision, update_task_status
- **Function:** Development documentation, session logging, decision tracking, task management
- **Data:** Rich project history in Obsidian vault

### OpenClaw Needs
- Log OpenClaw operations and decisions
- Track task status for ongoing projects
- Reference existing documentation for context
- Session logging for audit trail

### Gap Analysis
| Capability | Exists? | Gap |
|---|---|---|
| MCP connection | Yes | None |
| Document CRUD | Yes | None |
| Session logging | Yes | None |
| Decision logging | Yes | None |
| Task management | Yes | None |

### Effort Estimate
- **Total: 0 hours** (fully integrated)

### Priority: P1 (already done)
No work needed. OpenClaw can use RAFE immediately.

---

## Critical Path

The critical path for full integration is:

```
GHL MCP audit (P0, 4h)
  -> Clay adapter build (P0, 16h)
    -> Waterfall enrichment config (P0, 8h)
      -> End-to-end lead test (P0, 4h)

Parallel track:
n8n MCP verify (P0, 2h) -> Example workflows (P1, 8h)

Deferred track:
Supabase reactivate (P1, 8h) -> pgvector RAG (P1, 8h)
OnTrack adapter (P2, 16h)
```

**Minimum viable integration (Week 1):** GHL MCP + n8n MCP + Airtable MCP + Clay adapter = full lead pipeline.

**Total effort to full integration:** ~80-120 hours across all tools.
**Minimum viable effort:** ~30-40 hours for P0 integrations.

---

## RESEARCH GAPS

- [ ] Audit GHL MCP server to list all current tools
- [ ] Verify n8n MCP server tool list and capabilities
- [ ] Get Clay API key and test basic operations
- [ ] Check OnTrack Marketing API documentation completeness
- [ ] Verify Rise Local pipeline components are all in n8n (vs scattered scripts)
- [ ] Determine if Ralph AI needs any runtime integration or is dev-only
