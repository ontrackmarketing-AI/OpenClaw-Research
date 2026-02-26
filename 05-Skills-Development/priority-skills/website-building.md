# Website Building Skill

## Goal

Build an OpenClaw skill that generates, customizes, and deploys client websites. Given business information, industry, and desired features, the agent produces a fully functional, SEO-optimized website deployed to a live URL. This is a core deliverable for Rise Local's SMB clients.

---

## Tech Stack Options

### 1. Astro (Recommended for Marketing Sites)

**What it is**: A modern static site generator optimized for content-driven websites. Ships zero JavaScript by default for maximum performance.

**Why it fits your use case**:
- SMB marketing sites are primarily content-driven (about, services, contact, testimonials)
- Zero-JS default means blazing fast page loads (critical for PageSpeed scores)
- Island architecture: add interactive components only where needed
- You already have Astro experience
- Excellent SEO capabilities built-in

**Best for**: Plumber websites, solar company landing pages, dentist practice sites, lawyer firm sites, restaurant sites -- any primarily informational site.

**Deployment**: Vercel, Netlify, or Cloudflare Pages (all free tier available).

### 2. Next.js (For Interactive Features)

**What it is**: React-based framework with server-side rendering, API routes, and dynamic capabilities.

**Why it fits some use cases**:
- When the site needs interactive features (booking systems, client portals, dynamic pricing)
- When the site needs API routes (form handling, webhook endpoints)
- When the site needs authentication (client login areas)
- You already have Next.js experience

**Best for**: Sites with booking integration, client portals, dynamic content, or complex forms.

**Deployment**: Vercel (optimal) or self-hosted.

### 3. Hugo (For Maximum Speed)

**What it is**: The fastest static site generator, written in Go. Builds thousands of pages in seconds.

**Pros**: Extremely fast builds, simple Markdown content, minimal dependencies.
**Cons**: Go templating syntax is less intuitive, smaller component ecosystem, less flexible than Astro.

**Best for**: If you need to generate hundreds of similar sites quickly (template-based mass deployment).

### Recommendation

- **Default**: Astro for 90% of SMB marketing sites
- **When needed**: Next.js for sites requiring interactivity or server-side features
- **Fallback**: Hugo for ultra-simple single-page sites or mass deployment

---

## Skill Design: @yourname/website-builder

### skill.json Manifest (Key Sections)

```json
{
  "name": "@yourname/website-builder",
  "version": "1.0.0",
  "description": "Generate and deploy professional websites for SMB clients",
  "commands": ["/website", "/build-site", "/deploy-site"],
  "inputs": {
    "required": {
      "action": {
        "type": "string",
        "enum": ["generate", "customize", "deploy", "update", "audit"],
        "description": "Website action to perform"
      },
      "business": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "industry": { "type": "string" },
          "location": { "type": "string" },
          "phone": { "type": "string" },
          "email": { "type": "string" },
          "website_domain": { "type": "string" }
        }
      }
    },
    "optional": {
      "pages": {
        "type": "array",
        "items": { "type": "string" },
        "default": ["home", "about", "services", "contact"],
        "description": "Pages to generate"
      },
      "services": {
        "type": "array",
        "items": { "type": "string" },
        "description": "Services the business offers (generates individual service pages)"
      },
      "brand": {
        "type": "object",
        "properties": {
          "primary_color": { "type": "string" },
          "secondary_color": { "type": "string" },
          "logo_url": { "type": "string" },
          "font": { "type": "string" },
          "style": { "type": "string", "enum": ["modern", "classic", "bold", "minimal"] }
        }
      },
      "template": {
        "type": "string",
        "description": "Industry template name"
      },
      "framework": {
        "type": "string",
        "enum": ["astro", "nextjs"],
        "default": "astro"
      },
      "features": {
        "type": "array",
        "items": { "type": "string" },
        "description": "Special features: ['contact-form', 'booking', 'testimonials', 'blog', 'gallery', 'map', 'faq', 'reviews-widget']"
      },
      "content": {
        "type": "object",
        "description": "Pre-written content to use instead of AI-generated"
      },
      "deployment": {
        "type": "object",
        "properties": {
          "provider": { "type": "string", "enum": ["vercel", "netlify", "cloudflare"] },
          "domain": { "type": "string" },
          "environment": { "type": "string", "enum": ["preview", "production"] }
        }
      }
    }
  },
  "outputs": {
    "site_url": { "type": "string", "description": "Deployed URL or local preview URL" },
    "repo_url": { "type": "string", "description": "Git repository URL" },
    "pages_generated": { "type": "array" },
    "lighthouse_scores": { "type": "object", "description": "Performance, SEO, accessibility, best practices" }
  },
  "tools": {
    "required": ["file_write", "file_read", "shell", "web_fetch"],
    "optional": ["browser", "code_execution"]
  },
  "permissions": {
    "network": ["api.vercel.com", "api.netlify.com", "api.github.com", "api.unsplash.com", "*"],
    "filesystem": ["read:./templates", "write:./output", "write:./sites"],
    "system": ["shell:node", "shell:npm", "shell:git", "shell:vercel"],
    "environment": [
      "VERCEL_TOKEN",
      "GITHUB_TOKEN",
      "UNSPLASH_ACCESS_KEY"
    ]
  }
}
```

### Execution Flow: Full Site Generation

```
Step 1: Select Template
  Input: industry, style, features
  Process: Match to best industry template or default template
  Output: Template project structure

Step 2: Customize Design
  Input: brand colors, fonts, logo
  Process:
    - Update CSS variables / Tailwind config with brand colors
    - Replace placeholder logo with client logo
    - Set fonts in theme configuration
    - Adjust component styles to match brand
  Output: Branded template

Step 3: Generate Content
  Input: business info, services, industry context
  Process: AI generates content for each page:
    - Homepage: hero headline, value proposition, service overview, CTA
    - About: company story, team (if provided), values, mission
    - Services: individual service pages with descriptions, benefits, process
    - Contact: contact form, map embed, business hours, phone/email
    - Additional pages based on features list
  Output: Markdown/MDX content files for each page

Step 4: Generate SEO Elements
  Input: business info, location, services, content
  Process: For each page:
    - Title tag (60 chars max, includes business name + location + keyword)
    - Meta description (160 chars max, compelling with CTA)
    - Open Graph tags (for social sharing)
    - Schema.org structured data (LocalBusiness, Service, FAQ)
    - XML sitemap
    - robots.txt
    - Canonical URLs
  Output: SEO metadata per page + sitemap + robots.txt

Step 5: Integrate Features
  Input: features list
  Process: Add requested components:
    - Contact form -> Formspree or custom handler -> GHL webhook
    - Testimonials -> Static component with client reviews
    - Google Map -> Embedded Google Maps iframe
    - FAQ -> Schema-marked FAQ accordion
    - Blog -> Blog post template + CMS setup
    - Gallery -> Image gallery with lightbox
    - Reviews widget -> Embedded Google/Yelp reviews
    - Booking -> Cal.com or GHL calendar embed
  Output: Feature components integrated into site

Step 6: Build and Validate
  Input: Complete site project
  Process:
    - npm install dependencies
    - Build the site (astro build / next build)
    - Run Lighthouse audit
    - Check for broken links
    - Validate HTML
    - Test mobile responsiveness
  Output: Built site + Lighthouse scores + validation report

Step 7: Deploy
  Input: Built site + deployment config
  Process:
    - Initialize Git repo (if not exists)
    - Push to GitHub
    - Deploy via Vercel CLI / Netlify CLI
    - Configure custom domain (if provided)
    - Verify deployment
  Output: Live URL + repo URL
```

---

## Template System

### Industry-Specific Templates

Each template is a complete Astro project with industry-appropriate design, placeholder content, and optimized structure.

```
templates/
├── home-services/
│   ├── plumber/           # Blue tones, pipe imagery, emergency CTA
│   ├── hvac/              # Cool/warm imagery, seasonal promotions
│   ├── electrician/       # Yellow/orange accents, safety-focused
│   ├── roofing/           # Sturdy imagery, before/after sections
│   └── landscaping/       # Green tones, portfolio gallery
├── healthcare/
│   ├── dental/            # Clean white, smile imagery, booking-focused
│   ├── chiropractor/      # Wellness imagery, testimonial-heavy
│   └── veterinarian/      # Warm tones, pet imagery
├── professional/
│   ├── lawyer/            # Dark tones, authoritative, trust signals
│   ├── accountant/        # Blue/green, organized, service breakdown
│   └── real-estate/       # Property imagery, listing integration
├── food-service/
│   ├── restaurant/        # Food photography, menu, online ordering
│   └── catering/          # Event imagery, menu packages
├── energy/
│   └── solar/             # Green/yellow, ROI calculator, installation gallery
└── generic/
    ├── service-business/  # Adaptable to any service industry
    └── local-business/    # Simple, all-purpose local business template
```

### Template Contents

Each template includes:

```
template-name/
├── src/
│   ├── layouts/
│   │   └── BaseLayout.astro       # Main layout with SEO, header, footer
│   ├── components/
│   │   ├── Header.astro           # Navigation, logo, CTA button
│   │   ├── Footer.astro           # Links, contact info, social
│   │   ├── Hero.astro             # Hero section with headline + image
│   │   ├── ServiceCard.astro      # Individual service display
│   │   ├── Testimonial.astro      # Customer testimonial
│   │   ├── ContactForm.astro      # Contact form component
│   │   ├── FAQ.astro              # FAQ accordion with schema
│   │   ├── Map.astro              # Google Maps embed
│   │   └── CTA.astro              # Call-to-action section
│   ├── pages/
│   │   ├── index.astro            # Homepage
│   │   ├── about.astro            # About page
│   │   ├── services/
│   │   │   ├── index.astro        # Services overview
│   │   │   └── [service].astro    # Dynamic service page
│   │   ├── contact.astro          # Contact page
│   │   └── blog/                  # Optional blog
│   │       ├── index.astro
│   │       └── [slug].astro
│   ├── content/
│   │   ├── config.ts              # Content collections config
│   │   ├── services/              # Service markdown files
│   │   ├── testimonials/          # Testimonial data
│   │   └── blog/                  # Blog post markdown
│   └── styles/
│       └── globals.css            # Tailwind + custom styles
├── public/
│   ├── images/                    # Placeholder images (replaced per client)
│   ├── favicon.svg
│   └── robots.txt
├── astro.config.mjs
├── tailwind.config.mjs
├── package.json
└── tsconfig.json
```

---

## Content Generation

### AI-Written Copy Guidelines

When generating content for each page, the skill uses these guidelines:

**Homepage**:
- Hero headline: 8-12 words, value-focused, includes location
  - Example: "Austin's Most Trusted Plumber -- 24/7 Emergency Service"
- Subheadline: 15-25 words, supporting the headline
- Service overview: 3-6 services with brief descriptions
- Trust signals: years in business, number of customers, rating
- Primary CTA: "Get a Free Quote" or "Schedule Service"

**About Page**:
- Company story: 2-3 paragraphs, professional but warm
- Why choose us: 3-5 differentiators
- Team section (if info provided): name, role, brief bio
- Values/mission: 1 paragraph

**Service Pages**:
- Service description: 2-3 paragraphs explaining the service
- Benefits: 4-6 bullet points
- Process: step-by-step how it works
- FAQ: 3-5 common questions about the service
- CTA: specific to the service

**Contact Page**:
- Contact form with name, email, phone, message, service dropdown
- Business address with Google Maps embed
- Phone number (click-to-call on mobile)
- Business hours
- Emergency contact info (if applicable)

### Content Personalization

The AI tailors content based on:
- **Industry**: Uses industry-specific terminology and pain points
- **Location**: Includes city/area references throughout ("serving Austin and surrounding areas")
- **Services**: Creates unique descriptions for each service
- **Competitors**: If competitor data is available, emphasizes differentiators
- **Reviews**: Incorporates real review quotes as testimonials

---

## SEO Implementation

### Technical SEO Checklist (Automated)

Every generated site includes:

- [ ] Title tags: unique per page, 50-60 characters, keyword + location + brand
- [ ] Meta descriptions: unique per page, 150-160 characters, with CTA
- [ ] H1 tags: one per page, matches title intent
- [ ] Header hierarchy: H1 -> H2 -> H3 (proper nesting)
- [ ] Image alt text: descriptive, includes keywords naturally
- [ ] Internal linking: services linked from homepage, breadcrumbs on subpages
- [ ] XML sitemap: auto-generated, includes all pages with last-modified dates
- [ ] robots.txt: allows all crawlers, references sitemap
- [ ] Canonical URLs: self-referencing canonicals on all pages
- [ ] Open Graph tags: title, description, image for social sharing
- [ ] Twitter Card tags: summary_large_image format
- [ ] Favicon: SVG format for scalability

### Schema.org Structured Data

```json
// LocalBusiness schema on every page
{
  "@context": "https://schema.org",
  "@type": "Plumber",
  "name": "Acme Plumbing Co.",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "123 Main St",
    "addressLocality": "Austin",
    "addressRegion": "TX",
    "postalCode": "78701"
  },
  "telephone": "+1-512-555-0123",
  "url": "https://acmeplumbing.com",
  "openingHours": "Mo-Fr 08:00-18:00",
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.8",
    "reviewCount": "127"
  },
  "areaServed": {
    "@type": "City",
    "name": "Austin"
  }
}

// FAQ schema on service pages
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "How much does drain cleaning cost?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Drain cleaning typically costs between $100-$300..."
      }
    }
  ]
}
```

---

## Deployment via Vercel

### Deployment Commands

```bash
# Initial deployment (creates new Vercel project)
vercel --yes --prod

# Subsequent deployments
vercel --prod

# Preview deployment (for client review before going live)
vercel  # (without --prod flag)

# Configure custom domain
vercel domains add acmeplumbing.com
```

### Vercel Configuration (vercel.json)

```json
{
  "framework": "astro",
  "buildCommand": "astro build",
  "outputDirectory": "dist",
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" }
      ]
    },
    {
      "source": "/images/(.*)",
      "headers": [
        { "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }
      ]
    }
  ]
}
```

---

## Client Iteration Workflow

### Feedback Loop

```
1. Agent generates site -> deploys to preview URL
2. Client reviews preview URL
3. Client provides feedback (via email, chat, or meeting notes)
4. Agent processes feedback:
   - Text changes: update content files, rebuild, redeploy
   - Design changes: adjust CSS/Tailwind, rebuild, redeploy
   - Feature changes: add/remove components, rebuild, redeploy
   - Structural changes: add/remove pages, update navigation, rebuild, redeploy
5. Client reviews updated preview
6. Repeat until approved
7. Deploy to production domain
```

### Revision Commands

```
/website customize
  site: "acme-plumbing"
  changes: [
    { "page": "home", "section": "hero", "change": "Update headline to: Fastest Plumber in Austin" },
    { "page": "services", "action": "add", "service": "Water Heater Installation" },
    { "page": "about", "section": "team", "change": "Add team member: Jane Smith, Lead Technician" }
  ]
```

---

## Asset Management

### Image Strategy

| Source | Use Case | Cost |
|--------|----------|------|
| Unsplash API | Industry-relevant hero images, backgrounds | Free (attribution) |
| Client-provided | Logo, team photos, project photos | Free |
| AI-generated | Custom illustrations, icons | $0.02-0.10 per image |
| Stock icons | Service icons, feature icons | Free (Heroicons, Lucide) |

### Image Optimization

All images are automatically optimized:
- Convert to WebP format (smaller file size)
- Generate responsive sizes (640, 768, 1024, 1280, 1536px)
- Lazy loading on below-fold images
- Proper width/height attributes to prevent layout shift
- Alt text generated from context

---

## Quality Assurance

### Automated Checks Before Delivery

```bash
# Lighthouse audit (target: all scores 90+)
lighthouse https://preview-url --output json

# Broken link check
linkchecker https://preview-url

# HTML validation
html-validate dist/

# Mobile responsiveness check (via Playwright)
# Screenshot at 375px, 768px, 1024px, 1440px widths

# Performance budget
# Total page weight < 500KB
# Time to First Byte < 200ms
# Largest Contentful Paint < 2.5s
# Cumulative Layout Shift < 0.1
```

### Manual Review Checklist

- [ ] All business info is accurate (name, address, phone)
- [ ] Contact form submits successfully (to GHL or email)
- [ ] Phone numbers are click-to-call on mobile
- [ ] Navigation works on all pages
- [ ] Images are appropriate for the industry
- [ ] No placeholder text remaining ("Lorem ipsum")
- [ ] Footer has correct copyright year
- [ ] Social media links work (if provided)
- [ ] Google Maps shows correct location
- [ ] Site loads in under 3 seconds on 3G connection

---

*Last updated: 2026-02-05*
*Status: Skill design complete; templates need to be built per industry*
