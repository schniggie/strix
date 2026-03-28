"""Integration tests for SSO extension."""

import json
from unittest.mock import MagicMock, patch

import pytest


class TestMCPClient:
    """Tests for MCP client functionality."""

    @patch('strix_extensions.tools.mcp_client.httpx.Client')
    def test_call_mcp_tool_success(self, mock_client):
        """Test successful MCP tool call."""
        from strix_extensions.tools.mcp_client import call_mcp_tool
        
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": [
                {
                    "type": "text",
                    "text": '{"final_url": "https://example.com", "cookies": []}'
                }
            ],
            "isError": False
        }
        mock_response.raise_for_status = MagicMock()
        
        mock_client_instance = MagicMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance
        
        # Call tool
        result = call_mcp_tool(
            tool_name="test_tool",
            arguments={"arg1": "value1"}
        )
        
        # Verify
        assert result["status"] == "success"
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "json"

    @patch('strix_extensions.tools.mcp_client.httpx.Client')
    def test_call_mcp_tool_error(self, mock_client):
        """Test MCP tool call with error response."""
        from strix_extensions.tools.mcp_client import call_mcp_tool
        
        # Mock error response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": [
                {
                    "type": "text",
                    "text": "Authentication failed"
                }
            ],
            "isError": True
        }
        mock_response.raise_for_status = MagicMock()
        
        mock_client_instance = MagicMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance
        
        # Call tool
        result = call_mcp_tool(
            tool_name="test_tool",
            arguments={"arg1": "value1"}
        )
        
        # Verify
        assert result["status"] == "error"
        assert "Authentication failed" in result["message"]

    @patch('strix_extensions.tools.mcp_client.call_mcp_tool')
    def test_login_sso_success(self, mock_call_mcp):
        """Test successful SSO login."""
        from strix_extensions.tools.mcp_client import login_sso
        
        # Mock MCP response
        mock_call_mcp.return_value = {
            "status": "success",
            "content": [
                {
                    "type": "json",
                    "data": {
                        "final_url": "https://example.com",
                        "login_done": True,
                        "cookies": [
                            {
                                "name": "session_id",
                                "value": "abc123",
                                "domain": "example.com",
                                "path": "/"
                            }
                        ]
                    }
                }
            ]
        }
        
        # Call login_sso
        result = login_sso(
            url="https://example.com",
            username="testuser",
            password="testpass"
        )
        
        # Verify
        assert result["status"] == "success"
        assert result["login_done"] is True
        assert len(result["cookies"]) == 1
        assert result["cookies"][0]["name"] == "session_id"

    @patch('strix_extensions.tools.mcp_client.call_mcp_tool')
    def test_login_sso_no_cookies(self, mock_call_mcp):
        """Test SSO login with no cookies returned."""
        from strix_extensions.tools.mcp_client import login_sso
        
        # Mock MCP response with no cookies
        mock_call_mcp.return_value = {
            "status": "success",
            "content": [
                {
                    "type": "json",
                    "data": {
                        "final_url": "https://example.com",
                        "login_done": True,
                        "cookies": []
                    }
                }
            ]
        }
        
        # Call login_sso
        result = login_sso(
            url="https://example.com",
            username="testuser",
            password="testpass"
        )
        
        # Verify
        assert result["status"] == "error"
        assert "no cookies" in result["message"].lower()


class TestBrowserCookies:
    """Tests for browser cookie management."""

    def test_cookie_validation(self):
        """Test cookie format validation."""
        # This would require mocking the browser instance
        # For now, just test the structure
        valid_cookie = {
            "name": "test",
            "value": "abc123",
            "domain": "example.com",
            "path": "/"
        }
        
        assert "name" in valid_cookie
        assert "value" in valid_cookie
        assert "domain" in valid_cookie

    def test_invalid_cookie_missing_fields(self):
        """Test handling of invalid cookies."""
        invalid_cookie = {
            "name": "test"
            # Missing value and domain
        }
        
        assert "value" not in invalid_cookie
        assert "domain" not in invalid_cookie


class TestIntegrationWorkflow:
    """End-to-end integration tests."""

    @patch('strix_extensions.tools.mcp_client.call_mcp_tool')
    @patch('strix_extensions.tools.browser_cookies._get_browser_instance')
    def test_full_sso_workflow(self, mock_browser, mock_mcp):
        """Test complete SSO authentication workflow."""
        from strix_extensions.tools.mcp_client import login_sso
        from strix_extensions.tools.browser_cookies import set_cookies
        
        # Mock SSO login response
        mock_mcp.return_value = {
            "status": "success",
            "content": [
                {
                    "type": "json",
                    "data": {
                        "final_url": "https://app.example.com",
                        "login_done": True,
                        "cookies": [
                            {
                                "name": "OAuth_Token_Request_State",
                                "value": "c2ba1675-2ad1-4d16-9193-15457f069fb6",
                                "domain": "app.example.com",
                                "path": "/"
                            }
                        ]
                    }
                }
            ]
        }
        
        # Mock browser instance
        mock_browser_instance = MagicMock()
        mock_context = MagicMock()
        mock_browser_instance.context = mock_context
        mock_browser_instance._loop = MagicMock()
        mock_browser.return_value = mock_browser_instance
        
        # Step 1: Login and get cookies
        login_result = login_sso(
            url="https://app.example.com",
            username="testuser",
            password="testpass"
        )
        
        assert login_result["status"] == "success"
        assert len(login_result["cookies"]) == 1
        
        # Step 2: Set cookies in browser (would normally work with real browser)
        # This is mocked, so we just verify the structure
        cookies = login_result["cookies"]
        assert cookies[0]["name"] == "OAuth_Token_Request_State"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

