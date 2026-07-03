"""MCP (Model Context Protocol) client tool for Strix.

This module provides a tool to communicate with external MCP servers,
enabling integration with external authentication and other services.
"""

import json
import logging
import os
from typing import Any

import httpx
from strix.tools.registry import register_tool

logger = logging.getLogger(__name__)

# MCP server configuration (configurable via environment variables)
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "https://sso.mcp.offsec.corpintra.net/mcp")
MCP_TIMEOUT = float(os.environ.get("MCP_TIMEOUT", "30.0"))


def _parse_mcp_response(response_data: dict[str, Any]) -> dict[str, Any]:
    """Parse MCP response and extract useful data.
    
    Args:
        response_data: Raw MCP response dictionary
        
    Returns:
        Parsed response with extracted data
    """
    if response_data.get("isError", False):
        error_content = response_data.get("content", [])
        error_msg = "Unknown error"
        if error_content and isinstance(error_content, list):
            for item in error_content:
                if isinstance(item, dict) and item.get("type") == "text":
                    error_msg = item.get("text", error_msg)
                    break
        return {
            "status": "error",
            "message": error_msg
        }
    
    # Extract content from response
    content = response_data.get("content", [])
    result = {
        "status": "success",
        "content": []
    }
    
    for item in content:
        if not isinstance(item, dict):
            continue
            
        item_type = item.get("type")
        
        if item_type == "text":
            text = item.get("text", "")
            # Try to parse as JSON if it looks like JSON
            if text.strip().startswith("{"):
                try:
                    parsed = json.loads(text)
                    result["content"].append({
                        "type": "json",
                        "data": parsed
                    })
                except json.JSONDecodeError:
                    result["content"].append({
                        "type": "text",
                        "text": text
                    })
            else:
                result["content"].append({
                    "type": "text",
                    "text": text
                })
        elif item_type == "image":
            result["content"].append({
                "type": "image",
                "data": item.get("data", ""),
                "mimeType": item.get("mimeType", "image/png")
            })
        else:
            result["content"].append(item)
    
    return result


@register_tool(sandbox_execution=True)
def call_mcp_tool(
    tool_name: str,
    arguments: dict[str, Any],
    progress_token: int | None = None
) -> dict[str, Any]:
    """Call a tool on the configured MCP server.
    
    This tool communicates with an external MCP server via HTTP to execute
    tools that are not available in Strix. Common use cases include:
    - SSO authentication (login_sso)
    - External API integrations
    - Specialized security tools
    
    Args:
        tool_name: Name of the MCP tool to call (e.g., "login_sso")
        arguments: Dictionary of arguments to pass to the tool
        progress_token: Optional progress token for tracking
        
    Returns:
        Dictionary with:
        - status: "success" or "error"
        - content: List of content items from MCP response
        - message: Error message if status is "error"
        
    Example:
        call_mcp_tool(
            tool_name="login_sso",
            arguments={
                "url": "https://app.example.com",
                "username": "user@example.com",
                "password": "secret",
                "totp_secret": "YOUR_TOTP_SECRET"
            }
        )
    """
    try:
        # Build MCP request
        request_payload = {
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        if progress_token is not None:
            request_payload["params"]["_meta"] = {
                "progressToken": progress_token
            }
        
        logger.info(f"Calling MCP tool '{tool_name}' at {MCP_SERVER_URL}")
        logger.debug(f"Request arguments: {arguments}")
        
        # Make HTTP request to MCP server
        with httpx.Client(timeout=MCP_TIMEOUT) as client:
            response = client.post(
                MCP_SERVER_URL,
                json=request_payload,
                headers={
                    "Content-Type": "application/json"
                }
            )
            
            response.raise_for_status()
            response_data = response.json()
        
        logger.info(f"MCP tool '{tool_name}' completed successfully")
        logger.debug(f"Response: {response_data}")
        
        # Parse and return response
        result = _parse_mcp_response(response_data)
        
        # Add raw response for debugging
        result["_raw_response"] = response_data
        
        return result
        
    except httpx.TimeoutException as e:
        logger.error(f"MCP request timeout: {e}")
        return {
            "status": "error",
            "message": f"Request to MCP server timed out after {MCP_TIMEOUT}s",
            "content": []
        }
    except httpx.HTTPStatusError as e:
        logger.error(f"MCP HTTP error: {e}")
        return {
            "status": "error",
            "message": f"HTTP error from MCP server: {e.response.status_code} {e.response.text}",
            "content": []
        }
    except httpx.RequestError as e:
        logger.error(f"MCP request error: {e}")
        return {
            "status": "error",
            "message": f"Failed to connect to MCP server: {str(e)}",
            "content": []
        }
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON response from MCP: {e}")
        return {
            "status": "error",
            "message": f"MCP server returned invalid JSON: {str(e)}",
            "content": []
        }
    except Exception as e:
        logger.error(f"Unexpected error calling MCP tool: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
            "content": []
        }


@register_tool(sandbox_execution=True)
def login_sso(
    url: str,
    username: str,
    password: str,
    totp_secret: str | None = None,
    totp_secret_int: str | None = None
) -> dict[str, Any]:
    """Convenience wrapper for SSO login via MCP server.
    
    This is a high-level tool that combines MCP call and cookie extraction
    for SSO authentication. It calls the login_sso tool on the MCP server
    and returns the authentication cookies ready for injection.
    
    Args:
        url: Target application URL to authenticate to
        username: SSO username (e.g., "YOUR_USERNAME")
        password: SSO password
        totp_secret: Optional TOTP secret for 2FA (e.g., "YOUR_TOTP_SECRET")
        totp_secret_int: Optional TOTP secret (alternate format)
        
    Returns:
        Dictionary with:
        - status: "success" or "error"
        - cookies: List of cookies to inject (if successful)
        - final_url: Final URL after authentication
        - login_done: Whether login completed successfully
        - message: Error message if status is "error"
        
    Example:
        result = login_sso(
            url="https://appinspector.example.com",
            username="YOUR_USERNAME",
            password="secret",
            totp_secret="YOUR_TOTP_SECRET"
        )
        
        if result["status"] == "success":
            set_cookies(result["cookies"])
    """
    try:
        # Prepare arguments for MCP login_sso tool
        arguments = {
            "url": url,
            "username": username,
            "password": password
        }
        
        if totp_secret is not None:
            arguments["totp_secret"] = totp_secret
        
        if totp_secret_int is not None:
            arguments["totp_secret_int"] = totp_secret_int
        
        logger.info(f"Initiating SSO login for {username} to {url}")
        
        # Call MCP server
        mcp_result = call_mcp_tool(
            tool_name="login_sso",
            arguments=arguments
        )
        
        if mcp_result["status"] == "error":
            return mcp_result
        
        # Extract login data from response
        login_data = None
        for item in mcp_result.get("content", []):
            if item.get("type") == "json":
                login_data = item.get("data")
                break
        
        if not login_data:
            logger.error("No JSON data found in MCP response")
            return {
                "status": "error",
                "message": "MCP response did not contain login data",
                "cookies": []
            }
        
        # Extract key fields
        cookies = login_data.get("cookies", [])
        final_url = login_data.get("final_url", "")
        login_done = login_data.get("login_done", False)
        
        if not login_done:
            logger.warning("SSO login reported not done")
            return {
                "status": "error",
                "message": "SSO login did not complete successfully",
                "cookies": [],
                "final_url": final_url
            }
        
        if not cookies:
            logger.warning("No cookies returned from SSO login")
            return {
                "status": "error",
                "message": "SSO login succeeded but no cookies were returned",
                "cookies": [],
                "final_url": final_url
            }
        
        logger.info(f"SSO login successful, received {len(cookies)} cookies")
        
        return {
            "status": "success",
            "cookies": cookies,
            "final_url": final_url,
            "login_done": login_done,
            "message": f"Successfully authenticated to {url}"
        }
        
    except Exception as e:
        logger.error(f"Error in login_sso: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"Failed to complete SSO login: {str(e)}",
            "cookies": []
        }
