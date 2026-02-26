# Hardware Requirements: Mac Mini M4 for OpenClaw

## Overview

Running OpenClaw 24/7 alongside Ollama for local LLMs and Docker for containerized services
places meaningful demands on your hardware. The Mac Mini M4 line is an excellent choice for a
dedicated always-on AI agent server due to its low power draw (15-30W typical), fanless or
near-silent operation, and Apple Silicon's unified memory architecture which lets LLMs access
the full system RAM without a discrete GPU.

This document covers the recommended specs, why each matters, and which Mac Mini M4
configuration best fits your workload.

---

## Mac Mini M4 Configuration Comparison

| Spec               | M4 Base (10-core) | M4 Pro (12-core)     | M4 Pro (14-core)     | M4 Max (16-core)     |
|--------------------|--------------------|----------------------|----------------------|----------------------|
| **CPU Cores**      | 10 (4P + 6E)      | 12 (10P + 2E)       | 14 (10P + 4E)       | 16 (12P + 4E)       |
| **GPU Cores**      | 10                 | 16                   | 20                   | 40                   |
| **Neural Engine**  | 16-core            | 16-core              | 16-core              | 16-core              |
| **Max RAM**        | 32 GB              | 64 GB                | 64 GB                | 128 GB               |
| **Memory Bandwidth** | 120 GB/s         | 273 GB/s             | 273 GB/s             | 546 GB/s             |
| **Base Price**     | ~$599 (16GB/256GB) | ~$1,399 (24GB/512GB) | ~$1,599 (24GB/512GB) | ~$2,199 (36GB/512GB) |
| **Recommended Config** | $799 (16GB/512GB) | $1,999 (64GB/1TB) | $2,199 (64GB/1TB) | $3,199 (64GB/1TB)  |

> **Note:** Prices are approximate USD as of late 2025/early 2026. Apple pricing varies by
> region and changes over time. Check apple.com for current pricing.

---

## RAM (Unified Memory)

RAM is the single most important factor for running local LLMs. Apple Silicon's unified memory
architecture means both the CPU and GPU share the same memory pool, and Ollama can load models
directly into this shared space.

| RAM   | Suitability | What You Can Run                                                          |
|-------|-------------|---------------------------------------------------------------------------|
| 16 GB | Minimum     | OpenClaw + 1 small model (7B-8B parameters) simultaneously. Tight when running Docker + a browser. No room for 14B+ models while other services run. |
| 24 GB | Workable    | OpenClaw + Docker + one 14B model loaded. Some headroom but will feel constrained if you run multiple agent sessions concurrently. |
| 32 GB | Recommended | OpenClaw + Docker + Ollama with a 14B model comfortably loaded, with room for macOS overhead and background processes. Can briefly load a 30B model. |
| 64 GB | Ideal       | Run 70B-parameter models (llama3.3:70b requires ~40GB), keep multiple models warm in memory, run concurrent agent sessions, and still have headroom for Docker containers and macOS. |
| 128 GB | Overkill (but future-proof) | Multiple 70B models loaded simultaneously, or a single 100B+ model. Only necessary if you plan to run very large open-weight models locally. |

**Why RAM matters so much:**
- A 7B-parameter model at Q4 quantization uses approximately 4 GB of RAM
- A 14B-parameter model at Q4 quantization uses approximately 8 GB of RAM
- A 70B-parameter model at Q4 quantization uses approximately 40 GB of RAM
- macOS itself reserves 3-5 GB
- Docker Desktop reserves 2-4 GB depending on containers
- OpenClaw's Node.js process uses 200-500 MB, but agent memory and context windows can grow

**Recommendation:** 64 GB is the sweet spot. It lets you run the highest-quality local models
(70B class) while keeping OpenClaw, Docker, and macOS comfortable. If budget is tight, 32 GB
works well with 14B models, which are excellent for most agent tasks.

---

## Storage

| Storage | Suitability | Notes                                                                     |
|---------|-------------|---------------------------------------------------------------------------|
| 256 GB  | Too small   | macOS takes ~30 GB, Docker images grow quickly, and a single 70B model is ~40 GB. You will run out. |
| 512 GB  | Minimum     | Room for macOS + Docker + 3-5 models + OpenClaw data. Will require active management of downloaded models. |
| 1 TB    | Recommended | Comfortable room for 10+ models, Docker images, logs, agent memory databases, and growth over time. |
| 2 TB    | Generous    | Future-proof. Room for many models, large SQLite memory databases, extensive logging, and backups. |

**Model size reference:**
- 7B Q4: ~4 GB on disk
- 14B Q4: ~8 GB on disk
- 30B Q4: ~18 GB on disk
- 70B Q4: ~40 GB on disk
- Embedding models (nomic-embed-text): ~275 MB on disk

**Other storage consumers:**
- Docker images: OpenClaw image ~500 MB, supporting containers add up
- Agent memory (SQLite): grows over time, typically 10 MB - 1 GB depending on usage
- Logs: can grow to several GB if not rotated
- macOS + Xcode CLI tools: ~30-40 GB

---

## Network

For a 24/7 agent server, network reliability directly impacts uptime.

### Ethernet (Strongly Recommended)
- The Mac Mini M4 has a built-in Gigabit Ethernet port (10 Gbit on Pro/Max models)
- Use a wired connection for:
  - Consistent latency to LLM APIs (Anthropic, OpenAI)
  - Reliable WebSocket connections (OpenClaw Gateway on port 18789)
  - Stable SSH remote management sessions
  - No WiFi dropouts during long-running agent tasks

### WiFi (Fallback Only)
- WiFi 6E is built in, adequate for development/testing
- Not recommended as primary connection for 24/7 operation because:
  - WiFi reconnection events can drop WebSocket connections
  - Interference from other devices causes latency spikes
  - macOS may sleep the WiFi interface under certain power conditions

### Static IP / DHCP Reservation
- Configure a DHCP reservation on your router so the Mac Mini always gets the same local IP
- This makes SSH, port forwarding, and service access predictable
- Example: Reserve `192.168.1.100` for the Mac Mini's MAC address in your router admin panel

---

## UPS (Uninterruptible Power Supply)

For always-on operation, a UPS protects against:
- Power outages causing abrupt shutdowns (can corrupt SQLite databases)
- Power fluctuations and brownouts
- Gives you time to gracefully shut down or lets the Mac Mini ride through brief outages

**Recommended UPS specs:**
- 600 VA / 360 W minimum (Mac Mini M4 draws 15-30W typical, 65W max)
- A 600 VA UPS gives 30+ minutes of runtime for a Mac Mini alone
- Look for USB-connected models that support macOS power management (APC, CyberPower)
- macOS can detect UPS battery state and auto-shutdown at low battery via System Settings > Battery

**Budget option:** APC Back-UPS BE600M1 (~$70) provides ample runtime for a Mac Mini.

---

## Workload Profile: OpenClaw + Ollama + Docker

Here is what your Mac Mini will be running simultaneously:

| Process            | CPU Usage         | RAM Usage        | Notes                              |
|--------------------|-------------------|------------------|------------------------------------|
| macOS Sequoia      | 1-3% idle         | 3-5 GB           | Base OS overhead                   |
| Docker Desktop     | 1-5% idle         | 2-4 GB           | Hypervisor + container overhead    |
| OpenClaw Gateway   | 2-10% per session | 200-500 MB       | Node.js WebSocket server on :18789 |
| Ollama Service     | 0% idle, 100% during inference | Model-dependent (4-40 GB) | Loads model into memory on first request |
| Active LLM Inference | 80-100% all cores | Included in Ollama | Burst usage during token generation |

**Peak load scenario:** An agent session triggers an LLM call while another session is running.
Ollama will peg all CPU cores during inference. With 64 GB RAM and the M4 Pro, this is
comfortable. With 16 GB RAM, you may experience memory pressure if a 14B model is loaded.

---

## Recommended Configuration

**Best value for OpenClaw 24/7 operation:**

> **Mac Mini M4 Pro (12-core CPU / 16-core GPU)**
> - **64 GB Unified Memory**
> - **1 TB SSD**
> - **Approximate price: $1,999**

This configuration provides:
- Enough RAM to run 70B local models or keep multiple 14B models warm
- Fast enough CPU for responsive inference and concurrent agent sessions
- Memory bandwidth (273 GB/s) that significantly improves token generation speed over the base M4 (120 GB/s)
- 10 Gigabit Ethernet for future-proof networking
- Plenty of storage for models, data, and growth

**Budget alternative:**

> **Mac Mini M4 Base (10-core CPU / 10-core GPU)**
> - **32 GB Unified Memory**
> - **512 GB SSD**
> - **Approximate price: $999**

Capable of running OpenClaw with 14B local models comfortably. You sacrifice the ability to
run 70B models and the higher memory bandwidth of the Pro chip.

---

## Next Steps

- [macOS Preparation](macos-preparation.md) - Setting up the operating system
- [Ollama Local Models](ollama-local-models.md) - Installing and configuring local LLMs
- [Docker Installation](docker-installation.md) - Container-based OpenClaw deployment
