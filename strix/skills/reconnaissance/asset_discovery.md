---
name: asset_discovery
description: Subdomain enumeration, IP discovery, and external asset mapping for comprehensive attack surface identification
---

# Asset Discovery

Comprehensive asset discovery identifies all externally-accessible resources associated with a target. This phase seeds all subsequent testing by revealing the full scope of what can be attacked.

## Core Objectives

1. **Subdomain Enumeration** - Find all subdomains associated with target domain(s)
2. **IP Range Discovery** - Identify IP blocks and cloud infrastructure
3. **Service Correlation** - Map relationships between discovered assets
4. **Scope Expansion** - Identify related assets that may be in-scope

## Subdomain Enumeration

### Passive Discovery (No Target Interaction)

**Subfinder** - Primary passive enumeration tool
```bash
# Basic enumeration with all passive sources
subfinder -d target.com -all -o subdomains.txt

# Multiple domains
subfinder -dL domains.txt -all -o all_subdomains.txt

# JSON output with sources for analysis
subfinder -d target.com -all -json -o subdomains.json

# Recursive enumeration (find subdomains of subdomains)
subfinder -d target.com -all -recursive -o recursive_subs.txt
```

**Certificate Transparency**
```bash
# Query CT logs directly
curl -s "https://crt.sh/?q=%.target.com&output=json" | jq -r '.[].name_value' | sort -u

# Historical certificates (may reveal old/forgotten subdomains)
curl -s "https://crt.sh/?q=%.target.com&output=json" | jq -r '.[].common_name' | sort -u
```

**DNS Aggregators**
- SecurityTrails API
- VirusTotal domain reports
- DNSDumpster
- RapidDNS
- Riddler.io

### Active Discovery (Direct Interaction)

**DNS Brute Force**
```bash
# Using dnsx for resolution + brute
dnsx -d target.com -w /path/to/wordlist.txt -o bruteforce_subs.txt

# Common wordlists
# - SecLists/Discovery/DNS/subdomains-top1million-5000.txt
# - SecLists/Discovery/DNS/fierce-hostlist.txt
# - SecLists/Discovery/DNS/namelist.txt
```

**DNS Record Analysis**
```bash
# Resolve all discovered subdomains
cat subdomains.txt | dnsx -silent -a -resp -o resolved.txt

# Get all DNS record types
cat subdomains.txt | dnsx -silent -a -aaaa -cname -mx -txt -resp-only -o dns_records.txt

# Find CNAME chains (potential takeover targets)
cat subdomains.txt | dnsx -silent -cname -resp -o cnames.txt
```

### Virtual Host Discovery

```bash
# Fuzz for vhosts on known IPs
ffuf -w /path/to/vhost-wordlist.txt -u http://IP_ADDRESS -H "Host: FUZZ.target.com" -fs SIZE_TO_FILTER

# Check for vhost variations
for sub in admin staging dev test uat; do
  curl -s -o /dev/null -w "%{http_code}" -H "Host: $sub.target.com" http://IP_ADDRESS
done
```

## IP and Infrastructure Discovery

### ASN and IP Range Mapping

```bash
# Find ASN for organization
whois -h whois.radb.net -- '-i origin AS12345'

# Get IP ranges from ASN
curl -s "https://api.bgpview.io/asn/12345/prefixes" | jq -r '.data.ipv4_prefixes[].prefix'

# Map domains to IPs
cat subdomains.txt | dnsx -silent -a -resp-only | sort -u > ips.txt
```

### Cloud Infrastructure Detection

**AWS**
```bash
# S3 bucket enumeration
for bucket in target target-prod target-dev target-backup; do
  aws s3 ls s3://$bucket --no-sign-request 2>/dev/null && echo "PUBLIC: $bucket"
done

# Check for EC2 metadata exposure on discovered hosts
curl -s http://TARGET/latest/meta-data/
```

**Azure/GCP**
```bash
# Azure blob storage
curl -s "https://targetaccount.blob.core.windows.net/\$web?restype=container&comp=list"

# GCP storage
curl -s "https://storage.googleapis.com/target-bucket"
```

## Live Host Identification

### HTTP Probing

```bash
# Probe all subdomains for live web servers
cat subdomains.txt | httpx -silent -status-code -title -tech-detect -o live_hosts.txt

# With additional metadata
cat subdomains.txt | httpx -silent -json -status-code -content-length -title -tech-detect -favicon -jarm -o httpx_results.json

# Filter for interesting status codes
cat subdomains.txt | httpx -silent -mc 200,301,302,401,403,500 -o filtered_hosts.txt
```

### Service Detection

```bash
# Fast port scan on discovered IPs
naabu -l ips.txt -top-ports 1000 -o open_ports.txt

# Target specific ports
naabu -l ips.txt -p 80,443,8080,8443,8000,3000,5000,9000 -o web_ports.txt

# Combined with httpx
naabu -l ips.txt -p 80,443,8080,8443 -silent | httpx -silent -o web_services.txt
```

## Asset Correlation

### Relationship Mapping

Build a graph of relationships:
1. **Domain → Subdomains** - Parent-child DNS relationships
2. **Subdomain → IP** - DNS resolution mappings
3. **IP → Services** - Port/protocol associations
4. **Service → Technology** - Framework/platform detection
5. **Cross-domain links** - Shared infrastructure indicators

### Shared Infrastructure Signals

- Same IP serving multiple subdomains
- Shared SSL certificates (SAN entries)
- Common CNAME targets
- Matching JARM fingerprints
- Similar response patterns

## Output Format for Task Generation

Structure discovery output for downstream task decomposition:

```json
{
  "domain": "target.com",
  "subdomains": [
    {
      "hostname": "api.target.com",
      "ip": "1.2.3.4",
      "ports": [443],
      "technologies": ["nginx", "nodejs"],
      "status_code": 200,
      "content_length": 1234
    }
  ],
  "ip_ranges": ["1.2.3.0/24"],
  "cloud_assets": {
    "s3_buckets": ["target-uploads"],
    "azure_apps": []
  },
  "takeover_candidates": [
    {"hostname": "old.target.com", "cname": "target.s3.amazonaws.com", "status": "NXDOMAIN"}
  ]
}
```

## Task Generation Triggers

Asset discovery findings that should spawn specific tasks:

| Finding | Task Type |
|---------|-----------|
| Live web server | Web crawling + vulnerability scanning |
| API endpoint | API security testing |
| Admin/staging subdomain | Authentication testing, default creds |
| CNAME to external service | Subdomain takeover check |
| S3/cloud bucket | Bucket permission testing |
| Open database port | Database authentication testing |
| Mail server (MX) | SMTP security testing |
| DNS zone transfer enabled | Document and test further |

## Pro Tips

1. **Combine sources** - No single tool finds everything; merge results from 3+ sources
2. **Historical data** - Wayback Machine, CT logs, and DNS history reveal forgotten assets
3. **Monitor for changes** - Continuous discovery catches new assets as they appear
4. **Permutation generation** - Generate subdomain permutations (dev-api, api-dev, api2, api-v2)
5. **Acquisition research** - Check for acquired companies' domains that may share infrastructure
6. **GitHub/GitLab search** - Code repos often leak internal hostnames
7. **Error messages** - 404/500 pages sometimes reveal internal hostnames

## Validation Checklist

- [ ] All passive sources queried (CT, DNS aggregators, search engines)
- [ ] Active DNS brute force completed with quality wordlist
- [ ] All discovered hosts probed for HTTP/HTTPS
- [ ] IP ranges identified and port scanned
- [ ] Cloud assets checked (S3, Azure, GCP)
- [ ] Subdomain takeover candidates identified
- [ ] Results correlated and deduplicated
- [ ] Output structured for task generation
