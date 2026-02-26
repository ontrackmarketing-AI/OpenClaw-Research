# Vercel Deployment Pipeline

## Overview

Vercel is the deployment platform for all OpenClaw-generated client websites. You already have Vercel experience with multiple deployments, and the platform's seamless GitHub integration makes it the ideal choice for automated site deployment. This document covers the complete deployment pipeline from generated code to live website, including automation, configuration, domain management, monitoring, and cost management.

---

## Your Existing Vercel Skills

Based on your current MCP tools and experience:
- **vercel deploy:** Deploy projects to Vercel (both preview and production)
- **vercel logs:** View deployment and function logs
- **vercel project setup:** Configure new projects with environment variables
- **GitHub integration:** Auto-deploy from repository pushes

These skills form the foundation of the automated deployment pipeline. OpenClaw extends them with orchestration logic to handle the full lifecycle.

---

## Deployment Flow

### Step 1: Site Code Generation

OpenClaw generates the complete site codebase (Astro or Next.js):

```
Output structure:
client-site-{slug}/
  src/                    # Source files
  public/                 # Static assets
  package.json            # Dependencies
  astro.config.mjs        # Astro config (or next.config.js)
  tailwind.config.mjs     # Tailwind config
  vercel.json             # Vercel-specific configuration
  .env.example            # Required environment variables
```

**Site generation creates a complete, deployable project.** All dependencies are specified, all configuration is in place, and the site builds without errors locally before any deployment attempt.

---

### Step 2: GitHub Repository Setup

**Option A: Auto-create new repository**
```bash
# Create new repo via GitHub CLI
gh repo create client-sites/{slug} --private --clone

# Copy generated files into repo
cp -r generated-site/* client-sites/{slug}/

# Initial commit
cd client-sites/{slug}
git add .
git commit -m "Initial site generation for {business_name}"
git push origin main
```

**Option B: Use existing repository (monorepo)**
```bash
# Add client site as subdirectory in monorepo
cp -r generated-site/* monorepo/sites/{slug}/
cd monorepo
git add sites/{slug}/
git commit -m "Add site for {business_name}"
git push origin main
```

**Repository naming convention:**
- Individual repos: `client-sites/{business-slug}` (e.g., `client-sites/smith-plumbing-austin`)
- Monorepo: `client-sites/sites/{business-slug}`

**Repository settings:**
- Visibility: Private (client sites should not be publicly browsable on GitHub)
- Branch protection: main branch requires PR (optional for automated flow)
- Default branch: `main`

---

### Step 3: Vercel Auto-Deploy

**Option A: GitHub integration (recommended)**

With Vercel's GitHub integration connected:
1. Push to `main` branch triggers production deployment
2. Push to any other branch triggers preview deployment
3. No manual intervention needed

**Setup (one-time per repo):**
```bash
# Import project to Vercel via CLI
vercel link --project={slug}

# Or via Vercel dashboard:
# 1. Import Git Repository
# 2. Select the GitHub repo
# 3. Configure build settings
# 4. Deploy
```

**Option B: CLI deployment**
```bash
# Preview deployment
vercel deploy

# Production deployment
vercel deploy --prod
```

**Option C: API deployment (for full automation)**
```javascript
// Trigger deployment via Vercel API
const response = await fetch('https://api.vercel.com/v13/deployments', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${VERCEL_TOKEN}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: slug,
    gitSource: {
      type: 'github',
      repo: `client-sites/${slug}`,
      ref: 'main'
    }
  })
});
```

---

### Step 4: Deployment Verification

After deployment completes, run automated checks:

**Health check:**
```javascript
// Verify the deployed site is accessible
const deploymentUrl = deployment.url; // e.g., https://smith-plumbing-abc123.vercel.app
const response = await fetch(deploymentUrl);

if (response.status !== 200) {
  alert('Deployment failed health check');
  // Trigger rollback
}
```

**Lighthouse audit:**
```bash
# Run Lighthouse on deployed URL
npx lighthouse https://smith-plumbing.vercel.app \
  --output=json \
  --output-path=./lighthouse-results.json \
  --chrome-flags="--headless"

# Parse results
# Performance >= 90
# SEO >= 95
# Accessibility >= 90
# Best Practices >= 90
```

**Automated verification checklist:**
- [ ] Site returns HTTP 200 on homepage
- [ ] All linked pages return 200 (no 404s)
- [ ] SSL certificate valid (Vercel handles this automatically)
- [ ] Meta titles and descriptions present on all pages
- [ ] Structured data valid (via Google Rich Results Test API)
- [ ] Contact form submission works (send test submission)
- [ ] Images load correctly
- [ ] Mobile responsive (test at 375px width)
- [ ] Lighthouse scores meet thresholds

---

### Step 5: Custom Domain Configuration

**If client provides a domain:**

```bash
# Add custom domain to Vercel project
vercel domains add smithplumbing.com

# Configure DNS at registrar:
# A record: @ -> 76.76.21.21
# CNAME record: www -> cname.vercel-dns.com
```

**If using a subdomain of your agency domain:**
```bash
# Add subdomain
vercel domains add smith-plumbing.youragency.com

# Configure DNS:
# CNAME record: smith-plumbing -> cname.vercel-dns.com
```

**SSL is automatic.** Vercel provisions Let's Encrypt SSL certificates for all custom domains. No manual configuration needed. Certificate renewal is also automatic.

**Domain verification:**
```bash
# Check domain is properly configured
vercel domains inspect smithplumbing.com
```

---

### Step 6: Ongoing Monitoring

**Uptime monitoring:**
- Use Vercel's built-in analytics or external service (UptimeRobot, free tier)
- Check every 5 minutes
- Alert on downtime (email or Slack notification)

**Performance monitoring:**
- Vercel Analytics (available on Pro plan): real user performance data
- Monthly Lighthouse audits via automation
- Alert if Core Web Vitals degrade

**Error monitoring:**
- Vercel deployment logs for build errors
- Runtime errors for any serverless functions (contact forms, API routes)
- 404 monitoring: track pages that return 404 (broken links or missing pages)

---

## Vercel Configuration

### vercel.json

Standard configuration for client sites:

```json
{
  "framework": "astro",
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        },
        {
          "key": "Referrer-Policy",
          "value": "strict-origin-when-cross-origin"
        }
      ]
    },
    {
      "source": "/images/(.*)",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=31536000, immutable"
        }
      ]
    },
    {
      "source": "/(.*).css",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=31536000, immutable"
        }
      ]
    }
  ],
  "redirects": [
    {
      "source": "/home",
      "destination": "/",
      "permanent": true
    }
  ],
  "rewrites": []
}
```

### Environment Variables

Set via Vercel CLI or dashboard:

```bash
# Set environment variables for project
vercel env add GOOGLE_MAPS_API_KEY production
vercel env add CONTACT_FORM_ENDPOINT production
vercel env add ANALYTICS_ID production
```

**Common environment variables for client sites:**
| Variable | Purpose | Example |
|----------|---------|---------|
| `GOOGLE_MAPS_API_KEY` | Maps embed on contact page | `AIza...` |
| `CONTACT_FORM_ENDPOINT` | Where contact form submissions go | `https://api.youragency.com/submit` |
| `ANALYTICS_ID` | Google Analytics 4 measurement ID | `G-ABC123DEF` |
| `SITE_URL` | Canonical URL for the site | `https://smithplumbing.com` |

---

## Preview Deployments

Every push to a non-main branch creates a preview deployment:

**Use case: client review**
1. Generate site and push to `draft` branch
2. Vercel creates preview: `smith-plumbing-draft-abc123.vercel.app`
3. Share preview URL with client for review
4. Client requests changes
5. Make changes, push again (new preview auto-generated)
6. Client approves
7. Merge `draft` to `main` (triggers production deployment)

**Use case: content updates**
1. Client requests a change (new service, updated hours, etc.)
2. Create branch `update-hours`
3. Make changes, push
4. Preview deployed for verification
5. Merge to main for production

**Preview deployment features:**
- Unique URL for each preview (shareable with client)
- Comments on preview deployments (Vercel dashboard)
- Automatic cleanup: old preview deployments expire after 30 days
- Password protection available (Vercel Pro feature)

---

## Rollback

If a deployment causes issues:

```bash
# List recent deployments
vercel ls

# Rollback to a specific deployment
vercel rollback [deployment-url]

# Or via dashboard:
# 1. Go to project deployments
# 2. Find the working deployment
# 3. Click "Promote to Production"
```

**Automatic rollback triggers (implement via monitoring):**
- Homepage returns non-200 status
- Lighthouse performance drops below 50
- Contact form stops working
- SSL error detected

**Rollback is instant.** Vercel keeps all previous deployments. Rolling back simply points the domain to the previous deployment -- no rebuild needed.

---

## Cost Analysis

### Vercel Free Tier (Hobby Plan)

| Resource | Free Tier Limit | Typical Usage per Client Site |
|----------|----------------|-------------------------------|
| Bandwidth | 100 GB/month | 1-5 GB/month |
| Serverless Function Executions | 100,000/month | 100-500/month (contact forms) |
| Build Minutes | 6,000 minutes/month | 1-2 min per build |
| Deployments | 100/day | 1-5/month per site |
| Projects | Unlimited | One per client |
| Custom Domains | Unlimited | One per client |
| SSL Certificates | Included | Automatic |
| Edge Functions | 500,000/month | Minimal unless using middleware |

**Assessment:** A single Vercel Hobby account can host 20-50 low-traffic client sites within free tier limits. The primary constraint is bandwidth (100 GB shared across all projects).

### Vercel Pro Plan ($20/month)

| Resource | Pro Limit | When You Need It |
|----------|-----------|-----------------|
| Bandwidth | 1 TB/month | When hosting 50+ sites or high-traffic sites |
| Serverless Function Executions | 1,000,000/month | Heavy form usage or API routes |
| Build Minutes | Unlimited | Frequent rebuilds across many sites |
| Team Members | $20/month per member | If collaborators need dashboard access |
| Password Protection | Included | Client preview protection |
| Vercel Analytics | Included | Real user monitoring |

**When to upgrade:** When total bandwidth across all client sites exceeds ~80 GB/month, or when you need team collaboration or password-protected previews.

### Cost per Client Site

| Scenario | Monthly Cost |
|----------|-------------|
| 10 client sites on free tier | $0/month |
| 30 client sites on free tier | $0/month (approaching bandwidth limit) |
| 50 client sites on Pro | $20/month ($0.40/site) |
| 100 client sites on Pro | $20/month ($0.20/site) |

**Client sites are essentially free to host.** This is a significant competitive advantage -- your hosting costs are near-zero, so the entire retainer is margin minus labor and tool costs.

---

## CI/CD Pipeline

### Automatic Redeploy on Git Push

This is the default behavior with Vercel's GitHub integration. No additional CI/CD setup needed:

```
Developer pushes to main -> Vercel detects push -> Builds site -> Deploys to production
Developer pushes to branch -> Vercel detects push -> Builds site -> Deploys as preview
```

### Automated Content Updates

For sites with dynamic content (blog posts, testimonials), set up scheduled rebuilds:

**Option A: Vercel Deploy Hook**
```bash
# Create a deploy hook in Vercel project settings
# Get webhook URL: https://api.vercel.com/v1/integrations/deploy/prj_xxx/xxx

# Trigger rebuild via cron job (e.g., daily at midnight)
curl -X POST https://api.vercel.com/v1/integrations/deploy/prj_xxx/xxx
```

**Option B: n8n scheduled workflow**
- n8n workflow triggers daily
- Checks if content has changed (new reviews, new blog post)
- If changed: trigger deploy hook
- If unchanged: skip (save build minutes)

### Build Caching

Vercel caches build artifacts between deployments:
- `node_modules` cached (speeds up dependency installation)
- Build output cached for unchanged pages (ISR / Astro)
- Image optimization results cached
- Typical rebuild time for minor content changes: 30-60 seconds

---

## Multi-Site Management

### Organization Structure

```
Vercel Account (your agency)
  |
  |- Project: smith-plumbing-austin
  |    |- Domain: smithplumbing.com
  |    |- Domain: www.smithplumbing.com
  |
  |- Project: jones-solar-dallas
  |    |- Domain: jonessolar.com
  |
  |- Project: abc-dentistry-houston
  |    |- Domain: abcdentistry.com
  |
  |- ... (one project per client)
```

### Bulk Operations

For managing many sites, use the Vercel API:

```javascript
// List all projects
const projects = await fetch('https://api.vercel.com/v9/projects', {
  headers: { Authorization: `Bearer ${VERCEL_TOKEN}` }
}).then(r => r.json());

// Check deployment status for all projects
for (const project of projects.projects) {
  const deployments = await fetch(
    `https://api.vercel.com/v6/deployments?projectId=${project.id}&limit=1`,
    { headers: { Authorization: `Bearer ${VERCEL_TOKEN}` } }
  ).then(r => r.json());

  console.log(`${project.name}: ${deployments.deployments[0]?.state}`);
}
```

### Monitoring Dashboard

Build a simple dashboard (or Airtable view) tracking:

| Client | Domain | Last Deploy | Status | Lighthouse Score | Uptime |
|--------|--------|------------|--------|-----------------|--------|
| Smith Plumbing | smithplumbing.com | Feb 5, 2026 | Live | 96 | 99.9% |
| Jones Solar | jonessolar.com | Feb 3, 2026 | Live | 94 | 99.8% |
| ABC Dentistry | abcdentistry.com | Feb 1, 2026 | Preview | 91 | -- |

---

## Troubleshooting Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Build fails | Missing dependency | Check package.json, run `npm install` locally |
| Build fails | Environment variable missing | Add to Vercel project settings |
| 404 on pages | Incorrect routing | Check Astro/Next.js page file structure |
| Slow builds | Large images in repo | Use image optimization, external CDN, or Git LFS |
| Domain not working | DNS not propagated | Wait 24-48 hours, verify DNS records |
| SSL error | Domain just added | Vercel auto-provisions SSL within minutes |
| Function timeout | Contact form API slow | Increase function timeout in vercel.json |
| Bandwidth exceeded | High traffic or large assets | Upgrade to Pro or optimize asset sizes |

---

## Deployment Automation Script

Complete script OpenClaw runs to deploy a new client site:

```bash
#!/bin/bash
# deploy-client-site.sh
# Called by OpenClaw after site generation

SLUG=$1
BUSINESS_NAME=$2
DOMAIN=$3  # Optional

# 1. Create GitHub repo
gh repo create client-sites/${SLUG} --private

# 2. Clone and copy generated files
git clone git@github.com:youragency/client-sites/${SLUG}.git /tmp/${SLUG}
cp -r /generated/${SLUG}/* /tmp/${SLUG}/
cd /tmp/${SLUG}

# 3. Initial commit and push
git add .
git commit -m "Initial site for ${BUSINESS_NAME}"
git push origin main

# 4. Link to Vercel (creates project)
vercel link --yes --project=${SLUG}

# 5. Set environment variables
vercel env add SITE_URL production <<< "https://${DOMAIN:-${SLUG}.vercel.app}"

# 6. Deploy to production
vercel deploy --prod

# 7. Add custom domain (if provided)
if [ -n "$DOMAIN" ]; then
  vercel domains add ${DOMAIN}
  echo "Configure DNS for ${DOMAIN}:"
  echo "  A record: @ -> 76.76.21.21"
  echo "  CNAME: www -> cname.vercel-dns.com"
fi

# 8. Verify deployment
DEPLOY_URL=$(vercel inspect --json | jq -r '.url')
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://${DEPLOY_URL})

if [ "$HTTP_STATUS" = "200" ]; then
  echo "Deployment successful: https://${DEPLOY_URL}"
else
  echo "Deployment verification failed: HTTP ${HTTP_STATUS}"
fi

# 9. Cleanup
rm -rf /tmp/${SLUG}
```
