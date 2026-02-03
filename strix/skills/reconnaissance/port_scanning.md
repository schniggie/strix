---
name: port_scanning
description: Network port scanning, service detection, and protocol identification for infrastructure mapping
---

# Port Scanning

Comprehensive port scanning identifies all network services exposed by target hosts. This feeds directly into service-specific vulnerability testing.

## Core Objectives

1. **Port Discovery** - Identify all open TCP/UDP ports
2. **Service Detection** - Determine what services run on each port
3. **Version Fingerprinting** - Identify specific software versions
4. **Protocol Analysis** - Understand how services communicate

## Scanning Strategy

### Phased Approach

**Phase 1: Fast Discovery**
```bash
# Quick top ports scan with naabu (fastest)
naabu -l hosts.txt -top-ports 100 -silent -o quick_scan.txt

# Parallel scanning for speed
naabu -l hosts.txt -p 80,443,22,21,23,25,53,110,143,3306,5432,6379,27017 -rate 1000 -o common_ports.txt
```

**Phase 2: Comprehensive Scan**
```bash
# Full port range on high-value targets
naabu -host target.com -p - -silent -o full_ports.txt

# Top 1000 ports on all hosts
naabu -l hosts.txt -top-ports 1000 -o top1000.txt
```

**Phase 3: Service Identification**
```bash
# Nmap service detection on discovered ports
nmap -sV -sC -p $(cat open_ports.txt | tr '\n' ',') -oA nmap_services target.com

# Aggressive version detection
nmap -sV --version-intensity 5 -p PORT target.com
```

## Tool Selection

### Naabu (Speed-Optimized)

```bash
# Basic scan
naabu -host target.com -top-ports 1000

# With rate limiting (for stability)
naabu -l hosts.txt -top-ports 1000 -rate 500 -retries 2

# Exclude CDN/WAF IPs
naabu -l hosts.txt -top-ports 1000 -exclude-cdn

# Output with host:port format
naabu -l hosts.txt -top-ports 1000 -silent -o results.txt

# JSON output for parsing
naabu -host target.com -top-ports 1000 -json -o results.json
```

### Nmap (Feature-Rich)

```bash
# SYN scan (requires root)
sudo nmap -sS -p- --min-rate 1000 target.com

# Service version detection
nmap -sV -p 22,80,443,3306 target.com

# OS detection
sudo nmap -O target.com

# Script scanning
nmap -sC -sV -p 80,443 target.com

# UDP scan (slow but necessary)
sudo nmap -sU --top-ports 100 target.com

# Comprehensive scan
sudo nmap -sS -sV -sC -O -p- --min-rate 1000 -oA full_scan target.com
```

### Masscan (Massive Scale)

```bash
# Internet-scale scanning (use with caution)
sudo masscan -p80,443,8080,8443 10.0.0.0/8 --rate 10000 -oL results.txt

# Target list scanning
sudo masscan -iL targets.txt -p1-65535 --rate 1000
```

## Service-Specific Detection

### Web Services

```bash
# HTTP/HTTPS on non-standard ports
naabu -host target.com -p 80,443,8000,8080,8443,8888,9000,9090,3000,5000 | httpx -silent

# Identify web technologies
httpx -l hosts.txt -tech-detect -status-code -title

# Check for web panels
nmap -sV -p 80,443,8080 --script http-title target.com
```

### Database Services

| Port | Service | Detection Command |
|------|---------|-------------------|
| 3306 | MySQL | `nmap -sV -p 3306 --script mysql-info` |
| 5432 | PostgreSQL | `nmap -sV -p 5432 --script pgsql-info` |
| 1433 | MSSQL | `nmap -sV -p 1433 --script ms-sql-info` |
| 27017 | MongoDB | `nmap -sV -p 27017 --script mongodb-info` |
| 6379 | Redis | `nmap -sV -p 6379 --script redis-info` |
| 9200 | Elasticsearch | `curl http://target:9200` |

### Remote Access Services

```bash
# SSH
nmap -sV -p 22 --script ssh2-enum-algos,ssh-hostkey target.com

# RDP
nmap -sV -p 3389 --script rdp-enum-encryption target.com

# VNC
nmap -sV -p 5900-5910 --script vnc-info target.com

# Telnet
nmap -sV -p 23 --script telnet-encryption target.com
```

### Mail Services

```bash
# SMTP
nmap -sV -p 25,465,587 --script smtp-commands,smtp-enum-users target.com

# IMAP/POP3
nmap -sV -p 110,143,993,995 --script imap-capabilities,pop3-capabilities target.com
```

## UDP Scanning

UDP scanning is slow but critical for finding:
- DNS (53)
- SNMP (161)
- NTP (123)
- TFTP (69)
- DHCP (67-68)

```bash
# Top UDP ports
sudo nmap -sU --top-ports 20 --reason target.com

# Specific UDP services
sudo nmap -sU -p 53,123,161,500 -sV target.com

# SNMP enumeration
sudo nmap -sU -p 161 --script snmp-info target.com
```

## Evasion Techniques

### Timing and Rate Control

```bash
# Slow scan to avoid detection
nmap -T2 -p- target.com

# Custom timing
nmap --scan-delay 500ms --max-retries 1 target.com

# Rate limiting with naabu
naabu -host target.com -rate 100 -p -
```

### Fragmentation and Decoys

```bash
# Fragment packets
sudo nmap -f target.com

# Use decoys
sudo nmap -D RND:10 target.com

# Spoof source port
sudo nmap --source-port 53 target.com
```

## Output Processing

### Structured Output

```bash
# Nmap XML output for parsing
nmap -oX scan.xml -sV target.com

# Convert to JSON
python3 -c "import xmltodict, json; print(json.dumps(xmltodict.parse(open('scan.xml').read())))"

# Naabu JSON
naabu -host target.com -json -o scan.json
```

### Task Generation Format

```json
{
  "host": "target.com",
  "ip": "1.2.3.4",
  "ports": [
    {
      "port": 22,
      "protocol": "tcp",
      "state": "open",
      "service": "ssh",
      "version": "OpenSSH 8.4",
      "tasks": ["ssh_bruteforce", "ssh_config_audit"]
    },
    {
      "port": 3306,
      "protocol": "tcp",
      "state": "open",
      "service": "mysql",
      "version": "MySQL 5.7.32",
      "tasks": ["mysql_auth_test", "mysql_injection_check"]
    }
  ]
}
```

## Task Generation Triggers

| Service | Port(s) | Generated Tasks |
|---------|---------|-----------------|
| SSH | 22 | Brute force, key audit, version check |
| HTTP/HTTPS | 80,443,8080 | Web vulnerability scanning, crawling |
| MySQL | 3306 | Auth bypass, SQLi, default creds |
| PostgreSQL | 5432 | Auth test, SQLi, privilege escalation |
| Redis | 6379 | Unauthenticated access, command injection |
| MongoDB | 27017 | No-auth access, injection |
| Elasticsearch | 9200 | Unauthenticated access, data exposure |
| SMTP | 25,587 | Open relay, user enumeration |
| FTP | 21 | Anonymous access, brute force |
| SMB | 445 | Null sessions, EternalBlue, shares enum |

## Pro Tips

1. **Start fast, go deep** - Quick scans first to identify targets, then deep scans on interesting hosts
2. **Don't forget UDP** - Critical services like DNS and SNMP are UDP-only
3. **Check non-standard ports** - Web apps on 8080, 8443, 3000, 5000 are common
4. **Version matters** - Same service on different versions has different vulns
5. **Correlate with assets** - Same port patterns across hosts indicate shared infrastructure
6. **Document everything** - Keep raw scan outputs for later analysis
7. **Watch for honeypots** - All ports open or unusual service combinations

## Validation Checklist

- [ ] Fast scan completed on all targets
- [ ] Top 1000 ports scanned on primary targets
- [ ] Full port scan on high-value targets
- [ ] Service versions identified for open ports
- [ ] UDP ports checked for critical services
- [ ] Database ports specifically tested
- [ ] Web services on non-standard ports identified
- [ ] Results parsed and structured for task generation
