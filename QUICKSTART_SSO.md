# 🚀 SSO Extension Quick Start

Get started with SSO authentication in Strix in **3 minutes**.

## Prerequisites

- Strix installed and working
- Python 3.12+
- Access to SSO MCP server (https://sso.mcp.offsec.corpintra.net/mcp)

## Installation

### 1. Install Dependencies

```bash
pip install -r strix_extensions/requirements.txt
```

This installs:
- `mcp` - MCP protocol support
- `httpx` - HTTP client for MCP communication

### 2. Validate Extension

```bash
python strix_extensions/validate_extension.py
```

Expected output:
```
✓ All validations passed! Extension is ready to use.
```

## Usage

### Run Strix with SSO Extension

```bash
python run_strix_with_sso.py
```

That's it! Strix now has SSO capabilities.

### Test with Example Task

```bash
python run_strix_with_sso.py --task "Authenticate to https://appinspector-nonprod.offsec.mercedes-benz-techinnovation.com using SSO"
```

### Example Agent Workflow

The agent can now use these tools:

```python
# 1. Authenticate
result = login_sso(
    url="https://appinspector-nonprod.offsec.mercedes-benz-techinnovation.com",
    username="PID9A15",
    password="your_password",
    totp_secret="GVSU KSKO ZYJO KF5T G2GT TBIK OMUN JGVD"
)

# 2. Inject cookies
set_cookies(result["cookies"])

# 3. Access protected app
browser_action(action="goto", url="https://appinspector-nonprod.offsec.mercedes-benz-techinnovation.com")
```

## What's Available?

### New Tools

1. **`login_sso()`** - Authenticate to SSO-protected apps
2. **`set_cookies()`** - Inject authentication cookies
3. **`get_cookies()`** - Retrieve browser cookies
4. **`clear_cookies()`** - Clear all cookies
5. **`call_mcp_tool()`** - Generic MCP client

### Typical Workflow

```
Agent receives task
    ↓
Call login_sso() with credentials
    ↓
Extract cookies from response
    ↓
Call set_cookies() to inject
    ↓
Navigate to protected application
    ↓
Application accessible!
```

## Configuration

### MCP Server URL

Edit `strix_extensions/tools/mcp_client.py`:

```python
MCP_SERVER_URL = "https://sso.mcp.offsec.corpintra.net/mcp"
```

Or set environment variable:

```bash
export MCP_SERVER_URL="https://your-server.com/mcp"
python run_strix_with_sso.py
```

## Testing

### Unit Tests

```bash
pytest strix_extensions/tests/test_sso_integration.py -v
```

### E2E Tests (Docker)

```bash
docker-compose -f docker-compose.sso-test.yml up --build
```

## Troubleshooting

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'mcp'`

**Solution**:
```bash
pip install -r strix_extensions/requirements.txt
```

### Tool Not Registered

**Problem**: Agent says "Unknown tool: login_sso"

**Solution**: Make sure you're using `run_strix_with_sso.py`, not vanilla `strix`

### MCP Connection Error

**Problem**: `Failed to connect to MCP server`

**Solution**:
- Verify network access to MCP server
- Check if you need VPN
- Test with: `curl https://sso.mcp.offsec.corpintra.net/mcp`

## Next Steps

- 📖 Read the [full documentation](strix_extensions/README.md)
- 💡 Check [usage examples](strix_extensions/USAGE_EXAMPLE.md)
- 🧪 Run tests to see it in action
- 🤝 Consider contributing cookie management upstream

## Key Files

```
run_strix_with_sso.py              # Launch script
strix_extensions/
├── tools/
│   ├── mcp_client.py              # MCP integration
│   ├── browser_cookies.py         # Cookie management
│   ├── mcp_client_schema.xml      # Tool schemas
│   └── browser_cookies_schema.xml
├── tests/
│   └── test_sso_integration.py    # Unit tests
├── README.md                       # Full documentation
└── USAGE_EXAMPLE.md               # Examples
```

## Architecture

```
┌───────────────────────────────┐
│  Strix Agent                   │
│  + SSO Extension Tools         │
└────────┬──────────────┬────────┘
         │              │
    ┌────▼────┐    ┌────▼─────────┐
    │ Browser │    │ MCP Server   │
    │ Cookies │    │ (SSO Login)  │
    └─────────┘    └──────────────┘
```

## Support

- **Extension Issues**: Check `strix_extensions/README.md`
- **Strix Issues**: https://github.com/usestrix/strix/issues
- **Validation**: Run `python strix_extensions/validate_extension.py`

---

**You're ready to go!** 🎉

Start Strix with: `python run_strix_with_sso.py`

