"""
Security utilities for the Strix web interface.
"""

import re
import time
from collections import defaultdict
from typing import Dict, List
from urllib.parse import urlparse

from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer
from pydantic import ValidationError


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = defaultdict(list)
    
    def is_allowed(self, client_ip: str) -> bool:
        """Check if request is allowed based on rate limiting."""
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip] 
            if req_time > window_start
        ]
        
        # Check if under limit
        if len(self.requests[client_ip]) >= self.max_requests:
            return False
        
        # Add current request
        self.requests[client_ip].append(now)
        return True


class InputValidator:
    """Input validation utilities."""
    
    # Allowed URL schemes
    ALLOWED_SCHEMES = {'http', 'https'}
    
    # Allowed repository URL patterns
    REPO_URL_PATTERNS = [
        r'^https://github\.com/[\w\-\.]+/[\w\-\.]+/?$',
        r'^git@github\.com:[\w\-\.]+/[\w\-\.]+\.git$',
        r'^https://gitlab\.com/[\w\-\.]+/[\w\-\.]+/?$',
        r'^https://bitbucket\.org/[\w\-\.]+/[\w\-\.]+/?$',
    ]
    
    # Dangerous patterns to block
    DANGEROUS_PATTERNS = [
        r'javascript:',
        r'data:',
        r'file:',
        r'ftp:',
        r'localhost',
        r'127\.0\.0\.1',
        r'0\.0\.0\.0',
        r'::1',
        r'169\.254\.',  # Link-local addresses
        r'10\.',        # Private networks
        r'172\.(1[6-9]|2[0-9]|3[0-1])\.',
        r'192\.168\.',
    ]
    
    @classmethod
    def validate_target_url(cls, url: str) -> str:
        """Validate and sanitize target URL."""
        if not url or not url.strip():
            raise ValueError("Target URL cannot be empty")
        
        url = url.strip()
        
        # Parse URL
        try:
            parsed = urlparse(url)
        except Exception:
            raise ValueError("Invalid URL format")
        
        # Check scheme
        if parsed.scheme.lower() not in cls.ALLOWED_SCHEMES:
            raise ValueError(f"URL scheme must be one of: {', '.join(cls.ALLOWED_SCHEMES)}")
        
        # Check for dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                raise ValueError("URL contains potentially dangerous content")
        
        # Check hostname
        if not parsed.hostname:
            raise ValueError("URL must have a valid hostname")
        
        # Block private/local addresses in production
        hostname = parsed.hostname.lower()
        if any(re.search(pattern, hostname, re.IGNORECASE) for pattern in cls.DANGEROUS_PATTERNS):
            raise ValueError("Private/local addresses are not allowed")
        
        return url
    
    @classmethod
    def validate_repo_url(cls, url: str) -> str:
        """Validate repository URL."""
        if not url or not url.strip():
            return ""
        
        url = url.strip()
        
        # Check against allowed patterns
        if not any(re.match(pattern, url, re.IGNORECASE) for pattern in cls.REPO_URL_PATTERNS):
            raise ValueError("Repository URL format not supported. Supported: GitHub, GitLab, Bitbucket")
        
        return url
    
    @classmethod
    def validate_instructions(cls, instructions: str) -> str:
        """Validate and sanitize instructions."""
        if not instructions or not instructions.strip():
            return ""
        
        instructions = instructions.strip()
        
        # Length limit
        if len(instructions) > 5000:
            raise ValueError("Instructions too long (max 5000 characters)")
        
        # Check for potentially dangerous content
        dangerous_keywords = [
            'rm -rf', 'sudo', 'chmod', 'chown', 'passwd', 'shadow',
            'eval', 'exec', 'system', 'shell', 'bash', 'sh',
            'curl', 'wget', 'nc', 'netcat', 'telnet', 'ssh'
        ]
        
        instructions_lower = instructions.lower()
        for keyword in dangerous_keywords:
            if keyword in instructions_lower:
                raise ValueError(f"Instructions contain potentially dangerous keyword: {keyword}")
        
        return instructions


# Global rate limiter instance
rate_limiter = RateLimiter(max_requests=20, window_seconds=300)  # 20 requests per 5 minutes


def get_client_ip(request: Request) -> str:
    """Get client IP address from request."""
    # Check for forwarded headers (when behind proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct connection
    return request.client.host if request.client else "unknown"


def check_rate_limit(request: Request):
    """Check rate limit for request."""
    client_ip = get_client_ip(request)
    
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later."
        )


def validate_scan_input(target_url: str, repo_url: str = None, instructions: str = None) -> tuple:
    """Validate all scan input parameters."""
    try:
        # Validate target URL
        validated_target = InputValidator.validate_target_url(target_url)
        
        # Validate repo URL
        validated_repo = InputValidator.validate_repo_url(repo_url) if repo_url else None
        
        # Validate instructions
        validated_instructions = InputValidator.validate_instructions(instructions) if instructions else None
        
        return validated_target, validated_repo, validated_instructions
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Security headers middleware
def add_security_headers(response):
    """Add security headers to response."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
        "font-src 'self' https://cdnjs.cloudflare.com; "
        "img-src 'self' data:; "
        "connect-src 'self' ws: wss:; "
        "frame-ancestors 'none';"
    )
    return response