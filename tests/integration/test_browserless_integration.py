#!/usr/bin/env python3
"""
Integration test script for browserless connectivity.

This script validates that the browserless integration works correctly.
It can be run manually to verify functionality without running the full test suite.

Usage:
    # Test with browserless
    export STRIX_BROWSERLESS_BASE=ws://localhost:3000
    export STRIX_BROWSERLESS_TYPE=chromium
    python tests/integration/test_browserless_integration.py

    # Test with local browser (no env vars)
    python tests/integration/test_browserless_integration.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from strix.tools.browser.browser_instance import BrowserInstance


def print_header(text: str) -> None:
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_success(text: str) -> None:
    """Print success message."""
    print(f"✅ {text}")


def print_error(text: str) -> None:
    """Print error message."""
    print(f"❌ {text}")


def print_info(text: str) -> None:
    """Print info message."""
    print(f"ℹ️  {text}")


def check_environment() -> dict[str, str | None]:
    """Check and display environment configuration."""
    print_header("Environment Configuration")
    
    config = {
        "browserless_base": os.getenv("STRIX_BROWSERLESS_BASE"),
        "browserless_type": os.getenv("STRIX_BROWSERLESS_TYPE", "chromium"),
    }
    
    if config["browserless_base"]:
        print_info(f"Browserless Base: {config['browserless_base']}")
        print_info(f"Browser Type: {config['browserless_type']}")
        print_info("Mode: Remote browserless connection")
    else:
        print_info("Browserless Base: Not set")
        print_info("Mode: Local browser launch")
    
    return config


def test_browser_launch() -> bool:
    """Test browser launch and basic navigation."""
    print_header("Test 1: Browser Launch")
    
    browser = None
    try:
        browser = BrowserInstance()
        print_success("BrowserInstance created")
        
        # Launch browser
        result = browser.launch()
        print_success("Browser launched successfully")
        
        if "tab_id" in result:
            print_success(f"Tab ID: {result['tab_id']}")
        
        if "screenshot" in result:
            screenshot_len = len(result["screenshot"])
            print_success(f"Screenshot captured ({screenshot_len} bytes)")
        
        return True
        
    except Exception as e:
        print_error(f"Browser launch failed: {e}")
        return False
    finally:
        if browser:
            browser.close()
            print_info("Browser closed")


def test_navigation() -> bool:
    """Test browser navigation."""
    print_header("Test 2: Navigation")
    
    browser = None
    try:
        browser = BrowserInstance()
        browser.launch()
        print_success("Browser launched")
        
        # Navigate to a test URL
        test_url = "https://example.com"
        print_info(f"Navigating to {test_url}")
        result = browser.goto(test_url)
        
        if result.get("url") == test_url:
            print_success(f"Navigation successful: {result.get('url')}")
        else:
            print_error(f"Navigation failed. Expected {test_url}, got {result.get('url')}")
            return False
        
        if result.get("title"):
            print_success(f"Page title: {result.get('title')}")
        
        return True
        
    except Exception as e:
        print_error(f"Navigation test failed: {e}")
        return False
    finally:
        if browser:
            browser.close()
            print_info("Browser closed")


def test_interaction() -> bool:
    """Test basic browser interaction."""
    print_header("Test 3: Browser Interaction")
    
    browser = None
    try:
        browser = BrowserInstance()
        browser.launch()
        print_success("Browser launched")
        
        # Navigate to example.com
        browser.goto("https://example.com")
        print_success("Navigated to example.com")
        
        # Test scroll
        result = browser.scroll("down")
        print_success("Scroll action executed")
        
        if "screenshot" in result:
            print_success("Screenshot captured after scroll")
        
        return True
        
    except Exception as e:
        print_error(f"Interaction test failed: {e}")
        return False
    finally:
        if browser:
            browser.close()
            print_info("Browser closed")


def test_connection_stability() -> bool:
    """Test connection stability with multiple operations."""
    print_header("Test 4: Connection Stability")
    
    browser = None
    try:
        browser = BrowserInstance()
        browser.launch()
        print_success("Browser launched")
        
        # Perform multiple navigation operations
        urls = [
            "https://example.com",
            "https://www.google.com",
            "https://github.com",
        ]
        
        for i, url in enumerate(urls, 1):
            print_info(f"Navigation {i}/{len(urls)}: {url}")
            result = browser.goto(url)
            if result.get("url"):
                print_success(f"  ✓ Success: {result.get('title', 'No title')}")
            else:
                print_error(f"  ✗ Failed to navigate to {url}")
                return False
        
        print_success("All navigation operations completed successfully")
        return True
        
    except Exception as e:
        print_error(f"Connection stability test failed: {e}")
        return False
    finally:
        if browser:
            browser.close()
            print_info("Browser closed")


def main() -> int:
    """Run all integration tests."""
    print_header("Browserless Integration Test Suite")
    print_info("Testing Strix browser tool with browserless support")
    
    # Check environment
    config = check_environment()
    
    # Run tests
    tests = [
        ("Browser Launch", test_browser_launch),
        ("Navigation", test_navigation),
        ("Interaction", test_interaction),
        ("Connection Stability", test_connection_stability),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print_error(f"Test '{test_name}' raised exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print_header("Test Summary")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print_success("All tests passed! 🎉")
        return 0
    else:
        print_error(f"{total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

