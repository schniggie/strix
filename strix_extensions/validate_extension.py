#!/usr/bin/env python3
"""Validation script for SSO extension.

This script verifies that the extension is properly configured and can be loaded.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def validate_imports():
    """Validate that all extension modules can be imported."""
    print("🔍 Validating imports...")
    
    try:
        from strix_extensions.tools import mcp_client, browser_cookies
        print("  ✓ Extension tools imported successfully")
        return True
    except ImportError as e:
        print(f"  ✗ Failed to import extension tools: {e}")
        return False


def validate_tools_registered():
    """Validate that tools are registered in Strix registry."""
    print("\n🔍 Validating tool registration...")
    
    try:
        # Import extension tools (registers them)
        from strix_extensions.tools import mcp_client, browser_cookies
        
        # Check Strix registry
        from strix.tools.registry import _tools_by_name
        
        expected_tools = [
            "login_sso",
            "call_mcp_tool",
            "set_cookies",
            "get_cookies",
            "clear_cookies"
        ]
        
        all_registered = True
        for tool_name in expected_tools:
            if tool_name in _tools_by_name:
                print(f"  ✓ {tool_name} registered")
            else:
                print(f"  ✗ {tool_name} NOT registered")
                all_registered = False
        
        return all_registered
        
    except Exception as e:
        print(f"  ✗ Failed to validate tool registration: {e}")
        return False


def validate_schemas():
    """Validate that XML schemas exist."""
    print("\n🔍 Validating XML schemas...")
    
    schemas = [
        "strix_extensions/tools/browser_cookies_schema.xml",
        "strix_extensions/tools/mcp_client_schema.xml"
    ]
    
    all_exist = True
    for schema_path in schemas:
        if os.path.exists(schema_path):
            print(f"  ✓ {schema_path}")
        else:
            print(f"  ✗ {schema_path} NOT FOUND")
            all_exist = False
    
    return all_exist


def validate_dependencies():
    """Validate that required dependencies are available."""
    print("\n🔍 Validating dependencies...")
    
    dependencies = [
        ("httpx", "httpx"),
        ("mcp", "mcp")
    ]
    
    all_available = True
    for package_name, import_name in dependencies:
        try:
            __import__(import_name)
            print(f"  ✓ {package_name} available")
        except ImportError:
            print(f"  ✗ {package_name} NOT available (install with: pip install {package_name})")
            all_available = False
    
    return all_available


def main():
    """Run all validations."""
    print("=" * 60)
    print("SSO Extension Validation")
    print("=" * 60)
    
    results = []
    
    # Run validations
    results.append(("Imports", validate_imports()))
    results.append(("Tool Registration", validate_tools_registered()))
    results.append(("XML Schemas", validate_schemas()))
    results.append(("Dependencies", validate_dependencies()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{name:.<40} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n✓ All validations passed! Extension is ready to use.")
        print("\nTo run Strix with SSO extension:")
        print("  python run_strix_with_sso.py")
        return 0
    else:
        print("\n✗ Some validations failed. Please review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

