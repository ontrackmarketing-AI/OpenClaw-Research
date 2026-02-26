# WordPress REST API Integration

## Overview

The WordPress REST API provides a standardized HTTP interface for interacting with WordPress sites programmatically. For Steven's SW Recovery Services site, this enables automated content publishing, media management, and integration with our n8n content pipeline. WordPress admin access is provided in Phase 2, and the REST API will be the primary interface for all automated content operations.

Key capabilities relevant to our build:
- **Post creation and scheduling** -- publish blog posts from the content pipeline automatically
- **Media upload** -- programmatic image/video uploads for blog posts and landing pages
- **Taxonomy management** -- assign categories and tags to maintain SEO structure
- **Featured images** -- set hero images on posts for consistent visual branding
- **Custom post types** -- extend WordPress for case studies, testimonials, or service pages

The API is available at `https://{site-domain}/wp-json/wp/v2/` and follows RESTful conventions using standard HTTP methods (GET, POST, PUT, DELETE).

---

## API/Integration Details

### Authentication Methods

#### 1. Application Passwords (Recommended for Server-to-Server)

WordPress 5.6+ includes built-in Application Passwords. This is the simplest method for n8n or backend service authentication.

**Setup:**
1. Navigate to Users > Profile in WordPress admin
2. Scroll to "Application Passwords" section
3. Enter a name (e.g., "n8n-content-pipeline") and click "Add New Application Password"
4. Store the generated password securely (shown only once)

**Usage:**
```bash
# Base64 encode "username:application_password"
curl -X POST https://site.com/wp-json/wp/v2/posts \
  -H "Authorization: Basic dXNlcm5hbWU6YXBwX3Bhc3N3b3Jk" \
  -H "Content-Type: application/json" \
  -d '{"title":"New Post","content":"Post content","status":"publish"}'
```

**Security notes:**
- Application passwords ONLY work via REST API, not for wp-admin login
- Each integration should have its own application password for audit trails
- Revoke unused passwords promptly
- HTTPS is mandatory (application passwords are blocked on non-SSL sites by default)

#### 2. OAuth 2.0 (For Third-Party / User-Facing Apps)

Required when acting on behalf of different WordPress.com or Jetpack-connected users. Supports Authorization Code, Implicit, Client Credentials, and Password Grant flows.

**When to use:** Only if we build a multi-tenant tool or user-facing app that connects to WordPress. For Steven's single-site integration, Application Passwords are sufficient.

#### 3. JWT Authentication (Plugin-Based)

Requires installing the `JWT Authentication for WP REST API` plugin. Useful for SPAs or mobile apps that need stateless token-based auth.

**When to use:** Only if building a React/Vue frontend that authenticates against WordPress directly.

### Core Endpoints

#### Posts (`/wp/v2/posts`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/wp/v2/posts` | List posts (supports filtering, pagination) |
| GET | `/wp/v2/posts/{id}` | Retrieve a single post |
| POST | `/wp/v2/posts` | Create a new post |
| PUT | `/wp/v2/posts/{id}` | Update an existing post |
| DELETE | `/wp/v2/posts/{id}` | Delete a post (moves to trash by default) |

**Create a post with scheduling:**
```json
POST /wp/v2/posts
{
  "title": "5 Signs You Need Debt Recovery Help",
  "content": "<p>Full HTML content here...</p>",
  "status": "future",
  "date": "2026-03-01T09:00:00",
  "categories": [12, 15],
  "tags": [8, 22, 31],
  "featured_media": 456,
  "excerpt": "Short description for SEO...",
  "slug": "signs-you-need-debt-recovery-help",
  "meta": {
    "_yoast_wpseo_metadesc": "Custom meta description for SEO"
  }
}
```

**Post status values:**
- `publish` -- immediately visible
- `future` -- scheduled for the `date` field value
- `draft` -- saved but not visible
- `pending` -- awaiting editorial review
- `private` -- visible only to authenticated users

#### Media (`/wp/v2/media`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/wp/v2/media` | List media items |
| POST | `/wp/v2/media` | Upload new media |
| PUT | `/wp/v2/media/{id}` | Update media metadata |
| DELETE | `/wp/v2/media/{id}` | Delete media item |

**Upload an image:**
```bash
curl -X POST https://site.com/wp-json/wp/v2/media \
  -H "Authorization: Basic {base64_credentials}" \
  -H "Content-Disposition: attachment; filename=hero-image.jpg" \
  -H "Content-Type: image/jpeg" \
  --data-binary @hero-image.jpg
```

**Response includes:**
```json
{
  "id": 456,
  "source_url": "https://site.com/wp-content/uploads/2026/02/hero-image.jpg",
  "media_details": {
    "sizes": {
      "thumbnail": { "source_url": "...", "width": 150, "height": 150 },
      "medium": { "source_url": "...", "width": 300, "height": 200 },
      "large": { "source_url": "...", "width": 1024, "height": 683 }
    }
  }
}
```

**Set featured image on a post:**
```json
PUT /wp/v2/posts/123
{
  "featured_media": 456
}
```

#### Categories (`/wp/v2/categories`)

```json
POST /wp/v2/categories
{
  "name": "Debt Recovery Tips",
  "slug": "debt-recovery-tips",
  "description": "Educational content about debt recovery processes",
  "parent": 0
}
```

#### Tags (`/wp/v2/tags`)

```json
POST /wp/v2/tags
{
  "name": "collections",
  "slug": "collections"
}
```

### Custom Post Types

If Steven needs case studies, testimonials, or service-area pages as distinct content types:

1. Register the CPT in the theme's `functions.php` with `'show_in_rest' => true`
2. Optionally set `'rest_base' => 'case-studies'` for a clean URL
3. Access via `/wp/v2/case-studies/`

```php
register_post_type('case_study', [
    'label' => 'Case Studies',
    'public' => true,
    'show_in_rest' => true,
    'rest_base' => 'case-studies',
    'supports' => ['title', 'editor', 'thumbnail', 'excerpt'],
]);
```

### Pagination and Filtering

```
GET /wp/v2/posts?per_page=20&page=2&categories=12&orderby=date&order=desc
GET /wp/v2/posts?search=debt+recovery&status=publish
GET /wp/v2/posts?after=2026-01-01T00:00:00&before=2026-02-01T00:00:00
```

Response headers include:
- `X-WP-Total` -- total number of matching records
- `X-WP-TotalPages` -- total number of pages

---

## Implementation Approach

### Phase 2 Integration Plan

#### Step 1: Authentication Setup
1. Create a dedicated WordPress user with "Editor" role for API operations
2. Generate an Application Password for n8n integration
3. Store credentials in n8n's credential manager (encrypted)
4. Test connectivity with a simple GET request to `/wp/v2/posts`

#### Step 2: Content Pipeline Connection (n8n)
1. **Blog post workflow:**
   - Content generated by AI content pipeline -> review queue in Supabase
   - Approved content triggers n8n webhook
   - n8n uploads featured image via `/wp/v2/media`
   - n8n creates post via `/wp/v2/posts` with `status: "future"` and scheduled date
   - Confirmation logged to Supabase and Slack notification sent

2. **Media management workflow:**
   - AI-generated or stock images processed through image optimization
   - Upload to WordPress media library via API
   - Store WordPress media IDs in Supabase for reuse

3. **Taxonomy sync workflow:**
   - Maintain a canonical list of categories/tags in Supabase
   - Sync to WordPress on changes via `/wp/v2/categories` and `/wp/v2/tags`
   - Map content pipeline tags to WordPress taxonomy IDs

#### Step 3: SEO Integration
1. Install Yoast SEO or Rank Math on WordPress (both expose meta fields via REST API)
2. Set SEO meta title and description via post meta fields:
   ```json
   {
     "meta": {
       "_yoast_wpseo_title": "Custom SEO Title | SW Recovery",
       "_yoast_wpseo_metadesc": "Meta description for search results"
     }
   }
   ```
3. Auto-generate SEO metadata using the content pipeline's AI

#### Step 4: Monitoring and Error Handling
- Log all API responses (success and failure) to Supabase
- Set up n8n error workflow to alert Slack on failed publishes
- Implement retry logic with exponential backoff for transient failures
- Weekly audit: compare Supabase content records against WordPress to detect drift

### Rate Limits and Performance

- WordPress REST API has no built-in rate limit, but hosting providers may impose limits
- Typical shared hosting: 60-120 requests/minute
- Managed WordPress (WP Engine, Kinsta): 300+ requests/minute
- Batch operations: process media uploads sequentially, posts can be parallel
- Cache GET responses where possible (use `If-Modified-Since` headers)

### Security Hardening

- Restrict REST API access by IP if possible (via `.htaccess` or server config)
- Use a dedicated API user with minimum required permissions (Editor, not Administrator)
- Rotate Application Passwords quarterly
- Disable unused REST API endpoints via `rest_endpoints` filter
- Install a WAF plugin (Wordfence or Sucuri) to monitor API abuse

---

## Cost Implications

| Item | Cost | Notes |
|------|------|-------|
| WordPress REST API | Free | Built into WordPress core |
| Application Passwords | Free | Built into WordPress 5.6+ |
| Yoast SEO (Free) | $0/year | REST API meta field support included |
| Yoast SEO Premium | $99/year | Adds redirect manager, internal linking suggestions |
| Rank Math Pro (alternative) | $59/year | More REST API fields out of the box |
| Managed WordPress hosting | $30-75/month | Kinsta, WP Engine, Flywheel -- better API performance |
| n8n (self-hosted) | $0 | Already in the stack |
| n8n Cloud (alternative) | $24-50/month | If not self-hosting |

**Total incremental cost for REST API integration: $0** (assuming WordPress hosting and n8n are already budgeted).

---

## Estimated Build Hours

| Task | Hours | Notes |
|------|-------|-------|
| Authentication setup and testing | 2 | Application password creation, n8n credential config |
| Post creation/scheduling workflow | 4 | n8n workflow with error handling and Supabase logging |
| Media upload workflow | 3 | Image optimization, upload, ID mapping |
| Taxonomy management setup | 2 | Category/tag sync between Supabase and WordPress |
| SEO metadata integration | 3 | Yoast/Rank Math meta field mapping, AI generation |
| Featured image automation | 2 | Link media uploads to posts automatically |
| Error handling and monitoring | 2 | Slack alerts, retry logic, audit workflow |
| Testing and QA | 2 | End-to-end pipeline test with staging site |
| **Total** | **20** | |

**Dependencies:** WordPress admin access (Phase 2), n8n instance running, content pipeline producing approved content, Supabase schema for content tracking.
