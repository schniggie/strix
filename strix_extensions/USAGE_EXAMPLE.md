# SSO Extension Usage Examples

This document provides practical examples of using the Strix SSO extension for common authentication scenarios.

## Example 1: Basic SSO Authentication

**Scenario**: Authenticate to a Mercedes-Benz SSO-protected application

```python
# Agent prompt: "Authenticate to AppInspector and take a screenshot"

# Step 1: Authenticate via SSO
result = login_sso(
    url="https://example.com",
    username="YOUR_USERNAME",
    password="YOUR_PASSWORD",
    totp_secret="YOUR_TOTP_SECRET"
)

# Step 2: Check authentication
if result["status"] == "success":
    print(f"✓ Authenticated successfully")
    print(f"✓ Received {len(result['cookies'])} cookies")
    print(f"✓ Final URL: {result['final_url']}")
else:
    print(f"✗ Authentication failed: {result['message']}")
    exit(1)

# Step 3: Inject cookies
set_cookies(result["cookies"])

# Step 4: Navigate to application
browser_action(
    action="goto",
    url="https://example.com"
)

# Step 5: Take screenshot
browser_action(action="save_pdf", file_path="appinspector_dashboard.pdf")
```

**Expected Result**:
- ✓ Agent authenticates successfully
- ✓ Cookies injected into browser
- ✓ Application accessible without login prompt
- ✓ Screenshot saved

---

## Example 2: Multi-Page Navigation with Session

**Scenario**: Authenticate once, navigate to multiple pages

```python
# Agent prompt: "Login and explore the application menu"

# Authenticate (same as Example 1)
result = login_sso(
    url="https://example.com",
    username="YOUR_USERNAME",
    password="YOUR_PASSWORD",
    totp_secret="YOUR_TOTP_SECRET"
)

set_cookies(result["cookies"])

# Navigate to multiple pages - cookies persist!
pages = [
    "/dashboard",
    "/reports",
    "/settings",
    "/profile"
]

for page in pages:
    browser_action(
        action="goto",
        url=f"https://example.com{page}"
    )
    browser_action(action="wait", duration=2)
    print(f"✓ Visited {page}")
```

**Expected Result**:
- ✓ Single authentication works for all pages
- ✓ No re-authentication required
- ✓ Session persists across navigation

---

## Example 3: Verify Authentication State

**Scenario**: Login and verify cookies are properly set

```python
# Agent prompt: "Authenticate and show me the session cookies"

# Authenticate
result = login_sso(
    url="https://example.com",
    username="YOUR_USERNAME",
    password="YOUR_PASSWORD"
)

# Inject cookies
set_cookies(result["cookies"])

# Verify cookies are in browser
browser_cookies = get_cookies()
print(f"Browser has {browser_cookies['count']} cookies:")
for cookie in browser_cookies["cookies"]:
    print(f"  - {cookie['name']}: {cookie['value'][:20]}... (domain: {cookie['domain']})")

# Navigate and verify access
browser_action(
    action="goto",
    url="https://example.com/dashboard"
)

# Check page title to confirm we're authenticated
browser_action(action="execute_js", js_code="return document.title")
```

**Expected Result**:
- ✓ Cookies displayed with names and domains
- ✓ Dashboard accessible (no login redirect)
- ✓ Page title shows authenticated page

---

## Example 4: Session Refresh After Expiration

**Scenario**: Handle expired session by re-authenticating

```python
# Agent prompt: "Access the protected page, and if it fails, re-authenticate"

def check_authentication_required(page_url):
    """Check if page redirected to login"""
    current_url = browser_action(action="execute_js", js_code="return window.location.href")
    return "login" in current_url.lower()

# Try accessing protected page
browser_action(
    action="goto",
    url="https://example.com/dashboard"
)

if check_authentication_required("dashboard"):
    print("Session expired, re-authenticating...")
    
    # Clear old cookies
    clear_cookies()
    
    # Re-authenticate
    result = login_sso(
        url="https://example.com",
        username="YOUR_USERNAME",
        password="YOUR_PASSWORD",
        totp_secret="YOUR_TOTP_SECRET"
    )
    
    # Inject new cookies
    set_cookies(result["cookies"])
    
    # Retry access
    browser_action(
        action="goto",
        url="https://example.com/dashboard"
    )
    
    print("✓ Re-authentication successful")
else:
    print("✓ Session still valid")
```

**Expected Result**:
- ✓ Detects expired session
- ✓ Clears old cookies
- ✓ Re-authenticates automatically
- ✓ Resumes access

---

## Example 5: Parallel Applications (Same SSO Domain)

**Scenario**: Use one SSO session for multiple applications

```python
# Agent prompt: "Authenticate and access both AppInspector and TestPortal"

# Authenticate once
result = login_sso(
    url="https://example.com",
    username="YOUR_USERNAME",
    password="YOUR_PASSWORD",
    totp_secret="YOUR_TOTP_SECRET"
)

set_cookies(result["cookies"])

# Access multiple applications with same SSO
apps = [
    "https://example.com",
    "https://testportal-nonprod.offsec.mercedes-benz-techinnovation.com",
    "https://dashboard-nonprod.offsec.mercedes-benz-techinnovation.com"
]

for app_url in apps:
    browser_action(action="goto", url=app_url)
    print(f"✓ Accessed {app_url}")
    browser_action(action="wait", duration=1)
```

**Expected Result**:
- ✓ Single authentication works across apps
- ✓ SSO cookies recognized by all apps in same domain
- ✓ No individual logins required

---

## Example 6: Low-Level MCP Client Usage

**Scenario**: Use the generic MCP client for custom workflows

```python
# Agent prompt: "Call the SSO login tool directly and show me the raw response"

# Use low-level MCP client
result = call_mcp_tool(
    tool_name="login_sso",
    arguments={
        "url": "https://example.com",
        "username": "YOUR_USERNAME",
        "password": "your_password",
        "totp_secret": "your_totp_secret"
    }
)

# Inspect raw response
print(f"Status: {result['status']}")
print(f"Content items: {len(result['content'])}")

# Extract JSON data
for item in result["content"]:
    if item["type"] == "json":
        data = item["data"]
        print(f"Final URL: {data['final_url']}")
        print(f"Login done: {data['login_done']}")
        print(f"Cookies: {len(data['cookies'])}")
        
        # Manually inject cookies
        set_cookies(data["cookies"])
```

**Expected Result**:
- ✓ Raw MCP response visible
- ✓ JSON data extracted manually
- ✓ Cookies manually injected
- ✓ Full control over workflow

---

## Example 7: Error Handling and Debugging

**Scenario**: Handle authentication errors gracefully

```python
# Agent prompt: "Try to authenticate with invalid credentials and show error"

def safe_login(url, username, password, totp_secret=None):
    """Login with comprehensive error handling"""
    try:
        result = login_sso(
            url=url,
            username=username,
            password=password,
            totp_secret=totp_secret
        )
        
        if result["status"] == "error":
            print(f"✗ Authentication failed: {result['message']}")
            return None
        
        if not result.get("login_done"):
            print(f"✗ Login did not complete")
            return None
        
        if not result.get("cookies"):
            print(f"✗ No cookies received")
            return None
        
        print(f"✓ Authentication successful")
        print(f"  - Final URL: {result['final_url']}")
        print(f"  - Cookies: {len(result['cookies'])}")
        
        return result
        
    except Exception as e:
        print(f"✗ Unexpected error: {str(e)}")
        return None

# Try authentication
result = safe_login(
    url="https://example.com",
    username="INVALID_USER",
    password="WRONG_PASSWORD"
)

if result:
    set_cookies(result["cookies"])
    browser_action(action="goto", url=result["final_url"])
else:
    print("Authentication failed, cannot proceed")
```

**Expected Result**:
- ✓ Invalid credentials detected
- ✓ Clear error message displayed
- ✓ Graceful failure (no crash)
- ✓ User informed of issue

---

## Example 8: Testing with Docker Compose

**Scenario**: Run e2e test in containerized environment

```bash
# Terminal commands

# 1. Build test environment

# 2. Start services

# 3. Wait for services to be ready
sleep 5

# 4. Run Strix with test task

# 5. Check logs

# 6. Clean up
```

**Expected Result**:
- ✓ Services start successfully
- ✓ Strix authenticates to mock SSO
- ✓ Protected app accessible
- ✓ Test completes without errors

---

## Example 9: Cookie Debugging

**Scenario**: Inspect cookies for troubleshooting

```python
# Agent prompt: "Show me detailed cookie information after login"

# Authenticate
result = login_sso(
    url="https://example.com",
    username="YOUR_USERNAME",
    password="YOUR_PASSWORD"
)

# Show cookies received from SSO
print("=== Cookies from SSO ===")
for i, cookie in enumerate(result["cookies"], 1):
    print(f"\nCookie {i}:")
    print(f"  Name: {cookie['name']}")
    print(f"  Value: {cookie['value'][:50]}...")
    print(f"  Domain: {cookie['domain']}")
    print(f"  Path: {cookie['path']}")
    if "expires" in cookie:
        print(f"  Expires: {cookie['expires']}")
    if "secure" in cookie:
        print(f"  Secure: {cookie['secure']}")
    if "httpOnly" in cookie:
        print(f"  HttpOnly: {cookie['httpOnly']}")

# Inject cookies
set_cookies(result["cookies"])

# Show cookies in browser
print("\n=== Cookies in Browser ===")
browser_cookies = get_cookies()
for i, cookie in enumerate(browser_cookies["cookies"], 1):
    print(f"\nBrowser Cookie {i}:")
    print(f"  Name: {cookie['name']}")
    print(f"  Domain: {cookie['domain']}")

# Navigate and check cookies sent to server
browser_action(
    action="goto",
    url="https://example.com"
)

# Get cookies for specific URL
url_cookies = get_cookies(url="https://example.com")
print(f"\n=== Cookies sent to application: {url_cookies['count']} ===")
```

**Expected Result**:
- ✓ Detailed cookie information displayed
- ✓ Comparison between SSO cookies and browser cookies
- ✓ Verification of cookie injection
- ✓ URL-specific cookie filtering

---

## Example 10: Clean Session Management

**Scenario**: Ensure clean state between tests

```python
# Agent prompt: "Test authentication, then clean up for next test"

def run_test_with_cleanup():
    """Run authentication test with guaranteed cleanup"""
    try:
        # Clear any existing cookies
        print("Clearing existing cookies...")
        clear_cookies()
        
        # Authenticate
        print("Authenticating...")
        result = login_sso(
            url="https://example.com",
            username="YOUR_USERNAME",
            password="YOUR_PASSWORD",
            totp_secret="YOUR_TOTP_SECRET"
        )
        
        if result["status"] != "success":
            raise Exception(f"Authentication failed: {result['message']}")
        
        # Set cookies
        print("Setting cookies...")
        set_cookies(result["cookies"])
        
        # Test access
        print("Testing access...")
        browser_action(
            action="goto",
            url="https://example.com/dashboard"
        )
        
        # Verify access
        cookies = get_cookies()
        print(f"✓ Test successful, {cookies['count']} cookies active")
        
    finally:
        # Always clean up
        print("Cleaning up...")
        clear_cookies()
        print("✓ Cleanup complete")

# Run test
run_test_with_cleanup()
```

**Expected Result**:
- ✓ Clean state before test
- ✓ Authentication and access successful
- ✓ Cleanup guaranteed even if error occurs
- ✓ Ready for next test

---

## Tips and Best Practices

### 1. Always Check Status
```python
result = login_sso(...)
if result["status"] != "success":
    # Handle error
    print(result["message"])
```

### 2. Launch Browser Early
```python
# Launch browser before authentication
browser_action(action="launch")

# Now safe to set cookies
result = login_sso(...)
set_cookies(result["cookies"])
```

### 3. Use Final URL
```python
# Use final_url from SSO response (handles redirects)
result = login_sso(...)
browser_action(action="goto", url=result["final_url"])
```

### 4. Clear Cookies Between Tests
```python
# Start fresh
clear_cookies()

# Run test
test_authentication()

# Clean up
clear_cookies()
```

### 5. Verify Cookie Injection
```python
set_cookies(cookies)

# Verify
browser_cookies = get_cookies()
print(f"Injected {browser_cookies['count']} cookies")
```

---

## Common Patterns

### Pattern: Retry on Failure
```python
def authenticate_with_retry(max_retries=3):
    for attempt in range(max_retries):
        result = login_sso(...)
        if result["status"] == "success":
            return result
        print(f"Attempt {attempt + 1} failed, retrying...")
    raise Exception("Authentication failed after retries")
```

### Pattern: Session Validation
```python
def is_session_valid():
    cookies = get_cookies()
    return cookies["count"] > 0

if not is_session_valid():
    # Re-authenticate
    result = login_sso(...)
    set_cookies(result["cookies"])
```

### Pattern: Conditional Authentication
```python
# Only authenticate if needed
browser_action(action="goto", url=target_url)

if "login" in browser_action(action="execute_js", js_code="return window.location.href"):
    # Need to authenticate
    result = login_sso(...)
    set_cookies(result["cookies"])
    browser_action(action="goto", url=target_url)
```

---

This document should help you get started with the SSO extension! For more details, see the main [README](README.md).

