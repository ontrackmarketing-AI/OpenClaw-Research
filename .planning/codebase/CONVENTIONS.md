# Coding Conventions

**Analysis Date:** 2026-02-27

## Naming Patterns

**Files:**
- Kebab-case for executable scripts: `gsd-check-update.js`, `gsd-statusline.js`, `gsd-context-monitor.js`
- Documentation files use PascalCase with hyphens: `CLAUDE.md`, `GAP-ANALYSIS.md`, `MIGRATION-CHECKLIST.md`
- Directory names use numbers-and-hyphens pattern for organization: `00-Foundation/`, `04-Memory-and-RAG/`, `11-Implementation-Roadmap/`

**Functions:**
- camelCase for function names: `readFileSync()`, `writeFileSync()`, `parseJSON()`, `shouldWrapUp()`
- Descriptive names that indicate action: `parseInput()`, `buildWarningMessage()`, `checkMetricsStale()`
- Internal helper functions prefixed with underscore not used; utilities named directly: `buildProgressBar()`, `getTaskFromTodos()`

**Variables:**
- camelCase for local and module variables: `cacheDir`, `cacheFile`, `homeDir`, `sessionId`, `remaining`
- Constant-like variables in camelCase (not UPPER_SNAKE_CASE) with semantic prefix: `filePath`, `tmpDir`, `sessionId`
- UPPER_CASE for true configuration constants: `WARNING_THRESHOLD`, `CRITICAL_THRESHOLD`, `STALE_SECONDS`, `DEBOUNCE_CALLS`
- Abbreviated context: `ctx`, `rem`, `used` in performance-sensitive code (statusline rendering)

**Types:**
- No TypeScript in codebase; Node.js scripts use runtime type checking
- JSON schema pattern for complex data structures: objects with explicit properties (`{ session_id, remaining_percentage, used_pct, timestamp }`)

## Code Style

**Formatting:**
- 2-space indentation (observed consistently in all scripts)
- Lines typically 80-100 characters (flexible for readability)
- No semicolon enforcement visible; consistent without semicolons in some files, with in others
- Double quotes for strings: `"utf8"`, `"json"`, `"/tmp/claude-ctx-"`

**Linting:**
- No .eslintrc, .prettierrc, or linting configuration files in project root
- Code follows Node.js style guide conventions by convention, not enforcement
- Self-contained validation: scripts check file existence and handle errors gracefully rather than relying on lint-time validation

## Import Organization

**Order:**
1. Built-in Node.js modules: `const fs = require('fs');`, `const path = require('path');`, `const os = require('os');`
2. External packages: none in current codebase
3. Local modules: none in current codebase

**Path Aliases:**
- Not used; direct require paths to modules
- Relative path pattern: not applicable; all imports are from Node.js stdlib

## Error Handling

**Patterns:**
- Try-catch blocks for file I/O and JSON parsing: wraps potentially failing operations
- Silent failure with empty catch blocks: `try { ... } catch (e) {}` when operation is optional (file reading, JSON parsing)
- Conditional existence checks before operations: `if (fs.existsSync(path)) { ... }` before reading
- Exit codes on error: `process.exit(0);` for graceful failure in hooks, exit normally even on problems
- No exceptions thrown from utility code; instead, functions return null/undefined on error or operate defensively

**Example error pattern** (from `gsd-statusline.js`):
```javascript
try {
  const todos = JSON.parse(fs.readFileSync(path, 'utf8'));
  const inProgress = todos.find(t => t.status === 'in_progress');
  if (inProgress) task = inProgress.activeForm || '';
} catch (e) {
  // Silently fail on file system errors - don't break statusline
}
```

**Example defensive pattern** (from `gsd-context-monitor.js`):
```javascript
if (fs.existsSync(metricsPath)) {
  const metrics = JSON.parse(fs.readFileSync(metricsPath, 'utf8'));
  if (metrics.timestamp && (now - metrics.timestamp) > STALE_SECONDS) {
    process.exit(0);
  }
}
```

## Logging

**Framework:** console implicitly (via stdout/stderr writes), no logging library

**Patterns:**
- Structured JSON output for tool use: `process.stdout.write(JSON.stringify(output));`
- Colored terminal output using ANSI escape codes: `\x1b[32m`, `\x1b[33m`, `\x1b[38;5;208m`, `\x1b[5;31m`
- No explicit logging calls; output only when needed (side-effects driven)
- Status messages written to files as cache for inter-process communication: `fs.writeFileSync(cacheFile, JSON.stringify(result));`

**Example colored output** (from `gsd-statusline.js`):
```javascript
if (used < 63) {
  ctx = ` \x1b[32m${bar} ${used}%\x1b[0m`;  // green
} else if (used < 81) {
  ctx = ` \x1b[33m${bar} ${used}%\x1b[0m`;  // yellow
} else if (used < 95) {
  ctx = ` \x1b[38;5;208m${bar} ${used}%\x1b[0m`;  // orange
} else {
  ctx = ` \x1b[5;31m💀 ${bar} ${used}%\x1b[0m`;  // red blinking skull
}
```

## Comments

**When to Comment:**
- Explain WHY, not WHAT: comments focus on intent and reasoning
- Comment complex logic or non-obvious behavior: thresholds, debouncing logic, process detachment requirements
- Document magic numbers with context: `// Scale: 80% real usage = 100% displayed`
- No comments for self-documenting code: variable and function names should be clear

**Examples:**
```javascript
// VERSION file locations (check project first, then global)
const projectVersionFile = path.join(cwd, '.claude', 'get-shit-done', 'VERSION');

// Context window display (shows USED percentage scaled to 80% limit)
// Claude Code enforces an 80% context limit, so we scale to show 100% at that point

// Required on Windows for proper process detachment
detached: true
```

## Function Design

**Size:** Functions 20-100 lines; no strict limit but logic is kept focused

**Parameters:**
- Minimal parameters preferred; data passed as objects when multiple values needed
- Uses environment (process.cwd(), os.homedir()) rather than parameter passing for global state
- No explicit parameter validation; assumes correct types (Node.js duck typing)

**Return Values:**
- Functions return computed values (strings, objects) or void
- No consistent use of Promise/async-await in current scripts (all synchronous)
- Early returns for guard conditions: `if (!fs.existsSync(path)) { process.exit(0); }`

## Module Design

**Exports:**
- Executable scripts don't export; they perform side effects and exit
- No module.exports pattern; scripts are CLI tools, not libraries
- Single responsibility: each script does one thing (check updates, render statusline, monitor context)

**File Organization:**
- Script runs top-to-bottom; no class or function declarations followed by invocation
- Initialization at module load time: file paths, constants defined at top
- Stdin handling at bottom using event listeners: `process.stdin.on('data', ...)`, `process.stdin.on('end', ...)`

**Barrel Files:**
- Not applicable; no index files for exports

---

*Convention analysis: 2026-02-27*
