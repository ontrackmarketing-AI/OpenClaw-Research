# Website Template System

## Overview

The template system is the engine that allows OpenClaw to generate professional, industry-specific websites for agency clients at scale. Rather than building each site from scratch, the system uses a layered architecture: a base layout provides consistent structure and quality, industry-specific customizations add relevant content patterns, and client branding personalizes the final output. This approach enables generating a complete client website in minutes rather than weeks.

---

## Template Architecture

### Three-Layer Design

```
Layer 1: Base Layout
  Common structure shared by ALL client sites:
  - HTML5 semantic structure
  - Navigation (responsive, mobile hamburger menu)
  - Footer (contact info, links, copyright)
  - Global styles (Tailwind CSS base)
  - SEO foundation (meta tags, structured data, sitemap)
  - Performance optimization (image handling, lazy loading)
  - Accessibility baseline (ARIA labels, heading hierarchy, contrast)

Layer 2: Industry Customization
  Content patterns specific to the business type:
  - Section order and emphasis
  - Industry-specific components (e.g., service area map for plumbers)
  - Relevant CTAs (e.g., "Book Free Consultation" for lawyers)
  - Testimonial/review display style
  - Trust signals relevant to industry (licenses, certifications)
  - FAQ content templates
  - Service page structure

Layer 3: Client Branding
  Unique to each individual business:
  - Business name, logo, tagline
  - Color palette (primary, secondary, accent)
  - Typography selections
  - Custom images (or curated stock photos)
  - Specific service list and descriptions
  - Contact information (phone, email, address)
  - Business hours
  - Team member bios and photos
  - Testimonials and reviews
  - Service areas/locations
```

---

## Industry-Specific Templates

### 1. Plumber / HVAC Template

**Key sections:**
- **Hero:** Emergency service emphasis, phone number prominent, "Available 24/7" badge
- **Services grid:** Categorized by type (residential, commercial, emergency)
  - Plumbing: drain cleaning, water heater, pipe repair, sewer, fixture installation
  - HVAC: AC repair, heating, maintenance, installation, indoor air quality
- **Emergency CTA banner:** Sticky or floating, with click-to-call phone number
- **Service area map:** Interactive map showing covered zip codes/cities
- **Reviews section:** Google reviews pulled in, star rating displayed prominently
- **Licensing/insurance:** State license number, insurance verification, bonding info
- **Before/after gallery:** Photos of completed work
- **Pricing transparency:** "Starting from" pricing or "Free Estimates" emphasis
- **FAQ:** Common questions about services, pricing, emergency availability

**Unique components:**
```astro
<!-- EmergencyBanner.astro -->
<div class="bg-red-600 text-white py-3 text-center sticky top-0 z-50">
  <p class="text-lg font-bold">
    Plumbing Emergency? Call Now:
    <a href="tel:{phone}" class="underline">{phone}</a>
    - Available 24/7
  </p>
</div>

<!-- ServiceAreaMap.astro -->
<section id="service-area">
  <h2>Areas We Serve</h2>
  <div class="grid md:grid-cols-2 gap-8">
    <div id="map"></div>
    <div class="service-area-list">
      {areas.map(area => <span class="badge">{area}</span>)}
    </div>
  </div>
</section>
```

**Content generation prompts:**
- Homepage hero: "Write a compelling hero headline for a {city} {plumber/HVAC} company called {name} that emphasizes reliability and fast service"
- Service pages: "Write a 300-word service page for {service_name} targeting homeowners in {city}. Include common problems, our solution approach, and a call to action"
- FAQ: "Generate 8 common questions and answers about {service} for homeowners"

---

### 2. Solar Installer Template

**Key sections:**
- **Hero:** Savings-focused headline, "See How Much You Can Save" CTA
- **Savings calculator:** Interactive tool (estimated bill savings based on roof size and sun hours)
- **How it works:** 3-4 step process explanation (consultation, design, installation, activation)
- **Financing options:** Loan, lease, PPA, cash purchase comparison
- **Gallery:** Installation photos (residential roofs, ground mounts, commercial)
- **Testimonials:** Video testimonials preferred, with savings numbers
- **Certifications:** NABCEP certification, manufacturer partnerships (SunPower, Tesla, etc.)
- **Environmental impact:** CO2 saved, trees equivalent, community impact
- **Incentives section:** Federal tax credit (30% ITC), state incentives, utility rebates
- **FAQ:** Permitting, timeline, maintenance, warranty, grid connection

**Unique components:**
```astro
<!-- SavingsCalculator.astro (interactive island) -->
<div client:visible>
  <h2>See Your Estimated Savings</h2>
  <form>
    <label>Average Monthly Electric Bill</label>
    <input type="range" min="100" max="500" value="200" />
    <label>Roof Type</label>
    <select>
      <option>Asphalt Shingle</option>
      <option>Tile</option>
      <option>Metal</option>
      <option>Flat</option>
    </select>
  </form>
  <div class="results">
    <p>Estimated 25-Year Savings: <strong>${calculated}</strong></p>
    <p>Monthly Payment (financed): <strong>${monthly}</strong></p>
    <button>Get Your Free Custom Quote</button>
  </div>
</div>

<!-- IncentivesSection.astro -->
<section>
  <h2>Available Solar Incentives</h2>
  <div class="grid md:grid-cols-3 gap-6">
    <div class="incentive-card">
      <h3>Federal Tax Credit</h3>
      <p class="text-4xl font-bold text-green-600">30%</p>
      <p>of system cost as tax credit through 2032</p>
    </div>
    <!-- State and utility incentives dynamically populated -->
  </div>
</section>
```

---

### 3. Dentist Template

**Key sections:**
- **Hero:** Warm, welcoming imagery, "Accepting New Patients" badge, appointment CTA
- **Services list:** General dentistry, cosmetic, orthodontics, emergency, pediatric
- **Team section:** Doctor bios with photos, credentials, specialties, personal touches
- **Appointment booking:** Online scheduling integration (or contact form)
- **Insurance information:** Accepted insurance providers list, financing options
- **Patient testimonials:** Focus on comfort and results
- **Office tour:** Photos of office, modern equipment, comfortable waiting area
- **Technology:** Highlight advanced equipment (digital X-rays, lasers, 3D imaging)
- **New patient information:** What to expect, forms to download, first visit process
- **Location/hours:** Map, hours, parking information

**Unique components:**
- Insurance provider grid (logos of accepted insurances)
- Before/after smile gallery (with patient consent notice)
- Virtual office tour carousel
- New patient special offer banner

---

### 4. Lawyer Template

**Key sections:**
- **Hero:** Authority-focused, "Protecting Your Rights Since {year}" or "Over {X} Cases Won"
- **Practice areas:** Each area gets its own page (personal injury, family law, criminal, etc.)
- **Case results:** Notable settlements/verdicts with amounts (where ethically permitted)
- **Attorney profiles:** Detailed bios, education, bar admissions, awards, speaking engagements
- **Free consultation CTA:** Prominent on every page, multiple formats (call, form, chat)
- **Client testimonials:** With client initials for privacy (legal ethics requirements)
- **Legal resources:** Blog/articles demonstrating expertise, educational content
- **Awards/recognition:** Super Lawyers, Avvo rating, Martindale-Hubbell, bar associations

**Important compliance notes:**
- Legal advertising rules vary by state
- Include required disclaimers (e.g., "Results may vary", "Prior results do not guarantee similar outcome")
- Some states require "Attorney Advertising" notice
- Testimonials may need specific disclaimers
- OpenClaw should include appropriate state-specific disclaimers automatically

**Unique components:**
- Practice area cards with icons and brief descriptions
- Case results ticker or showcase section
- Consultation request form (detailed: case type, brief description, contact)
- Ethics-compliant disclaimer footer

---

### 5. Landscaper Template

**Key sections:**
- **Hero:** Seasonal imagery (lush green lawn, fall colors, snow removal), "Transform Your Outdoor Space"
- **Portfolio gallery:** Before/after projects, categorized by type
- **Seasonal services:** What's available now vs year-round
  - Spring: cleanup, planting, mulching
  - Summer: mowing, irrigation, pest control
  - Fall: leaf removal, aeration, overseeding
  - Winter: snow removal, holiday lighting, dormant pruning
- **Services:** Design, installation, maintenance, hardscaping, irrigation
- **Quote request form:** Property size, services needed, budget range, photos upload
- **Service area:** Map or city list
- **Testimonials:** With project photos alongside quotes

**Unique components:**
- Seasonal service toggle (show relevant services based on current season)
- Before/after image slider (interactive comparison)
- Project gallery with category filters
- Photo upload in quote request form

---

### 6. General Contractor Template

**Key sections:**
- **Hero:** Impressive project photo, "Building Dreams Since {year}", "Licensed & Insured"
- **Project gallery:** Categorized (kitchens, bathrooms, additions, whole home, commercial)
- **Our process:** Step-by-step (consultation, design, permits, construction, walkthrough)
- **Certifications:** State license, EPA lead-safe, OSHA, manufacturer certifications
- **Specialties:** Remodeling, new construction, commercial, specific room types
- **Client testimonials:** With project photos and details
- **Resources:** Remodeling cost guides, timeline expectations, permit information
- **Financing:** Payment plans, home equity options, lender partnerships

**Unique components:**
- Interactive project timeline ("Your project from start to finish")
- Certification badge display
- Cost estimator (basic: room type + square footage = rough estimate)
- Progress photo gallery for active projects (password-protected)

---

## Template Component Library

All templates share a common component library. Each component is configurable via props:

### Core Components

| Component | Description | Configuration |
|-----------|-------------|---------------|
| `Hero` | Full-width hero with headline, subheadline, CTA | image, title, subtitle, cta_text, cta_link, overlay_color |
| `ServiceCard` | Individual service with icon, title, description | icon, title, description, link |
| `ServicesGrid` | Grid of ServiceCards | services[], columns (2/3/4) |
| `Testimonials` | Rotating or grid testimonials | testimonials[], style (carousel/grid/featured) |
| `CTABanner` | Call-to-action strip | title, subtitle, button_text, button_link, bg_color |
| `ContactForm` | Contact/quote request form | fields[], submit_endpoint, success_message |
| `FAQ` | Accordion FAQ section | questions[], schema_markup (true/false) |
| `TeamGrid` | Team member cards | members[], style (grid/list) |
| `Gallery` | Project/photo gallery | images[], categories[], lightbox (true/false) |
| `ReviewDisplay` | Google reviews showcase | reviews[], show_rating, show_count |
| `LocationMap` | Google Maps embed | address, zoom, markers[] |
| `Footer` | Site footer | contact_info, links[], social[], copyright |
| `Navigation` | Responsive nav bar | logo, links[], cta_button, sticky (true/false) |
| `AboutSection` | Business story section | title, content, image, values[] |
| `StatsBar` | Key metrics display | stats[] (e.g., "500+ Projects", "15 Years") |

### Component Props Example

```astro
---
// Hero.astro
interface Props {
  title: string;
  subtitle?: string;
  ctaText: string;
  ctaLink: string;
  backgroundImage: string;
  overlayOpacity?: number; // 0-100
  phone?: string; // If provided, shows click-to-call
  alignment?: 'left' | 'center' | 'right';
}
const { title, subtitle, ctaText, ctaLink, backgroundImage,
        overlayOpacity = 50, phone, alignment = 'center' } = Astro.props;
---

<section class="relative h-[600px] flex items-center">
  <img src={backgroundImage} alt="" class="absolute inset-0 w-full h-full object-cover" />
  <div class="absolute inset-0 bg-black" style={`opacity: ${overlayOpacity}%`}></div>
  <div class={`relative z-10 container mx-auto px-6 text-white text-${alignment}`}>
    <h1 class="text-5xl font-bold mb-4">{title}</h1>
    {subtitle && <p class="text-xl mb-8">{subtitle}</p>}
    <a href={ctaLink} class="bg-primary text-white px-8 py-4 rounded-lg text-lg font-semibold">
      {ctaText}
    </a>
    {phone && (
      <a href={`tel:${phone}`} class="ml-4 border-2 border-white px-8 py-4 rounded-lg text-lg">
        Call {phone}
      </a>
    )}
  </div>
</section>
```

---

## Customization Points

### Colors (Tailwind Theme)

Each client site has a tailored `tailwind.config.mjs`:

```javascript
export default {
  theme: {
    extend: {
      colors: {
        primary: '#1E40AF',    // Client's brand primary
        secondary: '#9333EA',   // Client's brand secondary
        accent: '#F59E0B',      // Highlight/CTA color
        neutral: {
          50: '#F8FAFC',
          100: '#F1F5F9',
          900: '#0F172A',
        }
      },
      fontFamily: {
        heading: ['Montserrat', 'sans-serif'],
        body: ['Open Sans', 'sans-serif'],
      }
    }
  }
}
```

**Color derivation strategy:**
1. If client provides logo: extract dominant colors using color extraction library
2. If client provides brand guidelines: use specified colors
3. If no brand input: use industry-standard palettes
   - Plumber/HVAC: Blue primary, red accent (trust + urgency)
   - Solar: Green primary, orange accent (eco + energy)
   - Dentist: Teal/cyan primary, white secondary (clean + medical)
   - Lawyer: Navy primary, gold accent (authority + prestige)
   - Landscaper: Green primary, brown secondary (nature + earth)
   - Contractor: Gray/charcoal primary, yellow accent (industrial + safety)

### Typography

Standard font pairings by industry:

| Industry | Heading Font | Body Font |
|----------|-------------|-----------|
| Plumber/HVAC | Montserrat (bold, solid) | Open Sans |
| Solar | Poppins (modern, clean) | Inter |
| Dentist | Nunito (friendly, rounded) | Lato |
| Lawyer | Playfair Display (serif, authoritative) | Source Sans Pro |
| Landscaper | Raleway (natural, elegant) | Roboto |
| Contractor | Oswald (strong, condensed) | Merriweather Sans |

All fonts loaded from Google Fonts with `font-display: swap` for performance.

### Layout Variations

Each template supports 2-3 layout variations for variety across clients in the same industry:

- **Variation A:** Classic layout -- hero image, services below, about, testimonials, contact
- **Variation B:** Video hero, split-screen sections, card-based service display
- **Variation C:** Minimal/modern -- large typography, lots of whitespace, single-column flow

OpenClaw rotates variations to avoid identical-looking sites for competing businesses in the same area.

---

## Content Generation

### AI-Written Copy

OpenClaw (Claude) generates all website copy based on business data collected during enrichment:

**Input data for content generation:**
```json
{
  "business_name": "Smith & Sons Plumbing",
  "city": "Austin",
  "state": "TX",
  "services": ["drain cleaning", "water heater repair", "pipe repair", "sewer line"],
  "years_in_business": 12,
  "employee_count": 8,
  "google_rating": 4.7,
  "google_review_count": 89,
  "owner_name": "John Smith",
  "unique_selling_points": ["family-owned", "24/7 emergency", "free estimates"],
  "service_areas": ["Austin", "Round Rock", "Cedar Park", "Pflugerville"]
}
```

**Content pieces generated:**
1. Homepage hero headline and subheadline
2. About page (company story, mission, values)
3. Individual service page for each service (300-500 words each)
4. FAQ section (8-12 questions with answers)
5. Meta titles and descriptions for every page
6. Alt text for all images
7. Google Business Profile description (if managing GBP)
8. CTA text variations for different sections

**Content quality guidelines:**
- Write at 8th-grade reading level (accessible to all audiences)
- Include city/location naturally in content (local SEO)
- Avoid generic fluff -- every sentence should add value
- Include specific details from business data (years, ratings, service count)
- Match tone to industry (urgent for plumber, warm for dentist, authoritative for lawyer)
- All content must pass AI detection as natural-sounding (avoid obvious AI patterns)

---

## Asset Management

### Stock Photo Library

Maintain a curated library of industry-appropriate stock photos:

**Organization:**
```
assets/
  stock-photos/
    plumber/
      hero/          # 10-15 hero images
      services/      # Photos per service type
      team/          # Generic team/worker photos
      before-after/  # Stock before/after project photos
    solar/
      hero/
      installation/
      residential/
      commercial/
    dentist/
      hero/
      office/
      team/
      procedures/
    lawyer/
      hero/
      office/
      courtroom/
      consultation/
    landscaper/
      hero/
      projects/
      seasonal/
    contractor/
      hero/
      projects/
      tools/
```

**Image sources:**
- Unsplash (free, high-quality, commercial license)
- Pexels (free, commercial license)
- Pixabay (free, commercial license)
- Client-provided photos (preferred when available)

**Image optimization pipeline:**
1. Source image (JPEG/PNG, high resolution)
2. Resize to needed dimensions (hero: 1920x1080, cards: 800x600, thumbnails: 400x300)
3. Convert to WebP (30-50% smaller than JPEG at same quality)
4. Generate responsive srcset (640w, 768w, 1024w, 1280w, 1920w)
5. Create low-quality placeholder for lazy loading (blurred 20px thumbnail)
6. Compress with quality 80-85 (optimal quality/size ratio)

### Icon Sets

Use a consistent icon library across all templates:

- **Primary:** Lucide Icons (open source, consistent style, 1000+ icons)
- **Industry-specific:** Custom SVG icons for services (e.g., pipe wrench for plumbing, solar panel for solar)
- **Social media:** Brand icons from Simple Icons

---

## Quality Assurance Checklist

Every generated site must pass these checks before deployment:

### Performance (Lighthouse)
- [ ] Performance score >= 90
- [ ] First Contentful Paint < 1.5s
- [ ] Largest Contentful Paint < 2.5s
- [ ] Cumulative Layout Shift < 0.1
- [ ] Total Blocking Time < 200ms

### SEO (Lighthouse + Manual)
- [ ] SEO score >= 95
- [ ] Every page has unique meta title (50-60 chars)
- [ ] Every page has unique meta description (150-160 chars)
- [ ] H1 on every page (only one per page)
- [ ] Proper heading hierarchy (H1 > H2 > H3)
- [ ] All images have alt text
- [ ] Sitemap.xml generated and valid
- [ ] Robots.txt properly configured
- [ ] Canonical URLs set on all pages
- [ ] LocalBusiness structured data valid (test via Google's Rich Results Test)

### Accessibility (Lighthouse + Manual)
- [ ] Accessibility score >= 90
- [ ] Color contrast ratio >= 4.5:1 for normal text
- [ ] All interactive elements keyboard-accessible
- [ ] ARIA labels on non-text elements
- [ ] Skip navigation link present
- [ ] Form inputs have labels
- [ ] Focus indicators visible

### Mobile
- [ ] Responsive on all breakpoints (320px, 768px, 1024px, 1280px)
- [ ] Touch targets >= 44x44px
- [ ] No horizontal scroll on mobile
- [ ] Mobile navigation works (hamburger menu, closes on click)
- [ ] Phone numbers are click-to-call on mobile
- [ ] Text readable without zooming (min 16px body text)

### Content
- [ ] Business name spelled correctly throughout
- [ ] Phone number correct and clickable
- [ ] Address correct and linked to Google Maps
- [ ] Email address correct and linked
- [ ] Hours of operation accurate
- [ ] No placeholder content remaining (Lorem ipsum, TODO, etc.)
- [ ] All internal links work (no 404s)
- [ ] Contact form submits successfully

### Legal
- [ ] Privacy policy page included (template with business name)
- [ ] Cookie consent banner (if using analytics)
- [ ] ADA compliance basics met
- [ ] Industry-specific disclaimers included (legal, medical, financial)
- [ ] Copyright notice with correct year and business name

---

## Template Versioning

Templates evolve over time. Use semantic versioning:

- **Major version (2.0.0):** New layout, breaking changes to component API
- **Minor version (1.1.0):** New components, new industry template, non-breaking additions
- **Patch version (1.0.1):** Bug fixes, content corrections, performance improvements

**Existing client sites are not auto-updated to new template versions.** Updates require explicit action to prevent breaking changes on live sites. New sites always use the latest template version.
