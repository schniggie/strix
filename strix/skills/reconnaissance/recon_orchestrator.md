---
name: recon_orchestrator
description: End-to-end reconnaissance orchestration coordinating all recon phases and task generation for maximum testing coverage
---

# Reconnaissance Orchestrator

This skill coordinates the complete reconnaissance pipeline: from initial asset discovery through task decomposition to parallel vulnerability testing. This methodology ensures comprehensive coverage by systematically mapping the attack surface before testing.

## The XBOW-Killer Formula

```
SUCCESS = THOROUGH_RECON × SMART_DECOMPOSITION × PARALLEL_EXECUTION
```

The key insight: Don't run one massive scan. Instead:
1. **Recon deeply** - Map EVERYTHING
2. **Decompose smartly** - Create dozens of specific tasks
3. **Execute in parallel** - Many small agents beat one big agent

## Complete Recon Pipeline

### Stage 1: Asset Discovery (10-15% of total effort)

**Objective**: Find all externally-accessible assets

```bash
# 1. Subdomain enumeration
subfinder -d $TARGET -all -o subdomains.txt

# 2. DNS resolution
cat subdomains.txt | dnsx -silent -a -resp -o resolved.txt

# 3. Extract IPs for port scanning
cat resolved.txt | cut -d' ' -f2 | sort -u > ips.txt

# 4. Live host identification
cat subdomains.txt | httpx -silent -status-code -title -tech-detect -json -o live_hosts.json
```

**Output**:
- `subdomains.txt` - All discovered subdomains
- `live_hosts.json` - Live web servers with metadata
- `ips.txt` - Unique IP addresses

### Stage 2: Port Scanning (5-10% of total effort)

**Objective**: Identify all network services

```bash
# 1. Fast scan of common ports
naabu -l ips.txt -top-ports 1000 -o open_ports.txt

# 2. Full port scan on key targets (if time permits)
naabu -host primary_target.com -p - -o full_ports.txt

# 3. Service identification
nmap -sV -p $(cat open_ports.txt | grep $IP | cut -d: -f2 | tr '\n' ',') $IP
```

**Output**:
- `open_ports.txt` - All open ports per host
- Service version information

### Stage 3: Web Crawling (20-25% of total effort)

**Objective**: Map complete web application structure

```bash
# 1. Unauthenticated crawl with JS rendering
katana -u https://$TARGET -headless -d 5 -js-crawl -xhr-extraction -j -o unauth_crawl.json

# 2. Authenticated crawl (if credentials available)
katana -u https://$TARGET -H "Cookie: session=$SESSION" -headless -d 5 -js-crawl -o auth_crawl.json

# 3. Directory brute force
ffuf -u https://$TARGET/FUZZ -w /path/to/wordlist.txt -mc 200,301,302,401,403 -o dirs.json

# 4. API endpoint discovery
ffuf -u https://$TARGET/api/FUZZ -w api-wordlist.txt -mc 200,201,204,401,403 -o api.json
```

**Output**:
- Complete endpoint list
- Parameter names per endpoint
- Forms and input fields
- API endpoints

### Stage 4: Technology Fingerprinting (5-10% of total effort)

**Objective**: Identify all technologies for targeted testing

```bash
# 1. Automated tech detection
cat live_hosts.txt | httpx -tech-detect -json -o tech.json

# 2. Check for exposed documentation
for doc in swagger.json openapi.json graphql api-docs; do
  curl -sI https://$TARGET/$doc | grep -q "200 OK" && echo "FOUND: $doc"
done

# 3. Framework-specific checks
# WordPress
curl -s https://$TARGET/wp-login.php | grep -q "WordPress" && echo "WordPress detected"
# Django
curl -s https://$TARGET/admin/ | grep -q "Django" && echo "Django detected"
```

**Output**:
- Technology stack per host
- Framework versions
- Exposed documentation URLs

### Stage 5: Parameter Discovery (10-15% of total effort)

**Objective**: Find all input parameters for testing

```bash
# 1. Parameter mining from crawl
cat crawl.json | jq -r '.parameters' | sort -u > params_from_crawl.txt

# 2. Active parameter discovery
arjun -i endpoints.txt -oJ all_params.json

# 3. JavaScript analysis for hidden params
cat crawl.json | jq -r '.endpoint' | grep "\.js$" | while read js; do
  linkfinder -i "$js" -o cli 2>/dev/null
done | sort -u > js_endpoints.txt
```

**Output**:
- Complete parameter list per endpoint
- Hidden parameters from JS
- API request/response structures

### Stage 6: Task Decomposition (15-20% of total effort)

**Objective**: Convert recon data into specific, actionable tasks

#### Task Generation Script

```python
#!/usr/bin/env python3
"""
Recon to Tasks Converter
Generates pentest tasks from reconnaissance data
"""

import json

# Load recon data
endpoints = json.load(open('crawl.json'))
tech = json.load(open('tech.json'))
params = json.load(open('all_params.json'))

tasks = []

# ID patterns that indicate IDOR potential
ID_PATTERNS = ['id', 'user_id', 'uid', 'account_id', 'doc_id', 'order_id',
               'project_id', 'org_id', 'file_id', 'message_id']

# URL patterns that indicate SSRF potential
URL_PATTERNS = ['url', 'link', 'redirect', 'callback', 'webhook', 'next',
                'return', 'dest', 'target', 'uri']

for endpoint in endpoints:
    path = endpoint['path']
    methods = endpoint.get('methods', ['GET'])
    params = endpoint.get('parameters', [])
    auth = endpoint.get('auth_required', False)

    # Generate injection tasks for each parameter
    for param in params:
        param_name = param['name'].lower()

        # SQLi task
        tasks.append({
            'type': 'sql_injection',
            'endpoint': path,
            'parameter': param['name'],
            'priority': 8 if 'search' in param_name or 'query' in param_name else 5,
            'skills': ['sql_injection']
        })

        # XSS task
        tasks.append({
            'type': 'xss',
            'endpoint': path,
            'parameter': param['name'],
            'priority': 6,
            'skills': ['xss']
        })

        # IDOR task for ID-like parameters
        if any(pattern in param_name for pattern in ID_PATTERNS):
            tasks.append({
                'type': 'idor',
                'endpoint': path,
                'parameter': param['name'],
                'priority': 9,
                'skills': ['idor']
            })

        # SSRF task for URL-like parameters
        if any(pattern in param_name for pattern in URL_PATTERNS):
            tasks.append({
                'type': 'ssrf',
                'endpoint': path,
                'parameter': param['name'],
                'priority': 8,
                'skills': ['ssrf']
            })

    # CSRF for state-changing methods
    if 'POST' in methods or 'PUT' in methods or 'DELETE' in methods:
        tasks.append({
            'type': 'csrf',
            'endpoint': path,
            'priority': 5,
            'skills': ['csrf']
        })

    # Auth bypass for protected endpoints
    if auth:
        tasks.append({
            'type': 'auth_bypass',
            'endpoint': path,
            'priority': 7,
            'skills': ['authentication_jwt', 'business_logic']
        })

    # Admin endpoint special handling
    if '/admin' in path:
        tasks.append({
            'type': 'privilege_escalation',
            'endpoint': path,
            'priority': 10,
            'skills': ['broken_function_level_authorization', 'idor']
        })

# Sort by priority
tasks.sort(key=lambda x: x['priority'], reverse=True)

# Output
print(f"Generated {len(tasks)} tasks")
json.dump(tasks, open('pentest_tasks.json', 'w'), indent=2)
```

#### Output: Task List Structure

```json
{
  "summary": {
    "total_tasks": 127,
    "high_priority": 23,
    "medium_priority": 58,
    "standard_priority": 46
  },
  "tasks": [
    {
      "id": "task_001",
      "type": "idor",
      "priority": 10,
      "endpoint": "/api/v1/users/{id}",
      "parameter": "id",
      "method": "GET",
      "auth_context": "low_privilege_user",
      "skills": ["idor"],
      "description": "Test IDOR vulnerability by accessing other users via /api/v1/users/{id}"
    },
    {
      "id": "task_002",
      "type": "sql_injection",
      "priority": 9,
      "endpoint": "/search",
      "parameter": "q",
      "method": "GET",
      "skills": ["sql_injection"],
      "description": "Test SQL injection on search parameter"
    }
  ]
}
```

### Stage 7: Parallel Execution (30-40% of total effort)

**Objective**: Execute all tasks with maximum parallelization

#### Agent Creation Strategy

```
HIGH PRIORITY BATCH (spawn all at once):
├── IDOR Agent for /api/users/{id}          [skills: idor]
├── IDOR Agent for /api/orders/{id}         [skills: idor]
├── SQLi Agent for /search                  [skills: sql_injection]
├── SQLi Agent for /login                   [skills: sql_injection]
├── Auth Bypass Agent for /admin            [skills: authentication_jwt, business_logic]
└── JWT Analysis Agent                      [skills: authentication_jwt]

MEDIUM PRIORITY BATCH (spawn after high completes):
├── XSS Agent for /profile                  [skills: xss]
├── XSS Agent for /comments                 [skills: xss]
├── CSRF Agent for /settings                [skills: csrf]
├── Mass Assignment Agent for /api/users    [skills: mass_assignment]
└── SSRF Agent for /webhook                 [skills: ssrf]

STANDARD PRIORITY BATCH:
├── Path Traversal Agent for /download      [skills: path_traversal_lfi_rfi]
├── Rate Limit Agent for /login             [skills: business_logic]
├── Info Disclosure Agent                   [skills: information_disclosure]
└── Tech-Specific Agents based on stack     [skills: varies]
```

#### Execution Rules

1. **Spawn in batches** - Don't create all agents at once, batch by priority
2. **Monitor for findings** - Any finding triggers validation agent immediately
3. **Share context** - All agents can access /workspace and proxy history
4. **Iterate on findings** - New findings generate new tasks (e.g., IDOR reveals IDs → more IDOR tasks)

## Time Allocation Guide

| Phase | Time % | Key Activities |
|-------|--------|----------------|
| Asset Discovery | 10-15% | Subdomains, IPs, live hosts |
| Port Scanning | 5-10% | Service detection |
| Web Crawling | 20-25% | Endpoints, parameters, APIs |
| Tech Fingerprinting | 5-10% | Frameworks, versions |
| Parameter Discovery | 10-15% | Hidden params, JS mining |
| Task Decomposition | 15-20% | Generate task list |
| Parallel Execution | 30-40% | Run all testing tasks |

## Recon Quality Checklist

Before moving to testing, verify:

- [ ] All subdomains enumerated (passive + active)
- [ ] All live hosts identified with tech detection
- [ ] All open ports scanned on primary targets
- [ ] Complete crawl with JS rendering (auth + unauth)
- [ ] Directory brute force completed
- [ ] API endpoints discovered and documented
- [ ] Parameters mapped for each endpoint
- [ ] Technology stack identified per host
- [ ] Task list generated with priorities
- [ ] Minimum 50+ tasks generated for typical target

## Example Complete Pipeline

```bash
#!/bin/bash
# Complete recon pipeline for target.com

TARGET="target.com"
WORKDIR="/workspace/recon"
mkdir -p $WORKDIR && cd $WORKDIR

echo "[*] Stage 1: Asset Discovery"
subfinder -d $TARGET -all -o subdomains.txt
cat subdomains.txt | dnsx -silent -a -resp -o resolved.txt
cat subdomains.txt | httpx -silent -status-code -title -tech-detect -json -o live_hosts.json

echo "[*] Stage 2: Port Scanning"
cat resolved.txt | cut -d' ' -f2 | sort -u > ips.txt
naabu -l ips.txt -top-ports 1000 -o open_ports.txt

echo "[*] Stage 3: Web Crawling"
katana -u https://$TARGET -headless -d 5 -js-crawl -xhr-extraction -j -o crawl.json

echo "[*] Stage 4: Directory Enumeration"
ffuf -u https://$TARGET/FUZZ -w /path/to/wordlist.txt -mc 200,301,302,401,403 -o dirs.json

echo "[*] Stage 5: Parameter Discovery"
# Extract endpoints from crawl
cat crawl.json | jq -r '.endpoint' | sort -u > endpoints.txt
arjun -i endpoints.txt -oJ params.json

echo "[*] Stage 6: Task Generation"
python3 generate_tasks.py  # Run task decomposition script

echo "[*] Recon complete. Generated tasks in pentest_tasks.json"
echo "[*] Ready for parallel execution phase"
```

## Success Metrics

Measure recon effectiveness:

| Metric | Target |
|--------|--------|
| Subdomain coverage | 95%+ of actual subdomains |
| Endpoint discovery | 90%+ of accessible endpoints |
| Parameter coverage | 85%+ of actual parameters |
| Tech accuracy | 95%+ correct identification |
| Task generation | 5+ tasks per significant endpoint |
| Parallelization | 70%+ tasks independent |

## Pro Tips

1. **Never skip recon** - 30 minutes of recon saves hours of testing
2. **Document everything** - Every finding feeds future tasks
3. **Automate pipeline** - Script the recon flow for consistency
4. **Quality over speed** - Thorough recon beats fast shallow scans
5. **Iterate** - Run additional recon based on testing findings
6. **Cross-reference** - Combine multiple tool outputs for accuracy
7. **Version everything** - Technologies change; note versions for CVE matching
8. **Think like attacker** - What would you want to know before attacking?

This orchestrated approach transforms chaotic penetration testing into a systematic, comprehensive assessment that leaves no stone unturned.
