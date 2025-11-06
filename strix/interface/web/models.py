"""
Pydantic models for the Strix web interface API.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl, validator


class ScanStatus(str, Enum):
    """Status of a penetration test scan."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class VulnerabilitySeverity(str, Enum):
    """Severity levels for vulnerabilities."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ScanTargetRequest(BaseModel):
    """Request model for creating a new scan."""
    target_url: str = Field(..., description="Primary target URL to scan")
    repo_url: Optional[str] = Field(None, description="Optional repository URL for white-box testing")
    instructions: Optional[str] = Field(None, description="Optional focused testing instructions")
    
    @validator('target_url')
    def validate_target_url(cls, v):
        """Validate target URL format."""
        if not v or not v.strip():
            raise ValueError("Target URL cannot be empty")
        return v.strip()
    
    @validator('repo_url')
    def validate_repo_url(cls, v):
        """Validate repository URL format if provided."""
        if v and not v.strip():
            return None
        return v.strip() if v else None
    
    @validator('instructions')
    def validate_instructions(cls, v):
        """Validate instructions if provided."""
        if v and not v.strip():
            return None
        return v.strip() if v else None


class ScanResponse(BaseModel):
    """Response model for scan creation."""
    scan_id: UUID = Field(default_factory=uuid4, description="Unique scan identifier")
    status: ScanStatus = Field(default=ScanStatus.PENDING, description="Current scan status")
    target_url: str = Field(..., description="Target URL being scanned")
    repo_url: Optional[str] = Field(None, description="Repository URL if provided")
    instructions: Optional[str] = Field(None, description="Testing instructions if provided")
    created_at: str = Field(..., description="Scan creation timestamp")
    started_at: Optional[str] = Field(None, description="Scan start timestamp")
    completed_at: Optional[str] = Field(None, description="Scan completion timestamp")


class VulnerabilityReport(BaseModel):
    """Model for vulnerability findings."""
    report_id: str = Field(..., description="Unique vulnerability report identifier")
    title: str = Field(..., description="Vulnerability title")
    severity: VulnerabilitySeverity = Field(..., description="Vulnerability severity")
    content: str = Field(..., description="Detailed vulnerability description")
    found_at: str = Field(..., description="Timestamp when vulnerability was found")


class ScanProgress(BaseModel):
    """Model for scan progress updates."""
    scan_id: UUID = Field(..., description="Scan identifier")
    status: ScanStatus = Field(..., description="Current scan status")
    progress_message: str = Field(..., description="Current progress message")
    vulnerabilities_found: int = Field(default=0, description="Number of vulnerabilities found so far")
    timestamp: str = Field(..., description="Progress update timestamp")


class ScanResult(BaseModel):
    """Complete scan result model."""
    scan_id: UUID = Field(..., description="Scan identifier")
    status: ScanStatus = Field(..., description="Final scan status")
    target_url: str = Field(..., description="Target URL that was scanned")
    repo_url: Optional[str] = Field(None, description="Repository URL if provided")
    instructions: Optional[str] = Field(None, description="Testing instructions if provided")
    created_at: str = Field(..., description="Scan creation timestamp")
    started_at: Optional[str] = Field(None, description="Scan start timestamp")
    completed_at: Optional[str] = Field(None, description="Scan completion timestamp")
    vulnerabilities: List[VulnerabilityReport] = Field(default_factory=list, description="Found vulnerabilities")
    final_report: Optional[str] = Field(None, description="Final penetration test report")
    error_message: Optional[str] = Field(None, description="Error message if scan failed")


class ScanListResponse(BaseModel):
    """Response model for listing scans."""
    scans: List[ScanResponse] = Field(..., description="List of scans")
    total: int = Field(..., description="Total number of scans")


class WebSocketMessage(BaseModel):
    """WebSocket message model."""
    type: str = Field(..., description="Message type")
    data: Dict[str, Any] = Field(..., description="Message data")
    timestamp: str = Field(..., description="Message timestamp")