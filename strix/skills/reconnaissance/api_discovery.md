---
name: api_discovery
description: API endpoint enumeration, parameter discovery, and documentation extraction for comprehensive API attack surface mapping
---

# API Discovery

Comprehensive API discovery maps all endpoints, parameters, authentication mechanisms, and data structures. APIs are high-value targets with direct access to business logic and data.

## Core Objectives

1. **Endpoint Enumeration** - Find all API routes and methods
2. **Parameter Discovery** - Identify all input parameters
3. **Documentation Mining** - Extract specs from OpenAPI/Swagger
4. **Authentication Mapping** - Understand auth mechanisms

## API Documentation Discovery

### OpenAPI/Swagger

```bash
# Common Swagger/OpenAPI paths
for path in /swagger.json /swagger/v1/swagger.json /api-docs /api/swagger.json \
  /openapi.json /v1/openapi.json /v2/openapi.json /v3/openapi.json \
  /swagger-ui/ /swagger-ui.html /api/swagger-ui.html /swagger/index.html \
  /docs /api/docs /redoc /api-docs.json /api/api-docs; do
  curl -sI "https://target.com$path" | grep -q "200 OK" && echo "FOUND: $path"
done

# Swagger UI detection
curl -s https://target.com/swagger-ui/ | grep -i swagger

# Parse OpenAPI spec
curl -s https://target.com/openapi.json | jq '.paths | keys[]'
```

### GraphQL Introspection

```bash
# Check for GraphQL endpoint
for endpoint in /graphql /graphiql /v1/graphql /api/graphql /query; do
  curl -s -X POST "https://target.com$endpoint" \
    -H "Content-Type: application/json" \
    -d '{"query":"{ __typename }"}' | grep -q "data" && echo "GraphQL: $endpoint"
done

# Full introspection query
curl -s -X POST https://target.com/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ __schema { types { name fields { name type { name } } } } }"}' \
  | jq '.' > graphql_schema.json

# Extract all queries/mutations
cat graphql_schema.json | jq '.data.__schema.types[] | select(.name == "Query" or .name == "Mutation") | .fields[].name'
```

### WADL/WSDL (Legacy APIs)

```bash
# WADL discovery
curl -s https://target.com/application.wadl
curl -s https://target.com/api/application.wadl

# WSDL discovery (SOAP)
curl -s "https://target.com/service?wsdl"
curl -s "https://target.com/ws/service.wsdl"
```

## Endpoint Enumeration

### Brute Force Discovery

```bash
# ffuf API endpoint discovery
ffuf -u https://target.com/api/FUZZ -w /path/to/api-wordlist.txt -mc 200,201,204,301,302,401,403,405

# Version variations
for v in "" v1 v2 v3 api api/v1 api/v2; do
  ffuf -u "https://target.com/$v/FUZZ" -w api-wordlist.txt -mc 200,201,204,401,403 -o "${v:-root}.json"
done

# Method testing
ffuf -u https://target.com/api/users -X FUZZ -w methods.txt -mc all
# methods.txt: GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD
```

### JavaScript Mining

```bash
# Extract API endpoints from JS files
katana -u https://target.com -headless -js-crawl | grep -E "/api/|/v[0-9]/" > js_apis.txt

# LinkFinder for detailed extraction
linkfinder -i https://target.com/main.js -o cli | grep -E "^/" > api_paths.txt

# Regex for API patterns
curl -s https://target.com/bundle.js | grep -oE '["'"'"'][/][a-zA-Z0-9_/-]+["'"'"']' | tr -d '"'"'" | sort -u
```

### Proxy Traffic Analysis

```bash
# Use proxy tool to capture API calls during browsing
# Then extract unique endpoints from proxy history

# Python script to parse proxy output
python3 << 'EOF'
import json
# Parse proxy export and extract unique API endpoints
# Group by base path, identify parameters
EOF
```

## Parameter Discovery

### Arjun (Primary Tool)

```bash
# Discover hidden parameters
arjun -u https://target.com/api/users -oJ users_params.json

# POST parameters
arjun -u https://target.com/api/login -m POST -oJ login_params.json

# JSON body parameters
arjun -u https://target.com/api/users -m JSON -oJ json_params.json

# Custom wordlist
arjun -u https://target.com/api/users -w custom_params.txt

# With authentication
arjun -u https://target.com/api/users -H "Authorization: Bearer TOKEN"

# Multiple URLs
arjun -i api_endpoints.txt -oJ all_params.json
```

### Parameter Fuzzing

```bash
# Fuzz for parameter names
ffuf -u "https://target.com/api/users?FUZZ=test" -w params.txt -mc 200 -fs 0

# Fuzz parameter values
ffuf -u "https://target.com/api/users?id=FUZZ" -w numbers.txt -mc 200

# JSON body fuzzing
ffuf -u https://target.com/api/users -X POST \
  -H "Content-Type: application/json" \
  -d '{"FUZZ":"test"}' \
  -w params.txt -mc 200,201
```

### Common Parameter Patterns

| Category | Parameters |
|----------|------------|
| Pagination | page, limit, offset, per_page, skip, take, cursor, after, before |
| Sorting | sort, order, orderby, sort_by, direction, asc, desc |
| Filtering | filter, q, query, search, where, status, type, category |
| Selection | fields, include, exclude, select, expand, embed, projection |
| Auth | token, api_key, key, auth, access_token, session |
| IDs | id, user_id, account_id, org_id, project_id, item_id |
| Debug | debug, test, verbose, dev, trace |

## Authentication Analysis

### Auth Mechanism Detection

```bash
# Check for auth headers
curl -sI https://target.com/api/users | grep -iE "www-authenticate|authorization"

# Test without auth
curl -s https://target.com/api/users
curl -s https://target.com/api/admin/users

# JWT detection
curl -s https://target.com/api/users -H "Authorization: Bearer INVALID" 2>&1 | grep -i jwt
```

### Auth Types to Document

| Type | Indicators | Testing Approach |
|------|------------|------------------|
| Bearer Token | `Authorization: Bearer xxx` | Token analysis, expiry, scope |
| API Key | `X-API-Key: xxx` or URL param | Key rotation, scope, leakage |
| Basic Auth | `Authorization: Basic xxx` | Brute force, default creds |
| OAuth2 | `/oauth/token`, redirect_uri | CSRF, open redirect, scope |
| JWT | `eyJ...` tokens | Algorithm confusion, weak secret |
| Session Cookie | `Cookie: session=xxx` | Fixation, hijacking |

### Auth Bypass Attempts

```bash
# Try different auth header formats
curl -s https://target.com/api/admin -H "Authorization: Bearer null"
curl -s https://target.com/api/admin -H "Authorization: Bearer undefined"
curl -s https://target.com/api/admin -H "Authorization: Bearer {}"
curl -s https://target.com/api/admin -H "X-Original-URL: /api/admin"
curl -s https://target.com/api/admin -H "X-Rewrite-URL: /api/admin"

# Path traversal in API
curl -s https://target.com/api/user/../admin
curl -s https://target.com/api/v1/user/../../admin
```

## HTTP Method Analysis

### Method Enumeration

```bash
# OPTIONS request
curl -sI -X OPTIONS https://target.com/api/users | grep -i allow

# Test all methods on endpoint
for method in GET POST PUT DELETE PATCH HEAD OPTIONS TRACE; do
  code=$(curl -s -o /dev/null -w "%{http_code}" -X $method https://target.com/api/users)
  echo "$method: $code"
done
```

### Method Override

```bash
# X-HTTP-Method-Override
curl -s -X POST https://target.com/api/users/1 -H "X-HTTP-Method-Override: DELETE"

# Query parameter override
curl -s -X POST "https://target.com/api/users/1?_method=DELETE"

# Content-Type method override
curl -s -X POST https://target.com/api/users/1 -d "_method=DELETE"
```

## Content-Type Testing

```bash
# Test different content types
for ct in "application/json" "application/xml" "application/x-www-form-urlencoded" "multipart/form-data"; do
  curl -s -X POST https://target.com/api/users \
    -H "Content-Type: $ct" \
    -d '{"test":"data"}' | head -1
done

# JSON to XML conversion attacks
curl -s -X POST https://target.com/api/users \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0"?><user><name>test</name></user>'
```

## API Versioning Analysis

```bash
# Discover all versions
for v in 1 2 3 4 5; do
  for format in "v$v" "api/v$v" "v$v/api"; do
    curl -sI "https://target.com/$format/users" | grep -q "200\|401\|403" && echo "Found: /$format"
  done
done

# Header-based versioning
curl -s https://target.com/api/users -H "Accept-Version: 1.0"
curl -s https://target.com/api/users -H "API-Version: 2"
curl -s https://target.com/api/users -H "Accept: application/vnd.api.v1+json"
```

## Rate Limit Analysis

```bash
# Check rate limit headers
curl -sI https://target.com/api/users | grep -iE "rate|limit|remaining|retry"

# Common rate limit headers:
# X-RateLimit-Limit
# X-RateLimit-Remaining
# X-RateLimit-Reset
# Retry-After
```

## Output Format

```json
{
  "api_summary": {
    "base_url": "https://target.com/api/v1",
    "auth_type": "Bearer JWT",
    "total_endpoints": 47,
    "documentation_exposed": true,
    "graphql": false
  },
  "endpoints": [
    {
      "path": "/users",
      "methods": ["GET", "POST"],
      "auth_required": true,
      "parameters": {
        "query": ["page", "limit", "search"],
        "body": ["name", "email", "role"]
      },
      "response_type": "application/json",
      "tasks": ["idor_test", "mass_assignment", "sqli_search"]
    },
    {
      "path": "/users/{id}",
      "methods": ["GET", "PUT", "DELETE"],
      "auth_required": true,
      "parameters": {
        "path": ["id"],
        "body": ["name", "email", "role", "password"]
      },
      "tasks": ["idor_test", "privilege_escalation", "mass_assignment"]
    },
    {
      "path": "/admin/users",
      "methods": ["GET"],
      "auth_required": true,
      "role_required": "admin",
      "tasks": ["auth_bypass", "privilege_escalation"]
    }
  ],
  "authentication": {
    "login_endpoint": "/auth/login",
    "token_type": "JWT",
    "token_location": "Authorization header",
    "refresh_available": true,
    "tasks": ["jwt_analysis", "token_leakage", "refresh_abuse"]
  },
  "rate_limits": {
    "global": "1000/hour",
    "per_endpoint": "100/minute"
  }
}
```

## Task Generation Matrix

| API Finding | Generated Tasks |
|-------------|-----------------|
| CRUD endpoint | IDOR, mass assignment, injection |
| Search endpoint | SQLi, NoSQLi, XSS |
| File upload | Unrestricted upload, path traversal |
| User management | Privilege escalation, account takeover |
| Admin endpoints | Auth bypass, BFLA |
| Webhook config | SSRF, event injection |
| Export/report | IDOR, sensitive data exposure |
| Password reset | Token weakness, user enumeration |
| GraphQL | Introspection abuse, DoS, auth bypass |
| Rate limit found | Bypass testing |

## Pro Tips

1. **Documentation first** - Always check for exposed API docs before brute forcing
2. **Version comparison** - Old API versions may lack security controls
3. **Method matters** - Same endpoint may behave differently per method
4. **Parameter pollution** - Send same param multiple times
5. **Content-type switching** - APIs may accept unexpected formats
6. **Auth header variations** - Try different auth header formats
7. **Mobile API** - Check for separate mobile API endpoints
8. **Error verbosity** - Invalid requests may reveal parameter names

## Validation Checklist

- [ ] API documentation endpoints checked (Swagger, OpenAPI)
- [ ] GraphQL introspection attempted
- [ ] Endpoint brute force completed
- [ ] JavaScript analyzed for API calls
- [ ] Parameters discovered (query, body, header)
- [ ] Authentication mechanism documented
- [ ] All HTTP methods tested per endpoint
- [ ] Content-type variations tested
- [ ] API versions enumerated
- [ ] Rate limits documented
- [ ] Output structured for task generation
