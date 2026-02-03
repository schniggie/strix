---
name: web_content_discovery
description: Directory enumeration, endpoint discovery, and hidden content mapping for web applications
---

# Web Content Discovery

Systematic discovery of web application content including directories, files, endpoints, and hidden resources. This identifies the attack surface for vulnerability testing.

## Core Objectives

1. **Directory Enumeration** - Find all accessible paths
2. **File Discovery** - Locate sensitive files and backups
3. **Endpoint Mapping** - Identify API endpoints and parameters
4. **Hidden Content** - Uncover unlisted/forgotten resources

## Directory Brute Force

### FFuf (Fastest)

```bash
# Basic directory discovery
ffuf -u https://target.com/FUZZ -w /path/to/wordlist.txt -o results.json

# With extensions
ffuf -u https://target.com/FUZZ -w wordlist.txt -e .php,.asp,.aspx,.jsp,.html,.js,.json

# Filter by status code
ffuf -u https://target.com/FUZZ -w wordlist.txt -mc 200,301,302,401,403

# Filter by response size
ffuf -u https://target.com/FUZZ -w wordlist.txt -fs 1234

# Filter by words/lines
ffuf -u https://target.com/FUZZ -w wordlist.txt -fw 10 -fl 5

# Recursive discovery
ffuf -u https://target.com/FUZZ -w wordlist.txt -recursion -recursion-depth 2

# With cookies/auth
ffuf -u https://target.com/FUZZ -w wordlist.txt -H "Cookie: session=abc123"

# Rate limiting
ffuf -u https://target.com/FUZZ -w wordlist.txt -rate 100
```

### Dirsearch

```bash
# Basic scan
dirsearch -u https://target.com -o results.txt

# With extensions
dirsearch -u https://target.com -e php,asp,aspx,jsp,html,js

# Recursive
dirsearch -u https://target.com -r -R 3

# Multiple targets
dirsearch -l urls.txt -e php,html -o results.txt

# With authentication
dirsearch -u https://target.com --header "Authorization: Bearer TOKEN"
```

## Wordlist Selection

### Purpose-Built Wordlists

| Wordlist | Purpose | Size |
|----------|---------|------|
| `raft-medium-directories.txt` | General directories | ~30k |
| `raft-medium-files.txt` | Common files | ~17k |
| `directory-list-2.3-medium.txt` | Comprehensive dirs | ~220k |
| `common-api-endpoints.txt` | API paths | ~3k |
| `quickhits.txt` | Fast initial scan | ~2.5k |

### Recommended Paths

```
/path/to/SecLists/Discovery/Web-Content/
├── raft-medium-directories.txt
├── raft-medium-files.txt
├── directory-list-2.3-medium.txt
├── common.txt
├── quickhits.txt
├── api/
│   └── api-endpoints.txt
└── CGIs.txt
```

### Custom Wordlist Generation

```bash
# Combine multiple wordlists
cat wordlist1.txt wordlist2.txt | sort -u > combined.txt

# Generate variations
for word in $(cat base.txt); do
  echo $word
  echo ${word}s
  echo ${word}-api
  echo v1/${word}
  echo api/${word}
done | sort -u > variations.txt
```

## Sensitive File Discovery

### Backup Files

```bash
# Common backup patterns
ffuf -u https://target.com/FUZZ -w - << 'EOF'
.git/config
.git/HEAD
.svn/entries
.env
.env.local
.env.production
.env.backup
config.php.bak
config.php.old
config.php~
web.config.bak
database.yml.bak
settings.py.bak
backup.sql
dump.sql
database.sql
backup.zip
backup.tar.gz
www.zip
site.zip
EOF

# Append common extensions to discovered files
ffuf -u https://target.com/discovered_fileFUZZ -w - << 'EOF'
.bak
.old
.orig
.save
.swp
~
.copy
.backup
EOF
```

### Configuration Files

```bash
# Framework configs
ffuf -u https://target.com/FUZZ -w - << 'EOF'
wp-config.php
configuration.php
config.php
settings.php
database.php
db.php
connect.php
conn.php
application.properties
application.yml
appsettings.json
web.config
.htaccess
.htpasswd
robots.txt
sitemap.xml
crossdomain.xml
clientaccesspolicy.xml
EOF
```

### Version Control Leaks

```bash
# Git repository extraction
# Check if .git is exposed
curl -s https://target.com/.git/config

# Tools for git extraction
git-dumper https://target.com/.git/ output_dir/
gittools.py dumper https://target.com/.git/ output_dir/

# SVN
curl -s https://target.com/.svn/entries
svn-extractor.py --url https://target.com/.svn/
```

## API Endpoint Discovery

### Common API Patterns

```bash
# RESTful patterns
ffuf -u https://target.com/api/FUZZ -w api-wordlist.txt

# Version patterns
for v in v1 v2 v3 api api/v1 api/v2; do
  ffuf -u https://target.com/$v/FUZZ -w api-wordlist.txt -o ${v//\//_}.json
done

# GraphQL endpoints
ffuf -u https://target.com/FUZZ -w - << 'EOF'
graphql
graphiql
graphql/console
graphql/playground
/api/graphql
/v1/graphql
EOF
```

### Parameter Discovery (Arjun)

```bash
# Find hidden parameters
arjun -u https://target.com/endpoint -oJ params.json

# With custom wordlist
arjun -u https://target.com/endpoint -w params.txt

# Multiple URLs
arjun -i urls.txt -oJ all_params.json

# POST parameters
arjun -u https://target.com/endpoint -m POST
```

## JavaScript Analysis

### Extracting Endpoints from JS

```bash
# Find JS files
gospider -s https://target.com -d 2 --js | grep "\.js" | sort -u > js_files.txt

# Extract URLs from JS
for js in $(cat js_files.txt); do
  curl -s "$js" | grep -oE "(https?://[^\"\\'> ]+|/[a-zA-Z0-9_/\-\.]+)" | sort -u
done > js_endpoints.txt

# LinkFinder for API endpoints in JS
linkfinder -i https://target.com/app.js -o cli

# Bulk JS analysis
cat js_files.txt | while read js; do
  linkfinder -i "$js" -o cli 2>/dev/null
done | sort -u > api_from_js.txt
```

### JS-Snooper Analysis

```bash
# Analyze bundled JS for secrets and endpoints
js-snooper -u https://target.com/main.js

# Extract hardcoded secrets
grep -E "(api[_-]?key|secret|password|token|auth)" js_files/*.js
```

## Wayback Machine Mining

```bash
# Get historical URLs
waybackurls target.com > wayback_urls.txt

# Filter for interesting patterns
cat wayback_urls.txt | grep -E "\.(php|asp|aspx|jsp|json|xml|config|bak|old|sql)" > interesting_wayback.txt

# Check if old endpoints still exist
cat wayback_urls.txt | httpx -silent -mc 200 > live_wayback.txt
```

## Virtual Host Discovery

```bash
# Fuzz for vhosts
ffuf -u http://target.com -H "Host: FUZZ.target.com" -w subdomains.txt -fs 0

# With custom filter
ffuf -u http://IP -H "Host: FUZZ.target.com" -w wordlist.txt -mc 200 -fw 1234

# Common vhost patterns
for env in dev staging test uat qa admin api; do
  curl -s -o /dev/null -w "%{http_code} %{size_download}" -H "Host: $env.target.com" http://TARGET
done
```

## Combining Results

### Deduplication and Normalization

```bash
# Combine all discovered paths
cat dir_results.txt api_results.txt js_endpoints.txt wayback_urls.txt | \
  sort -u | \
  grep -v "^#" | \
  grep -v "^$" > all_endpoints.txt

# Normalize URLs
cat all_endpoints.txt | \
  sed 's/\?.*//' | \
  sort -u > normalized_endpoints.txt
```

### Output for Task Generation

```json
{
  "host": "target.com",
  "endpoints": [
    {
      "path": "/api/v1/users",
      "methods": ["GET", "POST"],
      "parameters": ["id", "name", "email"],
      "auth_required": true,
      "tasks": ["idor_test", "sqli_test", "mass_assignment"]
    },
    {
      "path": "/admin/login",
      "methods": ["GET", "POST"],
      "parameters": ["username", "password"],
      "auth_required": false,
      "tasks": ["auth_bypass", "brute_force", "sqli_test"]
    }
  ],
  "files": [
    {
      "path": "/.env",
      "type": "config",
      "status": 403,
      "tasks": ["config_exposure"]
    }
  ],
  "js_files": [
    {
      "path": "/static/app.js",
      "extracted_endpoints": 15,
      "tasks": ["js_analysis", "secret_detection"]
    }
  ]
}
```

## Task Generation Triggers

| Discovery | Task Type |
|-----------|-----------|
| Login page | Auth testing, brute force, SQLi |
| API endpoint | IDOR, injection, auth bypass |
| File upload | Unrestricted upload, RCE |
| Admin panel | Default creds, auth bypass |
| GraphQL endpoint | Introspection, query abuse |
| Backup file | Sensitive data exposure |
| .git exposed | Source code analysis |
| Config file | Credential extraction |
| User profile | IDOR, XSS, CSRF |
| Search function | SQLi, XSS |
| Password reset | Logic flaws, token weakness |

## Pro Tips

1. **Layer wordlists** - Start small, expand based on findings
2. **Technology-specific** - Use framework-aware wordlists (WordPress, Django, etc.)
3. **Response analysis** - Different error pages reveal valid vs invalid paths
4. **Extension fuzzing** - Same path with different extensions (.php, .bak, .json)
5. **Case sensitivity** - Test /Admin vs /admin vs /ADMIN
6. **URL encoding** - Try %2e%2e%2f for ../
7. **Combine sources** - Merge automated results with JS analysis and Wayback
8. **Track history** - Compare scans over time for new content

## Validation Checklist

- [ ] Multiple wordlists used (quick, medium, large)
- [ ] Common backup extensions tested
- [ ] Version control directories checked (.git, .svn)
- [ ] Configuration files enumerated
- [ ] API endpoints discovered and documented
- [ ] JavaScript files analyzed for endpoints
- [ ] Wayback Machine queried
- [ ] Parameters discovered for endpoints
- [ ] Results normalized and deduplicated
- [ ] Tasks generated from discoveries
