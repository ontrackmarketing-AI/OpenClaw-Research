# Static Site Generators for Agency Websites

## Overview

Choosing the right static site generator (SSG) for agency client websites is a foundational decision that affects build speed, developer experience, client satisfaction, hosting costs, and long-term maintainability. This document compares the three most relevant SSGs for your agency workflow and provides clear recommendations for which to use when.

---

## Next.js

### What It Is
Next.js is a React-based framework by Vercel that supports static site generation (SSG), server-side rendering (SSR), incremental static regeneration (ISR), and client-side rendering. It is the most feature-rich option but also the most complex.

### Rendering Modes
- **SSG (Static Site Generation):** Pages pre-rendered at build time as static HTML. Best performance.
- **SSR (Server-Side Rendering):** Pages rendered on each request. Required for personalized content.
- **ISR (Incremental Static Regeneration):** Static pages that revalidate after a configurable time period. Best of both worlds for semi-dynamic content.
- **Client-Side Rendering:** Traditional React SPA behavior for highly interactive sections.

### Strengths
- Full React ecosystem (thousands of components, libraries)
- App Router (Next.js 13+) with layouts, loading states, error boundaries
- API routes for backend functionality (contact forms, webhooks)
- Image optimization built-in (next/image with automatic WebP, lazy loading, responsive sizing)
- Middleware for redirects, rewrites, authentication
- Excellent TypeScript support
- Vercel deployment is seamless (one-click, automatic)

### Weaknesses
- JavaScript-heavy output: even "static" Next.js sites ship React runtime (~80-150KB JS)
- Slower build times for large sites (each page requires React hydration setup)
- Complexity overhead for simple brochure sites
- Requires React knowledge to customize templates
- Bundle size grows with features
- Cold starts on serverless if using SSR

### Your Experience
You have multiple Next.js deployments on Vercel. You are comfortable with the framework, its deployment pipeline, and its configuration options. This is your strongest SSG skill.

### Performance Characteristics
- Build time: 30-120 seconds for a 10-page site (depends on data fetching)
- Lighthouse score: 85-100 with proper optimization
- First Contentful Paint: 0.8-1.5 seconds (depends on JS bundle)
- Time to Interactive: 1.5-3.5 seconds (React hydration required)
- Bundle size: 80-200KB JS minimum (React runtime + framework code)

### Cost on Vercel
- Free tier: 100GB bandwidth, 100 deployments/day, serverless functions included
- Pro: $20/month per team member (1TB bandwidth, more build minutes)
- Most client sites will run comfortably on the free tier

### Best For
- Sites requiring interactivity (calculators, dashboards, dynamic forms)
- Sites with user authentication
- Sites needing API routes (e.g., backend contact form processing)
- Complex multi-section sites with dynamic content
- Sites where you want to add features incrementally over time

### Not Ideal For
- Simple 5-7 page brochure sites (too much overhead)
- Maximum Lighthouse performance scores (JS bundle is a tax)
- Sites where load speed is the number one priority

---

## Astro

### What It Is
Astro is a content-focused web framework that uses an "islands architecture" to ship zero JavaScript by default, adding interactive components only where needed. It supports components from multiple frameworks (React, Vue, Svelte, Preact) but renders them as static HTML unless explicitly marked as interactive.

### Rendering Approach
- **Zero JS by default:** Pages are pure HTML + CSS unless you opt in to client-side JavaScript
- **Islands:** Interactive components are isolated "islands" that hydrate independently
- **Partial hydration directives:**
  - `client:load` -- hydrate on page load
  - `client:idle` -- hydrate when browser is idle
  - `client:visible` -- hydrate when element scrolls into view
  - `client:media` -- hydrate based on media query
  - `client:only` -- render only on client (skip SSR)

### Strengths
- Near-perfect Lighthouse scores out of the box (no JS = fast)
- Content collections: type-safe markdown/MDX content management
- Bring-your-own-framework: use React components where needed, static HTML elsewhere
- Extremely fast build times
- Excellent SEO defaults (static HTML, proper meta tags, sitemaps)
- Built-in markdown and MDX support
- Image optimization (astro:assets with automatic format conversion)
- Integrations: Tailwind, MDX, sitemap, RSS -- all official packages
- Growing ecosystem of themes and templates

### Weaknesses
- Smaller ecosystem than React/Next.js
- Less suitable for highly interactive applications
- Relatively newer (v1.0 in 2022, v4.0+ in 2024) -- less community content
- Some React components need adaptation for island architecture
- No built-in API routes for SSG mode (use serverless functions or separate API)

### Your Experience
You have existing Astro deployments. You understand the framework's approach and have working build pipelines.

### Performance Characteristics
- Build time: 5-30 seconds for a 10-page site
- Lighthouse score: 95-100 consistently (pure HTML output)
- First Contentful Paint: 0.3-0.8 seconds
- Time to Interactive: 0.3-0.8 seconds (no JS to hydrate for static pages)
- Bundle size: 0KB JS for fully static pages, only what you add for interactive islands

### Cost on Vercel
- Same as Next.js on Vercel free tier
- Also deployable to Netlify, Cloudflare Pages, or any static hosting
- Cloudflare Pages: free tier is extremely generous (unlimited bandwidth)

### Best For
- Marketing/brochure websites (the majority of agency client sites)
- Content-heavy sites (blogs, portfolios, directories)
- Sites where Lighthouse scores matter (SEO-critical businesses)
- Template-based generation where consistency is key
- Fast build pipelines (important when generating many client sites)

### Not Ideal For
- Highly interactive web applications
- Sites requiring complex state management
- Real-time features (chat, notifications, live data)

---

## Hugo

### What It Is
Hugo is a Go-based static site generator known for being the fastest SSG available. It compiles sites in milliseconds, handles thousands of pages effortlessly, and has a mature, stable ecosystem.

### Rendering Approach
- **Pure static:** All pages are pre-rendered as HTML at build time
- **Go templates:** Uses Go's `html/template` for page layouts
- **No JavaScript framework:** output is plain HTML/CSS + whatever JS you manually include
- **Taxonomies:** built-in support for tags, categories, and custom taxonomies

### Strengths
- Fastest build times of any SSG (1,000 pages in <1 second)
- Single binary -- no Node.js, no npm, no dependency management
- Extremely stable and mature (since 2013)
- Built-in image processing (resize, crop, filter)
- Multi-language support built in
- Extensive theme marketplace (300+ themes)
- Powerful content organization (sections, taxonomies, archetypes)
- Excellent documentation

### Weaknesses
- Go templates have a steep learning curve (not intuitive for JS developers)
- No component ecosystem (no React/Vue components)
- Limited interactivity without adding separate JS
- Harder to integrate modern JS tools (Tailwind requires extra setup)
- Template syntax feels dated compared to JSX or Astro components
- Fewer agency-specific themes than WordPress alternatives

### Your Experience
You do not have existing Hugo deployments. There would be a learning curve for Go templates and Hugo's content organization model.

### Performance Characteristics
- Build time: <1 second for 100 pages, 2-5 seconds for 1,000 pages
- Lighthouse score: 95-100 (pure HTML output)
- First Contentful Paint: 0.3-0.6 seconds
- Time to Interactive: 0.3-0.6 seconds
- Bundle size: 0KB JS unless manually added

### Cost on Vercel
- Same hosting costs as other SSGs
- Hugo sites are typically the smallest in file size

### Best For
- Extremely simple brochure sites (5-10 pages, minimal interactivity)
- Sites with massive page counts (thousands of location pages, directory sites)
- Developers who prefer Go over JavaScript

### Not Ideal For
- Your agency workflow (unfamiliar technology adds development time)
- Sites requiring any JavaScript interactivity
- Template-based generation (Go templates are harder to maintain than JSX/Astro)

---

## Head-to-Head Comparison

| Feature | Next.js | Astro | Hugo |
|---------|---------|-------|------|
| **Language** | JavaScript/TypeScript | JavaScript/TypeScript | Go |
| **Component Model** | React | Multi-framework + Astro | Go templates |
| **Default JS Output** | 80-200KB | 0KB | 0KB |
| **Build Speed (10 pages)** | 30-120s | 5-30s | <1s |
| **Build Speed (1000 pages)** | 5-15 min | 30-90s | 2-5s |
| **Lighthouse Score (typical)** | 85-95 | 95-100 | 95-100 |
| **Interactivity** | Full React | Islands (opt-in) | Manual JS only |
| **API Routes** | Built-in | Serverless adapters | None |
| **Image Optimization** | Built-in (excellent) | Built-in (good) | Built-in (basic) |
| **TypeScript** | Excellent | Excellent | N/A |
| **Learning Curve** | Moderate (React) | Low-Moderate | Moderate-High (Go) |
| **Your Familiarity** | High | High | None |
| **Template Ecosystem** | Large (Vercel templates) | Growing | Large (Hugo themes) |
| **SEO Defaults** | Good (needs config) | Excellent | Excellent |
| **Hosting Options** | Vercel, AWS, any | Any static host | Any static host |

---

## Recommendation for Your Agency

### Primary SSG: Astro (80% of client sites)

**Use Astro for:** Every standard marketing/brochure website, blog, portfolio, and landing page. This covers the vast majority of local business clients.

**Rationale:**
1. Perfect Lighthouse scores without effort -- critical for SEO-focused agency
2. Fast build times -- important when OpenClaw generates sites programmatically
3. Zero JS by default -- simplest possible output for client sites
4. You already have Astro experience
5. Tailwind CSS integration is seamless
6. Content collections make template-based generation clean and maintainable
7. Can add React/Vue islands if a specific page needs interactivity

**Template structure for Astro-based client sites:**
```
client-site/
  src/
    layouts/
      BaseLayout.astro       # HTML head, nav, footer
      ServiceLayout.astro    # Service page template
    pages/
      index.astro            # Homepage
      about.astro            # About page
      services/
        index.astro          # Services overview
        [service].astro      # Dynamic service pages
      contact.astro          # Contact page
      blog/
        [slug].astro         # Blog post pages
    components/
      Hero.astro             # Hero section
      ServiceCard.astro      # Service listing card
      Testimonials.astro     # Testimonial carousel
      ContactForm.astro      # Contact form (island if needed)
      FAQ.astro              # FAQ accordion
    content/
      services/              # Markdown files per service
      blog/                  # Markdown files per blog post
      testimonials/          # Testimonials data
    styles/
      global.css             # Tailwind + custom styles
  public/
    images/                  # Client images and assets
  astro.config.mjs           # Astro configuration
  tailwind.config.mjs        # Tailwind configuration
```

### Secondary SSG: Next.js (20% of client sites)

**Use Next.js for:** Client sites requiring interactivity beyond what Astro islands can handle -- dashboards, booking systems, client portals, e-commerce, or sites where you plan to build advanced features over time.

**Specific use cases:**
- Client with a booking/scheduling system
- Client who wants a customer portal
- E-commerce sites with dynamic inventory
- Sites requiring authentication (member areas)
- Complex multi-step forms (insurance quotes, project estimators)

### Skip: Hugo

**Do not use Hugo.** The learning curve for Go templates is not justified when Astro provides comparable performance with familiar JavaScript/TypeScript tooling. Hugo's speed advantage (sub-second builds) is only meaningful at 500+ pages, which is rare for agency client sites.

---

## Template-to-Deployment Pipeline

This is how OpenClaw automates the full flow from lead data to deployed website:

```
1. Lead Data Collected
   - Business name, services, location, hours, reviews, branding preferences

2. Template Selection
   - Industry-specific template chosen (plumber, solar, dentist, etc.)
   - Layout variant selected based on content availability

3. Content Generation
   - OpenClaw (Claude) writes page copy based on business details
   - Service descriptions, about page, FAQ, meta descriptions
   - All content stored as markdown in content collections

4. Asset Preparation
   - Stock photos selected based on industry and location
   - Logo uploaded or placeholder created
   - Color scheme derived from logo or client preference
   - Favicon generated

5. Site Assembly
   - Astro template populated with generated content
   - Tailwind theme configured with client colors/fonts
   - All pages rendered and validated

6. Quality Check
   - Lighthouse audit: all scores >90
   - Mobile responsiveness verified
   - All links validated
   - SEO checklist verified (meta tags, schema, sitemap)
   - Accessibility check (alt text, heading hierarchy, contrast)

7. Deployment
   - Git push to GitHub repository
   - Vercel auto-deploys from GitHub
   - Custom domain configured (if available)
   - SSL auto-provisioned

8. Handoff
   - Client preview URL generated
   - Change request workflow activated
   - CMS access provided (if applicable)
```

**Target time from lead data to deployed site: under 30 minutes with human review, under 5 minutes fully automated.**
