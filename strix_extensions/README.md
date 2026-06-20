# Strix SSO Extension

This extension adds **SSO authentication capabilities** to Strix via MCP (Model Context Protocol) integration and browser cookie management.

## 🎯 Features

- **SSO Authentication**: Authenticate to SSO-protected applications via external MCP server
- **Cookie Management**: Inject, retrieve, and clear browser cookies
- **MCP Integration**: Generic MCP client for calling external tools
- **Zero Core Modifications**: Extends Strix without touching upstream code
- **Test-Driven**: Includes Docker Compose setup for e2e testing

## 🚀 Quick Start

### Installation

1. **Install dependencies**:
   ```bash
   pip install -r strix_extensions/requirements.txt
   ```

2. **Install Playwright browser** (if not already installed):
   ```bash
   python -m playwright install chromium
   ```

3. **Run Strix with SSO extension**:
   ```bash
   python run_strix_with_sso.py
   ```

### Basic Usage

Once Strix is running with the extension, agents have access to new tools:

#### Option 1: High-Level SSO Login (Recommended)

```python
# Agent prompt: "Authenticate to the application"

# The agent can use:
result = login_sso(
    url="https://example.com",
    username="YOUR_USERNAME",
    password="YOUR_PASSWORD",
    totp_secret="YOUR_TOTP_SECRET"
)

if result["status"] == "success":
    # Cookies are automatically ready for injection
    set_cookies(result["cookies"])
    
    # Navigate to protected app
    browser_action(action="goto", url=result["final_url"])
```

#### Option 2: Low-Level MCP Client

```python
# Call any MCP tool
result = call_mcp_tool(
    tool_name="login_sso",
    arguments={
        "url": "https://app.example.com",
        "username": "user",
        "password": "pass"
    }
)
```

## 📋 Available Tools

### 1. `login_sso(url, username, password, totp_secret=None)`

High-level SSO authentication tool. Returns cookies ready for browser injection.

**Example**:
```python
result = login_sso(
    url="https://app.example.com",
    username="YOUR_USERNAME",
    password="secret",
    totp_secret="YOUR_TOTP_SECRET"
)
# Returns: {"status": "success", "cookies": [...], "final_url": "...", "login_done": True}
```

### 2. `call_mcp_tool(tool_name, arguments)`

Generic MCP client for calling any tool on the configured MCP server.

**Example**:
```python
result = call_mcp_tool(
    tool_name="login_sso",
    arguments={"url": "...", "username": "...", "password": "..."}
)
# Returns: {"status": "success", "content": [...]}
```

### 3. `set_cookies(cookies)`

Inject cookies into the browser context.

**Example**:
```python
set_cookies([
    {
        "name": "session_id",
        "value": "abc123",
        "domain": "example.com",
        "path": "/"
    }
])
# Returns: {"status": "success", "cookies_set": 1}
```

### 4. `get_cookies(url=None)`

Retrieve cookies from the browser.

**Example**:
```python
result = get_cookies()
# Returns: {"status": "success", "cookies": [...], "count": 2}
```

### 5. `clear_cookies()`

Clear all cookies from the browser.

**Example**:
```python
clear_cookies()
# Returns: {"status": "success", "message": "Cleared all cookies"}
```

## 🔄 Typical Workflow

### Complete SSO Authentication Flow

```python
# 1. Launch browser (if not already running)
browser_action(action="launch")

# 2. Authenticate via SSO
sso_result = login_sso(
    url="https://appinspector.example.com",
    username="YOUR_USERNAME",
    password="secret",
    totp_secret="YOUR_TOTP_SECRET"
)

# 3. Check authentication status
if sso_result["status"] != "success":
    print(f"Authentication failed: {sso_result['message']}")
    exit(1)

# 4. Inject cookies into browser
cookie_result = set_cookies(sso_result["cookies"])
print(f"Set {cookie_result['cookies_set']} cookies")

# 5. Navigate to protected application
browser_action(
    action="goto",
    url="https://appinspector.example.com"
)

# 6. Application is now accessible with SSO session!
# Continue with regular browser automation...

# 7. Optional: Verify cookies
cookies = get_cookies()
print(f"Active cookies: {cookies['count']}")

# 8. Optional: Clear session when done
clear_cookies()
```

## 🔧 Configuration

### MCP Server Configuration

The MCP server URL is configured in `strix_extensions/tools/mcp_client.py`:

```python
MCP_SERVER_URL = "https://your-mcp-server.example.com/mcp"
MCP_TIMEOUT = 30.0  # seconds
```

To use a different MCP server, modify these constants or set environment variables:

```bash
export MCP_SERVER_URL="https://your-mcp-server.com/mcp"
export MCP_TIMEOUT="60.0"
```

## 🧪 Testing

### Unit Tests

```bash
# Run tests
pytest strix_extensions/tests/test_sso_integration.py -v

# Run with coverage
pytest strix_extensions/tests/test_sso_integration.py --cov=strix_extensions
```

- **strix-sso**: Strix instance with SSO extension

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Strix Agent                        │
├─────────────────────────────────────────────────────┤
│  Built-in Tools           Extension Tools            │
│  ├─ browser_action        ├─ login_sso              │
│  ├─ file_edit             ├─ call_mcp_tool          │
│  ├─ terminal              ├─ set_cookies            │
│  └─ ...                   ├─ get_cookies            │
│                           └─ clear_cookies          │
└──────────────┬────────────────────────┬─────────────┘
               │                        │
               ▼                        ▼
      ┌────────────────┐      ┌────────────────────┐
      │ Playwright     │      │  External MCP      │
      │ Browser        │      │  SSO Server        │
      └────────────────┘      └────────────────────┘
```

### Component Overview

1. **Extension Loader** (`run_strix_with_sso.py`): Loads extension tools before Strix starts
2. **MCP Client** (`mcp_client.py`): Communicates with external MCP server via HTTP
3. **Browser Cookies** (`browser_cookies.py`): Manages Playwright browser cookies
4. **Tool Registry**: Strix's `@register_tool` decorator integrates everything

### Key Design Decisions

- **No Core Modifications**: All code in separate `strix_extensions/` directory
- **Wrapper Script Pattern**: Extensions load via import before Strix initialization
- **Playwright Native APIs**: Uses Playwright's built-in cookie management
- **SSE Transport**: MCP client uses HTTP/SSE for simplicity (no stdio complexity)

### ⚠️ **Important Compatibility Note**

This extension accesses some private Strix APIs (`manager._get_agent_browser()` and `browser._loop`) for browser integration. While this works with the current version of Strix, these private APIs may change in future releases.

**Recommendations**:
- Test after each Strix upgrade
- Consider contributing cookie management to upstream Strix for a more stable public API
- Monitor Strix release notes for browser API changes

If Strix changes these internal APIs, the extension may need updates. Opening an issue with Strix maintainers to request public browser cookie APIs would make this extension more maintainable long-term.

## 📚 Documentation

### XML Schemas

The extension includes comprehensive XML schemas for agent understanding:

- `browser_cookies_schema.xml`: Cookie management tools
- `mcp_client_schema.xml`: MCP client and SSO login tools

These schemas teach the agent:
- When to use each tool
- Required parameters and types
- Common workflows and patterns
- Error handling strategies

### Example Agent Prompts

**Authenticate to protected application**:
```
"Authenticate to https://appinspector.example.com using SSO credentials 
and navigate to the dashboard"
```

**Test SSO session persistence**:
```
"Login to the application, verify the cookies are set, navigate to 3 different 
pages, and confirm the session persists"
```

**Debug authentication issues**:
```
"Authenticate to the app, retrieve and display all cookies, then clear cookies 
and try accessing the app again to verify it's protected"
```

## 🔒 Security Considerations

1. **Credential Handling**:
   - Credentials are passed to MCP server over HTTPS
   - Not logged or persisted by default
   - Use environment variables for sensitive data

2. **Cookie Storage**:
   - Cookies stored in browser context only (memory)
   - Not persisted to disk unless explicitly configured
   - Each agent gets isolated browser instance

3. **Network Security**:
   - MCP server should be on trusted network
   - Consider VPN/firewall for production deployments
   - HTTPS required for credential transmission

## 🐛 Troubleshooting

### "No browser instance available"

**Cause**: Browser not launched before calling set_cookies()

**Solution**: Launch browser first:
```python
browser_action(action="launch")
# OR just navigate (auto-launches):
browser_action(action="goto", url="https://example.com")
```

### "MCP server unreachable"

**Cause**: Network connectivity issue or wrong MCP URL

**Solution**: 
- Verify MCP_SERVER_URL is correct
- Check network connectivity: `curl https://your-mcp-server.example.com/mcp`
- Ensure you're on the correct network (VPN, etc.)

### "No valid cookies provided"

**Cause**: Cookies missing required fields (name, value, domain)

**Solution**: Verify MCP response format:
```python
result = call_mcp_tool(...)
print(result)  # Inspect the cookie structure
```

### "Login did not complete successfully"

**Cause**: Invalid credentials or 2FA required

**Solution**:
- Verify username/password are correct
- Ensure totp_secret is provided if 2FA is required
- Check MCP server logs for details

## 🤝 Contributing

### Adding New MCP Tools

To add support for additional MCP tools:

1. Add tool documentation to `mcp_client_schema.xml`
2. Optionally create convenience wrapper (like `login_sso`)
3. Add tests to `test_sso_integration.py`
4. Update this README

### Proposing Upstream Changes

If you implement features that would benefit the Strix community:

1. Open issue in [Strix repository](https://github.com/usestrix/strix)
2. Describe the feature and use case
3. Offer to submit PR with your battle-tested implementation

The cookie management tools would be excellent candidates for upstreaming!

## 📄 License

This extension follows the same license as Strix (Apache 2.0).

## 🙏 Acknowledgments

- **Strix Team**: For the excellent agent framework and extensibility
- **MCP Protocol**: For standardized tool communication
- **Playwright**: For robust browser automation

## 📞 Support

For issues specific to this extension:
- Check troubleshooting section above
- Review test cases for usage examples
- Inspect XML schemas for tool documentation

For Strix core issues:
- [Strix GitHub Issues](https://github.com/usestrix/strix/issues)
- [Strix Documentation](https://docs.usestrix.com)
