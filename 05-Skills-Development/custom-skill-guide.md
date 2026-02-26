# Custom Skill Development Guide

## Overview

This is a step-by-step guide to building a custom OpenClaw skill from scratch. By the end, you will have a working skill that can be tested locally, used in your OpenClaw agent, and optionally published to ClawHub.

---

## Step 1: Scaffold the Skill

```bash
# Create a new skill with the OpenClaw CLI
openclaw skill create my-skill-name

# Interactive mode - answers prompts for metadata
openclaw skill create my-skill-name --interactive

# Create with a specific template
openclaw skill create my-skill-name --template api-integration
# Available templates: basic, api-integration, web-scraper, data-processor, workflow
```

### What the Scaffold Creates

```
my-skill-name/
├── skill.json              # Pre-filled manifest (you edit this)
├── index.ts                # Skeleton entry point
├── prompts/
│   └── system.md           # Empty system prompt template
├── config/
│   ├── defaults.json       # Empty defaults
│   └── schema.json         # Empty config schema
├── tests/
│   ├── unit/
│   │   └── index.test.ts   # Skeleton unit test
│   └── fixtures/
│       └── .gitkeep
├── README.md               # Template README
├── package.json            # Node.js package config
├── tsconfig.json           # TypeScript config
└── .gitignore
```

After scaffolding, `cd` into the skill directory and run `npm install` (or `pnpm install`) to set up the development environment.

---

## Step 2: Define the Manifest (skill.json)

The manifest is the most important file. It tells OpenClaw everything about your skill.

### Complete Example: "send-email" Skill

```json
{
  "name": "@yourname/send-email",
  "version": "1.0.0",
  "description": "Compose and send professional emails with AI-generated content",
  "agentskills": "1.0",
  "author": {
    "name": "Your Name",
    "email": "you@example.com"
  },
  "license": "MIT",
  "entry": "index.ts",
  "commands": ["/send-email", "/email"],
  "triggers": {
    "slash_command": "/send-email",
    "natural_language": [
      "send an email",
      "compose email",
      "email this person",
      "draft an email"
    ],
    "programmatic": true
  },
  "inputs": {
    "required": {
      "to": {
        "type": "string",
        "description": "Recipient email address"
      },
      "subject": {
        "type": "string",
        "description": "Email subject line"
      }
    },
    "optional": {
      "body": {
        "type": "string",
        "description": "Email body (if not provided, AI generates based on subject)"
      },
      "tone": {
        "type": "string",
        "enum": ["professional", "friendly", "urgent", "casual"],
        "default": "professional",
        "description": "Tone of the email"
      },
      "cc": {
        "type": "array",
        "items": { "type": "string" },
        "description": "CC recipients"
      },
      "attachments": {
        "type": "array",
        "items": { "type": "string" },
        "description": "File paths to attach"
      },
      "template": {
        "type": "string",
        "description": "Name of email template to use"
      }
    }
  },
  "outputs": {
    "message_id": {
      "type": "string",
      "description": "ID of the sent message"
    },
    "status": {
      "type": "string",
      "enum": ["sent", "queued", "draft", "failed"]
    },
    "body_used": {
      "type": "string",
      "description": "The actual email body that was sent"
    }
  },
  "tools": {
    "required": ["web_fetch"],
    "optional": ["file_read"]
  },
  "permissions": {
    "network": ["api.sendgrid.com", "smtp.gmail.com"],
    "filesystem": ["read:./templates", "read:./attachments"],
    "environment": ["SENDGRID_API_KEY", "FROM_EMAIL", "FROM_NAME"]
  },
  "dependencies": {
    "npm": {
      "@sendgrid/mail": "^7.7.0",
      "zod": "^3.22.0"
    }
  },
  "config": {
    "schema": "config/schema.json",
    "defaults": "config/defaults.json"
  },
  "keywords": ["email", "communication", "outreach", "sendgrid"]
}
```

### Manifest Fields Reference

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Scoped package name: `@namespace/skill-name` |
| `version` | Yes | Semantic version: `1.0.0` |
| `description` | Yes | One-line description (max 120 chars) |
| `agentskills` | Yes | AgentSkills spec version targeted |
| `entry` | Yes | Path to main skill file |
| `commands` | Yes | Slash commands that trigger this skill |
| `triggers` | No | Natural language and programmatic triggers |
| `inputs` | Yes | Input parameter definitions |
| `outputs` | Yes | Output schema definition |
| `tools` | Yes | Required and optional tool declarations |
| `permissions` | Yes | Network, filesystem, environment access |
| `dependencies` | No | Skill and npm dependencies |
| `config` | No | Configuration schema and defaults |
| `keywords` | No | Search keywords for ClawHub |

---

## Step 3: Write the Skill Logic (Entry Point)

The entry point is the core of your skill. It handles input validation, business logic, tool invocation, and result formatting.

### Complete Example: "send-email" Skill

```typescript
// index.ts
import { Skill, SkillContext, SkillResult } from '@openclaw/sdk';
import { z } from 'zod';

// Input validation schema (mirrors skill.json inputs but with runtime validation)
const InputSchema = z.object({
  to: z.string().email('Invalid recipient email address'),
  subject: z.string().min(1, 'Subject cannot be empty').max(200),
  body: z.string().optional(),
  tone: z.enum(['professional', 'friendly', 'urgent', 'casual']).default('professional'),
  cc: z.array(z.string().email()).optional(),
  attachments: z.array(z.string()).optional(),
  template: z.string().optional(),
});

export default class SendEmailSkill extends Skill {
  private apiKey: string = '';
  private fromEmail: string = '';
  private fromName: string = '';

  // ---- LIFECYCLE: Load ----
  async onLoad(context: SkillContext): Promise<void> {
    // Retrieve and validate configuration
    this.apiKey = context.config.get('SENDGRID_API_KEY');
    this.fromEmail = context.config.get('FROM_EMAIL');
    this.fromName = context.config.get('FROM_NAME') || 'OpenClaw Agent';

    if (!this.apiKey) {
      throw new Error(
        'SENDGRID_API_KEY is required. Run: openclaw skill config @yourname/send-email set SENDGRID_API_KEY=your-key'
      );
    }
    if (!this.fromEmail) {
      throw new Error(
        'FROM_EMAIL is required. Run: openclaw skill config @yourname/send-email set FROM_EMAIL=you@domain.com'
      );
    }
  }

  // ---- LIFECYCLE: Execute ----
  async execute(context: SkillContext): Promise<SkillResult> {
    // Step 1: Validate inputs
    const parsed = InputSchema.safeParse(context.inputs);
    if (!parsed.success) {
      return {
        status: 'error',
        error: `Invalid inputs: ${parsed.error.issues.map(i => i.message).join(', ')}`,
      };
    }
    const inputs = parsed.data;

    // Step 2: Generate email body if not provided
    let emailBody = inputs.body;
    if (!emailBody) {
      emailBody = await this.generateEmailBody(context, inputs.subject, inputs.tone, inputs.to);
    }

    // Step 3: Apply template if specified
    if (inputs.template) {
      emailBody = await this.applyTemplate(context, inputs.template, emailBody);
    }

    // Step 4: Send the email via SendGrid
    try {
      const result = await this.sendViaSendGrid(context, {
        to: inputs.to,
        cc: inputs.cc,
        subject: inputs.subject,
        body: emailBody,
        attachments: inputs.attachments,
      });

      return {
        status: 'success',
        data: {
          message_id: result.messageId,
          status: 'sent',
          body_used: emailBody,
        },
        metadata: {
          provider: 'sendgrid',
          timestamp: new Date().toISOString(),
          recipient: inputs.to,
        },
      };
    } catch (error) {
      context.log.error('Failed to send email', { error: error.message });
      return {
        status: 'error',
        error: `Failed to send email: ${error.message}`,
        data: {
          status: 'failed',
          body_used: emailBody,
        },
      };
    }
  }

  // ---- PRIVATE METHODS ----

  private async generateEmailBody(
    context: SkillContext,
    subject: string,
    tone: string,
    recipient: string
  ): Promise<string> {
    // Use the agent's LLM to generate email content
    const prompt = `Write a ${tone} email about: ${subject}.
    The recipient is: ${recipient}.
    Keep it concise (2-3 paragraphs).
    Do not include subject line or greeting - just the body.`;

    const generated = await context.llm.generate(prompt);
    return generated.text;
  }

  private async applyTemplate(
    context: SkillContext,
    templateName: string,
    body: string
  ): Promise<string> {
    // Read template file
    const templatePath = `./templates/${templateName}.html`;
    const template = await context.tools.file_read({ path: templatePath });

    // Replace {{body}} placeholder with actual content
    return template.content.replace('{{body}}', body);
  }

  private async sendViaSendGrid(
    context: SkillContext,
    params: {
      to: string;
      cc?: string[];
      subject: string;
      body: string;
      attachments?: string[];
    }
  ): Promise<{ messageId: string }> {
    const response = await context.tools.web_fetch({
      url: 'https://api.sendgrid.com/v3/mail/send',
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        personalizations: [{
          to: [{ email: params.to }],
          cc: params.cc?.map(email => ({ email })),
        }],
        from: { email: this.fromEmail, name: this.fromName },
        subject: params.subject,
        content: [
          { type: 'text/plain', value: params.body },
          { type: 'text/html', value: params.body.replace(/\n/g, '<br>') },
        ],
      }),
    });

    if (response.status !== 202) {
      throw new Error(`SendGrid API returned status ${response.status}: ${response.body}`);
    }

    return {
      messageId: response.headers['x-message-id'] || `msg-${Date.now()}`,
    };
  }

  // ---- LIFECYCLE: Unload ----
  async onUnload(): Promise<void> {
    // No cleanup needed for this skill
  }
}
```

---

## Step 4: Define Prompts

Prompts shape how the agent behaves when the skill is active. They are loaded into the agent's context window when the skill executes.

### System Prompt (prompts/system.md)

```markdown
# Send Email Skill

You are operating in email composition and sending mode. Your job is to help the user compose and send professional emails.

## Guidelines

1. **Clarity**: Write clear, concise emails. Avoid jargon unless the context demands it.
2. **Tone Matching**: Match the requested tone exactly:
   - Professional: formal language, proper greetings, structured paragraphs
   - Friendly: warm language, first-name basis, conversational
   - Urgent: direct language, clear action items, deadline emphasis
   - Casual: relaxed language, brief, minimal formality
3. **Personalization**: Use any available context about the recipient to personalize.
4. **Call to Action**: Every email should have a clear call to action unless it is purely informational.
5. **Length**: Default to 2-3 paragraphs unless the user specifies otherwise.

## Before Sending

Always confirm with the user before sending:
- Show the composed email
- Confirm the recipient address
- Ask if any changes are needed
- Only send after explicit approval

## After Sending

Report the outcome:
- Confirm successful send with message ID
- If failed, explain the error and suggest fixes
```

### Few-Shot Examples (prompts/examples/)

```markdown
<!-- prompts/examples/cold-outreach.md -->
# Example: Cold Outreach Email

**Input**:
- To: john@acmeplumbing.com
- Subject: "Website that brings in more customers"
- Tone: professional

**Output**:
Hi John,

I came across Acme Plumbing while researching top-rated plumbing companies in Austin. Your 4.8-star Google rating speaks volumes about the quality of your work.

I help local service businesses like yours get more customers through their website. Many plumbers I work with were surprised to learn that their website was actually turning away potential customers due to slow load times and missing mobile optimization.

Would you be open to a quick 10-minute call this week to see if there are some easy wins for Acme Plumbing? No pressure at all -- just a friendly conversation.

Best regards,
[Your Name]
```

---

## Step 5: Declare Tools

Tools are external capabilities the skill needs. They are declared in the manifest and optionally have custom handlers.

### Tool Declaration in skill.json

```json
{
  "tools": {
    "required": ["web_fetch"],
    "optional": ["file_read", "browser"]
  }
}
```

### Built-in OpenClaw Tools

| Tool Name | Description | Common Use |
|-----------|-------------|------------|
| `web_fetch` | HTTP requests (GET, POST, etc.) | API calls |
| `file_read` | Read local files | Templates, config |
| `file_write` | Write local files | Output files, logs |
| `browser` | Playwright browser automation | Web scraping, screenshots |
| `code_execution` | Run code in sandboxed environment | Data processing |
| `shell` | Execute shell commands | System operations |
| `database` | Database queries (if configured) | Data storage/retrieval |

### Custom Tool Handlers

If your skill needs a tool that does not exist, you can define custom tool handlers:

```typescript
// tools/handlers/email-validator.ts
import { ToolHandler, ToolResult } from '@openclaw/sdk';

export const emailValidator: ToolHandler = {
  name: 'validate_email',
  description: 'Validate an email address using ZeroBounce API',
  parameters: {
    email: { type: 'string', description: 'Email to validate', required: true }
  },
  async execute(params: { email: string }): Promise<ToolResult> {
    const response = await fetch(
      `https://api.zerobounce.net/v2/validate?api_key=${process.env.ZEROBOUNCE_KEY}&email=${params.email}`
    );
    const data = await response.json();
    return {
      valid: data.status === 'valid',
      status: data.status,
      sub_status: data.sub_status,
      did_you_mean: data.did_you_mean
    };
  }
};
```

Register custom tools in `skill.json`:

```json
{
  "tools": {
    "required": ["web_fetch"],
    "custom": [
      {
        "handler": "tools/handlers/email-validator.ts",
        "name": "validate_email"
      }
    ]
  }
}
```

---

## Step 6: Add Configuration

### Configuration Schema (config/schema.json)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "SENDGRID_API_KEY": {
      "type": "string",
      "description": "SendGrid API key for sending emails",
      "sensitive": true,
      "required": true
    },
    "FROM_EMAIL": {
      "type": "string",
      "format": "email",
      "description": "Sender email address (must be verified in SendGrid)",
      "required": true
    },
    "FROM_NAME": {
      "type": "string",
      "description": "Sender display name",
      "default": "OpenClaw Agent"
    },
    "MAX_ATTACHMENTS": {
      "type": "integer",
      "description": "Maximum number of attachments per email",
      "default": 5,
      "minimum": 0,
      "maximum": 10
    },
    "REQUIRE_CONFIRMATION": {
      "type": "boolean",
      "description": "Whether to require user confirmation before sending",
      "default": true
    }
  }
}
```

### Default Values (config/defaults.json)

```json
{
  "FROM_NAME": "OpenClaw Agent",
  "MAX_ATTACHMENTS": 5,
  "REQUIRE_CONFIRMATION": true
}
```

---

## Step 7: Write Tests

### Unit Tests (tests/unit/index.test.ts)

```typescript
import { describe, it, expect, vi } from 'vitest';
import { createMockContext } from '@openclaw/test-utils';
import SendEmailSkill from '../../index';

describe('SendEmailSkill', () => {

  describe('Input Validation', () => {
    it('should reject invalid email address', async () => {
      const context = createMockContext({
        inputs: { to: 'not-an-email', subject: 'Test' },
        config: { SENDGRID_API_KEY: 'test-key', FROM_EMAIL: 'from@test.com' }
      });
      const skill = new SendEmailSkill();
      await skill.onLoad(context);
      const result = await skill.execute(context);
      expect(result.status).toBe('error');
      expect(result.error).toContain('Invalid');
    });

    it('should reject empty subject', async () => {
      const context = createMockContext({
        inputs: { to: 'valid@email.com', subject: '' },
        config: { SENDGRID_API_KEY: 'test-key', FROM_EMAIL: 'from@test.com' }
      });
      const skill = new SendEmailSkill();
      await skill.onLoad(context);
      const result = await skill.execute(context);
      expect(result.status).toBe('error');
    });

    it('should accept valid inputs with defaults', async () => {
      const context = createMockContext({
        inputs: { to: 'valid@email.com', subject: 'Hello' },
        config: { SENDGRID_API_KEY: 'test-key', FROM_EMAIL: 'from@test.com' },
        mocks: {
          web_fetch: vi.fn().mockResolvedValue({ status: 202, headers: { 'x-message-id': 'test-123' } }),
          llm: { generate: vi.fn().mockResolvedValue({ text: 'Generated body text' }) }
        }
      });
      const skill = new SendEmailSkill();
      await skill.onLoad(context);
      const result = await skill.execute(context);
      expect(result.status).toBe('success');
      expect(result.data.status).toBe('sent');
    });
  });

  describe('Configuration', () => {
    it('should throw if SENDGRID_API_KEY is missing', async () => {
      const context = createMockContext({
        config: { FROM_EMAIL: 'from@test.com' }
      });
      const skill = new SendEmailSkill();
      await expect(skill.onLoad(context)).rejects.toThrow('SENDGRID_API_KEY');
    });
  });

  describe('Email Generation', () => {
    it('should generate body when not provided', async () => {
      const generateMock = vi.fn().mockResolvedValue({ text: 'Auto-generated email body' });
      const fetchMock = vi.fn().mockResolvedValue({
        status: 202,
        headers: { 'x-message-id': 'test-456' }
      });

      const context = createMockContext({
        inputs: { to: 'client@business.com', subject: 'Follow up on our call', tone: 'professional' },
        config: { SENDGRID_API_KEY: 'test-key', FROM_EMAIL: 'from@test.com' },
        mocks: {
          web_fetch: fetchMock,
          llm: { generate: generateMock }
        }
      });

      const skill = new SendEmailSkill();
      await skill.onLoad(context);
      const result = await skill.execute(context);

      expect(generateMock).toHaveBeenCalledOnce();
      expect(result.data.body_used).toBe('Auto-generated email body');
    });
  });
});
```

### Integration Tests (tests/integration/sendgrid.test.ts)

```typescript
import { describe, it, expect } from 'vitest';
import { createTestContext } from '@openclaw/test-utils';
import SendEmailSkill from '../../index';

// These tests require real API keys -- run with: openclaw skill test --live
describe('SendGrid Integration (Live)', () => {
  it('should send a real test email', async () => {
    const context = createTestContext({
      inputs: {
        to: process.env.TEST_RECIPIENT_EMAIL!,
        subject: `OpenClaw Test Email ${Date.now()}`,
        body: 'This is an automated test email from OpenClaw skill testing.',
      },
      config: {
        SENDGRID_API_KEY: process.env.SENDGRID_API_KEY!,
        FROM_EMAIL: process.env.FROM_EMAIL!,
      }
    });

    const skill = new SendEmailSkill();
    await skill.onLoad(context);
    const result = await skill.execute(context);

    expect(result.status).toBe('success');
    expect(result.data.message_id).toBeTruthy();
    expect(result.data.status).toBe('sent');
  });
});
```

---

## Step 8: Test Locally

```bash
# Run unit tests (default -- uses mocks, no real API calls)
openclaw skill test send-email

# Run with coverage report
openclaw skill test send-email --coverage

# Run in watch mode during development
openclaw skill test send-email --watch

# Run integration tests with real APIs
openclaw skill test send-email --live

# Test the skill interactively (loads it into a temporary agent session)
openclaw skill try send-email
# This opens an interactive session where you can invoke the skill and see results

# Validate the skill manifest and structure
openclaw skill validate ./send-email
```

### Debugging During Testing

```bash
# Enable verbose logging
openclaw skill test send-email --verbose

# Enable debug mode (step-through)
openclaw skill test send-email --debug

# Run a specific test file
openclaw skill test send-email --file tests/unit/index.test.ts

# Run tests matching a pattern
openclaw skill test send-email --filter "Email Generation"
```

---

## Step 9: Package

```bash
# Package the skill for distribution
openclaw skill pack

# This creates: send-email-1.0.0.tgz
# The package includes: compiled code, manifest, prompts, config schemas, README

# Verify the package contents
openclaw skill pack --dry-run
# Shows what would be included without creating the archive
```

### What Gets Packaged

- `skill.json` (manifest)
- Compiled JavaScript (from TypeScript)
- `prompts/` directory
- `config/schema.json` and `config/defaults.json`
- `README.md`
- `LICENSE`
- `CHANGELOG.md` (if exists)

### What Does NOT Get Packaged

- `node_modules/` (dependencies installed on user's machine)
- `tests/` (not needed at runtime)
- `.env` files (never publish secrets)
- Source TypeScript files (compiled JS is sufficient)
- `.git/` directory

---

## Step 10: Publish (Optional)

```bash
# Login to ClawHub (one-time)
openclaw auth login

# Publish to ClawHub
openclaw skill publish

# Output:
# Published @yourname/send-email@1.0.0 to ClawHub
# View at: https://clawhub.openclaw.sh/@yourname/send-email

# Publish a beta/pre-release version
openclaw skill publish --tag beta

# Update an existing published skill (bump version in skill.json first)
openclaw skill publish
```

---

## Best Practices

### Error Handling

```typescript
async execute(context: SkillContext): Promise<SkillResult> {
  try {
    // Wrap all external calls in try/catch
    const data = await context.tools.web_fetch({ url: '...' });

    // Validate responses
    if (!data || !data.body) {
      return { status: 'error', error: 'API returned empty response' };
    }

    // Type-check data
    if (typeof data.body.results !== 'object') {
      return { status: 'error', error: 'Unexpected API response format' };
    }

    return { status: 'success', data: data.body };
  } catch (error) {
    // Log the full error for debugging
    context.log.error('Skill execution failed', {
      error: error.message,
      stack: error.stack,
      inputs: context.inputs
    });

    // Return a user-friendly error
    if (error.message.includes('401')) {
      return { status: 'error', error: 'Authentication failed. Check your API key configuration.' };
    }
    if (error.message.includes('429')) {
      return { status: 'error', error: 'Rate limited. Please wait a moment and try again.' };
    }
    return { status: 'error', error: `Unexpected error: ${error.message}` };
  }
}
```

### Logging

```typescript
// Use context.log for structured logging
context.log.info('Starting enrichment', { target: inputs.target });
context.log.warn('API returned partial data', { missing_fields: ['email', 'phone'] });
context.log.error('API call failed', { status: 500, url: apiUrl });
context.log.debug('Raw API response', { body: response.body }); // Only shown in debug mode
```

### Timeout Management

```typescript
// Set timeouts on external calls
const data = await context.tools.web_fetch({
  url: 'https://api.slow-service.com/data',
  timeout: 10000,  // 10 seconds
});

// For long-running skills, report progress
async execute(context: SkillContext): Promise<SkillResult> {
  const leads = context.inputs.leads;  // array of 50 leads

  for (let i = 0; i < leads.length; i++) {
    await this.processLead(context, leads[i]);

    // Report progress to the user
    context.progress.update({
      current: i + 1,
      total: leads.length,
      message: `Enriching lead ${i + 1} of ${leads.length}: ${leads[i].name}`
    });
  }
  // ...
}
```

### Input Sanitization

```typescript
// Always sanitize user inputs before using in API calls or queries
import { sanitize } from '@openclaw/utils';

const safeName = sanitize.string(inputs.business_name);  // Remove injection characters
const safeUrl = sanitize.url(inputs.website);             // Validate and normalize URL
const safeEmail = sanitize.email(inputs.email);           // Validate email format
```

---

## Debugging Skills

### Log Inspection

```bash
# View skill execution logs
openclaw skill logs send-email

# View logs with debug level
openclaw skill logs send-email --level debug

# Tail logs in real-time
openclaw skill logs send-email --follow

# View logs for a specific execution
openclaw skill logs send-email --execution-id exec-abc123
```

### Interactive Debugging

```bash
# Start skill in debug mode
openclaw skill debug send-email

# This pauses at each step and shows:
# - Current inputs
# - Tool calls being made
# - API responses received
# - Generated content
# - Final output
```

### Test Fixtures

Create realistic test data to ensure your skill handles edge cases:

```json
// tests/fixtures/edge-cases/
// unicode-name.json - business with unicode characters
{
  "to": "jose@caf\u00e9-del-sol.com",
  "subject": "Your Caf\u00e9 Del Sol Website"
}

// long-subject.json - subject at max length
{
  "to": "test@example.com",
  "subject": "This is a very long subject line that tests the maximum character limit of two hundred characters for email subjects which some email clients may truncate or handle differently"
}

// missing-optional.json - only required fields
{
  "to": "minimal@test.com",
  "subject": "Minimal test"
}
```

---

## Skill Development Checklist

Before considering a skill complete, verify:

- [ ] `skill.json` manifest is complete and valid
- [ ] All required inputs are documented with types and descriptions
- [ ] All outputs are documented with types and descriptions
- [ ] Permissions are minimal (only what the skill actually needs)
- [ ] System prompt provides clear guidance to the agent
- [ ] Unit tests cover input validation, happy path, and error cases
- [ ] Integration tests exist for external API interactions
- [ ] Error messages are user-friendly (not raw stack traces)
- [ ] Logging is present at appropriate levels
- [ ] Configuration schema validates all settings
- [ ] README.md explains installation, configuration, and usage
- [ ] `openclaw skill validate` passes with no errors
- [ ] Tested locally with `openclaw skill try`

---

*Last updated: 2026-02-05*
*Status: Complete step-by-step development guide with full "send-email" example*
