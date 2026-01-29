---
name: task_decomposition
description: Strategic decomposition of reconnaissance findings into targeted, parallelizable penetration testing tasks
---

# Task Decomposition

Transform reconnaissance data into specific, actionable penetration testing tasks. This methodology maximizes coverage by creating focused, parallel workstreams for each attack vector.

## Core Principle: Recon → Decomposition → Parallel Execution

The key insight: effective penetration testing isn't about running one comprehensive scan—it's about **creating dozens of small, specific tasks** from reconnaissance data and executing them in parallel. Each task targets ONE vulnerability type at ONE location.

## Decomposition Strategy

### Input: Reconnaissance Data

From the recon phase, you have:
1. **Asset inventory** - Subdomains, IPs, services
2. **Endpoint map** - URLs, paths, parameters
3. **Technology stack** - Frameworks, versions, components
4. **Authentication flows** - Login, tokens, sessions
5. **API surface** - Endpoints, methods, parameters

### Output: Task Matrix

Create tasks using this formula:

```
TASK = ENDPOINT × VULNERABILITY_TYPE × CONTEXT
```

Example:
- Endpoint: `/api/v1/users/{id}`
- Vulnerability: IDOR
- Context: Authenticated user role
- **Task**: "Test IDOR on /api/v1/users/{id} endpoint using authenticated low-privilege session"

## Task Categories

### 1. Endpoint-Specific Tasks

For EACH discovered endpoint, generate tasks:

| Endpoint Type | Generated Tasks |
|---------------|-----------------|
| Login form | SQLi, brute force, credential stuffing, CSRF, rate limit bypass |
| Search box | SQLi, XSS (reflected), NoSQLi, command injection |
| User profile | IDOR, XSS (stored), CSRF, privilege escalation |
| File upload | Unrestricted upload, path traversal, SSRF, XXE |
| API endpoint | IDOR, mass assignment, injection, auth bypass |
| Admin panel | Auth bypass, default creds, BFLA, privilege escalation |
| Password reset | Token weakness, user enumeration, host header injection |
| Export/download | IDOR, path traversal, SSRF |
| Webhook config | SSRF, event injection |

### 2. Technology-Specific Tasks

Based on detected technologies:

| Technology | Tasks |
|------------|-------|
| WordPress | WPScan, plugin vulns, xmlrpc abuse, user enum |
| Django | Debug mode, SSTI, CSRF token analysis, admin panel |
| Node.js | Prototype pollution, SSRF, deserialization |
| PHP | LFI/RFI, type juggling, deserialization |
| Java/Spring | Deserialization, SpEL injection, Actuator endpoints |
| GraphQL | Introspection, batching abuse, DoS, auth bypass |
| JWT | None algorithm, weak secret, algorithm confusion |
| AWS | S3 bucket permissions, SSRF to metadata, IAM |

### 3. Vulnerability-Specific Tasks

For each vulnerability class, create targeted tasks:

#### Injection Tasks
```
- SQLi on search parameter (/search?q=)
- SQLi on login form (username field)
- SQLi on API filter (/api/users?status=)
- NoSQLi on MongoDB query (/api/data?filter=)
- Command injection on filename parameter
- XSS (reflected) on error messages
- XSS (stored) on user profile fields
- SSTI on template rendering endpoints
```

#### Access Control Tasks
```
- IDOR on user ID parameter (/users/123)
- IDOR on document download (/docs/456/download)
- BFLA on admin endpoint (/admin/users)
- Privilege escalation via role parameter
- JWT claim manipulation
- Session fixation testing
```

#### Logic Tasks
```
- Race condition on payment processing
- Business logic on discount application
- Multi-step process manipulation
- Price manipulation in cart
```

## Task Generation Algorithm

### Step 1: Enumerate Attack Points

From recon data, list every:
- Parameter (query, body, header, path)
- Input field (forms, API bodies)
- File operation (upload, download, include)
- ID reference (user_id, doc_id, org_id)

### Step 2: Map Vulnerabilities to Points

```python
# Pseudocode for task generation
tasks = []

for endpoint in discovered_endpoints:
    for param in endpoint.parameters:
        # Injection testing
        if param.type in ['string', 'search', 'query']:
            tasks.append(f"SQLi test on {endpoint.path} param {param.name}")
            tasks.append(f"XSS test on {endpoint.path} param {param.name}")

        # IDOR testing
        if param.name matches ID_PATTERNS:  # id, user_id, doc_id, etc.
            tasks.append(f"IDOR test on {endpoint.path} param {param.name}")

        # SSRF testing
        if param.name matches URL_PATTERNS:  # url, callback, webhook, redirect
            tasks.append(f"SSRF test on {endpoint.path} param {param.name}")

    # Auth-related tasks
    if endpoint.auth_required:
        tasks.append(f"Auth bypass test on {endpoint.path}")
        tasks.append(f"Token validation test on {endpoint.path}")

    # Method-based tasks
    if 'POST' in endpoint.methods:
        tasks.append(f"CSRF test on {endpoint.path}")
        tasks.append(f"Mass assignment test on {endpoint.path}")
```

### Step 3: Prioritize by Impact

Assign priority scores:

| Factor | Score |
|--------|-------|
| Handles sensitive data (PII, payment) | +10 |
| Admin/privileged endpoint | +8 |
| Authentication-related | +7 |
| File operations | +6 |
| Database operations | +5 |
| User-controllable output | +4 |
| Public endpoint | +2 |

Sort tasks by priority score for execution order.

### Step 4: Group for Parallel Execution

Group tasks that can run concurrently:

```
Parallel Group 1 (Independent endpoints):
├── SQLi test on /search
├── SQLi test on /login
├── SQLi test on /api/users
└── SQLi test on /api/products

Parallel Group 2 (Same vulnerability, different endpoints):
├── IDOR test on /api/users/{id}
├── IDOR test on /api/docs/{id}
├── IDOR test on /api/orders/{id}
└── IDOR test on /api/messages/{id}

Parallel Group 3 (Different vulns, same endpoint):
├── XSS test on /profile
├── CSRF test on /profile
├── Mass assignment on /profile
└── IDOR on /profile/{id}
```

## Task Specification Format

Each task should include:

```json
{
  "task_id": "sqli_search_001",
  "name": "SQL Injection on Search Endpoint",
  "type": "vulnerability_test",
  "priority": 8,
  "target": {
    "endpoint": "/api/v1/products",
    "method": "GET",
    "parameter": "search",
    "location": "query"
  },
  "vulnerability": "sql_injection",
  "context": {
    "auth_required": false,
    "technology": "PostgreSQL",
    "waf_present": true
  },
  "execution": {
    "skills_required": ["sql_injection"],
    "estimated_payloads": 500,
    "technique": "error_based,time_based,boolean_based"
  },
  "success_criteria": "Database error, time delay, or boolean difference observed",
  "validation_required": true
}
```

## Example Decomposition

### Input: Recon Summary

```json
{
  "target": "shop.example.com",
  "endpoints": [
    {"path": "/login", "methods": ["GET", "POST"], "params": ["username", "password"]},
    {"path": "/search", "methods": ["GET"], "params": ["q", "category", "sort"]},
    {"path": "/api/users/{id}", "methods": ["GET", "PUT"], "auth": true},
    {"path": "/api/orders", "methods": ["GET", "POST"], "auth": true},
    {"path": "/api/orders/{id}", "methods": ["GET", "DELETE"], "auth": true},
    {"path": "/profile", "methods": ["GET", "POST"], "auth": true},
    {"path": "/admin/users", "methods": ["GET"], "auth": true, "role": "admin"},
    {"path": "/upload", "methods": ["POST"], "auth": true}
  ],
  "technologies": ["Django", "PostgreSQL", "Redis"],
  "auth_type": "JWT"
}
```

### Output: Task List

```
HIGH PRIORITY (Score 8+):
1. [AUTH] JWT none algorithm attack
2. [AUTH] JWT weak secret brute force
3. [AUTH] Auth bypass on /admin/users
4. [IDOR] Access other user via /api/users/{id}
5. [IDOR] Access other user's orders via /api/orders/{id}
6. [SQLi] SQL injection on /login username
7. [SQLi] SQL injection on /search q parameter
8. [UPLOAD] Unrestricted file upload on /upload

MEDIUM PRIORITY (Score 5-7):
9. [XSS] Stored XSS on /profile
10. [CSRF] CSRF on /profile POST
11. [MASS] Mass assignment on /api/users/{id} PUT
12. [BFLA] Broken function level auth on /admin/users
13. [SQLi] SQL injection on /search category
14. [SQLi] SQL injection on /search sort
15. [IDOR] Order deletion via /api/orders/{id}

STANDARD PRIORITY (Score 3-4):
16. [XSS] Reflected XSS on /search
17. [RATE] Rate limiting on /login
18. [ENUM] User enumeration on /login
19. [CSRF] CSRF on /api/orders POST
20. [PATH] Path traversal on /upload filename

TECHNOLOGY-SPECIFIC:
21. [DJANGO] Debug mode check
22. [DJANGO] SSTI in error messages
23. [DJANGO] Admin panel discovery
24. [REDIS] Redis unauthorized access
25. [PG] PostgreSQL-specific SQLi payloads
```

## Agent Creation from Tasks

Convert tasks to specialized agents:

```python
# Task to Agent mapping
def create_agent_for_task(task):
    return {
        "name": f"{task.vulnerability} Agent - {task.endpoint}",
        "skills": [task.vulnerability],
        "objective": task.description,
        "target": task.target,
        "context": task.context
    }

# Example agents created:
# - "SQLi Agent - /login" with skills: [sql_injection]
# - "IDOR Agent - /api/users" with skills: [idor]
# - "JWT Agent - Authentication" with skills: [authentication_jwt]
# - "XSS Agent - /profile" with skills: [xss]
```

## Execution Strategy

### Phase 1: High-Impact Parallel Sweep
Run all high-priority tasks in parallel:
- Auth bypass attempts
- Critical IDOR tests
- SQLi on auth/search endpoints

### Phase 2: Systematic Coverage
Run medium-priority tasks grouped by:
- Vulnerability type (all XSS, all CSRF, etc.)
- Endpoint (all tests on /profile, etc.)

### Phase 3: Deep Dive
For any promising findings:
- Spawn validation agents
- Attempt exploitation chains
- Document and report

## Decomposition Quality Metrics

Measure effectiveness:
- **Coverage**: % of endpoints with at least one task
- **Depth**: Average tasks per endpoint
- **Specificity**: Tasks targeting specific params vs generic
- **Parallelization**: % of tasks that can run concurrently

Target:
- 100% endpoint coverage
- 5+ tasks per significant endpoint
- 80%+ tasks targeting specific parameters
- 70%+ tasks parallelizable

## Pro Tips

1. **One task = One thing** - Never combine multiple vulnerabilities in one task
2. **Specific > Generic** - "SQLi on /search q param" beats "Test /search for vulns"
3. **Context matters** - Include auth state, technology, WAF info in task
4. **Parallel by default** - Design tasks to be independent
5. **Validation chain** - Every finding task spawns a validation task
6. **Iterate** - New findings generate new tasks (IDOR reveals IDs → more IDOR tasks)
7. **Don't skip basics** - Simple attacks on every endpoint before advanced techniques

## Task Template Library

### Standard Web Application Tasks

```
For each form:
- SQLi on each text input
- XSS on each text input
- CSRF if state-changing
- Rate limiting if auth-related

For each API endpoint:
- IDOR if contains ID
- Auth bypass attempt
- Mass assignment on POST/PUT
- Method confusion

For each file operation:
- Path traversal
- Type validation bypass
- Size limit bypass
- Content validation bypass

For each auth flow:
- Token analysis
- Session management
- Password policy
- Account lockout
```

This systematic decomposition ensures comprehensive coverage while enabling maximum parallelization—the key to efficient, thorough penetration testing.
