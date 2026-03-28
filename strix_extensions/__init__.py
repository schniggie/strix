"""Strix SSO Extension.

This extension adds SSO authentication capabilities to Strix via MCP integration
and browser cookie management.

To use this extension, import it before starting Strix:

    from strix_extensions.tools import mcp_client, browser_cookies
    from strix.interface.main import main
    
    if __name__ == "__main__":
        main()

The extension provides:
- login_sso(): High-level SSO authentication
- call_mcp_tool(): Generic MCP client
- set_cookies(): Inject cookies into browser
- get_cookies(): Retrieve browser cookies
- clear_cookies(): Clear all cookies
"""

__version__ = "0.1.0"

