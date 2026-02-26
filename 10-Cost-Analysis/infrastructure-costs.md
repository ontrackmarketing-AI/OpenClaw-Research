# Infrastructure Costs: Mac Mini M4 for OpenClaw

## Overview

Running OpenClaw locally requires a dedicated machine for 24/7 operation. The Mac Mini M4 lineup offers the best performance-per-dollar for local LLM inference thanks to Apple Silicon's unified memory architecture, which allows the GPU to access all system RAM -- critical for running large language models through Ollama.

This document breaks down every hardware and infrastructure cost, recommends a specific configuration, and compares local hosting against cloud alternatives.

---

## Mac Mini M4 Configuration Options

### M4 Base (16GB / 256GB) -- $599
- **Verdict: NOT RECOMMENDED**
- 16GB unified memory is the absolute floor. You can run 7B-parameter models (e.g., Mistral 7B, Llama 3.1 8B) but with no headroom for Docker containers, Supabase local, or background services.
- 256GB storage fills up immediately with model files (a single 70B model is ~40GB quantized).
- You will hit swap constantly, degrading inference speed and SSD lifespan.
- Only consider this if you plan to use Ollama for tiny models and offload everything else to cloud APIs.

### M4 (16GB / 512GB) -- $699
- **Verdict: Minimum Viable for Basic OpenClaw**
- Same 16GB RAM limitation, but 512GB storage gives you room for 5-8 quantized models plus Docker volumes.
- Can comfortably run: Mistral 7B, Llama 3.1 8B, Phi-3, Gemma 2 9B.
- Cannot run: anything above ~13B parameters without severe quantization.
- OpenClaw orchestration (n8n, Supabase, Redis) will compete with Ollama for RAM.
- Realistic workflow: use local models only for simple classification/extraction, send everything else to Claude API.

### M4 (24GB / 512GB) -- $799
- **Verdict: Better -- Can Run 14B Models**
- 24GB opens up the 14B parameter class: Llama 3.1 14B, Qwen 2.5 14B, DeepSeek-R1 14B distill.
- These models are significantly more capable than 7B for tasks like lead qualification, content drafting, and data extraction.
- Still tight if running full OpenClaw stack (n8n + Supabase + Redis + Ollama simultaneously).
- Good entry point if budget is a primary concern and you accept some limitations.

### M4 Pro (24GB / 512GB) -- $1,399
- **Verdict: Recommended for Serious Use (Budget Option)**
- The M4 Pro chip has more GPU cores (16 vs 10) and higher memory bandwidth (~273 GB/s vs ~120 GB/s).
- Memory bandwidth is the bottleneck for LLM inference. The Pro nearly doubles token generation speed compared to base M4 at the same RAM.
- 24GB is workable but limits you to 14B models maximum while running the full stack.
- 512GB storage is adequate for most setups.

### M4 Pro (48GB / 512GB) -- $1,599
- **Verdict: Good Balance for Local LLMs**
- 48GB unified memory is the sweet spot. You can run 34B-parameter models (e.g., CodeLlama 34B, Yi 34B) comfortably.
- Enough headroom for the full OpenClaw stack (n8n, Supabase, Redis, Ollama) running simultaneously with ~15-20GB left for model loading.
- 512GB storage may feel tight if you download many models. Consider external SSD for model storage.

### M4 Pro (48GB / 1TB) -- $1,799
- **Verdict: RECOMMENDED -- Best Balance for OpenClaw + Ollama + Docker**
- Same 48GB RAM as above, but 1TB internal storage eliminates the need for external drives.
- Can store 10-15 quantized models locally, full Docker volumes, log files, and database storage.
- Can run 70B models with Q4 quantization (requires ~38-42GB for the model, leaving limited RAM for other services -- best to stop other containers first).
- For day-to-day operation: run a 14B-34B model continuously while the full OpenClaw stack runs.
- This is the configuration this knowledge base recommends.

### M4 Max (64GB / 1TB) -- $2,199+
- **Verdict: Overkill but Future-Proof**
- 64GB allows running 70B models (Llama 3.1 70B, Qwen 2.5 72B) while keeping the full stack running.
- Higher memory bandwidth (~546 GB/s) means noticeably faster token generation.
- Only justified if you plan to serve models to multiple users simultaneously or run inference-heavy batch jobs.
- The $400+ premium over the 48GB Pro is hard to justify for a single-user OpenClaw setup.

---

## Recommended Configuration: M4 Pro 48GB / 1TB -- $1,799

**Why this specific model:**
1. **48GB RAM** handles 99% of use cases without compromise. You run the full orchestration stack and a capable local model simultaneously.
2. **1TB storage** means no external drive hassles. Models, Docker volumes, databases, and logs all fit comfortably.
3. **M4 Pro memory bandwidth** (~273 GB/s) delivers roughly 25-40 tokens/second for 14B models -- fast enough for real-time workflows.
4. **Price-to-capability ratio** is the best in the lineup for this use case. The jump from $799 (24GB base) to $1,799 (48GB Pro) buys you 2x RAM, 2x bandwidth, and 2x storage.

---

## Peripherals and Accessories

| Item | Cost | Notes |
|------|------|-------|
| Monitor | $0-150 | Optional. Mac Mini can run headless via SSH/VNC. A cheap 1080p monitor is useful for initial setup and troubleshooting. |
| Keyboard + Mouse | $0-30 | Only needed for initial macOS setup. Use any USB keyboard/mouse you already have. |
| Ethernet cable (Cat 6) | $5-10 | Strongly recommended over Wi-Fi for 24/7 server use. More reliable, lower latency. |
| Network switch | $15-30 | Only if your router is out of Ethernet ports. A basic 5-port gigabit switch works. |
| UPS battery backup | $50-100 | Highly recommended. Protects against power surges and allows graceful shutdown during outages. APC BE600M1 ($50) or CyberPower CP1500AVRLCD ($100) are solid choices. |
| USB-C hub / dock | $0-40 | Only if you need extra ports. Mac Mini M4 Pro has 3x Thunderbolt 4, 1x USB-C, 1x USB-A, HDMI, Ethernet built in -- usually sufficient. |

**Peripherals subtotal: $70-200 (one-time)**

Most users already have a spare keyboard, mouse, and monitor. Minimum additional purchase is an Ethernet cable ($5) and a UPS ($50).

---

## Ongoing Infrastructure Costs

### Electricity
- Mac Mini M4 Pro idle power: ~7-10W
- Under moderate load (Ollama inference + Docker): ~25-40W
- Peak load (heavy inference): ~45-60W
- Average 24/7 consumption: ~15-25W (assuming intermittent inference, not constant)
- Monthly electricity at $0.15/kWh (US average):
  - Low estimate: 15W x 24h x 30d = 10.8 kWh = **$1.62/mo**
  - High estimate: 25W x 24h x 30d = 18 kWh = **$2.70/mo**
  - Peak estimate: 40W x 24h x 30d = 28.8 kWh = **$4.32/mo**
- **Realistic monthly electricity: $3-5/mo**
- Compare to a cloud GPU instance: you would pay $50-200/mo for equivalent always-on compute.

### Internet
- You likely already pay for internet, so this is $0 incremental.
- OpenClaw does not require exceptional bandwidth. A 50 Mbps connection is more than sufficient.
- If you need a static IP for webhook callbacks, check if your ISP offers one (usually $5-10/mo) or use Tailscale/Cloudflare Tunnel instead (free).

### Software
- macOS: included with Mac Mini ($0)
- Docker Desktop: free for personal use ($0)
- Ollama: open source ($0)
- Tailscale: free for personal use up to 100 devices ($0)
- n8n: self-hosted community edition ($0)

---

## Total Infrastructure Cost Summary

### One-Time Costs
| Item | Cost |
|------|------|
| Mac Mini M4 Pro 48GB/1TB | $1,799 |
| UPS battery backup | $50-100 |
| Ethernet cable + misc | $10-20 |
| Monitor (if needed) | $0-150 |
| **Total one-time** | **$1,859-2,069** |

Use **$1,900** as the planning number (assumes you have a spare monitor or run headless).

### Monthly Ongoing Costs
| Item | Cost |
|------|------|
| Electricity | $3-5/mo |
| Internet (incremental) | $0/mo |
| Software licenses | $0/mo |
| **Total monthly** | **$3-5/mo** |

### Amortized Monthly Cost (Hardware Over 3 Years)
- $1,900 / 36 months = **$52.78/mo**
- Plus electricity: $3-5/mo
- **Total amortized infrastructure: $55-58/mo**
- Round to **$55/mo** for planning purposes.

---

## Comparison: Local Mac Mini vs Cloud VPS

| Factor | Mac Mini M4 Pro 48GB | Cloud VPS (equivalent) |
|--------|---------------------|----------------------|
| Monthly cost | ~$55/mo (amortized) | $80-200/mo |
| RAM | 48GB unified | 48GB (shared or dedicated) |
| GPU for LLM | Apple Silicon (fast) | CPU-only or add GPU ($$$) |
| Storage | 1TB NVMe | 100-500GB SSD |
| Bandwidth | Your home internet | 1-10TB included |
| Uptime | Depends on your power/internet | 99.9%+ SLA |
| Privacy | Data stays local | Data on provider's servers |
| Scaling | Buy another Mac Mini | Click a button |
| Setup complexity | Moderate | Lower |

**Break-even analysis:**
- Cloud VPS at $100/mo = $3,600 over 3 years
- Mac Mini at $55/mo amortized = $1,980 over 3 years
- **Savings with Mac Mini: ~$1,620 over 3 years**
- Mac Mini pays for itself vs cloud hosting in **~12-19 months** (depending on equivalent cloud pricing).

**When cloud is better:**
- You need 99.99% uptime (medical, financial applications)
- You need to scale quickly to handle traffic spikes
- You travel frequently and cannot maintain a home server
- Your home internet is unreliable

**When Mac Mini is better:**
- You want data privacy and local control
- You run LLMs heavily (GPU access is expensive in the cloud)
- You have reliable home internet and power
- You are cost-sensitive over a multi-year horizon
- You are a solo operator or small team (no need for multi-region deployment)

---

## Action Items

1. **Order the Mac Mini M4 Pro 48GB/1TB ($1,799)** from Apple or authorized reseller.
2. **Purchase a UPS** -- APC BE600M1 ($50) minimum for basic surge protection and 5-10 min battery.
3. **Get a Cat 6 Ethernet cable** to connect directly to your router.
4. **Budget $55/mo** for amortized infrastructure in your operating cost spreadsheet.
5. **Plan for headless operation** -- install Tailscale and set up SSH during initial setup so you can manage the Mac Mini remotely from your primary machine.
