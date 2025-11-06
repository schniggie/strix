"""
FastAPI web interface for Strix cybersecurity agent.
Provides REST API endpoints and WebSocket support for real-time scan updates.
"""

import json
import logging
from typing import List
from uuid import UUID

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .models import (
    ScanTargetRequest, 
    ScanResponse, 
    ScanResult, 
    ScanListResponse,
    ScanStatus
)
from .scan_manager import scan_manager
from .security import check_rate_limit, validate_scan_input, add_security_headers


logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Strix Web Interface",
    description="Self-service web interface for Strix cybersecurity penetration testing",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
try:
    app.mount("/static", StaticFiles(directory="strix/interface/web/static"), name="static")
    templates = Jinja2Templates(directory="strix/interface/web/templates")
except Exception as e:
    logger.warning(f"Could not mount static files or templates: {e}")
    templates = None


@app.middleware("http")
async def add_security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    return add_security_headers(response)


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, _: None = Depends(check_rate_limit)):
    """Serve the main web interface."""
    if templates:
        return templates.TemplateResponse("index.html", {"request": request})
    else:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Strix Web Interface</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 800px; margin: 0 auto; }
                .form-group { margin-bottom: 20px; }
                label { display: block; margin-bottom: 5px; font-weight: bold; }
                input, textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
                button { background: #007bff; color: white; padding: 12px 24px; border: none; border-radius: 4px; cursor: pointer; }
                button:hover { background: #0056b3; }
                .status { margin-top: 20px; padding: 15px; border-radius: 4px; }
                .status.running { background: #d4edda; border: 1px solid #c3e6cb; }
                .status.completed { background: #d1ecf1; border: 1px solid #bee5eb; }
                .status.failed { background: #f8d7da; border: 1px solid #f5c6cb; }
                .vulnerability { margin: 10px 0; padding: 10px; border-left: 4px solid #dc3545; background: #f8f9fa; }
                .vulnerability.high { border-left-color: #dc3545; }
                .vulnerability.medium { border-left-color: #ffc107; }
                .vulnerability.low { border-left-color: #28a745; }
                .vulnerability.critical { border-left-color: #6f42c1; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🦉 Strix Cybersecurity Agent</h1>
                <p>Self-service penetration testing for developers</p>
                
                <form id="scanForm">
                    <div class="form-group">
                        <label for="targetUrl">Target URL *</label>
                        <input type="url" id="targetUrl" name="targetUrl" required 
                               placeholder="https://example.com">
                    </div>
                    
                    <div class="form-group">
                        <label for="repoUrl">Repository URL (optional)</label>
                        <input type="url" id="repoUrl" name="repoUrl" 
                               placeholder="https://github.com/user/repo">
                    </div>
                    
                    <div class="form-group">
                        <label for="instructions">Focused Test Instructions (optional)</label>
                        <textarea id="instructions" name="instructions" rows="3" 
                                  placeholder="Focus on authentication vulnerabilities, test with credentials admin:password123, etc."></textarea>
                    </div>
                    
                    <button type="submit">Start Penetration Test</button>
                </form>
                
                <div id="scanStatus" style="display: none;"></div>
                <div id="vulnerabilities"></div>
                <div id="finalReport" style="display: none;"></div>
            </div>
            
            <script>
                let currentScanId = null;
                let websocket = null;
                
                document.getElementById('scanForm').addEventListener('submit', async (e) => {
                    e.preventDefault();
                    
                    const formData = new FormData(e.target);
                    const scanData = {
                        target_url: formData.get('targetUrl'),
                        repo_url: formData.get('repoUrl') || null,
                        instructions: formData.get('instructions') || null
                    };
                    
                    try {
                        // Create scan
                        const response = await fetch('/api/scans', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(scanData)
                        });
                        
                        if (!response.ok) {
                            throw new Error('Failed to create scan');
                        }
                        
                        const scan = await response.json();
                        currentScanId = scan.scan_id;
                        
                        // Show status
                        document.getElementById('scanStatus').style.display = 'block';
                        document.getElementById('scanStatus').innerHTML = 
                            '<div class="status running">🔄 Penetration test starting...</div>';
                        
                        // Clear previous results
                        document.getElementById('vulnerabilities').innerHTML = '';
                        document.getElementById('finalReport').style.display = 'none';
                        
                        // Start scan
                        await fetch(`/api/scans/${currentScanId}/start`, { method: 'POST' });
                        
                        // Connect WebSocket
                        connectWebSocket(currentScanId);
                        
                    } catch (error) {
                        alert('Error starting scan: ' + error.message);
                    }
                });
                
                function connectWebSocket(scanId) {
                    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                    websocket = new WebSocket(`${protocol}//${window.location.host}/api/scans/${scanId}/ws`);
                    
                    websocket.onmessage = (event) => {
                        const data = JSON.parse(event.data);
                        handleWebSocketMessage(data);
                    };
                    
                    websocket.onerror = (error) => {
                        console.error('WebSocket error:', error);
                    };
                    
                    websocket.onclose = () => {
                        console.log('WebSocket connection closed');
                    };
                }
                
                function handleWebSocketMessage(data) {
                    const statusDiv = document.getElementById('scanStatus');
                    const vulnerabilitiesDiv = document.getElementById('vulnerabilities');
                    const finalReportDiv = document.getElementById('finalReport');
                    
                    switch (data.type) {
                        case 'progress':
                            statusDiv.innerHTML = `<div class="status running">🔄 ${data.message}</div>`;
                            break;
                            
                        case 'vulnerability':
                            const vuln = data.vulnerability;
                            const vulnDiv = document.createElement('div');
                            vulnDiv.className = `vulnerability ${vuln.severity}`;
                            vulnDiv.innerHTML = `
                                <h4>🐞 ${vuln.title}</h4>
                                <p><strong>Severity:</strong> ${vuln.severity.toUpperCase()}</p>
                                <p><strong>Report ID:</strong> ${vuln.report_id}</p>
                                <div>${vuln.content}</div>
                            `;
                            vulnerabilitiesDiv.appendChild(vulnDiv);
                            break;
                            
                        case 'completion':
                            statusDiv.innerHTML = '<div class="status completed">✅ Penetration test completed</div>';
                            if (data.result.final_report) {
                                finalReportDiv.innerHTML = `
                                    <h3>📄 Final Report</h3>
                                    <pre>${data.result.final_report}</pre>
                                `;
                                finalReportDiv.style.display = 'block';
                            }
                            break;
                            
                        case 'failure':
                            statusDiv.innerHTML = `<div class="status failed">❌ Scan failed: ${data.error}</div>`;
                            break;
                    }
                }
            </script>
        </body>
        </html>
        """)


@app.post("/api/scans", response_model=ScanResponse)
async def create_scan(scan_request: ScanTargetRequest, request: Request, _: None = Depends(check_rate_limit)):
    """Create a new penetration test scan."""
    try:
        # Validate input
        validated_target, validated_repo, validated_instructions = validate_scan_input(
            scan_request.target_url,
            scan_request.repo_url,
            scan_request.instructions
        )
        
        scan_response = await scan_manager.create_scan(
            target_url=validated_target,
            repo_url=validated_repo,
            instructions=validated_instructions
        )
        return scan_response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create scan: {e}")
        raise HTTPException(status_code=500, detail="Failed to create scan")


@app.post("/api/scans/{scan_id}/start")
async def start_scan(scan_id: UUID):
    """Start a penetration test scan."""
    success = await scan_manager.start_scan(scan_id)
    if not success:
        raise HTTPException(status_code=404, detail="Scan not found or cannot be started")
    return {"message": "Scan started successfully"}


@app.get("/api/scans/{scan_id}", response_model=ScanResponse)
async def get_scan(scan_id: UUID):
    """Get scan information by ID."""
    scan = scan_manager.get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan


@app.get("/api/scans/{scan_id}/result", response_model=ScanResult)
async def get_scan_result(scan_id: UUID):
    """Get scan result by ID."""
    result = scan_manager.get_scan_result(scan_id)
    if not result:
        raise HTTPException(status_code=404, detail="Scan result not found")
    return result


@app.get("/api/scans", response_model=ScanListResponse)
async def list_scans():
    """List all scans."""
    scans = scan_manager.list_scans()
    return ScanListResponse(scans=scans, total=len(scans))


@app.post("/api/scans/{scan_id}/cancel")
async def cancel_scan(scan_id: UUID):
    """Cancel a running scan."""
    success = await scan_manager.cancel_scan(scan_id)
    if not success:
        raise HTTPException(status_code=404, detail="Scan not found or cannot be cancelled")
    return {"message": "Scan cancelled successfully"}


@app.websocket("/api/scans/{scan_id}/ws")
async def websocket_endpoint(websocket: WebSocket, scan_id: UUID):
    """WebSocket endpoint for real-time scan updates."""
    await websocket.accept()
    
    # Add connection to scan manager
    scan_manager.add_websocket_connection(scan_id, websocket)
    
    try:
        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for messages (ping/pong, etc.)
                data = await websocket.receive_text()
                # Echo back for ping/pong
                await websocket.send_text(f"Echo: {data}")
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
    finally:
        # Remove connection from scan manager
        scan_manager.remove_websocket_connection(scan_id, websocket)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "strix-web-interface"}


@app.get("/api/status")
async def api_status():
    """API status endpoint."""
    active_scans = len(scan_manager.active_scans)
    completed_scans = len([s for s in scan_manager.scan_results.values() 
                          if s.status == ScanStatus.COMPLETED])
    
    return {
        "status": "operational",
        "active_scans": active_scans,
        "completed_scans": completed_scans,
        "websocket_connections": sum(len(conns) for conns in scan_manager.websocket_connections.values())
    }