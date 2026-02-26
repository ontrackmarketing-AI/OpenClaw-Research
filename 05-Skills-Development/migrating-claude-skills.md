# Migrating Claude Code Skills to OpenClaw Format

## Your Existing Claude Code Skills

You currently have 6 custom skills built for Claude Code that need to be migrated to the OpenClaw AgentSkills format. Here is each skill, what it does, and the migration plan.

---

## Skill Inventory

### 1. clay-enrichment

- **Location**: Claude Code skill (slash command)
- **Purpose**: Interface with Clay.com for lead enrichment via waterfall lookups and enrichment tables
- **Core Capabilities**:
  - Create and manage Clay enrichment tables
  - Run waterfall enrichment across multiple data providers
  - Pull enriched data back into your pipeline
- **Key Dependencies**: Clay.com API, web_fetch
- **Migration Complexity**: **Medium** -- API calls are straightforward, but the waterfall logic may need careful porting

### 2. lead-pipeline

- **Location**: Claude Code skill (slash command)
- **Purpose**: Rise Local lead generation pipeline -- the full discovery-to-qualified-lead flow
- **Core Capabilities**:
  - Google Places business discovery by industry/location
  - 15-signal pain scoring system
  - Lead qualification and routing
  - Integration with downstream systems (Supabase, GHL)
- **Key Dependencies**: Google Places API, DataForSEO, BuiltWith, web_fetch, Supabase, GHL
- **Migration Complexity**: **Complex** -- multiple API integrations, scoring logic, and downstream routing

### 3. supabase-ops

- **Location**: Claude Code skill (slash command)
- **Purpose**: Database operations for Rise Local Supabase instance
- **Core Capabilities**:
  - CRUD operations on Rise Local tables
  - Complex queries with joins and aggregations
  - Schema inspection and migration support
  - pgvector operations for embeddings/RAG
- **Key Dependencies**: Supabase client library, database connection
- **Migration Complexity**: **Simple** -- well-defined CRUD operations, existing MCP server for Supabase

### 4. obsidian-helix

- **Location**: Claude Code skill (slash command)
- **Purpose**: HELIX documentation system for Obsidian vault management
- **Core Capabilities**:
  - Create/update session logs
  - Manage decision records
  - Navigate knowledge base structure
  - Maintain documentation standards
- **Key Dependencies**: Obsidian MCP server, file system access
- **Migration Complexity**: **Medium** -- file operations are straightforward, but the HELIX convention/prompt logic is nuanced

### 5. ghl-form-connect

- **Location**: Claude Code skill (slash command)
- **Purpose**: Connect landing page forms to GoHighLevel CRM
- **Core Capabilities**:
  - Map form fields to GHL contact fields
  - Handle form submissions and route to GHL
  - Create/update GHL contacts from form data
  - Trigger GHL workflows on form submission
- **Key Dependencies**: GHL API, web_fetch, possibly GHL MCP server
- **Migration Complexity**: **Simple** -- clear input/output, single API integration

### 6. smb-local-marketing

- **Location**: Claude Code skill (slash command)
- **Purpose**: Local marketing and lead generation strategies for small businesses
- **Core Capabilities**:
  - Generate marketing strategies for SMB clients
  - Create content calendars
  - Audit local SEO presence
  - Provide competitive analysis
  - Generate marketing reports
- **Key Dependencies**: Various APIs (DataForSEO, Google, social platforms), web_fetch
- **Migration Complexity**: **Medium** -- heavy prompt engineering, multiple data sources

---

## Claude Code Skill Format vs OpenClaw Skill Format

### Claude Code Skill Structure

Claude Code skills are relatively simple -- primarily markdown-based prompt files:

```
.claude/commands/my-skill.md
```

Or in a skills directory:

```
my-skill/
├── skill.md           # Main prompt with instructions
├── (optional) additional reference files
```

**Key characteristics of Claude Code skills**:
- Single markdown file is the primary format
- Prompts define behavior through natural language instructions
- Tool access is inherited from the parent Claude Code session (all tools available)
- No formal input/output schema -- inputs come from user message, outputs are freeform
- No manifest, no versioning, no dependency management
- No configuration system -- API keys and settings hardcoded in prompts or referenced from environment
- No test framework -- testing is manual
- No distribution mechanism -- shared via copy/paste or git

### OpenClaw Skill Structure

OpenClaw skills are structured packages following the AgentSkills standard:

```
my-skill/
├── skill.json              # Formal manifest with metadata, permissions, I/O schema
├── index.ts                # Programmatic entry point
├── prompts/
│   ├── system.md           # System prompt
│   └── examples/           # Few-shot examples
├── config/
│   ├── schema.json         # Configuration validation
│   └── defaults.json       # Default values
├── tests/
│   ├── unit/
│   └── integration/
└── README.md
```

**Key characteristics of OpenClaw skills**:
- Structured package with manifest
- Programmatic entry point (TypeScript/JavaScript) for logic
- Prompts are separate files in a prompts/ directory
- Explicit input/output schemas with types and validation
- Explicit permission declarations (network, filesystem, environment)
- Configuration system with schema validation
- Built-in test framework
- Distribution via ClawHub marketplace

### Side-by-Side Comparison

| Feature | Claude Code | OpenClaw |
|---------|-------------|----------|
| **Skill definition** | Markdown prompt file | `skill.json` manifest + code |
| **Prompts** | Inline in the skill file | Separate files in `prompts/` |
| **Logic** | LLM interprets prompt instructions | TypeScript/JavaScript code + LLM |
| **Inputs** | Parsed from user message (unstructured) | Typed schema in manifest |
| **Outputs** | Freeform text/actions | Typed schema in manifest |
| **Tools** | All session tools available | Only declared tools |
| **Config** | Env vars or hardcoded | Schema-validated config store |
| **Secrets** | `.env` file or prompt reference | Encrypted credential store |
| **Testing** | Manual invocation | Vitest + mock framework |
| **Distribution** | Git/copy | ClawHub marketplace |
| **Versioning** | None (or git tags) | Semantic versioning |
| **Dependencies** | Implicit (user must have tools) | Explicit in manifest |
| **Composition** | Cannot call other skills | `context.skills.invoke()` |

---

## Migration Strategy: General Process

For each Claude Code skill, follow these steps:

### Phase 1: Extract and Analyze (30 min per skill)

1. **Read the existing skill file(s)** thoroughly
2. **Document the core logic**: What does this skill actually DO step by step?
3. **List all tool calls**: What tools does the skill use? (web_fetch, file operations, bash, etc.)
4. **List all external APIs**: What endpoints does the skill call?
5. **List all inputs**: What information does the skill need from the user?
6. **List all outputs**: What does the skill produce?
7. **Identify configuration**: What API keys, URLs, or settings does the skill reference?

### Phase 2: Design the OpenClaw Skill (1 hour per skill)

1. **Create skill.json manifest**:
   - Define inputs with types, required/optional, descriptions
   - Define outputs with types
   - Declare required tools
   - Declare permissions (network endpoints, filesystem paths, env vars)
   - List dependencies (npm packages, other skills)

2. **Design the entry point logic**:
   - What can be coded programmatically vs. what needs LLM generation?
   - API calls should be in code (more reliable than LLM tool calls)
   - Content generation should use `context.llm.generate()`
   - Input validation should use Zod schemas

3. **Port the prompts**:
   - Extract the system prompt from the Claude Code skill markdown
   - Split into system.md (core behavior) and examples (few-shot)
   - Remove any tool-specific instructions that are now handled in code

4. **Design configuration schema**:
   - Each API key becomes a config entry with `sensitive: true`
   - Each user-adjustable setting becomes a config entry with a default

### Phase 3: Implement (2-4 hours per skill)

1. **Scaffold**: `openclaw skill create skill-name --template api-integration`
2. **Write skill.json** from your Phase 2 design
3. **Implement index.ts** with the core logic
4. **Write prompts** in `prompts/system.md` and `prompts/examples/`
5. **Write config schema** in `config/schema.json`
6. **Write tests** -- at minimum: input validation, happy path, error handling

### Phase 4: Test and Validate (1-2 hours per skill)

1. **Run unit tests**: `openclaw skill test skill-name`
2. **Run integration tests**: `openclaw skill test skill-name --live`
3. **Interactive testing**: `openclaw skill try skill-name`
4. **Compare outputs**: Run the same inputs through Claude Code skill and OpenClaw skill, verify results match
5. **Edge case testing**: Empty inputs, invalid inputs, API failures, rate limits

---

## Per-Skill Migration Plans

### 1. clay-enrichment -> @yourname/clay-enrichment

**Estimated Migration Time**: 4-6 hours

**skill.json inputs**:
```json
{
  "inputs": {
    "required": {
      "action": {
        "type": "string",
        "enum": ["create_table", "run_enrichment", "get_results", "waterfall_lookup"],
        "description": "The enrichment action to perform"
      }
    },
    "optional": {
      "table_id": { "type": "string", "description": "Clay table ID" },
      "leads": { "type": "array", "description": "Array of lead objects to enrich" },
      "enrichment_type": { "type": "string", "enum": ["email", "phone", "company", "full"] },
      "waterfall_providers": { "type": "array", "description": "Ordered list of data providers" }
    }
  }
}
```

**Permissions**:
```json
{
  "permissions": {
    "network": ["api.clay.com", "app.clay.com"],
    "environment": ["CLAY_API_KEY"]
  }
}
```

**Migration Steps**:
1. Extract Clay API call patterns from existing skill prompt
2. Implement API client in TypeScript with proper error handling
3. Port waterfall logic (try provider A, fall back to B, then C)
4. Add retry logic for rate-limited requests
5. Test with a small batch of known leads

---

### 2. lead-pipeline -> @yourname/lead-pipeline

**Estimated Migration Time**: 8-12 hours (most complex skill)

**skill.json inputs**:
```json
{
  "inputs": {
    "required": {
      "action": {
        "type": "string",
        "enum": ["discover", "score", "qualify", "full_pipeline"],
        "description": "Pipeline stage to execute"
      }
    },
    "optional": {
      "industry": { "type": "string", "description": "Target industry (e.g., plumber, solar)" },
      "location": { "type": "string", "description": "City and state" },
      "radius_miles": { "type": "integer", "default": 25 },
      "max_results": { "type": "integer", "default": 50 },
      "scoring_threshold": { "type": "integer", "default": 60, "description": "Minimum score (0-100) to qualify" },
      "leads": { "type": "array", "description": "Pre-existing leads to score/qualify" }
    }
  }
}
```

**Permissions**:
```json
{
  "permissions": {
    "network": [
      "maps.googleapis.com",
      "api.dataforseo.com",
      "api.builtwith.com",
      "api.clay.com",
      "*.supabase.co"
    ],
    "environment": [
      "GOOGLE_PLACES_API_KEY",
      "DATAFORSEO_LOGIN",
      "DATAFORSEO_PASSWORD",
      "BUILTWITH_API_KEY",
      "CLAY_API_KEY",
      "SUPABASE_URL",
      "SUPABASE_ANON_KEY"
    ]
  }
}
```

**Composition** (calls other skills):
```json
{
  "dependencies": {
    "skills": {
      "@yourname/clay-enrichment": "^1.0.0",
      "@yourname/database-ops": "^1.0.0"
    }
  }
}
```

**Migration Steps**:
1. Map out the complete pipeline flow from the existing skill
2. Implement Google Places discovery as a standalone function
3. Port the 15-signal scoring system to a typed scoring module
4. Implement each enrichment source as a pluggable provider
5. Use skill composition: call clay-enrichment and database-ops skills
6. Add progress reporting for long-running batch operations
7. Test end-to-end with a known location and industry

---

### 3. supabase-ops -> @yourname/database-ops

**Estimated Migration Time**: 3-4 hours

**skill.json inputs**:
```json
{
  "inputs": {
    "required": {
      "operation": {
        "type": "string",
        "enum": ["query", "insert", "update", "delete", "upsert", "schema", "migrate"],
        "description": "Database operation to perform"
      },
      "table": {
        "type": "string",
        "description": "Table name to operate on"
      }
    },
    "optional": {
      "data": { "type": "object", "description": "Data for insert/update/upsert" },
      "filters": { "type": "object", "description": "Query filters" },
      "select": { "type": "string", "description": "Fields to select (default: *)" },
      "limit": { "type": "integer", "description": "Max rows to return" },
      "order_by": { "type": "string", "description": "Sort field and direction" }
    }
  }
}
```

**Migration Steps**:
1. Extract Supabase query patterns from existing skill
2. Implement using @supabase/supabase-js npm package
3. Add safety checks: require confirmation for DELETE, warn on UPDATE without WHERE
4. Port any pgvector-specific operations
5. Test against your Rise Local Supabase instance

---

### 4. obsidian-helix -> @yourname/obsidian-helix

**Estimated Migration Time**: 4-6 hours

**skill.json inputs**:
```json
{
  "inputs": {
    "required": {
      "action": {
        "type": "string",
        "enum": ["log_session", "log_decision", "update_task", "create_doc", "read_doc", "search"],
        "description": "HELIX documentation action"
      }
    },
    "optional": {
      "content": { "type": "object", "description": "Content for the documentation action" },
      "path": { "type": "string", "description": "Document path in vault" },
      "query": { "type": "string", "description": "Search query" }
    }
  }
}
```

**Migration Steps**:
1. Extract HELIX conventions and document templates from existing skill
2. Map Obsidian MCP server calls to OpenClaw tool declarations
3. Port template system (session, decision, component, phase, task templates)
4. Preserve the HELIX naming and structural conventions in prompts
5. Test by creating a session log and verifying format matches existing HELIX format

**Note**: If OpenClaw has its own documentation/knowledge base system, consider whether HELIX should be ported as-is or adapted to OpenClaw's conventions. The core value of HELIX is the structured approach -- that can work in any system.

---

### 5. ghl-form-connect -> @yourname/ghl-form-connect

**Estimated Migration Time**: 2-3 hours

**skill.json inputs**:
```json
{
  "inputs": {
    "required": {
      "action": {
        "type": "string",
        "enum": ["map_fields", "process_submission", "create_contact", "trigger_workflow"],
        "description": "Form connection action"
      }
    },
    "optional": {
      "form_data": { "type": "object", "description": "Form submission data" },
      "field_mapping": { "type": "object", "description": "Form field to GHL field mapping" },
      "workflow_id": { "type": "string", "description": "GHL workflow to trigger" },
      "pipeline_id": { "type": "string", "description": "GHL pipeline to add contact to" },
      "stage_id": { "type": "string", "description": "Pipeline stage for new contact" }
    }
  }
}
```

**Migration Steps**:
1. Extract GHL API patterns from existing skill
2. Implement field mapping logic in TypeScript (more reliable than LLM mapping)
3. Add validation for required GHL fields
4. Test with a sample form submission
5. Verify contact creation and workflow triggering in GHL

---

### 6. smb-local-marketing -> @yourname/smb-local-marketing

**Estimated Migration Time**: 5-7 hours

**skill.json inputs**:
```json
{
  "inputs": {
    "required": {
      "action": {
        "type": "string",
        "enum": ["strategy", "content_calendar", "seo_audit", "competitor_analysis", "report"],
        "description": "Marketing action to perform"
      },
      "business": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "industry": { "type": "string" },
          "location": { "type": "string" },
          "website": { "type": "string" }
        },
        "description": "Business information"
      }
    },
    "optional": {
      "competitors": { "type": "array", "description": "Competitor URLs to analyze" },
      "time_range": { "type": "string", "description": "Report time range" },
      "platforms": { "type": "array", "description": "Marketing platforms to include" }
    }
  }
}
```

**Migration Steps**:
1. Extract marketing strategy templates and prompts
2. Port the content calendar generation logic
3. Implement SEO audit using DataForSEO API calls in code
4. Port competitor analysis logic
5. Create report generation templates
6. Heavy LLM usage for content generation -- ensure prompts are well-structured in `prompts/`

---

## Migration Priority Order

Based on dependencies and business value:

| Priority | Skill | Reason | Estimated Time |
|----------|-------|--------|----------------|
| 1 | supabase-ops -> database-ops | Foundation -- other skills depend on it | 3-4 hours |
| 2 | clay-enrichment | Foundation -- lead-pipeline depends on it | 4-6 hours |
| 3 | ghl-form-connect | Simple, high business value | 2-3 hours |
| 4 | lead-pipeline | Core business value, depends on #1 and #2 | 8-12 hours |
| 5 | smb-local-marketing | Business value, complex prompts | 5-7 hours |
| 6 | obsidian-helix | Important but can use existing Obsidian MCP meanwhile | 4-6 hours |

**Total Estimated Time**: 26-38 hours

---

## Key Research Gaps

- **Exact skill.json schema**: Need the complete AgentSkills specification to validate manifest format
- **Tool name mapping**: Need to confirm exact OpenClaw tool names (are they `web_fetch`, `http_request`, or something else?)
- **LLM access in skills**: How exactly does `context.llm.generate()` work? What models are available?
- **MCP server reuse**: Can existing MCP servers (Supabase, GHL, Obsidian) be declared as tools in OpenClaw skills, or do they need to be wrapped?
- **Skill-to-skill communication**: Does `context.skills.invoke()` pass full context or only declared inputs?
- **Migration tooling**: Does OpenClaw provide any automated migration tools for Claude Code skills?

---

## Testing Migration Success

For each migrated skill, validate:

1. **Same inputs produce same outputs**: Run identical test cases through both versions
2. **Error handling is equivalent or better**: Test with invalid inputs, API failures
3. **Performance is acceptable**: OpenClaw skill should not be significantly slower
4. **All features are preserved**: No functionality lost in migration
5. **New capabilities work**: Test OpenClaw-specific features (composition, progress reporting, etc.)

---

*Last updated: 2026-02-05*
*Status: Migration plan ready; execution blocked on OpenClaw access and AgentSkills spec verification*
