# Testing Patterns

**Analysis Date:** 2026-02-27

## Test Framework

**Runner:**
- Not detected - No test framework configured (Jest, Vitest, Mocha not found)
- Configuration: None present

**Assertion Library:**
- Not applicable - No automated testing infrastructure

**Run Commands:**
```bash
# No test runner configured
# Scripts are tested manually via Claude Code hooks
```

## Test File Organization

**Location:**
- Not applicable - No .test.js, .spec.js files in codebase

**Naming:**
- Not applicable

**Structure:**
- Not applicable

## Testing Approach

**Current Pattern: Runtime Validation**

Instead of automated tests, the codebase uses defensive programming and runtime validation:

1. **File Existence Checks**: Every file I/O operation is guarded
```javascript
if (!fs.existsSync(cacheDir)) {
  fs.mkdirSync(cacheDir, { recursive: true });
}
```

2. **Optional Path Handling**: Gracefully handles missing files
```javascript
let installed = '0.0.0';
try {
  if (fs.existsSync(projectVersionFile)) {
    installed = fs.readFileSync(projectVersionFile, 'utf8').trim();
  } else if (fs.existsSync(globalVersionFile)) {
    installed = fs.readFileSync(globalVersionFile, 'utf8').trim();
  }
} catch (e) {}
```

3. **Stale Data Detection**: Validates timestamp freshness before use
```javascript
if (metrics.timestamp && (now - metrics.timestamp) > STALE_SECONDS) {
  process.exit(0);
}
```

4. **Null/Undefined Guards**: Checks for optional values before accessing
```javascript
if (remaining != null) {
  const rem = Math.round(remaining);
  // proceed
}
```

## Integration Testing

**Framework:** None

**Manual Testing Pattern:**
Scripts are invoked by Claude Code hooks at specific lifecycle events:
- `SessionStart`: runs `gsd-check-update.js` to cache npm package version
- `PostToolUse`: runs `gsd-context-monitor.js` to inject context warnings

Testing happens through:
1. **Hook Integration**: Scripts are registered in `.claude/settings.json` and invoked by Claude Code runtime
2. **Behavioral Observation**: User sees statusline updates, warnings appear in context when thresholds crossed
3. **File State Verification**: Output files written to `/tmp/` and `~/.claude/cache/` can be inspected

## Mocking

**Framework:** None

**Approach:**
- No mocking library used
- Environment-dependent: scripts interact with real filesystem and environment
- Process spawning with `stdio: 'ignore'`: subprocess isolation for background tasks
```javascript
const child = spawn(process.execPath, ['-e', `...`], {
  stdio: 'ignore',
  windowsHide: true,
  detached: true
});
child.unref();
```

## Fixtures and Test Data

**Test Data:**
- Not applicable - No test fixtures needed

**JSON Fixtures Created at Runtime:**
Scripts create their own test/cache files:
- `~/.claude/cache/gsd-update-check.json`: version comparison cache
- `/tmp/claude-ctx-{sessionId}.json`: context metrics bridge
- `/tmp/claude-ctx-{sessionId}-warned.json`: debounce state

## Coverage

**Requirements:** No coverage metrics enforced

**View Coverage:**
- Not applicable

## Test Types

**Unit Tests:**
- Not applicable - No unit test framework

**Integration Tests:**
- Implicit through hook execution in Claude Code environment
- Scripts run as actual hooks; behavior is validated by user observation
- Success = statusline renders, warnings appear at correct thresholds

**E2E Tests:**
- Not applicable - Scripts are end-to-end tools themselves

## Validation Patterns

**Input Validation:**

Stdin JSON parsing in hook scripts:
```javascript
let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
  try {
    const data = JSON.parse(input);
    // Proceed with parsed data
  } catch (e) {
    // Silent fail on malformed JSON
    process.exit(0);
  }
});
```

**Output Validation:**

JSON structure validation before writing:
```javascript
const result = {
  update_available: latest && installed !== latest,
  installed,
  latest: latest || 'unknown',
  checked: Math.floor(Date.now() / 1000)
};
fs.writeFileSync(cacheFile, JSON.stringify(result));
```

## Error Testing

**Pattern:**
No explicit error test cases. Error handling is defensive:

1. **Try-Catch for Optional Operations**: Wraps non-critical I/O
```javascript
try {
  const cache = JSON.parse(fs.readFileSync(cacheFile, 'utf8'));
  if (cache.update_available) {
    gsdUpdate = '\x1b[33m⬆ /gsd:update\x1b[0m │ ';
  }
} catch (e) {
  // If cache is corrupted or missing, silently continue
}
```

2. **Guard Clauses for Invalid State**: Exit gracefully on bad conditions
```javascript
if (!sessionId) {
  process.exit(0);
}
if (!fs.existsSync(metricsPath)) {
  process.exit(0);
}
```

3. **Timeout Handling**: npm commands have timeouts to prevent hangs
```javascript
latest = execSync('npm view get-shit-done-cc version', {
  encoding: 'utf8',
  timeout: 10000,
  windowsHide: true
}).trim();
```

## Edge Cases Handled

**Async Operations:**
- All file operations are synchronous (fs.readFileSync, fs.writeFileSync)
- Process spawning is non-blocking (child.unref())
- No Promise chains or async/await

**Process Detachment (Windows):**
```javascript
const child = spawn(process.execPath, ['-e', `...`], {
  stdio: 'ignore',
  windowsHide: true,
  detached: true  // Required on Windows for proper process detachment
});
child.unref();
```

**Stale Metrics:**
Context monitor discards metrics older than 60 seconds:
```javascript
const STALE_SECONDS = 60;
if (metrics.timestamp && (now - metrics.timestamp) > STALE_SECONDS) {
  process.exit(0);
}
```

**Debounce Logic:**
Prevents warning spam by tracking tool calls and severity escalation:
```javascript
const DEBOUNCE_CALLS = 5;
warnData.callsSinceWarn = (warnData.callsSinceWarn || 0) + 1;

const severityEscalated = currentLevel === 'critical' && warnData.lastLevel === 'warning';
if (!firstWarn && warnData.callsSinceWarn < DEBOUNCE_CALLS && !severityEscalated) {
  fs.writeFileSync(warnPath, JSON.stringify(warnData));
  process.exit(0);
}
```

## Testing Recommendations

**For New Code:**
1. Follow defensive patterns already established: always check fs.existsSync() before reading
2. Wrap optional operations in try-catch, silently fail
3. Guard clauses for invalid state: exit early if preconditions unmet
4. Validate JSON before parsing; handle parse errors gracefully
5. Add timeout to any subprocess operations (execSync with timeout option)

**For Debugging:**
1. Check output files in `/tmp/` and `~/.claude/cache/` for state inspection
2. Add temporary console.log() calls if needed (they may appear in Claude Code logs)
3. Manually invoke scripts with echo piping test JSON: `echo '{"test": "data"}' | node script.js`

---

*Testing analysis: 2026-02-27*
