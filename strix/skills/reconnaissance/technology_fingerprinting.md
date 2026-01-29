---
name: technology_fingerprinting
description: Technology stack identification, framework detection, and version fingerprinting for targeted vulnerability testing
---

# Technology Fingerprinting

Identifying the technology stack enables targeted vulnerability testing. Each framework, library, and service has known weaknesses that can be exploited with specific techniques.

## Core Objectives

1. **Framework Detection** - Identify web frameworks (Django, Rails, Express, etc.)
2. **Version Identification** - Determine specific versions for CVE matching
3. **Component Mapping** - Catalog all technologies in use
4. **Vulnerability Correlation** - Map technologies to known vulnerabilities

## Automated Detection

### httpx (Primary Tool)

```bash
# Basic tech detection
cat hosts.txt | httpx -tech-detect -o tech_results.txt

# Detailed output with headers
cat hosts.txt | httpx -tech-detect -title -status-code -content-length -o detailed.txt

# JSON output for parsing
cat hosts.txt | httpx -tech-detect -json -o tech.json

# Include response headers
cat hosts.txt | httpx -tech-detect -include-response-header -json -o full_tech.json
```

### Wappalyzer-Based Detection

```bash
# Using webanalyze (Go implementation of Wappalyzer)
webanalyze -host https://target.com -crawl 2

# CLI wappalyzer
wappalyzer https://target.com

# Bulk analysis
cat urls.txt | while read url; do
  webanalyze -host "$url" -output json
done > tech_analysis.json
```

### Nuclei Technology Detection

```bash
# Run tech detection templates
nuclei -u https://target.com -t technologies/ -o tech_nuclei.txt

# Specific technology checks
nuclei -u https://target.com -t technologies/tech-detect.yaml
nuclei -u https://target.com -t technologies/wordpress-detect.yaml
```

## Manual Fingerprinting

### HTTP Headers Analysis

```bash
# Capture and analyze headers
curl -sI https://target.com | tee headers.txt

# Key headers to examine:
# Server: nginx/1.19.0
# X-Powered-By: PHP/7.4.3
# X-AspNet-Version: 4.0.30319
# X-Generator: Drupal 8
# Set-Cookie: JSESSIONID=xxx (Java)
# Set-Cookie: ASP.NET_SessionId=xxx (.NET)
```

### Response Body Patterns

| Pattern | Technology |
|---------|------------|
| `wp-content/`, `wp-includes/` | WordPress |
| `/sites/default/files/` | Drupal |
| `Powered by Joomla` | Joomla |
| `csrfmiddlewaretoken` | Django |
| `_csrf_token` | Rails/Phoenix |
| `__VIEWSTATE` | ASP.NET |
| `__RequestVerificationToken` | ASP.NET MVC |
| `laravel_session` | Laravel |
| `connect.sid` | Express.js |

### Cookie Patterns

| Cookie Name | Framework |
|-------------|-----------|
| `PHPSESSID` | PHP |
| `JSESSIONID` | Java |
| `ASP.NET_SessionId` | ASP.NET |
| `_session_id` | Rails |
| `laravel_session` | Laravel |
| `connect.sid` | Express |
| `ci_session` | CodeIgniter |
| `symfony` | Symfony |

### Error Page Fingerprinting

```bash
# Trigger error pages
curl -s https://target.com/nonexistent_page_12345
curl -s https://target.com/test.php
curl -s https://target.com/?id='

# Framework error signatures:
# Django: "DoesNotExist at", "DEBUG = True"
# Rails: "ActionController::RoutingError"
# Laravel: "Whoops!", "Illuminate\\"
# Express: "Cannot GET", "ENOENT"
# Spring: "Whitelabel Error Page"
# ASP.NET: "Server Error in '/' Application"
```

## Framework-Specific Detection

### WordPress

```bash
# Check for WordPress
curl -s https://target.com/wp-login.php
curl -s https://target.com/wp-admin/
curl -s https://target.com/xmlrpc.php

# Version detection
curl -s https://target.com/readme.html | grep -i version
curl -s https://target.com/wp-includes/version.php
curl -s https://target.com | grep "generator.*wordpress"

# Plugin enumeration
wpscan --url https://target.com --enumerate p

# Theme enumeration
wpscan --url https://target.com --enumerate t
```

### Drupal

```bash
# Check for Drupal
curl -s https://target.com/CHANGELOG.txt
curl -s https://target.com/core/CHANGELOG.txt
curl -s https://target.com/user/login

# Version detection
curl -s https://target.com/CHANGELOG.txt | head -10
```

### Joomla

```bash
# Check for Joomla
curl -s https://target.com/administrator/
curl -s https://target.com/configuration.php~
curl -s https://target.com/README.txt

# Version
curl -s https://target.com/administrator/manifests/files/joomla.xml | grep version
```

### JavaScript Frameworks

```bash
# React
curl -s https://target.com | grep -E "react|_reactRoot|__NEXT_DATA__"

# Angular
curl -s https://target.com | grep -E "ng-app|angular\.js|\[ngClass\]"

# Vue.js
curl -s https://target.com | grep -E "vue\.js|v-bind|v-model|__VUE__"

# Next.js
curl -s https://target.com | grep "__NEXT_DATA__"
curl -s https://target.com/_next/static/chunks/

# Nuxt.js
curl -s https://target.com | grep "__NUXT__"
```

## API Technology Detection

### REST API Frameworks

```bash
# Check common API framework patterns
curl -s https://target.com/api/ | head -50

# FastAPI (Python) - auto-docs
curl -s https://target.com/docs
curl -s https://target.com/openapi.json
curl -s https://target.com/redoc

# Swagger/OpenAPI
curl -s https://target.com/swagger.json
curl -s https://target.com/swagger/
curl -s https://target.com/api-docs/

# GraphQL detection
curl -s -X POST https://target.com/graphql -H "Content-Type: application/json" \
  -d '{"query":"{ __typename }"}'
```

### Authentication Services

```bash
# Auth0
curl -s https://target.com | grep "auth0"

# Firebase
curl -s https://target.com | grep "firebase"

# Okta
curl -s https://target.com | grep "okta"

# Cognito
curl -s https://target.com | grep "cognito"
```

## Version Fingerprinting

### CVE Matching

Once versions are identified, match to known vulnerabilities:

```bash
# Search for CVEs
nuclei -u https://target.com -t cves/ -o cve_results.txt

# Version-specific CVE check
# Example: If nginx 1.19.0 detected
searchsploit nginx 1.19

# CVE database query
curl -s "https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=nginx+1.19"
```

### Vulnerable Library Detection

```bash
# Retire.js for JavaScript libraries
retire --js --path /path/to/js/files

# Check JS libraries in browser
# In DevTools Console:
# React.version
# angular.version.full
# jQuery.fn.jquery

# Snyk for dependency vulnerabilities
snyk test
```

## Infrastructure Detection

### Web Servers

```bash
# Server identification
curl -sI https://target.com | grep -i server

# Common servers:
# nginx, Apache, IIS, LiteSpeed, Caddy, Cloudflare

# Version-specific headers
nmap -sV -p 80,443 target.com --script http-server-header
```

### WAF/CDN Detection

```bash
# wafw00f detection
wafw00f https://target.com

# Common WAF signatures in headers:
# X-Sucuri-ID (Sucuri)
# CF-RAY (Cloudflare)
# X-Akamai-* (Akamai)
# X-AWS-WAF-* (AWS WAF)
# __cfduid (Cloudflare)
```

### Load Balancer Detection

```bash
# Check for load balancer indicators
# Multiple requests may hit different backend servers
for i in {1..10}; do
  curl -sI https://target.com | grep -E "Server:|X-Backend|X-Served-By"
done | sort | uniq -c
```

## Output Structure

```json
{
  "target": "https://target.com",
  "technologies": {
    "web_server": {
      "name": "nginx",
      "version": "1.19.0",
      "cves": ["CVE-2021-23017"]
    },
    "backend_framework": {
      "name": "Django",
      "version": "3.2",
      "language": "Python",
      "cves": []
    },
    "frontend_framework": {
      "name": "React",
      "version": "17.0.2",
      "cves": []
    },
    "cms": null,
    "database": {
      "name": "PostgreSQL",
      "detected_via": "error_message",
      "version": "unknown"
    },
    "authentication": {
      "service": "Auth0",
      "jwt_used": true
    },
    "waf": {
      "name": "Cloudflare",
      "bypass_techniques": ["rate_limit_rotation", "origin_discovery"]
    }
  },
  "task_recommendations": [
    {
      "technology": "Django",
      "tasks": ["csrf_token_analysis", "debug_mode_check", "admin_panel_discovery"]
    },
    {
      "technology": "JWT",
      "tasks": ["jwt_none_algorithm", "jwt_weak_secret", "jwt_confusion"]
    },
    {
      "technology": "PostgreSQL",
      "tasks": ["sqli_postgres_specific", "pg_sleep_timing"]
    }
  ]
}
```

## Technology-Specific Testing Matrix

| Technology | Primary Vulnerabilities | Tools/Techniques |
|------------|------------------------|------------------|
| WordPress | Plugin vulns, SQLi, XSS | WPScan, nuclei WP templates |
| Django | Debug mode, CSRF, SSTI | Django-specific payloads |
| Rails | Mass assignment, SSTI | Brakeman, Rails-specific attacks |
| Laravel | Debug mode, deserialization | Laravel-specific techniques |
| Node.js | Prototype pollution, SSRF | Node-specific payloads |
| PHP | LFI, RCE, type juggling | PHP-specific attacks |
| Java/Spring | Deserialization, SSTI | ysoserial, Spring exploits |
| .NET | ViewState, deserialization | .NET-specific tools |
| GraphQL | Introspection, DoS, auth | GraphQL-specific testing |

## Pro Tips

1. **Multiple methods** - Use automated + manual detection for accuracy
2. **Error triggering** - Intentional errors reveal framework details
3. **Version pinning** - Exact versions enable precise CVE matching
4. **Stack correlation** - Technologies often come in predictable combinations
5. **Default files** - Framework-specific files reveal presence
6. **WAF awareness** - Detection affects testing strategy
7. **Historical data** - Wayback may show old versions/configs
8. **Documentation** - Framework-specific docs pages may be exposed

## Validation Checklist

- [ ] Automated tech detection completed (httpx, Wappalyzer)
- [ ] HTTP headers analyzed for server/framework info
- [ ] Response body patterns checked
- [ ] Cookie names analyzed for framework hints
- [ ] Error pages triggered and analyzed
- [ ] CMS detection and version identification
- [ ] JavaScript framework detection
- [ ] API technology identification
- [ ] WAF/CDN detection
- [ ] Technologies mapped to potential vulnerabilities
- [ ] Task recommendations generated based on stack
