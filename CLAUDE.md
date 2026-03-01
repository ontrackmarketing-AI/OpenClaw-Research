# OpenClaw-Research

## What This Is
Blueprint repo for building the OpenClaw AI agent platform for OnTrack Marketing (digital marketing for local service businesses). 175+ markdown docs across 13 sections covering architecture, security, memory, skills, integrations, capabilities, and a 13-phase implementation roadmap.

## GSD Framework (Get Shit Done)
This repo uses the [GSD spec-driven development system](https://github.com/gsd-build/get-shit-done) for execution.

### Key Commands
- `/gsd:progress` -- See current status and next steps (start here)
- `/gsd:resume-work` -- Restore full context from last session
- `/gsd:new-project` -- Initialize project (run once to set up .planning/)
- `/gsd:plan-phase N` -- Research + plan a phase
- `/gsd:execute-phase N` -- Execute a planned phase
- `/gsd:verify-work N` -- Post-execution verification
- `/gsd:quick` -- Ad-hoc task with GSD guarantees
- `/gsd:help` -- Full command reference

### Project Reference Data
The master index of everything trackable in this repo lives at `~/.openclaw/gsd/index.md`:
- 13 roadmap phases (11-Implementation-Roadmap/)
- 15 gap analysis items (GAP-ANALYSIS.md)
- 9 priority skills (05-Skills-Development/priority-skills/)
- 53 capability files across 14 categories (08-Capabilities-Deep-Dive/)
- 35 integration files across 11 areas (06-Integrations/)
- 213 migration checklist items across 8 phases (MIGRATION-CHECKLIST.md)
- 58 supporting doc files across 9 directories

Use this index when feeding context to GSD phases and planning.

## Machine Context
- This Mac is the **agent machine** -- it IS the agent
- Human works on a **Windows PC** (the work machine)
- OpenClaw accesses remote work via MCP servers, git repos, cloud APIs

## Key Paths
- Research docs: `~/OpenClaw-Research/`
- GSD project state: `.planning/` (created by /gsd:new-project)
- GSD master index: `~/.openclaw/gsd/index.md`
- Agent memory: `~/.openclaw/memory/MEMORY.md`
- Agent config: `~/.openclaw/config/`
- Dashboard: `~/.openclaw/dashboard/` (Next.js, port 3000)
