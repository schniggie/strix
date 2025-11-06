// Strix Web Interface JavaScript

class StrixWebInterface {
    constructor() {
        this.currentScanId = null;
        this.websocket = null;
        this.vulnerabilityCount = 0;
        
        this.initializeEventListeners();
    }
    
    initializeEventListeners() {
        // Form submission
        document.getElementById('scanForm').addEventListener('submit', (e) => {
            this.handleScanSubmission(e);
        });
        
        // Download report button
        document.getElementById('downloadReportBtn').addEventListener('click', () => {
            this.downloadReport();
        });
    }
    
    async handleScanSubmission(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const scanData = {
            target_url: formData.get('targetUrl'),
            repo_url: formData.get('repoUrl') || null,
            instructions: formData.get('instructions') || null
        };
        
        // Validate input
        if (!scanData.target_url) {
            this.showError('Target URL is required');
            return;
        }
        
        try {
            // Show loading overlay
            this.showLoadingOverlay(true);
            
            // Disable form
            this.setFormEnabled(false);
            
            // Create scan
            const response = await fetch('/api/scans', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(scanData)
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to create scan');
            }
            
            const scan = await response.json();
            this.currentScanId = scan.scan_id;
            
            // Show progress section
            this.showScanProgress();
            
            // Start scan
            const startResponse = await fetch(`/api/scans/${this.currentScanId}/start`, {
                method: 'POST'
            });
            
            if (!startResponse.ok) {
                throw new Error('Failed to start scan');
            }
            
            // Connect WebSocket
            this.connectWebSocket(this.currentScanId);
            
            // Hide loading overlay
            this.showLoadingOverlay(false);
            
        } catch (error) {
            console.error('Error starting scan:', error);
            this.showError('Error starting scan: ' + error.message);
            this.showLoadingOverlay(false);
            this.setFormEnabled(true);
        }
    }
    
    connectWebSocket(scanId) {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/api/scans/${scanId}/ws`;
        
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onopen = () => {
            console.log('WebSocket connected');
            this.updateStatus('Connected to scan service', 'running');
        };
        
        this.websocket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };
        
        this.websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.updateStatus('Connection error occurred', 'failed');
        };
        
        this.websocket.onclose = (event) => {
            console.log('WebSocket connection closed:', event.code, event.reason);
            if (event.code !== 1000) { // Not a normal closure
                this.updateStatus('Connection lost', 'failed');
            }
        };
    }
    
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'progress':
                this.updateStatus(data.message, 'running');
                this.updateProgressBar(50); // Indeterminate progress
                break;
                
            case 'vulnerability':
                this.addVulnerability(data.vulnerability);
                break;
                
            case 'completion':
                this.handleScanCompletion(data.result);
                break;
                
            case 'failure':
                this.handleScanFailure(data.error);
                break;
                
            default:
                console.log('Unknown message type:', data.type);
        }
    }
    
    updateStatus(message, type) {
        const statusContainer = document.getElementById('scanStatus');
        const statusClass = type === 'running' ? 'running' : 
                           type === 'completed' ? 'completed' : 'failed';
        
        const icon = type === 'running' ? '<i class="fas fa-cog fa-spin"></i>' :
                     type === 'completed' ? '<i class="fas fa-check-circle"></i>' :
                     '<i class="fas fa-exclamation-triangle"></i>';
        
        statusContainer.innerHTML = `
            <div class="status ${statusClass}">
                ${icon} ${message}
            </div>
        `;
    }
    
    updateProgressBar(percentage) {
        const progressFill = document.querySelector('.progress-fill');
        if (progressFill) {
            progressFill.style.width = `${percentage}%`;
        }
    }
    
    addVulnerability(vulnerability) {
        this.vulnerabilityCount++;
        
        // Update count
        document.getElementById('vulnerabilitiesCount').textContent = 
            `${this.vulnerabilityCount} vulnerability${this.vulnerabilityCount !== 1 ? 's' : ''} found`;
        
        // Show vulnerabilities section
        document.getElementById('vulnerabilitiesSection').style.display = 'block';
        
        // Create vulnerability element
        const vulnElement = document.createElement('div');
        vulnElement.className = `vulnerability ${vulnerability.severity}`;
        vulnElement.innerHTML = `
            <h4><i class="fas fa-bug"></i> ${this.escapeHtml(vulnerability.title)}</h4>
            <div class="severity ${vulnerability.severity}">${vulnerability.severity}</div>
            <div class="report-id">Report ID: ${this.escapeHtml(vulnerability.report_id)}</div>
            <div class="content">${this.escapeHtml(vulnerability.content)}</div>
        `;
        
        // Add to container
        document.getElementById('vulnerabilities').appendChild(vulnElement);
        
        // Scroll to new vulnerability
        vulnElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        
        // Show notification
        this.showNotification(`New ${vulnerability.severity} vulnerability found: ${vulnerability.title}`, 'warning');
    }
    
    handleScanCompletion(result) {
        this.updateStatus('Penetration test completed successfully', 'completed');
        this.updateProgressBar(100);
        
        // Show final report if available
        if (result.final_report) {
            document.getElementById('finalReport').textContent = result.final_report;
            document.getElementById('finalReportSection').style.display = 'block';
        }
        
        // Re-enable form
        this.setFormEnabled(true);
        
        // Close WebSocket
        if (this.websocket) {
            this.websocket.close();
        }
        
        // Show completion notification
        const vulnCount = result.vulnerabilities ? result.vulnerabilities.length : this.vulnerabilityCount;
        this.showNotification(
            `Scan completed! Found ${vulnCount} vulnerability${vulnCount !== 1 ? 's' : ''}`, 
            'success'
        );
    }
    
    handleScanFailure(error) {
        this.updateStatus(`Scan failed: ${error}`, 'failed');
        this.updateProgressBar(0);
        
        // Re-enable form
        this.setFormEnabled(true);
        
        // Close WebSocket
        if (this.websocket) {
            this.websocket.close();
        }
        
        // Show error notification
        this.showNotification(`Scan failed: ${error}`, 'error');
    }
    
    showScanProgress() {
        document.getElementById('scanProgress').style.display = 'block';
        document.getElementById('scanProgress').scrollIntoView({ behavior: 'smooth' });
    }
    
    setFormEnabled(enabled) {
        const form = document.getElementById('scanForm');
        const inputs = form.querySelectorAll('input, textarea, button');
        
        inputs.forEach(input => {
            input.disabled = !enabled;
        });
        
        const submitBtn = document.getElementById('startScanBtn');
        if (enabled) {
            submitBtn.innerHTML = '<i class="fas fa-play"></i> Start Penetration Test';
        } else {
            submitBtn.innerHTML = '<i class="fas fa-cog fa-spin"></i> Running...';
        }
    }
    
    showLoadingOverlay(show) {
        const overlay = document.getElementById('loadingOverlay');
        overlay.style.display = show ? 'flex' : 'none';
    }
    
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    showNotification(message, type) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${type === 'success' ? 'check-circle' : 
                                   type === 'warning' ? 'exclamation-triangle' : 
                                   'exclamation-circle'}"></i>
                <span>${this.escapeHtml(message)}</span>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        // Add styles if not already present
        if (!document.getElementById('notification-styles')) {
            const styles = document.createElement('style');
            styles.id = 'notification-styles';
            styles.textContent = `
                .notification {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    z-index: 10000;
                    max-width: 400px;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                    animation: slideIn 0.3s ease-out;
                }
                
                .notification-content {
                    padding: 16px;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    color: white;
                    font-weight: 500;
                }
                
                .notification-success { background: #28a745; }
                .notification-warning { background: #ffc107; color: #212529; }
                .notification-error { background: #dc3545; }
                
                .notification-close {
                    background: none;
                    border: none;
                    color: inherit;
                    cursor: pointer;
                    padding: 4px;
                    margin-left: auto;
                }
                
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
            `;
            document.head.appendChild(styles);
        }
        
        // Add to page
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }
    
    async downloadReport() {
        if (!this.currentScanId) {
            this.showError('No scan result available');
            return;
        }
        
        try {
            const response = await fetch(`/api/scans/${this.currentScanId}/result`);
            if (!response.ok) {
                throw new Error('Failed to fetch scan result');
            }
            
            const result = await response.json();
            
            // Create downloadable content
            let content = `Strix Penetration Test Report\n`;
            content += `=====================================\n\n`;
            content += `Scan ID: ${result.scan_id}\n`;
            content += `Target URL: ${result.target_url}\n`;
            if (result.repo_url) {
                content += `Repository URL: ${result.repo_url}\n`;
            }
            if (result.instructions) {
                content += `Instructions: ${result.instructions}\n`;
            }
            content += `Started: ${result.started_at}\n`;
            content += `Completed: ${result.completed_at}\n`;
            content += `Status: ${result.status}\n\n`;
            
            if (result.vulnerabilities && result.vulnerabilities.length > 0) {
                content += `Vulnerabilities Found: ${result.vulnerabilities.length}\n\n`;
                
                result.vulnerabilities.forEach((vuln, index) => {
                    content += `${index + 1}. ${vuln.title}\n`;
                    content += `   Severity: ${vuln.severity.toUpperCase()}\n`;
                    content += `   Report ID: ${vuln.report_id}\n`;
                    content += `   Found: ${vuln.found_at}\n`;
                    content += `   Description:\n   ${vuln.content.replace(/\n/g, '\n   ')}\n\n`;
                });
            } else {
                content += `No vulnerabilities found.\n\n`;
            }
            
            if (result.final_report) {
                content += `Final Report:\n`;
                content += `=============\n`;
                content += result.final_report;
            }
            
            // Create and download file
            const blob = new Blob([content], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `strix-report-${result.scan_id}.txt`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            this.showNotification('Report downloaded successfully', 'success');
            
        } catch (error) {
            console.error('Error downloading report:', error);
            this.showError('Failed to download report: ' + error.message);
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new StrixWebInterface();
});