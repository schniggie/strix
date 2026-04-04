---
name: crawling_spidering
description: Comprehensive web crawling and spidering for complete attack surface mapping using Katana and browser automation
---

# Crawling and Spidering

Systematic crawling discovers the complete web application structure by following links, parsing JavaScript, and simulating user interactions. This produces a comprehensive sitemap for vulnerability testing.

## Core Objectives

1. **Complete Coverage** - Discover all accessible pages and endpoints
2. **JavaScript Rendering** - Handle SPAs and dynamic content
3. **Form Discovery** - Identify all input points
4. **State Exploration** - Navigate authentication states

## Katana (Primary Crawler)

### Basic Crawling

```bash
# Simple crawl
katana -u https://target.com -o crawl_results.txt

# With depth control
katana -u https://target.com -d 5 -o deep_crawl.txt

# JSON output for parsing
katana -u https://target.com -j -o crawl.json

# Multiple targets
katana -list urls.txt -o multi_crawl.txt
```

### Headless Browser Mode

```bash
# Enable headless browser for JavaScript rendering
katana -u https://target.com -headless -o js_crawl.txt

# With browser timeout
katana -u https://target.com -headless -timeout 30 -o crawl.txt

# Crawl SPAs (React, Angular, Vue)
katana -u https://target.com -headless -js-crawl -o spa_crawl.txt

# Capture AJAX/XHR requests
katana -u https://target.com -headless -xhr-extraction -o xhr_endpoints.txt
```

### Advanced Options

```bash
# Scope control - stay within domain
katana -u https://target.com -fs dn -o scoped_crawl.txt

# Include subdomains
katana -u https://target.com -fs rdn -o subdomain_crawl.txt

# Custom headers
katana -u https://target.com -H "Authorization: Bearer TOKEN" -o auth_crawl.txt

# Cookie-based auth
katana -u https://target.com -H "Cookie: session=abc123" -o cookie_crawl.txt

# Rate limiting
katana -u https://target.com -rl 100 -o rate_limited.txt

# Concurrent requests
katana -u https://target.com -c 20 -o concurrent.txt

# Timeout per request
katana -u https://target.com -timeout 15 -o crawl.txt
```

### Field Extraction

```bash
# Extract specific fields
katana -u https://target.com -f url,path,fqdn -o fields.txt

# Available fields: url, path, fqdn, rdn, rurl, qurl, qpath, file, key, value, kv, dir, udir

# Extract URLs with parameters
katana -u https://target.com -f qurl -o param_urls.txt

# Extract unique directories
katana -u https://target.com -f udir -o directories.txt

# Extract form data
katana -u https://target.com -f kv -o form_params.txt
```

### Output Filtering

```bash
# Filter by extension
katana -u https://target.com -ef png,jpg,gif,css,woff,svg -o no_static.txt

# Match specific extensions only
katana -u https://target.com -em php,asp,aspx,jsp,json -o code_files.txt

# Filter by content type
katana -u https://target.com -ct application/json -o json_endpoints.txt
```

## GoSpider (Alternative Crawler)

```bash
# Basic crawl
gospider -s https://target.com -d 3 -o gospider_output

# With JavaScript parsing
gospider -s https://target.com --js -d 3 -o js_output

# Include subdomains
gospider -s https://target.com --subs -d 2 -o subs_crawl

# Concurrent crawling
gospider -s https://target.com -c 10 -t 5 -o concurrent_crawl

# Output to file
gospider -s https://target.com -d 3 -o - | tee crawl.txt
```

## Browser-Based Crawling

### Authenticated Crawling

```bash
# Use Katana with session
katana -u https://target.com/dashboard \
  -H "Cookie: session=AUTHENTICATED_SESSION_COOKIE" \
  -H "Authorization: Bearer JWT_TOKEN" \
  -headless \
  -d 5 \
  -o auth_crawl.txt

# Login flow with browser tool
# 1. Use browser tool to authenticate
# 2. Extract session cookies
# 3. Use cookies with Katana
```

### Multi-User State Crawling

For comprehensive coverage, crawl in multiple states:

1. **Unauthenticated** - Guest/public access
2. **Low privilege** - Regular user account
3. **High privilege** - Admin/staff account
4. **Different roles** - Each role may see different endpoints

```bash
# Unauthenticated crawl
katana -u https://target.com -headless -d 5 -o unauth_crawl.txt

# User crawl
katana -u https://target.com -H "Cookie: user_session=xxx" -headless -d 5 -o user_crawl.txt

# Admin crawl
katana -u https://target.com -H "Cookie: admin_session=yyy" -headless -d 5 -o admin_crawl.txt

# Diff the results to find privilege-specific endpoints
comm -13 <(sort unauth_crawl.txt) <(sort admin_crawl.txt) > admin_only.txt
```

## Form and Input Discovery

### Form Extraction

```bash
# Extract all forms with Katana
katana -u https://target.com -headless -f url,kv -o forms.txt

# Parse forms from HTML
curl -s https://target.com | grep -oP '<form[^>]*action="[^"]*"'

# Extract input fields
curl -s https://target.com | grep -oP 'name="[^"]*"' | sort -u
```

### Input Point Mapping

Track all user input points:

| Input Type | Location | Discovery Method |
|------------|----------|------------------|
| URL parameters | Query string | Katana `-f qurl` |
| Form fields | POST body | Form extraction |
| Headers | HTTP headers | Manual + fuzzing |
| Cookies | Cookie values | Browser inspection |
| Path segments | URL path | Katana `-f path` |
| JSON body | API requests | XHR extraction |
| File uploads | Multipart forms | Form analysis |

## API Endpoint Extraction

### From JavaScript

```bash
# Extract endpoints from JS files during crawl
katana -u https://target.com -headless -js-crawl -f url | grep "/api" > api_endpoints.txt

# LinkFinder integration
katana -u https://target.com -f url | grep "\.js$" | while read js; do
  linkfinder -i "$js" -o cli 2>/dev/null
done | sort -u > js_api_endpoints.txt
```

### XHR/Fetch Capture

```bash
# Capture dynamic API calls
katana -u https://target.com -headless -xhr-extraction -j | \
  jq -r '.endpoint' | sort -u > dynamic_apis.txt
```

## Sitemap Building

### Structured Output

```bash
# Generate comprehensive sitemap
katana -u https://target.com -headless -d 10 -j -o full_crawl.json

# Process into structured format
cat full_crawl.json | jq -s '{
  base_url: "https://target.com",
  pages: [.[].endpoint] | unique,
  parameters: [.[].parameters // empty] | flatten | unique,
  forms: [.[] | select(.method != null)]
}' > sitemap.json
```

### Hierarchical Map

```
target.com/
├── / (homepage)
├── /login (auth)
├── /register (auth)
├── /dashboard/ (authenticated)
│   ├── /profile
│   ├── /settings
│   └── /api/
│       ├── /users
│       ├── /orders
│       └── /admin/ (admin only)
├── /api/
│   ├── /v1/
│   └── /v2/
└── /static/ (excluded)
```

## Crawl Optimization

### Performance Tuning

```bash
# Aggressive crawling (faster, more resource intensive)
katana -u https://target.com \
  -headless \
  -c 50 \
  -rl 200 \
  -d 10 \
  -timeout 10 \
  -o aggressive_crawl.txt

# Gentle crawling (slower, avoids rate limits)
katana -u https://target.com \
  -headless \
  -c 5 \
  -rl 20 \
  -d 5 \
  -timeout 30 \
  -delay 1 \
  -o gentle_crawl.txt
```

### Filtering Noise

```bash
# Exclude static assets and tracking
katana -u https://target.com \
  -ef png,jpg,jpeg,gif,svg,ico,css,woff,woff2,ttf,eot \
  -ef js \  # Optionally exclude JS files themselves (keep endpoints)
  -deny "analytics|tracking|cdn|static" \
  -o clean_crawl.txt
```

## Output for Task Generation

```json
{
  "crawl_summary": {
    "target": "https://target.com",
    "total_urls": 547,
    "unique_endpoints": 89,
    "forms_found": 12,
    "api_endpoints": 34
  },
  "authentication_states": {
    "unauthenticated": 45,
    "user_role": 67,
    "admin_role": 89
  },
  "endpoints": [
    {
      "url": "https://target.com/api/v1/users/{id}",
      "method": "GET",
      "parameters": ["id"],
      "auth_required": true,
      "discovered_via": "xhr_extraction",
      "tasks": ["idor_test", "auth_bypass"]
    },
    {
      "url": "https://target.com/search",
      "method": "GET",
      "parameters": ["q", "page", "sort"],
      "auth_required": false,
      "discovered_via": "form_crawl",
      "tasks": ["sqli_test", "xss_test"]
    }
  ],
  "forms": [
    {
      "action": "/login",
      "method": "POST",
      "fields": ["username", "password", "remember"],
      "tasks": ["auth_brute", "sqli_test", "csrf_test"]
    }
  ],
  "admin_only_endpoints": [
    "/admin/users",
    "/admin/settings",
    "/api/admin/export"
  ]
}
```

## Task Generation Triggers

| Crawl Finding | Generated Tasks |
|---------------|-----------------|
| Login form | Auth testing, brute force, SQLi, CSRF |
| Search form | SQLi, XSS, parameter pollution |
| File upload | Unrestricted upload, path traversal |
| User profile | IDOR, XSS, CSRF |
| API endpoint | Auth bypass, IDOR, injection |
| Admin-only URL | Privilege escalation, IDOR |
| Password reset | Token weakness, email enumeration |
| Multi-step form | Business logic, race conditions |
| Export/download | IDOR, path traversal |
| Webhook config | SSRF |

## Pro Tips

1. **Multiple states** - Crawl as different users to find all endpoints
2. **JavaScript rendering** - Always use headless mode for modern SPAs
3. **XHR capture** - Many APIs are only called dynamically
4. **Depth tuning** - Start shallow, increase depth for important areas
5. **Delta crawling** - Compare authenticated vs unauthenticated results
6. **Form analysis** - Every form is a potential injection point
7. **Scope awareness** - Configure crawl to stay in scope
8. **Rate respect** - Avoid overwhelming target; use delays

## Validation Checklist

- [ ] Unauthenticated crawl completed
- [ ] Authenticated crawl(s) completed for each role
- [ ] Headless mode used for JavaScript rendering
- [ ] XHR/dynamic requests captured
- [ ] Forms extracted and documented
- [ ] API endpoints identified
- [ ] Static assets filtered out
- [ ] Results compared across auth states
- [ ] Sitemap structured for task generation
