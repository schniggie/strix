#!/usr/bin/env python3
"""Strix launcher with SSO extension.

This script loads the SSO extension tools before starting Strix,
making them available to agents without modifying core Strix code.

Usage:
    python run_strix_with_sso.py [strix arguments...]

Example:
    python run_strix_with_sso.py --task "Authenticate to the application"
"""

import sys
import os

# Add extension path to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import extensions BEFORE Strix starts (this registers the tools)
print("Loading SSO extension tools...")
from strix_extensions.tools import mcp_client, browser_cookies
print("✓ SSO extension loaded successfully")

# Now start Strix normally with all tools available
from strix.interface.main import main

if __name__ == "__main__":
    main()

