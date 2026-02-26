# n8n Workflow Integration Skill

## Goal

Build an OpenClaw skill that triggers, orchestrates, and monitors n8n workflows. This creates a bidirectional bridge: OpenClaw can start n8n workflows and receive their results, while n8n can trigger OpenClaw skills as part of its automation flows. Together, they form the automation backbone of the Rise Local operation.

---

## Your n8n Setup

- **Location**: Docker container at `Desktop/rise-local-n8n`
- **Access**: Local instance (self-hosted), accessible via `http://localhost:5678` (or configured port)
- **Custom nodes**: You have custom n8n nodes installed
- **Existing MCP**: n8n MCP server already configured for direct workflow management
- **Workflows**: Lead processing, email automation, data sync, and other Rise Local automations

---

## Integration Approaches

### Approach 1: Webhook Triggers (OpenClaw -> n8n)

**How it works**: Each n8n workflow can have a Webhook trigger node. OpenClaw calls the webhook URL with data, n8n executes the workflow, and returns the result.

```
OpenClaw Skill
  -> HTTP POST to n8n webhook URL
  -> n8n workflow executes
  -> n8n returns result to OpenClaw via webhook response
```

**Setup in n8n**:
1. Add a "Webhook" trigger node to the workflow
2. Configure it with a unique path (e.g., `/webhook/lead-enrichment`)
3. Set response mode to "Last Node" (returns the final node's output)
4. The full URL becomes: `http://localhost:5678/webhook/lead-enrichment`

**Calling from OpenClaw**:
```typescript
const result = await context.tools.web_fetch({
  url: 'http://localhost:5678/webhook/lead-enrichment',
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    business_name: 'Acme Plumbing',
    website: 'https://acmeplumbing.com',
    enrichment_depth: 'full'
  })
});
```

**Pros**: Simple, reliable, standard HTTP. Works without any n8n API credentials.
**Cons**: Synchronous (waits for workflow to complete). Long workflows may time out.

### Approach 2: n8n REST API (OpenClaw -> n8n)

**How it works**: OpenClaw uses the n8n REST API to manage workflows programmatically -- list, activate, execute, monitor, and retrieve results.

**Key API Endpoints**:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/workflows` | GET | List all workflows |
| `/api/v1/workflows/{id}` | GET | Get workflow details |
| `/api/v1/workflows/{id}/activate` | POST | Activate a workflow |
| `/api/v1/workflows/{id}/deactivate` | POST | Deactivate a workflow |
| `/api/v1/executions` | GET | List recent executions |
| `/api/v1/executions/{id}` | GET | Get execution details and output |
| `/api/v1/workflows/{id}/run` | POST | Manually trigger a workflow execution |

**Authentication**:
```typescript
// n8n API uses either API key or basic auth
const headers = {
  'X-N8N-API-KEY': config.N8N_API_KEY,
  'Content-Type': 'application/json'
};
```

**Executing a workflow via API**:
```typescript
// Trigger a workflow execution and get the execution ID
const triggerResponse = await context.tools.web_fetch({
  url: `${config.N8N_BASE_URL}/api/v1/workflows/${workflowId}/run`,
  method: 'POST',
  headers,
  body: JSON.stringify({
    // Input data for the workflow
    startData: {
      business_name: 'Acme Plumbing',
      website: 'https://acmeplumbing.com'
    }
  })
});

const executionId = triggerResponse.data.executionId;

// Poll for completion
let execution;
do {
  await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds
  execution = await context.tools.web_fetch({
    url: `${config.N8N_BASE_URL}/api/v1/executions/${executionId}`,
    headers
  });
} while (execution.data.status === 'running');

// Get the result
if (execution.data.status === 'success') {
  return execution.data.data.resultData;
} else {
  throw new Error(`Workflow execution failed: ${execution.data.data.error}`);
}
```

**Pros**: Full control over workflow lifecycle. Can trigger, monitor, and retrieve results asynchronously.
**Cons**: Requires n8n API key. More complex than webhook approach.

### Approach 3: n8n Calls OpenClaw (n8n -> OpenClaw)

**How it works**: n8n workflows use an HTTP Request node to call an OpenClaw endpoint, triggering OpenClaw skills from within n8n automation flows.

**Setup requirements**:
1. OpenClaw must expose an HTTP endpoint (webhook receiver or API)
2. n8n sends POST requests to this endpoint with skill invocation data

**n8n HTTP Request Node Configuration**:
```json
{
  "method": "POST",
  "url": "http://localhost:OPENCLAW_PORT/api/skills/invoke",
  "headers": {
    "Authorization": "Bearer OPENCLAW_API_KEY",
    "Content-Type": "application/json"
  },
  "body": {
    "skill": "@yourname/lead-enrichment",
    "inputs": {
      "website": "={{ $json.website }}",
      "depth": "full"
    }
  }
}
```

**RESEARCH GAP**: Need to confirm how OpenClaw exposes an API for external systems to trigger skills. This may require:
- An OpenClaw webhook receiver configuration
- An API server mode for OpenClaw
- A custom Edge Function or webhook handler that bridges to OpenClaw

**Pros**: n8n workflows can leverage AI/LLM capabilities via OpenClaw. Enables complex automation that combines structured workflows (n8n) with intelligent decision-making (OpenClaw).
**Cons**: Requires OpenClaw to have an API/webhook receiver. May need custom bridge.

---

## Bidirectional Communication Patterns

### Pattern 1: OpenClaw Orchestrates, n8n Executes

```
Use case: Lead arrives, needs multi-step processing

OpenClaw (brain):
  1. Receives new lead data
  2. Decides enrichment strategy based on lead type
  3. Calls n8n "lead-enrichment" workflow via webhook
  4. Receives enriched data back
  5. Runs AI-powered scoring and qualification
  6. Decides next action: outreach, nurture, or disqualify
  7. Calls n8n "outreach-sequence" workflow for qualified leads

n8n (hands):
  - "lead-enrichment" workflow: calls Clay API, Apollo, BuiltWith in parallel
  - "outreach-sequence" workflow: sends email, schedules follow-ups, creates GHL tasks
```

### Pattern 2: n8n Triggers, OpenClaw Decides

```
Use case: n8n monitors for events, OpenClaw provides intelligence

n8n (monitor):
  1. Webhook receives new form submission
  2. Enriches basic data (email verification, company lookup)
  3. Calls OpenClaw with enriched data

OpenClaw (brain):
  1. Receives enriched lead data from n8n
  2. Analyzes lead quality using AI
  3. Generates personalized outreach message
  4. Decides pipeline stage and follow-up sequence
  5. Returns: { stage, outreach_message, follow_up_plan, priority }

n8n (executor):
  1. Receives OpenClaw's decision
  2. Creates GHL contact with assigned stage
  3. Sends personalized outreach message
  4. Schedules follow-up tasks
```

### Pattern 3: Event-Driven Collaboration

```
Use case: Continuous monitoring and response

n8n "competitor-monitor" workflow (runs daily):
  1. Checks competitor websites for changes
  2. Scrapes new Google reviews
  3. Checks SEO ranking changes
  4. If significant changes detected: calls OpenClaw

OpenClaw "competitor-analyst" skill:
  1. Receives change data from n8n
  2. AI analyzes the significance and implications
  3. Generates competitive intelligence brief
  4. Decides which clients need to be notified
  5. Returns: { impact_assessment, affected_clients, recommended_actions }

n8n "notification" workflow:
  1. Receives OpenClaw's analysis
  2. Formats notification email/Slack message
  3. Sends to relevant team members
  4. Creates tasks in project management tool
```

---

## Reusing Existing n8n MCP

Your existing n8n MCP server provides direct workflow management capabilities. The OpenClaw skill should leverage this:

```typescript
// The n8n MCP tools available in the skill context:
// (These are the actual MCP tools you have configured)

// Search for workflows/nodes
await context.tools.n8n_search_nodes({ query: 'webhook' });

// Get node information
await context.tools.n8n_get_node({ nodeType: 'n8n-nodes-base.webhook' });

// Validate a workflow configuration
await context.tools.n8n_validate_workflow({ workflow: workflowJson });

// Get template workflows
await context.tools.n8n_get_template({ templateId: 123 });

// Search templates for patterns
await context.tools.n8n_search_templates({ query: 'lead enrichment' });
```

---

## Skill Design: @yourname/n8n-orchestrator

### skill.json Manifest (Key Sections)

```json
{
  "name": "@yourname/n8n-orchestrator",
  "version": "1.0.0",
  "description": "Trigger, monitor, and orchestrate n8n workflows from OpenClaw",
  "commands": ["/n8n", "/workflow", "/run-workflow"],
  "inputs": {
    "required": {
      "action": {
        "type": "string",
        "enum": [
          "trigger_workflow",
          "trigger_webhook",
          "check_status",
          "get_result",
          "list_workflows",
          "list_executions",
          "create_workflow",
          "activate_workflow",
          "deactivate_workflow",
          "get_workflow_stats"
        ]
      }
    },
    "optional": {
      "workflow_id": {
        "type": "string",
        "description": "n8n workflow ID"
      },
      "workflow_name": {
        "type": "string",
        "description": "n8n workflow name (alternative to ID)"
      },
      "webhook_path": {
        "type": "string",
        "description": "Webhook path for trigger_webhook action"
      },
      "data": {
        "type": "object",
        "description": "Data to pass to the workflow"
      },
      "execution_id": {
        "type": "string",
        "description": "Execution ID for status/result checks"
      },
      "wait_for_completion": {
        "type": "boolean",
        "default": true,
        "description": "Wait for workflow to complete before returning"
      },
      "timeout_seconds": {
        "type": "integer",
        "default": 300,
        "description": "Maximum time to wait for workflow completion"
      },
      "workflow_json": {
        "type": "object",
        "description": "Workflow definition for create_workflow action"
      }
    }
  },
  "outputs": {
    "execution_id": { "type": "string" },
    "status": { "type": "string", "enum": ["running", "success", "error", "waiting", "unknown"] },
    "result": { "type": "object", "description": "Workflow execution result data" },
    "duration_seconds": { "type": "number" },
    "workflows": { "type": "array", "description": "List of workflows (for list_workflows)" },
    "executions": { "type": "array", "description": "List of executions (for list_executions)" }
  },
  "permissions": {
    "network": ["localhost:5678", "n8n.yourdomain.com"],
    "environment": ["N8N_BASE_URL", "N8N_API_KEY", "N8N_WEBHOOK_BASE_URL"]
  },
  "tools": {
    "required": ["web_fetch"],
    "optional": ["n8n_search_nodes", "n8n_get_node", "n8n_validate_workflow"]
  }
}
```

### Core Implementation

```typescript
import { Skill, SkillContext, SkillResult } from '@openclaw/sdk';

export default class N8nOrchestrator extends Skill {
  private baseUrl: string = '';
  private apiKey: string = '';
  private webhookBaseUrl: string = '';

  async onLoad(context: SkillContext): Promise<void> {
    this.baseUrl = context.config.get('N8N_BASE_URL') || 'http://localhost:5678';
    this.apiKey = context.config.get('N8N_API_KEY');
    this.webhookBaseUrl = context.config.get('N8N_WEBHOOK_BASE_URL') || this.baseUrl;
  }

  async execute(context: SkillContext): Promise<SkillResult> {
    const { action } = context.inputs;

    switch (action) {
      case 'trigger_webhook':
        return await this.triggerViaWebhook(context);
      case 'trigger_workflow':
        return await this.triggerViaApi(context);
      case 'check_status':
        return await this.checkExecutionStatus(context);
      case 'get_result':
        return await this.getExecutionResult(context);
      case 'list_workflows':
        return await this.listWorkflows(context);
      case 'list_executions':
        return await this.listExecutions(context);
      default:
        return { status: 'error', error: `Unknown action: ${action}` };
    }
  }

  private async triggerViaWebhook(context: SkillContext): Promise<SkillResult> {
    const { webhook_path, data } = context.inputs;

    const url = `${this.webhookBaseUrl}/webhook/${webhook_path}`;
    context.log.info('Triggering n8n webhook', { url, dataKeys: Object.keys(data || {}) });

    const response = await context.tools.web_fetch({
      url,
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data || {})
    });

    return {
      status: 'success',
      data: {
        status: 'success',
        result: response.body,
        trigger_method: 'webhook',
        webhook_path
      }
    };
  }

  private async triggerViaApi(context: SkillContext): Promise<SkillResult> {
    const { workflow_id, workflow_name, data, wait_for_completion, timeout_seconds } = context.inputs;

    // Resolve workflow ID from name if needed
    let resolvedId = workflow_id;
    if (!resolvedId && workflow_name) {
      resolvedId = await this.resolveWorkflowId(context, workflow_name);
    }

    if (!resolvedId) {
      return { status: 'error', error: 'Either workflow_id or workflow_name is required' };
    }

    // Trigger execution
    const triggerResponse = await context.tools.web_fetch({
      url: `${this.baseUrl}/api/v1/workflows/${resolvedId}/run`,
      method: 'POST',
      headers: {
        'X-N8N-API-KEY': this.apiKey,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ startData: data || {} })
    });

    const executionId = triggerResponse.body?.data?.executionId;

    if (!wait_for_completion) {
      return {
        status: 'success',
        data: {
          execution_id: executionId,
          status: 'running',
          message: 'Workflow triggered. Use check_status to monitor.'
        }
      };
    }

    // Wait for completion
    return await this.waitForExecution(context, executionId, timeout_seconds || 300);
  }

  private async waitForExecution(
    context: SkillContext,
    executionId: string,
    timeoutSeconds: number
  ): Promise<SkillResult> {
    const startTime = Date.now();
    const timeoutMs = timeoutSeconds * 1000;
    let pollInterval = 2000; // Start with 2 seconds

    while (Date.now() - startTime < timeoutMs) {
      const response = await context.tools.web_fetch({
        url: `${this.baseUrl}/api/v1/executions/${executionId}`,
        headers: { 'X-N8N-API-KEY': this.apiKey }
      });

      const execution = response.body?.data;

      if (execution?.status === 'success') {
        return {
          status: 'success',
          data: {
            execution_id: executionId,
            status: 'success',
            result: execution.data?.resultData,
            duration_seconds: (Date.now() - startTime) / 1000
          }
        };
      }

      if (execution?.status === 'error') {
        return {
          status: 'error',
          error: `Workflow execution failed: ${execution.data?.error || 'Unknown error'}`,
          data: {
            execution_id: executionId,
            status: 'error',
            duration_seconds: (Date.now() - startTime) / 1000
          }
        };
      }

      // Report progress
      context.progress.update({
        message: `Waiting for workflow execution... (${Math.round((Date.now() - startTime) / 1000)}s)`
      });

      // Exponential backoff (max 10 seconds)
      await new Promise(resolve => setTimeout(resolve, pollInterval));
      pollInterval = Math.min(pollInterval * 1.5, 10000);
    }

    return {
      status: 'error',
      error: `Workflow execution timed out after ${timeoutSeconds} seconds`,
      data: { execution_id: executionId, status: 'unknown' }
    };
  }

  private async resolveWorkflowId(context: SkillContext, name: string): Promise<string | null> {
    const response = await context.tools.web_fetch({
      url: `${this.baseUrl}/api/v1/workflows`,
      headers: { 'X-N8N-API-KEY': this.apiKey }
    });

    const workflows = response.body?.data || [];
    const match = workflows.find((w: any) =>
      w.name.toLowerCase() === name.toLowerCase()
    );

    return match?.id || null;
  }
}
```

---

## Example Integrated Workflows

### Workflow 1: Lead Arrives -> n8n Enriches -> OpenClaw Scores -> n8n Routes to GHL

```
Trigger: New form submission via GHL webhook -> n8n

n8n Workflow "lead-processing":
  Node 1: Webhook trigger (receives form data)
  Node 2: HTTP Request to Clay API (enrich email/phone)
  Node 3: HTTP Request to BuiltWith API (tech stack)
  Node 4: HTTP Request to DataForSEO (SEO metrics)
  Node 5: HTTP Request to OpenClaw (score and qualify)
    -> POST /api/skills/invoke
    -> Skill: @yourname/lead-enrichment (scoring only)
    -> Returns: pain_score, recommended_services, pipeline_stage
  Node 6: IF node (pain_score >= 60?)
    -> Yes: HTTP Request to GHL API (create contact, add to pipeline)
    -> No: HTTP Request to GHL API (add to nurture list)
  Node 7: Slack notification (new qualified lead alert)
```

### Workflow 2: Client Requests Report -> OpenClaw Generates -> n8n Formats and Sends

```
Trigger: OpenClaw receives "/generate-report" command

OpenClaw Skill "report-generator":
  1. Queries Supabase for client data, pipeline metrics, enrichment stats
  2. Queries competitor scan data
  3. AI generates report narrative
  4. Triggers n8n "report-delivery" workflow

n8n Workflow "report-delivery":
  Node 1: Webhook trigger (receives report data from OpenClaw)
  Node 2: HTML template node (formats report as styled HTML)
  Node 3: PDF generation node (converts HTML to PDF)
  Node 4: Email node (sends PDF to client via SendGrid)
  Node 5: Google Drive node (stores PDF in client folder)
  Node 6: GHL API node (logs communication in CRM)
  Node 7: Slack notification (report sent confirmation)
```

### Workflow 3: Competitor Change -> n8n Alerts -> OpenClaw Analyzes

```
Trigger: n8n scheduled workflow (runs daily at 7 AM)

n8n Workflow "competitor-monitor":
  Node 1: Cron trigger (daily at 7 AM)
  Node 2: Supabase node (get list of tracked competitors)
  Node 3: Loop node (for each competitor):
    Node 3a: HTTP Request (fetch competitor homepage)
    Node 3b: Compare node (diff against stored version)
    Node 3c: IF node (significant change detected?)
      -> Yes: HTTP Request to OpenClaw (analyze change)
      -> No: Continue to next competitor
  Node 4: Supabase node (store scan results)
  Node 5: IF node (any alerts generated?)
    -> Yes: Slack notification + email to team
    -> No: Log "no changes" and end

OpenClaw "competitor-analyst" (called by Node 3c):
  1. Receives: competitor URL, old content, new content, change type
  2. AI analyzes what changed and why it matters
  3. Generates impact assessment
  4. Returns: { severity, summary, affected_clients, recommended_actions }
```

---

## Error Handling

### What to Do When n8n Workflow Fails

| Error Type | Detection | Response |
|------------|-----------|----------|
| **Workflow not found** | 404 from API | Log error, notify user, suggest checking workflow ID/name |
| **Webhook timeout** | HTTP timeout | Retry once, then fall back to async API trigger |
| **Execution error** | Status "error" in execution result | Log full error details, retry if transient, alert if persistent |
| **n8n service down** | Connection refused / 503 | Check Docker container status, attempt restart, alert |
| **Rate limiting** | 429 response | Back off exponentially, queue remaining requests |
| **Invalid input data** | Validation error in n8n node | Log which node failed and why, fix data and retry |

### Automatic Retry Strategy

```typescript
async function executeWithRetry(
  fn: () => Promise<any>,
  maxRetries: number = 3,
  backoffMs: number = 2000
): Promise<any> {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      if (attempt === maxRetries) throw error;

      const isRetryable =
        error.status === 429 ||
        error.status === 503 ||
        error.message.includes('ECONNREFUSED') ||
        error.message.includes('timeout');

      if (!isRetryable) throw error;

      const delay = backoffMs * Math.pow(2, attempt - 1);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
}
```

### n8n Health Check

```typescript
// Check if n8n is running and responsive
async function checkN8nHealth(context: SkillContext): Promise<boolean> {
  try {
    const response = await context.tools.web_fetch({
      url: `${this.baseUrl}/api/v1/workflows`,
      headers: { 'X-N8N-API-KEY': this.apiKey },
      timeout: 5000
    });
    return response.status === 200;
  } catch {
    return false;
  }
}

// If n8n is down, attempt Docker restart
async function attemptN8nRestart(context: SkillContext): Promise<void> {
  context.log.warn('n8n appears to be down. Attempting restart...');
  // This requires shell access and Docker
  await context.tools.shell({
    command: 'docker restart rise-local-n8n',
    timeout: 30000
  });
  // Wait for n8n to come back up
  await new Promise(resolve => setTimeout(resolve, 10000));
  const healthy = await checkN8nHealth(context);
  if (healthy) {
    context.log.info('n8n restarted successfully');
  } else {
    context.log.error('n8n failed to restart. Manual intervention required.');
  }
}
```

---

## Monitoring and Observability

### Workflow Execution History

```typescript
// Get execution stats for a workflow
async function getWorkflowStats(
  context: SkillContext,
  workflowId: string,
  days: number = 7
): Promise<WorkflowStats> {
  const response = await context.tools.web_fetch({
    url: `${this.baseUrl}/api/v1/executions?workflowId=${workflowId}&limit=100`,
    headers: { 'X-N8N-API-KEY': this.apiKey }
  });

  const executions = response.body?.data || [];
  const since = new Date(Date.now() - days * 24 * 60 * 60 * 1000);

  const recent = executions.filter((e: any) => new Date(e.startedAt) > since);

  return {
    total_executions: recent.length,
    successful: recent.filter((e: any) => e.status === 'success').length,
    failed: recent.filter((e: any) => e.status === 'error').length,
    success_rate: recent.length > 0
      ? (recent.filter((e: any) => e.status === 'success').length / recent.length * 100).toFixed(1) + '%'
      : 'N/A',
    avg_duration_seconds: recent.length > 0
      ? recent.reduce((sum: number, e: any) => {
          const start = new Date(e.startedAt).getTime();
          const end = new Date(e.stoppedAt).getTime();
          return sum + (end - start) / 1000;
        }, 0) / recent.length
      : 0,
    last_execution: recent[0]?.startedAt || 'Never',
    last_status: recent[0]?.status || 'Unknown',
    common_errors: getCommonErrors(recent.filter((e: any) => e.status === 'error'))
  };
}
```

### Dashboard Data

The skill can generate a monitoring overview:

```
/n8n get_workflow_stats

Output:
## n8n Workflow Health Dashboard (Last 7 Days)

| Workflow | Executions | Success Rate | Avg Duration | Last Run | Status |
|----------|-----------|-------------|-------------|----------|--------|
| lead-enrichment | 142 | 96.5% | 12.3s | 2h ago | Healthy |
| outreach-sequence | 89 | 98.9% | 3.1s | 4h ago | Healthy |
| competitor-monitor | 7 | 100% | 45.2s | 18h ago | Healthy |
| report-delivery | 12 | 91.7% | 8.7s | 3d ago | Warning |
| data-sync | 168 | 99.4% | 1.8s | 1h ago | Healthy |

Alerts:
- report-delivery: 1 failure in last 7 days (email delivery error on Feb 2)
- No critical issues detected
```

---

## Workflow Registry

Maintain a registry of known workflows and their purposes for the agent to reference:

```json
// config/workflow-registry.json
{
  "workflows": [
    {
      "id": "wf-001",
      "name": "lead-enrichment",
      "description": "Enrich lead data via Clay, Apollo, BuiltWith, DataForSEO",
      "webhook_path": "lead-enrichment",
      "expected_input": { "business_name": "string", "website": "string" },
      "expected_output": { "enriched_data": "object", "score": "number" },
      "avg_duration_seconds": 12,
      "category": "lead-processing"
    },
    {
      "id": "wf-002",
      "name": "outreach-sequence",
      "description": "Send multi-touch email outreach sequence via SendGrid",
      "webhook_path": "outreach-sequence",
      "expected_input": { "contact": "object", "sequence_type": "string" },
      "expected_output": { "emails_queued": "number", "sequence_id": "string" },
      "avg_duration_seconds": 3,
      "category": "communication"
    },
    {
      "id": "wf-003",
      "name": "competitor-monitor",
      "description": "Daily competitor website and review monitoring",
      "trigger": "cron",
      "schedule": "0 7 * * *",
      "expected_output": { "changes_detected": "array", "alerts": "array" },
      "avg_duration_seconds": 45,
      "category": "intelligence"
    },
    {
      "id": "wf-004",
      "name": "report-delivery",
      "description": "Format and send client reports via email with PDF attachment",
      "webhook_path": "report-delivery",
      "expected_input": { "client_id": "string", "report_data": "object" },
      "expected_output": { "email_sent": "boolean", "pdf_url": "string" },
      "avg_duration_seconds": 9,
      "category": "reporting"
    },
    {
      "id": "wf-005",
      "name": "data-sync",
      "description": "Sync data between Supabase, Airtable, and GHL",
      "trigger": "cron",
      "schedule": "*/30 * * * *",
      "expected_output": { "records_synced": "number", "errors": "array" },
      "avg_duration_seconds": 2,
      "category": "data-management"
    }
  ]
}
```

The agent can query this registry to determine which workflow to trigger for a given task, without needing to know workflow IDs.

---

## Configuration

```json
{
  "N8N_BASE_URL": {
    "type": "string",
    "description": "n8n instance URL (e.g., http://localhost:5678)",
    "default": "http://localhost:5678",
    "required": true
  },
  "N8N_API_KEY": {
    "type": "string",
    "description": "n8n REST API key",
    "sensitive": true,
    "required": true
  },
  "N8N_WEBHOOK_BASE_URL": {
    "type": "string",
    "description": "Base URL for webhook triggers (may differ from API URL if behind a proxy)",
    "default": "http://localhost:5678"
  },
  "DEFAULT_TIMEOUT_SECONDS": {
    "type": "integer",
    "description": "Default timeout for synchronous workflow execution",
    "default": 300,
    "minimum": 10,
    "maximum": 3600
  },
  "RETRY_MAX_ATTEMPTS": {
    "type": "integer",
    "description": "Maximum retry attempts for failed workflow triggers",
    "default": 3,
    "minimum": 0,
    "maximum": 10
  },
  "HEALTH_CHECK_INTERVAL_MINUTES": {
    "type": "integer",
    "description": "How often to check n8n health (0 to disable)",
    "default": 15,
    "minimum": 0,
    "maximum": 60
  }
}
```

---

## Testing Plan

### Unit Tests

- Workflow ID resolution from name
- Retry logic with exponential backoff
- Timeout handling
- Error classification and response
- Health check logic

### Integration Tests

- Trigger a test webhook and verify response
- Trigger a workflow via API and poll for result
- List workflows and verify expected workflows exist
- Get execution history and verify format

### End-to-End Tests

- Full lead processing: OpenClaw -> n8n enrichment -> OpenClaw scoring -> n8n GHL routing
- Report generation: OpenClaw generates -> n8n formats and sends
- Error recovery: Trigger workflow with bad data, verify graceful error handling

---

*Last updated: 2026-02-05*
*Status: Skill design complete; leverages existing n8n Docker instance and n8n MCP server*
