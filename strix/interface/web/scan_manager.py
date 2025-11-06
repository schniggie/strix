"""
Scan management system for the Strix web interface.
Handles scan lifecycle, progress tracking, and result storage.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from strix.agents.StrixAgent import StrixAgent
from strix.interface.utils import generate_run_name, infer_target_type, assign_workspace_subdirs, clone_repository, collect_local_sources
from strix.llm.config import LLMConfig
from strix.telemetry.tracer import Tracer, set_global_tracer

from .models import ScanStatus, ScanResponse, ScanResult, VulnerabilityReport, VulnerabilitySeverity


logger = logging.getLogger(__name__)


class ScanManager:
    """Manages penetration test scans for the web interface."""
    
    def __init__(self):
        self.active_scans: Dict[UUID, Dict] = {}
        self.scan_results: Dict[UUID, ScanResult] = {}
        self.websocket_connections: Dict[UUID, List] = {}
    
    async def create_scan(self, target_url: str, repo_url: Optional[str] = None, 
                         instructions: Optional[str] = None) -> ScanResponse:
        """Create a new penetration test scan."""
        scan_id = uuid4()
        run_name = generate_run_name()
        created_at = datetime.utcnow().isoformat()
        
        # Prepare targets info similar to CLI
        targets = [target_url]
        if repo_url:
            targets.append(repo_url)
        
        targets_info = []
        for target in targets:
            try:
                target_type, target_dict = infer_target_type(target)
                if target_type == "local_code":
                    display_target = target_dict.get("target_path", target)
                else:
                    display_target = target
                
                targets_info.append({
                    "type": target_type,
                    "details": target_dict,
                    "original": display_target
                })
            except ValueError as e:
                logger.error(f"Invalid target '{target}': {e}")
                raise ValueError(f"Invalid target '{target}': {e}")
        
        assign_workspace_subdirs(targets_info)
        
        scan_response = ScanResponse(
            scan_id=scan_id,
            status=ScanStatus.PENDING,
            target_url=target_url,
            repo_url=repo_url,
            instructions=instructions,
            created_at=created_at
        )
        
        # Store scan info
        self.active_scans[scan_id] = {
            "response": scan_response,
            "targets_info": targets_info,
            "run_name": run_name,
            "task": None
        }
        
        return scan_response
    
    async def start_scan(self, scan_id: UUID) -> bool:
        """Start a penetration test scan."""
        if scan_id not in self.active_scans:
            return False
        
        scan_info = self.active_scans[scan_id]
        scan_response = scan_info["response"]
        
        if scan_response.status != ScanStatus.PENDING:
            return False
        
        # Update status to running
        scan_response.status = ScanStatus.RUNNING
        scan_response.started_at = datetime.utcnow().isoformat()
        
        # Start the scan task
        task = asyncio.create_task(self._run_scan(scan_id))
        scan_info["task"] = task
        
        return True
    
    async def _run_scan(self, scan_id: UUID):
        """Execute the actual penetration test scan."""
        try:
            scan_info = self.active_scans[scan_id]
            scan_response = scan_info["response"]
            targets_info = scan_info["targets_info"]
            run_name = scan_info["run_name"]
            
            # Handle repository cloning if needed
            for target_info in targets_info:
                if target_info["type"] == "repository":
                    repo_url = target_info["details"]["target_repo"]
                    dest_name = target_info["details"].get("workspace_subdir")
                    cloned_path = clone_repository(repo_url, run_name, dest_name)
                    target_info["details"]["cloned_repo_path"] = cloned_path
            
            local_sources = collect_local_sources(targets_info)
            
            # Prepare scan configuration
            scan_config = {
                "scan_id": run_name,
                "targets": targets_info,
                "user_instructions": scan_response.instructions or "",
                "run_name": run_name,
            }
            
            # Configure LLM and agent
            llm_config = LLMConfig()
            agent_config = {
                "llm_config": llm_config,
                "max_iterations": 300,
                "non_interactive": True,
            }
            
            if local_sources:
                agent_config["local_sources"] = local_sources
            
            # Set up tracer for progress tracking
            tracer = Tracer(run_name)
            tracer.set_scan_config(scan_config)
            
            # Set up vulnerability callback
            def vulnerability_callback(report_id: str, title: str, content: str, severity: str):
                self._handle_vulnerability_found(scan_id, report_id, title, content, severity)
            
            tracer.vulnerability_found_callback = vulnerability_callback
            set_global_tracer(tracer)
            
            # Send progress update
            await self._send_progress_update(scan_id, "Starting penetration test...")
            
            # Execute the scan
            agent = StrixAgent(agent_config)
            result = await agent.execute_scan(scan_config)
            
            # Handle scan completion
            await self._handle_scan_completion(scan_id, result, tracer)
            
        except Exception as e:
            logger.error(f"Scan {scan_id} failed: {e}")
            await self._handle_scan_failure(scan_id, str(e))
    
    def _handle_vulnerability_found(self, scan_id: UUID, report_id: str, title: str, 
                                  content: str, severity: str):
        """Handle vulnerability discovery during scan."""
        vulnerability = VulnerabilityReport(
            report_id=report_id,
            title=title,
            severity=VulnerabilitySeverity(severity.lower()),
            content=content,
            found_at=datetime.utcnow().isoformat()
        )
        
        # Store vulnerability
        if scan_id not in self.scan_results:
            self.scan_results[scan_id] = ScanResult(
                scan_id=scan_id,
                status=ScanStatus.RUNNING,
                target_url=self.active_scans[scan_id]["response"].target_url,
                repo_url=self.active_scans[scan_id]["response"].repo_url,
                instructions=self.active_scans[scan_id]["response"].instructions,
                created_at=self.active_scans[scan_id]["response"].created_at,
                started_at=self.active_scans[scan_id]["response"].started_at
            )
        
        self.scan_results[scan_id].vulnerabilities.append(vulnerability)
        
        # Send real-time update via WebSocket
        asyncio.create_task(self._send_vulnerability_update(scan_id, vulnerability))
    
    async def _handle_scan_completion(self, scan_id: UUID, result, tracer):
        """Handle successful scan completion."""
        scan_info = self.active_scans[scan_id]
        scan_response = scan_info["response"]
        
        # Update scan status
        scan_response.status = ScanStatus.COMPLETED
        scan_response.completed_at = datetime.utcnow().isoformat()
        
        # Create final result
        scan_result = ScanResult(
            scan_id=scan_id,
            status=ScanStatus.COMPLETED,
            target_url=scan_response.target_url,
            repo_url=scan_response.repo_url,
            instructions=scan_response.instructions,
            created_at=scan_response.created_at,
            started_at=scan_response.started_at,
            completed_at=scan_response.completed_at,
            vulnerabilities=self.scan_results.get(scan_id, ScanResult(scan_id=scan_id, status=ScanStatus.COMPLETED, target_url="", created_at="")).vulnerabilities,
            final_report=tracer.final_scan_result if tracer else None
        )
        
        self.scan_results[scan_id] = scan_result
        
        # Send completion update
        await self._send_completion_update(scan_id, scan_result)
        
        # Cleanup tracer
        if tracer:
            tracer.cleanup()
    
    async def _handle_scan_failure(self, scan_id: UUID, error_message: str):
        """Handle scan failure."""
        scan_info = self.active_scans[scan_id]
        scan_response = scan_info["response"]
        
        # Update scan status
        scan_response.status = ScanStatus.FAILED
        scan_response.completed_at = datetime.utcnow().isoformat()
        
        # Create failure result
        scan_result = ScanResult(
            scan_id=scan_id,
            status=ScanStatus.FAILED,
            target_url=scan_response.target_url,
            repo_url=scan_response.repo_url,
            instructions=scan_response.instructions,
            created_at=scan_response.created_at,
            started_at=scan_response.started_at,
            completed_at=scan_response.completed_at,
            error_message=error_message
        )
        
        self.scan_results[scan_id] = scan_result
        
        # Send failure update
        await self._send_failure_update(scan_id, error_message)
    
    async def _send_progress_update(self, scan_id: UUID, message: str):
        """Send progress update via WebSocket."""
        if scan_id in self.websocket_connections:
            update_data = {
                "type": "progress",
                "scan_id": str(scan_id),
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            for websocket in self.websocket_connections[scan_id]:
                try:
                    await websocket.send_text(json.dumps(update_data))
                except Exception as e:
                    logger.error(f"Failed to send progress update: {e}")
    
    async def _send_vulnerability_update(self, scan_id: UUID, vulnerability: VulnerabilityReport):
        """Send vulnerability update via WebSocket."""
        if scan_id in self.websocket_connections:
            update_data = {
                "type": "vulnerability",
                "scan_id": str(scan_id),
                "vulnerability": vulnerability.dict(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            for websocket in self.websocket_connections[scan_id]:
                try:
                    await websocket.send_text(json.dumps(update_data))
                except Exception as e:
                    logger.error(f"Failed to send vulnerability update: {e}")
    
    async def _send_completion_update(self, scan_id: UUID, result: ScanResult):
        """Send scan completion update via WebSocket."""
        if scan_id in self.websocket_connections:
            update_data = {
                "type": "completion",
                "scan_id": str(scan_id),
                "result": result.dict(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            for websocket in self.websocket_connections[scan_id]:
                try:
                    await websocket.send_text(json.dumps(update_data))
                except Exception as e:
                    logger.error(f"Failed to send completion update: {e}")
    
    async def _send_failure_update(self, scan_id: UUID, error_message: str):
        """Send scan failure update via WebSocket."""
        if scan_id in self.websocket_connections:
            update_data = {
                "type": "failure",
                "scan_id": str(scan_id),
                "error": error_message,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            for websocket in self.websocket_connections[scan_id]:
                try:
                    await websocket.send_text(json.dumps(update_data))
                except Exception as e:
                    logger.error(f"Failed to send failure update: {e}")
    
    def get_scan(self, scan_id: UUID) -> Optional[ScanResponse]:
        """Get scan information by ID."""
        if scan_id in self.active_scans:
            return self.active_scans[scan_id]["response"]
        return None
    
    def get_scan_result(self, scan_id: UUID) -> Optional[ScanResult]:
        """Get scan result by ID."""
        return self.scan_results.get(scan_id)
    
    def list_scans(self) -> List[ScanResponse]:
        """List all scans."""
        return [scan_info["response"] for scan_info in self.active_scans.values()]
    
    def add_websocket_connection(self, scan_id: UUID, websocket):
        """Add WebSocket connection for scan updates."""
        if scan_id not in self.websocket_connections:
            self.websocket_connections[scan_id] = []
        self.websocket_connections[scan_id].append(websocket)
    
    def remove_websocket_connection(self, scan_id: UUID, websocket):
        """Remove WebSocket connection."""
        if scan_id in self.websocket_connections:
            try:
                self.websocket_connections[scan_id].remove(websocket)
                if not self.websocket_connections[scan_id]:
                    del self.websocket_connections[scan_id]
            except ValueError:
                pass
    
    async def cancel_scan(self, scan_id: UUID) -> bool:
        """Cancel a running scan."""
        if scan_id not in self.active_scans:
            return False
        
        scan_info = self.active_scans[scan_id]
        scan_response = scan_info["response"]
        
        if scan_response.status != ScanStatus.RUNNING:
            return False
        
        # Cancel the task
        task = scan_info.get("task")
        if task and not task.done():
            task.cancel()
        
        # Update status
        scan_response.status = ScanStatus.CANCELLED
        scan_response.completed_at = datetime.utcnow().isoformat()
        
        return True


# Global scan manager instance
scan_manager = ScanManager()