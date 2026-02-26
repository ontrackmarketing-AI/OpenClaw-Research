# OpenClaw Skills Architecture

## What Is an OpenClaw Skill?

An OpenClaw skill is a **self-contained capability module** that gives an OpenClaw agent a specific ability. Each skill defines:

- **Inputs**: What data it needs to perform its job (parameters, context, files)
- **Outputs**: What it returns when finished (structured data, files, status)
- **Tool Access**: Which external tools, APIs, or system capabilities it requires
- **Prompts**: The system-level instructions that guide the agent's behavior when executing the skill
- **Metadata**: Name, version, author, description, permissions, dependencies

A skill is NOT a full agent. It is a **building block** that an agent loads and executes. Think of skills as specialized "modes" the agent can switch into. When a user invokes a skill (via slash command, natural language, or programmatic trigger), the agent loads the skill's prompts, gains access to the skill's declared tools, and executes the skill's logic.

### Key Distinction from Claude Code Skills

| Aspect | Claude Code Skill | OpenClaw Skill |
|--------|------------------|----------------|
| Format | Single markdown file with prompts | Structured package: manifest + code + prompts |
| Distribution | Copy/paste or git | ClawHub marketplace |
| Tool Access | Inherits all agent tools | Explicitly declared per skill |
| Configuration | Hardcoded in prompt | Environment variables + user settings |
| Testing | Manual only | Built-in test framework |
| Composition | Cannot call other skills | Skills can invoke other skills |
| Versioning | Manual | Semantic versioning with dependency resolution |

---

## The AgentSkills Standard

AgentSkills is the **specification** that defines how OpenClaw skills are structured, packaged, and executed. It is the contract between skill authors and the OpenClaw runtime.

### Core Principles of AgentSkills

1. **Declarative Manifest**: Every skill declares what it needs upfront in `skill.json`
2. **Sandboxed Execution**: Skills run with only the permissions they declare
3. **Composability**: Skills can depend on and invoke other skills
4. **Testability**: Every skill must be testable in isolation
5. **Portability**: Skills work across OpenClaw deployments without modification

### AgentSkills Specification Version

The current AgentSkills spec version should be checked at the OpenClaw documentation. Skills declare which spec version they target in their manifest. The runtime maintains backward compatibility across minor versions.

**RESEARCH GAP**: Need to confirm the exact current AgentSkills spec version and where the specification document lives (likely docs.openclaw.sh or in the OpenClaw GitHub repo).

---

## Skill Anatomy: File Structure

A complete OpenClaw skill follows this directory structure:

```
my-skill/
├── skill.json              # Manifest: metadata, permissions, dependencies
├── index.ts                # Entry point: main skill logic (or index.js)
├── prompts/
│   ├── system.md           # System prompt loaded when skill activates
│   ├── examples/           # Few-shot examples for the LLM
│   │   ├── example-1.md
│   │   └── example-2.md
│   └── templates/          # Prompt templates with variable slots
│       └── enrichment.md
├── tools/
│   ├── tool-declarations.json  # External tool definitions
│   └── handlers/               # Custom tool handler implementations
│       └── my-custom-tool.ts
├── config/
│   ├── defaults.json       # Default configuration values
│   └── schema.json         # Configuration validation schema
├── tests/
│   ├── unit/
│   │   └── logic.test.ts
│   ├── integration/
│   │   └── api-calls.test.ts
│   └── fixtures/
│       ├── input-1.json
│       └── expected-output-1.json
├── README.md               # Skill documentation
├── CHANGELOG.md            # Version history
└── LICENSE                 # License (required for ClawHub publishing)
```

### skill.json Manifest (Detailed)

```json
{
  "name": "@yourname/my-skill",
  "version": "1.0.0",
  "description": "Short description of what the skill does",
  "agentskills": "1.0",
  "author": {
    "name": "Your Name",
    "email": "you@example.com",
    "url": "https://github.com/yourname"
  },
  "license": "MIT",
  "entry": "index.ts",
  "commands": ["/my-skill"],
  "triggers": {
    "slash_command": "/my-skill",
    "natural_language": ["do the thing", "run my skill"],
    "programmatic": true
  },
  "inputs": {
    "required": {
      "target": {
        "type": "string",
        "description": "The target to process"
      }
    },
    "optional": {
      "depth": {
        "type": "string",
        "enum": ["shallow", "deep"],
        "default": "shallow",
        "description": "How deep to go"
      }
    }
  },
  "outputs": {
    "result": {
      "type": "object",
      "description": "The processed result"
    }
  },
  "tools": {
    "required": ["web_fetch", "file_write"],
    "optional": ["browser", "code_execution"]
  },
  "permissions": {
    "network": ["api.example.com", "*.openai.com"],
    "filesystem": ["read:./data", "write:./output"],
    "environment": ["API_KEY", "SECRET_TOKEN"]
  },
  "dependencies": {
    "skills": {
      "@openclaw/web-scraper": "^2.0.0",
      "@openclaw/data-formatter": "^1.5.0"
    },
    "npm": {
      "axios": "^1.6.0",
      "zod": "^3.22.0"
    }
  },
  "config": {
    "schema": "config/schema.json",
    "defaults": "config/defaults.json"
  },
  "tests": {
    "command": "vitest run",
    "coverage_minimum": 80
  },
  "keywords": ["enrichment", "data", "lead-gen"],
  "repository": "https://github.com/yourname/my-skill"
}
```

### index.ts Entry Point (Detailed)

```typescript
import { Skill, SkillContext, SkillResult } from '@openclaw/sdk';

// The skill class extends the base Skill class
export default class MySkill extends Skill {

  // Called once when skill is loaded
  async onLoad(context: SkillContext): Promise<void> {
    // Initialize connections, validate config, etc.
    this.apiKey = context.config.get('API_KEY');
    if (!this.apiKey) {
      throw new Error('API_KEY is required in skill configuration');
    }
  }

  // Main execution method - called when skill is invoked
  async execute(context: SkillContext): Promise<SkillResult> {
    const { target, depth } = context.inputs;

    // Use declared tools
    const webData = await context.tools.web_fetch({
      url: `https://api.example.com/enrich?q=${target}`,
      headers: { 'Authorization': `Bearer ${this.apiKey}` }
    });

    // Use another skill (composition)
    const formatted = await context.skills.invoke('@openclaw/data-formatter', {
      data: webData,
      format: 'structured'
    });

    // Return structured result
    return {
      status: 'success',
      data: formatted,
      metadata: {
        source: 'api.example.com',
        enrichment_depth: depth,
        timestamp: new Date().toISOString()
      }
    };
  }

  // Called when skill is unloaded
  async onUnload(): Promise<void> {
    // Cleanup connections, temp files, etc.
  }
}
```

---

## Skill Lifecycle

### 1. Install

```bash
# From ClawHub
openclaw skill install @creator/skill-name

# From local directory
openclaw skill install ./path/to/my-skill

# From git repository
openclaw skill install https://github.com/creator/skill-name
```

Installation downloads the skill package, resolves dependencies (both skill and npm), and registers the skill with the local OpenClaw instance.

### 2. Configure

```bash
# Set skill-specific configuration
openclaw skill config @creator/skill-name set API_KEY=sk-xxx
openclaw skill config @creator/skill-name set MAX_RESULTS=50

# View current configuration
openclaw skill config @creator/skill-name list

# Reset to defaults
openclaw skill config @creator/skill-name reset
```

Configuration is stored locally (never published to ClawHub). The skill's `config/schema.json` validates all configuration values. Required configuration that is missing will prompt the user on first use.

### 3. Load

When a skill is invoked (via slash command, natural language trigger, or programmatic call), the runtime:

1. Reads the skill manifest
2. Checks all required permissions are granted
3. Loads the entry point module
4. Calls `onLoad()` with the skill context
5. Injects declared tools into the context
6. Loads system prompts and examples into the agent's context window

### 4. Execute

The runtime calls `execute()` with:
- Parsed and validated inputs
- Tool access (only declared tools)
- Configuration values
- Skill context (user info, session info, memory access)

During execution, the skill can:
- Call external APIs (only to declared network endpoints)
- Read/write files (only to declared paths)
- Invoke other skills
- Stream progress updates to the user
- Request human input (pause and ask the user)

### 5. Return Result

The skill returns a `SkillResult` object containing:
- Status: success, partial, error
- Data: the structured output
- Metadata: timing, sources, confidence scores
- Side effects: files created, records updated, etc.

The runtime validates the output against the declared output schema, logs the execution, and returns the result to the caller (agent or another skill).

---

## Skill Permissions Model

OpenClaw skills operate under a **least-privilege** model. Skills can ONLY access what they explicitly declare in their manifest.

### Permission Categories

| Category | Examples | Manifest Key |
|----------|----------|--------------|
| **Network** | API endpoints, domains | `permissions.network` |
| **Filesystem** | Read/write specific paths | `permissions.filesystem` |
| **Environment** | Environment variable names | `permissions.environment` |
| **Tools** | OpenClaw tool names | `tools.required`, `tools.optional` |
| **Skills** | Other skills to invoke | `dependencies.skills` |
| **System** | Shell execution, process spawning | `permissions.system` |

### Permission Scoping

```json
{
  "permissions": {
    "network": [
      "api.clay.com",
      "*.supabase.co",
      "httpbin.org"
    ],
    "filesystem": [
      "read:./templates",
      "write:./output",
      "read:/shared/config"
    ],
    "environment": [
      "CLAY_API_KEY",
      "SUPABASE_URL",
      "SUPABASE_ANON_KEY"
    ],
    "system": [
      "shell:python3"
    ]
  }
}
```

### Permission Elevation

If a skill needs a permission it did not declare:
1. The runtime blocks the operation
2. The user is prompted: "Skill X is requesting access to Y. Allow? [y/n]"
3. If approved, a runtime-only permission is granted (not persisted)
4. If denied, the skill receives a PermissionDenied error

### Security Implications

- **ClawHub verified skills**: Permissions are reviewed by the OpenClaw team
- **Community skills**: Permissions are displayed to the user before install
- **Local skills**: No permission restrictions (developer mode)

---

## Skill Composition

Skills can call other skills, enabling complex multi-step operations built from simple, tested components.

### How Composition Works

```typescript
// Inside a "lead-pipeline" skill
async execute(context: SkillContext): Promise<SkillResult> {
  // Step 1: Discover businesses
  const businesses = await context.skills.invoke('@yourname/google-places-search', {
    query: context.inputs.industry,
    location: context.inputs.city,
    radius: 25
  });

  // Step 2: Enrich each business
  const enriched = [];
  for (const biz of businesses.data) {
    const enrichment = await context.skills.invoke('@yourname/lead-enrichment', {
      business_name: biz.name,
      website: biz.website,
      depth: 'full'
    });
    enriched.push({ ...biz, ...enrichment.data });
  }

  // Step 3: Score leads
  const scored = await context.skills.invoke('@yourname/lead-scorer', {
    leads: enriched,
    scoring_model: 'rise-local-15-signal'
  });

  return { status: 'success', data: scored.data };
}
```

### Composition Rules

1. **Dependency Declaration**: Composed skills must be listed in `dependencies.skills`
2. **Permission Inheritance**: The calling skill does NOT inherit the called skill's permissions; each skill runs in its own permission sandbox
3. **Error Propagation**: If a called skill fails, the calling skill receives the error and must handle it
4. **Circular Prevention**: The runtime detects and prevents circular skill invocations
5. **Depth Limit**: Maximum composition depth is configurable (default: 5 levels)

---

## Skill Versioning and Updates

### Semantic Versioning

All OpenClaw skills follow [semver](https://semver.org/):

- **MAJOR** (1.0.0 -> 2.0.0): Breaking changes to inputs, outputs, or behavior
- **MINOR** (1.0.0 -> 1.1.0): New features, backward-compatible
- **PATCH** (1.0.0 -> 1.0.1): Bug fixes, no behavior changes

### Version Pinning

```json
{
  "dependencies": {
    "skills": {
      "@openclaw/web-scraper": "^2.0.0",
      "@yourname/lead-enrichment": "~1.5.0",
      "@community/email-sender": "1.3.2"
    }
  }
}
```

- `^2.0.0`: Any 2.x.x (minor and patch updates)
- `~1.5.0`: Any 1.5.x (patch updates only)
- `1.3.2`: Exact version only

### Updating Skills

```bash
# Check for updates
openclaw skill outdated

# Update a specific skill
openclaw skill update @creator/skill-name

# Update all skills
openclaw skill update --all

# Update with major version changes (opt-in)
openclaw skill update @creator/skill-name --major
```

---

## Local vs Installed Skills

### Local Skills (Custom / Development)

- Stored in your project's `.openclaw/skills/` directory or a configured skills path
- No manifest validation required (developer mode)
- Hot-reload: changes take effect immediately
- Not published to ClawHub
- Full filesystem access (no sandboxing)
- Best for: prototyping, project-specific skills, skills in development

### Installed Skills (ClawHub)

- Stored in OpenClaw's global skills directory (e.g., `~/.openclaw/skills/`)
- Manifest validated on install
- Sandboxed: only declared permissions
- Updated via `openclaw skill update`
- Shared across all OpenClaw projects on the machine
- Best for: stable, reusable, community skills

### Override Priority

When a local skill and installed skill have the same name:
1. Local skill takes precedence (project-level override)
2. Warning is shown: "Local skill 'X' is overriding installed skill 'X'"

---

## Skill Configuration

### Per-Skill Environment Variables

Each skill can define its own configuration variables, separate from the global OpenClaw config.

```json
// config/schema.json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "API_KEY": {
      "type": "string",
      "description": "API key for the service",
      "required": true,
      "sensitive": true
    },
    "MAX_RESULTS": {
      "type": "integer",
      "description": "Maximum results to return",
      "default": 50,
      "minimum": 1,
      "maximum": 500
    },
    "OUTPUT_FORMAT": {
      "type": "string",
      "enum": ["json", "csv", "markdown"],
      "default": "json"
    }
  }
}
```

### Configuration Storage

- Sensitive values (marked `"sensitive": true`): Stored encrypted in OpenClaw's credential store
- Non-sensitive values: Stored in `~/.openclaw/skill-config/<skill-name>.json`
- Environment variables: Can be overridden via `OPENCLAW_SKILL_<SKILL_NAME>_<VAR>` env vars

### Accessing Configuration in Skill Code

```typescript
async execute(context: SkillContext): Promise<SkillResult> {
  const apiKey = context.config.get('API_KEY');        // Required, throws if missing
  const maxResults = context.config.get('MAX_RESULTS'); // Returns 50 if not set (default)
  const format = context.config.get('OUTPUT_FORMAT');   // Returns 'json' if not set
  // ...
}
```

---

## Skill Testing

### Testing Framework

OpenClaw provides a built-in testing framework for skills, based on Vitest (or your preferred test runner).

### Unit Tests

Test individual functions and logic without external dependencies:

```typescript
// tests/unit/logic.test.ts
import { describe, it, expect } from 'vitest';
import { scoreLeadSignals } from '../../lib/scoring';

describe('Lead Scoring', () => {
  it('should score a lead with all positive signals as high', () => {
    const signals = {
      has_website: true,
      website_mobile_friendly: true,
      no_existing_seo: true,
      high_review_count: true,
      // ... all 15 signals
    };
    const score = scoreLeadSignals(signals);
    expect(score).toBeGreaterThan(80);
    expect(score).toBeLessThanOrEqual(100);
  });
});
```

### Integration Tests

Test the skill's interaction with external services (using mocks or test accounts):

```typescript
// tests/integration/api-calls.test.ts
import { describe, it, expect } from 'vitest';
import { createTestContext } from '@openclaw/test-utils';
import MySkill from '../../index';

describe('MySkill Integration', () => {
  it('should enrich a known business', async () => {
    const context = createTestContext({
      inputs: { target: 'test-business-123' },
      config: { API_KEY: process.env.TEST_API_KEY },
      mocks: {
        web_fetch: (url) => {
          if (url.includes('api.example.com')) {
            return { status: 200, data: { name: 'Test Business' } };
          }
        }
      }
    });

    const skill = new MySkill();
    await skill.onLoad(context);
    const result = await skill.execute(context);

    expect(result.status).toBe('success');
    expect(result.data.name).toBe('Test Business');
  });
});
```

### Running Tests

```bash
# Run all tests for a skill
openclaw skill test my-skill-name

# Run with coverage
openclaw skill test my-skill-name --coverage

# Run in watch mode (during development)
openclaw skill test my-skill-name --watch

# Run specific test file
openclaw skill test my-skill-name --file tests/unit/logic.test.ts

# Test with real API calls (no mocks)
openclaw skill test my-skill-name --live
```

### Test Fixtures

Store sample inputs and expected outputs in `tests/fixtures/`:

```json
// tests/fixtures/input-1.json
{
  "target": "acme-plumbing",
  "depth": "deep"
}

// tests/fixtures/expected-output-1.json
{
  "status": "success",
  "data": {
    "name": "Acme Plumbing",
    "score": 85,
    "signals": { "has_website": true, "mobile_friendly": true }
  }
}
```

---

## Quick Reference: Common Commands

| Command | Description |
|---------|-------------|
| `openclaw skill create <name>` | Scaffold a new skill |
| `openclaw skill install <pkg>` | Install from ClawHub or path |
| `openclaw skill list` | List installed skills |
| `openclaw skill info <name>` | Show skill details |
| `openclaw skill config <name> set KEY=val` | Configure a skill |
| `openclaw skill test <name>` | Run skill tests |
| `openclaw skill pack` | Package for distribution |
| `openclaw skill publish` | Publish to ClawHub |
| `openclaw skill update <name>` | Update a skill |
| `openclaw skill remove <name>` | Uninstall a skill |

---

## Research Gaps and Open Questions

- **Exact AgentSkills spec location**: Need to find and review the full specification document
- **Runtime internals**: How exactly does the OpenClaw runtime load and sandbox skills?
- **Credential store details**: What encryption is used for sensitive config values?
- **Skill marketplace economics**: Are there paid skills on ClawHub? What is the revenue model?
- **Performance limits**: What are the timeout and resource limits for skill execution?
- **Offline skills**: Can skills run fully offline (no network)?

---

*Last updated: 2026-02-05*
*Status: Detailed architectural reference based on available OpenClaw documentation and reasonable inference from the AgentSkills standard*
