"""Strix extension tools.

This module auto-registers custom tools when imported.
"""

from . import browser_cookies, mcp_client

__all__ = ["browser_cookies", "mcp_client"]

