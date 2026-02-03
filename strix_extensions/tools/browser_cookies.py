"""Browser cookie management tools for Strix.

This module provides tools to manage browser cookies, enabling SSO authentication
and session management workflows.
"""

import logging
from typing import Any

from strix.tools.registry import register_tool

logger = logging.getLogger(__name__)


def _get_browser_instance() -> Any:
    """Get the current agent's browser instance."""
    from strix.tools.browser.tab_manager import get_browser_tab_manager

    manager = get_browser_tab_manager()
    browser = manager._get_agent_browser()
    
    if browser is None:
        raise RuntimeError(
            "No browser instance available. Please launch the browser first "
            "using browser_action(action='launch')"
        )
    
    if browser.context is None:
        raise RuntimeError(
            "Browser context not initialized. Please navigate to a URL first "
            "using browser_action(action='goto', url='...')"
        )
    
    return browser


@register_tool(sandbox_execution=True)
def set_cookies(cookies: list[dict[str, Any]], tab_id: str | None = None) -> dict[str, Any]:
    """Inject cookies into the browser context.

    This tool allows you to set authentication cookies received from SSO login
    or other authentication mechanisms. Cookies will persist across all browser
    actions until explicitly cleared or the browser is closed.

    Args:
        cookies: List of cookie dictionaries. Each cookie must have:
            - name (str): Cookie name
            - value (str): Cookie value
            - domain (str): Cookie domain
            - path (str): Cookie path (default: "/")
            Optional fields:
            - expires (float): Unix timestamp for expiration
            - httpOnly (bool): HttpOnly flag
            - secure (bool): Secure flag
            - sameSite (str): "Strict", "Lax", or "None"
        tab_id: Optional tab ID (unused, for compatibility)

    Returns:
        dict with status and message

    Example:
        set_cookies([
            {
                "name": "session_token",
                "value": "abc123",
                "domain": "example.com",
                "path": "/"
            }
        ])
    """
    try:
        browser = _get_browser_instance()
        
        # Validate cookies
        validated_cookies = []
        for cookie in cookies:
            if not isinstance(cookie, dict):
                logger.warning(f"Skipping invalid cookie (not a dict): {cookie}")
                continue
            
            # Required fields
            if "name" not in cookie or "value" not in cookie or "domain" not in cookie:
                logger.warning(f"Skipping cookie missing required fields: {cookie}")
                continue
            
            # Build validated cookie with defaults
            validated = {
                "name": str(cookie["name"]),
                "value": str(cookie["value"]),
                "domain": str(cookie["domain"]),
                "path": cookie.get("path", "/"),
            }
            
            # Optional fields
            if "expires" in cookie:
                validated["expires"] = float(cookie["expires"])
            if "httpOnly" in cookie:
                validated["httpOnly"] = bool(cookie["httpOnly"])
            if "secure" in cookie:
                validated["secure"] = bool(cookie["secure"])
            if "sameSite" in cookie:
                same_site = str(cookie["sameSite"])
                if same_site in ["Strict", "Lax", "None"]:
                    validated["sameSite"] = same_site
            
            validated_cookies.append(validated)
        
        if not validated_cookies:
            return {
                "status": "error",
                "message": "No valid cookies provided",
                "cookies_set": 0
            }
        
        # Add cookies to browser context
        import asyncio
        loop = browser._loop
        future = asyncio.run_coroutine_threadsafe(
            browser.context.add_cookies(validated_cookies),
            loop
        )
        future.result(timeout=10)
        
        logger.info(f"Successfully set {len(validated_cookies)} cookies")
        
        return {
            "status": "success",
            "message": f"Set {len(validated_cookies)} cookies in browser context",
            "cookies_set": len(validated_cookies)
        }
        
    except RuntimeError as e:
        logger.error(f"Browser error: {e}")
        return {
            "status": "error",
            "message": str(e),
            "cookies_set": 0
        }
    except Exception as e:
        logger.error(f"Failed to set cookies: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"Failed to set cookies: {str(e)}",
            "cookies_set": 0
        }


@register_tool(sandbox_execution=True)
def get_cookies(url: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
    """Retrieve cookies from the browser context.

    Args:
        url: Optional URL to filter cookies by domain
        tab_id: Optional tab ID (unused, for compatibility)

    Returns:
        dict with status and list of cookies

    Example:
        result = get_cookies()
        # Returns: {"status": "success", "cookies": [{...}, {...}]}
    """
    try:
        browser = _get_browser_instance()
        
        # Get cookies from browser context
        import asyncio
        loop = browser._loop
        future = asyncio.run_coroutine_threadsafe(
            browser.context.cookies(url),
            loop
        )
        cookies = future.result(timeout=10)
        
        logger.info(f"Retrieved {len(cookies)} cookies")
        
        return {
            "status": "success",
            "cookies": cookies,
            "count": len(cookies)
        }
        
    except RuntimeError as e:
        logger.error(f"Browser error: {e}")
        return {
            "status": "error",
            "message": str(e),
            "cookies": []
        }
    except Exception as e:
        logger.error(f"Failed to get cookies: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"Failed to get cookies: {str(e)}",
            "cookies": []
        }


@register_tool(sandbox_execution=True)
def clear_cookies(tab_id: str | None = None) -> dict[str, Any]:
    """Clear all cookies from the browser context.

    Args:
        tab_id: Optional tab ID (unused, for compatibility)

    Returns:
        dict with status and message

    Example:
        clear_cookies()
        # Returns: {"status": "success", "message": "Cleared all cookies"}
    """
    try:
        browser = _get_browser_instance()
        
        # Clear cookies from browser context
        import asyncio
        loop = browser._loop
        future = asyncio.run_coroutine_threadsafe(
            browser.context.clear_cookies(),
            loop
        )
        future.result(timeout=10)
        
        logger.info("Cleared all cookies from browser context")
        
        return {
            "status": "success",
            "message": "Cleared all cookies from browser context"
        }
        
    except RuntimeError as e:
        logger.error(f"Browser error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }
    except Exception as e:
        logger.error(f"Failed to clear cookies: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"Failed to clear cookies: {str(e)}"
        }

