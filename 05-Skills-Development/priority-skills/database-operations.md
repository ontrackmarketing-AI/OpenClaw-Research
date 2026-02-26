# Database Operations Skill

## Goal

Build an OpenClaw skill that manages database operations across both Supabase (primary) and Airtable (secondary). This skill is a foundational dependency -- most other skills need to read/write data. It replaces and extends the existing Claude Code `supabase-ops` skill.

---

## Supabase Operations

### Your Supabase Setup

- **Instance**: Rise Local production Supabase project
- **Tables**: Leads, clients, enrichment data, pipeline tracking, sessions, and more
- **Features used**: PostgreSQL, pgvector (for embeddings/RAG), Realtime, Edge Functions
- **Existing skill**: `supabase-ops` Claude Code skill handles basic CRUD

### CRUD Operations

#### Create (Insert)

```typescript
// Single record insert
async function insertRecord(table: string, data: Record<string, any>) {
  const { data: result, error } = await supabase
    .from(table)
    .insert(data)
    .select();

  if (error) throw new Error(`Insert failed: ${error.message}`);
  return result[0];
}

// Batch insert (up to 1000 records)
async function batchInsert(table: string, records: Record<string, any>[]) {
  const { data: result, error } = await supabase
    .from(table)
    .insert(records)
    .select();

  if (error) throw new Error(`Batch insert failed: ${error.message}`);
  return result;
}

// Upsert (insert or update on conflict)
async function upsertRecord(table: string, data: Record<string, any>, onConflict: string) {
  const { data: result, error } = await supabase
    .from(table)
    .upsert(data, { onConflict })
    .select();

  if (error) throw new Error(`Upsert failed: ${error.message}`);
  return result[0];
}
```

#### Read (Select)

```typescript
// Simple query
async function getRecords(table: string, filters?: QueryFilters) {
  let query = supabase.from(table).select(filters?.select || '*');

  // Apply filters
  if (filters?.eq) {
    for (const [key, value] of Object.entries(filters.eq)) {
      query = query.eq(key, value);
    }
  }
  if (filters?.gt) query = query.gt(filters.gt.column, filters.gt.value);
  if (filters?.lt) query = query.lt(filters.lt.column, filters.lt.value);
  if (filters?.ilike) query = query.ilike(filters.ilike.column, `%${filters.ilike.value}%`);
  if (filters?.in) query = query.in(filters.in.column, filters.in.values);
  if (filters?.order) query = query.order(filters.order.column, { ascending: filters.order.ascending });
  if (filters?.limit) query = query.limit(filters.limit);
  if (filters?.offset) query = query.range(filters.offset, filters.offset + (filters.limit || 10) - 1);

  const { data, error, count } = await query;
  if (error) throw new Error(`Query failed: ${error.message}`);
  return { data, count };
}

// Complex query with joins
async function getRecordsWithJoin(table: string, select: string) {
  // Example: 'id, name, enrichments(pain_score, tech_stack), pipeline_stages(name, entered_at)'
  const { data, error } = await supabase
    .from(table)
    .select(select);

  if (error) throw new Error(`Join query failed: ${error.message}`);
  return data;
}

// Aggregation via RPC (stored function)
async function runAggregation(functionName: string, params: Record<string, any>) {
  const { data, error } = await supabase.rpc(functionName, params);
  if (error) throw new Error(`RPC call failed: ${error.message}`);
  return data;
}
```

#### Update

```typescript
// Update with filters
async function updateRecords(
  table: string,
  data: Record<string, any>,
  filters: { column: string; value: any }[]
) {
  let query = supabase.from(table).update(data);

  for (const filter of filters) {
    query = query.eq(filter.column, filter.value);
  }

  const { data: result, error } = await query.select();
  if (error) throw new Error(`Update failed: ${error.message}`);
  return result;
}
```

#### Delete

```typescript
// Delete with safety check
async function deleteRecords(
  table: string,
  filters: { column: string; value: any }[],
  confirmDeletion: boolean = false
) {
  if (!confirmDeletion) {
    // First, count how many records would be deleted
    let countQuery = supabase.from(table).select('id', { count: 'exact' });
    for (const filter of filters) {
      countQuery = countQuery.eq(filter.column, filter.value);
    }
    const { count } = await countQuery;

    return {
      status: 'confirmation_required',
      message: `This will delete ${count} record(s) from '${table}'. Set confirmDeletion=true to proceed.`,
      affected_count: count
    };
  }

  let query = supabase.from(table).delete();
  for (const filter of filters) {
    query = query.eq(filter.column, filter.value);
  }

  const { data, error } = await query.select();
  if (error) throw new Error(`Delete failed: ${error.message}`);
  return { status: 'deleted', count: data.length };
}
```

### Schema Operations

```typescript
// List all tables (via information_schema)
async function listTables() {
  const { data, error } = await supabase.rpc('get_all_tables');
  // Requires a stored function:
  // CREATE FUNCTION get_all_tables() RETURNS TABLE(table_name text, row_count bigint)
  // AS $$ SELECT ... FROM information_schema.tables ... $$ LANGUAGE sql;
  return data;
}

// Get table schema (columns, types, constraints)
async function getTableSchema(tableName: string) {
  const { data, error } = await supabase.rpc('get_table_schema', { p_table_name: tableName });
  return data;
}

// Run a migration (SQL)
async function runMigration(sql: string, description: string) {
  // Log migration before executing
  await supabase.from('schema_migrations').insert({
    description,
    sql,
    status: 'pending',
    created_at: new Date().toISOString()
  });

  // Execute via RPC or Edge Function
  const { data, error } = await supabase.rpc('execute_migration', { p_sql: sql });

  if (error) {
    await supabase.from('schema_migrations').update({ status: 'failed', error: error.message });
    throw error;
  }

  await supabase.from('schema_migrations').update({ status: 'completed' });
  return data;
}
```

### Realtime Subscriptions

```typescript
// Subscribe to changes on a table (useful for triggering agent actions)
function subscribeToTable(table: string, callback: (payload: any) => void) {
  const channel = supabase
    .channel(`${table}-changes`)
    .on(
      'postgres_changes',
      {
        event: '*', // INSERT, UPDATE, DELETE
        schema: 'public',
        table: table
      },
      (payload) => {
        callback({
          event: payload.eventType,
          table: table,
          old: payload.old,
          new: payload.new,
          timestamp: new Date().toISOString()
        });
      }
    )
    .subscribe();

  return channel;
}

// Example: Trigger agent when new lead is inserted
subscribeToTable('enriched_leads', async (payload) => {
  if (payload.event === 'INSERT' && payload.new.pain_score >= 60) {
    // Trigger the CRM skill to create a GHL contact
    await context.skills.invoke('@yourname/ghl-crm', {
      action: 'create_contact',
      contact_data: {
        firstName: payload.new.contact_name?.split(' ')[0],
        lastName: payload.new.contact_name?.split(' ').slice(1).join(' '),
        email: payload.new.contact_email,
        phone: payload.new.phone,
        companyName: payload.new.business_name,
        website: payload.new.website,
        tags: ['auto-enriched', `score-${payload.new.pain_score}`]
      }
    });
  }
});
```

### pgvector Operations (RAG)

```typescript
// Store embedding
async function storeEmbedding(table: string, record: { content: string; embedding: number[]; metadata: any }) {
  const { data, error } = await supabase
    .from(table)
    .insert({
      content: record.content,
      embedding: record.embedding,
      metadata: record.metadata
    })
    .select();

  return data;
}

// Similarity search
async function similaritySearch(table: string, queryEmbedding: number[], limit: number = 5, threshold: number = 0.7) {
  const { data, error } = await supabase.rpc('match_documents', {
    query_embedding: queryEmbedding,
    match_threshold: threshold,
    match_count: limit,
    p_table: table
  });

  return data;
}

// Requires stored function:
// CREATE FUNCTION match_documents(
//   query_embedding vector(1536),
//   match_threshold float,
//   match_count int,
//   p_table text
// ) RETURNS TABLE(id uuid, content text, similarity float)
```

---

## Airtable Operations

### Your Airtable Setup

- **Bases**: Various project tracking and client management bases
- **Existing MCP**: Airtable MCP server already configured and working
- **Use cases**: Project management, content calendars, client tracking, lightweight CRM supplement

### Operations via Airtable MCP

The existing Airtable MCP already provides:

| Operation | MCP Tool | Notes |
|-----------|----------|-------|
| List bases | `list_bases` | Get all accessible bases |
| List tables | `list_tables` | Get tables in a base |
| List records | `list_records` | Paginated record listing with filters |
| Get record | `get_record` | Single record by ID |
| Create record | `create_record` | Insert a new record |
| Update record | `update_record` | Update fields on existing record |
| Delete record | `delete_record` | Remove a record |
| Search records | `search_records` | Search by field value |
| Create table | `create_table` | Create new table with fields |
| Create field | `create_field` | Add field to existing table |

### Wrapping Airtable MCP in the Skill

The database-ops skill wraps Airtable MCP calls to add:
- Consistent error handling across both databases
- Input validation before API calls
- Automatic retry on rate limit errors (Airtable: 5 requests/second)
- Logging of all operations for audit trail
- Type conversion between Airtable and Supabase types

---

## Skill Design: @yourname/database-ops

### skill.json Manifest (Key Sections)

```json
{
  "name": "@yourname/database-ops",
  "version": "1.0.0",
  "description": "Unified database operations across Supabase and Airtable",
  "commands": ["/db", "/query", "/database"],
  "inputs": {
    "required": {
      "database": {
        "type": "string",
        "enum": ["supabase", "airtable"],
        "description": "Which database to operate on"
      },
      "operation": {
        "type": "string",
        "enum": [
          "query", "insert", "update", "delete", "upsert",
          "schema", "migrate", "count",
          "subscribe", "unsubscribe",
          "embedding_store", "embedding_search",
          "sync", "backup"
        ]
      }
    },
    "optional": {
      "table": { "type": "string", "description": "Table name (Supabase) or table name (Airtable)" },
      "base_id": { "type": "string", "description": "Airtable base ID (only for Airtable operations)" },
      "data": { "type": "object", "description": "Data for insert/update/upsert" },
      "filters": {
        "type": "object",
        "description": "Query filters",
        "properties": {
          "eq": { "type": "object", "description": "Equality filters: { column: value }" },
          "gt": { "type": "object", "description": "Greater than: { column, value }" },
          "lt": { "type": "object", "description": "Less than: { column, value }" },
          "ilike": { "type": "object", "description": "Case-insensitive LIKE: { column, value }" },
          "in": { "type": "object", "description": "IN array: { column, values[] }" }
        }
      },
      "select": { "type": "string", "description": "Fields to select (default: *)" },
      "order_by": { "type": "string", "description": "Sort column" },
      "order_direction": { "type": "string", "enum": ["asc", "desc"], "default": "asc" },
      "limit": { "type": "integer", "default": 50, "maximum": 1000 },
      "offset": { "type": "integer", "default": 0 },
      "sql": { "type": "string", "description": "Raw SQL for migrations (Supabase only)" },
      "confirm_destructive": { "type": "boolean", "default": false },
      "embedding": { "type": "array", "description": "Vector embedding for similarity search" },
      "similarity_threshold": { "type": "number", "default": 0.7 }
    }
  },
  "outputs": {
    "data": { "type": "any", "description": "Query results or operation confirmation" },
    "count": { "type": "integer", "description": "Number of affected/returned records" },
    "status": { "type": "string", "enum": ["success", "error", "confirmation_required"] },
    "message": { "type": "string" }
  },
  "permissions": {
    "network": ["*.supabase.co", "api.airtable.com"],
    "environment": [
      "SUPABASE_URL",
      "SUPABASE_ANON_KEY",
      "SUPABASE_SERVICE_ROLE_KEY",
      "AIRTABLE_API_KEY"
    ]
  }
}
```

---

## Safety Model

### Read-Only by Default

The skill operates in **read-only mode** by default. Write operations require explicit opt-in:

```json
// Config: config/schema.json
{
  "WRITE_MODE": {
    "type": "string",
    "enum": ["read-only", "write-with-confirmation", "write-auto"],
    "default": "write-with-confirmation",
    "description": "Controls write operation behavior"
  }
}
```

| Mode | Behavior |
|------|----------|
| `read-only` | All write operations are blocked. Query/select only. |
| `write-with-confirmation` | Write operations show what would change and ask for confirmation. **Default.** |
| `write-auto` | Write operations execute immediately. For trusted automated pipelines only. |

### Operation-Specific Safety Rules

| Operation | Safety Level | Behavior |
|-----------|-------------|----------|
| `query` / `count` / `schema` | None | Always allowed |
| `insert` | Low | Allowed in write modes; logs the insertion |
| `update` | Medium | Shows affected row count before executing; requires filter (no blanket updates) |
| `delete` | High | Always shows affected records; requires `confirm_destructive: true` |
| `migrate` | Critical | Shows SQL preview; requires confirmation; creates backup first |
| `upsert` | Low-Medium | Logs which records were inserted vs updated |

### Backup Before Destructive Operations

```typescript
async function backupBeforeDelete(table: string, filters: any) {
  // Export affected records before deletion
  const { data: affectedRecords } = await supabase
    .from(table)
    .select('*')
    .match(filters);

  // Store backup
  await supabase.from('operation_backups').insert({
    operation: 'delete',
    table_name: table,
    records: affectedRecords,
    created_at: new Date().toISOString(),
    expires_at: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString() // 30 days
  });

  return affectedRecords.length;
}
```

---

## Cross-Database Sync

### Supabase <-> Airtable Sync

For cases where data needs to exist in both systems:

```typescript
async function syncToAirtable(
  supabaseTable: string,
  airtableBase: string,
  airtableTable: string,
  fieldMapping: Record<string, string>, // supabase_column -> airtable_field
  syncDirection: 'supabase_to_airtable' | 'airtable_to_supabase' | 'bidirectional'
) {
  // Get Supabase records
  const { data: supabaseRecords } = await supabase
    .from(supabaseTable)
    .select('*')
    .order('updated_at', { ascending: false });

  // Get Airtable records
  const airtableRecords = await airtable.listRecords(airtableBase, airtableTable);

  // Map and sync based on a shared key (e.g., email, business_name)
  for (const record of supabaseRecords) {
    const mappedFields: Record<string, any> = {};
    for (const [sbCol, atField] of Object.entries(fieldMapping)) {
      mappedFields[atField] = record[sbCol];
    }

    // Check if record exists in Airtable
    const existing = airtableRecords.find(r =>
      r.fields[fieldMapping.email] === record.email
    );

    if (existing) {
      await airtable.updateRecord(airtableBase, airtableTable, existing.id, mappedFields);
    } else {
      await airtable.createRecord(airtableBase, airtableTable, mappedFields);
    }
  }
}
```

### Common Sync Scenarios

| Scenario | From | To | Trigger |
|----------|------|-----|---------|
| New enriched lead | Supabase (enriched_leads) | Airtable (Lead Tracker) | After enrichment completes |
| Client status update | Airtable (Clients) | Supabase (clients) | Manual update in Airtable |
| Pipeline metrics | Supabase (pipeline views) | Airtable (Reports) | Daily scheduled sync |
| Content calendar | Airtable (Content Calendar) | Supabase (scheduled_content) | Content approval |

---

## Migration from Existing Claude Code Skills

### supabase-ops Migration

| Claude Code Feature | Database-Ops Equivalent | Migration Effort |
|---------------------|------------------------|-----------------|
| Basic CRUD queries | `query`, `insert`, `update`, `delete` operations | Low -- same logic, new format |
| Schema inspection | `schema` operation | Low -- wrap existing logic |
| pgvector operations | `embedding_store`, `embedding_search` operations | Low -- existing code |
| Custom SQL | `migrate` operation with safety checks | Medium -- add safety layer |

### Airtable Integration

The existing Airtable MCP is already functional. The database-ops skill wraps it:

```typescript
// Inside the skill, delegate to Airtable MCP for Airtable operations
if (context.inputs.database === 'airtable') {
  switch (context.inputs.operation) {
    case 'query':
      return await context.tools.airtable_list_records({
        base_id: context.inputs.base_id,
        table_name: context.inputs.table,
        max_records: context.inputs.limit
      });
    case 'insert':
      return await context.tools.airtable_create_record({
        base_id: context.inputs.base_id,
        table_name: context.inputs.table,
        fields: context.inputs.data
      });
    // ... etc
  }
}
```

---

## Common Query Patterns

### Frequently Used Queries

```
# Get all leads above a pain score threshold
/db query
  database: supabase
  table: enriched_leads
  filters: { gt: { column: "pain_score", value: 60 } }
  order_by: pain_score
  order_direction: desc
  limit: 50

# Search leads by city
/db query
  database: supabase
  table: enriched_leads
  filters: { eq: { city: "Austin" }, ilike: { category: "plumb" } }

# Get pipeline metrics
/db query
  database: supabase
  table: enriched_leads
  select: "pipeline_stage, count(*)"
  group_by: pipeline_stage

# Find duplicate leads by email
/db query
  database: supabase
  sql: "SELECT contact_email, COUNT(*) FROM enriched_leads GROUP BY contact_email HAVING COUNT(*) > 1"

# Get recent enrichment history
/db query
  database: supabase
  table: enriched_leads
  filters: { gt: { column: "last_enriched_at", value: "2026-01-01" } }
  order_by: last_enriched_at
  order_direction: desc
```

---

## Performance Considerations

### Supabase Query Optimization

- Always use indexed columns in WHERE clauses
- Use `select` to limit returned columns (don't `SELECT *` for large tables)
- Use pagination (`limit` + `offset`) for large result sets
- For complex aggregations, create database views or stored functions
- Use `count: 'exact'` only when needed (slower than `count: 'estimated'`)

### Airtable Limitations

- Maximum 100 records per API call (pagination required for more)
- Rate limit: 5 requests per second per base
- Maximum 50,000 records per table
- No JOINs (use linked records instead)
- Formula fields are computed, not stored (can be slow)

### Batch Operation Limits

| Database | Max Records per Batch | Rate Limit |
|----------|----------------------|------------|
| Supabase | 1,000 per insert | Varies by plan |
| Airtable | 10 per create/update | 5 requests/second |

---

## Error Handling

```typescript
// Comprehensive error handling for database operations
async function handleDatabaseError(error: any, operation: string, table: string) {
  // Classify error
  if (error.code === '23505') {
    return { status: 'error', message: `Duplicate key violation on '${table}': record already exists`, retryable: false };
  }
  if (error.code === '23503') {
    return { status: 'error', message: `Foreign key violation on '${table}': referenced record does not exist`, retryable: false };
  }
  if (error.code === '42P01') {
    return { status: 'error', message: `Table '${table}' does not exist`, retryable: false };
  }
  if (error.code === 'PGRST116') {
    return { status: 'error', message: `No rows returned for single-row query on '${table}'`, retryable: false };
  }
  if (error.status === 429) {
    return { status: 'error', message: 'Rate limited. Retrying in 2 seconds...', retryable: true, retryAfter: 2000 };
  }
  if (error.status === 500 || error.status === 503) {
    return { status: 'error', message: `Database service error (${error.status}). Retrying...`, retryable: true, retryAfter: 5000 };
  }

  // Unknown error
  return { status: 'error', message: `Unexpected error in ${operation} on '${table}': ${error.message}`, retryable: false };
}
```

---

*Last updated: 2026-02-05*
*Status: Skill design complete; foundational skill that other skills depend on*
